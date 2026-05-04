import sys
from pathlib import Path

from textual.app import App
from textual.binding import Binding

from core.logging_config import get_logger
from ui.managers.state_store import StateStore
from ui.screens.selection import SelectionScreen
from ui.screens.config import ConfigScreen
from ui.screens.deploy import DeployScreen
from ui.styles.theme import THEME

logger = get_logger(__name__)

class OrionTUI(App):
    CSS = """
    Screen { background: #0D1117; }

    Header { background: #161B22; }
    Header > Static { color: #00D9FF; text-style: bold; }

    Footer { background: #161B22; }
    Footer > Static { color: #6E7681; }

    #main-container { height: 100%; layout: horizontal; }
    #left-panel { width: 50%; height: 100%; border-right: solid #00D9FF; padding: 1 2; }
    #right-panel { width: 50%; height: 100%; padding: 1 2; }

    Button { margin: 1 0; }
    Button:hover { background: #00D9FF; color: #0D1117; }
    Button:focus { background: #00D9FF; color: #0D1117; border: solid #FFFFFF; }

    #status-display { border: solid #21262D; background: #161B22; }
    .p-2 { padding: 2; }
    .mt-2 { margin-top: 2; }
    """

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