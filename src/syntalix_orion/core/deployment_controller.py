"""
Controlador de Despliegue (DeploymentController) - Syntalix-Orion.

Este módulo implementa el patrón de Controlador para separar la lógica de negocio
de la interfaz de usuario (Textual UI). Encapsula toda la lógica de resolución
de dependencias transitivas, permitiendo que SelectionScreen sea puramente
presentacional.

Principios aplicados:
    - SRP (Single Responsibility Principle): Este controlador solo maneja
      la lógica del grafo de selección de aplicaciones.
    - Dependency Injection: Recibe el catálogo y el state_store como
      dependencias, facilitando el testing.
    - Facade Pattern: Oculta la complejidad del grafo de dependencias
      detrás de una interfaz simple.
"""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field

from syntalix_orion.core.models import AppMetadata


@dataclass
class ToggleResult:
    """Resultado de una operación de toggle (selección/deselección)."""
    success: bool
    message: str = ""
    auto_added: List[str] = field(default_factory=list)
    auto_removed: List[str] = field(default_factory=list)


class DeploymentController:
    """
    Controlador de lógica de selección y dependencias.

    Maneja la lógica de negocio relacionada con la selección de aplicaciones
    y la resolución automática de dependencias transitivas. Este controlador
    es el único responsable de modificar el estado de selección.

    Uso:
        >>> controller = DeploymentController(catalog, state_store)
        >>> result = controller.toggle_app("traefik", True)
        >>> if not result.success:
        ...     print(f"Bloqueado: {result.message}")
    """

    def __init__(
        self,
        catalog: Dict[str, AppMetadata],
        state_store
    ):
        """
        Inicializa el controlador con el catálogo y el estado.

        Args:
            catalog: Diccionario de aplicaciones por ID.
            state_store: Instancia de StateStore para persistencia de estado.
        """
        self.catalog = catalog
        self.state_store = state_store
        self.user_selected: Set[str] = set()
        self.auto_dependencies: Set[str] = set()

    def toggle_app(self, app_id: str, is_selected: bool) -> ToggleResult:
        """
        Maneja el toggle de selección de una aplicación.

        Args:
            app_id: ID de la aplicación a togglear.
            is_selected: True para seleccionar, False para deseleccionar.

        Returns:
            ToggleResult con el resultado de la operación.
        """
        if is_selected:
            return self._select_app(app_id)
        else:
            return self._deselect_app(app_id)

    def _select_app(self, app_id: str) -> ToggleResult:
        """Selecciona una app y añade sus dependencias automáticamente."""
        self.state_store.add_app(app_id)
        self.user_selected.add(app_id)

        auto_added: List[str] = []
        app_meta = self.catalog.get(app_id)
        if app_meta and app_meta.dependencies:
            for dep_id in app_meta.dependencies:
                if dep_id not in self.state_store.selected_apps:
                    self.state_store.add_app(dep_id)
                    self.auto_dependencies.add(dep_id)
                    auto_added.append(dep_id)

        return ToggleResult(
            success=True,
            auto_added=auto_added
        )

    def _deselect_app(self, app_id: str) -> ToggleResult:
        """Deselecciona una app verificando bloqueos por dependencias."""
        dependents = self._get_dependents(app_id)
        if dependents:
            dep_names = [self.catalog.get(d).name for d in dependents if self.catalog.get(d)]
            return ToggleResult(
                success=False,
                message=f"Requiere: {', '.join(dep_names)}"
            )

        if app_id not in self.user_selected:
            return ToggleResult(success=False, message="No se puede deseleccionar dependencia automática")

        self.state_store.remove_app(app_id)
        self.user_selected.discard(app_id)

        removed = self._remove_transitive_orphan_dependencies(app_id)

        return ToggleResult(
            success=True,
            auto_removed=removed
        )

    def _get_dependents(self, app_id: str) -> List[str]:
        """
        Obtiene las apps que dependen de app_id.

        Args:
            app_id: ID de la aplicación a verificar.

        Returns:
            Lista de IDs de aplicaciones que dependen de app_id.
        """
        dependents = []
        for selected_id in self.state_store.selected_apps:
            if selected_id == app_id:
                continue
            sel_meta = self.catalog.get(selected_id)
            if sel_meta and app_id in sel_meta.dependencies:
                dependents.append(sel_meta.name)
        return dependents

    def _remove_transitive_orphan_dependencies(self, app_id: str) -> List[str]:
        """
        Remueve dependencias huérfanas después de deseleccionar una app.

        Args:
            app_id: ID de la aplicación removida.

        Returns:
            Lista de IDs de apps removidas por quedar huérfanas.
        """
        removed: List[str] = []
        dependents_to_check = [app_id]

        while dependents_to_check:
            current = dependents_to_check.pop()
            for aid, app in self.catalog.items():
                if current in app.dependencies and aid in self.state_store.selected_apps:
                    if aid not in self.user_selected:
                        self.state_store.remove_app(aid)
                        self.auto_dependencies.discard(aid)
                        removed.append(aid)
                        dependents_to_check.append(aid)

        return removed

    def get_selected_with_deps(self) -> Set[str]:
        """Retorna todas las apps seleccionadas (usuario + auto-añadidas)."""
        return set(self.state_store.selected_apps)

    def get_user_selected(self) -> Set[str]:
        """Retorna solo las apps seleccionadas explícitamente por el usuario."""
        return set(self.user_selected)

    def get_auto_dependencies(self) -> Set[str]:
        """Retorna las apps añadidas automáticamente como dependencias."""
        return set(self.auto_dependencies)

    def is_auto_added(self, app_id: str) -> bool:
        """Verifica si una app fue añadida automáticamente como dependencia."""
        return app_id in self.auto_dependencies

    def reset(self) -> None:
        """Limpia todo el estado del controlador."""
        self.user_selected.clear()
        self.auto_dependencies.clear()
        self.state_store.clear_selections()