"""
Gestor de Estado Centralizado - Syntalix-Orion.

Módulo que define las estructuras de datos para el almacenamiento global
del estado de la aplicación TUI. Utiliza dataclasses para garantizar
inmutabilidad y tipo de datos en las transacciones entre pantallas.

Arquitectura del Estado:
    StateStore actúa como almacén de estado global compartido entre
    todas las pantallas (Selection, Config, Deploy). El estado incluye:
        - Aplicaciones seleccionadas por el usuario.
        - Variables de configuración ingresadas.
        - Plan de despliegue calculado.

Autor: Syntalix-Orion Team
Versión: 2.0.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Any, Optional


@dataclass
class DeploymentPlan:
    """
    Estructura de datos que representa el plan de despliegue calculado.

    Attributes:
        plan (List[str]): Lista ordenada de IDs de aplicaciones a desplegar.
        ram_total_mb (int): Cantidad total de RAM estimada en megabytes.
        vars_generated (Dict[str, Any]): Variables de configuración generadas.
        dependencies (List[str]): Lista de IDs de dependencias añadidas.
        has_warning (bool): Indica si hay advertencias en el plan.
        warning_message (Optional[str]): Mensaje descriptivo de la advertencia.
    """

    plan: List[str] = field(default_factory=list)
    ram_total_mb: int = 0
    vars_generated: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    has_warning: bool = False
    warning_message: Optional[str] = None


@dataclass
class StateStore:
    """
    Gestor de estado centralizado para la TUI de Syntalix-Orion.

    Esta clase almacena el estado global de la aplicación, permitiendo
    que las pantallas compartan información sin acoplamiento directo.
    Se inyecta como atributo 'state_store' en la instancia de OrionTUI.

    Attributes:
        selected_apps (Set[str]): Conjunto de IDs de apps seleccionadas.
        user_variables (Dict[str, str]): Variables ingresadas por el usuario.
        deployment_plan (Optional[DeploymentPlan]): Plan calculado de despliegue.

    Ejemplo:
        >>> app = OrionTUI()
        >>> app.state_store.add_app("traefik")
        >>> app.state_store.deployment_plan = my_plan
    """

    selected_apps: Set[str] = field(default_factory=set)
    user_variables: Dict[str, str] = field(default_factory=dict)
    deployment_plan: Optional[DeploymentPlan] = None

    def clear_selections(self) -> None:
        """Limpia todas las selecciones de aplicaciones del estado."""
        self.selected_apps.clear()

    def add_app(self, app_id: str) -> None:
        """
        Añade una aplicación al conjunto de selections.

        Args:
            app_id (str): Identificador único de la aplicación.
        """
        self.selected_apps.add(app_id)

    def remove_app(self, app_id: str) -> None:
        """
        Elimina una aplicación del conjunto de selections.

        Args:
            app_id (str): Identificador único de la aplicación.
        """
        self.selected_apps.discard(app_id)
