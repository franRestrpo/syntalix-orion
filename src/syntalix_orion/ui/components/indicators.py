"""
Widget StatusIndicator - Syntalix-Orion.

Componente visual de indicador de estado para mostrar el estado de
configuración de servicios o componentes. Extiende Static y renderiza
un icono con texto descriptivo según el estado.

Estados Soportados:
    - success: Configurado correctamente (✓ verde).
    - warning: Requiere revisión (⚠ amarillo).
    - error: Hay errores (✗ rojo).
    - pending: No configurado aún (○ gris).
    - loading: En proceso (◐ cyan).

Autor: Syntalix-Orion Team
Versión: 2.0.0
"""

from textual.widgets import Static


class StatusIndicator(Static):
    """
    Indicador visual de estado con icono y texto.

    Este widget muestra el estado de un componente o servicio
    con un icono coloreado y texto descriptivo.

    Atributos:
        state (str): Estado actual del indicador.
        custom_text (str): Texto personalizado (sobrescribe el default).

    Ejemplo:
        >>> indicator = StatusIndicator(state="success", custom_text="Traefik")
        >>> print(indicator._render())
        [✓] Traefik
    """

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
        """
        Renderiza el indicador con formato markup de Textual.

        Returns:
            str: String con formato "[icon] texto" con colores.
        """
        state_info = self.states.get(self.state, self.states["pending"])
        icon = state_info["icon"]
        color = state_info["color"]
        text = self.custom_text or state_info["text"]
        return f"[{color}]{icon}[/] {text}"