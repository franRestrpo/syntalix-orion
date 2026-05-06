"""
Módulo de Gestión de Estado y Persistencia para Syntalix-Orion.

Este módulo centraliza la lógica para persistir y recuperar la configuración de la
aplicación y el estado del despliegue. Maneja tanto formatos estructurados (JSON)
como archivos de entorno estándar (.env) utilizados por Ansible y Docker Compose.

Funcionalidades:
    - Guardado y carga del estado global de la sesión.
    - Serialización de variables de entorno a archivos .env.
    - Gestión de permisos de archivos para proteger información sensible.
    - Protocolo Write-and-Verify para contraseñas de Category C.
    - Sanitización automática de valores antes de persistir.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from core.logging_config import get_logger
from core.security import validate_password_strength, sanitize_input, get_password_category, PasswordCategory

logger = get_logger(__name__)

STATE_FILE = "state.json"
SECRETS_DIR = "secrets"


class PasswordPersistenceError(Exception):
    """Excepción crítica cuando la verificación de contraseña falla."""
    pass


def get_secrets_dir() -> Path:
    """
    Obtiene la ruta absoluta al directorio de secretos.

    Returns:
        Path: Ruta al directorio secrets/ en la raíz del proyecto.
    """
    return Path(__file__).parent.parent.parent / SECRETS_DIR


def ensure_secrets_dir() -> bool:
    """
    Asegura que el directorio secrets/ exista con permisos restrictivos (chmod 700).

    Returns:
        bool: True si el directorio existe o fue creado exitosamente.
    """
    secrets_path = get_secrets_dir()
    try:
        secrets_path.mkdir(exist_ok=True)
        os.chmod(secrets_path, 0o700)
        logger.info("Directorio secrets/ verificado con permisos 700")
        return True
    except Exception as e:
        logger.error(f"No se pudo crear/configurar el directorio secrets/: {e}")
        return False


def save_state(state: Dict[str, Any], path: str = STATE_FILE) -> bool:
    """
    Persiste el estado actual del sistema en un archivo de datos estructurado.

    Args:
        state: Mapa de claves y valores que representan el estado.
        path: Ruta absoluta o relativa al archivo de destino.

    Returns:
        bool: True si la persistencia en disco se completó correctamente.
    """
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, default=str)
        return True
    except Exception as e:
        logger.error(f"Error al guardar el estado en {path}: {e}")
        return False


def load_state(path: str = STATE_FILE) -> Dict[str, Any]:
    """
    Recupera el estado persistido previamente desde el almacenamiento.

    Args:
        path: Ruta al archivo de estado JSON.

    Returns:
        Dict[str, Any]: El estado recuperado o un diccionario vacío si el archivo no existe.
    """
    if not Path(path).exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error al cargar el estado desde {path}: {e}")
        return {}


def load_env_file(env_path: str) -> Dict[str, str]:
    """
    Analiza un archivo de entorno (.env) y extrae sus variables activas.

    Implementa un filtro para omitir valores nulos o cacheados que podrían corromper
    la lógica de la interfaz de usuario en re-ejecuciones.

    Args:
        env_path: Ruta al archivo de configuración de entorno.

    Returns:
        Dict[str, str]: Mapeo de variables detectadas con valores válidos.
    """
    env_vars: Dict[str, str] = {}
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        if value in ("None", "null", ""):
                            continue
                        env_vars[key] = value
        except Exception as e:
            logger.error(f"Error al leer el archivo .env en {env_path}: {e}")
    return env_vars


def get_main_env_path() -> str:
    """
    Obtiene la ruta al archivo principal de variables de entorno (.env).

    Este archivo ahora se almacena en el directorio secrets/ para proteger
    la información sensible.

    Returns:
        str: Ruta completa al archivo .env en secrets/.
    """
    return str(get_secrets_dir() / ".env")


def _is_user_facing_var(key: str) -> bool:
    """
    Determina si una clave de variable corresponde a una aplicación con UI
    donde el usuario ingresa la contraseña directamente.

    Args:
        key: Clave de variable (ej: TRAEFIK__PASSWORD)

    Returns:
        bool: True si es una variable de Category C.
    """
    user_facing_patterns = [
        "GRAFANA__PASSWORD",
        "PORTAINER__PASSWORD",
        "AUTHENTIK__PASSWORD",
        "CHATWOOT__PASSWORD",
    ]
    return key in user_facing_patterns


def save_env_file(env_path: str, variables: Dict[str, str], skip_verify: bool = False) -> bool:
    """
    Exporta variables de configuración a un archivo compatible con el estándar .env.

    Implementa el protocolo Write-and-Verify para contraseñas de Category C:
        1. Sanitiza valores (trim espacios)
        2. Para Category C: Valida fortaleza antes de persistir
        3. Escribe archivo con chmod 600
        4. Verifica leyendo desde disco y comparando con memoria

    Args:
        env_path: Ruta de destino para el archivo .env.
        variables: Conjunto de variables a exportar.
        skip_verify: Si True, omite la verificación (para testing).

    Returns:
        bool: True si la exportación y verificación fueron exitosas.

    Raises:
        PasswordPersistenceError: Si la verificación falla para Category C.
    """
    ensure_secrets_dir()

    processed_vars: Dict[str, str] = {}

    for key, value in variables.items():
        if value in (None, "None", "null", ""):
            continue

        sanitized = sanitize_input(str(value))

        if _is_user_facing_var(key):
            is_valid, error_msg = validate_password_strength(sanitized)
            if not is_valid:
                logger.error(f"Validación de fortaleza fallida para {key}: {error_msg}")
                raise PasswordPersistenceError(f"Contraseña inválida para {key}: {error_msg}")

            logger.info(f"Category C password validado para {key}")

        processed_vars[key] = sanitized

    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            for key, value in processed_vars.items():
                f.write(f"{key}={value}\n")

        try:
            os.chmod(env_path, 0o600)
        except Exception as e:
            logger.warning(f"No se pudieron establecer permisos restrictivos en {env_path}: {e}")

        if not skip_verify:
            verified_vars = load_env_file(env_path)
            for key, value in processed_vars.items():
                disk_value = verified_vars.get(key)
                if disk_value != value:
                    error_msg = f"Verificación fallida para {key}: memoria='{value}' disco='{disk_value}'"
                    logger.error(error_msg)
                    raise PasswordPersistenceError(error_msg)

        logger.info(f"Archivo .env verificado exitosamente en {env_path}")
        return True

    except PasswordPersistenceError:
        raise
    except Exception as e:
        logger.error(f"Error al guardar el archivo .env en {env_path}: {e}")
        return False


def save_password_verified(env_path: str, key: str, value: str) -> bool:
    """
    Persiste una única contraseña con verificación completa.

   专门para Category C (aplicaciones con UI como Traefik).

    Args:
        env_path: Ruta al archivo .env.
        key: Nombre de la variable.
        value: Valor de la contraseña.

    Returns:
        bool: True si la persistencia y verificación fueron exitosas.

    Raises:
        PasswordPersistenceError: Si la validación o verificación falla.
    """
    is_valid, error_msg = validate_password_strength(value)
    if not is_valid:
        raise PasswordPersistenceError(f"Contraseña inválida para {key}: {error_msg}")

    all_vars = load_env_file(env_path)
    all_vars[key] = value

    return save_env_file(env_path, all_vars)


__all__ = [
    "save_state",
    "load_state",
    "load_env_file",
    "save_env_file",
    "save_password_verified",
    "get_secrets_dir",
    "ensure_secrets_dir",
    "get_main_env_path",
    "PasswordPersistenceError",
]