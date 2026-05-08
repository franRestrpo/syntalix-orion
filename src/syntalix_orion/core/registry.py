"""
Registro de Aplicaciones (AppRegistry) - Syntalix-Orion.

Este módulo proporciona un cargador declarativo para el catálogo de aplicaciones.
Lee archivos YAML desde el directorio `catalog/` y los valida usando Pydantic,
permitiendo la gestión descentralizada del catálogo de aplicaciones.

Funcionalidades:
    - Carga dinámica de metadatos desde archivos YAML.
    - Validación estricta de esquemas con Pydantic V2.
    - Cacheo en memoria para evitar lecturas repetidas de disco.
    - Conversión bidireccional con el formato legacy (apps_metadata.py).
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Optional, List
from pydantic import ValidationError

from syntalix_orion.core.models import AppMetadata, AppVariable

CATALOG_DIR = Path(__file__).parent.parent / "catalog"


class RegistryLoadError(Exception):
    """Error al cargar el catálogo de aplicaciones."""
    pass


class AppRegistry:
    """
    Cargador y validador del catálogo de aplicaciones.

    Lee archivos `.yml` desde el directorio `catalog/` y los valida contra
    los modelos Pydantic, proporcionando un acceso tipado y cacheado al
    catálogo de aplicaciones.

    Uso:
        >>> registry = AppRegistry()
        >>> catalog = registry.load_all()
        >>> traefik = registry.get_app("traefik")
    """

    _instance: Optional['AppRegistry'] = None
    _catalog: Optional[Dict[str, AppMetadata]] = None

    def __new__(cls, catalog_dir: Optional[str] = None):
        """Implementación del patrón Singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, catalog_dir: Optional[str] = None):
        """
        Inicializa el registro.

        Args:
            catalog_dir: Ruta al directorio de catálogos. Usa 'catalog/' por defecto.
        """
        if self._initialized:
            return
        self._initialized = True
        self._catalog_dir = Path(catalog_dir) if catalog_dir else CATALOG_DIR
        self._catalog = None

    @property
    def catalog_dir(self) -> Path:
        """Directorio donde se buscan los archivos YAML."""
        return self._catalog_dir

    def load_all(self, force_reload: bool = False) -> Dict[str, AppMetadata]:
        """
        Carga y valida todos los archivos YAML del catálogo.

        Args:
            force_reload: Si True, ignora el cache y recarga desde disco.

        Returns:
            Dict[str, AppMetadata]: Diccionario de apps validadas.

        Raises:
            RegistryLoadError: Si hay errores de validación en los archivos.
        """
        if self._catalog is not None and not force_reload:
            return self._catalog

        apps: Dict[str, AppMetadata] = {}
        errors: List[str] = []

        if not self._catalog_dir.exists():
            raise RegistryLoadError(
                f"Directorio de catálogo no encontrado: {self._catalog_dir}"
            )

        for yaml_file in self._catalog_dir.glob("*.yml"):
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data is None:
                        continue

                    app_id = data.get("id", yaml_file.stem)
                    data["id"] = app_id
                    app = AppMetadata(**data)
                    apps[app.id] = app

            except ValidationError as e:
                errors.append(f"{yaml_file.name}: {e}")
            except Exception as e:
                errors.append(f"{yaml_file.name}: {e}")

        if errors:
            raise RegistryLoadError(
                f"Errores de validación en el catálogo:\n" + "\n".join(errors)
            )

        self._catalog = apps
        return apps

    def get_app(self, app_id: str) -> Optional[AppMetadata]:
        """
        Obtiene una aplicación por su ID.

        Args:
            app_id: Identificador de la aplicación.

        Returns:
            AppMetadata o None si no existe.
        """
        catalog = self.load_all()
        return catalog.get(app_id)

    def reload(self) -> Dict[str, AppMetadata]:
        """Fuerza la recarga del catálogo desde disco."""
        self._catalog = None
        return self.load_all(force_reload=True)

    def exists(self, app_id: str) -> bool:
        """Verifica si una aplicación existe en el catálogo."""
        return app_id in self.load_all()

    def export_to_legacy(self) -> Dict[str, Dict]:
        """
        Exporta el catálogo cargado al formato legacy (dict de dicts).

        Útil para mantener backwards compatibility con código que espera
        el formato de apps_metadata.py.

        Returns:
            Dict[str, Dict]: Catálogo en formato legacy.
        """
        catalog = self.load_all()
        result = {}
        for app_id, app in catalog.items():
            app_dict = app.model_dump()
            app_dict["variables"] = {
                k: v.model_dump() if hasattr(v, 'model_dump') else v
                for k, v in app.variables.items()
            }
            result[app_id] = app_dict
        return result


def get_registry() -> AppRegistry:
    """Obtiene la instancia singleton del registro."""
    return AppRegistry()


def load_catalog_legacy() -> Dict[str, AppMetadata]:
    """
    Función de compatibilidad para cargar desde apps_metadata.py.

    Returns:
        Dict[str, AppMetadata]: Catálogo validado desde apps_metadata.
    """
    from syntalix_orion.apps_metadata import APP_METADATA
    from syntalix_orion.core.models import load_app_catalog
    return load_app_catalog(APP_METADATA)