# 📋 Reporte de Auditoría Técnica: Syntalix-Orion V2

Este documento detalla los hallazgos tras la revisión exhaustiva del código fuente y la arquitectura del proyecto, clasificados por categorías críticas.

---

## 1. 🛡️ Seguridad (Security Issues)

### Hallazgos
- [x] **Ejecución de Comandos (`shell=True`):** 
  - **Ubicación:** `Orion-Python-Ansible/scripts/core/preflight.py`.
  - **Estado:** ✅ Solucionado. Se reemplazó la lógica de `subprocess` con `shutil.which`.
  - **Recomendación:** Mantener el uso de utilidades nativas de Python para evitar la exposición a inyecciones de shell.
- [ ] **Almacenamiento de Secretos (`.env`):**
  - **Ubicación:** Raíz del proyecto.
  - **Riesgo:** Aunque se aplica `chmod 600`, si un servicio (como Traefik) se configura mal y expone la raíz del proyecto, el archivo `.env` (que contiene todas las claves de base de datos) podría ser accesible.
  - **Recomendación:** Mover los archivos sensibles a un directorio dedicado (ej: `secrets/` o `credentials/`) que esté explícitamente excluido de cualquier montaje de volumen de contenedor.
- [ ] **Validación de Secretos en Metadatos:**
  - **Ubicación:** `apps_metadata.py`.
  - **Riesgo:** Algunas contraseñas como `TRAEFIK_PASSWORD` se piden en texto plano y no se validan contra políticas de robustez complejas más allá de la longitud.
  - **Recomendación:** Implementar un validador de entropía para secretos introducidos manualmente por el usuario.

---

## 2. 🧩 Principio de Responsabilidad Única (SRP Violations)

### Hallazgos
- [x] **DependencyGraph Multitarea:**
  - **Estado:** ✅ Solucionado. La lógica de generación y transformación de secretos se movió a `core/security.py`.
  - **Mejora:** `DependencyGraph` ahora solo orquesta el plan, delegando la responsabilidad criptográfica al módulo especializado.
- [ ] **Lógica de Negocio en la UI:**
  - **Ubicación:** `ui/screens/selection.py` y `config.py`.
  - **Problema:** Las pantallas de Textual contienen lógica compleja de resolución de dependencias transitivas y validación de planes.
  - **Recomendación:** Mover la lógica de "si selecciono A, debo marcar B" a un controlador de estado (`StateStore` o un `DeploymentController`) para que la UI sea puramente presentacional.

---

## 3. 🧹 Código Limpio (Clean Code Issues)

### Hallazgos
- [ ] **Inyección Dinámica de PATH:**
  - **Ubicación:** `main.py`, `tui.py`, `ui/app.py`, etc.
  - **Problema:** Uso repetitivo de `sys.path.insert(0, ...)` para poder importar módulos locales. Esto es frágil y dificulta el testing.
  - **Recomendación:** Estructurar el proyecto como un paquete Python instalable (`pyproject.toml` o `setup.py`) y usar rutas relativas de importación estándar.
- [ ] **Carga de Metadatos Redundante:**
  - **Ubicación:** `core/dependency_graph.py` (función `_load_app_metadata`).
  - **Problema:** Algoritmo de búsqueda de archivos manual con múltiples fallbacks. 
  - **Recomendación:** Centralizar la carga del catálogo en un solo punto (Registry) que sea inyectado en las clases que lo necesiten.
- [ ] **Manejo de Errores Silencioso:**
  - **Ubicación:** `core/state.py` (funciones `save_state` y `load_state`).
  - **Problema:** Bloques `except Exception: return False` o `return {}` que ocultan errores de E/S o permisos.
  - **Recomendación:** Capturar excepciones específicas y utilizar el sistema de logging para registrar el error antes de retornar un valor por defecto.

---

## 4. 🏛️ Arquitectura (Architectural Flaws)

### Hallazgos
- [ ] **Acoplamiento con Ansible:**
  - **Ubicación:** `engine/ansible_runner_real.py`.
  - **Problema:** El runner asume rutas fijas para `site.yml` y depende de la existencia de un binario en el venv.
  - **Recomendación:** Abstraer el `AnsibleRunner` mediante una interfaz/clase base para permitir otros backends o modos de simulación (Mock) más robustos.
- [ ] **Fuente de Verdad (apps_metadata.py):**
  - **Problema:** El catálogo es un diccionario Python gigante. A medida que crezca, será difícil de mantener.
  - **Recomendación:** Migrar el catálogo a archivos YAML o JSON individuales por aplicación y cargarlos dinámicamente al inicio.
- [ ] **Gestión de Estado Centralizada:**
  - **Problema:** El estado se guarda en `state.json` y `.env` de forma fragmentada.
  - **Recomendación:** Implementar un repositorio de estado unificado que maneje la persistencia de forma atómica.

---

## 5. 🧹 Deuda Técnica y Limpieza (Legacy Proxmox)

### Hallazgos
- [x] **Código Muerto (Dead Code) en `main.py`:**
  - **Estado:** ✅ Solucionado. Se eliminaron las referencias a Proxmox y la función `run_remote_mode`.
  - **Mejora:** La interfaz ahora es coherente con las capacidades reales del sistema, evitando errores de importación.
- [ ] **Importaciones Condicionales Frágiles:**
  - **Ubicación:** `main.py` (dentro de `run_remote_mode`).
  - **Problema:** Intento de importación local de `SyntalixApp` que fallará inevitablemente en el estado actual.

---

## ✅ Resumen de Recomendaciones Críticas

1.  **Eliminar `shell=True`** en todas las llamadas de sistema.
2.  **Eliminar manipulaciones de `sys.path`** a favor de un entorno de paquete Python formal.
3.  **Refactorizar `DependencyGraph`** para separar el análisis de grafo de la generación de datos.
4.  **Centralizar el almacenamiento de credenciales** en un directorio protegido y fuera de la raíz de la aplicación.
