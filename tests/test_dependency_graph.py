import os
import sys
import importlib.util

# Ensure repo root is in sys.path so that apps_metadata.py and the graph can be loaded
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

# Load the DependencyGraph module via path to avoid package path issues
dep_graph_path = os.path.join(repo_root, "Orion-Python-Ansible", "scripts", "core", "dependency_graph.py")
spec = importlib.util.spec_from_file_location("dep_graph", dep_graph_path)
dep_graph = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dep_graph)  # type: ignore
DependencyGraph = getattr(dep_graph, "DependencyGraph")
dg = DependencyGraph()


def test_resolve_dependencies_order_for_dify():
    plan = dg.resolve_dependencies("dify")
    # Ensure core dependencies come before dify
    assert plan.index("postgres_pgvector") < plan.index("dify"), plan
    assert plan.index("redis") < plan.index("dify"), plan


def test_total_ram_plan_non_negative():
    ram = dg.total_ram_for_plan("dify")
    assert isinstance(ram, int) and ram > 0


def test_plan_with_vars_structure():
    result = dg.plan_with_vars("dify")
    assert isinstance(result, dict)
    assert "plan" in result
    assert "ram_mb_total" in result
    assert "vars" in result
