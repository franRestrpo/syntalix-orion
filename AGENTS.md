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
│  main.py → TUI → DependencyGraph → secrets/.env           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  CAPA 3: ORQUESTACIÓN (Ansible)                            │
│  site.yml → roles/ → secrets/*.env → Docker Swarm         │
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
├── secrets/                          # Directorio protegido (chmod 700)
│   ├── .env                         # Variables globales (chmod 600)
│   ├── traefik.env                  # Variables por rol
│   ├── grafana.env
│   └── ...
│
├── deploy/                           # YAML manifests (sin datos sensibles)
│   ├── traefik_stack.yml
│   ├── grafana_stack.yml
│   └── ...
│
├── engine/                          # Motor de ejecución Ansible
│   └── ansible_runner_real.py      # Runner asíncrono basado en subprocess
│
├── scripts/
│   ├── tui.py                      # Punto de entrada de la interfaz
│   ├── core/                       # Lógica de negocio
│   │   ├── dependency_graph.py     # Resolución de dependencias
│   │   ├── security.py           # Gestión de contraseñas y validación
│   │   ├── state.py              # Persistencia con protocolo Write-and-Verify
│   │   └── preflight.py          # Auditoría de requisitos
│   └── ui/
│       ├── app.py                 # Clase OrionTUI principal
│       ├── theme.tcss            # Estilos globales (colores, botones)
│       ├── screens/              # Pantallas modulares
│       │   ├── selection/
│       │   │   ├── screen.py
│       │   │   └── style.tcss
│       │   ├── config/
│       │   │   ├── screen.py
│       │   │   └── style.tcss
│       │   └── deploy/
│       │       ├── screen.py
│       │       └── style.tcss
│       ├── managers/             # Gestores de estado (StateStore)
│       └── components/           # Widgets personalizados
│
├── roles/                          # Roles Ansible (core, data, monitoring, apps)
├── group_vars/all/vars.yml         # Variables centralizadas
└── docs/                           # Documentación técnica
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
- **Excepción:** Traefik requiere **obligatoriamente** el uso de un hash (ej. bcrypt) para el middleware `basicauth`. Esta contraseña se solicitará en texto plano en la TUI pero deberá ser transformada a hash (bcrypt) antes de persistirse.
- **Validación obligatoria:** Fortaleza mínima antes de persistir (antes de cualquier hasheo).
- **Ejemplos:** `GRAFANA_PASSWORD`, `PORTAINER_PASSWORD` (texto plano). `TRAEFIK_PASSWORD` (hasheado con bcrypt).

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

## Protocolo de Integridad (Write-and-Verify)

Todo proceso que modifique `secrets/*.env` debe:

1. **Sanitizar:** Eliminar espacios en blanco al inicio/final
2. **Validar:** Verificar fortaleza para Categoría C
3. **Escribir:** Guardar con `chmod 600`
4. **Verificar:** Leer desde disco y comparar con memoria
5. **Abortarr:** Si hay discrepancia, lanzar `PasswordPersistenceError`

```
Pseudocódigo:
  write_file(path, vars)
  disk_content = read_file(path)
  if disk_content != vars:
      raise PasswordPersistenceError("Discrepancia detectada")
```

## Estándar de UI Modular (Separación de Concernss)

### Regla de Oro: CSS Externo Obligatorio
- **PROHIBIDO:** Usar `CSS = """..."""` dentro de clases Python
- **OBLIGATORIO:** Usar `CSS_PATH` para vincular archivos `.tcss`

### Jerarquía de Estilos
```
theme.tcss (Global)
├── Colores de marca ($accent, $primary)
├── Estilos de Header, Footer
└── Botones globales

screen_name/style.tcss (Local)
├── Layout específico de pantalla
├── Bordes y padding
└── Comportamiento de scroll
```

### Requisitos CSS para DeployScreen
```css
# ansible-log {           /* Contenedor de logs Ansible */
    height: 1fr;         /* Expansión flexible */
    border: tall $accent;
    overflow-y: scroll;  /* Scroll vertical obligatorio */
}
```

## Flujo de Ejecución TUI

1. **SelectionScreen:** Navegación por catálogo y resolución de dependencias
2. **ConfigScreen:**
   - Recolección de parámetros (dominios, emails, secretos Category C)
   - Validación de fortaleza en tiempo real
3. **DeployScreen:**
   - Persistencia en `secrets/.env` con protocolo Write-and-Verify
   - Ejecución asíncrona de Ansible
   - Monitoreo via RichLog con scroll automático

## Reglas de Contraseñas y Secretos

### CONTRASEÑAS DE INFRAESTRUCTURA (Category A - NUNCA HASHEAR)
- Texto plano seguro (`secrets.token_urlsafe()`)
- Compatibilidad con protocolos de autenticación de bases de datos

### CONTRASEÑAS DE APLICACIONES UI (Category C - PROHIBIDO HASHEAR)
- Text plano fiel al ingreso del usuario
- Validación de fortaleza obligatoria
- Ejemplo: `TRAEFIK_PASSWORD` se persiste tal cual se ingresa

## Fuente de Verdad

**`apps_metadata.py`** es la ÚNICA fuente de verdad para:
- Catálogo de aplicaciones, RAM, dependencias y variables de configuración.

**`secrets/`** es la ÚNICA ubicación para:
- Contraseñas, tokens, dominios y correos de administración.

## Hallazgos Críticos de Auditoría (V2)

Consultar `AUDITORIA_V2.md` para detalles. Puntos clave:
- **Seguridad:** Eliminar el uso de `shell=True` en `preflight.py`.
- **Arquitectura:** Migrar de inyecciones de `sys.path` a una estructura de paquete formal (`pyproject.toml`).
- **SRP:** Desacoplar la generación de secretos de la clase `DependencyGraph`.
- **Persistencia:** Centralizar todos los secretos en `secrets/` con permisos 700/600.
- **Category C:** PROHIBIDO hashear contraseñas de aplicaciones con UI.

## Redes y Networking

**REGLAS:**
- Solo puertos 80/443 expuestos vía Traefik.
- Red overlay: `SyntalixNet`.
- Uso de labels dinámicos para TLS y seguridad.

## Comandos de Ejecución

```bash
# Ejecución estándar (Modo Local)
python main.py

# Despliegue desatendido (requiere secrets/.env previo)
sudo ./setup.sh --deploy
```

## Workflow de Desarrollo

**IMPORTANTE:** El desarrollo se realiza localmente pero la ejecución y testing se validan en el VPS remoto. **Commit y push inmediatos** tras cada cambio funcional.

## Alineación con Auditoría

Cualquier cambio en la gestión de secretos debe ser validado contra `AUDITORIA_V2.md` para evitar regresiones de seguridad.

---
*Este documento sirve como guía para agentes de IA que interactúen con el repositorio.*