from textual.widgets import Checkbox
from textual.message import Message

class ModernCheckbox(Checkbox):
    states = {
        "unchecked": {"box": "○", "color": "#64748B"},
        "checked": {"box": "●", "color": "#00D9FF"},
        "focused": {"box": "◉", "color": "#FFFFFF"},
        "disabled": {"box": "○", "color": "#374151"}
    }

    class Changed(Message):
        def __init__(self, checkbox: "ModernCheckbox", value: bool) -> None:
            self.value = value
            super().__init__()

    def __init__(self, label: str, app_id: str, is_mandatory: bool, value: bool = False,
                 tooltip: str = "", category: str = "core", **kwargs):
        self.label = label
        self.app_id = app_id
        self.is_mandatory = is_mandatory
        self._value = value
        self._tooltip = tooltip
        self.category = category
        super().__init__(label=f"[{category}] {label}", checked=value, id=f"checkbox-{app_id}", disabled=is_mandatory, **kwargs)

    def _get_category_color(self) -> str:
        colors = {
            "core": "#F472B6", "data": "#60A5FA", "monitoring": "#34D399",
            "networking": "#FBBF24", "ai": "#A78BFA", "automation": "#FB923C",
            "communication": "#38BDF8", "management": "#94A3B8"
        }
        return colors.get(self.category, '#00D9FF')

    def watch_checked(self, value: bool) -> None:
        if self.is_mandatory and not value:
            return
        self._value = value