"""
Pantalla de Despliegue y Monitoreo - Syntalix-Orion.

Esta pantalla muestra el progreso del despliegue de aplicaciones mediante
Ansible, incluyendo logs en tiempo real y estado de cada componente.

Autor: Syntalix-Orion Team
Versin: 2.0.0
"""

from textual import work
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, VerticalScroll, Horizontal
from textual.widgets import Header, Footer, Static, Button
from textual.message import Message

from syntalix_orion.core.logging_config import get_logger
from syntalix_orion.engine import get_runner
from syntalix_orion.core.state_repository import StateRepository

logger = get_logger(__name__)


class DeployScreen(Screen):
    """
    Pantalla de Monitoreo de Despliegue.

    Muestra el progreso de la ejecucin de Ansible y permite al usuario
    visualizar los logs del proceso de despliegue en tiempo real.
    """

    CSS_PATH = "deploy_screen.tcss"

    BINDINGS = [
        ("ctrl+b", "back", "Atrs"),
    ]

    class DeployComplete(Message):
        """Mensaje emitido cuando el despliegue se completa exitosamente."""

    class DeployFailed(Message):
        """Mensaje emitido cuando el despliegue falla."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.deployment_success = False
        self._log_lines = []

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main-container"):
            with VerticalScroll(id="log-panel"):
                yield Static("?? MONITOR DE DESPLIEGUE", classes="section-title")
                yield Static(id="deployment-status", markup=True)
                with VerticalScroll(id="log-container"):
                    yield Static(id="ansible-log", classes="log-output")
            with Vertical(id="status-panel"):
                yield Static("?? ESTADO DEL CLSTER", classes="section-title")
                yield Static(id="cluster-status", markup=True)
                with Vertical(id="action-container"):
                    yield Button("? Volver", id="back-button", variant="default", classes="btn-back")
                    yield Button("? Finalizar", id="finish-button", variant="success", classes="btn-success")
        yield Footer()

    def on_mount(self) -> None:
        status = self.query_one("#deployment-status", Static)
        status.update("[b]Iniciando despliegue...[/b]")
        self._run_deployment()

    def _update_log_ui(self, msg: str) -> None:
        self._log_lines.append(msg)
        if len(self._log_lines) > 200:
            self._log_lines.pop(0)
            
        log = self.query_one("#ansible-log", Static)
        log.update("\n".join(self._log_lines))
        
        container = self.query_one("#log-container", VerticalScroll)
        container.scroll_end(animate=False)

    def _process_runner_event(self, event: dict) -> None:
        status_widget = self.query_one("#cluster-status", Static)
        etype = event.get("type")
        
        if etype == "log":
            level = event.get("level", "info")
            msg = event.get("message", "")
            if level == "error":
                self._update_log_ui(f"[red]{msg}[/red]")
            elif level == "warning":
                self._update_log_ui(f"[yellow]{msg}[/yellow]")
            elif level == "debug":
                self._update_log_ui(f"[dim]{msg}[/dim]")
            else:
                self._update_log_ui(msg)
        elif etype == "progress":
            val = event.get("value", 0)
            status_widget.update(f"Progreso de Ansible: {val}%")
        elif etype == "done":
            success = event.get("success", False)
            if success:
                self.deployment_success = True
                self._update_log_ui("\n[bold green]??? DESPLIEGUE FINALIZADO EXITOSAMENTE ???[/bold green]")
                status_widget.update("[bold green]Cluster Operativo[/bold green]")
            else:
                self._update_log_ui("\n[bold red]??? EL DESPLIEGUE FALL ???[/bold red]")
                status_widget.update("[bold red]Fallo en el Cluster[/bold red]")
            
            status = self.query_one("#deployment-status", Static)
            status.update("[b]Despliegue finalizado.[/b]")

    @work(exclusive=True, thread=True)
    async def _run_deployment(self) -> None:
        self.app.call_from_thread(self._update_log_ui, "[dim]Preparando plan de ejecucin...[/dim]")
        
        plan = self.app.state_store.deployment_plan
        if not plan:
            self.app.call_from_thread(self._update_log_ui, "[red]Error: No hay plan de despliegue definido.[/red]")
            return

        try:
            self.app.call_from_thread(self._update_log_ui, "[blue]Guardando configuraciones y secretos (Idempotencia)...[/blue]")
            repo = StateRepository()
            repo.save_full_state(
                selected_apps=list(self.app.state_store.selected_apps),
                env_vars=plan.vars_generated,
                auto_dependencies=plan.dependencies
            )
            self.app.call_from_thread(self._update_log_ui, "[green]Estado local persistido correctamente.[/green]")
        except Exception as e:
            self.app.call_from_thread(self._update_log_ui, f"[red]Error crtico guardando el estado: {e}[/red]")
            return

        self.app.call_from_thread(self._update_log_ui, "[blue]Iniciando motor de orquestacin Ansible...[/blue]")
        
        def on_event(event):
            self.app.call_from_thread(self._process_runner_event, event)
            
        runner = get_runner(on_event=on_event)
        
        try:
            await runner.run(
                config=plan.vars_generated,
                modules=plan.plan
            )
        except Exception as e:
            self.app.call_from_thread(self._update_log_ui, f"[red]Excepcin fatal en ejecucin de Ansible: {e}[/red]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-button":
            self.post_message(self.app.on_config_screen_config_back)
        elif event.button.id == "finish-button":
            self.post_message(self.DeployComplete())

    def action_back(self) -> None:
        self.post_message(self.DeployComplete())
