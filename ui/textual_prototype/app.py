"""
Minimal Textual prototype to manage deployments.
Phase 2: UI Textual initial scaffold.
"""
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, ListView
from textual.containers import Container


class DeploymentUI(App):
    """Very small prototype UI that will, in the real app, interact with DependencyGraph."""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Container(
            Static("Deployment Studio — Phase 2 Prototype", id="title"),
            ListView([], id="deployments"),
        )
        yield Footer()

    def on_mount(self) -> None:
        # TODO: integrate with DependencyGraph to load deployments dynamically
        pass


if __name__ == "__main__":
    DeploymentUI().run()
