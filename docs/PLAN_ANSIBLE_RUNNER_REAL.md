Plan: Replacing mock AnsibleRunner with real ansible-runner

Overview
- Objective: swap the mock runner used by Phase 2 UI with a real integration using the Python package ansible-runner.
- Outcome: streaming of playbook events (progress, per-task logs), robust error handling, and a safe fallback.

Assumptions
- ansible-runner package is installed in the execution environment.
- Playbooks and inventories are organized in the repo (e.g., playbooks/deploy.yml, inventory/hosts).
- Secrets management is centralized (group_vars/all/vars.yml) or Vault; no secrets are logged.
- The UI communicates with the runner via a defined callback API (on_event(event)).

Milestones
1) Interface contract and baseline (1 week)
- Define event contract: type (log, progress, stderr, done), level, message, progress, stderr, done, success.
- Implement a wrapper in engine/ansible_runner.py that can delegate to RealAnsibleRunner when enabled.
- Add configuration flag (ENV or app setting) to switch between Mock and Real runner.

2) Real runner integration scaffolding (2 weeks)
- Implement engine/ansible_runner_real.py using ansible_runner.run with private_data_dir, inventory, and playbook.
- Hydrate inputs from UI (config, modules) to extravars and inventory handling.
- Emit events: per-task logs if supported, progress updates, and done with success/failure.

3) Event streaming and UI adaptation (2 weeks)
- Adapt main UI to handle streaming events from RealRunner (progress updates, log lines, stderr extraction).
- Add a debug mode to stream raw ansible-runner events when needed (toggle via UI or a hotkey).
- Ensure error handling surfaces actionable details (including SSH/Networking errors).

4) Tests (2 weeks)
- Unit tests for RealAnsibleRunner: success path, failure path, exception handling.
- Integration tests for the flow: UI -> runner -> events -> UI updates.
- Regression tests to ensure mock path remains working if real runner is unavailable.

5) CI and docs (1 week)
- CI jobs to install ansible-runner and run minimal tests.
- Documentation: how to enable real runner, prerequisites, and troubleshooting.

Design considerations
- Safety: if ansible-runner is unavailable, gracefully fall back to mock to avoid breaking deployments.
- Observability: provide a verbose debug mode to help troubleshooting quickly.
- Security: ensure secrets are never logged; provide a vault-based secret store integration plan.

Acceptance criteria
- Real runner can be enabled via config and emits events that UI consumes.
- UI shows per-task levels, progress, and stderr details on failure.
- Tests exist for both mock and real runner paths and the transition path is covered.

Notes
- This plan is a staged approach to minimize risk and maintain current deployments while enabling real runner integration.
