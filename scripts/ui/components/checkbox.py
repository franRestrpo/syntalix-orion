"""
Widget ModernCheckbox - Syntalix-Orion.

Componente de checkbox personalizado que extiende Static para mostrar
una interfaz visual de selección coniconos de estado y soporte para
categorías de colores. Diseñado para la pantalla de selección del
catálogo de aplicaciones.

Estados del Widget:
    - unchecked: Sin seleccionar (círculo vacío).
    - checked: Seleccionado (círculo lleno).
    - focused: Con foco de teclado.
    - disabled: Deshabilitado (para items mandatory).

Autor: Syntalix-Orion Team
Versión: 2.0.0
"""

from textual.widgets import Static
from textual.message import Message


class ModernCheckbox(Static):
    """
    Widget de checkbox moderno con soporte para estados visuales y tooltip.

    Este componente representa un item selectable en el catálogo de
    aplicaciones. Muestra un checkbox estilizado coniconos de estado
    y colores por categoría.

    Atributos:
        app_id (str): Identificador único de la aplicación asociada.
        is_mandatory (bool): Si True, el item no puede deseleccionarse.
        category (str): Categoría de la app para color (core, data, etc.).
        _suppress_events (bool): Flag interno para evitar eventos en batch.

    Mensajes Emitidos:
        Changed: Se emite cuando el valor del checkbox cambia.

    Ejemplo:
        >>> checkbox = ModernCheckbox(
        ...     label="Traefik (v1.0) - 256MB",
        ...     app_id="traefik",
        ...     is_mandatory=False,
        ...     value=True,
        ...     tooltip="ID: traefik\\nRAM: 256MB",
        ...     category="networking"
        ... )
    """

    states = {
        "unchecked": {"box": "○", "color": "#64748B"},
        "checked": {"box": "●", "color": "#00D9FF"},
        "focused": {"box": "◉", "color": "#FFFFFF"},
        "disabled": {"box": "○", "color": "#374151"}
    }

    class Changed(Message):
        """Mensaje emitido cuando el estado del checkbox cambia."""

        def __init__(self, checkbox: "ModernCheckbox", value: bool) -> None:
            super().__init__()
            self.checkbox = checkbox
            self.value = value

    def __init__(self, label: str, app_id: str, is_mandatory: bool, value: bool = False,
                 tooltip: str = "", category: str = "core", **kwargs):
        self.app_id = app_id
        self.is_mandatory = is_mandatory
        self._value = value
        self._tooltip = tooltip
        self.category = category
        self._suppress_events = False
        super().__init__(id=f"checkbox-{app_id}", **kwargs)
        self.label = label

    @property
    def checkbox(self) -> "ModernCheckbox":
        """Property que devuelve self para compatibilidad con mensajes."""
        return self

    @property
    def value(self) -> bool:
        """Obtiene el estado actual del checkbox."""
        return self._value

    @value.setter
    def value(self, new_value: bool) -> None:
        """
        Establece el valor del checkbox con validación de mandatory.

        Args:
            new_value (bool): Nuevo estado del checkbox.

        Notes:
            Si is_mandatory es True, no permite deseleccionar el checkbox.
        """
        if self.is_mandatory and not new_value:
            return
        if self._value == new_value:
            return
        self._value = new_value
        self.refresh()
        if not self._suppress_events:
            self.post_message(self.Changed(self, new_value))

    def set_value_without_event(self, new_value: bool) -> None:
        """
        Establece valor sin emitir evento (para batch updates).

        Args:
            new_value (bool): Nuevo estado sin disparar Changed.
        """
        if self._value == new_value:
            return
        self._value = new_value
        self.refresh()

    def _get_state_key(self) -> str:
        """
        Determina la clave de estado visual del checkbox.

        Returns:
            str: Clave de estado ('checked', 'unchecked', etc.).
        """
        if self.is_mandatory:
            return "checked"
        if self._value:
            return "checked"
        return "unchecked"

    def render(self) -> str:
        """
        Renderiza el checkbox con formato markup de Textual.

        Returns:
            str: String con markup para display del checkbox.
        """
        state = self.states[self._get_state_key()]
        checkbox = state["box"]
        color = state["color"]
        category_color = self._get_category_color()
        return f"[{color}]{checkbox}[/] [{category_color}]{self.label}[/]"

    def _get_category_color(self) -> str:
        """
        Obtiene el color de la categoría del widget.

        Returns:
            str: Código hexadecimal del color de categoría.
        """
        colors = {
            "core": "#F472B6", "data": "#60A5FA", "monitoring": "#34D399",
            "networking": "#FBBF24", "ai": "#A78BFA", "automation": "#FB923C",
            "communication": "#38BDF8", "management": "#94A3B8"
        }
        return colors.get(self.category, '#00D9FF')

    def on_click(self) -> None:
        """Maneja el evento de click, alternando el valor del checkbox."""
        if self.is_mandatory:
            return
        self.value = not self._value