"""
Pantalla de Ejecución de Despliegue - Syntalix-Orion.

Orquesta la fase final del proceso, comunicándose con el motor de Ansible para 
aplicar la configuración en el clúster. Proporciona retroalimentación en 
tiempo real a través de un log enriquecido y gestiona la persistencia del estado.
"""

import sys
import os
import asyncio
from pathlib import Path

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Header, Footer, Static, Button, RichLog

from engine.ansible_runner_real import RealAnsibleRunner
from core.state import save_env_file
from core.logging_config import get_logger

logger = get_logger(__name__)

from textual import work

class DeployScreen(Screen):
    """
    Monitor de Ejecución y Orquestación.
    
    Responsable de:
    1. Persistir las variables finales en el archivo de entorno seguro.
    2. Lanzar el proceso de Ansible en un hilo dedicado.
    3. Capturar y visualizar los eventos de la ejecución para el usuario.
    """
    CSS = """
    Screen { background: #0D1117; }
    
    #main-layout { 
        height: 100%; 
        border: tall #00D9FF;
        margin: 1 2;
        padding: 1 2;
        background: #0D1117;
    }
    
    .section-title { 
        text-style: bold; 
        color: #00D9FF; 
        margin-bottom: 1;
    }
    
    #deploy-status { 
        color: #8B949E; 
        margin-bottom: 1; 
        text-style: italic; 
    }
    
    #log-container {
        height: 1fr;
        overflow: hidden;
    }

    #ansible-log {
        height: 100%;
        width: 100%;
        overflow-y: auto;
        overflow-x: hidden;
        background: #161B22;
        color: #E6EDF3;
    }
    
    #action-container { 
        height: auto; 
        align: center middle; 
    }
    
    .btn-error { 
        background: #EF4444; 
        color: #FFFFFF; 
        text-style: bold; 
        width: 100%; 
        height: 3; 
    }
    
    .log-success { color: #10B981; }
    .log-error { color: #EF4444; }
    .log-info { color: #38BDF8; }
    .log-warning { color: #F59E0B; }
    """

    BINDINGS = [
        ("ctrl+q", "quit", "Salir"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="main-layout"):
            yield Static("🚀 DESPLIEGUE DE INFRAESTRUCTURA", classes="section-title")
            yield Static("", id="deploy-status")
            
            with VerticalScroll(id="log-container"):
                yield RichLog(id="ansible-log", highlight=True, auto_scroll=True, can_focus=True)

            with Vertical(id="action-container"):
                yield Button("CERRAR Y SALIR", id="quit-button", variant="error", disabled=True, classes="btn-error")
        yield Footer()

    def on_mount(self) -> None:
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

        vars_to_inject = plan.vars_generated.copy()

        env_file_path = str(Path.cwd() / ".env")
        if save_env_file(env_file_path, vars_to_inject):
            try:
                os.chmod(env_file_path, 0o600)
                logger.info("Validación exitosa. Archivo .env guardado de forma segura con permisos 600.")
                log_widget.write("[SECURE] Archivo .env guardado de forma segura.")
            except Exception as e:
                logger.warning(f"No se pudieron establecer los permisos 600: {e}")
        else:
            logger.error("Fallo al guardar el archivo .env")
            log_widget.write("[ERROR] Fallo al persistir el archivo .env de forma segura.")

        self.run_ansible_thread(vars_to_inject, plan.plan)

    @work(thread=True)
    def run_ansible_thread(self, vars_to_inject: dict, modules: list) -> None:
        log_widget = self.query_one("#ansible-log", RichLog)

        def on_event(event: dict) -> None:
            msg = event.get("message", str(event))
            if event.get("type") == "done":
                success = event.get("success", False)
                final_msg = "[OK] Despliegue Exitoso" if success else "[ERROR] Despliegue Fallido"
                style = "log-success" if success else "log-error"
                self.call_from_thread(log_widget.write, f"\n{final_msg}", style=style)
                self.call_from_thread(self._enable_quit)
            else:
                style = "log-info"
                if "[ERROR]" in msg or "[FATAL]" in msg:
                    style = "log-error"
                elif "[WARNING]" in msg or "[WARN]" in msg or "WARNING" in msg:
                    style = "log-warning"
                self.call_from_thread(log_widget.write, msg, style=style)

        runner = RealAnsibleRunner(on_event=on_event, debug=True)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(runner.run(config=vars_to_inject, modules=modules))
        except Exception as e:
            on_event({"type": "log", "message": f"Error fatal en el thread: {e}"})
            on_event({"type": "done", "success": False})
        finally:
            loop.close()

    def _enable_quit(self) -> None:
        quit_btn = self.query_one("#quit-button", Button)
        quit_btn.disabled = False
        status = self.query_one("#deploy-status", Static)
        status.update("✓ Despliegue finalizado.")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit-button":
            self.action_quit()

    def action_quit(self) -> None:
        self.app.exit()