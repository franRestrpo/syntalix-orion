"""
Orquestador de Variables y Secretos - Syntalix-Orion.

Este mdulo centraliza la lgica de generacin, transformacin y asignacin 
de variables de entorno y secretos para los planes de despliegue.

Responsabilidades (SRP):
    - Extraer variables definidas en el catlogo.
    - Generar contraseas y secretos seguros segn especificacin.
    - Aplicar transformaciones criptogrficas (bcrypt, base64).
    - Preservar estado anterior (idempotencia).
"""

from typing import Dict, List, Any, Optional
from syntalix_orion.core.models import AppMetadata, AppVariable
from syntalix_orion.core.security import generate_and_transform_secret
from syntalix_orion.utils import map_app_variable
from syntalix_orion.core.logging_config import get_logger

logger = get_logger(__name__)

class VariableOrchestrator:
    """
    Servicio encargado de generar y consolidar variables para despliegues.
    """

    def __init__(self, catalog: Dict[str, AppMetadata]):
        """
        Inicializa el orquestador con el catlogo de aplicaciones.
        
        Args:
            catalog: Diccionario de metadatos de aplicaciones validados.
        """
        self.catalog = catalog

    def _generate_secret_value(self, var_def: AppVariable) -> str:
        """
        Delega la generacin de valores secretos al mdulo de seguridad.
        """
        return generate_and_transform_secret(
            length=var_def.length or 32,
            transform=var_def.transform
        )

    def generate_vars_for_plan(self, ordered_plan: List[str], existing_vars: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Genera el conjunto de variables de entorno necesarias para la ejecucin del plan.
        Preserva variables existentes para asegurar la idempotencia.

        Args:
            ordered_plan (List[str]): Lista de IDs de aplicaciones en orden de despliegue.
            existing_vars (Optional[Dict[str, str]]): Diccionario de variables de estado previas.
            
        Returns:
            Dict[str, Any]: Diccionario de variables mapeadas como APPID__VARNAME.
        """
        existing_vars = existing_vars or {}
        all_vars: Dict[str, Any] = existing_vars.copy()
        
        # Aadir la lista de roles activos para Ansible
        all_vars["ansible_enabled_roles"] = ordered_plan

        for aid in ordered_plan:
            meta = self.catalog.get(aid)
            if not meta:
                continue
                
            vars_def = meta.variables or {}

            for var_name, var_def in vars_def.items():
                key = map_app_variable(aid, var_name)

                # Preservar variable si ya existe y tiene un valor vlido
                if key in existing_vars and existing_vars[key]:
                    continue

                # Respetar auto_generate: si es False, no autogenerar
                if var_def.type == "secret" and var_def.auto_generate:
                    value = self._generate_secret_value(var_def)
                    all_vars[key] = value
                else:
                    value = var_def.default or ""
                    all_vars[key] = value
                    
        return all_vars
