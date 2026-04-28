# 📋 INFORME DE ANÁLISIS DE CÓDIGO - SYNTALIX-ORION

> **Fecha de análisis:** 2026-04-28
> **Versión del proyecto:** V2 (3-layer architecture)

---

## 1. ESTRUCTURA GENERAL DEL PROYECTO

```
syntalix-orion/
├── apps_metadata.py              # 🔴 FUENTE DE VERDAD - Catálogo de apps
├── main.py                     # ⚠️ TUI Textual para Proxmox (remoto)
├── requirements.txt            # Dependencias Python
├── requirements.yml           # Playbooks Ansible
│
├── Orion-Python-Ansible/scripts/   # 🔵 CORE V2
│   ├── core/
│   │   ├── dependency_graph.py    # ✅ MÓDULO PRINCIPAL
│   │   ├── models.py              # Pydantic models
│   │   ├── config.py              # ConfigManager legacy
│   │   ├── security.py           # Seguridad
│   │   ├── logging_config.py     # Logging
│   │   ├── templating.py         # Jinja2
│   │   └── registry.py           # Service registry (V1)
│   ├── tui.py                   # ✅ TUI PRINCIPAL (local)
│   ├── main.py                   # CLI legacy
│   ├── generator.py              # ⚠️ Duplicado
│   ├── deploy.py                # ⚠️ Duplicado
│   ├── constants.py
│   ├── utils.py
│   ├── checks.py
│   ├── resources.py
│   ├── preflight.py
│   └── tests/
│
├── engine/
│   ├── ansible_runner.py      # Mock runner
│   └── ansible_runner_real.py  # Real runner
│
├── ui/textual_prototype/       # 🗑️ Obsoleto (V1)
│   ├── app.py
│   └── dep_graph.py
│
└── roles/                       # Ansible roles
```

---

## 2. DESCRIPCIÓN DETALLADA DE ARCHIVOS

### 🔴 ARCHIVOS PRINCIPALES (Raíz)

| Archivo | Propósito | Líneas | Estado |
|---------|-----------|-------|--------|
| `apps_metadata.py` | **FUENTE DE VERDAD** - Catálogo de apps con RAM, dependencias, variables | 353 | ✅ Activo |
| `main.py` | Entry point TUI Textual moderna (para Proxmox remoto) | 263 | ⚠️ Need local mode |
| `requirements.yml` | Playbooks Ansible para instalar dependencias | - | ✅ |
| `site.yml` | Playbook maestro de deployment | - | ✅ |
| `inventory.ini` | Hosts Ansible | 7 | ✅ |
| `ansible.cfg` | Configuración Ansible | - | ✅ |

---

### 🟢 CORE: `Orion-Python-Ansible/scripts/core/`

| Archivo | Propósito | Líneas | Estado |
|---------|-----------|-------|--------|
| `dependency_graph.py` | **MÓDULO PRINCIPAL** - Resuelve deps transitivas, detecta ciclos, calcula RAM, genera vars | 502 | ✅ Activo |
| `models.py` | Modelos Pydantic para validación de esquemas | 243 | ✅ Activo |
| `config.py` | ConfigManager interactivo (legacy V1) | 132 | ⚠️ Legacy |
| `security.py` | Generación passwords, bcrypt, validación, mask_secret | 271 | ✅ Activo |
| `logging_config.py` | Logging estructurado con rotación (dual: archivo + consola) | 322 | ✅ Activo |
| `templating.py` | Jinja2 template rendering | 53 | ✅ Activo |
| `registry.py` | Service registry (V1 modular) | 72 | ⚠️ Legacy |

---

### 🟡 SCRIPTS: `Orion-Python-Ansible/scripts/`

| Archivo | Propósito | Estado |
|---------|---------|--------|
| `tui.py` | **TUI PRINCIPAL** - Textual UI para seleccionar apps y desplegar con Ansible | ✅ Activo |
| `main.py` | CLI legacy (V1 modular) | 🗑️ Obsoleto |
| `generator.py` | Generador simple de stack files (string replace) | ⚠️ Duplicado |
| `deploy.py` | Docker stack deploy helper | ⚠️ Duplicado |
| `constants.py` | Constantes (MIN_RAM, CPU, DISK) | ✅ Activo |
| `utils.py` | Helpers Docker, passwords, validación | ✅ Activo |
| `checks.py` | Pre-flight checks | ✅ Activo |
| `resources.py` | Validación recursos Linux (RAM, CPU, disk) | ⚠️ Solo Linux |
| `preflight.py` | Runner preflight | ✅ Activo |

---

### 🟣 ENGINE: `engine/`

| Archivo | Propósito | Estado |
|---------|---------|--------|
| `ansible_runner.py` | Mock runner para UI (simula deployment) | ✅ Activo |
| `ansible_runner_real.py` | Real runner usando ansible-runner package | ✅ Activo |

---

### 🔵 PROTOTYPE: `ui/textual_prototype/` (OBSOLETO V1)

| Archivo | Propósito | Estado |
|---------|---------|--------|
| `app.py` | Prototipo básico Textual | 🗑️ Eliminar |
| `dep_graph.py` | Mock liviano de DependencyGraph | 🗑️ Eliminar |
| `README.md` | Documentación del prototipo | 🗑️ Eliminar |

---

### 🔵 TESTS: `Orion-Python-Ansible/scripts/tests/`

| Archivo | Propósito |
|---------|--------|
| `test_dependency_graph.py` | Tests para DependencyGraph |
| `test_models.py` | Tests para modelos Pydantic |
| `test_security.py` | Tests para seguridad |
| `test_tui.py` | Tests para la TUI |
| `conftest.py` | Fixtures pytest |

---

## 3. FLUJO DE ARQUITECTURA V2

```
┌─────────────────────────────────────────────────────────────┐
│                    apps_metadata.py                         │
│         (FUENTE DE VERDAD - Catálogo de apps)              │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              Orion-Python-Ansible/scripts/                 │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐ │
│  │dependency_  │   models   │  security   │  logging   │ │
│  │  graph.py  │   .py      │    .py      │  _config   │ │
│  └─────────────┴─────────────┴─────────────┴─────────────┘ │
│                      │                                    │
│                      ▼                                   │
│  ┌──────────────────────────────────────────────────┐   │
│  │                    tui.py                         │   │
│  │        (Textual UI - Selección de apps)            │   │
│  └────────────────────┬───────────────────────────────┘   │
│                     │                                    │
│                     ▼                                    │
│  ┌──────────────────────────────────────────────────┐   │
│  │           Genera ansible_vars.yml                    │   │
│  └────────────────────┬───────────────────────────────┘   │
└──────────────────────┼──────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────���─��──────────────────────────┐
│                      Ansible                              │
│  ┌──────────────┬──────────────┬──────────────┐            │
│  │ ansible-    │  site.yml   │ inventory   │            │
│  │ runner.py   │            │   .ini      │            │
│  └──────────────┴──────────────┴──────────────┘            │
└──────────────────────────────────────────────────────────┘
```

---

## 4. CÓDIGO REPETIDO/UNIFICABLE IDENTIFICADO

### 🔴 A) MULTIPLES DEPENDENCY GRAPHS

| Ubicación | Función |lines |
|-----------|--------|------|
| `core/dependency_graph.py` | **COMPLETO** - resolve_dependencies, total_ram_for_plan, generate_vars_for_plan, plan_with_vars_multi | 502 |
| `ui/textual_prototype/dep_graph.py` | MOCK simple con get_plan() | 26 |
| `tui.py` (líneas 220-299) | DeploymentResult dataclass | ~80 |

**PROBLEMA:** Hay 2 implementations del grafo de dependencias.
**IMPACTO:** Confusión, mantenimiento duplicado.
**ACCIÓN:** Eliminar `ui/textual_prototype/dep_graph.py`, mantener solo el oficial.

---

### 🔴 B) MULTIPLES GENERATORS (Template Rendering)

| Ubicación | Función | Tecnología |
|-----------|--------|-------------|
| `core/templating.py` | TemplateManager.render_template() | **Jinja2** (oficial) |
| `generator.py` | generate_stack_file() | String replace `{{key}}` |

**PROBLEMA:** `generator.py` usa plain string replace, no es robusto.
**ACCIÓN:** Mantener solo `core/templating.py` (Jinja2), eliminar `generator.py`.

---

### 🔴 C) MULTIPLES RUNTIME DEPLOYMENT

| Ubicación | Función | Método |
|-----------|--------|--------|
| `deploy.py` | deploy() | **Docker stack** |
| `tui.py` (883-991) | run_ansible_deploy() | **ansible-playbook** |

**PROBLEMA:** Dos formas de deployment diferentes.
**ACCIÓN:** Mantener Ansible (tui.py), eliminar `deploy.py`.

---

### 🔴 D) STATE MANAGEMENT DUPLICADO

| Ubicación | Función | Método |
|-----------|--------|--------|
| `main.py` (45-60) | save_state(), load_state() | JSON file |
| `core/config.py` (74-87) | load_env_file() | .env parsing |

**PROBLEMA:** Funcionalidad similar dispersa.
**ACCIÓN:** Unificar en módulo consistente.

---

### 🔴 E) PASSWORD GENERATION DUPLICADO

| Ubicación | Función |
|-----------|--------|
| `core/security.py` (125-148) | generate_secure_password() |
| `core/config.py` (122-125) | _generate_secret() |
| `utils.py` (215-226) | generate_app_password() |
| `apps_metadata.py` (2-3) | secrets import |

**PROBLEMA:** 3+ funciones casi idénticas.
**ACCIÓN:** Consolidar en `core/security.py`, eliminar otras.

---

### 🔴 F) PREFLIGHT CHECKS DISPERSOS

| Ubicación | Funciones |
|-----------|-----------|
| `checks.py` | require(), swarm_active(), network_exists() |
| `resources.py` | _ram_gb(), _cpu(), _disk_gb(), validate() |
| `preflight.py` | run() - junta todos |
| `utils.py` (103-180) | check_docker_available(), check_swarm_active(), check_network_exists() |

**PROBLEMA:** Lógica dispersa en 4 archivos.
**ACCIÓN:** Consolidar en módulo unificado.

---

## 5. RECOMENDACIONES DE LIMPIEZA

### 🗑️ ARCHIVOS A ELIMINAR

| Archivo | Razón |
|--------|-------|
| `ui/textual_prototype/dep_graph.py` | Redundante - usar `core/dependency_graph.py` |
| `ui/textual_prototype/app.py` | Redundante - usar `tui.py` |
| `ui/textual_prototype/README.md` | Documentación obsoleta |
| `Orion-Python-Ansible/scripts/generator.py` | Duplicado de `core/templating.py` |
| `Orion-Python-Ansible/scripts/deploy.py` | Duplicado de `tui.py` |
| `Orion-Python-Ansible/scripts/main.py` | CLI legacy obsoleto |
| `Orion-Python-Ansible/scripts/preflight.py` | Duplicado de checks.py + utils.py |
| `Orion-Python-Ansible/scripts/resources.py` | Solo Linux, duplica validación |

### 🔧 FUNCIONES A UNIFICAR

| Módulo origen | Módulo destino | Función |
|---------------|---------------|---------|
| `generator.py` | `core/templating.py` | Eliminar |
| `deploy.py` | `tui.py` | Eliminar |
| `main.py` (state) | `core/config.py` | Unificar save/load |
| `config.py` (secrets) | `core/security.py` | Usar generate_secure_password |
| `utils.py` (passwords) | `core/security.py` | Usar generate_secure_password |
| `checks.py` | `utils.py` | Mover a utils |
| `preflight.py` | `utils.py` | Unificar |
| `resources.py` | `utils.py` | Unificar o eliminar |

### ⚠️ ISSUE: main.py vs tui.py

| Archivo | Modo | Uso |
|---------|-----|-----|
| `main.py` (raíz) | Remoto | Pide IP de Proxmox |
| `tui.py` | **Local** | Despliega en Docker local |

**PROBLEMA:** El usuario ejecutó `main.py` y le pidió IP de Proxmox.
**SOLUCIÓN:** Usar `Orion-Python-Ansible/scripts/tui.py` para deployments locales.

---

## 6. ARQUITECTURA RECOMENDADA (POST-LIMPIEZA)

```
syntalix-orion/
├── apps_metadata.py              # ✅ SIN CAMBIOS
├── main.py                    # ⚠️ Needs refactor para modo local
│
├── Orion-Python-Ansible/scripts/
│   ├── core/
│   │   ├── dependency_graph.py  # ✅ SIN CAMBIOS
│   │   ├── models.py            # ✅ SIN CAMBIOS
│   │   ├── config.py           # 🔧 Unificar state mgmt
│   │   ├── security.py        # 🔧 Consolidar passwords
│   │   ├── logging_config.py  # ✅ SIN CAMBIOS
│   │   └── templating.py      # ✅ SIN CAMBIOS
│   ├── tui.py                # ✅ SIN CAMBIOS (TUI oficial)
│   ├── constants.py          # ✅ SIN CAMBIOS
│   └── utils.py            # 🔧 Consolidar checks
│
├── engine/
│   ├── ansible_runner.py      # ✅ SIN CAMBIOS
│   └── ansible_runner_real.py # ✅ SIN CAMBIOS
│
└── roles/                   # ✅ SIN CAMBIOS
```

---

## 7. SUMMARY DE ACCIONES RECOMENDADAS

| Prioridad | Acción | Impacto |
|----------|--------|---------|
| 🔴 Alta | Eliminar `ui/textual_prototype/` | Limpia代码base |
| 🔴 Alta | Eliminar `generator.py` | Reduce duplicación |
| 🔴 Alta | Eliminar `deploy.py` | Reduce duplicación |
| 🟡 Media | Unificar password generation | Mantenimiento |
| 🟡 Media | Unificar preflight checks | Mantenimiento |
| 🟢 Baja | Refactorizar `main.py` para local | Mejor UX |

---

## 8. VERSION INFO

- **Python:** 3.10+
- **Dependencies:** textual, pydantic, pyyaml, ansible-runner, bcrypt, jinja2
- **Test suites:**
  - `python -m unittest discover -v` (root tests/)
  - `pytest` (Orion-Python-Ansible/scripts/tests/)

---

> *Documento generado automáticamente el 2026-04-28*
> *Última actualización: 2026-04-28 (POST-REFACTORIZACIÓN)*

---

## RESUMEN POST-REFACTORIZACIÓN V2

### Archivos Eliminados ✅
- `ui/textual_prototype/` (directorio completo)
- `Orion-Python-Ansible/scripts/generator.py`
- `Orion-Python-Ansible/scripts/deploy.py`
- `Orion-Python-Ansible/scripts/main.py`
- `Orion-Python-Ansible/scripts/preflight.py`
- `Orion-Python-Ansible/scripts/resources.py`
- `Orion-Python-Ansible/scripts/checks.py`
- `Orion-Python-Ansible/scripts/constants.py`
- `Orion-Python-Ansible/scripts/core/config.py`

### Módulos Nuevos/Creados ✅
- `core/state.py` - Gestión de estado unificada
- `core/preflight.py` - Validaciones pre-vuelo consolidadas

### Módulos Actualizados ✅
- `core/security.py` - Agregados `generate_app_password()`, `generate_secret()`
- `core/__init__.py` - Exporta todos los módulos core
- `utils.py` - Re-exporta desde módulos core

### Entry Points Refactorizados ✅
- `main.py` - Bootstrap selector (Local vs Remote)