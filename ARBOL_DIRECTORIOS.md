# Árbol de Directorios - Syntalix-Orion

Generado: 2026-05-01
Proyecto: Syntalix-Orion v2.0.1

```
syntalix-orion/
├── main.py                          # Entry point - Bootstrap selector (Local/Remote mode)
├── apps_metadata.py                  # SOURCE OF TRUTH - App catalog (18 apps)
├── site.yml                         # V2 Master Playbook (reads ansible_vars.yml)
├── playbook.yml                      # Legacy playbook
├── ansible.cfg                      # Ansible configuration
├── inventory.ini                     # Ansible inventory (localhost)
├── requirements.yml                  # Ansible Galaxy dependencies
├── setup.sh                         # Bootstrap script
├── redeploy.sh                      # Redeployment script
├── uninstall.sh                     # Uninstall script
├── fix_permissions.sh              # Permission fix utility
├── AGENTS.md                        # Agent instructions (V2 architecture rules)
├── README.md                        # Project documentation
├── LICENSE                          # License file
├── .gitignore                       # Git ignore rules
├── .ansible-lint                    # Ansible lint config
│
├── .github/
│   ├── workflows/
│   │   └── ci.yml                 # GitHub Actions CI pipeline
│   └── PULL_REQUEST_TEMPLATE.md    # PR template
│
├── aplicaciones.d/                  # Modular app configuration
│   ├── 00-infra.yml               # Infrastructure apps (Traefik, Portainer)
│   └── 01-apps.yml                # User applications
├── aplicaciones.yml                 # Legacy app catalog
│
├── credenciales/                    # Credentials storage (git-ignored)
│   └── .gitkeep
│
├── docs/
│   ├── V2_ARCHITECTURE.md         # V2 architecture documentation
│   ├── CONFIG_DEPLOY.md           # Deployment configuration guide
│   ├── HARDENING.md               # Security hardening guide
│   ├── TROUBLESHOOTING.md         # Troubleshooting guide
│   └── INFORME_ANALISIS.md        # Previous analysis report
│
├── engine/                          # Ansible runner engines
│   ├── ansible_runner.py          # Mock Ansible runner (for UI testing)
│   └── ansible_runner_real.py     # Real Ansible runner (uses ansible-runner)
│
├── group_vars/
│   └── all/
│       └── vars.yml                # Centralized variables (Phase 3 migration)
│
├── logs/                           # Log directory
│   └── .gitkeep
│
├── roles/                          # V2 Ansible Roles (refactored structure)
│   ├── README.md
│   ├── central_vars_demo/
│   │   ├── README.md
│   │   └── tasks/main.yml
│   ├── wait_for_db/
│   │   └── tasks/main.yml
│   ├── core/                       # Core infrastructure
│   │   ├── .gitkeep
│   │   ├── traefik/
│   │   │   └── tasks/main.yml     # Reverse proxy with SSL
│   │   ├── crowdsec/
│   │   │   └── tasks/main.yml     # WAF/Security
│   │   ├── authentik/
│   │   │   └── tasks/main.yml     # SSO/Identity
│   │   └── portainer/
│   │       └── tasks/main.yml     # Docker management UI
│   ├── data/                       # Data backends
│   │   ├── .gitkeep
│   │   ├── postgres_pgvector/
│   │   │   └── tasks/main.yml     # PostgreSQL with vector extension
│   │   ├── mariadb/
│   │   │   └── tasks/main.yml     # MySQL/MariaDB
│   │   ├── mongodb/
│   │   │   └── tasks/main.yml     # NoSQL database
│   │   ├── redis/
│   │   │   └── tasks/main.yml     # Cache/Broker
│   │   ├── rabbitmq/
│   │   │   └── tasks/main.yml     # Message queue
│   │   ├── qdrant/
│   │   │   └── tasks/main.yml     # Vector search
│   │   └── minio/
│   │       └── tasks/main.yml     # S3-compatible storage
│   ├── monitoring/                 # Observability stack
│   │   ├── .gitkeep
│   │   ├── prometheus/
│   │   │   └── tasks/main.yml     # Metrics collection
│   │   ├── grafana/
│   │   │   └── tasks/main.yml     # Dashboards/Visualization
│   │   ├── loki/
│   │   │   └── tasks/main.yml     # Log aggregation
│   │   └── uptime_kuma/
│   │       └── tasks/main.yml     # Uptime monitoring
│   ├── apps_ai/                    # AI Applications
│   │   ├── .gitkeep
│   │   ├── dify/
│   │   │   └── tasks/main.yml     # LLMOps platform
│   │   ├── openwebui/
│   │   │   └── tasks/main.yml     # LLM web interface
│   │   └── flowise/
│   │       └── tasks/main.yml     # AI flow orchestration
│   ├── apps_automation/            # Automation platforms
│   │   ├── .gitkeep
│   │   ├── n8n/
│   │   │   └── tasks/main.yml     # Workflow automation
│   │   └── activepieces/
│   │       └── tasks/main.yml     # Open-source automation
│   ├── apps_comms/                 # Communication platforms
│   │   ├── .gitkeep
│   │   ├── chatwoot/
│   │   │   └── tasks/main.yml     # Customer support CRM
│   │   ├── evolution_api/
│   │   │   └── tasks/main.yml     # WhatsApp API
│   │   └── typebot/
│   │       └── tasks/main.yml     # Chatbots/Forms
│   └── apps_management/            # Business management (commented out)
│       └── .gitkeep
│
├── tests/                          # Unit tests (legacy)
│   └── dep_graph_test.py
│
├── scripts/                        # Legacy/placeholder UI
│
└── Orion-Python-Ansible/          # Python core + Legacy Ansible
    ├── requirements.txt              # Python dependencies
    ├── cleanup_installer.py          # Installer cleanup utility
    │
    ├── ansible/
    │   ├── playbooks/
    │   │   └── infra.yml
    │   └── roles/
    │       ├── common/              # Base system setup
    │       │   ├── defaults/main.yml
    │       │   └── tasks/main.yml
    │       ├── docker/              # Docker installation
    │       │   └── tasks/
    │       │       ├── main.yml
    │       │       └── install_debian.yml
    │       └── desplegador_aplicaciones/  # App deployment role
    │           ├── tasks/
    │           │   ├── main.yml
    │           │   ├── procesar_aplicacion.yml
    │           │   └── dependencias.yml
    │           └── templates/
    │               ├── chatwoot.env.j2
    │               ├── chatwoot.yml.j2
    │               ├── evolution.env.j2
    │               ├── evolution.yml.j2
    │               ├── n8n.env.j2
    │               ├── n8n.yml.j2
    │               ├── portainer.env.j2
    │               ├── portainer.yml.j2
    │               ├── traefik.env.j2
    │               └── traefik.yml.j2
    │
    └── scripts/                    # Python core modules
        ├── main.py                # Legacy entry point
        ├── tui.py                # V2 Textual TUI (OrionTUI class)
        ├── utils.py               # General utilities (re-exports core modules)
        ├── validate_swarm.py      # Swarm validation
        │
        ├── core/                 # Core Python modules
        │   ├── __init__.py        # (TO UPDATE) Package documentation
        │   ├── dependency_graph.py    # Dependency resolution & planning
        │   ├── models.py             # Pydantic models (validation)
        │   ├── security.py           # Security (passwords, SSL, validation)
        │   ├── state.py              # State management (JSON/.env)
        │   ├── preflight.py          # System checks (Docker, RAM, CPU)
        │   ├── logging_config.py     # Structured logging setup
        │   ├── templating.py         # Jinja2 template manager
        │   └── registry.py          # Service registry (manifest.json)
        │
        ├── registry/               # Service manifests
        │   ├── __init__.py        # (TO UPDATE) Registry package docs
        │   ├── traefik/
        │   │   ├── manifest.json
        │   │   └── stack.yml.j2
        │   └── portainer/
        │       ├── manifest.json
        │       └── stack.yml.j2
        │
        ├── stacks/                 # Docker stack templates
        │   ├── .env.example
        │   ├── traefik.yml
        │   └── portainer.yml
        │
        ├── examples/
        │   └── portainer_deploy.py
        │
        └── tests/                 # Pytest test suite
            ├── __init__.py        # (TO UPDATE) Test package docs
            ├── conftest.py        # Pytest fixtures
            ├── README.md
            ├── test_dependency_graph.py
            ├── test_models.py
            ├── test_security.py
            └── test_tui.py
```

## Estadísticas del Proyecto

- **Total de archivos**: ~120 archivos
- **Archivos Python**: ~15 módulos principales
- **Archivos YAML (Ansible)**: ~45 roles/tasks
- **Archivos de configuración**: 8 archivos clave
- **Documentación**: 4 archivos Markdown
- **Tests**: 5 módulos de prueba (pytest) + 1 legacy (unittest)

## Distribución por Categorías

| Categoría | Cantidad | Estados |
|-----------|----------|--------|
| Core (Traefik, Portainer, etc.) | 4 roles | ✅ Activos |
| Data (Postgres, Redis, etc.) | 7 roles | ✅ Activos |
| Monitoring (Prometheus, Grafana) | 4 roles | ✅ Activos |
| AI Apps (Dify, OpenWebUI) | 3 roles | ✅ Activos |
| Automation (n8n, ActivePieces) | 2 roles | ✅ Activos |
| Communication (Chatwoot, etc.) | 3 roles | ✅ Activos |
| Management (Odoo, etc.) | 0 roles | ⏸️ Comentados |
