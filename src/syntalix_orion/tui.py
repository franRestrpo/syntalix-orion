"""
Módulo de re-exportación para compatibilidad con el punto de entrada legacy.

Este módulo existe únicamente para mantener la compatibilidad con el antiguo
punto de entrada que usaba `from tui import OrionTUI`. El código moderno
debe usar `from syntalix_orion.ui.app import OrionTUI` directamente.
"""

from syntalix_orion.ui.app import OrionTUI

__all__ = ["OrionTUI"]