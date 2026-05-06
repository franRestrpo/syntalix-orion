"""
Widget ProgressBar - Syntalix-Orion.

Componente de barra de progreso para visualizar el consumo de recursos
(RAM, CPU, disco) en la interfaz de terminal. Extiende Static y renderiza
una barra ASCII estilizada con colores dinámicos según el nivel de uso.

Colores de Estado:
    - Verde (#10B981): Uso inferior al 50%.
    - Amarillo (#F59E0B): Uso entre 50% y 80%.
    - Rojo (#EF4444): Uso superior al 80%.

Autor: Syntalix-Orion Team
Versión: 2.0.0
"""

from textual.widgets import Static


class ProgressBar(Static):
    """
    Barra de progreso visual con colores dinámicos.

    Este widget renderiza una barra de progreso ASCII que indica
    el uso actual versus el máximo de un recurso (ej. RAM).

    Atributos:
        label (str): Etiqueta descriptiva del recurso.
        current (float): Valor actual del recurso.
        maximum (float): Valor máximo del recurso.
        width (int): Ancho de la barra en caracteres.

    Ejemplo:
        >>> bar = ProgressBar(label="RAM", current=4.2, maximum=8.0)
        >>> print(bar._render())
        RAM: [███░░░░░░░░░░░] 4.2GB / 8.0GB (52%)
    """

    def __init__(self, label: str, current: float, maximum: float, width: int = 40):
        super().__init__()
        self.label = label
        self.current = current
        self.maximum = maximum
        self.width = width

    def _get_color(self) -> str:
        """
        Determina el color según el porcentaje de uso.

        Returns:
            str: Código hexadecimal del color según umbral:
                - < 50%: #10B981 (verde)
                - 50-80%: #F59E0B (amarillo)
                - > 80%: #EF4444 (rojo)
        """
        ratio = self.current / self.maximum if self.maximum > 0 else 0
        if ratio < 0.5:
            return "#10B981"
        elif ratio < 0.8:
            return "#F59E0B"
        return "#EF4444"

    def _render(self) -> str:
        """
        Renderiza la barra de progreso con formato markup.

        Returns:
            str: String con formato "[label]: [barra] porcentaje".
        """
        ratio = self.current / self.maximum if self.maximum > 0 else 0
        filled = int(ratio * self.width)
        bar = "█" * filled + "░" * (self.width - filled)
        color = self._get_color()
        pct = int(ratio * 100)
        return f"[{color}]{self.label}[/]: [{color}]{bar}[/{color}] {self.current:.1f}GB / {self.maximum:.1f}GB ({pct}%)"