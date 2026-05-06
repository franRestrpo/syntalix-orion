# Syntalix-Orion - Instrucciones para Agentes

## Descripción General

**Syntalix-Orion** es una plataforma de Infraestructura como Código (IaC) para desplegar aplicaciones self-hosted en Docker Swarm, utilizando automatización declarativa (Ansible) y una interfaz de terminal guiada (TUI en Textual).

## Arquitectura V2 (3 Capas) - Estado Actual

```
┌─────────────────────────────────────────────────────────────┐
│  CAPA 1: METADATOS (Fuente de Verdad)                      │
│  apps_metadata.py - Catálogo de apps, RAM, dependencias     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  CAPA 2: PRESENTACIÓN Y LÓGICA (Textual TUI)              │
│  main.py → TUI → DependencyGraph → .env                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  CAPA 3: ORQUESTACIÓN (Ansible)                            │
│  site.yml → engine/runner → Docker Swarm                  │
└─────────────────────────────────────────────────────────────┘
```

## Estructura del Proyecto

```
syntalix-orion/
├── main.py                          # Punto de entrada (raíz)
├── apps_metadata.py                  # Fuente de verdad (catálogo de apps)
├── site.yml                         # Playbook maestro de Ansible
├── setup.sh                         # Script de bootstrap
├── inventory.ini                     # Inventario (localhost)
├── ansible.cfg                       # Configuración Ansible
├── AUDITORIA_V2.md                   # Reporte de hallazgos técnicos (Seguridad/SRP/Clean Code)
│
├── engine/                          # Motor de ejecución Ansible
│   └── ansible_runner_real.py      # Runner asíncrono basado en subprocess
│
├── scripts/                   # Módulos Python (TUI, core, tests)
│   ├── tui.py               # Punto de entrada de la interfaz
│   ├── core/                # Lógica de negocio (DependencyGraph, Security, State)
│   ├── ui/                  # Componentes de la interfaz Textual
│   │   ├── app.py           # Clase OrionTUI principal
│   │   ├── screens/         # Pantallas (Selection, Config, Deploy)
│   │   ├── managers/        # Gestores de estado (StateStore)
│   │   └── components/      # Widgets personalizados
│   └── tests/               # Suite de tests pytest
│
├── roles/                          # Roles Ansible (core, data, monitoring, apps)
├── group_vars/all/vars.yml         # Variables centralizadas
└── docs/                           # Documentación técnica (Hardening, Config, Troubleshooting)
```

## Estándar de Documentación Profesional

El proyecto ha sido profesionalizado con docstrings detallados en **español**:
1.  **Docstrings de Módulos:** Describen responsabilidades, componentes principales y flujo de datos.
2.  **Docstrings de Clases y Métodos:** Utilizan un estilo técnico profesional, especificando argumentos, tipos de retorno y posibles excepciones.
3.  **Idioma:** Estrictamente español para la documentación narrativa y técnica (respetando términos de industria en inglés).

## Hallazgos Críticos de Auditoría (V2)

Consultar `AUDITORIA_V2.md` para detalles. Puntos clave:
- **Seguridad:** Eliminar el uso de `shell=True` en `preflight.py`.
- **Arquitectura:** Migrar de inyecciones de `sys.path` a una estructura de paquete formal (`pyproject.toml`).
- **SRP:** Desacoplar la generación de secretos de la clase `DependencyGraph`.

## Fuente de Verdad

**`apps_metadata.py`** es la ÚNICA fuente de verdad para:
- Catálogo de aplicaciones, RAM, dependencias y variables de configuración.

## Reglas de Contraseñas y Secretos

### CONTRASEÑAS DE BASE DE DATOS (PLAINTEXT - NUNCA HASHEAR)
- Deben ser texto plano seguro (`secrets.token_urlsafe()`).
- **Razón:** Compatibilidad con protocolos de autenticación de bases de datos.

### CREDENCIALES DE APLICACIÓN UI (BCRYPT)
- Deben ser hasheadas con bcrypt (ej: `TRAEFIK_PASSWORD`, `N8N_BASIC_AUTH`).

## Redes y Networking

**REGLAS:**
- Solo puertos 80/443 expuestos vía Traefik.
- Red overlay: `SyntalixNet`.
- Uso de labels dinámicos para TLS y seguridad.

## Flujo de Ejecución TUI

1.  **SelectionScreen:** Navegación por catálogo y resolución de dependencias transitivas.
2.  **ConfigScreen:** Recolección y validación de parámetros (dominios, emails, secretos).
3.  **DeployScreen:** Persistencia en `.env` (chmod 600) y ejecución asíncrona de Ansible.

## Comandos de Ejecución

```bash
# Ejecución estándar (Modo Local)
python main.py

# Despliegue desatendido (requiere .env previo)
sudo ./setup.sh --deploy
```

## Workflow de Desarrollo

**IMPORTANTE:** El desarrollo se realiza localmente pero la ejecución y testing se validan en el VPS remoto. **Commit y push inmediatos** tras cada cambio funcional.

---
*Este documento sirve como guía para agentes de IA que interactúen con el repositorio.*
