"""
Komponen bersama BFS & DFS (sesuai slide "Pencarian BFS dan DFS").

Ruang keadaan (state space) dirumuskan Sigma = <S, P, I, G, W>:
    S = himpunan state, P = operator (arc pada graf), I = state awal,
    G = tes tujuan, W = bobot/biaya tiap arc (di sini STEP_COST = 1).
Graf: node = state, arc = operator.

BFS dan DFS memakai kerangka yang sama (Open, Closed, Child); bedanya hanya
struktur data Open:  BFS = Queue (FIFO)   |   DFS = Stack (LIFO).
"""



STEP_COST = 1            # W : biaya satu operator


def cost(a):
    """W: biaya satu operator."""
    return STEP_COST


def build_path(parent, goal):
    path, cur = [], goal
    while parent[cur] is not None:
        prev, a = parent[cur]
        path.append(a)
        cur = prev
    path.reverse()
    return path


def build_states(parent, goal):
    """Urutan state dari awal sampai tujuan (dipakai untuk rute grid)."""
    states, cur = [goal], goal
    while parent[cur] is not None:
        cur = parent[cur][0]
        states.append(cur)
    states.reverse()
    return states


def node_label(n):
    """0->A, 1->B, ... 25->Z, 26->AA (label node seperti huruf pada slide)."""
    n += 1
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


class Tracer:
    """Merekam isi Open & Closed pada tiap iterasi (untuk tampilan trace)."""

    def __init__(self, record):
        self.record = record
        self.labels = {}      # state -> huruf, urut saat pertama kali dihasilkan
        self.trace = []

    def lab(self, s):
        if s not in self.labels:
            self.labels[s] = node_label(len(self.labels))
        return self.labels[s]

    def note_generated(self, s):
        if self.record:
            self.lab(s)

    def snap(self, x, open_nodes, closed, goal=False):
        """open_nodes dalam urutan tampil (kiri = berikutnya diambil)."""
        if not self.record:
            return
        self.trace.append(dict(
            x=None if x is None else self.lab(x),
            open=[self.lab(s) for s in open_nodes],
            closed=[self.lab(s) for s in closed],
            goal=goal))


def hasil_pencarian(name, found, parent, goal, tr, st):
    path = build_path(parent, goal) if found else []
    return dict(
        name=name, found=found, path=path,
        states=build_states(parent, goal) if found else [],   # urutan node dari awal ke tujuan
        d=len(path),                                   # kedalaman solusi
        cost=sum(cost(a) for a in path),               # total W
        generated=st["generated"],                     # time complexity (slide)
        expanded=st["expanded"],
        max_open=st["max_open"],                       # space complexity (slide)
        b_max=st["b_max"],                             # b (faktor percabangan maks)
        b_avg=st["children"] / max(1, st["expanded"]),
        m=st["m"],                                     # kedalaman maks pohon pencarian
        trace=tr.trace,
        by_label={v: k for k, v in tr.labels.items()})
