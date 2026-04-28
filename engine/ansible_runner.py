"""Lightweight AnsibleRunner bridge for the Textual UI.

- In Phase 2 this is a mock, emitting structured events to drive the UI.
- In Phase 3+ it should be replaced with a real integration to ansible-runner.
"""

import asyncio
import random
from typing import Any, Callable, Dict, Optional

EventCallback = Callable[[Dict[str, Any]], None]


class AnsibleRunner:
    def __init__(self, on_event: Optional[EventCallback] = None, debug: bool = False) -> None:
        self._on_event = on_event or (lambda e: None)
        self._debug = bool(debug)

    async def run(self, config: Dict[str, Any], modules: list[str], debug: bool | None = None) -> None:
        if debug is not None:
            self._debug = bool(debug)

        total_steps = 4
        steps = [
            "Inventory & Preparation",
            "Connection Checks",
            "Running Playbooks",
            "Post-Deployment Validation",
        ]

        self._emit({"type": "log", "level": "info", "message": "Deployment started"})
        if self._debug:
            self._emit({"type": "log", "level": "debug", "message": "Debug mode enabled"})
            self._emit({"type": "log", "level": "debug", "message": f"Config: {config}"})
            self._emit({"type": "log", "level": "debug", "message": f"Modules: {modules}"})

        for i, step in enumerate(steps, start=1):
            await asyncio.sleep(1.0)
            if random.random() < 0.1:
                self._emit({"type": "log", "level": "error", "message": f"Error during: {step}", "stderr": "Traceback (simulado): ..."})
                self._emit({"type": "done", "success": False})
                return

            self._emit({"type": "log", "level": "info", "message": f"{step} completed"})
            if self._debug:
                self._emit({"type": "log", "level": "debug", "message": f"Step {i}/{total_steps} finished"})
            self._emit({"type": "progress", "value": int((i / total_steps) * 100)})

        self._emit({"type": "log", "level": "info", "message": "Deployment completed successfully"})
        self._emit({"type": "done", "success": True})

    def _emit(self, event: Dict[str, Any]) -> None:
        try:
            self._on_event(event)
        except Exception:
            # Never crash the UI; log silently
            pass
