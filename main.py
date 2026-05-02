#!/usr/bin/env python3
"""
Selector de Arranque (Bootstrap) de Syntalix-Orion.

Este archivo constituye el punto de entrada unificado para todo el ecosistema 
Syntalix-Orion V2. Su función principal es actuar como orquestador de inicio, 
permitiendo al usuario seleccionar entre los dos modos principales de operación:

    1. Modo Local (Docker): Diseñado para el despliegue rápido de la pila de 
       aplicaciones en un servidor Docker ya existente o en la máquina local.
       Es el modo recomendado para soberanía digital personal.

    2. Modo Remoto (Proxmox): Orientado a entornos de infraestructura como 
       código (IaC) avanzados, permitiendo la gestión de VMs y contenedores 
       en nodos Proxmox VE.

El script maneja la inyección de rutas de sistema para los módulos internos y 
proporciona una interfaz de línea de comandos amigable.
"""

import sys
import os
from pathlib import Path

# Configuración dinámica del PATH para asegurar la importación de módulos internos
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
    Presenta una interfaz interactiva para la selección del modo de instalación.
    
    Captura la entrada del usuario y valida que la opción seleccionada sea 
    legal ('local' o 'remote'). Implementa manejo de interrupciones de teclado 
    para una salida limpia.

    Returns:
        str: 'local' para despliegue Docker, 'remote' para despliegue Proxmox.
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
    """
    Inicializa y lanza la Terminal User Interface (TUI) para el modo local.
    
    Este método realiza la carga diferida de los módulos de Textual UI y 
    configura el sistema de logging antes de ceder el control al motor 
    de la interfaz OrionTUI.
    """
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
    """
    Función principal que orquesta el flujo de arranque del sistema.
    
    Procesa los argumentos de la línea de comandos (CLI) para permitir el 
    inicio desatendido o muestra el menú de selección si no se proporcionan 
    parámetros.
    """
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