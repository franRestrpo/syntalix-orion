"""
Core modules para Syntalix-Orion.

Este paquete contiene los módulos centrales de la plataforma:
- security: Configuración SSL y generación de secretos
- models: Modelos Pydantic para validación de metadatos
- logging_config: Logging estructurado
- dependency_graph: Grafo de dependencias para despliegues
- config: Gestión de configuración
- templating: Renderizado de plantillas
- registry: Registro de servicios
- state: Gestión de estado (JSON, .env)
- preflight: Validaciones del sistema
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
