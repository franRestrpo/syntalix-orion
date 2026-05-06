# Guía de Configuración y Despliegue - Syntalix-Orion

Esta guía detalla el proceso completo para instalar, configurar y gestionar la infraestructura de **Syntalix-Orion**.

## 📋 Requisitos Previos

Antes de comenzar, asegúrese de que su servidor cumple con los siguientes requisitos:

*   **Sistema Operativo:** Ubuntu 22.04 LTS o Debian 12 (Recomendado).
*   **Recursos:** Mínimo 2GB RAM, 2 vCPUs (Dependiendo de las aplicaciones a desplegar).
*   **Acceso:** Usuario con privilegios de `sudo` o acceso `root`.
*   **Red:** Puertos 80, 443, 2377 (Swarm), 7946 (Swarm UDP/TCP) y 4789 (Overlay) abiertos si se planea un clúster multi-nodo.

## 🚀 Instalación Paso a Paso

### 1. Preparación del Entorno
Clone el repositorio en su servidor:

```bash
git clone https://github.com/franRestrpo/Syntalix-Orion.git
cd Syntalix-Orion
```

### 2. Ejecución del Setup Maestro
El script `setup.sh` automatiza la creación de un entorno virtual de Python, la instalación de Ansible y la ejecución de las tareas base.

```bash
sudo ./setup.sh
```

## 🔄 Migración a Syntalix-Orion v2 (TUI + 3 Capas)
La versión 2 introduce una Terminal User Interface (Textual) y una separación en 3 capas: Metadatos, Presentación/Lógica y Orquestación. A la fecha de este documento, la implementación se encuentra en progreso y permite la generación de un plan de despliegue basado en un catálogo de apps. Consulte docs/V2_ARCHITECTURE.md para los detalles y el estado actual.

**¿Qué hace este script?**
1. Actualiza los repositorios del sistema.
2. Instala dependencias base (`curl`, `git`, `python3-venv`).
3. Crea un entorno virtual (`venv`) para aislar las dependencias de Python.
4. Lanza el Playbook de Ansible para configurar Docker Engine y Docker Swarm.

### 3. Verificación de la Infraestructura
Una vez finalizado, verifique que los componentes principales estén operativos:

```bash
# Verificar estado de Swarm
docker node ls

# Listar stacks desplegados (Traefik y Portainer)
docker stack ls
```

## 📦 Gestión de Aplicaciones (Asistente Syntalix)

Syntalix-Orion incluye un **Wizard Interactivo** para facilitar el despliegue de aplicaciones complejas.

### Desplegar una nueva aplicación
Para iniciar el asistente, ejecute el script de Python:

```bash
python3 main.py
```

El asistente le solicitará:
1. **Dominio:** El FQDN (ej: `crm.tuempresa.com`).
2. **Email:** Para la generación de certificados SSL.
3. **Credenciales:** Contraseñas para bases de datos y servicios.

### Actualización de aplicaciones
Para aplicar cambios en la configuración o actualizar versiones de imágenes:
1. Modifique el archivo de variables correspondiente en `deploy/`.
2. Re-ejecute el asistente o el playbook de Ansible.

## 🛠️ Mantenimiento y Operaciones

### Reinicio de Servicios
Si necesita reiniciar un stack completo (ej: Traefik):
```bash
docker stack rm traefik
# Espere unos segundos a que se limpien los recursos
docker stack deploy -c deploy/traefik.yml traefik
```

### Gestión de Volúmenes
Los datos persistentes se almacenan en volúmenes de Docker. Puede listarlos con:
```bash
docker volume ls | grep Syntalix
```

---
Para más detalles sobre la seguridad del sistema, consulte la [Guía de Hardening](HARDENING.md).
