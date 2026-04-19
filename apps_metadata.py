from typing import Dict, Any, List, Optional
import secrets
import bcrypt

"""Catalogo de metadatos de aplicaciones (versión 2)."""

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
        "variables": {}
    },
    "authentik": {
        "id": "authentik",
        "name": "Authentik",
        "category": "Core",
        "version": "latest",
        "ram_mb": 512,
        "dependencies": ["crowdsec", "traefik"],
        "variables": {}
    },
    "portainer": {
        "id": "portainer",
        "name": "Portainer",
        "category": "Core",
        "version": "latest",
        "ram_mb": 256,
        "dependencies": ["traefik"],
        "variables": {}
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
                "transform": "bcrypt",
                "length": 32
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
                "auto_generate": True,
                "transform": "bcrypt"
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
                "auto_generate": True,
                "transform": "bcrypt"
            }
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
                "transform": "bcrypt",
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
                "auto_generate": True,
                "transform": "bcrypt"
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
                "auto_generate": True,
                "transform": "bcrypt"
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
            "DIFY_ADMIN_PASSWORD": {
                "type": "secret",
                "description": "Dify admin password",
                "auto_generate": True,
                "transform": "bcrypt"
            },
            "DB_PASSWORD": {
                "type": "secret",
                "description": "Postgres DB password for Dify",
                "auto_generate": True,
                "transform": "bcrypt"
            },
            "REDIS_PASSWORD": {
                "type": "secret",
                "description": "Redis password for Dify",
                "auto_generate": True,
                "transform": "bcrypt"
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
        "variables": {}
    },
    "flowise": {
        "id": "flowise",
        "name": "Flowise",
        "category": "AI",
        "version": "latest",
        "ram_mb": 512,
        "dependencies": ["traefik"],
        "variables": {}
    },
    "n8n": {
        "id": "n8n",
        "name": "n8n",
        "category": "Automation",
        "version": "latest",
        "ram_mb": 512,
        "dependencies": ["postgres_pgvector", "redis", "traefik"],
        "variables": {
            "N8N_BASIC_AUTH": {
                "type": "secret",
                "description": "n8n basic auth password",
                "auto_generate": True,
                "transform": "bcrypt"
            }
        }
    },
    "activepieces": {
        "id": "activepieces",
        "name": "ActivePieces",
        "category": "Automation",
        "version": "latest",
        "ram_mb": 512,
        "dependencies": ["traefik"],
        "variables": {}
    },

    # Comunicacion
    "chatwoot": {
        "id": "chatwoot",
        "name": "Chatwoot",
        "category": "Communication",
        "version": "latest",
        "ram_mb": 1024,
        "dependencies": ["postgres_pgvector", "redis", "traefik"],
        "variables": {
            "POSTGRES_PASSWORD": {
                "type": "secret",
                "description": "Postgres Password for Chatwoot",
                "auto_generate": True,
                "transform": "bcrypt"
            },
            "ACME_EMAIL": {
                "type": "email",
                "description": "Email for TLS certificates",
                "required": True
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
            "POSTGRES_PASSWORD": {
                "type": "secret",
                "description": "Postgres Password for Odoo",
                "auto_generate": True,
                "transform": "bcrypt"
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
    return APP_METADATA.get(app_id)

def all_app_ids() -> List[str]:
    return sorted(APP_METADATA.keys())

__all__ = ["APP_METADATA", "APP_METADATA_ALIAS", "get_metadata", "all_app_ids"]
