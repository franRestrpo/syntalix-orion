#!/usr/bin/env python3
"""
Orquestador de Arranque (Bootstrap) - Syntalix-Orion V2.

Punto de entrada unificado para la gestión de infraestructura. Este script
actúa como el controlador principal para el inicio de la plataforma.

Modos de Operación:
    - Modo Local (Docker): Optimizado para despliegues rápidos y soberanía
      digital en servidores Linux estándar o máquinas locales.

Características:
    - Interfaz de línea de comandos (CLI) con soporte para argumentos.
    - Validación de prerrequisitos de entorno antes de la ejecución.
    - Imports absolutos desde el paquete syntalix_orion.
"""

import sys


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
        from syntalix_orion.ui.app import OrionTUI
        from syntalix_orion.core.logging_config import setup_logging

        setup_logging("INFO")

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

    En V2 solo existe el modo local, así que se ejecuta directamente.
    """
    print_banner()

    run_local_mode()


if __name__ == "__main__":
    main()