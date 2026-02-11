# 🛡️ Hardening y Mejores Prácticas - Syntalix-Orion

La seguridad es un pilar fundamental en **Syntalix-Orion**. Este documento describe las medidas de seguridad implementadas y las recomendaciones para mantener un entorno de producción seguro.

## 1. Seguridad a Nivel de Sistema Operativo

*   **Minimización de Superficie de Ataque:** Solo se instalan los paquetes estrictamente necesarios para el funcionamiento de Docker y Ansible.
*   **Gestión de Repositorios:** Se utilizan repositorios oficiales con validación de firmas GPG para garantizar la integridad del software instalado.
*   **Aislamiento de Entorno:** El motor de automatización (Python/Ansible) reside en un entorno virtual (`venv`), evitando conflictos con librerías del sistema y facilitando la auditoría de dependencias.

## 2. Docker y Swarm Hardening

*   **Redes Overlay Aisladas:** Todos los servicios se despliegan en redes `overlay` privadas (ej: `SyntalixNet`). Los contenedores no tienen exposición directa a la red pública a menos que se configure explícitamente a través del proxy inverso.
*   **Gestión de Secretos:** (Recomendado) Utilizar `docker secret` para manejar contraseñas, certificados y claves de API, en lugar de variables de entorno en texto plano.
*   **Control de Tráfico con Traefik:**
    *   **Terminación SSL/TLS:** Configuración forzada de HTTPS.
    *   **Seguridad de Cabeceras:** (Opcional) Implementación de cabeceras HSTS, X-Frame-Options, y Content-Security-Policy.
*   **Actualizaciones Automáticas:** El uso de Ansible permite programar actualizaciones de imágenes de contenedores de forma idempotente.

## 3. Mejores Prácticas de Despliegue

### Gestión de Credenciales
*   **Nunca** guarde contraseñas en los archivos `.yml.j2` o playbooks.
*   Utilice el asistente interactivo para inyectar credenciales en archivos `.env` protegidos (permisos `600`).

### Monitorización y Logs
*   **Portainer:** Utilice el control de acceso basado en roles (RBAC) de Portainer para limitar quién puede modificar los stacks.
*   **Logs de Docker:** Los servicios están configurados para usar el driver de log predeterminado (JSON-file) con rotación configurada para evitar el agotamiento de disco.

## 4. Checklist de Seguridad para Producción

1.  [ ] **Cambiar Contraseñas por Defecto:** Inmediatamente después del despliegue, cambie las credenciales de Traefik y Portainer.
2.  [ ] **Configurar Firewall (UFW/Iptables):** Solo permita tráfico en los puertos necesarios (80, 443, 22).
3.  [ ] **SSH Hardening:** Deshabilite el login de root y utilice autenticación por llave pública.
4.  [ ] **Backups:** Implemente una estrategia de backup para los volúmenes de Docker ubicados en `/var/lib/docker/volumes/`.

---
*Para reportar vulnerabilidades o sugerir mejoras de seguridad, por favor abra un Issue en el repositorio.*
