import sys
from pathlib import Path
from typing import Dict, List, Set

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Horizontal, Vertical, VerticalScroll, Container
from textual.widgets import Header, Footer, Static, Button, Checkbox
from textual.message import Message
from textual.reactive import reactive

SCRIPT_DIR = Path(__file__).parent.parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from apps_metadata import APP_METADATA
from core.models import load_app_catalog
from core.dependency_graph import DependencyGraph
from ui.components import ModernCheckbox, ProgressBar

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
    CSS = """
    Screen { background: #0D1117; }
    #main-container { height: 100%; layout: horizontal; }
    #left-panel { width: 50%; height: 100%; border-right: solid #00D9FF; padding: 1 2; }
    #right-panel { width: 50%; height: 100%; padding: 1 2; }
    #catalog-title { text-style: bold; color: #00D9FF; }
    #catalog-subtitle { color: #8B949E; margin-bottom: 1; }
    .category-header { text-style: bold; margin-top: 1; padding: 0 1; }
    .category-core { color: #F472B6; }
    .category-data { color: #60A5FA; }
    .category-monitoring { color: #34D399; }
    .category-ai { color: #A78BFA; }
    .category-automation { color: #FB923C; }
    .category-communication { color: #38BDF8; }
    .category-management { color: #94A3B8; }
    #monitor-title { text-style: bold; color: #00D9FF; }
    #status-display { height: 75%; padding: 1; margin-bottom: 1; }
    #summary-container { height: auto; }
    #action-container { height: auto; align: center bottom; padding: 1; }
    .btn-primary { background: #00D9FF; color: #0D1117; }
    .btn-back { color: #8B949E; }
    #footer-hint { color: #6E7681; }
    .app-selected { color: #10B981; }
    .app-dependency { color: #60A5FA; }
    .app-dependency-label { color: #38BDF8; }
    .ram-warning { color: #F59E0B; }
    .ram-critical { color: #EF4444; }
    .divider { color: #21262D; }
    """

    BINDINGS = [
        ("ctrl+n", "next", "Siguiente (Configurar)"),
        ("ctrl+q", "quit", "Salir"),
    ]

    class SelectionComplete(Message):
        pass

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.catalog = load_app_catalog(APP_METADATA)
        self.dep_graph = DependencyGraph(self.catalog)
        self.user_selected: Set[str] = set()
        self.auto_dependencies: Set[str] = set()

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main-container"):
            with VerticalScroll(id="left-panel"):
                yield Static("◉ Syntalix-Orion V2", id="catalog-title")
                yield Static("Selecciona las aplicaciones a desplegar.", id="catalog-subtitle")

                category_apps = {}
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
                                
                            # Construir tooltip informativo con dependencias
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

            with Vertical(id="right-panel"):
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
                self.auto_dependencies.add(app.id)
        self._update_status_display()
        self._update_all_checkboxes()

    def on_modern_checkbox_changed(self, event: ModernCheckbox.Changed) -> None:
        checkbox = event.checkbox
        if not hasattr(checkbox, 'app_id'):
            return
        app_id = checkbox.app_id
        
        if checkbox.value:
            # Flujo de selección
            self.user_selected.add(app_id)
            self._rebuild_dependencies()
        else:
            # Flujo de deselección: Verificar si otras apps en user_selected dependen de esta
            dependents = []
            for uid in self.user_selected:
                if uid == app_id:
                    continue
                
                try:
                    plan = self.dep_graph.resolve_dependencies(uid)
                    if app_id in plan:
                        dependents.append(self.catalog.get(uid).name)
                except Exception:
                    pass
            
            if dependents:
                # Bloquear deselección: hay apps seleccionadas que dependen de esta
                deps_str = ", ".join(dependents)
                self.notify(f"Requiere: {deps_str}", title="Dependencia Activa", severity="warning")
                # Revertir visualmente el checkbox al estado seleccionado
                self._update_all_checkboxes()
                return

            if not getattr(checkbox, 'is_mandatory', False):
                self.user_selected.discard(app_id)
                self._rebuild_dependencies()
                
        self._update_status_display()
        self._update_all_checkboxes()

    def _rebuild_dependencies(self) -> None:
        """
        Reconstruye el estado de apps seleccionadas desde cero, basado únicamente en 
        las aplicaciones Core y las seleccionadas por el usuario (user_selected).
        Esto asegura que cuando se deselecciona una app, sus dependencias huérfanas
        se eliminen automáticamente.
        """
        new_selected = set()
        new_auto_deps = set()
        
        # 1. Apps Core son obligatorias
        for app in self.catalog.values():
            if app.category in CORE_CATEGORIES:
                new_selected.add(app.id)
                new_auto_deps.add(app.id)
                
        # 2. Resolver dependencias para todas las apps seleccionadas por el usuario
        for uid in self.user_selected:
            new_selected.add(uid)
            try:
                plan = self.dep_graph.resolve_dependencies(uid)
                for dep_id in plan:
                    new_selected.add(dep_id)
                    if dep_id != uid:
                        new_auto_deps.add(dep_id)
            except Exception as e:
                # Ignoramos errores de grafo aquí, se manejan en validación
                pass
                
        # 3. Si una app es user_selected y no es Core, no debe estar en auto_deps
        for uid in self.user_selected:
            if uid in new_auto_deps and self.catalog.get(uid).category not in CORE_CATEGORIES:
                new_auto_deps.discard(uid)
                
        # 4. Actualizar estado
        self.app.state_store.selected_apps = new_selected
        self.auto_dependencies = new_auto_deps

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
                if app_id in self.user_selected:
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