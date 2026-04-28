## PR: Migración a Syntalix-Orion v2 — Arquitectura en 3 Capas y DependencyGraph (Phase 1)

Resumen:
- Introducción de la Capa de Metadatos (apps_metadata.py) y la Capa de Lógica (DependencyGraph) para la V2.
- Actualización de documentación para describir la Migración Phase 1 y el plan de Phase 2 (UI Textual + Vars.yml).
- Ajustes en el catálogo de apps para consolidar dependencias y RAM; eliminación de duplicación de contraseñas DB en apps de Valor.

Cambios principales:
- Nueva Capa: apps_metadata.py con catálogo central de apps y dependencias:
  - Core: Traefik, CrowdSec, Authentik, Portainer
  - Data: Postgres_pgvector, MariaDB, MongoDB, Redis, Qdrant, MinIO, RabbitMQ, etc.
  - Monitoring: Prometheus, Grafana, Loki, Uptime Kuma
  - Apps de Valor: Dify, OpenWebUI, Flowise, n8n, ActivePieces, Chatwoot, Evolution API, Odoo, etc.
- Nueva Capa: DependencyGraph (dependency_graph.py) para resolver dependencias y generar vars.yml de forma automatizada.
- Actualización de AGENTS.md con pautas y ejemplos prácticos de DependencyGraph (ahora con escenarios de prueba).
- Documentación añadida: docs/V2_ARCHITECTURE.md, PHASE2_MIGRATION.md, PR_V2_Migration_Body.md para facilitar revisión y pruebas.

Plan de validación y pruebas (Phase 1):
- Verificación de dependencias: asegurar que para una app dada, las dependencias se resuelven en orden correcto (depósitos antes de dependientes).
- RAM plan: validar que total_ram_for_plan(app) da un valor razonable y no excede el umbral configurado.
- Generación de vars: generar vars.yml maestro para un plan concreto y validar estructura (clave-app__variable).
- Seguridad: validar que POSTGRES_PASSWORD está centralizado en postgres_pgvector y que no hay duplicación en otros apps.

Cómo ejecutar/Probar (manual):
- Cargar DependencyGraph y pedir plan para una app (p. ej. dify):
  - from Orion-Python-Ansible.scripts.core.dependency_graph import DependencyGraph
  - dg = DependencyGraph()
  - plan = dg.resolve_dependencies('dify')
- Ver RAM y generar vars:
  - info = dg.plan_with_vars('dify')
  - info['ram_mb_total'], info['vars']

Notas de implementación:
- Este PR sienta las bases para Phase 2 (UI Textual + Vars.yml) y Phase 3 (refactor de Ansible en roles).
