# Syntalix-Orion (v2.0)

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Docker Swarm](https://img.shields.io/badge/Orchestrator-Docker%20Swarm-blue.svg)](https://docs.docker.com/engine/swarm/)
[![Ansible](https://img.shields.io/badge/Automation-Ansible-red.svg)](https://www.ansible.com/)

**Syntalix-Orion** es una plataforma de automatización avanzada diseñada para el despliegue y gestión de infraestructura moderna basada en contenedores. Optimizada para la seguridad, escalabilidad y facilidad de uso, utiliza **Ansible**, **Python** y **Docker Swarm** para ofrecer un entorno de producción robusto.

## 🌟 Características Principales

*   **Orquestación Nativa:** Despliegue automatizado sobre **Docker Swarm** para alta disponibilidad.
*   **Gestión de Tráfico:** Proxy inverso dinámico con **Traefik**, incluyendo terminación SSL automática.
*   **Panel de Control:** Administración visual de contenedores y servicios mediante **Portainer**.
*   **Wizard Interactivo:** Asistente inteligente para el despliegue de aplicaciones (Chatwoot, n8n, etc.).
*   **Infraestructura como Código (IaC):** Configuración idempotente mediante roles de Ansible altamente modulares.
*   **Seguridad por Diseño:** Implementación de mejores prácticas de hardening y redes aisladas (Overlay).

## 📂 Estructura del Proyecto

```text
.
├── setup.sh                # Script maestro de inicialización
├── playbook.yml            # Orquestador principal de Ansible
├── deploy/                 # Artefactos de despliegue y variables de entorno
├── Orion-Python-Ansible/   # Núcleo de automatización (Roles y Scripts)
├── ansible/            # Roles: common, docker, desplegador_aplicaciones
│   └── scripts/            # Lógica de negocio y asistente interactivo
└── docs/                   # Documentación técnica detallada
```

## 🚀 Inicio Rápido

Para iniciar el despliegue de la infraestructura base, ejecute los siguientes comandos en un servidor limpio (Ubuntu/Debian):

```bash
git clone https://github.com/franRestrpo/Syntalix-Orion.git
cd Syntalix-Orion
sudo ./setup.sh
```

*Para una guía detallada paso a paso, consulte la [Guía de Configuración y Despliegue](docs/CONFIG_DEPLOY.md).*

## 📖 Documentación

| Documento | Descripción |
| :--- | :--- |
| 🛡️ [**Hardening & Seguridad**](docs/HARDENING.md) | Mejores prácticas y configuraciones de seguridad aplicadas. |
| ⚙️ [**Guía de Despliegue**](docs/CONFIG_DEPLOY.md) | Configuración paso a paso y gestión de aplicaciones. |
| 🛠️ [**Arquitectura Técnica**](docs/ARCHITECTURE.md) | Detalles internos sobre el motor de automatización. |

## ⚖️ Licencia

Este proyecto se distribuye bajo la licencia **GNU General Public License v3.0**. Consulte el archivo `LICENSE` para obtener más información.

---
Desarrollado con ❤️ por **Syntalix-Orion**.
