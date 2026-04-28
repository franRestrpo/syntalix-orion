import os
import sys
import importlib.util

# Ensure repo root is in sys.path so that apps_metadata.py is importable
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

# Load apps_metadata.py via importlib to avoid package path issues
md_path = os.path.join(repo_root, "apps_metadata.py")
spec = importlib.util.spec_from_file_location("apps_metadata", md_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)  # type: ignore

APP_METADATA = getattr(module, "APP_METADATA", {})


def test_postgres_password_defined_only_in_postgres_pgvector():
    defined_apps = [app for app, meta in APP_METADATA.items() if "POSTGRES_PASSWORD" in meta.get("variables", {})]
    assert defined_apps == ["postgres_pgvector"], f"POSTGRES_PASSWORD debe definirse solo en postgres_pgvector, encontrado en: {defined_apps}"


def test_rabbitmq_dependency_in_chatwoot():
    assert "chatwoot" in APP_METADATA, "Chatwoot debe existir en el catálogo"
    deps = APP_METADATA["chatwoot"].get("dependencies", [])
    assert "rabbitmq" in deps, f"Chatwoot debe depender de RabbitMQ. Dependencias actuales: {deps}"


def test_mongodb_dependency_in_evolution_api():
    assert "evolution_api" in APP_METADATA, "Evolution API debe existir en el catálogo"
    deps = APP_METADATA["evolution_api"].get("dependencies", [])
    assert "mongodb" in deps, f Evolution API debe depender de MongoDB. Dependencias actuales: {deps}"
