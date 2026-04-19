import os
import importlib.util
from typing import Dict, List, Set, Optional, Any
import secrets
import bcrypt

# Attempt to load APP_METADATA from the root catalog
APP_METADATA: Dict[str, Dict[str, Any]] = {}
try:
    from apps_metadata import APP_METADATA as _AM  # type: ignore
    APP_METADATA = _AM  # type: ignore
except Exception:
    # Fallback: try to load from repository root via absolute path
    root_candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../apps_metadata.py")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../apps_metadata.py")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../apps_metadata.py")),
    ]
    for path in root_candidates:
        if os.path.exists(path):
            spec = importlib.util.spec_from_file_location("apps_metadata", path)  # type: ignore
            mod = importlib.util.module_from_spec(spec)  # type: ignore
            spec.loader.exec_module(mod)  # type: ignore
            APP_METADATA = getattr(mod, "APP_METADATA", {})  # type: ignore
            break


class DependencyGraph:
    """
    Dependency graph for deployment planning based on apps metadata.
    Reads APP_METADATA (app_id -> metadata) and resolves transitive dependencies.
    """

    def __init__(self, catalog: Optional[Dict[str, Dict[str, Any]]] = None) -> None:
        # catalog is a mapping from app_id -> metadata dict
        self.catalog: Dict[str, Dict[str, Any]] = catalog if catalog is not None else APP_METADATA

    def get_metadata(self, app_id: str) -> Optional[Dict[str, Any]]:
        return self.catalog.get(app_id)

    def resolve_dependencies(self, app_id: str) -> List[str]:
        """
        Resolve transitive dependencies for a given app_id and return
        an ordered list where dependencies come before dependents.
        Throws KeyError if app_id or any dependency is unknown, or ValueError for cycles.
        """
        if app_id not in self.catalog:
            raise KeyError(f"Unknown app_id '{app_id}' in metadata catalog.")

        visited: Set[str] = set()
        order: List[str] = []

        def dfs(node: str, visiting: Set[str]):
            if node in visited:
                return
            if node in visiting:
                cycle = " -> ".join(list(visiting) + [node])
                raise ValueError(f"Circular dependency detected: {cycle}")
            visiting.add(node)
            for dep in self.catalog.get(node, {}).get("dependencies", []):
                if dep not in self.catalog:
                    raise KeyError(f"Dependency '{dep}' for app '{node}' not found in catalog.")
                dfs(dep, visiting)
            visiting.remove(node)
            visited.add(node)
            order.append(node)

        dfs(app_id, set())
        return order

    # --------- New helpers for V2 features ---------
    def total_ram_for_plan(self, app_id: str) -> int:
        plan = self.resolve_dependencies(app_id)
        # Plan includes dependencies first, then the app_id itself
        unique_apps = set(plan)
        total = 0
        for aid in unique_apps:
            meta = self.catalog.get(aid, {})
            total += int(meta.get("ram_mb", 0))
        return total

    def _generate_secret_value(self, var_def: Dict[str, Any]) -> str:
        length = int(var_def.get("length", 32))
        value = secrets.token_urlsafe(length)
        # Optional bcrypt transform if requested
        if var_def.get("transform") == "bcrypt":
            hashed = bcrypt.hashpw(value.encode("utf-8"), bcrypt.gensalt())
            value = hashed.decode("utf-8")
        return value

    def generate_vars_for_plan(self, app_id: str) -> Dict[str, Any]:
        plan = self.resolve_dependencies(app_id)
        vars_out: Dict[str, Any] = {}
        for aid in plan:
            meta = self.catalog.get(aid, {})
            vars_def = meta.get("variables", {}) or {}
            for var_name, var_def in vars_def.items():
                key = f"{aid}__{var_name}".upper()
                if var_def.get("type") == "secret":
                    # Generate a secret if auto_generate is true or if there is no placeholder yet
                    value = self._generate_secret_value(var_def)
                    # If a bcrypt transform is requested, ensure the value is hashed (already done above)
                    vars_out[key] = value
                else:
                    # Non-secret variables: prefer provided default, else empty string
                    value = var_def.get("default", "")
                    vars_out[key] = value
        return vars_out

    def plan_with_vars(self, app_id: str) -> Dict[str, Any]:
        """Convenience: returns plan, RAM and generated vars for given app."""
        plan = self.resolve_dependencies(app_id)
        ram = self.total_ram_for_plan(app_id)
        generated_vars = self.generate_vars_for_plan(app_id)
        return {
            "plan": plan,
            "ram_mb_total": ram,
            "vars": generated_vars,
        }


if __name__ == "__main__":
    dg = DependencyGraph()
    app = "chatwoot"
    try:
        plan = dg.resolve_dependencies(app)
        print(f"Deployment plan for '{app}': {plan}")
    except Exception as e:
        print(f"Dependency resolution error: {e}")
