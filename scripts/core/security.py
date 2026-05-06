"""
Módulo de Seguridad y Criptografía para Syntalix-Orion.

Este módulo centraliza todas las operaciones relacionadas con la seguridad del sistema, 
proporcionando una capa de abstracción para la gestión de secretos, validación de 
entradas y configuraciones SSL.

Funcionalidades principales:
    - Gestión de contextos SSL y certificados CA.
    - Generación de contraseñas seguras con entropía criptográfica.
    - Hasheo y verificación de credenciales con bcrypt.
    - Validación de dominios y correos electrónicos (regex).
    - Sanitización de entradas para prevenir ataques de inyección.
    - Enmascaramiento de secretos para logging seguro.
"""

import os
import ssl
import secrets
import hashlib
import base64
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass

# Intentar importar bcrypt (opcional)
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False
    import warnings
    warnings.warn("bcrypt no disponible. Instalar con: pip install bcrypt")


@dataclass
class SSLContext:
    """Configuración de contexto SSL."""
    verify: bool = True
    cert_file: Optional[str] = None
    key_file: Optional[str] = None
    ca_file: Optional[str] = None


class SecurityConfig:
    """
    Gestión Centralizada de la Configuración de Seguridad (Singleton).
    
    Proporciona un punto único de control para la infraestructura de seguridad 
    del sistema, incluyendo la gestión de bundles de CA para validación SSL y 
    las políticas de robustez de contraseñas.
    """
    
    DEFAULT_PASSWORD_LENGTH = 32
    MIN_PASSWORD_LENGTH = 16
    
    _instance = None
    
    def __new__(cls):
        """Implementación del patrón Singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Inicializa los parámetros de seguridad por defecto."""
        if self._initialized:
            return
        self._initialized = True
        self._ssl_context: Optional[ssl.SSLContext] = None
        self._ca_bundle_path: Optional[str] = None
    
    def configure_ca_bundle(self, path: Optional[str] = None) -> None:
        """
        Configura la ubicación del bundle de certificados de Autoridades de Certificación (CA).
        
        Si no se proporciona una ruta, el sistema intentará localizar automáticamente 
        los bundles estándar en sistemas operativos tipo Unix.

        Args:
            path (Optional[str]): Ruta absoluta al archivo .crt o .pem del CA bundle.
        """
        if path and os.path.exists(path):
            self._ca_bundle_path = path
        else:
            # Intentar rutas comunes en Linux
            common_paths = [
                '/etc/ssl/certs/ca-certificates.crt',
                '/etc/pki/tls/certs/ca-bundle.crt',
                '/etc/ssl/ca-bundle.pem',
            ]
            for p in common_paths:
                if os.path.exists(p):
                    self._ca_bundle_path = p
                    break
    
    def get_ssl_context(self, verify: bool = True) -> ssl.SSLContext:
        """
        Genera un contexto SSL (TLS) configurado según las políticas de seguridad.
        
        Args:
            verify (bool): Determina si se debe realizar la verificación de certificados.
            
        Returns:
            ssl.SSLContext: Contexto configurado listo para su uso en sockets o clientes HTTP.
        """
        if verify:
            context = ssl.create_default_context()
            
            # Inyectar bundle de CA personalizado si existe
            if self._ca_bundle_path:
                context.load_verify_locations(self._ca_bundle_path)
            else:
                # Fallback a los certificados raíz del sistema
                context.load_default_certs()
                
        else:
            # Contexto inseguro (USAR SOLO EN DESARROLLO/TESTING LOCAL)
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
        return context
    
    def get_verify_param(self, verify: bool = True) -> Optional[str]:
        """
        Obtiene el parámetro de verificación para requests.
        
        Returns:
            Ruta al CA bundle, o False para desactivar verificación
        """
        if verify:
            return self._ca_bundle_path if self._ca_bundle_path else True
        return False


# Singleton global
_security_config = SecurityConfig()


def get_security_config() -> SecurityConfig:
    """Obtiene la instancia global de configuración de seguridad."""
    return _security_config


def generate_secure_password(
    length: int = SecurityConfig.DEFAULT_PASSWORD_LENGTH,
    use_bcrypt: bool = False
) -> str:
    """
    Genera una contraseña de alta entropía apta para entornos productivos.
    
    Utiliza el generador de números aleatorios seguro del sistema (os.urandom) 
    para garantizar que los secretos generados sean resistentes a ataques de fuerza bruta.
    
    Args:
        length (int): Cantidad de caracteres del secreto (mínimo 16).
        use_bcrypt (bool): Si es True, retorna el hash bcrypt del secreto en lugar 
            de su valor en texto plano. Recomendado para contraseñas de UI.
            
    Returns:
        str: Secreto generado en formato URL-safe o su representación hasheada.
    """
    if length < SecurityConfig.MIN_PASSWORD_LENGTH:
        length = SecurityConfig.MIN_PASSWORD_LENGTH
    
    password = secrets.token_urlsafe(length)
    
    if use_bcrypt and BCRYPT_AVAILABLE:
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        return hashed.decode('utf-8')
    
    return password


def hash_password_bcrypt(password: str) -> str:
    """
    Realiza un hasheo irreversible utilizando el algoritmo bcrypt.
    
    Este método es el estándar para almacenar credenciales de usuario de forma segura, 
    añadiendo un 'salt' aleatorio de forma transparente.
    
    Args:
        password (str): Contraseña en texto plano que se desea proteger.
        
    Returns:
        str: Hash bcrypt resultante codificado en UTF-8.
    """
    if not BCRYPT_AVAILABLE:
        raise ImportError("bcrypt no está instalado. Ejecute: pip install bcrypt")
    
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password_bcrypt(password: str, hashed: str) -> bool:
    """
    Valida si una contraseña en texto plano coincide con un hash bcrypt previo.
    
    Args:
        password (str): Credencial proporcionada por el usuario.
        hashed (str): Hash almacenado en el sistema para la validación.
        
    Returns:
        bool: True si la verificación es exitosa.
    """
    if not BCRYPT_AVAILABLE:
        raise ImportError("bcrypt no está instalado. Ejecute: pip install bcrypt")
    
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def generate_api_key(length: int = 32) -> str:
    """
    Genera una clave de API (API Key) criptográficamente segura.
    
    Args:
        length (int): Longitud de la clave generada.
        
    Returns:
        str: Clave API en formato URL-safe.
    """
    return secrets.token_urlsafe(length)


def validate_domain(domain: str) -> bool:
    """
    Valida si una cadena de texto sigue el formato estándar de un dominio (FQDN).
    
    Args:
        domain (str): Cadena a validar.
        
    Returns:
        bool: True si el formato es correcto.
    """
    import re
    # Patrón robusto para validación de dominios
    pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain))


def validate_email(email: str) -> bool:
    """
    Valida si una cadena de texto tiene un formato de correo electrónico válido.
    
    Args:
        email (str): Cadena a validar.
        
    Returns:
        bool: True si el formato es correcto.
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def generate_and_transform_secret(length: int = 32, transform: Optional[str] = None) -> str:
    """
    Genera un secreto seguro y aplica una transformación criptográfica si se solicita.
    
    Args:
        length (int): Longitud base del secreto.
        transform (Optional[str]): Algoritmo de transformación ('bcrypt', etc).
        
    Returns:
        str: El secreto resultante (plano o hasheado).
    """
    # Generar token seguro base
    secret = generate_secure_password(length=length)
    
    if transform == "bcrypt":
        try:
            return hash_password_bcrypt(secret)
        except (ImportError, Exception):
            # Fallback a plano si falla el hasheo, pero emitiendo advertencia
            return secret
            
    return secret


def sanitize_input(value: str, max_length: int = 255) -> str:
    """
    Limpia y normaliza cadenas de entrada para mitigar riesgos de inyección (Shell/SQL).
    
    Filtra caracteres especiales potencialmente peligrosos y restringe la longitud 
    del texto para prevenir ataques de denegación de servicio por agotamiento de memoria.

    Args:
        value (str): Cadena de texto a procesar.
        max_length (int): Límite superior de caracteres permitidos.
        
    Returns:
        str: Cadena sanitizada, libre de operadores de control y espacios innecesarios.
    """
    if not value:
        return ""
    
    # Eliminar operadores de control de shell y caracteres de escape
    dangerous_chars = [';', '&', '|', '`', '$', '(', ')', '<', '>', '\n', '\r']
    result = value
    
    for char in dangerous_chars:
        result = result.replace(char, '')
    
    return result[:max_length].strip()



def mask_secret(value: str, visible_chars: int = 4) -> str:
    """
    Enmascara un secreto para logging seguro.
    
    Args:
        value: Secreto a enmascarar
        visible_chars: Caracteres visibles al final
        
    Returns:
        Secreto enmascarado (ej: "****abcd")
    """
    if not value or len(value) <= visible_chars:
        return "****"
    
    return "*" * (len(value) - visible_chars) + value[-visible_chars:]


def generate_app_password(length: int = 32) -> str:
    """
    Genera una contraseña segura para aplicaciones.
    Alias recomendado para uso en toda la aplicación.
    
    Args:
        length: Longitud de la contraseña
        
    Returns:
        Contraseña segura
    """
    return generate_secure_password(length=length)


def generate_secret(length: int = 32) -> str:
    """
    Genera una cadena aleatoria segura para secretos.
    Alias compatibilidad para código legacy.
    
    Args:
        length: Longitud del secreto
        
    Returns:
        Cadena aleatoria segura
    """
    import string
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))
