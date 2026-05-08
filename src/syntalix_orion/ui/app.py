"""
Interfaz de Usuario de Terminal (TUI) - Núcleo de la Aplicación.

Este módulo define la clase principal OrionTUI, construida sobre el framework
Textual para Python. Gestiona el flujo de navegación entre pantallas, el estado
global de la selección de aplicaciones y la orquestación del despliegue visual.

Arquitectura del Módulo:
    - OrionTUI: Aplicación principal que hereda de textual.app.App.
    - Flujo de navegación: Selection -> Config -> Deploy.
    - Estado global: StateStore compartido entre todas las pantallas.

Documentación Técnica:
    El tema CSS global se carga desde 'theme.tcss' y se aplica a toda la
    aplicación. Las pantallas individuales pueden definir CSS_PATH para
    estilos específicos que Textual carga automáticamente desde la ubicación
    del módulo de pantalla.

Uso:
    orion
    o
    python -m syntalix_orion.main

Autor: Syntalix-Orion Team
Versión: 2.0.0
"""

from pathlib import Path

from textual.app import App
from textual.binding import Binding

from syntalix_orion.core.logging_config import get_logger
from syntalix_orion.ui.managers.state_store import StateStore
from syntalix_orion.ui.screens.selection import SelectionScreen
from syntalix_orion.ui.screens.config import ConfigScreen
from syntalix_orion.ui.screens.deploy.deploy_screen import DeployScreen

logger = get_logger(__name__)


def _load_theme_css() -> str:
    """
    Carga el archivo de tema global de la aplicación.

    Returns:
        str: Contenido del archivo theme.tcss si existe, cadena vacía otherwise.
    """
    theme_path = Path(__file__).parent / "theme.tcss"
    if theme_path.exists():
        return theme_path.read_text()
    return ""


class OrionTUI(App):
    """
    Aplicación Principal de la TUI de Syntalix-Orion.

    Esta clase orquesta el flujo visual de tres fases:
        1. Selección de aplicaciones del catálogo.
        2. Configuración de variables y parámetros.
        3. Despliegue y monitoreo mediante Ansible.

    Atributos:
        state_store (StateStore): Almacén de estado global compartido entre
            todas las pantallas de la aplicación.

    Herencia:
        textual.app.App: Clase base del framework Textual.

    Ejemplo:
        >>> app = OrionTUI()
        >>> app.run()
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
        """
        Inicializa la aplicación OrionTUI.

        Args:
            *args: Argumentos variables传递给 textual.app.App.
            **kwargs: Argumentos de palabra clave传递给 la clase base.
        """
        super().__init__(*args, **kwargs)
        self.state_store = StateStore()
        logger.info("OrionTUI inicializada con tema nuevo")

    def on_mount(self) -> None:
        """Callback invoked cuando la aplicación se monta en la terminal."""
        self.push_screen("selection")

    def on_selection_screen_selection_complete(self, message: SelectionScreen.SelectionComplete) -> None:
        """
        Maneja el evento de selección completada en SelectionScreen.

        Args:
            message: Mensaje de tipo SelectionComplete con los datos de la selección.
        """
        self.push_screen("config")

    def on_config_screen_config_complete(self, message: ConfigScreen.ConfigComplete) -> None:
        """
        Maneja el evento de configuración completada en ConfigScreen.

        Args:
            message: Mensaje de tipo ConfigComplete con los datos de configuración.
        """
        self.push_screen("deploy")

    def on_config_screen_config_back(self, message: ConfigScreen.ConfigBack) -> None:
        """
        Maneja el evento de retroceso en ConfigScreen.

        Args:
            message: Mensaje de tipo ConfigBack que indica navegación hacia atrás.
        """
        self.pop_screen()