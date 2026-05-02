"""
Paquete Central (Core) de Syntalix-Orion V2.

Este paquete constituye el núcleo lógico de la plataforma, implementando la 
arquitectura de tres capas (Metadatos, TUI y Orquestación). Consolida todos 
los módulos fundamentales necesarios para la gestión segura y eficiente de 
la infraestructura.

Estado del Paquete:
    - Versión: 2.0.1
    - Fase: Finalización de Fase 2 (Transición a Orquestación V2).
    - Integridad: Validaciones automáticas de catálogo y seguridad criptográfica activas.

Módulos Incluidos:
    - security: Gestión de secretos, hashing bcrypt y validación de seguridad.
    - models: Esquemas de datos Pydantic para validación de metadatos.
    - dependency_graph: Motor de resolución topológica de dependencias y recursos.
    - logging_config: Infraestructura de registro de eventos (Consola/JSON).
    - state: Persistencia de estado y gestión de archivos de entorno (.env).
    - preflight: Suite de auditoría de requisitos del sistema y hardware.
    - templating: Motor de renderizado dinámico de configuraciones (Jinja2).
    - registry: Sistema de descubrimiento de servicios basado en manifiestos.

Flujo de Ejecución:
    1. Carga y validación del catálogo desde apps_metadata.py.
    2. Interacción del usuario vía TUI para la selección de componentes.
    3. Resolución del grafo de dependencias y cálculo de recursos.
    4. Generación segura de variables de entorno y archivos de orquestación.
    5. Ejecución delegada a Ansible para el despliegue final.
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
