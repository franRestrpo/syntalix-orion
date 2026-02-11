import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

class ServiceRegistry:
    def __init__(self, registry_path: str):
        self.registry_path = Path(registry_path)
        self.services: Dict[str, Any] = {}
        self.categories: Dict[str, List[str]] = {}

    def scan_registry(self) -> None:
        """
        Escanea el directorio de registro en busca de servicios válidos.
        Un servicio es válido si tiene un archivo manifest.json.
        """
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Registry path not found: {self.registry_path}")

        for service_dir in self.registry_path.iterdir():
            if service_dir.is_dir():
                manifest_path = service_dir / "manifest.json"
                if manifest_path.exists():
                    self._load_service(service_dir.name, manifest_path)

    def _load_service(self, service_id: str, manifest_path: Path) -> None:
        """
        Carga la definición de un servicio desde su manifiesto.
        """
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
                
            # Validar campos requeridos mínimos
            required_fields = ['name', 'category', 'version']
            if not all(field in manifest for field in required_fields):
                print(f"Warning: Service {service_id} missing required fields in manifest. Skipping.")
                return

            # Añadir ID del servicio al manifiesto para referencia interna
            manifest['id'] = service_id
            manifest['path'] = str(manifest_path.parent)
            
            self.services[service_id] = manifest
            
            # Organizar por categoría
            category = manifest.get('category', 'Uncategorized')
            if category not in self.categories:
                self.categories[category] = []
            self.categories[category].append(service_id)
            
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in manifest for service {service_id}")
        except Exception as e:
            print(f"Error loading service {service_id}: {str(e)}")

    def get_service(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Devuelve el manifiesto de un servicio específico."""
        return self.services.get(service_id)

    def get_all_services(self) -> List[Dict[str, Any]]:
        """Devuelve una lista de todos los servicios cargados."""
        return list(self.services.values())

    def get_services_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Devuelve todos los servicios de una categoría específica."""
        service_ids = self.categories.get(category, [])
        return [self.services[sid] for sid in service_ids]

    def get_categories(self) -> List[str]:
        """Devuelve una lista de todas las categorías disponibles."""
        return sorted(list(self.categories.keys()))