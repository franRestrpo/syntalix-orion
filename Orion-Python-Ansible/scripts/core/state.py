"""
Módulo unificado de gestión de estado para Syntalix-Orion.

Proporciona:
- Persistencia de estado en JSON
- Carga/guardado de configuración
- Manejo de archivos .env

Este módulo unifica las funciones dispersas en main.py y config.py.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from configparser import ConfigParser


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
    
    Args:
        env_path: Ruta al archivo .env
        
    Returns:
        Diccionario con las variables del entorno
    """
    env_vars: Dict[str, str] = {}
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        except Exception:
            pass
    return env_vars


def save_env_file(env_path: str, variables: Dict[str, str]) -> bool:
    """
    Guarda variables en un archivo .env de forma segura.
    
    Args:
        env_path: Ruta al archivo .env
        variables: Diccionario de variables a guardar
        
    Returns:
        True si se guardó exitosamente
    """
    try:
        config = ConfigParser()
        config.read_dict({'DEFAULT': variables})
        
        with open(env_path, 'w', encoding='utf-8') as f:
            config.write(f)
        
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