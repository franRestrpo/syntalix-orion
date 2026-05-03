# Syntalix-Orion Agent Instructions

This repository is transitioning to a **V2 3-layer architecture**: Metadata (Python), TUI Planner (Textual), and Orchestration (Ansible). 

## Architecture & Source of Truth
- **`apps_metadata.py`** is the ONLY source of truth for the app catalog, RAM specs, and dependencies.
- The **Dependency Graph** must load `apps_metadata.py`, resolve transitive dependencies (detecting cycles), and emit a deterministic deployment plan.
- The Textual UI/Planner outputs a single master `vars.yml` (or `.env`). Ansible playbooks must consume this single source of truth.

## Crucial App Constraints & Secrets (DO NOT MISS)
- **Database passwords MUST be deduplicated:** `POSTGRES_PASSWORD` should only exist in the `postgres_pgvector` entry. Do not repeat or redefine DB passwords in dependent apps (Chatwoot, Odoo, Dify, etc.). Apps must consume the centrally generated global DB password.
- **Secret Generation:** Use `secrets.token_urlsafe()` for all generated credentials.
- **CRITICAL RULE FOR PASSWORDS (ENCRYPTED VS PLAINTEXT):** 
  - Applicative UI credentials and web-facing access keys MUST be encrypted (e.g., using `bcrypt`).
  - **Database passwords (Postgres, Redis, MongoDB, etc.) MUST ALWAYS be random secure plaintext.** NEVER encrypt or hash database passwords. Applications (like n8n, Authentik) need the raw plaintext password to pass it over the network protocol for DB authentication. Hashing a DB password will immediately crash the dependent services (connection failed / NOAUTH).
- **RAM Limits:** The engine MUST sum the total RAM required (selected app + dependencies) and emit a critical warning if the plan exceeds the server threshold (e.g., 8 GB).
- **Networking:** Do NOT expose HTTP app ports directly to the host. All web apps must remain behind **Traefik** using dynamic Docker labels for TLS and security policies.

## Hardcoded Application Dependencies
- **Flowise** and **ActivePieces**: Must depend on `Postgres_pgvector` and `Redis`. They cannot run without persistent storage.
- **Evolution API**: Must include `MongoDB` as a mandatory dependency.
- **Chatwoot**: Must declare `RabbitMQ` as a mandatory dependency (not just Redis).

## Testing Commands
- The CI runs two test suites:
  1. `python -m unittest discover -v` (for tests in the root `tests/` directory)
  2. `pytest` for the newer modules.
- To run the modern tests:
  ```bash
  cd Orion-Python-Ansible/scripts
  pytest
  # Or run specific tests: pytest tests/test_security.py
  ```
- Important fixtures are available in `Orion-Python-Ansible/scripts/tests/conftest.py` (e.g., `sample_metadata`).

## Execution & TUI
- `main.py` is the main entrypoint for the V2 Textual TUI (`SyntalixApp`). 
- When working on the TUI deployment monitor, use the `RUNNER_MODE=mock` environment variable (or toggle via the UI) to test the UI flow without executing real Ansible playbooks.