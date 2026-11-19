"""
PILAR PBO 1: ABSTRACTION (Abstract Search Algorithm)
Kerangka kerja standar untuk algoritma pencarian ruang keadaan Sigma = <S, P, I, G, W>.
"""

from abc import ABC, abstractmethod


class AbstractSearchAlgorithm(ABC):
    """
    Interface / Abstract Class untuk algoritma pencarian blind search (BFS & DFS).
    Setiap algoritma turunan wajib mengimplementasikan `algorithm_name()` dan `search()`.
    """

    @abstractmethod
    def algorithm_name(self) -> str:
        """Nama algoritma pencarian (misal: 'BFS' atau 'DFS')."""
        pass

    @abstractmethod
    def open_structure_label(self) -> str:
        """Deskripsi struktur data Open (misal: 'Queue (FIFO)' atau 'Stack (LIFO)')."""
        pass

    @abstractmethod
    def search(self, start, succ, goal, record: bool = True, **kwargs) -> dict:
        """
        Menjalankan algoritma pencarian dari state `start` menggunakan fungsi `succ` dan tes `goal`.
        Mengembalikan dictionary hasil lengkap beserta trace Open dan Closed.
        """
        pass
