## Migration V2

### Summary
- Phase 2: UI Textual prototype for deployment management.
- Phase 3: Centralized Ansible vars.yml scaffold to start consuming a single source of truth for credentials and dependencies.
- Branch: pr/v2-migration (contains Phase 2/3 changes).

### Changes
- Added UI textual prototype: `ui/textual_prototype/app.py`.
- Added centralized Ansible vars: `group_vars/all/vars.yml`.
- Opened PR branch ready for final PR body content.

### Rationale
- Establish a concrete base for UI-driven deployment workflows and a centralized configuration model to eliminate secret duplication.
- Enable incremental, safe changes that won’t disrupt existing deployments while enabling Phase 2/3 follow-ups.

### Testing & Validation
- UI prototype: run `python ui/textual_prototype/app.py` (requires Textual).
- Ansible: review `group_vars/all/vars.yml` structure and verify roles read from centralized vars.

### Notes
- This PR focuses on scaffolding. Future commits will flesh out UI interactions and complete the Ansible refactor with tests and CI checks.

### Checklist (PR Review)
- [ ] UI: Verify Welcome, ConfigWizard, and DeployMonitor flow works and keyboard navigation is intuitive.
- [ ] Runner: Ensure mock runner is available as fallback; plan for real ansible-runner integration.
- [ ] Graph: Wire mock dependency graph to UI; plan to integrate real graph with cycles detection.
- [ ] Tests: Unit tests for DependencyGraph; UI flow smoke tests; runner event tests.
- [ ] Security: Centralized secrets; ensure no secrets logged; plan Vault integration.
- [ ] Documentation: Update Phase 2/3 docs and migration notes.
- [ ] CI: Ensure tests and linters run in CI.
- [ ] State persistence: state.json supports resume and re-run.

### Notas de Migración (para usuarios que migren de YAML a la UI)
- Objetivo: migrar la edición YAML a una UI de terminal que guíe la configuración y despliegue.
- Pasos clave:
  1) Centralizar secrets y credenciales en vars.yml (group_vars/all) y usar referencias en Playbooks.
  2) Adaptar Playbooks para consumir extravars desde la UI, reduciendo edición manual de YAML.
  3) Añadir un grafo de dependencias para planificar despliegues y detectar ciclos.
  4) Proporcionar una ruta de reanudación con state.json que guarde configuración y progreso.
- Seguridad: evitar logs de secretos; usar vault/secret store para credenciales sensibles.
- Plan de rollback: si falla la integración real de ansible-runner, regresar al modo Mock y documentar una transición gradual.
