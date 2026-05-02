"""
Tests Package - Syntalix-Orion v2.0.1

================================================================================
ESTADO ACTUAL: SUITE DE PRUEBAS COMPLETA (PYTEST)
================================================================================

Este paquete contiene las pruebas automatizadas para todos los módulos
de Syntalix-Orion, usando el framework pytest.

CONFIGURACIÓN:
--------------
- Framework: pytest
- Fixtures: conftest.py (contiene sample_metadata, etc.)
- Cobertura: Módulos core + TUI

PRUEBAS DISPONIBLES:
--------------------

1. test_dependency_graph.py
   - Testea DependencyGraph y resolución de dependencias
   - Verifica detección de ciclos
   - Valida cálculo de RAM
   - Comprueba generación de variables
   - Estado: ✅ Operativo

2. test_models.py
   - Testea modelos Pydantic (AppMetadata, AppVariable, DeploymentPlan)
   - Valida esquemas y tipos
   - Verifica validators personalizados
   - Estado: ✅ Operativo

3. test_security.py
   - Testea generación de contraseñas seguras
   - Valida hashing bcrypt (solo UI)
   - Comprueba validación de dominios/emails
   - Verifica sanitización de inputs
   - Estado: ✅ Operativo - ACTUALIZADO para nueva política de bcrypt

4. test_tui.py
   - Testea interfaz Textual (OrionTUI)
   - Valida selección de apps
   - Comprueba actualización de plan
   - Mock de Ansible runner
   - Estado: ✅ Operativo

5. conftest.py
   - Fixtures compartidas para todos los tests
   - sample_metadata: Catálogo de ejemplo para pruebas
   - Estado: ✅ Operativo

EJECUCIÓN DE PRUEBAS:
----------------------
# Todas las pruebas
cd Orion-Python-Ansible/scripts
pytest

# Prueba específica
pytest tests/test_security.py -v

# Con cobertura
pytest --cov=core tests/

# Pruebas legacy (unittest)
python -m unittest discover -v

NOTAS DE ACTUALIZACIÓN (2026-05-01):
-----------------------------------
✅ test_security.py debe actualizarse para verificar:
   - Bases de datos NO usan bcrypt (texto plano)
   - Apps UI SI usan bcrypt (Traefik, n8n, Odoo)
   - generate_secure_password() usa secrets.token_urlsafe()

PENDIENTES:
-----------
⚠️ Añadir pruebas para state.py (nuevo formato .env)
⚠️ Añadir pruebas para logging_config.py (manejo de errores)
⚠️ Añadir pruebas de integración (flujo completo)
"""

__version__ = "2.0.1"
__test_framework__ = "pytest"

__all__ = []
