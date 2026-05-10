# Syntalix-Orion - Instrucciones para Agentes

## Descripción General

**Syntalix-Orion** es una plataforma de Infraestructura como Código (IaC) para desplegar aplicaciones self-hosted en Docker Swarm, utilizando automatización declarativa (Ansible) y una interfaz de terminal guiada (TUI en Textual).

## Arquitectura V2 (3 Capas) - Estado Actualizado

```
┌─────────────────────────────────────────────────────────────┐
│  CAPA 1: METADATOS (Fuente de Verdad)                      │
│  src/syntalix_orion/catalog/*.yml - Catálogo validado Pydantic │
│  src/syntalix_orion/apps_metadata.py - Legacy bridge         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  CAPA 2: PRESENTACIÓN Y LÓGICA (Textual TUI)              │
│  src/syntalix_orion/main.py → OrionTUI → DeploymentController │
│  src/syntalix_orion/core/state_repository.py → secrets/.env  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  CAPA 3: ORQUESTACIÓN (Ansible)                            │
│  site.yml → roles/ → secrets/*.env → Docker Swarm         │
└─────────────────────────────────────────────────────────────┘
```

## Estructura del Proyecto (Layout `src/`)

```
syntalix-orion/
├── pyproject.toml                    # Configuración de paquete (uv/setuptools)
├── setup.sh                          # Script de bootstrap (actualizado para uv)
├── site.yml                         # Playbook maestro de Ansible
├── inventory.ini                     # Inventario (localhost)
├── ansible.cfg                       # Configuración Ansible
├── AUDITORIA_V2.md                   # Reporte de hallazgos técnicos
│
├── src/
│   └── syntalix_orion/
│       ├── __init__.py
│       ├── main.py                  # Punto de entrada (orion command)
│       ├── apps_metadata.py         # Legacy bridge para backward compat
│       ├── utils.py                 # Utilidades (map_app_variable)
│       │
│       ├── core/                    # Lógica de negocio (SRP applied)
│       │   ├── __init__.py
│       │   ├── models.py           # Modelos Pydantic (AppMetadata, AppVariable)
│       │   ├── registry.py          # AppRegistry (cargador YAML)
│       │   ├── dependency_graph.py  # Resolución de dependencias
│       │   ├── deployment_controller.py  # SRP: Lógica de selección
│       │   ├── security.py          # Gestión de contraseñas y validación
│       │   ├── state.py            # Persistencia legacy
│       │   ├── state_repository.py # Persistencia atómica (nuevo)
│       │   ├── preflight.py         # Auditoría de requisitos
│       │   └── logging_config.py    # Configuración de logging
│       │
│       ├── catalog/                 # Catálogo YAML (Fuente de Verdad V2)
│       │   ├── traefik.yml
│       │   ├── crowdsec.yml
│       │   ├── authentik.yml
│       │   ├── portainer.yml
│       │   ├── postgres_pgvector.yml
│       │   ├── redis.yml
│       │   ├── grafana.yml
│       │   └── prometheus.yml
│       │
│       ├── ui/
│       │   ├── __init__.py
│       │   ├── app.py              # Clase OrionTUI principal
│       │   ├── components/          # Widgets personalizados
│       │   │   ├── __init__.py
│       │   │   ├── checkbox.py     # ModernCheckbox
│       │   │   ├── progress.py      # ProgressBar
│       │   │   └── indicators.py    # StatusIndicator
│       │   ├── screens/
│       │   │   ├── __init__.py
│       │   │   ├── selection.py     # SelectionScreen (delegates to Controller)
│       │   │   ├── config.py         # ConfigScreen
│       │   │   └── deploy/
│       │   │       ├── deploy_screen.py
│       │   │       └── deploy_screen.tcss
│       │   ├── managers/
│       │   │   ├── __init__.py
│       │   │   └── state_store.py   # StateStore (en memoria, UI only)
│       │   ├── styles/              # Estilos CSS (theme, colors, typography)
│       │   └── widgets/              # Widgets adicionales
│       │
│       └── engine/                  # Motor de ejecución Ansible
│           ├── __init__.py
│           ├── ansible_runner.py    # Mock Runner
│           └── ansible_runner_real.py  # Real Runner (async)
│
├── secrets/                          # Directorio protegido (chmod 700)
│   ├── .env                         # Variables globales (chmod 600)
│   ├── backups/                     # Backups automáticos
│   └── ...
│
├── roles/                          # Roles Ansible (core, data, monitoring, apps)
├── group_vars/all/vars.yml         # Variables centralizadas
├── tests/                           # Tests (fuera de src/)
│   ├── test_core/
│   ├── test_ui/
│   └── conftest.py
└── docs/                           # Documentación técnica
```

## Modelo de Ejecución con `uv` y `pyproject.toml`

### Comandos de Ejecución

```bash
# Instalación del paquete (primera vez o tras cambios)
uv pip install -e .

# Ejecución vía entry point (recomendado)
orion

# Ejecución como módulo
python -m syntalix_orion.main

# Ejecución directa (desde package)
python -c "from syntalix_orion.main import main; main()"
```

### Gestión de Dependencias con `uv`

```bash
# Crear entorno virtual
uv venv

# Instalar dependencias de desarrollo
uv pip install -e ".[dev]"

# Añadir nueva dependencia
uv add textual
uv add pydantic --dev

# Actualizar todas las dependencias
uv pip install -e . --upgrade
```

## Separación Física de Secretos

**OBLIGATORIO:** Todos los datos sensibles deben residir exclusivamente en `secrets/`.

### Permisos de Seguridad
| Recurso | Permiso | Descripción |
|---------|---------|-------------|
| `secrets/` | `chmod 700` | Restringido al propietario |
| `secrets/*.env` | `chmod 600` | Lectura/escritura solo propietario |
| `deploy/*.yml` | `chmod 644` | Solo lectura pública (sin secretos) |

### Rutas de Orquestación
- **ANTIGUO:** `deploy/*.env` (PROHIBIDO)
- **NUEVO:** `secrets/*.env` (OBLIGATORIO)
- Los roles Ansible deben buscar configuración en `../../secrets/`

## Gobernanza de Contraseñas (Manejo Diferenciado por Categoría)

### Categoría A: Infraestructura (Bases de Datos / Queues)
- **Origen:** Autogeneradas por el sistema (`secrets.token_urlsafe()`)
- **Regla:** El usuario NO puede asignarlas manualmente
- **Entropía mínima:** 64 bits garantizados
- **Ejemplos:** `POSTGRES_PASSWORD`, `RABBITMQ_PASSWORD`, `REDIS_PASSWORD`

### Categoría B: Tokens Técnicos (API Keys)
- **Origen:** Generadas automáticamente por módulos internos
- **Regla:** Generación transparente tras selección de aplicación
- **Ejemplos:** `N8N_ENCRYPTION_KEY`, `AUTHENTIK_SECRET_KEY`, `CROWDSEC_ENROLL_KEY`

### Categoría C: Aplicaciones con Interfaz (TUI)
- **Origen:** Entrada directa del usuario en `ConfigScreen`
- **Regla Crítica:** **PROHIBIDO HASHEAR por defecto** (salvo excepciones explícitas como Traefik) - Persistir texto plano fiel al ingreso para la mayoría de las apps.
- **Excepción:** Traefik requiere **obligatoriamente** el uso de un hash `htpasswd` para el middleware `basicauth`. La aplicación se encarga de emular la salida de `htpasswd -nbB` (prefijo `$2y$`) para evitar problemas de compatibilidad causados por el prefijo `$2b$` de Python.
- **Validación obligatoria:** Fortaleza mínima antes de persistir (antes de cualquier hasheo).
- **Ejemplos:** `GRAFANA_PASSWORD`, `PORTAINER_PASSWORD` (texto plano). `TRAEFIK_PASSWORD` (hasheado con bcrypt formato htpasswd `$2y$`).

## Validación de Fortaleza para Categoría C

Toda contraseña de Categoría C debe cumplir estos requisitos **antes de persistir**:

| Criterio | Requisito |
|----------|-----------|
| Longitud mínima | 12 caracteres |
| Mayúsculas | Al menos 1 |
| Números | Al menos 1 |
| Símbolos | Al menos 1 |
| Espacios | PROHIBIDOS al inicio/final |
| Entropía mínima | 64 bits |

**Si no cumple:** El sistema bloquea el despliegue y emite error crítico.

## Protocolo de Integridad (Write-and-Verify + Atomic Write)

Todo proceso que modifique `secrets/*.env` debe:

1. **Escribir a archivo temporal** (`secrets/.env.tmp`)
2. **Establecer permisos** (`chmod 600`) en temporal
3. **Renombrar atómicamente** (`os.replace()`) temp → real
4. **Verificar** leyendo desde disco y comparando con memoria
5. **Abortar** si hay discrepancia, lanzar `StatePersistenceError`

```
write_file(.env.tmp, vars)
os.chmod(.env.tmp, 0o600)
os.replace(.env.tmp, .env)  # Atómico a nivel SO
verify(.env)
```

## Principio de Responsabilidad Única (SRP) Aplicado

### DeploymentController (Lógica de Negocio)
- **Ubicación:** `src/syntalix_orion/core/deployment_controller.py`
- **Responsabilidad:** Resolver dependencias transitivas, bloquear deselecciones inválidas
- **UI:** SelectionScreen solo emite eventos y recibe resultados

### AppRegistry (Carga de Datos)
- **Ubicación:** `src/syntalix_orion/core/registry.py`
- **Responsabilidad:** Cargar y validar YAMLs del catálogo contra modelos Pydantic
- **Caché:** Singleton para evitar lecturas repetidas de disco

### StateRepository (Persistencia)
- **Ubicación:** `src/syntalix_orion/core/state_repository.py`
- **Responsabilidad:** Escritura atómica, backups, gestión de `.env` y `state.json`
- **Transaccionalidad:** Si falla `.env`, no se modifica `state.json`

## Estándar de UI Modular (Separación de Concerns)

### Regla de Oro: CSS Externo Obligatorio
- **PROHIBIDO:** Usar `CSS = """..."""` dentro de clases Python
- **OBLIGATORIO:** Usar `CSS_PATH` para vincular archivos `.tcss`

### Jerarquía de Estilos
```
ui/styles/theme.tcss (Global)
├── Colores de marca ($accent, $primary)
├── Estilos de Header, Footer
└── Botones globales

screens/{screen}/screen_name.tcss (Local)
├── Layout específico de pantalla
├── Bordes y padding
└── Comportamiento de scroll
```

## Flujo de Ejecución TUI

1. **SelectionScreen:** Navegación por catálogo y resolución de dependencias
   - Delega toda la lógica a `DeploymentController`
2. **ConfigScreen:**
   - Recolección de parámetros (dominios, emails, secretos Category C)
   - Validación de fortaleza en tiempo real
3. **DeployScreen:**
   - Persistencia en `secrets/.env` vía `StateRepository` (atómico)
   - Ejecución asíncrona de Ansible
   - Monitoreo via logs con scroll automático

## Reglas de Contraseñas y Secretos

### CONTRASEÑAS DE INFRAESTRUCTURA (Category A - NUNCA HASHEAR)
- Texto plano seguro (`secrets.token_urlsafe()`)
- Compatibilidad con protocolos de autenticación de bases de datos
- **Regla de Independencia y Reutilización:** Los servicios base (como Redis, Postgres, MariaDB) se instancian una vez por red. Sus contraseñas autogeneradas se persistirán en el archivo global `secrets/.env` con su formato canónico (ej. `REDIS__REDIS_PASSWORD`, `POSTGRES_PGVECTOR__POSTGRES_PASSWORD`). Todas las aplicaciones dependientes (como n8n, Authentik) **DEBEN** referenciar explícitamente estas variables canónicas en lugar de usar variables locales genéricas o aliases. NUNCA se debe inyectar contraseñas de infraestructura a través de variables intermedias como `app_actual.password_db` en los playbooks.

### CONTRASEÑAS DE APLICACIONES UI (Category C - PROHIBIDO HASHEAR)
- Text plano fiel al ingreso del usuario
- Validación de fortaleza obligatoria
- Ejemplo: `TRAEFIK_PASSWORD` se persiste tal cual se ingresa

## Fuente de Verdad

**`src/syntalix_orion/catalog/*.yml`** es la nueva fuente de verdad para:
- Catálogo de aplicaciones, RAM, dependencias y variables de configuración.
- Validado por modelos Pydantic en `core/models.py`.

**`src/syntalix_orion/apps_metadata.py`** (legacy):
- Mantenido para backward compatibility temporal.
- Será migrado completamente a YAML en future versions.

**`secrets/`** es la ÚNICA ubicación para:
- Contraseñas, tokens, dominios y correos de administración.

## Hallazgos de Auditoría Implementados

Ver `AUDITORIA_V2.md` para detalles completos. Cambios implementados:

- ✅ **Seguridad:** Eliminado `shell=True` en `preflight.py`
- ✅ **Arquitectura:** Estructura de paquete formal con `pyproject.toml` y `src/`
- ✅ **SRP:** `DeploymentController` separado de `SelectionScreen`
- ✅ **Persistencia:** `StateRepository` con escritura atómica (Write-and-Rename)
- ✅ **Validación:** Modelos Pydantic para catalog YAML

## Redes y Networking

**REGLAS:**
- Solo puertos 80/443 expuestos vía Traefik
- Red overlay: `SyntalixNet`
- Uso de labels dinámicos para TLS y seguridad

## Comandos de Ejecución

```bash
# Instalación
uv venv
uv pip install -e ".[dev]"

# Ejecución estándar (Modo Local)
orion

# Despliegue desatendido (requiere secrets/.env previo)
sudo ./setup.sh --deploy
```

## Workflow de Desarrollo

**IMPORTANTE:** El desarrollo se realiza localmente pero la ejecución y testing se validan en el VPS remoto. **Commit y push inmediatos** tras cada cambio funcional.

### Estándar de Commits (Git)
Todos los mensajes de commit de Git deben redactarse en **español** de manera profesional, clara y descriptiva. Se recomienda el uso de la convención de "Conventional Commits" manteniendo el prefijo técnico (ej. `feat:`, `fix:`, `refactor:`, `docs:`) pero con el resumen y cuerpo del mensaje íntegramente en español (ej. `fix(n8n): corrige el error 522 de conexión en traefik`).

### Verificación de imports tras cambios

```bash
# Verificar que el paquete se importa correctamente
python -c "from syntalix_orion.core.models import AppMetadata; print('OK')"

# Verificar entry point
orion --help

# Ejecutar tests
pytest tests/
```

---

*Este documento sirve como guía para agentes de IA que interactúen con el repositorio.*