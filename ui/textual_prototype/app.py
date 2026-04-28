"""
Minimal Textual prototype to manage deployments.
Phase 2: UI Textual initial scaffold.
"""
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, ListView, ListItem
from textual.containers import Container, Horizontal
from textual import events
from .dep_graph import DependencyGraph


class DeploymentUI(App):
    """Very small prototype UI that will, in the real app, interact with DependencyGraph."""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            yield ListView(id="deployments")
            yield Static("Select a deployment using Up/Down or n/p. Press g to generate a plan.", id="detail_label")
        yield Static("", id="detail", expand=True)
        yield Footer()

    def on_mount(self) -> None:
        # Initialize a DependencyGraph and seed the UI with its deployments
        self.graph = DependencyGraph()
        self.deployments = self.graph.get_deployments()
        self.selected = 0
        # populate list
        list_view = self.query_one("#deployments", ListView)
        for d in self.deployments:
            list_view.append(ListItem(Static(f"{d['name']}")))
        self.render_detail()

    def render_detail(self) -> None:
        detail = self.query_one("#detail", Static)
        d = self.deployments[self.selected]
        details = d.get("dependencies", [])
        detail_text = (
            f"Selected: {d['name']}\n"
            f"Status: {d['status']}\n"
            f"Dependencies: {', '.join(details) if details else 'None'}"  # pulled from graph if present
        )
        detail.update(detail_text)

    def on_key(self, event: events.Key) -> None:
        # Basic navigation and action shortcuts
        if event.key in ("j", "down", "n"):
            self.selected = (self.selected + 1) % len(self.deployments)
            self.render_detail()
        elif event.key in ("k", "up", "p"):
            self.selected = (self.selected - 1) % len(self.deployments)
            self.render_detail()
        elif event.key == "g":
            self.generate_plan()

    def generate_plan(self) -> None:
        # Simple generated plan based on the selected deployment
        d = self.deployments[self.selected]
        plan = self.graph.get_plan(d["name"])
        detail = self.query_one("#detail", Static)
        detail.update(plan)



if __name__ == "__main__":
    DeploymentUI().run()
