"""
Pruebas Unitarias para el Grafo de Dependencias.

Este módulo implementa casos de prueba estructurados utilizando pytest para 
verificar la correcta resolución del árbol de dependencias de las aplicaciones.

Funcionalidades auditadas:
    - Inicialización de grafos con catálogos en memoria y locales.
    - Resolución DFS (Depth-First Search) y detección de referencias circulares.
    - Autogeneración de variables seguras para el plan consolidado.
    - Cálculo preciso del límite de memoria RAM.
"""

import pytest
from pathlib import Path

from core.dependency_graph import DependencyGraph


# Datos de prueba
SAMPLE_METADATA = {
    "app_a": {
        "id": "app_a",
        "name": "App A",
        "category": "Core",
        "version": "1.0",
        "ram_mb": 256,
        "dependencies": [],
    },
    "app_b": {
        "id": "app_b",
        "name": "App B",
        "category": "Core",
        "version": "1.0",
        "ram_mb": 512,
        "dependencies": ["app_a"],
    },
    "app_c": {
        "id": "app_c",
        "name": "App C",
        "category": "Data",
        "version": "1.0",
        "ram_mb": 1024,
        "dependencies": ["app_a", "app_b"],
    },
    "app_d": {
        "id": "app_d",
        "name": "App D",
        "category": "AI",
        "version": "1.0",
        "ram_mb": 2048,
        "dependencies": ["postgres", "redis"],
    },
    "postgres": {
        "id": "postgres",
        "name": "PostgreSQL",
        "category": "Data",
        "version": "latest",
        "ram_mb": 512,
        "dependencies": [],
    },
    "redis": {
        "id": "redis",
        "name": "Redis",
        "category": "Data",
        "version": "6",
        "ram_mb": 256,
        "dependencies": [],
    },
}


class TestDependencyGraph:
    """Tests para la clase DependencyGraph."""
    
    def test_initialization(self):
        """Test inicialización básica."""
        dg = DependencyGraph(catalog=SAMPLE_METADATA)
        assert dg.catalog == SAMPLE_METADATA
    
    def test_initialization_default_catalog(self):
        """Test inicialización con catálogo por defecto."""
        dg = DependencyGraph()
        assert dg.catalog is not None
    
    def test_get_metadata_existing(self):
        """Test obtener metadatos de app existente."""
        dg = DependencyGraph(catalog=SAMPLE_METADATA)
        meta = dg.get_metadata("app_a")
        assert meta is not None
        assert meta["name"] == "App A"
    
    def test_get_metadata_nonexisting(self):
        """Test obtener metadatos de app inexistente."""
        dg = DependencyGraph(catalog=SAMPLE_METADATA)
        meta = dg.get_metadata("nonexistent_app")
        assert meta is None
    
    def test_no_dependencies(self):
        """Test app sin dependencias."""
        dg = DependencyGraph(catalog=SAMPLE_METADATA)
        plan = dg.resolve_dependencies("app_a")
        assert plan == ["app_a"]
    
    def test_single_dependency(self):
        """Test app con una dependencia."""
        dg = DependencyGraph(catalog=SAMPLE_METADATA)
        plan = dg.resolve_dependencies("app_b")
        assert plan == ["app_a", "app_b"]  # Dependencia primero
    
    def test_multiple_dependencies(self):
        """Test app con múltiples dependencias."""
        dg = DependencyGraph(catalog=SAMPLE_METADATA)
        plan = dg.resolve_dependencies("app_c")
        assert plan == ["app_a", "app_b", "app_c"]
        # Verificar orden: dependencias antes de dependents
        assert plan.index("app_a") < plan.index("app_b")
        assert plan.index("app_b") < plan.index("app_c")
    
    def test_complex_dependencies(self):
        """Test con grafo de dependencias complejo."""
        dg = DependencyGraph(catalog=SAMPLE_METADATA)
        plan = dg.resolve_dependencies("app_d")
        
        # postgres y redis deben estar primero
        assert "postgres" in plan
        assert "redis" in plan
        assert "app_d" == plan[-1]  # La app misma al final
        
        # Verificar que postgres y redis están antes que app_d
        assert plan.index("postgres") < plan.index("app_d")
        assert plan.index("redis") < plan.index("app_d")
    
    def test_unknown_app_raises_keyerror(self):
        """Test que app desconocida lanza KeyError."""
        dg = DependencyGraph(catalog=SAMPLE_METADATA)
        with pytest.raises(KeyError) as exc_info:
            dg.resolve_dependencies("unknown_app")
        assert "unknown_app" in str(exc_info.value)
    
    def test_unknown_dependency_raises_keyerror(self):
        """Test que dependencia desconocida lanza KeyError."""
        bad_metadata = {
            "app_bad": {
                "id": "app_bad",
                "name": "App Bad",
                "category": "Test",
                "version": "1.0",
                "ram_mb": 100,
                "dependencies": ["nonexistent_dep"],
            }
        }
        dg = DependencyGraph(catalog=bad_metadata)
        with pytest.raises(KeyError) as exc_info:
            dg.resolve_dependencies("app_bad")
        assert "nonexistent_dep" in str(exc_info.value)
    
    def test_circular_dependency_raises_valueerror(self):
        """Test que dependencia circular lanza ValueError."""
        circular_metadata = {
            "app1": {
                "id": "app1",
                "name": "App 1",
                "category": "Test",
                "version": "1.0",
                "ram_mb": 100,
                "dependencies": ["app2"],
            },
            "app2": {
                "id": "app2",
                "name": "App 2",
                "category": "Test",
                "version": "1.0",
                "ram_mb": 100,
                "dependencies": ["app1"],
            },
        }
        dg = DependencyGraph(catalog=circular_metadata)
        with pytest.raises(ValueError) as exc_info:
            dg.resolve_dependencies("app1")
        assert "circular" in str(exc_info.value).lower()
    
    def test_self_reference_dependency(self):
        """Test dependencia de sí mismo."""
        self_ref_metadata = {
            "app_self": {
                "id": "app_self",
                "name": "App Self",
                "category": "Test",
                "version": "1.0",
                "ram_mb": 100,
                "dependencies": ["app_self"],
            }
        }
        dg = DependencyGraph(catalog=self_ref_metadata)
        with pytest.raises(ValueError):
            dg.resolve_dependencies("app_self")


class TestTotalRamForPlan:
    """Tests para cálculo de RAM total."""
    
    def test_single_app_ram(self):
        """Test RAM de app sin dependencias."""
        dg = DependencyGraph(catalog=SAMPLE_METADATA)
        total = dg.total_ram_for_plan("app_a")
        assert total == 256
    
    def test_app_with_dependencies_ram(self):
        """Test RAM de app con dependencias."""
        dg = DependencyGraph(catalog=SAMPLE_METADATA)
        total = dg.total_ram_for_plan("app_b")
        # app_a (256) + app_b (512) = 768
        assert total == 256 + 512
    
    def test_complex_plan_ram(self):
        """Test RAM de plan complejo."""
        dg = DependencyGraph(catalog=SAMPLE_METADATA)
        total = dg.total_ram_for_plan("app_d")
        # postgres (512) + redis (256) + app_d (2048) = 2816
        assert total == 512 + 256 + 2048
    
    def test_missing_ram_mb_handled(self):
        """Test que apps sin ram_mb no rompen el cálculo."""
        metadata_no_ram = {
            "app1": {
                "id": "app1",
                "name": "App 1",
                "category": "Test",
                "version": "1.0",
                "ram_mb": 100,
                "dependencies": [],
            },
            "app2": {
                "id": "app2",
                "name": "App 2", 
                "category": "Test",
                "version": "1.0",
                # Sin ram_mb definido
                "dependencies": ["app1"],
            },
        }
        dg = DependencyGraph(catalog=metadata_no_ram)
        total = dg.total_ram_for_plan("app2")
        # Solo cuenta app1 (100), app2 sin ram_mb suma 0
        assert total == 100


class TestGenerateVarsForPlan:
    """Tests para generación de variables."""
    
    def test_generates_all_vars(self):
        """Test que genera todas las variables."""
        metadata_with_vars = {
            "app1": {
                "id": "app1",
                "name": "App 1",
                "category": "Test",
                "version": "1.0",
                "ram_mb": 100,
                "dependencies": [],
                "variables": {
                    "DB_PASSWORD": {
                        "type": "secret",
                        "auto_generate": True,
                    },
                    "DB_HOST": {
                        "type": "string",
                        "default": "localhost",
                    },
                },
            },
        }
        dg = DependencyGraph(catalog=metadata_with_vars)
        vars = dg.generate_vars_for_plan("app1")
        
        assert "APP1__DB_PASSWORD" in vars
        assert "APP1__DB_HOST" in vars
        assert vars["APP1__DB_HOST"] == "localhost"
    
    def test_secret_auto_generated(self):
        """Test que secrets son auto-generados."""
        metadata_with_secret = {
            "app1": {
                "id": "app1",
                "name": "App 1",
                "category": "Test",
                "version": "1.0",
                "ram_mb": 100,
                "dependencies": [],
                "variables": {
                    "SECRET_KEY": {
                        "type": "secret",
                        "auto_generate": True,
                    },
                },
            },
        }
        dg = DependencyGraph(catalog=metadata_with_secret)
        vars = dg.generate_vars_for_plan("app1")
        
        secret = vars.get("APP1__SECRET_KEY")
        assert secret is not None
        assert len(secret) > 20  # Tokens seguros son largos
    
    def test_secret_with_bcrypt_transform(self):
        """Test que secrets con bcrypt son transformados."""
        metadata_with_bcrypt = {
            "app1": {
                "id": "app1",
                "name": "App 1",
                "category": "Test",
                "version": "1.0",
                "ram_mb": 100,
                "dependencies": [],
                "variables": {
                    "HASHED_PASS": {
                        "type": "secret",
                        "auto_generate": True,
                        "transform": "bcrypt",
                    },
                },
            },
        }
        dg = DependencyGraph(catalog=metadata_with_bcrypt)
        vars = dg.generate_vars_for_plan("app1")
        
        hashed = vars.get("APP1__HASHED_PASS")
        assert hashed is not None
        assert hashed.startswith("$2")  # Prefijo bcrypt


class TestPlanWithVars:
    """Tests para plan_with_vars."""
    
    def test_returns_all_fields(self):
        """Test que retorna todos los campos."""
        dg = DependencyGraph(catalog=SAMPLE_METADATA)
        result = dg.plan_with_vars("app_a")
        
        assert "plan" in result
        assert "ram_mb_total" in result
        assert "vars" in result
        assert result["plan"] == ["app_a"]
        assert result["ram_mb_total"] == 256
        assert isinstance(result["vars"], dict)
    
    def test_plan_validity(self):
        """Test que el plan incluye todas las dependencias."""
        dg = DependencyGraph(catalog=SAMPLE_METADATA)
        result = dg.plan_with_vars("app_c")
        
        plan = result["plan"]
        # Verificar que todas las dependencias están en el plan
        assert "app_a" in plan
        assert "app_b" in plan
        assert "app_c" in plan


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
