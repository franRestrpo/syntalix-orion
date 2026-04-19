"""
Tests para la Terminal User Interface (TUI).

Nota: Los tests de TUI son limitados porque Textual requiere un terminal real.
Estos tests verifican la lógica de negocio sin renderizar la UI.
"""

import pytest
import sys
from pathlib import Path

# Agregar directorios al path
SCRIPT_DIR = Path(__file__).parent.parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SCRIPT_DIR))


class TestDependencyGraphMulti:
    """Tests para el método plan_with_vars_multi."""

    @pytest.fixture
    def sample_catalog(self):
        """Catálogo de ejemplo para tests."""
        return {
            "traefik": {
                "id": "traefik",
                "name": "Traefik",
                "category": "Core",
                "version": "3.x",
                "ram_mb": 256,
                "dependencies": [],
                "variables": {
                    "TRAEFIK_PASSWORD": {
                        "type": "secret",
                        "auto_generate": True,
                        "length": 32
                    }
                }
            },
            "postgres": {
                "id": "postgres",
                "name": "PostgreSQL",
                "category": "Data",
                "version": "latest",
                "ram_mb": 512,
                "dependencies": [],
                "variables": {
                    "POSTGRES_PASSWORD": {
                        "type": "secret",
                        "auto_generate": True,
                        "length": 32
                    }
                }
            },
            "n8n": {
                "id": "n8n",
                "name": "n8n",
                "category": "Automation",
                "version": "latest",
                "ram_mb": 512,
                "dependencies": ["postgres", "traefik"],
                "variables": {}
            },
        }

    def test_plan_with_vars_multi_empty(self, sample_catalog):
        """Test con lista vacía."""
        from core.dependency_graph import DependencyGraph
        
        dg = DependencyGraph(catalog=sample_catalog)
        result = dg.plan_with_vars_multi([])
        
        assert result["plan"] == []
        assert result["ram_mb_total"] == 0
        assert result["selected_apps"] == []
        assert result["dependencies"] == []

    def test_plan_with_vars_multi_single_app(self, sample_catalog):
        """Test con una sola app."""
        from core.dependency_graph import DependencyGraph
        
        dg = DependencyGraph(catalog=sample_catalog)
        result = dg.plan_with_vars_multi(["traefik"])
        
        assert "traefik" in result["plan"]
        assert result["ram_mb_total"] == 256
        assert result["selected_apps"] == ["traefik"]
        assert result["dependencies"] == []

    def test_plan_with_vars_multi_with_dependencies(self, sample_catalog):
        """Test con app que tiene dependencias."""
        from core.dependency_graph import DependencyGraph
        
        dg = DependencyGraph(catalog=sample_catalog)
        result = dg.plan_with_vars_multi(["n8n"])
        
        # postgres y traefik deben estar en el plan como dependencias
        assert "traefik" in result["plan"]
        assert "postgres" in result["plan"]
        assert "n8n" in result["plan"]
        
        # Orden: dependencias primero
        traefik_idx = result["plan"].index("traefik")
        postgres_idx = result["plan"].index("postgres")
        n8n_idx = result["plan"].index("n8n")
        
        assert traefik_idx < n8n_idx
        assert postgres_idx < n8n_idx
        
        # RAM total
        assert result["ram_mb_total"] == 256 + 512 + 512  # traefik + postgres + n8n
        
        # Clasificacion
        assert result["selected_apps"] == ["n8n"]
        assert set(result["dependencies"]) == {"traefik", "postgres"}

    def test_plan_with_vars_multi_multiple_apps(self, sample_catalog):
        """Test con múltiples apps."""
        from core.dependency_graph import DependencyGraph
        
        dg = DependencyGraph(catalog=sample_catalog)
        result = dg.plan_with_vars_multi(["traefik", "postgres"])
        
        assert len(result["plan"]) == 2
        assert set(result["selected_apps"]) == {"traefik", "postgres"}
        assert result["dependencies"] == []

    def test_plan_with_vars_multi_generates_vars(self, sample_catalog):
        """Test que genera variables."""
        from core.dependency_graph import DependencyGraph
        
        dg = DependencyGraph(catalog=sample_catalog)
        result = dg.plan_with_vars_multi(["traefik"])
        
        # Debe generar la variable secret
        assert "TRAEFIK__TRAEFIK_PASSWORD" in result["vars"]
        assert len(result["vars"]["TRAEFIK__TRAEFIK_PASSWORD"]) > 20

    def test_plan_with_vars_multi_unknown_app_raises(self, sample_catalog):
        """Test que app desconocida lanza KeyError."""
        from core.dependency_graph import DependencyGraph
        
        dg = DependencyGraph(catalog=sample_catalog)
        
        with pytest.raises(KeyError) as exc_info:
            dg.plan_with_vars_multi(["unknown_app"])
        
        assert "unknown_app" in str(exc_info.value)


class TestCategoryOrder:
    """Tests para el ordenamiento de categorías."""

    def test_category_order_constant(self):
        """Test que CATEGORY_ORDER está definido correctamente."""
        from tui import CATEGORY_ORDER
        
        assert "Core" in CATEGORY_ORDER
        assert "Data" not in CATEGORY_ORDER  # Data se oculta
        assert "AI" in CATEGORY_ORDER
        assert CATEGORY_ORDER.index("Core") == 0


class TestRAMThreshold:
    """Tests para el umbral de RAM."""

    def test_ram_threshold_constant(self):
        """Test que el umbral está definido."""
        from tui import RAM_WARNING_THRESHOLD
        
        assert RAM_WARNING_THRESHOLD == 6000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
