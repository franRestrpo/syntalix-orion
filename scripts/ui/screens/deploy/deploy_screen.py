"""
Pantalla de Ejecución de Despliegue - Syntalix-Orion.

Representa la tercera y última fase del flujo de despliegue de infraestructura.
Se comunica con el motor de Ansible (RealAnsibleRunner) para aplicar la
configuración en el clúster Docker Swarm y proporciona retroalimentación
en tiempo real a través de un widget RichLog con auto-scroll.

Componentes Principales:
    - RichLog: Widget de Textual para visualizar logs con soporte ANSI.
    - VerticalScroll: Contenedor con scroll vertical para el área de logs.
    - RealAnsibleRunner: Motor de ejecución de playbooks en hilo separado.

Flujo de Datos:
    1. Recupera el DeploymentPlan desde StateStore.
    2. Persiste variables en archivo .env con permisos 0o600.
    3. Lanza RealAnsibleRunner en un @work thread.
    4. Los eventos de Ansible se transmiten vía callback thread-safe.

Arquitectura de Hilos:
    El playbook de Ansible se ejecuta en un hilo separado (@work) para no
    bloquear la interfaz. Los eventos se publican mediante call_from_thread()
    garantizando thread-safety con el hilo principal de Textual.

Autor: Syntalix-Orion Team
Versión: 2.0.0
"""

import os
import asyncio
from pathlib import Path

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Header, Footer, Static, Button, RichLog

from engine.ansible_runner_real import RealAnsibleRunner
from core.state import save_env_file, get_main_env_path, PasswordPersistenceError
from core.logging_config import get_logger

logger = get_logger(__name__)

from textual import work


class DeployScreen(Screen):
    """
    Monitor de Ejecución y Orquestación de Despliegue.

    Esta pantalla es responsable de:
        1. Persistir las variables finales en archivo .env seguro.
        2. Lanzar el proceso de Ansible en hilo dedicado (@work).
        3. Capturar y visualizar eventos de ejecución en RichLog.
        4. Habilitar el botón de salida tras completarse el despliegue.

    Atributos:
        CSS_PATH (str): Ruta relativa al archivo CSS específico de la pantalla.

    Señales/Mensajes:
        No emite mensajes; comunica con OrionTUI mediante callbacks thread-safe.

    Ejemplo:
        >>> # El estado se recupera de state_store
        >>> plan = self.app.state_store.deployment_plan
    """

    CSS_PATH = "deploy_screen.tcss"

    BINDINGS = [
        ("ctrl+q", "quit", "Salir"),
    ]

    def compose(self) -> ComposeResult:
        """
        Construye el layout visual de la pantalla de despliegue.

        Estructura del Layout:
            - Header: Título de la aplicación.
            - Vertical(id="main-layout"): Contenedor principal.
                - Static(id="section-title"): Título de la sección.
                - Static(id="deploy-status"): Estado del despliegue.
                - VerticalScroll(id="v-log"): Contenedor scrolleable del log.
                    - RichLog(id="ansible-log"): Widget de logs con auto-scroll.
                - Vertical(id="action-container"): Botones de acción.
            - Footer: Información de ayuda.

        Yields:
            ComposeResult: Generador de widgets para la composición.
        """
        yield Header()
        with Vertical(id="main-layout"):
            yield Static("🚀 DESPLIEGUE DE INFRAESTRUCTURA", classes="section-title")
            yield Static("", id="deploy-status")

            with VerticalScroll(id="v-log"):
                yield RichLog(id="ansible-log", highlight=True, auto_scroll=True)

            with Vertical(id="action-container"):
                yield Button("CERRAR Y SALIR", id="quit-button", variant="error", disabled=True, classes="btn-error")
        yield Footer()

    def on_mount(self) -> None:
        """
        Callback invocado al montar la pantalla.

        Recupera el plan de despliegue desde StateStore, valida su existencia
        y programa el inicio del despliegue mediante call_after_refresh().
        """
        plan = self.app.state_store.deployment_plan
        if not plan:
            self.notify("No hay un plan de despliegue configurado", severity="error")
            return

        status = self.query_one("#deploy-status", Static)
        status.update(f"Desplegando {len(plan.plan)} componentes (RAM estimada: {plan.ram_total_mb}MB)...")

        self.call_after_refresh(self._start_deployment)

    def _start_deployment(self) -> None:
        """
        Prepara y lanza el proceso de despliegue de Ansible.

        Pasos:
            1. Obtiene el plan de despliegue desde state_store.
            2. Recupera el widget RichLog para escribir logs.
            3. Escribe mensaje de inicio en el log.
            4. Persiste las variables en archivo .env dentro del directorio secrets/.
            5. Lanza el hilo de ejecución de Ansible.

        Notas:
            Este método debe llamarse desde el hilo principal de Textual.
            La ejecución real del Ansible ocurre en run_ansible_thread().
        """
        plan = self.app.state_store.deployment_plan
        log_widget = self.query_one("#ansible-log", RichLog)
        log_widget.write("[INFO] Iniciando orquestación con Ansible...")

        vars_to_inject = plan.vars_generated.copy()

        selected_apps = set(plan.plan)
        missing_required = []
        for key, value in vars_to_inject.items():
            if value in (None, "None", "null", ""):
                app_prefix = key.split("__")[0] if "__" in key else key.split("_")[0]
                if app_prefix.lower() in [a.lower() for a in selected_apps]:
                    if key.endswith("_PASSWORD") or key.endswith("_SECRET"):
                        missing_required.append(key)

        if missing_required:
            error_msg = f"[ERROR CRÍTICO] Faltan valores requeridos: {', '.join(missing_required)}"
            logger.error(error_msg)
            log_widget.write(error_msg)
            self.notify(f"Faltan valores requeridos: {missing_required}", severity="error")
            return

        env_file_path = get_main_env_path()
        try:
            if save_env_file(env_file_path, vars_to_inject):
                logger.info("Validación exitosa. Archivo .env guardado de forma segura con permisos 600.")
                log_widget.write("[SECURE] Archivo .env guardado de forma segura en secrets/.")
            else:
                logger.error("Fallo al guardar el archivo .env")
                log_widget.write("[ERROR] Fallo al persistir el archivo .env de forma segura.")
                return
        except PasswordPersistenceError as e:
            logger.error(f"Error de validación de contraseña: {e}")
            log_widget.write(f"[ERROR CRÍTICO] {e}")
            self.notify(f"Error de seguridad: {e}", severity="error")
            return

        self.run_ansible_thread(vars_to_inject, plan.plan)

    @work(thread=True)
    def run_ansible_thread(self, vars_to_inject: dict, modules: list) -> None:
        """
        Ejecuta el playbook de Ansible en un hilo separado.

        Args:
            vars_to_inject (dict): Variables de configuración para Ansible.
            modules (list): Lista de módulos/playbooks a ejecutar.

        Notas:
            - Utiliza @work(thread=True) de Textual para ejecución asíncrona.
            - Los eventos se transmiten thread-safely mediante call_from_thread().
            - El bucle de eventos asyncio se crea y cierra en este método.
        """
        log_widget = self.query_one("#ansible-log", RichLog)

        def on_event(event: dict) -> None:
            """
            Callback para procesar eventos del motor de Ansible.

            Args:
                event (dict): Diccionario con estructura:
                    - type (str): 'log' o 'done'.
                    - message (str): Mensaje descriptivo.
                    - success (bool): Solo para type='done'.
            """
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
        """
        Habilita el botón de salida tras completarse el despliegue.

        Called thread-safely desde run_ansible_thread() mediante call_from_thread().
        """
        quit_btn = self.query_one("#quit-button", Button)
        quit_btn.disabled = False
        status = self.query_one("#deploy-status", Static)
        status.update("✓ Despliegue finalizado.")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Maneja los eventos de presión de botones.

        Args:
            event (Button.Pressed): Evento de botón presionado.
        """
        if event.button.id == "quit-button":
            self.action_quit()

    def action_quit(self) -> None:
        """Acción de salida: cierra la aplicación."""
        self.app.exit()