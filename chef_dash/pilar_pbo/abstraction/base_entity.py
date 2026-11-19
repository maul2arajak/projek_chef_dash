"""
PILAR PBO 1: ABSTRACTION (Abstract Animated Entity)
Kerangka dasar standar untuk setiap entitas/karakter yang memiliki posisi, arah (depan, belakang, kiri, kanan),
dan animasi berjalan 5-frame (0, 1, 2, 3, 4).
"""

from abc import ABC, abstractmethod


class AbstractAnimatedEntity(ABC):
    """
    Kelas abstrak (Abstract Class) untuk semua entitas karakter di Chef Dash.
    Menyembunyikan detail manajemen sprite dan memaksa subclass mengimplementasikan
    method `step()`, `get_sprite_key()`, dan `render()`.
    """

    DIRECTIONS = ("depan", "belakang", "kiri", "kanan")
    TOTAL_FRAMES = 5

    @abstractmethod
    def step(self, dt: float, speed: float) -> bool:
        """Memperbarui posisi dan frame animasi 5-frame entitas setiap delta-time (dt)."""
        pass

    @abstractmethod
    def get_sprite_key(self) -> tuple:
        """Mengembalikan kunci aset sprite (folder_karakter, nama_arah, indeks_frame)."""
        pass

    @abstractmethod
    def render(self, surface, asset_manager, **kwargs) -> int:
        """Me-render sprite karakter ke layar Pygame dan mengembalikan koordinat Y atas kepala."""
        pass
