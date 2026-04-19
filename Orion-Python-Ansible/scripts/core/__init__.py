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
"""

from core.security import (
    SecurityConfig,
    generate_secure_password,
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

__version__ = "2.0.0"

__all__ = [
    # Security
    "SecurityConfig",
    "generate_secure_password",
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
]
