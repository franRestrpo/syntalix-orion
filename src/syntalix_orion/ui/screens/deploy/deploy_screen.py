"""
Pantalla de Despliegue y Monitoreo - Syntalix-Orion.

Esta pantalla muestra el progreso del despliegue de aplicaciones mediante
Ansible, incluyendo logs en tiempo real y estado de cada componente.

Autor: Syntalix-Orion Team
Versión: 2.0.0
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, VerticalScroll, Horizontal
from textual.widgets import Header, Footer, Static, Button
from textual.message import Message

from syntalix_orion.core.logging_config import get_logger

logger = get_logger(__name__)


class DeployScreen(Screen):
    """
    Pantalla de Monitoreo de Despliegue.

    Muestra el progreso de la ejecución de Ansible y permite al usuario
    visualizar los logs del proceso de despliegue en tiempo real.
    """

    CSS_PATH = "deploy/deploy_screen.tcss"

    BINDINGS = [
        ("ctrl+b", "back", "Atrás"),
    ]

    class DeployComplete(Message):
        """Mensaje emitido cuando el despliegue se completa exitosamente."""

    class DeployFailed(Message):
        """Mensaje emitido cuando el despliegue falla."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.deployment_success = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main-container"):
            with VerticalScroll(id="log-panel"):
                yield Static("📦 MONITOR DE DESPLIEGUE", classes="section-title")
                yield Static(id="deployment-status", markup=True)
                with VerticalScroll(id="log-container"):
                    yield Static(id="ansible-log", classes="log-output")
            with Vertical(id="status-panel"):
                yield Static("📊 ESTADO DEL CLÚSTER", classes="section-title")
                yield Static(id="cluster-status", markup=True)
                with Vertical(id="action-container"):
                    yield Button("⬅ Volver", id="back-button", variant="default", classes="btn-back")
                    yield Button("✔ Finalizar", id="finish-button", variant="success", classes="btn-success")
        yield Footer()

    def on_mount(self) -> None:
        status = self.query_one("#deployment-status", Static)
        status.update("[b]Iniciando despliegue...[/b]")
        self._run_deployment()

    def _run_deployment(self) -> None:
        log = self.query_one("#ansible-log", Static)
        log.update("[dim]Esperando configuración del plan...[/dim]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-button":
            self.post_message(self.app.on_config_screen_config_back)
        elif event.button.id == "finish-button":
            self.post_message(self.DeployComplete())

    def action_back(self) -> None:
        self.post_message(self.DeployComplete())