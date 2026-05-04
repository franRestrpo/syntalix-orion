from textual.widgets import Static
from textual.message import Message

class ModernCheckbox(Static):
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
        super().__init__(**kwargs)

    @property
    def value(self) -> bool:
        return self._value

    @value.setter
    def value(self, new_value: bool) -> None:
        if self.is_mandatory and not new_value:
            return
        self._value = new_value
        self.update(self._render())
        self.post_message(self.Changed(self, new_value))

    def _get_state_key(self) -> str:
        if self.is_mandatory:
            return "checked"
        if self._value:
            return "checked"
        return "unchecked"

    def _render(self) -> str:
        state = self.states[self._get_state_key()]
        checkbox = state["box"]
        color = state["color"]
        category_color = self._get_category_color()
        return f"[{color}]{checkbox}[/] {category_color}{self.label}[/{color}]"

    def _get_category_color(self) -> str:
        colors = {
            "core": "#F472B6", "data": "#60A5FA", "monitoring": "#34D399",
            "networking": "#FBBF24", "ai": "#A78BFA", "automation": "#FB923C",
            "communication": "#38BDF8", "management": "#94A3B8"
        }
        return f"[{colors.get(self.category, '#00D9FF')}]"

    def on_click(self) -> None:
        self.value = not self._value