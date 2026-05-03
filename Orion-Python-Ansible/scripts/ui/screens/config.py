import sys
from pathlib import Path
from typing import Dict, List, Tuple

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Header, Footer, Static, Button
from textual.message import Message

from core.dependency_graph import DependencyGraph
from core.security import validate_domain, validate_email
from core.state import load_env_file
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
        self.raw_metadata = APP_METADATA
        
        catalog_dict = {app_id: app.model_dump() for app_id, app in self.catalog.items()}
        self.dependency_graph = DependencyGraph(catalog=catalog_dict)
        self.required_vars: List[Tuple[str, str, str]] = [] # list of (var_name, description, type)
        self.user_inputs: Dict[str, str] = {}

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="config-container", classes="p-2"):
            yield Static("## [GATEKEEPER] Configuración del Despliegue", markup=True)
            yield Static(id="plan-summary", markup=True)
            
            yield Static("### Variables Requeridas", id="vars-title", markup=True)
            yield Static("", id="validation-error", classes="ram-warning")
            yield Vertical(id="forms-container")
            
            with Vertical(id="action-container", classes="mt-2"):
                yield Button("[🚀] Confirmar y Continuar al Despliegue", id="confirm-button", variant="success")
                yield Button("Volver", id="back-button", variant="default")
                
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#validation-error", Static).update("")
        self._calculate_plan()

    def _calculate_plan(self) -> None:
        selected = list(self.app.state_store.selected_apps)
        
        # Load existing .env variables to ensure idempotency across runs
        env_file_path = str(Path.cwd() / ".env")
        existing_vars = load_env_file(env_file_path)
        
        try:
            result = self.dependency_graph.plan_with_vars_multi(selected, existing_vars=existing_vars)
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
            
            # Identificar variables manuales requeridas por aplicación
            self.required_vars.clear()
            app_vars_map = {}
            for app_id in plan.plan:
                app_meta = self.raw_metadata.get(app_id, {})
                app_name = app_meta.get("name", app_id)
                variables = app_meta.get("variables", {})
                
                app_specific_vars = []
                for var_name, var_info in variables.items():
                    is_auto = var_info.get("auto_generate", False)
                    is_required = var_info.get("required", False)
                    if is_required and not is_auto:
                        desc = var_info.get("description", var_name)
                        v_type = var_info.get("type", "string")
                        full_key = f"{app_id}__{var_name}".upper()
                        app_specific_vars.append((full_key, desc, v_type))
                        self.required_vars.append((full_key, desc, v_type))
                
                if app_specific_vars:
                    app_vars_map[app_name] = app_specific_vars
            
            forms_container = self.query_one("#forms-container", Vertical)
            forms_container.remove_children()
            self.user_inputs.clear()
            
            for app_name, vars_list in app_vars_map.items():
                forms_container.mount(Static(f"\n[📦] **{app_name}**", markup=True))
                for full_key, desc, v_type in vars_list:
                    # Pre-llenar si ya estaba en el store o en las vars generadas (.env)
                    default_val = self.app.state_store.user_variables.get(full_key, plan.vars_generated.get(full_key, ""))
                    is_pwd = v_type == "secret"
                    form_input = DynamicFormInput(var_name=full_key, description=desc, default_value=default_val, is_password=is_pwd)
                    forms_container.mount(form_input)
                    self.user_inputs[full_key] = default_val
                    
        except Exception as e:
            self.notify(f"Error calculando plan: {e}", severity="error")

    def on_dynamic_form_input_value_changed(self, event: DynamicFormInput.ValueChanged) -> None:
        self.user_inputs[event.key] = event.value

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm-button":
            self.action_deploy()
        elif event.button.id == "back-button":
            self.action_back()

    def _validate_inputs(self) -> Tuple[bool, str]:
        """Aplica Fail-Fast validando las entradas obligatorias."""
        for var_name, desc, v_type in self.required_vars:
            val = self.user_inputs.get(var_name, "").strip()
            if not val or val in ("None", "null"):
                return False, f"El campo '{desc}' ({var_name}) es obligatorio."
            
            if v_type == "domain":
                if not validate_domain(val):
                    return False, f"El valor '{val}' para '{desc}' no es un dominio válido."
            elif v_type == "email":
                if not validate_email(val):
                    return False, f"El valor '{val}' para '{desc}' no es un correo válido."
        return True, ""

    def action_deploy(self) -> None:
        is_valid, error_msg = self._validate_inputs()
        error_widget = self.query_one("#validation-error", Static)
        
        if not is_valid:
            error_widget.update(f"**[ERROR]** {error_msg}")
            self.notify(error_msg, severity="error")
            return
            
        error_widget.update("")
        # Guardar en el store
        self.app.state_store.user_variables.update(self.user_inputs)
        # Actualizar las vars generadas con las del usuario
        if self.app.state_store.deployment_plan:
            self.app.state_store.deployment_plan.vars_generated.update(self.user_inputs)
            
        self.post_message(self.ConfigComplete())

    def action_back(self) -> None:
        self.post_message(self.ConfigBack())

