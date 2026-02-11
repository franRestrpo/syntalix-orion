# Arquitectura Detallada (Core v2.0) - Syntalix-Orion

Este documento describe la arquitectura interna del motor de automatización desarrollado en Python y Ansible para **Syntalix-Orion**.

## 1. Diseño Modular del Motor (Python)

El núcleo de la lógica reside en un sistema desacoplado que separa la definición del servicio de la lógica de despliegue.

### 1.1. Registro de Servicios (Service Registry)
Cada aplicación se define como un paquete autocontenido en `Orion-Python-Ansible/scripts/registry/`:
*   `manifest.json`: Metadatos, dependencias (Postgres, Redis), variables requeridas y secretos.
*   `stack.yml.j2`: Plantilla dinámica de Docker Stack.
*   `.env.example`: Definición de variables de entorno.

### 1.2. Módulos Core
*   **`generator.py`**: Transforma plantillas Jinja2 en archivos Compose finales, inyectando variables de entorno y configuraciones de red.
*   **`config.py`**: Gestiona la persistencia de configuraciones y la interacción con el usuario (CLI Wizard) para solicitar datos faltantes.
*   **`checks.py` / `preflight.py`**: Validan el estado del sistema, la existencia de redes overlay y la disponibilidad de recursos antes del despliegue.
*   **`deploy.py`**: Wrapper sobre el binario de Docker para ejecutar despliegues de stacks con manejo de errores avanzado.

## 2. Orquestación con Ansible

Ansible actúa como el motor de configuración del sistema operativo y preparación de infraestructura base.

### 2.1. Roles Principales
*   **`common`**: Prepara el sistema (paquetes base, Python venv, Git).
*   **`docker`**: Instala Docker Engine, configura el repositorio oficial e inicializa el clúster **Docker Swarm**.
*   **`desplegador_aplicaciones`**: El componente más avanzado que:
    *   Itera sobre el catálogo de aplicaciones definidas en `aplicaciones.yml`.
    *   Gestiona volúmenes persistentes de forma automática.
    *   Despliega los servicios directamente en Swarm.

## 3. Integración con Portainer API

Aunque el despliegue principal es directo a Swarm para mayor robustez, el sistema soporta la integración con Portainer para:
*   **Webhooks de Actualización**: Permite que sistemas externos (CI/CD) disparen actualizaciones de servicios en Portainer.
*   **Gestión por API**: Script de ejemplo en `scripts/examples/portainer_deploy.py` para usuarios que prefieren centralizar la gestión en la API de Portainer.

## 4. Flujo de Trabajo de Despliegue

1.  **Carga:** El sistema lee el manifiesto del servicio y las variables persistentes.
2.  **Validación:** Se comprueban dependencias (ej: si Chatwoot requiere Postgres, verifica que el stack de BD esté activo).
3.  **Generación:** Se renderizan los archivos `.env` y `_stack.yml` en la carpeta `/deploy`.
4.  **Ejecución:** Ansible o Python lanzan el comando `docker stack deploy`.
5.  **Monitoreo:** El sistema espera a que los servicios alcancen el estado `healthy`.

---
*Este documento complementa la [Guía de Configuración y Despliegue](CONFIG_DEPLOY.md).*
