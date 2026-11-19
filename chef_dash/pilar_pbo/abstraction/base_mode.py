"""
PILAR PBO 1: ABSTRACTION (Abstract Game Mode)
Kerangka standar untuk mode tampilan dan interaksi permainan (Mode Restoran & Mode Dapur).
"""

from abc import ABC, abstractmethod


class AbstractGameMode(ABC):
    """Kelas abstrak untuk mode layar permainan."""

    @abstractmethod
    def handle_click(self, pos: tuple) -> None:
        """Menangani klik mouse/gestur pada mode aktif."""
        pass

    @abstractmethod
    def render_mode(self) -> None:
        """Me-render tampilan visual mode aktif."""
        pass
