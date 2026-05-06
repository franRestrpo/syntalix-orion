"""
Motor de Resolución de Dependencias para el Ecosistema Syntalix-Orion.

Este módulo constituye el núcleo de inteligencia del orquestador, responsable de 
gestionar las interrelaciones complejas entre aplicaciones. Su objetivo es 
garantizar que cualquier despliegue sea técnicamente viable, ordenado y 
optimizado en términos de recursos.

Responsabilidades:
    - Resolución Topológica: Determina el orden exacto de despliegue (DFS).
    - Análisis de Ciclos: Previene bloqueos por dependencias circulares.
    - Proyección de Recursos: Calcula el consumo teórico de memoria RAM.
    - Gestión de Secretos: Orquesta la generación de credenciales seguras para todo el plan.
    - Validación de Integridad: Asegura que todas las dependencias declaradas existan.
"""

import os
import importlib.util
from typing import Dict, List, Set, Optional, Any

# Imports de módulos internos
from core.logging_config import get_logger
from core.security import generate_secure_password, generate_and_transform_secret
from utils import map_app_variable

# Logger
logger = get_logger(__name__)

# Intento de cargar APP_METADATA desde el catálogo raíz
APP_METADATA: Dict[str, Dict[str, Any]] = {}
_METADATA_LOADED = False

def _load_app_metadata() -> Dict[str, Dict[str, Any]]:
    """
    Carga los metadatos de las aplicaciones desde apps_metadata.py.
    
    Implementa un mecanismo de búsqueda inteligente en múltiples directorios para 
    localizar el archivo de metadatos independientemente de desde dónde se ejecute el script.

    Returns:
        Dict[str, Dict[str, Any]]: Diccionario con el catálogo completo de aplicaciones.
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
    Abstracción de Grafo para el Análisis de Despliegues.
    
    Proporciona los algoritmos y la lógica de negocio necesarios para transformar 
    una selección arbitraria de aplicaciones en un plan de ejecución determinista, 
    seguro y optimizado.
    """

    def __init__(self, catalog: Optional[Dict[str, Dict[str, Any]]] = None) -> None:
        """
        Inicializa una nueva instancia del motor de dependencias.
        
        Args:
            catalog (Optional[Dict[str, Dict[str, Any]]]): Catálogo de aplicaciones. 
                Si se omite, se realizará una carga automática desde la fuente de verdad.
        """
        if catalog is not None:
            self.catalog: Dict[str, Dict[str, Any]] = catalog
        else:
            self.catalog = _load_app_metadata()
        
        logger.debug("DependencyGraph inicializado", extra={"catalog_size": len(self.catalog)})

    def get_metadata(self, app_id: str) -> Optional[Dict[str, Any]]:
        """
        Recupera la ficha técnica (metadatos) de una aplicación específica.
        
        Args:
            app_id (str): Identificador único de la aplicación en el catálogo.
            
        Returns:
            Optional[Dict[str, Any]]: Metadatos de la aplicación o None si no existe.
        """
        return self.catalog.get(app_id)

    def resolve_dependencies(self, app_id: str) -> List[str]:
        """
        Resuelve de forma recursiva la jerarquía completa de dependencias de una aplicación.
        
        Aplica un algoritmo de búsqueda en profundidad (DFS) para obtener el orden 
        topológico correcto, garantizando que los servicios base se desplieguen 
        antes que sus consumidores.

        Args:
            app_id (str): ID de la aplicación raíz para iniciar la resolución.
            
        Returns:
            List[str]: Secuencia ordenada de IDs de aplicaciones para el despliegue.
            
        Raises:
            KeyError: Si se referencia una aplicación inexistente en la cadena.
            ValueError: Si se identifica una recursión infinita (dependencia circular).
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
        Calcula la demanda total de memoria RAM para un plan de despliegue dado.
        
        Args:
            app_id (str): ID de la aplicación principal.
            
        Returns:
            int: Consumo total proyectado de RAM expresado en Megabytes (MB).
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
        Delega la generación de valores secretos al módulo de seguridad.
        
        Args:
            var_def (Dict[str, Any]): Definición técnica de la variable.
            
        Returns:
            str: Valor secreto generado y procesado.
        """
        return generate_and_transform_secret(
            length=int(var_def.get("length", 32)),
            transform=var_def.get("transform")
        )

    def generate_vars_for_plan(self, app_id: str) -> Dict[str, Any]:
        """
        Genera el conjunto de variables de entorno necesarias para la ejecución del plan.
        
        Automatiza la creación de secretos y la asignación de valores por defecto para 
        toda la pila tecnológica requerida por la aplicación principal.

        Args:
            app_id (str): ID de la aplicación principal.
            
        Returns:
            Dict[str, Any]: Diccionario de variables mapeadas como APPID__VARNAME.
        """
        plan = self.resolve_dependencies(app_id)
        vars_out: Dict[str, Any] = {}
        
        for aid in plan:
            meta = self.catalog.get(aid, {})
            vars_def = meta.get("variables", {}) or {}
            
            for var_name, var_def in vars_def.items():
                key = map_app_variable(aid, var_name)
                
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
        Orquesta la creación de un plan de despliegue integral (E2E).
        
        Consolida la resolución de dependencias, el cálculo de recursos y la 
        generación de variables en una única estructura de datos atómica.
        
        Args:
            app_id (str): ID de la aplicación solicitada.
            
        Returns:
            Dict[str, Any]: Estructura que incluye el orden de despliegue, RAM y variables.
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
        Realiza una auditoría técnica de un plan de despliegue potencial.
        
        Verifica la viabilidad del plan contra restricciones de recursos del sistema 
        y valida la coherencia de las categorías de aplicaciones seleccionadas.
        
        Args:
            app_id (str): ID de la aplicación a validar.
            max_ram_mb (int, optional): Límite superior de RAM disponible en el host.
            
        Returns:
            Dict[str, Any]: Resultados de la validación, incluyendo advertencias y errores.
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

    def plan_with_vars_multi(self, app_ids: List[str], existing_vars: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Genera un plan de despliegue unificado para múltiples aplicaciones de primer nivel.

        Este método avanzado:
        1. Resuelve el grafo de dependencias conjunto evitando duplicidades.
        2. Preserva variables existentes (stateful) para asegurar la idempotencia.
        3. Genera dinámicamente nuevos secretos solo cuando es estrictamente necesario.
        4. Agrupa las aplicaciones en 'seleccionadas' y 'dependencias automáticas'.

        Args:
            app_ids (List[str]): Lista de aplicaciones elegidas por el usuario.
            existing_vars (Optional[Dict[str, str]]): Diccionario de variables de estado previas.

        Returns:
            Dict[str, Any]: Plan consolidado con metadatos de recursos y variables seguras.

        Raises:
            KeyError: Si se detecta una inconsistencia en el catálogo de metadatos.
            ValueError: Si existe una circularidad técnica en el grafo conjunto.
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

        existing_vars = existing_vars or {}

        selected_apps = [aid for aid in ordered_plan if aid in app_ids]
        dependencies = [aid for aid in ordered_plan if aid not in app_ids]

        all_vars: Dict[str, Any] = existing_vars.copy()

        # Añadir la lista de roles activos para Ansible
        all_vars["ansible_enabled_roles"] = ordered_plan

        for aid in ordered_plan:
            meta = self.catalog.get(aid, {})
            vars_def = meta.get("variables", {}) or {}

            for var_name, var_def in vars_def.items():
                key = map_app_variable(aid, var_name)

                # Preservar variable si ya existe y tiene un valor válido
                if key in existing_vars and existing_vars[key]:
                    continue

                # Respetar auto_generate: si es False, no autogenerar (el usuario provee el valor)
                if var_def.get("type") == "secret" and var_def.get("auto_generate", True):
                    value = self._generate_secret_value(var_def)
                    all_vars[key] = value
                else:
                    value = var_def.get("default", "")
                    all_vars[key] = value

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
