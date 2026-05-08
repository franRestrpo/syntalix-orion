"""
Motor de Resolucin de Dependencias para el Ecosistema Syntalix-Orion.

Este mdulo constituye el ncleo de inteligencia del orquestador, responsable de 
gestionar las interrelaciones complejas entre aplicaciones. Su objetivo es 
garantizar que cualquier despliegue sea tcnicamente viable, ordenado y 
optimizado en trminos de recursos.

Responsabilidades:
    - Resolucin Topolgica: Determina el orden exacto de despliegue (DFS).
    - Anlisis de Ciclos: Previene bloqueos por dependencias circulares.
    - Proyeccin de Recursos: Calcula el consumo terico de memoria RAM.
    - Validacin de Integridad: Asegura que todas las dependencias declaradas existan.
"""

from typing import Dict, List, Set, Optional, Any

from syntalix_orion.core.logging_config import get_logger
from syntalix_orion.core.models import AppMetadata
from syntalix_orion.core.registry import get_registry

logger = get_logger(__name__)

class DependencyGraph:
    """
    Abstraccin de Grafo para el Anlisis de Despliegues.
    
    Proporciona los algoritmos y la lgica de negocio necesarios para transformar 
    una seleccin arbitraria de aplicaciones en un plan de ejecucin determinista.
    """

    def __init__(self, catalog: Optional[Dict[str, AppMetadata]] = None) -> None:
        """
        Inicializa una nueva instancia del motor de dependencias.
        
        Args:
            catalog: Catlogo de aplicaciones. Si se omite, carga desde AppRegistry.
        """
        if catalog is not None:
            from syntalix_orion.core.models import AppMetadata
            # Convert raw dicts to AppMetadata if needed (for backwards compatibility with tests)
            self.catalog = {
                k: AppMetadata(**v) if isinstance(v, dict) else v 
                for k, v in catalog.items()
            }
        else:
            self.catalog = get_registry().load_all()
        
        logger.debug("DependencyGraph inicializado", extra={"catalog_size": len(self.catalog)})

    def get_metadata(self, app_id: str) -> Optional[AppMetadata]:
        """
        Recupera la ficha tcnica (metadatos) de una aplicacin especfica.
        """
        return self.catalog.get(app_id)

    def resolve_dependencies(self, app_id: str) -> List[str]:
        """
        Resuelve de forma recursiva la jerarqua completa de dependencias de una aplicacin.
        Aplica DFS para orden topolgico.
        """
        if app_id not in self.catalog:
            logger.error("App desconocida", extra={"app_id": app_id})
            raise KeyError(f"App '{app_id}' no encontrada en el catlogo")

        visited: Set[str] = set()
        order: List[str] = []

        def dfs(node: str, visiting: Set[str]) -> None:
            if node in visited:
                return
            if node in visiting:
                cycle = " -> ".join(list(visiting) + [node])
                logger.error("Dependencia circular detectada", extra={"cycle": cycle})
                raise ValueError(f"Dependencia circular detectada: {cycle}")
            
            visiting.add(node)
            
            app_meta = self.catalog.get(node)
            deps = app_meta.dependencies if app_meta and app_meta.dependencies else []
            for dep in deps:
                if dep not in self.catalog:
                    logger.error("Dependencia no encontrada", extra={
                        "app": node,
                        "missing_dep": dep
                    })
                    raise KeyError(f"Dependencia '{dep}' para app '{node}' no encontrada")
                dfs(dep, visiting)
            
            visiting.remove(node)
            visited.add(node)
            order.append(node)

        logger.debug("Resolviendo dependencias", extra={"app_id": app_id})
        dfs(app_id, set())
        
        return order

    def total_ram_for_plan(self, app_id: str) -> int:
        """
        Calcula la demanda total de memoria RAM para un plan de despliegue dado.
        """
        plan = self.resolve_dependencies(app_id)
        total = 0
        
        for aid in plan:
            meta = self.catalog.get(aid)
            ram = meta.ram_mb if meta else 0
            total += int(ram)
        
        return total

    def validate_plan(self, app_id: str, max_ram_mb: int = None) -> Dict[str, Any]:
        """
        Realiza una auditora tcnica de un plan de despliegue potencial.
        """
        warnings = []
        errors = []
        
        try:
            plan = self.resolve_dependencies(app_id)
        except (KeyError, ValueError) as e:
            errors.append(str(e))
            return {"valid": False, "errors": errors, "warnings": warnings}
        
        # Validar RAM
        total_ram = self.total_ram_for_plan(app_id)
        if max_ram_mb and total_ram > max_ram_mb:
            warnings.append(
                f"RAM requerida ({total_ram} MB) excede lmite ({max_ram_mb} MB)"
            )
        
        # Validar categoras
        categories = set()
        for aid in plan:
            meta = self.catalog.get(aid)
            cat = meta.category if meta else "Unknown"
            categories.add(cat)
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "plan": plan,
            "ram_mb_total": total_ram,
            "categories": list(categories),
        }

    def resolve_multi_dependencies(self, app_ids: List[str]) -> List[str]:
        """
        Resuelve dependencias conjuntas para mltiples aplicaciones, garantizando
        el orden topolgico sin duplicados.
        """
        plan_set: Set[str] = set()
        ordered_plan: List[str] = []
        visited: Set[str] = set()

        def resolve_with_deps(app_id: str) -> None:
            if app_id in visited:
                return
            visited.add(app_id)

            app_meta = self.catalog.get(app_id)
            deps = app_meta.dependencies if app_meta and app_meta.dependencies else []
            for dep in deps:
                if dep not in self.catalog:
                    raise KeyError(f"Dependencia '{dep}' no encontrada")
                resolve_with_deps(dep)
                if dep not in plan_set:
                    plan_set.add(dep)
                    ordered_plan.append(dep)

            if app_id not in plan_set:
                plan_set.add(app_id)
                ordered_plan.append(app_id)

        for app_id in app_ids:
            if app_id not in self.catalog:
                raise KeyError(f"Aplicacin '{app_id}' no encontrada en el catlogo")
            resolve_with_deps(app_id)

        return ordered_plan

    def plan_multi(self, app_ids: List[str]) -> Dict[str, Any]:
        """
        Genera el esqueleto topolgico del plan para mltiples aplicaciones.
        """
        if not app_ids:
            return {
                "plan": [],
                "ram_mb_total": 0,
                "selected_apps": [],
                "dependencies": []
            }

        ordered_plan = self.resolve_multi_dependencies(app_ids)

        ram_total = 0
        for aid in ordered_plan:
            meta = self.catalog.get(aid)
            ram_total += int(meta.ram_mb) if meta else 0

        selected_apps = [aid for aid in ordered_plan if aid in app_ids]
        dependencies = [aid for aid in ordered_plan if aid not in app_ids]

        return {
            "plan": ordered_plan,
            "ram_mb_total": ram_total,
            "selected_apps": selected_apps,
            "dependencies": dependencies
        }

__all__ = ["DependencyGraph"]