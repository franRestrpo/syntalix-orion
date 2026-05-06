from textual.widgets import Static

class StatusIndicator(Static):
    states = {
        "success": {"icon": "✓", "color": "#10B981", "text": "Configurado"},
        "warning": {"icon": "⚠", "color": "#F59E0B", "text": "Revisar"},
        "error": {"icon": "✗", "color": "#EF4444", "text": "Error"},
        "pending": {"icon": "○", "color": "#64748B", "text": "Pendiente"},
        "loading": {"icon": "◐", "color": "#00D9FF", "text": "Cargando..."}
    }

    def __init__(self, state: str = "pending", custom_text: str = ""):
        super().__init__()
        self.state = state
        self.custom_text = custom_text

    def _render(self) -> str:
        state_info = self.states.get(self.state, self.states["pending"])
        icon = state_info["icon"]
        color = state_info["color"]
        text = self.custom_text or state_info["text"]
        return f"[{color}]{icon}[/] {text}"