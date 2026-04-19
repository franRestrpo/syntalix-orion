"""
Validador de conexión a Docker Swarm a través de Portainer API.

Utiliza el módulo de seguridad para conexiones SSL configurables.
"""

import os
import sys
import requests
from typing import Optional, Tuple
from getpass import getpass

# Importar módulos de seguridad
from core.security import get_security_config, generate_secure_password
from core.logging_config import get_logger

# Logger
logger = get_logger(__name__)

# Colores para fallback (si no hay logging configurado)
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'


def print_success(msg: str) -> None:
    """Imprime mensaje de éxito."""
    print(f"{GREEN}[SUCCESS]{RESET} {msg}")


def print_info(msg: str) -> None:
    """Imprime mensaje informativo."""
    print(f"{YELLOW}[INFO]{RESET} {msg}")


def print_error(msg: str) -> None:
    """Imprime mensaje de error."""
    print(f"{RED}[ERROR]{RESET} {msg}")


def validate_swarm_connection(
    url: str,
    username: str,
    password: str,
    verify_ssl: bool = True,
    ca_bundle: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Valida conexión a Portainer y verifica el estado de Docker Swarm.
    
    Args:
        url: URL base de Portainer
        username: Nombre de usuario
        password: Contraseña
        verify_ssl: Si True, verifica certificados SSL
        ca_bundle: Ruta a archivo CA bundle personalizado
        
    Returns:
        Tupla (éxito: bool, mensaje: str|None)
    """
    # Configurar seguridad
    security_config = get_security_config()
    
    if ca_bundle:
        security_config.configure_ca_bundle(ca_bundle)
    
    # Obtener parámetro de verificación
    verify_param = security_config.get_verify_param(verify_ssl)
    
    # 1. Limpiar URL
    url = url.rstrip('/')
    if not url.startswith('http'):
        url = f"https://url}"
    
    logger.info("Conectando a Portainer", extra={"url": url, "verify_ssl": verify_ssl})
    print_info(f"Conectando a Portainer en: {url}")
    
    # 2. Autenticación (Obtener JWT)
    auth_url = f"{url}/api/auth"
    try:
        auth_payload = {"username": username, "password": password}
        response = requests.post(
            auth_url,
            json=auth_payload,
            verify=verify_param,
            timeout=10,
        )
        
        if response.status_code == 401:
            logger.error("Autenticación fallida - credenciales inválidas")
            print_error("Autenticación fallida - credenciales inválidas")
            return False, "Credenciales inválidas"
        
        if response.status_code == 404:
            logger.error("Endpoint de autenticación no encontrado")
            print_error(f"Endpoint de autenticación no encontrado en {auth_url}")
            return False, "API de Portainer no disponible"
        
        if response.status_code != 200:
            logger.error(f"Error de autenticación - Status: {response.status_code}")
            print_error(f"Autenticación fallida. Status: {response.status_code}")
            return False, f"Error HTTP {response.status_code}"
        
        jwt_token = response.json().get('jwt')
        if not jwt_token:
            logger.error("No se recibió token JWT")
            print_error("No se recibió token JWT")
            return False, "Token JWT no recibido"
        
        logger.info("Autenticación exitosa con Portainer")
        print_success("Autenticado con Portainer (JWT Token recibido)")
        
    except requests.exceptions.SSLError as e:
        logger.error("Error de certificado SSL", extra={"error": str(e)})
        print_error(f"Error de certificado SSL: {e}")
        print_info("Sugerencia: Use --ca-bundle para especificar un CA bundle personalizado")
        return False, f"Error SSL: {e}"
    
    except requests.exceptions.ConnectionError as e:
        logger.error("Error de conexión", extra={"error": str(e)})
        print_error(f"Error de conexión: {e}")
        return False, f"Error de conexión: {e}"
    
    except requests.exceptions.Timeout:
        logger.error("Timeout de conexión")
        print_error("Timeout de conexión (10s)")
        return False, "Timeout de conexión"
    
    except Exception as e:
        logger.error("Error desconocido", extra={"error": str(e)})
        print_error(f"Error de conexión: {str(e)}")
        return False, str(e)
    
    # Headers para solicitudes subsecuentes
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }
    
    # 3. Obtener Endpoints (Encontrar endpoint primario/Swarm)
    endpoints_url = f"{url}/api/endpoints"
    try:
        response = requests.get(
            endpoints_url,
            headers=headers,
            verify=verify_param,
            timeout=10,
        )
        
        if response.status_code != 200:
            logger.error(f"Error al obtener endpoints - Status: {response.status_code}")
            print_error(f"Error al obtener endpoints. Status: {response.status_code}")
            return False, f"Error HTTP {response.status_code}"
        
        endpoints = response.json()
        
        if not endpoints:
            logger.warning("No se encontraron endpoints")
            print_error("No se encontraron endpoints en Portainer")
            return False, "Sin endpoints disponibles"
        
        # Buscar endpoint primario
        target_endpoint = None
        for endpoint in endpoints:
            if endpoint.get('Name') == 'primary' or endpoint.get('Id') == 1:
                target_endpoint = endpoint
                break
        
        if not target_endpoint and len(endpoints) > 0:
            target_endpoint = endpoints[0]
        
        if not target_endpoint:
            logger.error("No se encontró endpoint primario")
            print_error("No se encontró endpoint primario")
            return False, "Sin endpoint primario"
        
        endpoint_id = target_endpoint.get('Id')
        endpoint_name = target_endpoint.get('Name', 'unknown')
        
        logger.info("Endpoint encontrado", extra={"id": endpoint_id, "name": endpoint_name})
        print_success(f"Endpoint encontrado: ID {endpoint_id} (Nombre: {endpoint_name})")
        
    except Exception as e:
        logger.error("Error al obtener endpoints", extra={"error": str(e)})
        print_error(f"Error al obtener endpoints: {str(e)}")
        return False, str(e)
    
    # 4. Validar Estado de Swarm
    docker_info_url = f"{url}/api/endpoints/{endpoint_id}/docker/info"
    try:
        response = requests.get(
            docker_info_url,
            headers=headers,
            verify=verify_param,
            timeout=10,
        )
        
        if response.status_code != 200:
            logger.error(f"Error al obtener Docker Info - Status: {response.status_code}")
            print_error(f"Error al obtener Docker Info. Status: {response.status_code}")
            return False, f"Error HTTP {response.status_code}"
        
        docker_info = response.json()
        swarm_info = docker_info.get('Swarm', {})
        
        # Verificar si LocalNodeState es 'active'
        node_state = swarm_info.get('LocalNodeState')
        
        if node_state == 'active':
            nodes_count = swarm_info.get('Nodes', 0)
            cluster_id = swarm_info.get('Cluster', {}).get('ID', 'unknown')
            
            logger.info(
                "Docker Swarm activo",
                extra={"cluster_id": cluster_id, "nodes": nodes_count}
            )
            print_success(f"Docker Swarm está ACTIVO")
            print_info(f"Nodos en Swarm: {nodes_count}")
            print_success(f"ID del Cluster: {cluster_id}")
            return True, None
        
        else:
            state_descriptions = {
                'pending': 'Swarm pendientes de inicializar',
                'error': 'Error en Swarm',
                'inactive': 'Swarm inactivo',
                'locked': 'Swarm bloqueado',
            }
            
            description = state_descriptions.get(node_state, f'Estado desconocido: {node_state}')
            
            logger.warning("Docker Swarm no activo", extra={"state": node_state})
            print_error(f"Docker Swarm NO está activo. Estado: {description}")
            return False, f"Swarm {node_state}"
        
    except Exception as e:
        logger.error("Error al validar Swarm", extra={"error": str(e)})
        print_error(f"Error al validar Swarm: {str(e)}")
        return False, str(e)


def main():
    """Función principal para validación interactiva."""
    print("--- Validador de Portainer & Swarm API ---")
    print()
    
    # Intentar obtener de variables de entorno primero
    url = os.getenv("PORTAINER_URL")
    user = os.getenv("PORTAINER_USER")
    pwd = os.getenv("PORTAINER_PASS")
    verify_ssl_str = os.getenv("PORTAINER_VERIFY_SSL", "true").lower()
    verify_ssl = verify_ssl_str in ("true", "1", "yes")
    ca_bundle = os.getenv("PORTAINER_CA_BUNDLE")
    
    if not url:
        url = input("URL de Portainer (ej: https://portainer.dominio.com): ").strip()
    if not user:
        user = input("Usuario: ").strip()
    if not pwd:
        pwd = getpass("Contraseña: ")
    
    print()
    
    # Ejecutar validación
    success, error_msg = validate_swarm_connection(
        url=url,
        username=user,
        password=pwd,
        verify_ssl=verify_ssl,
        ca_bundle=ca_bundle,
    )
    
    print()
    if success:
        print_success(">>> COMUNICACIÓN ESTABLECIDA EXITOSAMENTE <<<")
        sys.exit(0)
    else:
        print_error(f">>> COMUNICACIÓN FALLIDA: {error_msg} <<<")
        sys.exit(1)


if __name__ == "__main__":
    main()
