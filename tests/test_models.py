"""
Pruebas Unitarias de Modelos de Validación (Pydantic).

Este módulo verifica que los esquemas de datos del proyecto operen estrictamente 
bajo las reglas de negocio establecidas, asegurando que cualquier desviación 
en la 'Fuente de Verdad' falle temprano antes del despliegue.

Validaciones auditadas:
    - Conformidad estricta de 'AppMetadata' y 'AppVariable'.
    - Restricciones semánticas: Nombres sin espacios, rangos de RAM lógicos, etc.
    - Tipos de variables y transformaciones criptográficas (bcrypt/base64).
    - Plan de despliegue y detección de dependencias.
"""

import pytest
from pathlib import Path
from pydantic import ValidationError

from syntalix_orion.core.models import (
    AppVariable,
    AppMetadata,
    DeploymentPlan,
    validate_app_metadata,
    load_app_catalog,
)


class TestAppVariable:
    """Tests para el modelo AppVariable."""
    
    def test_valid_string_variable(self):
        """Test variable de tipo string válida."""
        var = AppVariable(
            type="string",
            description="Test variable",
            required=False,
            default="test_value"
        )
        assert var.type == "string"
        assert var.default == "test_value"
    
    def test_valid_secret_variable(self):
        """Test variable de tipo secret."""
        var = AppVariable(
            type="secret",
            description="Password field",
            auto_generate=True,
            length=32
        )
        assert var.type == "secret"
        assert var.auto_generate is True
        assert var.length == 32
    
    def test_invalid_type_raises_error(self):
        """Test que tipo inválido lanza error."""
        with pytest.raises(ValidationError) as exc_info:
            AppVariable(type="invalid_type")
        assert "tipo inválido" in str(exc_info.value).lower()
    
    def test_invalid_transform_raises_error(self):
        """Test que transform inválido lanza error."""
        with pytest.raises(ValidationError) as exc_info:
            AppVariable(type="string", transform="invalid")
        assert "transform" in str(exc_info.value).lower()
    
    def test_length_validation(self):
        """Test validación de longitud."""
        # Longitud válida
        var = AppVariable(type="string", length=64)
        assert var.length == 64
        
        # Longitud inválida (muy larga)
        with pytest.raises(ValidationError):
            AppVariable(type="string", length=200)
    
    def test_description_too_long(self):
        """Test que descripción muy larga lanza error."""
        with pytest.raises(ValidationError):
            AppVariable(type="string", description="x" * 300)


class TestAppMetadata:
    """Tests para el modelo AppMetadata."""
    
    def test_valid_metadata(self):
        """Test metadatos válidos."""
        meta = AppMetadata(
            id="test_app",
            name="Test App",
            category="Core",
            version="1.0.0",
            ram_mb=512,
            dependencies=["postgres"]
        )
        assert meta.id == "test_app"
        assert meta.ram_mb == 512
        assert "postgres" in meta.dependencies
    
    def test_invalid_id_format(self):
        """Test que ID inválido lanza error."""
        with pytest.raises(ValidationError) as exc_info:
            AppMetadata(
                id="Invalid-ID",  # Mayúsculas no permitidas
                name="Test",
                category="Core",
                version="1.0",
                ram_mb=256
            )
        assert "id" in str(exc_info.value).lower()
    
    def test_id_must_start_lowercase(self):
        """Test que ID debe empezar con minúscula."""
        with pytest.raises(ValidationError):
            AppMetadata(
                id="TestApp",
                name="Test",
                category="Core",
                version="1.0",
                ram_mb=256
            )
    
    def test_invalid_category(self):
        """Test que categoría inválida lanza error."""
        with pytest.raises(ValidationError) as exc_info:
            AppMetadata(
                id="test_app",
                name="Test",
                category="InvalidCategory",
                version="1.0",
                ram_mb=256
            )
        assert "categoría" in str(exc_info.value).lower()
    
    def test_negative_ram_raises_error(self):
        """Test que RAM negativa lanza error."""
        with pytest.raises(ValidationError):
            AppMetadata(
                id="test_app",
                name="Test",
                category="Core",
                version="1.0",
                ram_mb=-100
            )
    
    def test_name_too_short(self):
        """Test que nombre muy corto lanza error."""
        with pytest.raises(ValidationError):
            AppMetadata(
                id="test_app",
                name="A",
                category="Core",
                version="1.0",
                ram_mb=256
            )
    
    def test_dependencies_validation(self):
        """Test validación de dependencias."""
        with pytest.raises(ValidationError) as exc_info:
            AppMetadata(
                id="test_app",
                name="Test",
                category="Core",
                version="1.0",
                ram_mb=256,
                dependencies=["Invalid-Dep"]  # Formato inválido
            )
        assert "dependencia" in str(exc_info.value).lower()
    
    def test_with_variables(self):
        """Test metadatos con variables."""
        meta = AppMetadata(
            id="test_app",
            name="Test App",
            category="Core",
            version="1.0",
            ram_mb=256,
            variables={
                "DB_PASSWORD": AppVariable(
                    type="secret",
                    auto_generate=True
                )
            }
        )
        assert "DB_PASSWORD" in meta.variables
        assert meta.variables["DB_PASSWORD"].type == "secret"


class TestValidateAppMetadata:
    """Tests para la función validate_app_metadata."""
    
    def test_valid_dict_passes(self):
        """Test que dict válido pasa validación."""
        data = {
            "id": "test_app",
            "name": "Test App",
            "category": "Core",
            "version": "1.0",
            "ram_mb": 256,
        }
        result = validate_app_metadata(data)
        assert isinstance(result, AppMetadata)
        assert result.id == "test_app"
    
    def test_invalid_dict_raises(self):
        """Test que dict inválido lanza error."""
        data = {
            "id": "Invalid-ID",  # Inválido
            "name": "Test",
            "category": "Core",
            "version": "1.0",
            "ram_mb": 256,
        }
        with pytest.raises(ValidationError):
            validate_app_metadata(data)


class TestLoadAppCatalog:
    """Tests para la función load_app_catalog."""
    
    def test_valid_catalog(self):
        """Test carga de catálogo válido."""
        catalog = {
            "app1": {
                "id": "app1",
                "name": "App 1",
                "category": "Core",
                "version": "1.0",
                "ram_mb": 256,
            },
            "app2": {
                "id": "app2",
                "name": "App 2",
                "category": "Data",
                "version": "2.0",
                "ram_mb": 512,
            }
        }
        result = load_app_catalog(catalog)
        assert len(result) == 2
        assert "app1" in result
        assert "app2" in result
    
    def test_invalid_app_in_catalog(self):
        """Test que app inválida en catálogo lanza error."""
        catalog = {
            "app1": {
                "id": "app1",
                "name": "App 1",
                "category": "Core",
                "version": "1.0",
                "ram_mb": 256,
            },
            "bad_app": {
                "id": "bad_app",
                "name": "Bad App",
                "category": "InvalidCategory",  # Inválido
                "version": "1.0",
                "ram_mb": 256,
            }
        }
        with pytest.raises(ValueError) as exc_info:
            load_app_catalog(catalog)
        assert "bad_app" in str(exc_info.value)


class TestDeploymentPlan:
    """Tests para el modelo DeploymentPlan."""
    
    def test_valid_plan(self):
        """Test plan válido."""
        plan = DeploymentPlan(
            app_id="test_app",
            plan=["postgres", "redis", "test_app"],
            ram_mb_total=1024,
            vars={"KEY": "value"}
        )
        assert plan.app_id == "test_app"
        assert plan.is_valid is True
        assert plan.dependencies_count == 2
    
    def test_plan_with_warnings(self):
        """Test plan con advertencias."""
        plan = DeploymentPlan(
            app_id="test_app",
            plan=["postgres", "test_app"],
            ram_mb_total=2048,
            vars={},
            warnings=["RAM exceeds recommended limit"]
        )
        assert plan.is_valid is True
        assert len(plan.warnings) == 1
    
    def test_plan_with_errors(self):
        """Test plan con errores."""
        plan = DeploymentPlan(
            app_id="test_app",
            plan=[],
            ram_mb_total=0,
            errors=["Circular dependency detected"]
        )
        assert plan.is_valid is False
        assert len(plan.errors) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
