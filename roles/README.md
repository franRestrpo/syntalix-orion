# 📁 Estructura de Roles Ansible - Syntalix-Orion V2

Este directorio contiene la estructura modular de roles de Ansible organizados por capas funcionales.

## 🏗️ Arquitectura de Roles

```
roles/
├── core/                   # Infraestructura base (obligatorio)
│   ├── traefik/           # Proxy reverso + SSL
│   ├── crowdsec/          # WAF + protección
│   ├── authentik/         # SSO + autenticación
│   └── portainer/        # Gestión visual
│
├── data/                  # Bases de datos y almacenamiento
│   ├── postgres_pgvector/ # PostgreSQL + vector
│   ├── mariadb/           # MySQL compatible
│   ├── mongodb/           # NoSQL
│   ├── redis/             # Cache + sessions
│   ├── rabbitmq/          # Colas de mensajes
│   ├── qdrant/            # Búsqueda vectorial
│   └── minio/             # Almacenamiento S3
│
├── monitoring/            # Observabilidad
│   ├── prometheus/        # Métricas
│   ├── grafana/           # Dashboards
│   ├── loki/              # Logs
│   └── uptime_kuma/       # Uptime monitoring
│
├── apps_ai/              # Aplicaciones de IA
│   ├── dify/              # LLMOps platform
│   ├── openwebui/          # Web UI para LLMs
│   └── flowise/            # Flow orchestration
│
├── apps_automation/       # Automatización
│   ├── n8n/               # Workflow automation
│   └── activepieces/       # Open source automation
│
├── apps_comms/           # Comunicación
│   ├── chatwoot/         # CRM chat
│   ├── evolution_api/     # WhatsApp API
│   └── typebot/           # Chatbots
│
└── apps_management/      # Gestión empresarial
    ├── glpi/             # Helpdesk IT
    ├── odoo/             # ERP
    ├── nocodb/           # Spreadsheet DB
    └── vaultwarden/      # Password manager
```

## 🔄 Uso Dinámico

Los roles se ejecutan condicionalmente según `ansible_enabled_roles`:

```bash
# Instalar todos los roles seleccionados por la TUI
ansible-playbook -i inventory site.yml -e @ansible_vars.yml

# Instalar solo un rol específico
ansible-playbook -i inventory site.yml -e @ansible_vars.yml --tags "postgres"

# Verificar sin ejecutar (dry-run)
ansible-playbook -i inventory site.yml -e @ansible_vars.yml --check
```

## 📝 Estructura de un Rol

Cada rol sigue la estructura estándar de Ansible:

```
roles/<category>/<role_name>/
├── defaults/
│   └── main.yml           # Variables por defecto
├── tasks/
│   └── main.yml          # Tareas principales
├── handlers/
│   └── main.yml          # Handlers
├── templates/
│   └── *.j2              # Plantillas Jinja2
├── files/
│   └── *                 # Archivos estáticos
└── README.md              # Documentación del rol
```

## 🔐 Seguridad

- Los secretos se generan en `ansible_vars.yml` por la TUI
- Nunca commitea archivos `.env` o `ansible_vars.yml` a Git
- Usa `ansible-vault` para cifrar en producción:

```bash
# Cifrar archivo de variables
ansible-vault encrypt ansible_vars.yml

# Editar archivo cifrado
ansible-vault edit ansible_vars.yml

# Ejecutar con archivo cifrado
ansible-playbook -i inventory site.yml -e @ansible_vars.yml --ask-vault-pass
```

## 🚀 Próximos Pasos

1. Implementar cada rol según las variables definidas en `apps_metadata.py`
2. Añadir tests con `molecule` para cada rol
3. Integrar con Ansible Galaxy para dependencias externas
