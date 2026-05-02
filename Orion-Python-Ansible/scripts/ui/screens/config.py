import sys
from pathlib import Path
from typing import Dict

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Header, Footer, Static, Button
from textual.message import Message

from core.dependency_graph import DependencyGraph
from ui.widgets.forms import DynamicFormInput
from ui.managers.state_store import DeploymentPlan

class ConfigScreen(Screen):
    """Pantalla Gatekeeper para solicitar variables y confirmar el plan."""
    
    BINDINGS = [
        ("ctrl+d", "deploy", "Siguiente (Desplegar)"),
        ("ctrl+b", "back", "Atrás"),
    ]

    class ConfigComplete(Message):
        """Mensaje emitido cuando se aprueba la configuración."""
        pass
        
    class ConfigBack(Message):
        """Mensaje para volver a la pantalla anterior."""
        pass

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from apps_metadata import APP_METADATA
        from core.models import load_app_catalog
        self.catalog = load_app_catalog(APP_METADATA)
        
        catalog_dict = {app_id: app.model_dump() for app_id, app in self.catalog.items()}
        self.dependency_graph = DependencyGraph(catalog=catalog_dict)
        self.required_vars = []
        self.user_inputs: Dict[str, str] = {}

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="config-container", classes="p-2"):
            yield Static("## [GATEKEEPER] Configuración del Despliegue", markup=True)
            yield Static(id="plan-summary", markup=True)
            
            yield Static("### Variables de Entorno", id="vars-title", markup=True)
            yield Vertical(id="forms-container")
            
            with Vertical(id="action-container", classes="mt-2"):
                yield Button("[🚀] Confirmar y Continuar al Despliegue", id="confirm-button", variant="success")
                yield Button("Volver", id="back-button", variant="default")
                
        yield Footer()

    def on_mount(self) -> None:
        self._calculate_plan()

    def _calculate_plan(self) -> None:
        selected = list(self.app.state_store.selected_apps)
        try:
            result = self.dependency_graph.plan_with_vars_multi(selected)
            plan = DeploymentPlan(
                plan=result.get("plan", []),
                ram_total_mb=result.get("ram_mb_total", 0),
                vars_generated=result.get("vars", {}),
                dependencies=result.get("dependencies", [])
            )
            self.app.state_store.deployment_plan = plan
            
            # Mostrar resumen
            summary = self.query_one("#plan-summary", Static)
            lines = [
                f"- **Apps seleccionadas:** {len(selected)}",
                f"- **Total a instalar (con dependencias):** {len(plan.plan)}",
                f"- **RAM Estimada:** {plan.ram_total_mb} MB",
            ]
            summary.update("\n".join(lines))
            
            # TODO: Extraer variables que necesitan input manual del usuario
            # Por ahora, usamos vars_generated para que el usuario pueda sobrescribir
            # si lo desea.
            forms_container = self.query_one("#forms-container", Vertical)
            forms_container.remove_children()
            
            # En Orion V2, las variables se generan o están en la metadata.
            # Vamos a mostrar solo algunas o permitir configurarlas si tienen un patrón.
            for key, value in plan.vars_generated.items():
                if "PASSWORD" in key or "SECRET" in key:
                    continue # No pedir inputs para secretos auto-generados por seguridad
                
                # Ejemplo: pedir variables comunes de dominio o correo
                if "DOMAIN" in key or "EMAIL" in key:
                    form_input = DynamicFormInput(var_name=key, default_value=str(value))
                    forms_container.mount(form_input)
                    self.user_inputs[key] = str(value)
                    
        except Exception as e:
            self.notify(f"Error calculando plan: {e}", severity="error")

    def on_dynamic_form_input_value_changed(self, event: DynamicFormInput.ValueChanged) -> None:
        self.user_inputs[event.key] = event.value

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm-button":
            self.action_deploy()
        elif event.button.id == "back-button":
            self.action_back()

    def action_deploy(self) -> None:
        # Guardar en el store
        self.app.state_store.user_variables.update(self.user_inputs)
        # Actualizar las vars generadas con las del usuario
        if self.app.state_store.deployment_plan:
            self.app.state_store.deployment_plan.vars_generated.update(self.user_inputs)
            
        self.post_message(self.ConfigComplete())

    def action_back(self) -> None:
        self.post_message(self.ConfigBack())
