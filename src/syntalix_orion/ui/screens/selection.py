"""
Pantalla de Selección de Catálogo - Syntalix-Orion.

Esta interfaz permite al usuario navegar por las categorías de aplicaciones
disponibles y seleccionar los componentes que desea desplegar en su
infraestructura. La lógica de dependencias transitivas está centralizada
en DeploymentController para mantener SRP.

Autor: Syntalix-Orion Team
Versión: 2.0.0
"""

from typing import Dict, List, Set

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Horizontal, Vertical, VerticalScroll, Container
from textual.widgets import Header, Footer, Static, Button
from textual.message import Message

from syntalix_orion.core.registry import get_registry
from syntalix_orion.core.deployment_controller import DeploymentController
from syntalix_orion.ui.components import ModernCheckbox, ProgressBar

CATEGORY_ORDER = ["Core", "Data", "Monitoring", "AI", "Automation", "Communication", "Management"]
CORE_CATEGORIES = {"Core"}

CATEGORY_COLORS = {
    "Core": "#F472B6", "Data": "#60A5FA", "Monitoring": "#34D399",
    "AI": "#A78BFA", "Automation": "#FB923C", "Communication": "#38BDF8", "Management": "#94A3B8"
}

APP_ICONS = {
    "traefik": "🌐", "crowdsec": "🛡️", "authentik": "🔐", "portainer": "📦",
    "postgres_pgvector": "🐘", "mariadb": "🗄️", "mongodb": "🍃", "rabbitmq": "🐰",
    "redis": "💾", "qdrant": "🔍", "minio": "☁️",
    "prometheus": "📊", "grafana": "📈", "loki": "📋", "uptime_kuma": "⏱️",
    "dify": "🤖", "openwebui": "💬", "flowise": "🌊",
    "n8n": "⚡", "activepieces": "🔧", "evolution_api": "📱",
    "chatwoot": "💬", "odoo": "🏢"
}


def get_app_icon(app_id: str) -> str:
    return APP_ICONS.get(app_id, "📦")


class SelectionScreen(Screen):
    """
    Controlador Visual para la Selección de Aplicaciones.

    Esta pantalla es puramente presentacional. Delega toda la lógica de
    selección y resolución de dependencias a DeploymentController.

    Atributos:
        catalog (Dict[str, AppMetadata]): Catálogo completo de aplicaciones.
        controller (DeploymentController): Controlador de lógica de negocio.

    Mensajes Emitidos:
        SelectionComplete: Cuando el usuario confirma la selección.
    """

    CSS_PATH = "selection/selection_screen.tcss"

    BINDINGS = [
        ("ctrl+n", "next", "Siguiente (Configurar)"),
        ("ctrl+q", "quit", "Salir"),
    ]

    class SelectionComplete(Message):
        """Mensaje emitido cuando el usuario completa la selección de aplicaciones."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        registry = get_registry()
        self.catalog = registry.load_all()
        self.controller = DeploymentController(self.catalog, self.app.state_store)

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main-container"):
            with VerticalScroll(id="left-panel"):
                yield Static("◉ Syntalix-Orion V2", id="catalog-title")
                yield Static("Selecciona las aplicaciones a desplegar.", id="catalog-subtitle")

                category_apps: Dict[str, List] = {}
                for app_id, app in self.catalog.items():
                    category_apps.setdefault(app.category, []).append(app)

                for category in CATEGORY_ORDER:
                    if category in category_apps:
                        is_mandatory = category in CORE_CATEGORIES
                        apps = sorted(category_apps[category], key=lambda a: a.name)
                        color_class = f"category-{category.lower()}"
                        yield Static(f"▸ {category}", classes=f"category-header {color_class}")
                        for app in apps:
                            is_selected = app.id in self.app.state_store.selected_apps
                            if is_mandatory:
                                is_selected = True

                            deps_tooltip = ""
                            if app.dependencies:
                                dep_names = [self.catalog.get(d).name for d in app.dependencies if self.catalog.get(d)]
                                deps_tooltip = f"\nDependencias:\n- {chr(10) + '- '.join(dep_names)}"

                            checkbox = ModernCheckbox(
                                label=f"{app.name} (v{app.version}) - {app.ram_mb}MB",
                                app_id=app.id,
                                is_mandatory=is_mandatory,
                                value=is_selected,
                                tooltip=f"ID: {app.id}\nRAM: {app.ram_mb}MB{deps_tooltip}",
                                category=category.lower()
                            )
                            yield checkbox

            with VerticalScroll(id="right-panel"):
                yield Static("◉ RESUMEN DE SELECCIÓN", id="monitor-title")
                with VerticalScroll(id="status-display"):
                    yield Static(id="status-content", markup=True)
                with Container(id="summary-container"):
                    yield Static(id="ram-summary", markup=True)
                    yield Static(id="app-count", markup=True)
                with Vertical(id="action-container"):
                    yield Static("─" * 50, id="divider")
                    yield Button("⚡ CONTINUAR →  [Ctrl+N]", id="next-button", variant="primary")

        yield Footer()

    def on_mount(self) -> None:
        for app in self.catalog.values():
            if app.category in CORE_CATEGORIES:
                self.app.state_store.add_app(app.id)
                self.controller.user_selected.add(app.id)
                for dep_id in app.dependencies:
                    if dep_id in self.catalog:
                        self.app.state_store.add_app(dep_id)
                        self.controller.auto_dependencies.add(dep_id)
        self._update_status_display()
        self._update_all_checkboxes()

    def on_modern_checkbox_changed(self, event: ModernCheckbox.Changed) -> None:
        checkbox = event.checkbox
        if not hasattr(checkbox, 'app_id'):
            return
        app_id = checkbox.app_id

        result = self.controller.toggle_app(app_id, checkbox.value)

        if not result.success:
            self.notify(result.message, title="Dependencia Activa", severity="warning")
            self._update_all_checkboxes()
            return

        self._update_status_display()
        self._update_all_checkboxes()

    def _update_status_display(self) -> None:
        status = self.query_one("#status-content", Static)
        ram_summary = self.query_one("#ram-summary", Static)
        app_count = self.query_one("#app-count", Static)
        selected = self.app.state_store.selected_apps

        lines = []
        total_ram = 0
        user_apps = []
        dep_apps = []

        for app_id in sorted(selected):
            app = self.catalog.get(app_id)
            if app:
                if app_id in self.controller.user_selected:
                    user_apps.append((app_id, app))
                else:
                    dep_apps.append((app_id, app))

        if user_apps:
            lines.append("[b]★ Seleccionadas:[/b]")
            for app_id, app in user_apps:
                icon = get_app_icon(app_id)
                cat_color = CATEGORY_COLORS.get(app.category, "#00D9FF")
                deps_info = ""
                if app.dependencies:
                    dep_names = [self.catalog.get(d).name for d in app.dependencies if self.catalog.get(d)]
                    deps_info = f" → [dim][i]{', '.join(dep_names)}[/][/]"
                lines.append(f"  {icon} [bold][{cat_color}]{app.name}[/][/] ([b]{app.ram_mb}MB[/])[dim]{deps_info}[/]")
                total_ram += app.ram_mb

        if dep_apps:
            lines.append("")
            lines.append("[b]⚙ Dependencias auto-añadidas:[/b]")
            for app_id, app in dep_apps:
                icon = get_app_icon(app_id)
                cat_color = CATEGORY_COLORS.get(app.category, "#00D9FF")
                lines.append(f"  {icon} [{cat_color}]{app.name}[/] ([b]{app.ram_mb}MB[/])")
                total_ram += app.ram_mb

        if not lines:
            lines.append("[dim]Ninguna aplicación seleccionada.[/]")

        status.update("\n".join(lines) if lines else "")

        max_ram_gb = 8.0
        ram_ratio = (total_ram / 1024) / max_ram_gb
        ram_color = "#10B981" if ram_ratio < 0.5 else "#F59E0B" if ram_ratio < 0.8 else "#EF4444"

        progress = ProgressBar(label="RAM", current=total_ram / 1024, maximum=max_ram_gb)
        ram_summary.update(f"[b]{progress._render()}[/]\n")
        app_count.update(f"[b]Apps:[/b] {len(user_apps)} seleccionadas + {len(dep_apps)} dependencias = [bold]{len(selected)}[/] total | [b]RAM Total:[/b] [{ram_color}]{total_ram}MB[/]")

    def _update_all_checkboxes(self) -> None:
        checkboxes = list(self.query(ModernCheckbox))
        for checkbox in checkboxes:
            checkbox._suppress_events = True
        try:
            for checkbox in checkboxes:
                app_id = checkbox.app_id
                should_be_checked = app_id in self.app.state_store.selected_apps
                if checkbox.value != should_be_checked:
                    checkbox.set_value_without_event(should_be_checked)
        finally:
            for checkbox in checkboxes:
                checkbox._suppress_events = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "next-button":
            self.action_next()

    def action_next(self) -> None:
        if not self.app.state_store.selected_apps:
            self.notify("Debe seleccionar al menos una aplicación", severity="error")
            return
        self.post_message(self.SelectionComplete())

    def action_quit(self) -> None:
        self.app.exit()