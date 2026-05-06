# 🧪 Tests para Syntalix-Orion

Este directorio contiene los tests unitarios para los módulos de Syntalix-Orion.

## 📁 Estructura de Tests

```
tests/
├── __init__.py           # Inicialización del paquete
├── conftest.py           # Configuración y fixtures de pytest
├── test_security.py     # Tests para módulo de seguridad
├── test_models.py        # Tests para modelos Pydantic
└── test_dependency_graph.py  # Tests para grafo de dependencias
```

## 🚀 Ejecutar Tests

### Requisitos

```bash
# Instalar dependencias de test
pip install pytest pytest-cov

# Desde el directorio scripts
cd scripts
pip install -e .
```

### Comandos

```bash
# Ejecutar todos los tests
pytest

# Ejecutar con cobertura
pytest --cov=core --cov-report=html

# Ejecutar tests específicos
pytest tests/test_security.py
pytest tests/test_models.py

# Ejecutar con más detalle
pytest -v

# Ejecutar solo tests de seguridad
pytest -m security
```

## 📋 Cobertura de Tests

| Módulo | Descripción | Estado |
|--------|-------------|--------|
| `core.security` | SSL, passwords, hashing | ✅ Implementado |
| `core.models` | Validación Pydantic | ✅ Implementado |
| `core.dependency_graph` | Grafo de dependencias | ✅ Implementado |
| `core.logging_config` | Logging estructurado | 📋 Pendiente |

## 🏗️ Fixtures Disponibles

| Fixture | Descripción |
|---------|-------------|
| `sample_metadata` | Catálogo de apps de ejemplo |
| `temp_dir` | Directorio temporal |
| `mock_env_file` | Archivo .env de prueba |
| `security_config` | Configuración de seguridad |
| `reset_logging` | Reset de logging entre tests |

## 📝 Escribir Nuevos Tests

```python
import pytest
from core.my_module import my_function

def test_my_function():
    """Test básico."""
    result = my_function("input")
    assert result == "expected"
    
def test_my_function_with_fixtures(sample_metadata):
    """Test con fixture."""
    assert "app_a" in sample_metadata
```

## 🎯 Mejores Prácticas

1. **Nombrado**: Usar `test_*.py` para archivos de test
2. **Docstrings**: Documentar cada test
3. **Fixtures**: Reutilizar datos con fixtures
4. **Aislamiento**: Cada test debe ser independiente
5. **Coverage**: Apuntar a >80% de cobertura

## 🔗 Integración Continua

Los tests pueden integrarse con CI/CD:

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    cd scripts
    pip install -r requirements.txt
    pytest --cov=core --junitxml=report.xml
```
