"""
Utilidades Generales y Fachada de Sistema para Syntalix-Orion.

Este módulo actúa como una capa de conveniencia que centraliza y re-exporta las 
funcionalidades más utilizadas de los módulos 'core' unificados. Proporciona 
una interfaz simplificada para operaciones comunes de sistema, red y archivos.

Funcionalidades re-exportadas:
    - Seguridad: Generación de credenciales y validación de formatos.
    - Estado: Persistencia y recuperación de configuración.
    - Preflight: Auditoría de requisitos previos del sistema.
    - Logging: Acceso al sistema de registro de eventos.

Funcionalidades adicionales:
    - Ejecución controlada de subprocesos y comandos Docker.
    - Gestión de la estructura de directorios del proyecto (deploy, credenciales).
    - Normalización y validación específica de dominios y correos para apps.
"""

import subprocess
import os
from pathlib import Path
from typing import List, Optional, Tuple

# Importar módulos core unificados
from core.security import (
    generate_secure_password,
    generate_app_password,
    mask_secret,
    validate_domain,
    validate_email,
)
from core.logging_config import get_logger
from core.state import save_state, load_state, load_env_file as core_load_env, save_env_file as core_save_env
from core.preflight import (
    cmd_exists,
    check_docker_available,
    check_swarm_active,
    check_network_exists,
    create_overlay_network,
    get_cpu_cores,
    run_preflight_checks,
)

# Logger
logger = get_logger(__name__)


def run(
    cmd: List[str],
    check: bool = True,
    capture_output: bool = True
) -> subprocess.CompletedProcess:
    """
    Ejecuta un comando del sistema de forma segura y controlada.
    
    Proporciona una capa sobre subprocess.run que integra automáticamente 
    el sistema de logging del proyecto para facilitar la trazabilidad de 
    los comandos ejecutados.

    Args:
        cmd (List[str]): Lista de argumentos que componen el comando.
        check (bool): Si es True, lanza una excepción si el comando falla.
        capture_output (bool): Si es True, captura la salida estándar y de error.
        
    Returns:
        subprocess.CompletedProcess: Objeto con el resultado de la ejecución.
        
    Raises:
        subprocess.CalledProcessError: Si el comando falla y check es True.
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


def validate_app_domain(domain: str) -> Tuple[bool, Optional[str]]:
    """
    Valida el dominio de una aplicación.
    
    Args:
        domain: Dominio a validar
        
    Returns:
        Tupla (válido, mensaje de error o None)
    """
    if not domain or not domain.strip():
        return False, "El dominio no puede estar vacuoooo"
    
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
        os.chmod(cred_dir, 0o700)
    except Exception:
        pass
    
    return cred_dir


def load_env_file(env_path: Path) -> dict:
    """
    Carga un archivo .env de forma segura.
    
    Args:
        env_path: Path al archivo .env
        
    Returns:
        Diccionario con las variables de entorno
    """
    if isinstance(env_path, str):
        env_path = Path(env_path)
    
    return core_load_env(str(env_path))


def save_env_file(env_path: Path, variables: dict) -> bool:
    """
    Guarda variables en un archivo .env de forma segura.
    
    Args:
        env_path: Path al archivo .env
        variables: Diccionario de variables
        
    Returns:
        True si se guardó exitosamente
    """
    if isinstance(env_path, str):
        env_path = Path(env_path)
    
    return core_save_env(str(env_path), variables)


# Re-exportar desde módulos core (compatibilidad)
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
    "run_preflight_checks",
    "save_state",
    "load_state",
]