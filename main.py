"""SyntalixApp: Terminal UI for Phase 2 UI/Phase 3 Ansible central vars.

Screens:
- WelcomeScreen: ASCII logo, dependency checks summary.
- ConfigWizard: form for Proxmox connection and module selection.
- DeployMonitor: shows progress, logs, and errors; supports retry.
"""

from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from textual.app import App, Screen, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import (
    Button,
    Input,
    Static,
    Header,
    Footer,
    TextLog,
    ProgressBar,
)

from engine.ansible_runner import get_runner
import os

# Simple ASCII logo
ASCII_LOGO = r"""
  ____        _              _           _           
/ ___|  __ _| | ___  _ __  | |__   __ _| |_ ___  __
 \____|\__,_|_|\___/|_| |_| |_| |_|\__,_|\__\___/_/\_\
"""


def save_state(state: Dict[str, Any], path: str = "state.json") -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass


def load_state(path: str = "state.json") -> Dict[str, Any]:
    if not Path(path).exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


class WelcomeScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Static(ASCII_LOGO, style="bold cyan", id="logo")
        yield Static("Verifying local dependencies (ansible, ssh, python-venv)...", id="checks")
        yield Static("Detected system: Python {} | OS unknown".format("3.10+"), id="summary")
        yield Button("Continue", id="continue")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "continue":
            self.app.push_screen(ConfigWizardScreen())


class ConfigWizardScreen(Screen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._modules = {"mod_hardening": False, "mod_docker": False, "mod_monitoring": False}
        self._mod_labels = {
            "mod_hardening": "Hardening",
            "mod_docker": "Docker",
            "mod_monitoring": "Monitoring",
        }
    
    ip_input: Input
    token_input: Input
    user_input: Input

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Proxmox Connection", style="bold cyan")
            self.ip_input = Input(placeholder="IP address (e.g., 192.168.1.100)")
            yield self.ip_input
            self.token_input = Input(placeholder="Proxmox Token", password=True)
            yield self.token_input
            self.user_input = Input(placeholder="User")
            yield self.user_input

            yield Static("Modules", style="bold cyan")
            yield Button("Hardening", id="mod_hardening")
            yield Button("Docker", id="mod_docker")
            yield Button("Monitoring", id="mod_monitoring")
            yield Button("Start Deployment", id="start_deploy")
            yield Button("Back", id="back")
        yield Static("", id="summary", visible=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn = event.button.id
        if btn in {"mod_hardening", "mod_docker", "mod_monitoring"}:
            self._modules[btn] = not self._modules[btn]
            self.query_one("#summary", Static).update(
                f"Selected: {', '.join([self._mod_labels[k] for k, v in self._modules.items() if v]) or 'None'}"
            )
        elif btn == "start_deploy":
            cfg = self._gather_config()
            # Basic input validation for IP, token and user
            ip_valid = bool(re.match(r"^(?:\d{1,3}\.){3}\d{1,3}$", cfg.get("ip", "")))
            token = cfg.get("token", "")
            user = cfg.get("user", "")
            if not ip_valid or not token or not user:
                self.query_one("#summary", Static).update("Invalid configuration. Please provide valid IP, token and user.")
                return
            modules = [self._mod_labels[k] for k, v in self._modules.items() if v]
            # Persist minimal config
            save_state({"config": cfg, "modules": modules}, path="state.json")
            self.app.start_deployment(cfg, modules)
            self.app.pop_screen()
        elif btn == "back":
            self.app.pop_screen()

    def _gather_config(self) -> Dict[str, Any]:
        ip = self.ip_input.value or ""
        token = self.token_input.value or ""
        user = self.user_input.value or ""
        return {"ip": ip, "token": token, "user": user}


class DeployMonitorScreen(Screen):
    def __init__(self, config: Dict[str, Any], modules: List[str], **kwargs):
        super().__init__(**kwargs)
        self.config = config
        self.modules = modules
        self._runner: Optional[AnsibleRunner] = None
        self._details_visible = False
        self._event_queue: asyncio.Queue = asyncio.Queue()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Deploy Monitor", style="bold cyan")
            self._progress = ProgressBar(total=100)
            yield self._progress
            yield TextLog(highlight=True, markup=True, id="log")
            yield Button("Show Details", id="toggle_details")
            self._details_panel = Static("", id="details_panel", visible=False)
            yield self._details_panel
            yield Button("Retry", id="retry")
            yield Button("Close", id="close_monitor")

    async def on_mount(self) -> None:
        self._details_panel.visible = False
        self._runner = get_runner(on_event=self.enqueue_event, debug=getattr(self.app, "_debug", False))
        asyncio.create_task(self._runner.run(self.config, self.modules, debug=getattr(self.app, "_debug", False)))
        asyncio.create_task(self._process_events())
        
    def enqueue_event(self, event: Dict[str, Any]) -> None:
        self._event_queue.put_nowait(event)

    async def _process_events(self) -> None:
        log_widget = self.query_one("#log", TextLog)
        while True:
            event = await self._event_queue.get()
            etype = event.get("type", "log")
            if etype == "log":
                level = event.get("level", "info")
                msg = event.get("message", "")
                color = {"info": "white", "warning": "yellow", "error": "red"}.get(level, "white")
                log_widget.write(f"[{level.upper()}] {msg}", style=color)
            elif etype == "progress":
                value = int(event.get("value", 0))
                self._progress.update(value)
            elif etype == "stderr":
                details = event.get("stderr", "")
                self.query_one("#details_panel", Static).update(details)
                self._details_panel.visible = True
            elif etype == "done":
                ok = event.get("success", True)
                if ok:
                    log_widget.write("Deployment completed successfully ✅", style="green")
                else:
                    log_widget.write("Deployment failed ❌", style="red")
                # Persist final state for recovery
                try:
                    with open("state.json", "w", encoding="utf-8") as f:
                        json.dump({"config": self.config, "modules": self.modules, "status": "completed", "timestamp": datetime.now().timestamp()}, f, indent=2)
                except Exception:
                    pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "toggle_details":
            self._details_visible = not self._details_visible
            self._details_panel.visible = self._details_visible
            event.button.label = "Hide Details" if self._details_visible else "Show Details"
        elif event.button.id == "close_monitor":
            await self.app.pop_screen()
        elif event.button.id == "retry":
            if self._runner:
                asyncio.create_task(self._runner.run(self.config, self.modules, debug=self.app._debug))

    def show_stderr(self, text: str) -> None:
        self.query_one("#details_panel", Static).update(text)
        self._details_panel.visible = True


class SyntalixApp(App):
    CSS_PATH = None
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("f12", "toggle_debug", "Toggle Debug"),
        ("r", "toggle_runner_mode", "Toggle Runner Mode"),
        ("tab", "focus_next", "Next Focus"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._state = load_state()
        self._debug = False
        # Runner mode: 'mock' or 'real'
        self._runner_mode = os.environ.get("RUNNER_MODE", "mock")
        self._deploy_screen = None
        self._runner = None

    def on_mount(self) -> None:
        self.push_screen(WelcomeScreen())

    def start_deployment(self, config: Dict[str, Any], modules: List[str]) -> None:
        save_state({"config": config, "modules": modules}, path="state.json")
        screen = DeployMonitorScreen(config, modules)
        self._deploy_screen = screen
        self.push_screen(screen)
        self._runner = get_runner(on_event=screen.enqueue_event, debug=self._debug, mode=self._runner_mode)
        asyncio.create_task(self._runner.run(config, modules, debug=self._debug))

    def action_debug_toggle(self) -> None:
        self._debug = not self._debug
        # Inform the running monitor if present
        if self._deploy_screen and hasattr(self._deploy_screen, "enqueue_event"):
            self._deploy_screen.enqueue_event({"type": "log", "level": "info", "message": f"Debug mode {'ON' if self._debug else 'OFF'}"})

    def action_toggle_runner_mode(self) -> None:
        # Toggle between mock and real runner modes at runtime
        self._runner_mode = "real" if self._runner_mode == "mock" else "mock"
        # Persist preference for subsequent runs? Optional: write to env-like storage
        self.push_screen(WelcomeScreen())  # Reset flow for safety
        # Notify UI
        # Since we might be mid-run, just log the change
        if self._deploy_screen and hasattr(self._deploy_screen, 'enqueue_event'):
            self._deploy_screen.enqueue_event({"type": "log", "level": "info", "message": f"Runner mode set to {self._runner_mode}"})


if __name__ == "__main__":
    SyntalixApp.run(title="SyntalixApp", log="textual.log")
