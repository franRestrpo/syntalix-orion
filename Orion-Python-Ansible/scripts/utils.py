"""
Utilidades generales para Syntalix-Orion.

Funciones helper para:
- Ejecución de comandos
- Validación de sistema
- Generación de contraseñas seguras
- Logging
"""

import subprocess
import sys
import os
from typing import List, Optional, Tuple, Any
from pathlib import Path

# Importar módulos de seguridad
from core.security import generate_secure_password, validate_domain, validate_email
from core.logging_config import get_logger

# Logger
logger = get_logger(__name__)


def cmd_exists(cmd: str) -> bool:
    """
    Verifica si un comando existe en el PATH.
    
    Args:
        cmd: Nombre del comando
        
    Returns:
        True si el comando existe
    """
    result = subprocess.call(
        f"which {cmd}",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    ) == 0
    logger.debug(f"Comando '{cmd}' existe: {result}")
    return result


def run(cmd: List[str], check: bool = True, capture_output: bool = True) -> subprocess.CompletedProcess:
    """
    Ejecuta un comando de forma segura.
    
    Args:
        cmd: Comando como lista de argumentos
        check: Si True, lanza excepción en caso de error
        capture_output: Si True, captura stdout/stderr
        
    Returns:
        CompletedProcess con el resultado
    """
    logger.debug(f"Ejecutando comando: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=capture_output,
            text=True,
        )
        if result.returncode == 0:
            logger.debug(f"Comando exitoso")
        else:
            logger.warning(f"Comando exited con código: {result.returncode}")
        return result
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error ejecutando comando", extra={
            "cmd": ' '.join(cmd),
            "returncode": e.returncode,
            "stderr": e.stderr if hasattr(e, 'stderr') else None
        })
        if check:
            raise
        return subprocess.CompletedProcess(args=cmd, returncode=e.returncode)


def run_docker_command(
    args: List[str],
    check: bool = True,
    capture_output: bool = True,
) -> subprocess.CompletedProcess:
    """
    Ejecuta un comando Docker de forma segura.
    
    Args:
        args: Argumentos para docker
        check: Si True, lanza excepción en caso de error
        capture_output: Si True, captura stdout/stderr
        
    Returns:
        CompletedProcess con el resultado
    """
    full_cmd = ["docker"] + args
    return run(full_cmd, check=check, capture_output=capture_output)


def check_docker_available() -> Tuple[bool, Optional[str]]:
    """
    Verifica si Docker está disponible y en ejecución.
    
    Returns:
        Tupla (disponible, versión o mensaje de error)
    """
    if not cmd_exists("docker"):
        logger.warning("Docker no encontrado en PATH")
        return False, "Docker no está instalado"
    
    try:
        result = run(["docker", "version", "--format", "{{.Server.Version}}"], check=False)
        if result.returncode == 0:
            version = result.stdout.strip()
            logger.info("Docker disponible", extra={"version": version})
            return True, version
        else:
            error_msg = result.stderr.strip() if result.stderr else "Error desconocido"
            logger.error("Docker no está en ejecución", extra={"error": error_msg})
            return False, error_msg
            
    except Exception as e:
        logger.error("Error verificando Docker", extra={"error": str(e)})
        return False, str(e)


def check_swarm_active() -> Tuple[bool, Optional[str]]:
    """
    Verifica si Docker Swarm está activo.
    
    Returns:
        Tupla (activo, estado o mensaje)
    """
    try:
        result = run(["docker", "info", "--format", "{{.Swarm.LocalNodeState}}"], check=False)
        if result.returncode == 0:
            state = result.stdout.strip()
            is_active = state == "active"
            
            if is_active:
                logger.info("Docker Swarm activo")
            else:
                logger.warning(f"Docker Swarm no activo", extra={"state": state})
                
            return is_active, state
        else:
            return False, "Error al verificar Swarm"
            
    except Exception as e:
        logger.error("Error verificando Swarm", extra={"error": str(e)})
        return False, str(e)


def check_network_exists(network_name: str) -> bool:
    """
    Verifica si existe una red Docker.
    
    Args:
        network_name: Nombre de la red
        
    Returns:
        True si la red existe
    """
    try:
        result = run(
            ["docker", "network", "ls", "--format", "{{.Name}}"],
            check=True,
            capture_output=True
        )
        networks = result.stdout.strip().split('\n')
        exists = network_name in networks
        logger.debug(f"Red '{network_name}' existe: {exists}")
        return exists
        
    except Exception as e:
        logger.error("Error verificando red", extra={"network": network_name, "error": str(e)})
        return False


def create_overlay_network(network_name: str, attachable: bool = True) -> bool:
    """
    Crea una red overlay para Docker Swarm.
    
    Args:
        network_name: Nombre de la red
        attachable: Si True, permite attaching de servicios standalone
        
    Returns:
        True si se creó exitosamente o ya existía
    """
    if check_network_exists(network_name):
        logger.info(f"Red '{network_name}' ya existe")
        return True
    
    logger.info(f"Creando red overlay '{network_name}'", extra={"attachable": attachable})
    
    cmd = ["docker", "network", "create", "--driver=overlay"]
    if attachable:
        cmd.append("--attachable")
    cmd.append(network_name)
    
    try:
        run(cmd, check=True)
        logger.info(f"Red '{network_name}' creada exitosamente")
        return True
        
    except Exception as e:
        logger.error("Error creando red", extra={"network": network_name, "error": str(e)})
        return False


def generate_app_password(length: int = 32) -> str:
    """
    Genera una contraseña segura para aplicaciones.
    Reemplaza contraseñas hardcodeadas como 'admin123'.
    
    Args:
        length: Longitud de la contraseña
        
    Returns:
        Contraseña segura
    """
    return generate_secure_password(length=length)


def validate_app_domain(domain: str) -> Tuple[bool, Optional[str]]:
    """
    Valida el dominio de una aplicación.
    
    Args:
        domain: Dominio a validar
        
    Returns:
        Tupla (válido, mensaje de error o None)
    """
    if not domain or not domain.strip():
        return False, "El dominio no puede estar vacío"
    
    domain = domain.strip()
    
    # Normalizar: añadir .localhost si no tiene TLD
    if '.' not in domain:
        domain = f"{domain}.localhost"
    
    if validate_domain(domain):
        return True, None
    
    return False, f"Dominio inválido: {domain}"


def validate_app_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Valida el email de una aplicación.
    
    Args:
        email: Email a validar
        
    Returns:
        Tupla (válido, mensaje de error o None)
    """
    if not email or not email.strip():
        return False, "El email no puede estar vacío"
    
    if validate_email(email.strip()):
        return True, None
    
    return False, f"Email inválido: {email}"


def get_orion_base_dir() -> Path:
    """
    Obtiene el directorio base de Orion.
    
    Returns:
        Path al directorio base
    """
    return Path(__file__).parent.parent.parent


def get_deploy_dir() -> Path:
    """
    Obtiene el directorio de despliegue.
    
    Returns:
        Path al directorio deploy (crea si no existe)
    """
    deploy_dir = get_orion_base_dir() / "deploy"
    deploy_dir.mkdir(exist_ok=True)
    return deploy_dir


def ensure_credenciales_dir() -> Path:
    """
    Asegura que exista el directorio de credenciales.
    
    Returns:
        Path al directorio credenciales
    """
    cred_dir = get_orion_base_dir() / "credenciales"
    cred_dir.mkdir(exist_ok=True)
    
    # Establecer permisos restrictivos
    try:
        os.chmod(cred_dir, 0o700)  # Solo el propietario puede leer/escribir
    except Exception:
        pass  # Ignorar errores de permisos en Windows
    
    return cred_dir


def load_env_file(env_path: Path) -> dict:
    """
    Carga un archivo .env de forma segura.
    
    Args:
        env_path: Path al archivo .env
        
    Returns:
        Diccionario con las variables de entorno
    """
    from configparser import ConfigParser
    
    logger.debug(f"Cargando archivo .env: {env_path}")
    
    if not env_path.exists():
        logger.warning(f"Archivo .env no encontrado: {env_path}")
        return {}
    
    # Usar ConfigParser para parsing seguro
    config = ConfigParser()
    try:
        config.read(env_path)
    except Exception as e:
        logger.error("Error parsing .env", extra={"file": str(env_path), "error": str(e)})
        return {}
    
    result = {}
    if config.has_section('DEFAULT'):
        result = dict(config['DEFAULT'])
    elif config.sections():
        # Usar la primera sección
        result = dict(config[config.sections()[0]])
    
    logger.debug(f"Cargadas {len(result)} variables de {env_path}")
    return result


def save_env_file(env_path: Path, variables: dict) -> bool:
    """
    Guarda variables en un archivo .env de forma segura.
    
    Args:
        env_path: Path al archivo .env
        variables: Diccionario de variables
        
    Returns:
        True si se guardó exitosamente
    """
    from configparser import ConfigParser
    
    logger.info(f"Guardando variables en .env", extra={"file": str(env_path), "count": len(variables)})
    
    try:
        config = ConfigParser()
        config.read_dict({'DEFAULT': variables})
        
        with open(env_path, 'w', encoding='utf-8') as f:
            config.write(f)
        
        # Establecer permisos restrictivos
        try:
            os.chmod(env_path, 0o600)  # Solo propietario puede leer/escribir
        except Exception:
            pass  # Ignorar en Windows
        
        logger.info(f"Archivo .env guardado exitosamente")
        return True
        
    except Exception as e:
        logger.error("Error guardando .env", extra={"file": str(env_path), "error": str(e)})
        return False


__all__ = [
    "cmd_exists",
    "run",
    "run_docker_command",
    "check_docker_available",
    "check_swarm_active",
    "check_network_exists",
    "create_overlay_network",
    "generate_app_password",
    "validate_app_domain",
    "validate_app_email",
    "get_orion_base_dir",
    "get_deploy_dir",
    "ensure_credenciales_dir",
    "load_env_file",
    "save_env_file",
]
