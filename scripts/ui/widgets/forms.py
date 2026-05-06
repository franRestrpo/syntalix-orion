from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Input, Label
from textual.message import Message

class DynamicFormInput(Vertical):
    """Componente de formulario para una variable de entorno requerida."""
    
    class ValueChanged(Message):
        """Mensaje cuando cambia el valor."""
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
        
    def compose(self) -> ComposeResult:
        label = self.var_name if not self.description else f"{self.var_name} ({self.description})"
        yield Label(label, classes="form-label")
        yield Input(
            value=self.default_value,
            placeholder=self.var_name,
            password=self.is_password,
            id=f"input-{self.var_name}"
        )
        
    def on_input_changed(self, event: Input.Changed) -> None:
        self.post_message(self.ValueChanged(self.var_name, event.value))
