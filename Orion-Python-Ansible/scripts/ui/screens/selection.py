import sys
from pathlib import Path
from typing import Dict, List

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Header, Footer, Static, Button
from textual.message import Message

SCRIPT_DIR = Path(__file__).parent.parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from apps_metadata import APP_METADATA
from core.models import load_app_catalog
from ui.components import ModernCheckbox, ProgressBar

CATEGORY_ORDER = ["Core", "Data", "Monitoring", "AI", "Automation", "Communication", "Management"]
CORE_CATEGORIES = {"Core"}

CATEGORY_COLORS = {
    "Core": "#F472B6", "Data": "#60A5FA", "Monitoring": "#34D399",
    "AI": "#A78BFA", "Automation": "#FB923C", "Communication": "#38BDF8", "Management": "#94A3B8"
}

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
    #status-display { height: 60%; padding: 1; margin-bottom: 1; }
    .selected-item { color: #10B981; }
    #action-container { height: auto; align: center bottom; padding: 1; }
    .btn-primary { background: #00D9FF; color: #0D1117; }
    .btn-back { color: #8B949E; }
    #footer-hint { color: #6E7681; }
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
                            checkbox = ModernCheckbox(
                                label=f"{app.name} (v{app.version}) - {app.ram_mb}MB",
                                app_id=app.id,
                                is_mandatory=is_mandatory,
                                value=is_selected,
                                tooltip=f"ID: {app.id}\nRAM: {app.ram_mb}MB",
                                category=category.lower()
                            )
                            yield checkbox

            with Vertical(id="right-panel"):
                yield Static("◉ RESUMEN DE SELECCIÓN", id="monitor-title")
                with VerticalScroll(id="status-display"):
                    yield Static(id="status-content", markup=True)
                with Vertical(id="summary-container"):
                    yield Static(id="ram-summary", markup=True)
                with Vertical(id="action-container"):
                    yield Static("─" * 50, id="divider")
                    yield Button("⚡ CONTINUAR →  [Ctrl+N]", id="next-button", variant="primary")

        yield Footer()

    def on_mount(self) -> None:
        for app in self.catalog.values():
            if app.category in CORE_CATEGORIES:
                self.app.state_store.add_app(app.id)
        self._update_status_display()

    def on_checkbox_changed(self, event: ModernCheckbox.Changed) -> None:
        if isinstance(event.checkbox, ModernCheckbox):
            app_id = event.checkbox.app_id
            if event.checkbox.value:
                self.app.state_store.add_app(app_id)
                app_meta = self.catalog.get(app_id)
                if app_meta and app_meta.dependencies:
                    for dep_id in app_meta.dependencies:
                        if dep_id not in self.app.state_store.selected_apps:
                            self.app.state_store.add_app(dep_id)
                            try:
                                dep_checkbox = self.query_one(f"#checkbox-{dep_id}", ModernCheckbox)
                                if dep_checkbox:
                                    dep_checkbox.value = True
                            except Exception:
                                pass
            else:
                if not getattr(event.checkbox, 'is_mandatory', False):
                    self.app.state_store.remove_app(app_id)
            self._update_status_display()

    def _update_status_display(self) -> None:
        status = self.query_one("#status-content", Static)
        ram_summary = self.query_one("#ram-summary", Static)
        selected = self.app.state_store.selected_apps

        lines = ["```"]
        total_ram = 0
        for app_id in selected:
            app = self.catalog.get(app_id)
            if app:
                lines.append(f"✓ {app.name}")
                total_ram += app.ram_mb
        lines.append("```")

        status.update("\n".join(lines) if lines else "Ninguna aplicación seleccionada.")

        max_ram_gb = 4.0
        progress = ProgressBar(label="RAM", current=total_ram / 1024, maximum=max_ram_gb)
        ram_summary.update(f"\n{progress._render()}\n\n**Apps:** {len(selected)} | **RAM Total:** ~{total_ram}MB")

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