"""
Módulo de Metadatos de Aplicaciones (Fuente de Verdad).

Este archivo contiene la definición centralizada de todas las aplicaciones disponibles 
en el ecosistema Syntalix-Orion V2. Es la única fuente de verdad para el catálogo 
de aplicaciones, sus dependencias, requerimientos de RAM y variables de configuración.

Estructura del Catálogo:
    - Core: Infraestructura base (Traefik, CrowdSec, Authentik).
    - Data: Bases de datos y brokers (Postgres, MariaDB, Redis, RabbitMQ).
    - AI: Aplicaciones de inteligencia artificial (Dify, Flowise, OpenWebUI).
    - Automation: Automatización de flujos (n8n, ActivePieces).
    - Communication: Plataformas de comunicación (Chatwoot, Evolution API).
    - Management: Gestión empresarial (Odoo).
    - Monitoring: Observabilidad (Prometheus, Grafana, Loki).
"""

from typing import Dict, Any, List, Optional
import secrets
import bcrypt

APP_METADATA: Dict[str, Dict[str, Any]] = {
    # Core Infrastructure Layer
    "traefik": {
        "id": "traefik",
        "name": "Traefik",
        "category": "Core",
        "version": "3.x",
        "ram_mb": 256,
        "dependencies": [],
        "variables": {
            "TRAEFIK_DASHBOARD_URL": {
                "type": "domain",
                "description": "Domain for Traefik Dashboard",
                "required": True
            },
            "ACME_EMAIL": {
                "type": "email",
                "description": "Email for Let's Encrypt certificates",
                "required": True
            },
            "INTERNAL_NETWORK": {
                "type": "string",
                "description": "Internal Docker Network",
                "default": "SyntalixNet"
            },
            "TRAEFIK_USER": {
                "type": "string",
                "description": "Traefik Dashboard Username",
                "default": "traefik-admin"
            },
            "TRAEFIK_PASSWORD": {
                "type": "secret",
                "description": "Traefik Dashboard Password",
                "auto_generate": True,
                "transform": "bcrypt"
            }
        }
    },
    "crowdsec": {
        "id": "crowdsec",
        "name": "CrowdSec",
        "category": "Core",
        "version": "latest",
        "ram_mb": 256,
        "dependencies": ["traefik"],
        "variables": {
            "CROWDSEC_ENROLL_KEY": {
                "type": "secret",
                "description": "CrowdSec Enrollment Key",
                "auto_generate": True
            },
            "BOUNCER_KEY_TRAEFIK": {
                "type": "secret",
                "description": "CrowdSec Bouncer Key for Traefik",
                "auto_generate": True
            }
        }
    },
    "authentik": {
        "id": "authentik",
        "name": "Authentik",
        "category": "Core",
        "version": "latest",
        "ram_mb": 512,
        "dependencies": ["crowdsec", "traefik"],
        "variables": {
            "AUTHENTIK_DOMAIN": {
                "type": "domain",
                "description": "Domain for Authentik platform",
                "required": True,
                "auto_generate": False
            },
            "AUTHENTIK_SECRET_KEY": {
                "type": "secret",
                "description": "Authentik Secret Key",
                "auto_generate": True
            }
        }
    },
    "portainer": {
        "id": "portainer",
        "name": "Portainer",
        "category": "Core",
        "version": "latest",
        "ram_mb": 256,
        "dependencies": ["traefik"],
        "variables": {
            "PORTAINER_DOMAIN": {
                "type": "domain",
                "description": "Domain for Portainer Dashboard",
                "required": True,
                "auto_generate": False
            },
            "PORTAINER_ENCRYPTION_KEY": {
                "type": "secret",
                "description": "Encryption key for Portainer DB",
                "auto_generate": True,
                "length": 32
            }
        }
    },

    # Data Backends (obligatorios)
    "postgres_pgvector": {
        "id": "postgres_pgvector",
        "name": "Postgres (pgvector)",
        "category": "Data",
        "version": "latest",
        "ram_mb": 2048,
        "dependencies": [],
        "variables": {
            "POSTGRES_PASSWORD": {
                "type": "secret",
                "description": "PostgreSQL admin password",
                "auto_generate": True,
                "length": 32
            },
            "POSTGRES_USER": {
                "type": "string",
                "description": "Default database user",
                "default": "orion_admin"
            },
            "POSTGRES_DB": {
                "type": "string",
                "description": "Default database name",
                "default": "appdb"
            }
        },
        "init_sql": ["CREATE EXTENSION IF NOT EXISTS vector;"]
    },
    "mariadb": {
        "id": "mariadb",
        "name": "MariaDB / MySQL",
        "category": "Data",
        "version": "10.x",
        "ram_mb": 512,
        "dependencies": [],
        "variables": {
            "MYSQL_ROOT_PASSWORD": {
                "type": "secret",
                "description": "MySQL root password",
                "auto_generate": True
            },
            "MYSQL_DATABASE": {
                "type": "string",
                "description": "Default database",
                "default": "appdb"
            }
        }
    },
    "mongodb": {
        "id": "mongodb",
        "name": "MongoDB",
        "category": "Data",
        "version": "latest",
        "ram_mb": 1024,
        "dependencies": [],
        "variables": {
            "MONGODB_ROOT_PASSWORD": {
                "type": "secret",
                "description": "MongoDB root password",
                "auto_generate": True
            }
        }
    },
    
    # Message Queue (requerido por Chatwoot)
    "rabbitmq": {
        "id": "rabbitmq",
        "name": "RabbitMQ",
        "category": "Data",
        "version": "3-management",
        "ram_mb": 512,
        "dependencies": [],
        "volumes": {
            "/var/lib/rabbitmq": "rabbitmq_data"
        },
        "environment": {
            "RABBITMQ_DEFAULT_USER": "orion",
            "RABBITMQ_DEFAULT_PASS": "auto_generate",
            "RABBITMQ_DEFAULT_VHOST": "/"
        }
    },
    
    "redis": {
        "id": "redis",
        "name": "Redis",
        "category": "Data",
        "version": "6",
        "ram_mb": 256,
        "dependencies": [],
        "variables": {
            "REDIS_PASSWORD": {
                "type": "secret",
                "description": "Redis password",
                "auto_generate": True,
                "length": 32
            }
        }
    },
    "qdrant": {
        "id": "qdrant",
        "name": "Qdrant",
        "category": "Data",
        "version": "latest",
        "ram_mb": 512,
        "dependencies": [],
        "variables": {
            "QDRANT_PASSWORD": {
                "type": "secret",
                "description": "Qdrant access password",
                "auto_generate": True
            }
        }
    },
    "minio": {
        "id": "minio",
        "name": "MinIO",
        "category": "Data",
        "version": "latest",
        "ram_mb": 1024,
        "dependencies": [],
        "variables": {
            "MINIO_SECRET_KEY": {
                "type": "secret",
                "description": "MinIO secret key",
                "auto_generate": True
            }
        }
    },

    # Monitoring (Capa de Monitoreo)
    "prometheus": {
        "id": "prometheus",
        "name": "Prometheus",
        "category": "Monitoring",
        "version": "latest",
        "ram_mb": 512,
        "dependencies": [],
        "variables": {}
    },
    "grafana": {
        "id": "grafana",
        "name": "Grafana",
        "category": "Monitoring",
        "version": "latest",
        "ram_mb": 512,
        "dependencies": ["prometheus"],
        "variables": {}
    },
    "loki": {
        "id": "loki",
        "name": "Loki",
        "category": "Monitoring",
        "version": "latest",
        "ram_mb": 512,
        "dependencies": [],
        "variables": {}
    },
    "uptime_kuma": {
        "id": "uptime_kuma",
        "name": "Uptime Kuma",
        "category": "Monitoring",
        "version": "latest",
        "ram_mb": 256,
        "dependencies": [],
        "variables": {}
    },

    # Apps de Valor
    "dify": {
        "id": "dify",
        "name": "Dify AI",
        "category": "AI",
        "version": "latest",
        "ram_mb": 1536,
        "dependencies": ["postgres_pgvector", "redis", "qdrant", "traefik"],
        "variables": {
            "DIFY_DOMAIN": {
                "type": "domain",
                "description": "Domain for Dify AI platform",
                "required": True,
                "auto_generate": False
            },
            "DIFY_INIT_PASSWORD": {
                "type": "secret",
                "description": "Dify init admin password",
                "auto_generate": True
            }
        }
    },
    "openwebui": {
        "id": "openwebui",
        "name": "OpenWebUI",
        "category": "AI",
        "version": "latest",
        "ram_mb": 512,
        "dependencies": ["traefik"],
        "variables": {
            "OPENWEBUI_DOMAIN": {
                "type": "domain",
                "description": "Domain for OpenWebUI",
                "required": True,
                "auto_generate": False
            }
        }
    },
    "flowise": {
        "id": "flowise",
        "name": "Flowise",
        "category": "AI",
        "version": "latest",
        "ram_mb": 512,
        "dependencies": ["postgres_pgvector", "redis", "traefik"],
        "variables": {
            "FLOWISE_DOMAIN": {
                "type": "domain",
                "description": "Domain for Flowise AI",
                "required": True,
                "auto_generate": False
            }
        }
    },
    "n8n": {
        "id": "n8n",
        "name": "n8n",
        "category": "Automation",
        "version": "latest",
        "ram_mb": 512,
        "dependencies": ["postgres_pgvector", "redis", "traefik"],
        "variables": {
            "N8N_DOMAIN": {
                "type": "domain",
                "description": "Domain for n8n Automation",
                "required": True,
                "auto_generate": False
            },
            "N8N_BASIC_AUTH": {
                "type": "secret",
                "description": "n8n basic auth password",
                "auto_generate": True,
                "transform": "bcrypt"
            },
            "N8N_ENCRYPTION_KEY": {
                "type": "secret",
                "description": "n8n Encryption Key",
                "auto_generate": True
            },
            "N8N_RUNNERS_AUTH_TOKEN": {
                "type": "secret",
                "description": "n8n Worker Auth Token",
                "auto_generate": True,
                "length": 32
            }
        }
    },
    "activepieces": {
        "id": "activepieces",
        "name": "ActivePieces",
        "category": "Automation",
        "version": "latest",
        "ram_mb": 512,
        "dependencies": ["postgres_pgvector", "redis", "traefik"],
        "variables": {}
    },

    # Comunicacion
    "chatwoot": {
        "id": "chatwoot",
        "name": "Chatwoot",
        "category": "Communication",
        "version": "latest",
        "ram_mb": 1024,
        "dependencies": ["postgres_pgvector", "redis", "rabbitmq", "traefik"],
        "variables": {
            "CHATWOOT_DOMAIN": {
                "type": "domain",
                "description": "Domain for Chatwoot platform",
                "required": True,
                "auto_generate": False
            },
            "SECRET_KEY_BASE": {
                "type": "secret",
                "description": "Chatwoot secret key base",
                "auto_generate": True
            },
            "ACME_EMAIL": {
                "type": "email",
                "description": "Email for TLS certificates",
                "required": True
            }
        }
    },

    # Evolution API (requires MongoDB)
    "evolution_api": {
        "id": "evolution_api",
        "name": "Evolution API",
        "category": "Automation",
        "version": "latest",
        "ram_mb": 512,
        "dependencies": ["mongodb", "traefik"],
        "variables": {
            "EVOLUTION_API_DOMAIN": {
                "type": "domain",
                "description": "Domain for Evolution API",
                "required": True,
                "auto_generate": False
            },
            "EV_API_KEY": {
                "type": "secret",
                "description": "Evolution API key",
                "auto_generate": True
            }
        }
    },

    # Gestión
    "odoo": {
        "id": "odoo",
        "name": "Odoo (Community)",
        "category": "Management",
        "version": "15.x",
        "ram_mb": 1024,
        "dependencies": ["postgres_pgvector", "redis", "traefik"],
        "variables": {
            "ODOO_DOMAIN": {
                "type": "domain",
                "description": "Domain for Odoo ERP",
                "required": True,
                "auto_generate": False
            },
            "ADMIN_PASSWORD": {
                "type": "secret",
                "description": "Admin password for Odoo",
                "auto_generate": True,
                "transform": "bcrypt"
            }
        }
    },
}

# Backwards-compatible alias
APP_METADATA_ALIAS = APP_METADATA

def get_metadata(app_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene los metadatos de una aplicación específica por su identificador.

    Args:
        app_id (str): Identificador único de la aplicación (ej: 'traefik').

    Returns:
        Optional[Dict[str, Any]]: Diccionario con los metadatos de la aplicación 
            o None si el identificador no se encuentra en el catálogo.
    """
    return APP_METADATA.get(app_id)

def all_app_ids() -> List[str]:
    """
    Retorna una lista ordenada de todos los identificadores de aplicaciones 
    disponibles en el catálogo.

    Returns:
        List[str]: Lista alfabética de IDs de aplicaciones.
    """
    return sorted(APP_METADATA.keys())

__all__ = ["APP_METADATA", "APP_METADATA_ALIAS", "get_metadata", "all_app_ids"]

# =============================================================================
# AUTO-VALIDACIÓN DEL CATÁLOGO
# =============================================================================
# Valida automáticamente el catálogo al importar este módulo.
# Esto garantiza que el esquema sea correcto y falla temprano si hay errores.

if __name__ != "builtins":
    try:
        from core.models import load_app_catalog
        _validated_catalog = load_app_catalog(APP_METADATA)
    except ImportError:
        # Si no se puede importar (ej. desde la raíz sin path), omitir validación
        pass
    except Exception as e:
        raise ValueError(f"Error de validación en apps_metadata.py: {e}")
