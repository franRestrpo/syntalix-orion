from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Input, Label, Static
from textual.message import Message

class SecureInputField(Vertical):
    class ValueChanged(Message):
        def __init__(self, key: str, value: str):
            self.key = key
            self.value = value
            super().__init__()

    def __init__(self, var_name: str, description: str = "", default_value: str = "", is_password: bool = False):
        super().__init__()
        self.var_name = var_name
        self.description = description
        self.default_value = default_value
        self.is_password = is_password
        self._is_masked = is_password

    def compose(self) -> ComposeResult:
        label = self.var_name if not self.description else f"{self.var_name}"
        yield Label(f"[cyan]{label}[/]", classes="secure-label")
        if self.description:
            yield Static(f"[muted]{self.description}[/]", classes="secure-desc")
        with Horizontal(classes="input-row"):
            yield Input(
                value=self.default_value,
                placeholder=self.var_name,
                password=self._is_masked and not self._is_masking_temporarily_disabled(),
                id=f"input-{self.var_name}"
            )
            yield Static("[👁]" if self._is_masked else "[👁‍🗨]", classes="toggle-btn", id=f"toggle-{self.var_name}")

    def _is_masking_temporarily_disabled(self) -> bool:
        return getattr(self, '_show_password', False)

    def on_input_changed(self, event: Input.Changed) -> None:
        self.post_message(self.ValueChanged(self.var_name, event.value))