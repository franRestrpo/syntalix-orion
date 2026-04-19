# Syntalix-Orion v2: Arquitectura por Capas

Visión general: Syntalix-Orion v2 transforma el despliegue en un asistente de soberanía digital estructurado en tres capas: Metadatos (fuente de verdad), Presentación/Lógica (TUI en Textual) y Orquestación (Ansible refactorizado).

1) Capa de Metadatos (Fuente de Verdad)
- Archivo: apps_metadata.py
- Contenido: catálogo de aplicaciones con dependencias y consumo de RAM (en MB).
- Regla: Postgres se expone como una única opción con PostgreSQL + pgvector integrados, usando la imagen pgvector y un init para CREAR EXTENSION vector.

2) Capa de Presentación y Lógica (Textual UI)
- Interfaz: Terminal UI con Textual.
- Lectura del catálogo de apps desde apps_metadata.py.
- Grafo de dependencias: al seleccionar una app se marcan automáticamente dependencias de infraestructura necesarias.
- Calculador de RAM en tiempo real: suma de RAM de los componentes del plan; si el total se aproxima o excede el límite del servidor, se emite alerta/advertencia crítica.
- Generación de archivos maestros: produce vars.yml (o .env) con credenciales generadas criptográficamente seguras y la configuración consolidada de variables de entorno.

3) Capa de Orquestación (Ansible Refactorizado)
- Estructura de Roles: core, data, monitoring, apps.
- El playbook maestro site.yml invoca roles basados exclusivamente en las variables de vars.yml generado por la TUI.

Notas y beneficios:
- Seguridad: contraseñas generadas con secrets.token_urlsafe; evita credenciales débiles.
- Enrutamiento: todas las apps quedan behind Traefik con etiquetas dinámicas para TLS y seguridad.
- No monolito: cada app genera su propio env y stack gestionado por Ansible, evitando docker-compose masivo.
- Interoperabilidad: reglas para evitar exponer puertos de apps HTTP directamente; todo pasa por el proxy.

Guía de migración y progreso:
- Fase 1: Implementación de Capa de Metadatos y DependencyGraph; groundwork para TUI.
- Fase 2: Implementación de Textual UI y generación de vars.yml; integración de grafo y RAM.
- Fase 3: Refactor de Ansible en Roles y site.yml; orquestación basada en vars.yml.
- Fase 4: Seguridad y monitoreo (Vault, Prometheus/Grafana, etc.).

Referencias:
- CONFIG_DEPLOY.md para la guía de despliegue de la V2.
- HARDENING.md para consideraciones de seguridad.
