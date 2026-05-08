"""
Pantalla de Configuración de Variables - Syntalix-Orion.

Maneja la recolección de parámetros requeridos por las aplicaciones seleccionadas,
tales como dominios, correos electrónicos y secretos. Implementa validación en
tiempo real para asegurar la coherencia de los datos antes de continuar al
despliegue.

Arquitectura de la Pantalla:
    - Layout horizontal dividido en dos paneles.
    - Panel izquierdo (60%): Formularios de variables con campos de entrada.
    - Panel derecho (40%): Resumen del plan de instalación.

Flujo de Datos:
    1. Recupera el plan de selección desde StateStore.
    2. Calcula las variables requeridas según los metadatos de apps.
    3. Genera dinámicamente campos Input para cada variable.
    4. Valida el formato de los campos (dominio, email, etc.).
    5. Persiste las variables en StateStore para el despliegue.

Autor: Syntalix-Orion Team
Versión: 2.0.0
"""

from typing import Dict, List, Tuple

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, VerticalScroll, Horizontal
from textual.widgets import Header, Footer, Static, Button, Input
from textual.message import Message

from syntalix_orion.core.registry import get_registry
from syntalix_orion.core.dependency_graph import DependencyGraph
from syntalix_orion.core.variable_orchestrator import VariableOrchestrator
from syntalix_orion.core.security import (
    validate_domain,
    validate_email,
    validate_password_strength,
    _is_user_facing_password,
    hash_password_bcrypt
)
from syntalix_orion.core.state import load_env_file, get_main_env_path
from syntalix_orion.ui.managers.state_store import DeploymentPlan
from syntalix_orion.ui.components import StatusIndicator


class ConfigScreen(Screen):
    """
    Gestor de Formulario de Configuración Dinámica.

    Genera automáticamente campos de entrada (Input) basados en los metadatos
    de las aplicaciones seleccionadas en el plan. Cada campo incluye:
        - Etiqueta con nombre de variable.
        - Descripción del propósito del campo.
        - Validación de formato según tipo (domain, email, secret, etc.).

    Atributos:
        catalog (Dict[str, AppMetadata]): Catálogo de aplicaciones cargadas.
        dependency_graph (DependencyGraph): Grafo de dependencias.
        required_vars (List[Tuple]): Lista de variables requeridas.
        user_inputs (Dict[str, str]): Diccionario de valores ingresados.

    Mensajes Emitidos:
        ConfigComplete: Cuando todos los campos obligatorios están validados.
        ConfigBack: Cuando el usuario solicita volver a la pantalla anterior.

    Ejemplo:
        >>> # Validación y envío de configuración
        >>> self.post_message(self.ConfigComplete())
    """

    CSS_PATH = "config/config_screen.tcss"

    BINDINGS = [
        ("ctrl+enter", "deploy", "Confirmar y Desplegar"),
        ("ctrl+b", "back", "Atrás"),
    ]

    class ConfigComplete(Message):
        """Mensaje emitido cuando la configuración se completa exitosamente."""

    class ConfigBack(Message):
        """Mensaje emitido cuando el usuario solicita volver a la pantalla anterior."""

    def __init__(self, **kwargs):
        """
        Inicializa la pantalla de configuración.

        Args:
            **kwargs: Argumentos传递给 Screen base.
        """
        super().__init__(**kwargs)
        registry = get_registry()
        self.catalog = registry.load_all()
        self.raw_metadata = registry.export_to_legacy()

        self.dependency_graph = DependencyGraph(catalog=self.catalog)
        self.variable_orchestrator = VariableOrchestrator(catalog=self.catalog)
        self.required_vars: List[Tuple[str, str, str]] = []
        self.user_inputs: Dict[str, str] = {}

    def compose(self) -> ComposeResult:
        """
        Construye el layout visual de la pantalla de configuración.

        Layout:
            - Header con título de la aplicación.
            - Horizontal(id="main-container"): Contenedor principal.
                - VerticalScroll(id="left-panel"): Formularios de variables.
                    - Static: Título "VARIABLES REQUERIDAS".
                    - Static(id="validation-error"): Mensajes de error.
                    - VerticalScroll(id="forms-scroll-container"):
                        - Vertical(id="forms-container"): Campos de entrada.
                - Vertical(id="right-panel"): Resumen del plan.
                    - Static: Título "RESUMEN DE INSTALACIÓN".
                    - VerticalScroll(id="status-display"): Lista de apps.
                    - Vertical(id="action-container"): Botones de acción.
            - Footer.

        Yields:
            ComposeResult: Generador de widgets para la composición.
        """
        yield Header()
        with Horizontal(id="main-container"):
            with VerticalScroll(id="left-panel"):
                yield Static("📝 VARIABLES REQUERIDAS", classes="section-title")
                yield Static("", id="validation-error", classes="ram-warning")
                with VerticalScroll(id="forms-scroll-container"):
                    yield Vertical(id="forms-container")

            with Vertical(id="right-panel"):
                yield Static("📊 RESUMEN DE INSTALACIÓN", classes="section-title")
                with VerticalScroll(id="status-display"):
                     yield Static(id="plan-summary", markup=True)

                with Vertical(id="action-container"):
                    yield Button("⚡ CONFIRMAR Y CONTINUAR [Ctrl+Enter]", id="confirm-button", variant="success", classes="btn-success")
                    yield Button("← Volver", id="back-button", variant="default", classes="btn-back")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#validation-error", Static).update("")
        self._calculate_plan()

    def on_screen_resume(self, event=None) -> None:
        self.query_one("#validation-error", Static).update("")
        self._calculate_plan()

    def on_show(self, event=None) -> None:
        self.query_one("#validation-error", Static).update("")
        self._calculate_plan()

    def _calculate_plan(self) -> None:
        selected = list(self.app.state_store.selected_apps)
        env_file_path = get_main_env_path()
        existing_vars = load_env_file(env_file_path)

        try:
            result = self.dependency_graph.plan_multi(selected)
            ordered_plan = result.get("plan", [])
            vars_generated = self.variable_orchestrator.generate_vars_for_plan(ordered_plan, existing_vars)
            
            plan = DeploymentPlan(
                plan=ordered_plan,
                ram_total_mb=result.get("ram_mb_total", 0),
                vars_generated=vars_generated,
                dependencies=result.get("dependencies", [])
            )
            self.app.state_store.deployment_plan = plan

            summary = self.query_one("#plan-summary", Static)
            lines = [
                "[b]★ Apps en el Plan:[/b]",
            ]
            for app_id in plan.plan:
                app_meta = self.raw_metadata.get(app_id, {})
                name = app_meta.get("name", app_id)
                ram = app_meta.get("ram_mb", 0)
                lines.append(f"  • {name} ([dim]{ram}MB[/])")

            lines.append("")
            lines.append(f"[b]Resumen:[/b]")
            lines.append(f"  Total Apps: [bold]{len(plan.plan)}[/]")
            lines.append(f"  RAM Total: [bold #00D9FF]{plan.ram_total_mb}MB[/]")

            summary.update("\n".join(lines))

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
                        clean_var_name = var_name.upper()
                        app_prefix = app_id.upper() + "_"
                        if clean_var_name.startswith(app_prefix):
                            clean_var_name = clean_var_name[len(app_prefix):]
                        full_key = f"{app_id.upper()}__{clean_var_name}"
                        app_specific_vars.append((full_key, desc, v_type))
                        self.required_vars.append((full_key, desc, v_type))

                if app_specific_vars:
                    app_vars_map[app_name] = app_specific_vars

            forms_container = self.query_one("#forms-container", Vertical)
            for child in forms_container.children:
                child.remove()

            self.user_inputs.clear()

            widgets_to_mount = []
            for app_name, vars_list in app_vars_map.items():
                widgets_to_mount.append(Static(f"\n[📦] {app_name}", classes="app-title"))
                for full_key, desc, v_type in vars_list:
                    default_val = self.app.state_store.user_variables.get(full_key, plan.vars_generated.get(full_key, ""))
                    is_pwd = v_type in ("secret", "password")
                    widgets_to_mount.append(self._create_form_field(full_key, desc, default_val, is_pwd))
                    self.user_inputs[full_key] = default_val

            if widgets_to_mount:
                forms_container.mount(*widgets_to_mount)

        except Exception as e:
            self.notify(f"Error calculando plan: {e}", severity="error")

    def _create_form_field(self, full_key: str, desc: str, default_val: str, is_pwd: bool) -> Vertical:
        label = Static(f"{full_key}", classes="form-label")
        desc_widget = Static(f" {desc}", classes="form-desc")
        if is_pwd:
            input_widget = Input(value=default_val, placeholder=full_key, password=True, id=f"input-{full_key}")
        else:
            input_widget = Input(value=default_val, placeholder=full_key, id=f"input-{full_key}")

        return Vertical(label, desc_widget, input_widget, classes="input-row")

    def on_input_changed(self, event: Input.Changed) -> None:
        input_id = event.input.id
        if input_id.startswith("input-"):
            key = input_id[len("input-"):]
            self.user_inputs[key] = event.value

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm-button":
            self.action_deploy()
        elif event.button.id == "back-button":
            self.action_back()

    def _validate_inputs(self) -> Tuple[bool, str]:
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
            elif v_type in ("secret", "password"):
                if _is_user_facing_password(var_name):
                    if val.startswith("$2"):
                        continue
                    is_valid, error_msg = validate_password_strength(val)
                    if not is_valid:
                        return False, f"Contraseña débil para '{desc}': {error_msg}"
        return True, ""

    def action_deploy(self) -> None:
        is_valid, error_msg = self._validate_inputs()
        error_widget = self.query_one("#validation-error", Static)

        if not is_valid:
            error_widget.update(f"**[ERROR]** {error_msg}")
            self.notify(error_msg, severity="error")
            return

        error_widget.update("")

        for app_id, app_meta in self.raw_metadata.items():
            for var_name, var_def in app_meta.get("variables", {}).items():
                if var_def.get("transform") == "bcrypt":
                    clean_var_name = var_name.upper()
                    app_prefix = app_id.upper() + "_"
                    if clean_var_name.startswith(app_prefix):
                        clean_var_name = clean_var_name[len(app_prefix):]
                    full_key = f"{app_id.upper()}__{clean_var_name}"

                    val = self.user_inputs.get(full_key, "")
                    if val and not val.startswith("$2"):
                        try:
                            self.user_inputs[full_key] = hash_password_bcrypt(val)
                        except Exception as e:
                            self.notify(f"Error encriptando {full_key}: {e}", severity="error")
                            return

        self.app.state_store.user_variables.update(self.user_inputs)
        if self.app.state_store.deployment_plan:
            self.app.state_store.deployment_plan.vars_generated.update(self.user_inputs)

        self.post_message(self.ConfigComplete())

    def action_back(self) -> None:
        self.post_message(self.ConfigBack())