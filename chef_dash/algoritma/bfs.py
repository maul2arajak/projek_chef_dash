"""BFS - Breadth First Search (Open = Queue/FIFO) sesuai pseudocode slide, terintegrasi dengan Pilar Polimorfisme PBO."""

from pilar_pbo.polymorphism.search_polymorphism import BFSSearchStrategy, run_polymorphic_search

_bfs_strategy = BFSSearchStrategy()


def bfs(start, succ, goal, record=True):
    """Breadth First Search (slide): Open = Queue (FIFO), Closed = list (disisipkan di depan).

    succ(x) -> iterable (operator, anak) = Child(x, Sigma); goal(x) -> bool = Goal(x, Sigma).
    Mengembalikan dict hasil (path, states, d, cost, generated, expanded, max_open, b, m, trace)."""
    return run_polymorphic_search(_bfs_strategy, start, succ=succ, goal=goal, record=record)
