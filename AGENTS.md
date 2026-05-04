# Syntalix-Orion - Instrucciones para Agentes

## Descripción General

**Syntalix-Orion** es una plataforma de Infraestructura como Código (IaC) para desplegar aplicaciones self-hosted en Docker Swarm, utilizando automatización declarativa (Ansible) y una interfaz de terminal guiada (TUI en Textual).

## Arquitectura V2 (3 Capas)

```
┌─────────────────────────────────────────────────────────────┐
│  CAPA 1: METADATOS (Fuente de Verdad)                      │
│  apps_metadata.py - Catálogo de apps, RAM, dependencias     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  CAPA 2: PRESENTACIÓN Y LÓGICA (Textual TUI)              │
│  main.py → TUI → DependencyGraph → vars.yml               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  CAPA 3: ORQUESTACIÓN (Ansible)                            │
│  site.yml → roles/ → Docker Swarm                         │
└─────────────────────────────────────────────────────────────┘
```

## Estructura del Proyecto

```
syntalix-orion/
├── main.py                          # Punto de entrada (raíz)
├── apps_metadata.py                  # Fuente de verdad (catálogo de apps)
├── site.yml                         # Playbook maestro de Ansible
├── setup.sh                         # Script de bootstrap
├── requirements.yml                  # Dependencias Ansible Galaxy
├── ansible.cfg                       # Configuración Ansible
├── inventory.ini                     # Inventario (localhost)
│
├── Orion-Python-Ansible/scripts/    # Módulos Python (TUI, core, tests)
│   ├── main.py                     # (legacy - no usar)
│   ├── tui.py                      # Interfaz Textual (OrionTUI)
│   ├── core/                       # Módulos core
│   │   ├── dependency_graph.py    # Grafo de dependencias
│   │   ├── models.py              # Modelos Pydantic
│   │   ├── security.py            # Generación de secretos
│   │   ├── state.py               # Persistencia de estado
│   │   ├── preflight.py           # Verificaciones del sistema
│   │   └── logging_config.py      # Logging estructurado
│   └── tests/                      # Suite de tests pytest
│       ├── conftest.py            # Fixtures
│       ├── test_dependency_graph.py
│       ├── test_models.py
│       ├── test_security.py
│       └── test_tui.py
│
├── roles/                          # Roles Ansible (organizados por categoría)
│   ├── core/                       # traefik, crowdsec, authentik, portainer
│   ├── data/                       # postgres_pgvector, mariadb, mongodb, redis, rabbitmq, qdrant, minio
│   ├── monitoring/                 # prometheus, grafana, loki, uptime_kuma
│   └── apps_*/                     # apps_ai, apps_automation, apps_comms
│
├── group_vars/all/vars.yml         # Variables centralizadas
├── credenciales/                   # Almacenamiento de credenciales (gitignored)
└── docs/                           # Documentación técnica
```

## Fuente de Verdad

**`apps_metadata.py`** es la ÚNICA fuente de verdad para:
- Catálogo de aplicaciones disponibles
- Requerimientos de RAM por aplicación
- Dependencias entre aplicaciones
- Variables de configuración

**Reglas CRÍTICAS:**
1. El `DependencyGraph` debe cargar `apps_metadata.py` y resolver dependencias transitivas
2. El grafo debe detectar ciclos y emitir error si los hay
3. La TUI genera un único archivo `vars.yml` que Ansible consume
4. No يجوز editar roles de Ansible directamente para agregar apps - siempre modificar `apps_metadata.py`

## Reglas de Contraseñas y Secretos

### CONTRASEÑAS DE BASE DE DATOS (PLAINTEXT - NUNCA HASHEAR)
Las contraseñas de bases de datos DEBEN ser texto plano seguro generado con `secrets.token_urlsafe()`:
- `postgres_pgvector` → `POSTGRES_PASSWORD`
- `mariadb` → `MYSQL_ROOT_PASSWORD`
- `mongodb` → `MONGODB_ROOT_PASSWORD`
- `redis` → `REDIS_PASSWORD`
- `qdrant` → `QDRANT_PASSWORD`
- `minio` → `MINIO_SECRET_KEY`

**RAZÓN:** Las aplicaciones de base de datos necesitan la contraseña en texto plano para el protocolo de autenticación. Un hash bcrypt causaría fallo de conexión.

### CREDENCIALES DE APLICACIÓN UI (BCRYPT)
Las contraseñas de login web DEBEN ser hasheadas con bcrypt:
- `traefik` → `TRAEFIK_PASSWORD` (hasheado)
- `n8n` → `N8N_BASIC_AUTH` (hasheado)
- `odoo` → `ADMIN_PASSWORD` (hasheado)

### API KEYS Y SECRETOS
Generados con `secrets.token_urlsafe()` en texto plano:
- `CROWDSEC_ENROLL_KEY`
- `BOUNCER_KEY_TRAEFIK`
- `AUTHENTIK_SECRET_KEY`
- `EV_API_KEY`

### DEDUPLICACIÓN
- `POSTGRES_PASSWORD` solo existe en `postgres_pgvector`
- Apps dependientes (Chatwoot, Odoo, Dify, n8n) consumen la contraseña centralizada
- NO redefinir contraseñas de base de datos en apps dependientes

## Límites de RAM

El motor DEBE:
1. Sumar la RAM de todas las apps seleccionadas + dependencias
2. Emitir advertencia CRÍTICA si el total excede el umbral del servidor (por defecto 8 GB)
3. Advertir pero permitir despliegue si el usuario lo confirma

## Redes y Networking

**REGLAS:**
- NO exponer puertos HTTP directamente al host
- Todas las apps web deben estar detrás de Traefik
- Usar labels dinámicos de Docker para TLS y políticas de seguridad
- Red overlay: `SyntalixNet` (o configurable)

## Dependencias Obligatorias de Apps

| App | Dependencias Obligatorias |
|-----|---------------------------|
| Flowise | postgres_pgvector + redis |
| ActivePieces | postgres_pgvector + redis |
| Evolution API | mongodb |
| Chatwoot | rabbitmq (NO solo redis) |
| n8n | postgres_pgvector + redis |
| dify | postgres_pgvector + redis |

## Restricciones del Entorno

### WAF / Cloudflare
El entorno está protegido por un WAF externo (Cloudflare).
- Error `526 Invalid SSL Certificate`: Verificar configuración SSL/TLS en Cloudflare
- Error `404 Not Found`: Verificar rutas en Traefik Y en Cloudflare
- Traefik ACME challenge puede ser bloqueado por modo "Full (strict)"

### Tráfico Saliente Bloqueado
Servicios como CrowdSec o Authentik pueden mostrar `[Errno 111] Connection refused` si el WAF/firewall bloquea tráfico saliente externo. Esto NO es un problema de configuración Docker interna.

## Comandos de Testing

```bash
# Ejecutar suite de tests
cd Orion-Python-Ansible/scripts
pytest

# Tests específicos
pytest tests/test_security.py
pytest tests/test_dependency_graph.py

# Con cobertura
pytest --cov=core tests/
```

**Fixtures disponibles** (`conftest.py`):
- `sample_metadata`: Catálogo de ejemplo
- `temp_dir`: Directorio temporal
- `mock_env_file`: Archivo .env simulado
- `security_config`: Configuración de seguridad

## Ejecución y TUI

### Punto de Entrada
- `main.py` (raíz): Selector de bootstrap (modo local/remote)
- `Orion-Python-Ansible/scripts/tui.py`: OrionTUI (Textual App)

### Inyección de Path
`main.py` inyecta `Orion-Python-Ansible/scripts` en `sys.path` para importar los módulos core.

### Modo Mock
Para testing sin ejecutar Ansible real:
```bash
RUNNER_MODE=mock python main.py
```

## Workflow de Desarrollo y Deploy

### FLUJO CRÍTICO:
1. Realizar cambios en el código
2. **Commit y push immediatamente**: `git add . && git commit -m "..." && git push origin main`
3. En el VPS remoto: `git pull origin main`
4. Ejecutar los cambios

**RAZÓN:** El proyecto se testa activamente en un VPS remoto, no en el entorno local del agente.

## Ejecución de Playbooks Ansible

```bash
# Despliegue completo
ansible-playbook site.yml -e @ansible_vars.yml

# Verificar syntax
ansible-playbook site.yml --syntax-check

# Check mode (dry-run)
ansible-playbook site.yml -e @ansible_vars.yml --check
```

## Playbook Maestro (site.yml)

El playbook `site.yml` es el punto de entrada para Ansible. Lee `ansible_vars.yml` y ejecuta roles condicionalmente según `ansible_enabled_roles`.

## Notas de Seguridad

1. **Nunca commitar `ansible_vars.yml`** - contiene secretos
2. **Nunca commitar `credenciales/`** - gitignored pero verificar
3. **Permisos de archivos**: `chmod 600` para archivos .env y vars
4. **Logging seguro**: Usar `mask_secret()` en logs

## Glosario

| Término | Significado |
|---------|-------------|
| TUI | Terminal User Interface (interfaz de terminal) |
| IaC | Infrastructure as Code |
| Swarm | Docker Swarm (orquestación de contenedores) |
| Traefik | Proxy reverso con routing dinámico |
| Vars.yml | Archivo de variables generadas por la TUI |
