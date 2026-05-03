import sys
from pathlib import Path
from typing import Dict, List

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Header, Footer, Static, Button, Checkbox
from textual.message import Message

SCRIPT_DIR = Path(__file__).parent.parent.parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load Catalog
from apps_metadata import APP_METADATA
from core.models import load_app_catalog

from ui.widgets.lists import CatalogCategory, AppCheckbox

CATEGORY_ORDER = ["Core", "AI", "Automation", "Communication", "Management"]
CORE_CATEGORIES = {"Core"}

class SelectionScreen(Screen):
    """Pantalla para seleccionar las aplicaciones del catálogo."""
    
    BINDINGS = [
        ("ctrl+n", "next", "Siguiente (Configurar)"),
        ("ctrl+q", "quit", "Salir"),
    ]

    class SelectionComplete(Message):
        """Mensaje emitido cuando el usuario confirma la selección."""
        pass

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.catalog = load_app_catalog(APP_METADATA)
        
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Horizontal(id="main-container"):
            with VerticalScroll(id="left-panel"):
                yield Static("[PKG] **Catálogo de Aplicaciones**", id="catalog-title")
                yield Static("Selecciona las aplicaciones a desplegar.", id="catalog-subtitle")
                
                category_apps = {}
                for app_id, app in self.catalog.items():
                    category_apps.setdefault(app.category, []).append(app)
                    
                for category in CATEGORY_ORDER:
                    if category in category_apps:
                        is_mandatory = category in CORE_CATEGORIES
                        apps = sorted(category_apps[category], key=lambda a: a.name)
                        yield CatalogCategory(
                            name=category, 
                            apps=apps, 
                            selected_apps=self.app.state_store.selected_apps, 
                            is_mandatory=is_mandatory
                        )

            with Vertical(id="right-panel"):
                yield Static("## [STAT] Apps Seleccionadas", id="monitor-title")
                yield Static("", id="monitor-spacer")
                with VerticalScroll(id="status-display"):
                    yield Static(id="status-content", markup=True)
                
                with Vertical(id="action-container"):
                    yield Static("---")
                    yield Button("Siguiente: Configurar Variables [Ctrl+N]", id="next-button", variant="primary")
                    
        yield Footer()

    def on_mount(self) -> None:
        # Pre-seleccionar Core apps
        for app in self.catalog.values():
            if app.category in CORE_CATEGORIES:
                self.app.state_store.add_app(app.id)
        self._update_status_display()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if isinstance(event.checkbox, AppCheckbox):
            app_id = event.checkbox.app_id
            if event.checkbox.value:
                self.app.state_store.add_app(app_id)
                # Auto-select dependencies
                app_meta = self.catalog.get(app_id)
                if app_meta and app_meta.dependencies:
                    for dep_id in app_meta.dependencies:
                        if dep_id not in self.app.state_store.selected_apps:
                            dep_checkbox = self.query_one(f"#checkbox-{dep_id}", AppCheckbox)
                            if dep_checkbox:
                                dep_checkbox.value = True
            else:
                if getattr(event.checkbox, 'is_mandatory', False):
                    event.checkbox.value = True
                else:
                    self.app.state_store.remove_app(app_id)
            
            self._update_status_display()

    def _update_status_display(self) -> None:
        status = self.query_one("#status-content", Static)
        selected = self.app.state_store.selected_apps
        
        lines = ["### Aplicaciones seleccionadas:"]
        for app_id in selected:
            app = self.catalog.get(app_id)
            if app:
                lines.append(f"- **{app.name}**")
                
        status.update("\n".join(lines))

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
