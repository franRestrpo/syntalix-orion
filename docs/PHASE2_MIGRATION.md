# Fase 2: UI Textual + Vars.yml y flow de migración

Objetivo: Completar la capa de Presentación y Orquestación para la V2 usando una UI Textual (Textual) que genere un archivo maestro vars.yml y orqueste despliegues con Ansible.

Estructura de la migración:
- 2.1 UI Textual (Textual):
  - Cargar apps_metadata desde apps_metadata.py.
  - Construir el Grafo de Dependencias para la app seleccionada y sus dependencias.
  - Calcular RAM total en tiempo real y emitir advertencias si excede el umbral (ej., 8 GB).
  - Generar vars.yml maestro con credenciales criptográficas y claves de DB compartidas. Compartir la contraseña de POSTGRES_PASSWORD centralizada entre apps que la necesiten (p.ej., postgres_pgvector) y eliminar duplicación de passwords en otras apps.
  - Exportar el plan de despliegue (orden de despliegue) para el playbook de Ansible.

- 2.2 Estructura de vars.yml maestro:
  - Contendrá claves por app, p. ej. postgres_pgvector_POSTGRES_PASSWORD, chatwoot_SECRET_KEY_BASE, etc., consolidando contraseñas y credenciales generadas.

- 2.3 Requisitos de seguridad:
  - Secretos generados con secrets.token_urlsafe.
  - No incluir passwords en texto plano en código fuente; el repo debe contener solo los secretos generados en vars.yml en despliegue seguro.

- 2.4 Integración con Ansible (site.yml):
  - site.yml debe leer vars.yml para decidir qué roles/tareas ejecutar (core, data, monitoring, apps).

- 2.5 Pruebas/Verificación:
  - Pruebas unitarias para DependencyGraph y apps_metadata (casos de dependencias simples, transversales, ciclos).
  - Pruebas de generación de vars.yml con escenarios simples (p. ej., dify, chatwoot).

## Checklist de migración (alto nivel)
- [ ] UI Textual implementada y consumiendo apps_metadata.py
- [ ] Grafo de dependencias funcional y RAM calculada
- [ ] Generación de vars.yml maestro y pruebas básicas
- [ ] Refactor de Ansible en roles y sitio de despliegue para consumir vars.yml
- [ ] Pruebas locales (pytest) y verificación de RAM
- [ ] Documentación actualizada (CONFIG_DEPLOY.md/HARDENING)

Notas finales: Esta fase sienta las bases para una migración limpia hacia la V2 con UI interactiva y orquestación basada en variables centralizadas. Propondré parches de integración incrementales para evitar rupturas de servicio.
