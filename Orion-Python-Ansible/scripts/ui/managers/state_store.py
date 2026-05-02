from dataclasses import dataclass, field
from typing import Dict, List, Set, Any, Optional

@dataclass
class DeploymentPlan:
    plan: List[str] = field(default_factory=list)
    ram_total_mb: int = 0
    vars_generated: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    has_warning: bool = False
    warning_message: Optional[str] = None

@dataclass
class StateStore:
    """Gestor de estado centralizado para la TUI."""
    selected_apps: Set[str] = field(default_factory=set)
    user_variables: Dict[str, str] = field(default_factory=dict)
    deployment_plan: Optional[DeploymentPlan] = None
    
    def clear_selections(self):
        self.selected_apps.clear()
        
    def add_app(self, app_id: str):
        self.selected_apps.add(app_id)
        
    def remove_app(self, app_id: str):
        self.selected_apps.discard(app_id)
