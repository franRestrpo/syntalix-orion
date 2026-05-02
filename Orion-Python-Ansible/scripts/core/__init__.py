"""
Core Package - Syntalix-Orion v2.0.1

================================================================================
ESTADO ACTUAL: FASE 2 COMPLETADA - TRANSICIÓN A FASE 3
================================================================================

Este paquete contiene los módulos centrales de la plataforma Syntalix-Orion,
implementando la arquitectura V2 de 3 capas (Metadata, TUI, Orchestration).

ÚLTIMAS ACTUALIZACIONES (2026-05-01):
----------------------------------------
✅ CORRECCIÓN CRÍTICA: Eliminado 'transform: bcrypt' de 5 bases de datos en apps_metadata.py
   - mariadb, mongodb, redis, qdrant, minio ahora usan texto plano seguro
   - Se mantuvo bcrypt solo para UI logins (Traefik, n8n, Odoo)
✅ Mejora: Validación automática del catálogo al importar apps_metadata.py
✅ Refactor: state.py ahora usa formato .env estándar (eliminado ConfigParser)
✅ Corrección: Debug prints en tui.py reemplazados por logger
✅ Codificación: Añadido UTF-8 en templating.py

MÓDULOS DISPONIBLES:
-------------------

1. SECURITY (security.py)
   - Generación de contraseñas: generate_secure_password(), generate_app_password()
   - Hashing bcrypt: hash_password_bcrypt(), verify_password_bcrypt()
   - Validación: validate_domain(), validate_email(), sanitize_input()
   - Enmascaramiento: mask_secret() para logs seguros
   - SSL: SecurityConfig, SSLContext para configuración SSL/TLS
   - Estado: ✅ Operativo - CRÍTICO: bcrypt solo para UI

2. MODELS (models.py)
   - AppMetadata: Validación Pydantic de metadatos de aplicaciones
   - AppVariable: Definición de variables de entorno
   - DeploymentPlan: Plan de despliegue generado
   - Validadores: IDs, categorías, tipos, RAM
   - Estado: ✅ Operativo - Validación automática implementada

3. DEPENDENCY GRAPH (dependency_graph.py)
   - Resolución de dependencias transitivas
   - Detección de ciclos (DFS algorithm)
   - Cálculo de RAM total
   - Generación de variables seguras
   - Métodos: resolve_dependencies(), plan_with_vars_multi()
   - Estado: ✅ Operativo

4. LOGGING CONFIG (logging_config.py)
   - Logging dual (archivo + consola)
   - Formatos: JSONFormatter, StructuredFormatter (con colores)
   - Rotación de logs: 10MB, 5 backups
   - LogContext: Context manager para extra data
   - Estado: ✅ Operativo - Mejorado manejo de errores

5. STATE MANAGEMENT (state.py)
   - Persistencia JSON: save_state(), load_state()
   - Archivos .env: save_env_file(), load_env_file()
   - Formato estándar KEY=VALUE (sin secciones)
   - Permisos restrictivos (600) en archivos .env
   - Estado: ✅ Operativo - REFACTORIZADO (sin ConfigParser)

6. PREFLIGHT CHECKS (preflight.py)
   - Verificación de Docker y Swarm
   - Validación de recursos (RAM, CPU, disco)
   - Creación de redes overlay
   - Multiplataforma: Linux/Windows/macOS
   - Estado: ✅ Operativo

7. TEMPLATING (templating.py)
   - Renderizado Jinja2: render_template()
   - Generación de etiquetas Traefik: inject_traefik_labels()
   - Estado: ✅ Operativo - UTF-8 añadido

8. REGISTRY (registry.py)
   - Registro de servicios via manifest.json
   - Estado: ⚠️ Implementación básica

FLUJO DE DATOS TÍPICO:
----------------------
1. apps_metadata.py → Carga catálogo (validado por models.py)
2. TUI (tui.py) → Usuario selecciona apps
3. DependencyGraph → Resuelve dependencias, calcula RAM, genera vars
4. generate_vars.yml → Escribe variables seguras
5. site.yml (Ansible) → Lee ansible_vars.yml, despliega roles

VARIABLES DE ENTORNO RELEVANTES:
--------------------------------
- RUNNER_MODE=mock|real (para testing de TUI)
- LOG_LEVEL=DEBUG|INFO|WARNING|ERROR

COMPATIBILIDAD:
--------------
- Python: 3.10+ (recomendado 3.13)
- Dependencias: textual, pyyaml, pydantic, bcrypt, jinja2, ansible-runner (opcional)
- Sistema: Linux (producción), Windows/macOS (desarrollo)

TESTING:
---------
- pytest tests/ - Pruebas unitarias
- python -m unittest discover -v - Pruebas legacy
- Fixtures en tests/conftest.py (ej. sample_metadata)
"""

from core.security import (
    SecurityConfig,
    generate_secure_password,
    generate_app_password,
    generate_secret,
    hash_password_bcrypt,
    verify_password_bcrypt,
    generate_api_key,
    validate_domain,
    validate_email,
    sanitize_input,
    mask_secret,
    get_security_config,
    SSLContext,
)

from core.models import (
    AppVariable,
    AppMetadata,
    DeploymentPlan,
    validate_app_metadata,
    load_app_catalog,
    AppCategory,
    VariableType,
    TransformType,
)

from core.logging_config import (
    OrionLogger,
    get_logger,
    setup_logging,
    get_log_dir,
    LogContext,
    JSONFormatter,
    StructuredFormatter,
)

from core.dependency_graph import (
    DependencyGraph,
    APP_METADATA,
)

from core.state import (
    save_state,
    load_state,
    load_env_file,
    save_env_file,
)

from core.preflight import (
    cmd_exists,
    require,
    check_docker_available,
    check_swarm_active,
    check_network_exists,
    create_overlay_network,
    validate_resources,
    run_preflight_checks,
    get_platform,
    is_linux,
    is_windows,
    is_macos,
    get_system_ram_gb,
    get_cpu_cores,
    get_disk_free_gb,
)

__version__ = "2.0.1"
__status__ = "Phase 2 Complete - Transitioning to Phase 3"

__all__ = [
    # Security
    "SecurityConfig",
    "generate_secure_password",
    "generate_app_password",
    "generate_secret",
    "hash_password_bcrypt",
    "verify_password_bcrypt",
    "generate_api_key",
    "validate_domain",
    "validate_email",
    "sanitize_input",
    "mask_secret",
    "get_security_config",
    "SSLContext",
    # Models
    "AppVariable",
    "AppMetadata",
    "DeploymentPlan",
    "validate_app_metadata",
    "load_app_catalog",
    "AppCategory",
    "VariableType",
    "TransformType",
    # Logging
    "OrionLogger",
    "get_logger",
    "setup_logging",
    "get_log_dir",
    "LogContext",
    "JSONFormatter",
    "StructuredFormatter",
    # Dependency Graph
    "DependencyGraph",
    "APP_METADATA",
    # State
    "save_state",
    "load_state",
    "load_env_file",
    "save_env_file",
    # Preflight
    "cmd_exists",
    "require",
    "check_docker_available",
    "check_swarm_active",
    "check_network_exists",
    "create_overlay_network",
    "validate_resources",
    "run_preflight_checks",
    "get_platform",
    "is_linux",
    "is_windows",
    "is_macos",
    "get_system_ram_gb",
    "get_cpu_cores",
    "get_disk_free_gb",
]
