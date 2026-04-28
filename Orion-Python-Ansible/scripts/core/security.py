"""
Módulo de seguridad centralizado para Syntalix-Orion.

Proporciona:
- Contexto SSL configurable
- Generación de contraseñas seguras
- Validación de entradas
- Cifrado de secretos
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
    """Gestor de configuración de seguridad."""
    
    DEFAULT_PASSWORD_LENGTH = 32
    MIN_PASSWORD_LENGTH = 16
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._ssl_context: Optional[ssl.SSLContext] = None
        self._ca_bundle_path: Optional[str] = None
    
    def configure_ca_bundle(self, path: Optional[str] = None) -> None:
        """Configura la ruta al bundle de CA."""
        if path and os.path.exists(path):
            self._ca_bundle_path = path
        else:
            # Intentar rutas comunes
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
        Obtiene un contexto SSL configurado.
        
        Args:
            verify: Si True, verifica certificados SSL
            
        Returns:
            ssl.SSLContext configurado
        """
        if verify:
            context = ssl.create_default_context()
            
            # Añadir CA bundle si está configurado
            if self._ca_bundle_path:
                context.load_verify_locations(self._ca_bundle_path)
            else:
                # Usar los CA del sistema
                context.load_default_certs()
                
        else:
            # Contexto sin verificación (solo para desarrollo)
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
    Genera una contraseña segura criptográficamente.
    
    Args:
        length: Longitud de la contraseña
        use_bcrypt: Si True, retorna el hash bcrypt en lugar del password plano
        
    Returns:
        Contraseña segura o hash bcrypt
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
    Genera hash bcrypt de una contraseña.
    
    Args:
        password: Contraseña en texto plano
        
    Returns:
        Hash bcrypt codificado en UTF-8
    """
    if not BCRYPT_AVAILABLE:
        raise ImportError("bcrypt no está instalado. Instala con: pip install bcrypt")
    
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password_bcrypt(password: str, hashed: str) -> bool:
    """
    Verifica una contraseña contra su hash bcrypt.
    
    Args:
        password: Contraseña en texto plano
        hashed: Hash bcrypt a verificar
        
    Returns:
        True si la contraseña coincide
    """
    if not BCRYPT_AVAILABLE:
        raise ImportError("bcrypt no está instalado. Instala con: pip install bcrypt")
    
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def generate_api_key(length: int = 32) -> str:
    """
    Genera una clave API segura.
    
    Args:
        length: Longitud de la clave
        
    Returns:
        Clave API en formato URL-safe
    """
    return secrets.token_urlsafe(length)


def validate_domain(domain: str) -> bool:
    """
    Valida formato de dominio.
    
    Args:
        domain: Dominio a validar
        
    Returns:
        True si el dominio tiene formato válido
    """
    import re
    
    # Patrón básico de dominio
    pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain))


def validate_email(email: str) -> bool:
    """
    Valida formato de email.
    
    Args:
        email: Email a validar
        
    Returns:
        True si el email tiene formato válido
    """
    import re
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def sanitize_input(value: str, max_length: int = 255) -> str:
    """
    Sanitiza entrada de usuario para prevenir injection.
    
    Args:
        value: Valor a sanitizar
        max_length: Longitud máxima permitida
        
    Returns:
        Valor sanitizado
    """
    if not value:
        return ""
    
    # Eliminar caracteres potencialmente peligrosos
    dangerous_chars = [';', '&', '|', '`', '$', '(', ')', '<', '>', '\n', '\r']
    result = value
    
    for char in dangerous_chars:
        result = result.replace(char, '')
    
    # Limitar longitud
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
