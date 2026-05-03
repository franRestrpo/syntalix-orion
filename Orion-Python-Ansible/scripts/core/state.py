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
    Guarda el estado en un archivo JSON.
    
    Args:
        state: Diccionario con el estado a guardar
        path: Ruta del archivo (por defecto: state.json)
        
    Returns:
        True si se guardó exitosamente
    """
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, default=str)
        return True
    except Exception:
        return False


def load_state(path: str = STATE_FILE) -> Dict[str, Any]:
    """
    Carga el estado desde un archivo JSON.
    
    Args:
        path: Ruta del archivo (por defecto: state.json)
        
    Returns:
        Diccionario con el estado, o dict vacío si no existe
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
    Lee un archivo .env y devuelve un diccionario de variables.
    Ignora los valores 'None', 'null' o vacíos que puedan haber quedado
    cacheados por despliegues fallidos.
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
    Persiste un conjunto de variables en un archivo de formato .env.
    
    Escribe el archivo siguiendo el estándar KEY=VALUE. En sistemas tipo Unix, 
    aplica automáticamente permisos restrictivos (600) para proteger secretos.

    Args:
        env_path (str): Ruta completa donde se creará el archivo .env.
        variables (Dict[str, str]): Diccionario de pares clave-valor a escribir.
        
    Returns:
        bool: True si la operación de escritura y ajuste de permisos fue exitosa.
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