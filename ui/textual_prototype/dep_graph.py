"""Lightweight in-memory Dependency Graph for UI prototype."""

from typing import List, Dict


class DependencyGraph:
    def __init__(self):
        # Simple mock graph with deterministic order
        self._deployments: List[Dict] = [
            {"name": "Core", "dependencies": []},
            {"name": "Data", "dependencies": ["Core"]},
            {"name": "Monitoring", "dependencies": ["Core", "Data"]},
            {"name": "Apps", "dependencies": ["Core", "Data", "Monitoring"]},
        ]

    def get_deployments(self) -> List[Dict]:
        return self._deployments

    def get_plan(self, name: str) -> str:
        dep_map = {d["name"]: d["dependencies"] for d in self._deployments}
        deps = dep_map.get(name, [])
        lines = [f"Deployment Plan for {name}:","- Validate dependencies and resources"]
        if deps:
            lines.append(f"- Dependencies: {', '.join(deps)}")
        lines += ["- Prepare environment and config","- Deploy components in order: Core, Data, Monitoring, Apps","- Run health checks and validation"]
        return "\n".join(lines)
