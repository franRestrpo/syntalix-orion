import sys
import asyncio
from pathlib import Path

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical
from textual.widgets import Header, Footer, Static, Button, RichLog

from engine.ansible_runner_real import RealAnsibleRunner

class DeployScreen(Screen):
    """Pantalla final que ejecuta y muestra el despliegue con Ansible."""
    
    BINDINGS = [
        ("ctrl+q", "quit", "Salir"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(classes="p-2"):
            yield Static("## [🚀] Despliegue de Infraestructura", id="deploy-title", markup=True)
            yield Static("", id="deploy-status", markup=True)
            
            yield RichLog(id="ansible-log", highlight=True, auto_scroll=True, classes="mt-2 h-full")
            
            with Vertical(classes="mt-2 align-center"):
                yield Button("Salir", id="quit-button", variant="error", disabled=True)
                
        yield Footer()

    def on_mount(self) -> None:
        # Recuperar el plan del estado
        plan = self.app.state_store.deployment_plan
        if not plan:
            self.notify("No hay un plan de despliegue configurado", severity="error")
            return
            
        status = self.query_one("#deploy-status", Static)
        status.update(f"Desplegando {len(plan.plan)} componentes (RAM estimada: {plan.ram_total_mb}MB)...")
        
        self.call_after_refresh(self._start_deployment)

    def _start_deployment(self) -> None:
        plan = self.app.state_store.deployment_plan
        log_widget = self.query_one("#ansible-log", RichLog)
        log_widget.write("[INFO] Iniciando orquestación con Ansible...")
        
        # Preparar variables
        vars_to_inject = plan.vars_generated.copy()
        
        def on_event(event: dict) -> None:
            # Safely write to UI thread
            msg = event.get("message", str(event))
            if event.get("type") == "done":
                success = event.get("success", False)
                final_msg = "[OK] Despliegue Exitoso" if success else "[ERROR] Despliegue Fallido"
                self.call_from_thread(log_widget.write, f"\n{final_msg}")
                self.call_from_thread(self._enable_quit)
            else:
                self.call_from_thread(log_widget.write, msg)

        runner = RealAnsibleRunner(on_event=on_event, debug=True)
        
        # Ejecutar asíncronamente
        asyncio.create_task(
            runner.run(config=vars_to_inject, modules=plan.plan)
        )

    def _enable_quit(self) -> None:
        quit_btn = self.query_one("#quit-button", Button)
        quit_btn.disabled = False
        status = self.query_one("#deploy-status", Static)
        status.update("Despliegue finalizado.")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit-button":
            self.action_quit()

    def action_quit(self) -> None:
        self.app.exit()
