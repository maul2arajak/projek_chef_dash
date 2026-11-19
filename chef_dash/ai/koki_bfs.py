"""
AI KOKI (BFS) - ruang keadaan memasak nasi goreng + pencarian resep terpendek.
"""

from collections import namedtuple

from algoritma.bfs import bfs
from core.config import BLUE, PURPLE, RED

# ====================================================================
# STATE SPACE & PENCARIAN  (BFS / DFS sesuai slide)
#
# Rumusan formal ruang keadaan (slide):  Sigma = <S, P, I, G, W>
#   S = himpunan state    : semua tuple (beras, bawang, telur, garam, kecap, piring)
#   P = himpunan operator : daftar ACTIONS (tiap aksi = satu arc pada graf)
#   I = state awal        : START
#   G = state tujuan      : is_goal(s)  ->  piring sudah disajikan
#   W = bobot/biaya arc   : STEP_COST = 1 untuk setiap aksi
# Graf: node = state, arc = operator.
# ====================================================================
BERAS, BAWANG, TELUR, GARAM, KECAP, PIRING = range(6)
START = (0, 0, 0, 0, 0, 0)                      # I

# Potongan bayaran koki AI per langkah di atas resep terpendek (hasil BFS).
AI_STEP_PENALTY = 5

STAGES = {
    BERAS: ["Mentah", "Dicuci", "Nasi matang", "Nasi goreng"],
    BAWANG: ["Utuh", "Diiris", "Ditumis"],
    TELUR: ["Mentah", "Dikocok", "Didadar"],
    GARAM: ["Belum", "Sudah"],
    KECAP: ["Belum", "Sudah"],
    PIRING: ["Kosong", "Disajikan"],
}
NAMES = {BERAS: "Beras", BAWANG: "Bawang", TELUR: "Telur",
         GARAM: "Garam", KECAP: "Kecap manis", PIRING: "Piring"}
ICON_COL = {BERAS: (222, 196, 140), BAWANG: (170, 110, 190), TELUR: (245, 190, 60),
            GARAM: (200, 200, 205), KECAP: (90, 55, 40), PIRING: (120, 180, 230)}

Action = namedtuple("Action", "label idx need new extra why color")
C_BASIC, C_SEASON, C_FINAL, C_SHORT = (214, 150, 80), (230, 180, 60), (70, 170, 100), (110, 140, 190)

# Urutan list = urutan operator yang dicoba BFS/DFS.
ACTIONS = [
    Action("Tambah Garam", GARAM, 0, 1, None, "Garam sudah ditambahkan!", C_SEASON),
    Action("Tambah Kecap", KECAP, 0, 1, None, "Kecap sudah ditambahkan!", C_SEASON),
    Action("Kocok Telur", TELUR, 0, 1, None, "Telur sudah dikocok!", C_BASIC),
    Action("Dadar Telur", TELUR, 1, 2, None, "Telur harus dikocok dulu!", C_BASIC),
    Action("Iris Bawang", BAWANG, 0, 1, None, "Bawang sudah diiris!", C_BASIC),
    Action("Tumis Bawang", BAWANG, 1, 2, None, "Bawang harus diiris dulu!", C_BASIC),
    Action("Cuci Beras", BERAS, 0, 1, None, "Beras sudah dicuci!", C_BASIC),
    Action("Masak Nasi", BERAS, 1, 2, None, "Beras harus dicuci dulu!", C_BASIC),
    Action("Goreng Nasi", BERAS, 2, 3,
           lambda s, o: s[BAWANG] == 2 and s[TELUR] == (2 if o["egg"] else 0),
           "Nasi, bawang & telur harus siap sesuai pesanan!", C_FINAL),
    Action("Sajikan", PIRING, 0, 1,
           lambda s, o: s[BERAS] == 3 and s[GARAM] == 1 and s[KECAP] == (1 if o["kecap"] else 0),
           "Nasi goreng belum jadi / bumbu belum sesuai!", C_FINAL),
    Action("Nasi Sisa", BERAS, 0, 2, None, "Beras sudah diproses!", C_SHORT),
    Action("Bumbu Instan", BAWANG, 0, 2, None, "Bawang sudah diproses!", C_SHORT),
]
DISPLAY_ORDER = [6, 7, 4, 5, 2, 3, 0, 1, 8, 9, 10, 11]


def apply_action(s, a, o):
    act = ACTIONS[a]
    if s[act.idx] != act.need:
        return None
    if act.extra and not act.extra(s, o):
        return None
    lst = list(s)
    lst[act.idx] = act.new
    return tuple(lst)


def successors(s, o):
    for a in range(len(ACTIONS)):
        n = apply_action(s, a, o)
        if n is not None:
            yield a, n


def is_goal(s):
    return s[PIRING] == 1


def describe(s):
    """Deskripsi state untuk tampilan trace."""
    return ", ".join(f"{NAMES[i]}: {STAGES[i][s[i]]}" for i in range(6))


def bfs_masak(start, order=None, record=True):
    """BFS pada ruang keadaan memasak (Open = Queue/FIFO) -> resep terpendek."""
    return bfs(start, succ=lambda s: successors(s, order), goal=is_goal, record=record)


class KokiAI:
    """AI KOKI di dapur: memasak otomatis dengan resep terpendek hasil BFS."""

    def run_ai(self, name):
        if name != "BFS":
            self.say("DFS dipakai ASISTEN ANTAR di restoran (tombol AI Antar / A).", PURPLE)
            return
        if self.sel_ticket is None:
            self.say("Pilih tiket pesanan dulu, baru minta koki AI memasak.", RED)
            return
        if self.plan:
            return
        res = bfs_masak(self.state, self.order)
        self.stats[name] = res
        self.trace_algo, self.trace_i, self.trace_play = name, 0, False
        if not res["found"]:
            self.say("Tidak ada solusi dari kondisi ini. Tekan R untuk memasak ulang.", RED)
            return
        self.used_ai = True
        self.ai_name = name
        self.plan = list(res["path"])
        self.last_plan = list(res["path"])
        self.plan_i, self.plan_t = 0, 0.0
        self.say(f"Koki {name} memasak ({len(self.plan)} langkah). Lihat tab Trace (T)!", BLUE)
