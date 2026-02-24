# 🛠️ Resolución de Problemas (Troubleshooting) - Syntalix-Orion

Este documento detalla los desafíos técnicos más comunes al desplegar infraestructura con Docker Swarm y cómo este framework los mitiga automáticamente.

---

### 1. Fallo en la Comunicación entre Nodos (Cluster Quorum)
* **El Problema:** Los nodos Worker no logran unirse al Manager o se desconectan intermitentemente debido a puertos bloqueados o latencia.
* **Solución Orion:** El playbook de Ansible realiza una validación previa de los puertos críticos (2377/TCP, 7946/TCP-UDP, 4789/UDP). Orion asegura que las reglas de firewall en la red privada permitan este tráfico, garantizando un *handshake* exitoso.

### 2. Errores de Enrutamiento en Traefik (404 Not Found)
* **El Problema:** Los servicios nuevos no son detectados por el proxy reverso, usualmente por falta de red compartida o etiquetas incorrectas.
* **Solución Orion:** Se automatiza la creación de una red *overlay* global (`public_proxy`). Los roles de despliegue fuerzan la vinculación de cada servicio a esta red y aplican los *labels* dinámicos de Traefik de forma estandarizada, eliminando el error humano.

### 3. Persistencia y Permisos de Volúmenes
* **El Problema:** Contenedores que fallan al iniciar (`Exit 1`) porque no pueden escribir en las carpetas montadas del host (ej. Postgres o Portainer).
* **Solución Orion:** El rol `common` asegura la creación de las rutas de volúmenes en el sistema de archivos del host con los permisos (UID/GID) adecuados antes de que Docker intente levantar los servicios.

---

Para más ayuda, abre un *Issue* en el repositorio o consulta la documentación técnica en `/docs`.