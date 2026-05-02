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
    """Categorías válidas de aplicaciones."""
    CORE = "Core"
    DATA = "Data"
    MONITORING = "Monitoring"
    AI = "AI"
    AUTOMATION = "Automation"
    COMMUNICATION = "Communication"
    MANAGEMENT = "Management"
    OTHER = "Other"


class VariableType(str, Enum):
    """Tipos de variables válidos."""
    STRING = "string"
    SECRET = "secret"
    EMAIL = "email"
    DOMAIN = "domain"
    INTEGER = "integer"
    BOOLEAN = "boolean"


class TransformType(str, Enum):
    """Tipos de transformación válidos."""
    BCRYPT = "bcrypt"
    BASE64 = "base64"
    NONE = "none"


class AppVariable(BaseModel):
    """Definición de una variable de entorno."""
    type: str = Field(default="string", description="Tipo de variable")
    description: str = Field(default="", description="Descripción de la variable")
    required: bool = Field(default=False, description="Si la variable es obligatoria")
    default: Optional[str] = Field(default=None, description="Valor por defecto")
    auto_generate: bool = Field(default=False, description="Generar automáticamente")
    length: int = Field(default=32, ge=16, le=128, description="Longitud para auto-generación")
    transform: Optional[str] = Field(default=None, description="Transformación a aplicar")
    
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
    Representación técnica y validada de los metadatos de una aplicación.
    
    Este modelo define todos los atributos necesarios para que una aplicación 
    sea procesada por el orquestador, incluyendo su identidad, recursos y 
    relaciones de dependencia.
    """
    id: str = Field(..., description="ID único de la aplicación")
    name: str = Field(..., description="Nombre legible de la aplicación")
    category: str = Field(..., description="Categoría de la aplicación")
    version: str = Field(..., description="Versión de la aplicación")
    ram_mb: int = Field(..., ge=0, le=65536, description="RAM requerida en MB")
    dependencies: List[str] = Field(default_factory=list, description="IDs de dependencias")
    variables: Dict[str, AppVariable] = Field(default_factory=dict, description="Variables de entorno")
    init_sql: List[str] = Field(default_factory=list, description="Comandos SQL de inicialización")
    
    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        # Solo permite IDs alfanuméricos y guiones bajos
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
    """Plan de despliegue generado por DependencyGraph."""
    app_id: str
    plan: List[str] = Field(description="Orden de despliegue")
    ram_mb_total: int = Field(description="RAM total requerida")
    vars: Dict[str, Any] = Field(default_factory=dict, description="Variables generadas")
    warnings: List[str] = Field(default_factory=list, description="Advertencias")
    errors: List[str] = Field(default_factory=list, description="Errores de validación")
    
    @property
    def is_valid(self) -> bool:
        """Retorna True si el plan no tiene errores."""
        return len(self.errors) == 0
    
    @property
    def dependencies_count(self) -> int:
        """Retorna el número de dependencias en el plan."""
        return len(self.plan) - 1
    
    model_config = {
        "validate_assignment": True,
    }


def validate_app_metadata(data: Dict[str, Any]) -> AppMetadata:
    """
    Función helper para validar un diccionario como AppMetadata.
    
    Args:
        data: Diccionario con datos de la aplicación
        
    Returns:
        AppMetadata validado
        
    Raises:
        ValidationError: Si los datos no son válidos
    """
    return AppMetadata(**data)


def load_app_catalog(data: Dict[str, Dict[str, Any]]) -> Dict[str, AppMetadata]:
    """
    Carga, normaliza y valida un catálogo completo de aplicaciones.
    
    Itera sobre el diccionario de metadatos crudos, aplica las reglas de 
    validación de Pydantic y retorna una estructura de datos segura.

    Args:
        data (Dict[str, Dict[str, Any]]): Diccionario crudo de metadatos.
        
    Returns:
        Dict[str, AppMetadata]: Diccionario de objetos AppMetadata validados.
        
    Raises:
        ValueError: Si se detectan errores de esquema en uno o más componentes.
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