import sys
from pathlib import Path

from textual.app import App
from textual.binding import Binding

from core.logging_config import get_logger
from ui.managers.state_store import StateStore
from ui.screens.selection import SelectionScreen
from ui.screens.config import ConfigScreen
from ui.screens.deploy import DeployScreen

logger = get_logger(__name__)

class OrionTUI(App):
    """
    Aplicación principal Textual.
    Responsabilidad: Inicialización global, enrutamiento entre pantallas y gestión de estado.
    """
    
    # CSS base minimalista
    CSS = """
    Screen { background: $surface; }
    .category-header { text-style: bold; color: $accent; margin-top: 1; padding: 0 1; }
    .form-label { margin-top: 1; text-style: bold; }
    #main-container { height: 100%; layout: horizontal; }
    #left-panel { width: 45%; height: 100%; border-right: solid $primary; padding: 1 2; }
    #right-panel { width: 55%; height: 100%; padding: 1 2; }
    #status-display { height: 60%; padding: 1; border: solid $primary; margin-bottom: 1; }
    #action-container { height: auto; align: center bottom; padding: 1; }
    """

    SCREENS = {
        "selection": SelectionScreen,
        "config": ConfigScreen,
        "deploy": DeployScreen,
    }

    BINDINGS = [
        Binding("ctrl+c", "quit", "Salir Fuerte", show=False),
    ]

    TITLE = "[RUN] Syntalix-Orion V2"
    SUB_TITLE = "Gestor de Despliegue de Infraestructura"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.state_store = StateStore()
        logger.info("OrionTUI inicializada")

    def on_mount(self) -> None:
        self.push_screen("selection")

    def on_selection_screen_selection_complete(self, message: SelectionScreen.SelectionComplete) -> None:
        """Navega a ConfigScreen cuando se completa la selección."""
        self.push_screen("config")

    def on_config_screen_config_complete(self, message: ConfigScreen.ConfigComplete) -> None:
        """Navega a DeployScreen cuando se aprueba el plan y variables."""
        self.push_screen("deploy")
        
    def on_config_screen_config_back(self, message: ConfigScreen.ConfigBack) -> None:
        """Vuelve a la selección de aplicaciones."""
        self.pop_screen()
