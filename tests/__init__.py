"""
Suite de Pruebas Automatizadas (Tests) de Syntalix-Orion V2.

Este paquete centraliza todas las pruebas unitarias y de integración del 
proyecto, utilizando el framework 'pytest'. Garantiza la fiabilidad de los 
componentes críticos y previene regresiones durante la fase de orquestación.

Estructura de la Suite:
    - test_dependency_graph: Validación de la lógica de resolución de grafos.
    - test_models: Pruebas de integridad de esquemas Pydantic.
    - test_security: Auditoría de funciones criptográficas y sanitización.
    - test_tui: Pruebas funcionales de la interfaz de terminal (Textual).
    - conftest: Fixtures globales y catálogo de metadatos de prueba.

Instrucciones de Ejecución:
    - Ejecución total: `pytest` desde el directorio 'scripts'.
    - Cobertura: `pytest --cov=core tests/` para métricas de calidad.

Estado: ✅ Operativo y actualizado según las políticas DevSecOps V2.
"""

__version__ = "2.0.1"
__test_framework__ = "pytest"

__all__ = []
