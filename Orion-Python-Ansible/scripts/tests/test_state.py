"""Tests para el módulo de estado (state.py)."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.state import save_state, load_state, save_env_file, load_env_file


class TestSaveLoadState:
    """Tests para save_state y load_state."""

    def test_save_and_load_state(self, temp_dir):
        """Test guardar y cargar estado."""
        state_data = {
            "selected_apps": ["traefik", "postgres"],
            "config": {"domain": "example.com"}
        }
        state_file = temp_dir / "state.json"

        save_state(state_data, str(state_file))
        loaded = load_state(str(state_file))

        assert loaded == state_data

    def test_load_nonexistent_file(self, temp_dir):
        """Test cargar archivo inexistente."""
        result = load_state(str(temp_dir / "nonexistent.json"))
        assert result == {}


class TestEnvFiles:
    """Tests para archivos .env."""

    def test_save_and_load_env_file(self, temp_dir):
        """Test guardar y cargar archivo .env."""
        variables = {
            "POSTGRES_PASSWORD": "secret123",
            "TRAEFIK_DOMAIN": "example.com"
        }
        env_file = temp_dir / "test.env"

        save_env_file(str(env_file), variables)
        loaded = load_env_file(str(env_file))

        assert loaded["POSTGRES_PASSWORD"] == "secret123"
        assert loaded["TRAEFIK_DOMAIN"] == "example.com"

    def test_load_nonexistent_env_file(self, temp_dir):
        """Test cargar archivo .env inexistente."""
        result = load_env_file(str(temp_dir / "nonexistent.env"))
        assert result == {}

    def test_env_file_with_comments(self, temp_dir):
        """Test archivo .env con comentarios."""
        env_file = temp_dir / "comments.env"
        env_file.write_text("# Comment\nKEY=value\n# Another comment\n")

        loaded = load_env_file(str(env_file))
        assert "KEY" in loaded
        assert loaded["KEY"] == "value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])