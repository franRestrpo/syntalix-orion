#!/usr/bin/env python3
"""
Syntalix-Orion Bootstrap Selector

Este archivo es el punto de entrada principal. Pregunta al usuario si desea:
- Instalación Local (Docker): Despliega apps en Docker local
- Instalación Remota (Proxmox): Conecta a un servidor Proxmox VE

Uso:
    python main.py

El modo LOCAL es el recomendado para la mayoría de usuarios.
El modo REMOTO requiere configuración de API Proxmox.
"""

import sys
import os
from pathlib import Path

# Agregar scripts al path para imports
SCRIPT_DIR = Path(__file__).parent / "Orion-Python-Ansible" / "scripts"
if SCRIPT_DIR.exists():
    sys.path.insert(0, str(SCRIPT_DIR))

# ASCII Logo
ASCII_LOGO = r"""
   _____                       __ _      
  / ___/ __  ______  / /_ ____ _ / (_) __ __
  \__ \ / / / / __ \/ __// __ `// / / \ \/ /
 ___/ // /_/ / / / / /_ / /_/ // / /  >  <  
/____/ \__, /_/ /_/\__/ \__,_//_/_/ /_/\_\ 
      /____/                               
"""


def print_banner():
    """Imprime el banner de inicio."""
    print(ASCII_LOGO)
    print("Syntalix-Orion V2 - Gestor de Infraestructura")
    print("=" * 50)
    print()


def ask_installation_mode() -> str:
    """
    Pregunta al usuario el modo de instalación.
    
    Returns:
        'local' o 'remote'
    """
    print("Selecciona el modo de instalación:")
    print()
    print("  1) LOCAL   - Docker local (recomendado)")
    print("             Despliega apps en tu servidor Docker")
    print()
    print("  2) REMOTE - Proxmox VE (avanzado)")
    print("             Conecta a un servidor Proxmox remoto")
    print()
    
    while True:
        try:
            choice = input("Opción [1-2]: ").strip()
            if choice in ('1', 'local'):
                return 'local'
            elif choice in ('2', 'remote'):
                return 'remote'
            else:
                print("Por favor, ingresa 1 o 2")
        except (EOFError, KeyboardInterrupt):
            print("\n操作 cancelada.")
            sys.exit(0)


def run_local_mode():
    """Ejecuta la TUI local (Textual UI)."""
    print()
    print("[INFO] Iniciando TUI LOCAL...")
    print()
    
    try:
        from tui import OrionTUI
        from core.logging_config import setup_logging
        
        # Configurar logging
        setup_logging("INFO")
        
        # Ejecutar TUI
        app = OrionTUI()
        app.run()
        
    except ImportError as e:
        print(f"[ERROR] No se pudo importar la TUI: {e}")
        print()
        print("Asegúrate de tener las dependencias instaladas:")
        print("  pip install textual pyyaml pydantic bcrypt jinja2")
        sys.exit(1)
    
    except Exception as e:
        print(f"[ERROR] Error ejecutando la TUI: {e}")
        sys.exit(1)


def run_remote_mode():
    """Ejecuta el modo remoto (Proxmox)."""
    print()
    print("[INFO] Iniciando modo REMOTO...")
    print()
    print("El modo Proxmox requiere:")
    print("  - Dirección IP del servidor Proxmox")
    print("  - Token API de acceso")
    print("  - Usuario con permisos")
    print()
    print("Ejecutando configuración de Proxmox...")
    print()
    
    try:
        from textual.app import App, Screen, ComposeResult
        from textual.containers import Vertical
        from textual.widgets import Button, Input, Static, Header, Footer
        from rich.text import Text
        
        # Importar la app SyntalixApp original
        from main_proxmox import SyntalixApp
        
        # Ejecutar la app de Proxmox
        app = SyntalixApp()
        app.title = "SyntalixApp - Proxmox Mode"
        app.run()
        
    except ImportError as e:
        print(f"[ERROR] No se encontró el módulo Proxmox: {e}")
        sys.exit(1)
    
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        sys.exit(1)


def main():
    """Punto de entrada principal."""
    print_banner()
    
    # Detectar si se pasa argumento de modo
    mode = None
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ('local', '-l', '--local'):
            mode = 'local'
        elif arg in ('remote', '-r', '--remote', 'proxmox'):
            mode = 'remote'
        elif arg in ('--help', '-h'):
            print("Uso: python main.py [local|remote]")
            print()
            print("Opciones:")
            print("  local, -l, --local   Modo Docker local (defecto)")
            print("  remote, -r, --remote Modo Proxmox VE")
            print("  --help, -h           Mostrar esta ayuda")
            sys.exit(0)
    
    # Si no se especificó, preguntar
    if mode is None:
        mode = ask_installation_mode()
    
    # Ejecutar según el modo
    if mode == 'local':
        run_local_mode()
    else:
        run_remote_mode()


if __name__ == "__main__":
    main()