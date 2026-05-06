"""
Interfaz de Usuario de Terminal (TUI) - Núcleo de la Aplicación.

Este módulo define la clase principal OrionTUI, construida sobre el framework 
Textual. Gestiona el flujo de navegación entre pantallas, el estado global 
de la selección de aplicaciones y la orquestación del despliegue visual.
"""

import sys
from pathlib import Path
import sys

from textual.app import App
from textual.binding import Binding

SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from core.logging_config import get_logger
from ui.managers.state_store import StateStore
from ui.screens.selection import SelectionScreen
from ui.screens.config import ConfigScreen
from ui.screens.deploy.deploy_screen import DeployScreen

logger = get_logger(__name__)

def _load_theme_css() -> str:
    theme_path = SCRIPT_DIR / "theme.tcss"
    if theme_path.exists():
        return theme_path.read_text()
    return ""

class OrionTUI(App):
    """
    Aplicación Principal de la TUI de Syntalix-Orion.
    
    Orquestador visual que guía al usuario a través del proceso de:
    1. Selección de aplicaciones y módulos de infraestructura.
    2. Configuración de parámetros y variables de entorno.
    3. Ejecución y monitoreo en tiempo real del despliegue mediante Ansible.
    """
    CSS = _load_theme_css()

    SCREENS = {
        "selection": SelectionScreen,
        "config": ConfigScreen,
        "deploy": DeployScreen,
    }

    BINDINGS = [
        Binding("ctrl+c", "quit", "Salir Fuerte", show=False),
    ]

    TITLE = "◉ Syntalix-Orion V2"
    SUB_TITLE = "Gestor de Despliegue de Infraestructura"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.state_store = StateStore()
        logger.info("OrionTUI inicializada con tema nuevo")

    def on_mount(self) -> None:
        self.push_screen("selection")

    def on_selection_screen_selection_complete(self, message: SelectionScreen.SelectionComplete) -> None:
        self.push_screen("config")

    def on_config_screen_config_complete(self, message: ConfigScreen.ConfigComplete) -> None:
        self.push_screen("deploy")

    def on_config_screen_config_back(self, message: ConfigScreen.ConfigBack) -> None:
        self.pop_screen()