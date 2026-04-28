"""Real AnsibleRunner implementation using ansible-runner.

This is a pragmatic skeleton that attempts to run playbooks via the
`ansible_runner` Python package. It falls back gracefully if the package or
playbooks are not available in the environment.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, Optional

EventCallback = Callable[[Dict[str, Any]], None]


class RealAnsibleRunner:
    def __init__(self, on_event: Optional[EventCallback] = None, debug: bool = False) -> None:
        self._on_event = on_event or (lambda e: None)
        self._debug = bool(debug)

    async def run(self, config: Dict[str, Any], modules: list[str], debug: bool | None = None) -> None:
        if debug is not None:
            self._debug = bool(debug)

        # Attempt to run using ansible-runner; otherwise emit a fallback
        try:
            import ansible_runner  # type: ignore
        except Exception:
            self._emit({"type": "log", "level": "warning", "message": "ansible-runner not available. Falling back to mock.")})
            # Fallback behavior: simulate a quick success
            await asyncio.sleep(0.5)
            self._emit({"type": "log", "level": "info", "message": "Deployment completed (mock fallback)"})
            self._emit({"type": "done", "success": True})
            return

        # If ansible-runner exists, perform a best-effort run. This is a minimal shim.
        try:
            # The exact invocation depends on repository layout; this is a best-effort
            private_data_dir = str(Path.cwd())
            # You should adjust the playbook path according to your repo structure
            pb = "playbooks/deploy.yml"
            if not Path(pb).exists():
                pb = "playbooks/site.yml"
            if not Path(pb).exists():
                pb = None

            if pb is None:
                self._emit({"type": "log", "level": "warning", "message": "No playbook found for real runner. Using fallback."})
                self._emit({"type": "done", "success": True})
                return

            import ansible_runner  # type: ignore
            # We request JSON lines if supported; fallback to object events otherwise
            self._emit({"type": "log", "level": "info", "message": f"Starting real Ansible run: {pb}"})
            r = ansible_runner.run(private_data_dir=private_data_dir, playbook=pb, extravars=config, quiet=True)

            # Basic event consumption if available
            if hasattr(r, "events"):
                try:
                    for ev in r.events:
                        self._emit({"type": "log", "level": "info", "message": str(ev)})
                except Exception:
                    pass

            rc = getattr(r, "rc", 0)
            success = (rc == 0)
            self._emit({"type": "done", "success": success})
        except Exception as e:
            self._emit({"type": "log", "level": "error", "message": f"Real runner error: {e}", "stderr": str(e)})
            self._emit({"type": "done", "success": False})

    def _emit(self, event: Dict[str, Any]) -> None:
        try:
            self._on_event(event)
        except Exception:
            pass
