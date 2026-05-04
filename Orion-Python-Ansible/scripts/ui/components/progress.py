from textual.widgets import Static

class ProgressBar(Static):
    def __init__(self, label: str, current: float, maximum: float, width: int = 40):
        super().__init__()
        self.label = label
        self.current = current
        self.maximum = maximum
        self.width = width

    def _get_color(self) -> str:
        ratio = self.current / self.maximum if self.maximum > 0 else 0
        if ratio < 0.5:
            return "#10B981"
        elif ratio < 0.8:
            return "#F59E0B"
        return "#EF4444"

    def _render(self) -> str:
        ratio = self.current / self.maximum if self.maximum > 0 else 0
        filled = int(ratio * self.width)
        bar = "█" * filled + "░" * (self.width - filled)
        color = self._get_color()
        pct = int(ratio * 100)
        return f"[{color}]{self.label}[/]: [{color}]{bar}[/{color}] {self.current:.1f}GB / {self.maximum:.1f}GB ({pct}%)"