#!/usr/bin/env python3
"""
Punto de entrada para la Interfaz de Usuario de Terminal (TUI) de Syntalix-Orion V2.

Este script ahora delega la inicialización y el ciclo de vida a la aplicación
estructurada en el paquete `ui`.
"""

import sys
from pathlib import Path

# Configurar el PATH para incluir la raíz del proyecto
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SCRIPT_DIR))

from core.logging_config import setup_logging, get_logger
from ui.app import OrionTUI

def main() -> None:
    """
    Punto de entrada principal para la TUI refactorizada.
    """
    setup_logging("INFO")
    logger = get_logger(__name__)

    logger.info("=" * 60)
    logger.info("Iniciando Syntalix-Orion TUI v2.0 (Refactored)")
    logger.info("=" * 60)

    try:
        app = OrionTUI()
        app.run()
    except KeyboardInterrupt:
        logger.info("Aplicación interrumpida por el usuario")
    except Exception as e:
        logger.error(f"Error fatal: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Aplicación finalizada")

if __name__ == "__main__":
    main()
