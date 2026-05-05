"""
Módulo de Gestión de Estado y Persistencia para Syntalix-Orion.

Este módulo centraliza la lógica para persistir y recuperar la configuración de la 
aplicación y el estado del despliegue. Maneja tanto formatos estructurados (JSON) 
como archivos de entorno estándar (.env) utilizados por Ansible y Docker Compose.

Funcionalidades:
    - Guardado y carga del estado global de la sesión.
    - Serialización de variables de entorno a archivos .env.
    - Gestión de permisos de archivos para proteger información sensible.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


STATE_FILE = "state.json"


def save_state(state: Dict[str, Any], path: str = STATE_FILE) -> bool:
    """
    Persiste el estado actual del sistema en un archivo de datos estructurado.
    
    Args:
        state (Dict[str, Any]): Mapa de claves y valores que representan el estado.
        path (str): Ruta absoluta o relativa al archivo de destino.
        
    Returns:
        bool: True si la persistencia en disco se completó correctamente.
    """
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, default=str)
        return True
    except Exception:
        return False


def load_state(path: str = STATE_FILE) -> Dict[str, Any]:
    """
    Recupera el estado persistido previamente desde el almacenamiento.
    
    Args:
        path (str): Ruta al archivo de estado JSON.
        
    Returns:
        Dict[str, Any]: El estado recuperado o un diccionario vacío si el archivo no existe.
    """
    if not Path(path).exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def load_env_file(env_path: str) -> Dict[str, str]:
    """
    Analiza un archivo de entorno (.env) y extrae sus variables activas.
    
    Implementa un filtro para omitir valores nulos o cacheados que podrían corromper 
    la lógica de la interfaz de usuario en re-ejecuciones.

    Args:
        env_path (str): Ruta al archivo de configuración de entorno.
        
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
                        # Si el valor es el string "None" o "null", lo tratamos como vacío para que la TUI lo pida de nuevo
                        if value in ("None", "null", ""):
                            continue
                        env_vars[key] = value
        except Exception:
            pass
    return env_vars


def save_env_file(env_path: str, variables: Dict[str, str]) -> bool:
    """
    Exporta variables de configuración a un archivo compatible con el estándar .env.
    
    Garantiza la seguridad de los datos sensibles en sistemas Unix mediante la 
    aplicación de permisos restrictivos (chmod 600) inmediatamente tras la escritura.

    Args:
        env_path (str): Ruta de destino para el archivo .env.
        variables (Dict[str, str]): Conjunto de variables a exportar.
        
    Returns:
        bool: True si la exportación y el hardening de permisos fueron exitosos.
    """
    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            for key, value in variables.items():
                if value not in (None, "None", "null", ""):
                    f.write(f"{key}={value}\n")
        
        # Establecer permisos restrictivos (solo propietario puede leer/escribir)
        try:
            os.chmod(env_path, 0o600)
        except Exception:
            pass  # Ignorar en Windows
        
        return True
    except Exception:
        return False


__all__ = [
    "save_state",
    "load_state",
    "load_env_file",
    "save_env_file",
]