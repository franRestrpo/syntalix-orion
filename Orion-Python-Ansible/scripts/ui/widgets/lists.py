from typing import List, Set
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Checkbox, Static
from textual.message import Message

class AppCheckbox(Checkbox):
    """Checkbox extendido para aplicaciones."""
    def __init__(self, label: str, app_id: str, is_mandatory: bool, value: bool = False, tooltip: str = ""):
        super().__init__(label, value=value, disabled=is_mandatory, id=f"checkbox-{app_id}")
        self.app_id = app_id
        self.tooltip = tooltip
        self.is_mandatory = is_mandatory

class CatalogCategory(Static):
    """Agrupación de checkboxes por categoría."""
    def __init__(self, name: str, apps: List, selected_apps: Set[str], is_mandatory: bool):
        super().__init__()
        self.category_name = name
        self.apps = apps
        self.selected_apps = selected_apps
        self.is_mandatory = is_mandatory

    def compose(self) -> ComposeResult:
        icon = "[Wrench]" if self.is_mandatory else "[BOX]"
        yield Static(f"\n{icon} **{self.category_name}**", classes="category-header")
        for app in self.apps:
            is_selected = app.id in self.selected_apps
            if self.is_mandatory:
                is_selected = True
                
            checkbox = AppCheckbox(
                label=f"{app.name} (v{app.version}) - {app.ram_mb}MB",
                app_id=app.id,
                is_mandatory=self.is_mandatory,
                value=is_selected,
                tooltip=f"ID: {app.id}\nRAM: {app.ram_mb}MB"
            )
            yield checkbox
