"""
PILAR PBO 4: POLYMORPHISM (Polymorphic Search Strategy: BFS vs DFS)
Mengimplementasikan kontrak `AbstractSearchAlgorithm` dengan perilaku berbeda pada method `search()`:
- `BFSSearchStrategy`: menggunakan Queue (FIFO) -> menghasilkan jalur/resep terpendek (optimal).
- `DFSSearchStrategy`: menggunakan Stack (LIFO) -> menelusuri cabang mendalam terlebih dahulu.
"""

from collections import deque
from pilar_pbo.abstraction.base_algorithm import AbstractSearchAlgorithm
from algoritma.dasar import Tracer, hasil_pencarian


class BFSSearchStrategy(AbstractSearchAlgorithm):
    """Implementasi Polimorfik Breadth-First Search (Open = Queue / FIFO)."""

    def algorithm_name(self) -> str:
        return "BFS"

    def open_structure_label(self) -> str:
        return "Queue (FIFO)"

    def search(self, start, succ, goal, record: bool = True, **kwargs) -> dict:
        tr = Tracer(record)
        tr.note_generated(start)
        open_q, in_open = deque([start]), {start}
        closed, closed_set = [], set()
        parent, depth = {start: None}, {start: 0}
        st = dict(generated=1, expanded=0, max_open=1, b_max=0, children=0, m=0)
        tr.snap(None, open_q, closed)
        while open_q:
            x = open_q.popleft()                           # DeQueue(Open) - FIFO
            in_open.discard(x)
            if goal(x):                                    # Goal(x)? -> return x
                tr.snap(x, open_q, closed, goal=True)
                return hasil_pencarian(self.algorithm_name(), True, parent, x, tr, st)
            closed.insert(0, x)                            # Insert(x, Closed)
            closed_set.add(x)
            st["expanded"] += 1
            kids = list(succ(x))                           # Child(x, Sigma)
            st["children"] += len(kids)
            st["b_max"] = max(st["b_max"], len(kids))
            for a, y in kids:
                if y not in closed_set and y not in in_open:
                    parent[y] = (x, a)
                    depth[y] = depth[x] + 1
                    st["m"] = max(st["m"], depth[y])
                    tr.note_generated(y)
                    open_q.append(y)                       # EnQueue(y, Open)
                    in_open.add(y)
                    st["generated"] += 1
            st["max_open"] = max(st["max_open"], len(open_q))
            tr.snap(x, open_q, closed)
        return hasil_pencarian(self.algorithm_name(), False, parent, start, tr, st)


class DFSSearchStrategy(AbstractSearchAlgorithm):
    """Implementasi Polimorfik Depth-First Search (Open = Stack / LIFO)."""

    def algorithm_name(self) -> str:
        return "DFS"

    def open_structure_label(self) -> str:
        return "Stack (LIFO)"

    def search(self, start, succ, goal, record: bool = True, **kwargs) -> dict:
        limit = kwargs.get("limit", None)
        tr = Tracer(record)
        tr.note_generated(start)
        stack, in_open = [start], {start}
        closed, closed_set = [], set()
        parent, depth = {start: None}, {start: 0}
        st = dict(generated=1, expanded=0, max_open=1, b_max=0, children=0, m=0)
        tr.snap(None, reversed(stack), closed)             # puncak stack di kiri
        while stack:
            x = stack.pop()                                # Pop(Open) - LIFO
            in_open.discard(x)
            if goal(x):
                tr.snap(x, reversed(stack), closed, goal=True)
                return hasil_pencarian(self.algorithm_name(), True, parent, x, tr, st)
            closed.insert(0, x)
            closed_set.add(x)
            st["expanded"] += 1
            kids = list(succ(x))
            st["children"] += len(kids)
            st["b_max"] = max(st["b_max"], len(kids))
            if limit is not None and depth[x] >= limit:
                kids = []                                  # sudah di batas kedalaman
            # Beri label anak KIRI -> KANAN dulu supaya trace sama persis dengan slide
            for a, y in kids:
                tr.note_generated(y)
            # Reversed: anak pertama ditaruh paling atas stack (sesuai trace slide)
            for a, y in reversed(kids):
                if y not in closed_set and y not in in_open:
                    parent[y] = (x, a)
                    depth[y] = depth[x] + 1
                    st["m"] = max(st["m"], depth[y])
                    stack.append(y)                        # Push(y, Open)
                    in_open.add(y)
                    st["generated"] += 1
            st["max_open"] = max(st["max_open"], len(stack))
            tr.snap(x, reversed(stack), closed)
        return hasil_pencarian(self.algorithm_name(), False, parent, start, tr, st)


def run_polymorphic_search(strategy: AbstractSearchAlgorithm, start, succ, goal, record: bool = True, **kwargs) -> dict:
    """
    Fungsi Polimorfik: menerima objek turunan `AbstractSearchAlgorithm` apapun (`BFSSearchStrategy` atau
    `DFSSearchStrategy`) dan memanggil satu nama method yang sama `strategy.search(...)`.
    """
    return strategy.search(start, succ=succ, goal=goal, record=record, **kwargs)
