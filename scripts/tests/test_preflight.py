"""Tests para el módulo de preflight (verificaciones del sistema)."""

import pytest
from pathlib import Path

from core.preflight import (
    get_platform,
    cmd_exists,
)


class TestPlatformDetection:
    """Tests para detección de plataforma."""

    def test_get_platform_returns_valid(self):
        """Test que get_platform retorna un valor válido."""
        platform = get_platform()
        assert platform in ("linux", "windows", "darwin", "unknown")

    def test_cmd_exists_basic(self):
        """Test que cmd_exists funciona con comandos básicos."""
        assert cmd_exists("python") or cmd_exists("python3") or cmd_exists("py")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])