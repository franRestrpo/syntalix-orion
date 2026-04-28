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
