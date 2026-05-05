#!/usr/bin/env python3
"""
Orquestador de Arranque (Bootstrap) - Syntalix-Orion V2.

Punto de entrada unificado para la gestión de infraestructura. Este script 
actúa como el controlador principal para el inicio de la plataforma.

Modos de Operación:
    - Modo Local (Docker): Optimizado para despliegues rápidos y soberanía 
      digital en servidores Linux estándar o máquinas locales.

Características:
    - Inyección dinámica de dependencias en el sistema de rutas de Python.
    - Interfaz de línea de comandos (CLI) con soporte para argumentos.
    - Validación de prerrequisitos de entorno antes de la ejecución.
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
    legal ('local'). Implementa manejo de interrupciones de teclado 
    para una salida limpia.

    Returns:
        str: 'local' para despliegue Docker.
    """
    print("Selecciona el modo de instalación:")
    print()
    print("  1) LOCAL   - Docker local (recomendado)")
    print("             Despliega apps en tu servidor Docker")
    print()
    
    while True:
        try:
            choice = input("Opción [1]: ").strip()
            if choice in ('1', 'local', ''):
                return 'local'
            else:
                print("Por favor, ingresa 1 o pulsa Enter para LOCAL")
        except (EOFError, KeyboardInterrupt):
            print("\nOperación cancelada.")
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
        elif arg in ('--help', '-h'):
            print("Uso: python main.py [local]")
            print()
            print("Opciones:")
            print("  local, -l, --local   Modo Docker local (defecto)")
            print("  --help, -h           Mostrar esta ayuda")
            sys.exit(0)
    
    # Si no se especificó, preguntar
    if mode is None:
        mode = ask_installation_mode()
    
    # Ejecutar modo local (único soportado en V2)
    run_local_mode()


if __name__ == "__main__":
    main()