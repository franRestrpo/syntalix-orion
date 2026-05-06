"""
Modelos de Datos y Esquemas de Validación para Syntalix-Orion.

Este módulo utiliza la librería Pydantic para definir y validar las estructuras 
de datos fundamentales del sistema. Garantiza que la "Fuente de Verdad" 
(apps_metadata.py) y los planes de despliegue generados cumplan con las 
restricciones técnicas necesarias.

Componentes principales:
    - AppMetadata: Definición técnica completa de una aplicación.
    - AppVariable: Esquema para la gestión de variables de entorno y secretos.
    - DeploymentPlan: Estructura de salida del motor de dependencias.
    - Validadores: Lógica personalizada para IDs, memoria RAM y jerarquías.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


class AppCategory(str, Enum):
    """Categorías Técnicas de Aplicaciones."""
    CORE = "Core"
    DATA = "Data"
    MONITORING = "Monitoring"
    AI = "AI"
    AUTOMATION = "Automation"
    COMMUNICATION = "Communication"
    MANAGEMENT = "Management"
    OTHER = "Other"


class VariableType(str, Enum):
    """Tipos de Datos para Variables de Configuración."""
    STRING = "string"
    SECRET = "secret"
    EMAIL = "email"
    DOMAIN = "domain"
    INTEGER = "integer"
    BOOLEAN = "boolean"


class TransformType(str, Enum):
    """Transformaciones Criptográficas Soportadas."""
    BCRYPT = "bcrypt"
    BASE64 = "base64"
    NONE = "none"


class AppVariable(BaseModel):
    """
    Especificación Técnica de una Variable de Configuración.
    
    Define el comportamiento de una variable, incluyendo su validación, 
    obligatoriedad y si debe ser generada automáticamente por el sistema.
    """
    type: str = Field(default="string", description="Tipo de dato de la variable")
    description: str = Field(default="", description="Propósito de la variable (máx 200 caracteres)")
    required: bool = Field(default=False, description="Indica si el valor es mandatorio para el despliegue")
    default: Optional[str] = Field(default=None, description="Valor predeterminado si no se proporciona uno")
    auto_generate: bool = Field(default=False, description="Activa la generación automática de valores seguros")
    length: int = Field(default=32, ge=16, le=128, description="Longitud en caracteres para valores auto-generados")
    transform: Optional[str] = Field(default=None, description="Algoritmo de transformación (ej: bcrypt)")
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        valid_types = ['string', 'secret', 'email', 'domain', 'integer', 'boolean']
        if v not in valid_types:
            raise ValueError(f"Tipo inválido '{v}'. Valores válidos: {valid_types}")
        return v
    
    @field_validator('transform')
    @classmethod
    def validate_transform(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_transforms = ['bcrypt', 'base64', 'none']
            if v not in valid_transforms:
                raise ValueError(f"Transform inválida '{v}'. Valores válidos: {valid_transforms}")
        return v
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        if len(v) > 200:
            raise ValueError("Descripción muy larga (máx 200 caracteres)")
        return v
    
    model_config = {
        "extra_fields_forbid": True,
        "validate_assignment": True,
    }


class AppMetadata(BaseModel):
    """
    Contrato Técnico de una Aplicación (Catálogo).
    
    Este modelo actúa como el esquema de validación para cualquier aplicación 
    declarada en el sistema. Garantiza que la identidad, los recursos (RAM), 
    las dependencias y la configuración sigan las reglas de negocio.
    """
    id: str = Field(..., description="Identificador único (slug) de la aplicación")
    name: str = Field(..., description="Nombre comercial o descriptivo")
    category: str = Field(..., description="Categoría funcional en el ecosistema")
    version: str = Field(..., description="Etiqueta de versión (tag de imagen Docker)")
    ram_mb: int = Field(..., ge=0, le=65536, description="Memoria RAM mínima recomendada en MB")
    dependencies: List[str] = Field(default_factory=list, description="Lista de prerrequisitos tecnológicos")
    variables: Dict[str, AppVariable] = Field(default_factory=dict, description="Diccionario de configuración")
    init_sql: List[str] = Field(default_factory=list, description="Scripts de inicialización de base de datos")

    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Valida que el ID siga el formato de slug alfanumérico."""
        import re
        if not re.match(r'^[a-z][a-z0-9_]*$', v):
            raise ValueError(
                f"ID inválido '{v}'. Debe empezar con minúscula y contener "
                "solo letras minúsculas, números y guiones bajos."
            )
        return v
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if len(v) < 2:
            raise ValueError(f"Nombre demasiado corto: {v}")
        if len(v) > 100:
            raise ValueError(f"Nombre demasiado largo: {v}")
        return v.strip()
    
    @field_validator('version')
    @classmethod
    def validate_version(cls, v: str) -> str:
        if not v or v.isspace():
            raise ValueError("Versión no puede estar vacía")
        return v.strip()
    
    @field_validator('ram_mb')
    @classmethod
    def validate_ram(cls, v: int) -> int:
        if v < 0:
            raise ValueError("RAM no puede ser negativa")
        if v == 0:
            # Warning pero no error - algunas apps pueden no necesitar RAM especificada
            import warnings
            warnings.warn(f"RAM especificada es 0 para {cls.__name__}")
        return v
    
    @field_validator('dependencies', mode='after')
    @classmethod
    def validate_dependencies(cls, v: List[str]) -> List[str]:
        # Validar formato de IDs de dependencia
        import re
        for dep in v:
            if not re.match(r'^[a-z][a-z0-9_]*$', dep):
                raise ValueError(f"ID de dependencia inválido: '{dep}'")
        return v
    
    @model_validator(mode='after')
    def validate_category(self) -> 'AppMetadata':
        """Valida que la categoría sea válida."""
        valid_categories = ['Core', 'Data', 'Monitoring', 'AI', 'Automation', 'Communication', 'Management']
        if self.category not in valid_categories:
            raise ValueError(
                f"Categoría inválida '{self.category}'. "
                f"Valores válidos: {valid_categories}"
            )
        return self
    
    model_config = {
        "extra_fields_forbid": True,
        "validate_assignment": True,
        "str_strip_whitespace": True,
    }


class DeploymentPlan(BaseModel):
    """
    Representación de un Plan de Despliegue Validado.
    
    Encapsula los resultados generados por el motor de dependencias, incluyendo 
    la secuencia de ejecución, el consumo de recursos y el estado de las variables.
    """
    app_id: str
    plan: List[str] = Field(description="Secuencia ordenada de ejecución de roles")
    ram_mb_total: int = Field(description="Carga de memoria total proyectada")
    vars: Dict[str, Any] = Field(default_factory=dict, description="Variables de entorno resultantes")
    warnings: List[str] = Field(default_factory=list, description="Advertencias de salud del plan")
    errors: List[str] = Field(default_factory=list, description="Errores fatales de validación")
    
    @property
    def is_valid(self) -> bool:
        """Determina si el plan es apto para ejecución sin errores."""
        return len(self.errors) == 0
    
    @property
    def dependencies_count(self) -> int:
        """Calcula el número de componentes auxiliares en el plan."""
        return len(self.plan) - 1
    
    model_config = {
        "validate_assignment": True,
    }


def validate_app_metadata(data: Dict[str, Any]) -> AppMetadata:
    """
    Valida un objeto de datos contra el esquema AppMetadata.
    
    Args:
        data (Dict[str, Any]): Atributos de la aplicación a validar.
        
    Returns:
        AppMetadata: Instancia validada y tipada.
        
    Raises:
        ValidationError: Si los datos no cumplen con las restricciones técnicas.
    """
    return AppMetadata(**data)


def load_app_catalog(data: Dict[str, Dict[str, Any]]) -> Dict[str, AppMetadata]:
    """
    Carga y valida un catálogo completo de aplicaciones (Batch Validation).
    
    Transforma un diccionario crudo de metadatos en un registro tipado y seguro, 
    detectando inconsistencias en el catálogo de forma temprana.

    Args:
        data (Dict[str, Dict[str, Any]]): Catálogo de metadatos (Fuente de Verdad).
        
    Returns:
        Dict[str, AppMetadata]: Registro validado listo para su uso por el orquestador.
        
    Raises:
        ValueError: Si uno o más componentes del catálogo fallan la validación.
    """
    validated = {}
    errors = []
    
    for app_id, app_data in data.items():
        try:
            # Asegurar que el ID coincida
            app_data['id'] = app_id
            validated[app_id] = AppMetadata(**app_data)
        except Exception as e:
            errors.append(f"{app_id}: {str(e)}")
    
    if errors:
        raise ValueError(
            f"Errores de validación en el catálogo:\n" + "\n".join(errors)
        )
    
    return validated


__all__ = [
    "AppVariable",
    "AppMetadata", 
    "DeploymentPlan",
    "validate_app_metadata",
    "load_app_catalog",
    "AppCategory",
    "VariableType",
    "TransformType",
]