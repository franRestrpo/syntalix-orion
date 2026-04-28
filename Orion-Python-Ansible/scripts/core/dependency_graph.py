"""
Grafo de dependencias para planificación de despliegues.

Gestiona:
- Resolución de dependencias transitivas
- Detección de ciclos
- Cálculo de recursos (RAM)
- Generación de variables seguras

Integrado con:
- core.models: Validación con Pydantic
- core.security: Generación de secretos
- core.logging_config: Logging estructurado
"""

import os
import importlib.util
from typing import Dict, List, Set, Optional, Any

# Imports de módulos internos
from core.logging_config import get_logger
from core.security import generate_secure_password

# Logger
logger = get_logger(__name__)

# Attempt to load APP_METADATA from the root catalog
APP_METADATA: Dict[str, Dict[str, Any]] = {}
_METADATA_LOADED = False

def _load_app_metadata() -> Dict[str, Dict[str, Any]]:
    """
    Carga APP_METADATA desde el catálogo de aplicaciones.
    Implementa fallback inteligente para diferentes ubicaciones.
    """
    global APP_METADATA, _METADATA_LOADED
    
    if _METADATA_LOADED:
        return APP_METADATA
    
    # Intentar importar desde apps_metadata.py en el directorio raíz
    try:
        from apps_metadata import APP_METADATA as _AM
        APP_METADATA = _AM
        logger.debug("APP_METADATA cargado desde apps_metadata")
        _METADATA_LOADED = True
        return APP_METADATA
    except ImportError:
        pass
    
    # Fallback: intentar cargar desde el directorio raíz del proyecto
    root_candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../apps_metadata.py")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../apps_metadata.py")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../apps_metadata.py")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "apps_metadata.py")),
    ]
    
    for path in root_candidates:
        if os.path.exists(path):
            logger.debug(f"Intentando cargar APP_METADATA desde: {path}")
            try:
                spec = importlib.util.spec_from_file_location("apps_metadata", path)
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    APP_METADATA = getattr(mod, "APP_METADATA", {})
                    logger.info("APP_METADATA cargado exitosamente", extra={"path": path, "count": len(APP_METADATA)})
                    _METADATA_LOADED = True
                    return APP_METADATA
            except Exception as e:
                logger.warning(f"Error cargando desde {path}: {e}")
                continue
    
    logger.warning("No se pudo cargar APP_METADATA, usando catálogo vacío")
    _METADATA_LOADED = True
    return APP_METADATA


class DependencyGraph:
    """
    Grafo de dependencias para planificación de despliegues.
    
    Lee APP_METADATA (app_id -> metadata) y resuelve dependencias transitivas.
    Detecta ciclos y genera variables seguras.
    
    Uso:
        dg = DependencyGraph()
        plan = dg.resolve_dependencies("chatwoot")
        print(f"Plan de despliegue: {plan}")
        
        # Con variables generadas
        result = dg.plan_with_vars("chatwoot")
        print(f"RAM total: {result['ram_mb_total']} MB")
        print(f"Variables: {result['vars']}")
    """

    def __init__(self, catalog: Optional[Dict[str, Dict[str, Any]]] = None) -> None:
        """
        Inicializa el grafo de dependencias.
        
        Args:
            catalog: Catálogo de aplicaciones. Si es None, carga desde APP_METADATA.
        """
        if catalog is not None:
            self.catalog: Dict[str, Dict[str, Any]] = catalog
        else:
            self.catalog = _load_app_metadata()
        
        logger.debug("DependencyGraph inicializado", extra={"catalog_size": len(self.catalog)})

    def get_metadata(self, app_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene los metadatos de una aplicación.
        
        Args:
            app_id: ID de la aplicación
            
        Returns:
            Metadatos de la app o None si no existe
        """
        return self.catalog.get(app_id)

    def resolve_dependencies(self, app_id: str) -> List[str]:
        """
        Resuelve las dependencias transitivas para una app.
        
        Args:
            app_id: ID de la aplicación
            
        Returns:
            Lista ordenada donde las dependencias vienen antes que los dependientes.
            
        Raises:
            KeyError: Si app_id o alguna dependencia no existe en el catálogo.
            ValueError: Si se detecta un ciclo en las dependencias.
        """
        if app_id not in self.catalog:
            logger.error("App desconocida", extra={"app_id": app_id})
            raise KeyError(f"App '{app_id}' no encontrada en el catálogo")

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
            
            # Obtener dependencias de los metadatos
            deps = self.catalog.get(node, {}).get("dependencies", [])
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
        logger.info("Dependencias resueltas", extra={
            "app_id": app_id,
            "plan_size": len(order),
            "plan": order
        })
        
        return order

    def total_ram_for_plan(self, app_id: str) -> int:
        """
        Calcula la RAM total necesaria para el plan de despliegue.
        
        Args:
            app_id: ID de la aplicación
            
        Returns:
            RAM total en MB
        """
        plan = self.resolve_dependencies(app_id)
        total = 0
        
        for aid in plan:
            meta = self.catalog.get(aid, {})
            ram = meta.get("ram_mb", 0)
            total += int(ram)
        
        logger.debug("RAM calculada", extra={
            "app_id": app_id,
            "total_mb": total,
            "apps_count": len(plan)
        })
        
        return total

    def _generate_secret_value(self, var_def: Dict[str, Any]) -> str:
        """
        Genera un valor secreto seguro.
        
        Args:
            var_def: Definición de la variable
            
        Returns:
            Valor generado (o hasheado si se especifica transform)
        """
        length = int(var_def.get("length", 32))
        
        # Generar token seguro
        value = generate_secure_password(length=length)
        
        # Aplicar transformación si se especifica
        transform = var_def.get("transform")
        if transform == "bcrypt":
            try:
                from core.security import hash_password_bcrypt
                value = hash_password_bcrypt(value)
                logger.debug("Secret transformado con bcrypt")
            except ImportError:
                logger.warning("bcrypt no disponible, usando token plano")
        
        return value

    def generate_vars_for_plan(self, app_id: str) -> Dict[str, Any]:
        """
        Genera variables de entorno para el plan de despliegue.
        
        Args:
            app_id: ID de la aplicación
            
        Returns:
            Diccionario de variables en formato APPID__VARNAME: value
        """
        plan = self.resolve_dependencies(app_id)
        vars_out: Dict[str, Any] = {}
        
        for aid in plan:
            meta = self.catalog.get(aid, {})
            vars_def = meta.get("variables", {}) or {}
            
            for var_name, var_def in vars_def.items():
                # Generar nombre de variable con prefijo de app
                key = f"{aid}__{var_name}".upper()
                
                if var_def.get("type") == "secret":
                    # Generar secreto automáticamente
                    value = self._generate_secret_value(var_def)
                    vars_out[key] = value
                    logger.debug("Variable secreta generada", extra={
                        "key": key,
                        "length": len(value)
                    })
                else:
                    # Usar valor por defecto
                    value = var_def.get("default", "")
                    vars_out[key] = value
        
        logger.info("Variables generadas", extra={
            "app_id": app_id,
            "vars_count": len(vars_out)
        })
        
        return vars_out

    def plan_with_vars(self, app_id: str) -> Dict[str, Any]:
        """
        Genera un plan completo con dependencias, RAM y variables.
        
        Args:
            app_id: ID de la aplicación
            
        Returns:
            Diccionario con:
            - plan: Lista ordenada de apps
            - ram_mb_total: RAM total requerida
            - vars: Variables generadas
        """
        logger.debug("Generando plan completo", extra={"app_id": app_id})
        
        plan = self.resolve_dependencies(app_id)
        ram = self.total_ram_for_plan(app_id)
        generated_vars = self.generate_vars_for_plan(app_id)
        
        result = {
            "plan": plan,
            "ram_mb_total": ram,
            "vars": generated_vars,
        }
        
        logger.info("Plan generado exitosamente", extra={
            "app_id": app_id,
            "plan_size": len(plan),
            "ram_mb_total": ram
        })
        
        return result

    def validate_plan(self, app_id: str, max_ram_mb: int = None) -> Dict[str, Any]:
        """
        Valida un plan de despliegue.
        
        Args:
            app_id: ID de la aplicación
            max_ram_mb: RAM máxima disponible (opcional)
            
        Returns:
            Diccionario con validaciones y advertencias
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
                f"RAM requerida ({total_ram} MB) excede límite ({max_ram_mb} MB)"
            )
            logger.warning("RAM excede límite", extra={
                "required": total_ram,
                "limit": max_ram_mb
            })
        
        # Validar categorías
        categories = set()
        for aid in plan:
            meta = self.catalog.get(aid, {})
            cat = meta.get("category", "Unknown")
            categories.add(cat)
        
        logger.info("Plan validado", extra={
            "app_id": app_id,
            "valid": len(errors) == 0,
            "warnings_count": len(warnings),
            "errors_count": len(errors)
        })
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "plan": plan,
            "ram_mb_total": total_ram,
            "categories": list(categories),
        }

    def plan_with_vars_multi(self, app_ids: List[str]) -> Dict[str, Any]:
        """
        Genera un plan completo para múltiples aplicaciones seleccionadas.

        Este método:
        1. Calcula el grafo de dependencias unifydo para todas las apps
        2. Genera variables seguras para todo el plan
        3. Calcula la RAM total

        Args:
            app_ids: Lista de IDs de aplicaciones seleccionadas por el usuario

        Returns:
            Diccionario con:
            - plan: Lista ordenada de apps (incluye dependencias transitivas)
            - ram_mb_total: RAM total requerida
            - vars: Variables generadas para todas las apps
            - selected_apps: Lista de apps originalmente seleccionadas
            - dependencies: Lista de dependencias auto-añadidas

        Raises:
            KeyError: Si alguna app o dependencia no existe
            ValueError: Si hay dependencias circulares
        """
        if not app_ids:
            logger.warning("plan_with_vars_multi llamado con lista vacía")
            return {
                "plan": [],
                "ram_mb_total": 0,
                "vars": {},
                "selected_apps": [],
                "dependencies": []
            }

        logger.debug("Generando plan multi-app", extra={"app_ids": app_ids})

        # Validar que todas las apps existan
        for app_id in app_ids:
            if app_id not in self.catalog:
                raise KeyError(f"Aplicación '{app_id}' no encontrada en el catálogo")

        # Conjunto para tracking de apps en el plan
        plan_set: Set[str] = set()
        ordered_plan: List[str] = []
        visited: Set[str] = set()

        def resolve_with_deps(app_id: str) -> None:
            """Resuelve dependencias recursivamente."""
            if app_id in visited:
                return
            visited.add(app_id)

            # Añadir todas las dependencias primero
            deps = self.catalog.get(app_id, {}).get("dependencies", [])
            for dep in deps:
                if dep not in self.catalog:
                    raise KeyError(f"Dependencia '{dep}' no encontrada")
                resolve_with_deps(dep)
                if dep not in plan_set:
                    plan_set.add(dep)
                    ordered_plan.append(dep)

            # Añadir la app misma
            if app_id not in plan_set:
                plan_set.add(app_id)
                ordered_plan.append(app_id)

        # Resolver todas las apps seleccionadas
        for app_id in app_ids:
            resolve_with_deps(app_id)

        # Calcular RAM total
        ram_total = 0
        for aid in ordered_plan:
            meta = self.catalog.get(aid, {})
            ram_total += int(meta.get("ram_mb", 0))

        # Generar variables para todas las apps del plan
        all_vars: Dict[str, Any] = {}
        
        # Añadir la lista de roles activos para Ansible
        all_vars["ansible_enabled_roles"] = ordered_plan
        
        for aid in ordered_plan:
            meta = self.catalog.get(aid, {})
            vars_def = meta.get("variables", {}) or {}

            for var_name, var_def in vars_def.items():
                key = f"{aid}__{var_name}".upper()

                if var_def.get("type") == "secret":
                    value = self._generate_secret_value(var_def)
                    all_vars[key] = value
                else:
                    value = var_def.get("default", "")
                    all_vars[key] = value

        # Separar selected_apps de dependencies
        selected_apps = [aid for aid in ordered_plan if aid in app_ids]
        dependencies = [aid for aid in ordered_plan if aid not in app_ids]

        result = {
            "plan": ordered_plan,
            "ram_mb_total": ram_total,
            "vars": all_vars,
            "selected_apps": selected_apps,
            "dependencies": dependencies
        }

        logger.info("Plan multi-app generado", extra={
            "total_apps": len(ordered_plan),
            "selected": len(selected_apps),
            "dependencies": len(dependencies),
            "ram_total": ram_total
        })

        return result


# Ejemplo de uso directo
if __name__ == "__main__":
    from core.logging_config import setup_logging
    
    # Configurar logging para uso directo
    setup_logging("INFO")
    
    dg = DependencyGraph()
    app = "chatwoot"
    
    try:
        result = dg.plan_with_vars(app)
        print(f"\n📋 Plan de despliegue para '{app}':")
        print(f"   Orden: {result['plan']}")
        print(f"   RAM total: {result['ram_mb_total']} MB")
        print(f"   Variables: {len(result['vars'])} generadas")
        
        # Mostrar algunas variables (sin valores sensibles)
        for key, value in list(result['vars'].items())[:5]:
            masked = value[:8] + "..." if len(value) > 8 else "****"
            print(f"   - {key}: {masked}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


__all__ = ["DependencyGraph", "APP_METADATA"]
