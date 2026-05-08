"""
Módulo de Utilidades - Syntalix-Orion.

Contiene funciones helper usadas en múltiples partes del proyecto.
"""

from typing import Optional


def map_app_variable(app_id: str, var_name: str) -> str:
    """
    Mapea una variable de aplicación a su clave completa con prefijo.

    Args:
        app_id: Identificador de la aplicación (ej: 'traefik')
        var_name: Nombre de la variable (ej: 'PASSWORD')

    Returns:
        Clave formateada como 'TRAEFIK__PASSWORD'
    """
    app_prefix = app_id.upper()
    var_clean = var_name.upper()
    
    if var_clean.startswith(f"{app_prefix}__"):
        return var_clean
    elif var_clean.startswith(f"{app_prefix}_"):
        # Replace the first underscore with double underscore
        return f"{app_prefix}__{var_clean[len(app_prefix)+1:]}"
        
    return f"{app_prefix}__{var_clean}"