"""DFS - Depth First Search (Open = Stack/LIFO) sesuai pseudocode slide, terintegrasi dengan Pilar Polimorfisme PBO."""

from pilar_pbo.polymorphism.search_polymorphism import DFSSearchStrategy, run_polymorphic_search

_dfs_strategy = DFSSearchStrategy()


def dfs(start, succ, goal, limit=None, record=True):
    """Depth First Search. Open = Stack (LIFO). Closed = list (prepend).
    limit = batas kedalaman (None = tanpa batas). Slide 8-puzzle memakai batas 5.
    succ/goal: operator & tes tujuan (dipakai grafik rute restoran oleh asisten antar)."""
    return run_polymorphic_search(_dfs_strategy, start, succ=succ, goal=goal, record=record, limit=limit)
