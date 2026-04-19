Central Vars Demo Role

This role demonstrates consuming centralized vars.yml (shared_* credentials) without duplicating secrets in individual playbooks.

Usage:
- Include this role in a playbook to show how centralized vars are accessed via {{ shared_postgres_password }} and {{ shared_db_password }}.
