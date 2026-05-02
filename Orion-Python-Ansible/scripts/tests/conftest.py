"""
Configuración de Fixtures y Plugins para Pytest en Syntalix-Orion.

Este módulo define la infraestructura compartida necesaria para la ejecución 
de pruebas unitarias e integración. Proporciona metadatos de ejemplo, 
entornos temporales y mecanismos de limpieza automática.

Fixtures incluidas:
    - sample_metadata: Catálogo de aplicaciones de prueba con dependencias.
    - temp_dir: Directorio temporal para pruebas de archivos.
    - mock_env_file: Generador de archivos .env para validación de carga.
    - reset_logging: Limpieza automática del sistema de logs entre tests.
    - security_config: Instancia aislada de la configuración de seguridad.
"""

import sys
import os
from pathlib import Path

import pytest

# Agregar el directorio scripts al path
scripts_dir = Path(__file__).parent.parent
sys.path.insert(0, str(scripts_dir))

# Agregar el directorio raíz del proyecto
project_root = scripts_dir.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_metadata():
    """Fixture con metadatos de ejemplo."""
    return {
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
    }


@pytest.fixture
def temp_dir(tmp_path):
    """Fixture con directorio temporal."""
    return tmp_path


@pytest.fixture
def mock_env_file(temp_dir):
    """Fixture con archivo .env temporal."""
    env_file = temp_dir / "test.env"
    env_file.write_text("""
# Test environment file
TEST_VAR=value
SECRET_KEY=supersecret
DOMAIN=example.com
""")
    return env_file


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging antes de cada test."""
    import logging
    # Limpiar handlers de los loggers
    for logger_name in list(logging.Logger.manager.loggerDict.keys()):
        logger = logging.getLogger(logger_name)
        logger.handlers = []
        logger.setLevel(logging.WARNING)
    yield


@pytest.fixture
def security_config():
    """Fixture con configuración de seguridad."""
    from core.security import SecurityConfig
    config = SecurityConfig()
    config._initialized = False  # Reset para tests
    return config


# Configuración de pytest
def pytest_configure(config):
    """Configuración global de pytest."""
    config.addinivalue_line(
        "markers", "security: tests de seguridad"
    )
    config.addinivalue_line(
        "markers", "integration: tests de integración"
    )
    config.addinivalue_line(
        "markers", "slow: tests lentos"
    )


def pytest_collection_modifyitems(config, items):
    """Modificar items de test automáticamente."""
    for item in items:
        # Añadir marker de integración si el test requiere network
        if "network" in item.name or "http" in item.name.lower():
            item.add_marker(pytest.mark.integration)
        
        # Marker de seguridad para tests de security
        if "security" in str(item.fspath):
            item.add_marker(pytest.mark.security)
