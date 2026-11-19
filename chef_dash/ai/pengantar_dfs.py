"""
AI PENGANTAR MAKANAN (DFS) - grafik lantai restoran + pencarian rute dengan DFS.
"""

import pygame

from algoritma.bfs import bfs
from algoritma.dfs import dfs
from core.config import FLOOR_RECT, GREEN, MUTED, PURPLE, RED, TABLES, TEXT


# Batas kedalaman DFS (slide 8-puzzle memakai batas 5).
# None = tanpa batas. Di game ini aman tanpa batas karena SETIAP aksi hanya
# memajukan satu tahap bahan (tidak pernah mundur), sehingga graf state tidak
# punya siklus dan jumlah state berhingga -> DFS pasti berhenti.
# Catatan: jika diisi angka, DFS dengan daftar Closed bisa melewatkan solusi
# (node yang sudah di-Closed pada kedalaman besar tidak dibuka lagi).
DFS_DEPTH_LIMIT = None

# Asisten antar (DFS)
ASSIST_SPEED = 380            # px/detik
ASSIST_FEE = 10               # biaya jasa tetap per antaran (Rp)
ASSIST_EXTRA_PENALTY = 0.5    # potongan (Rp) per langkah di atas rute BFS terpendek



# ====================================================================
# GRAFIK RUTE PENGANTARAN (dipakai DFS oleh ASISTEN ANTAR)
#   S = petak lantai (kolom, baris)      P = geser Bawah / Kanan / Kiri / Atas
#   I = petak dekat meja saji            G = petak di depan meja pemesan
#   W = 1 per langkah                    Meja + kursi = penghalang
# ====================================================================
CELL = 40
GRID_COLS, GRID_ROWS = FLOOR_RECT.w // CELL, FLOOR_RECT.h // CELL
DIRS = [(0, 1), (1, 0), (-1, 0), (0, -1)]          # urutan operator yang dicoba DFS/BFS
OBSTACLES = [pygame.Rect(tx - 104, ty - 42, 208, 86) for tx, ty in TABLES]


def cell_center(cell):
    c, r = cell
    return (FLOOR_RECT.x + c * CELL + CELL // 2, FLOOR_RECT.y + r * CELL + CELL // 2)


def nearest_cell(x, y):
    c = round((x - FLOOR_RECT.x - CELL / 2) / CELL)
    r = round((y - FLOOR_RECT.y - CELL / 2) / CELL)
    return (max(0, min(GRID_COLS - 1, c)), max(0, min(GRID_ROWS - 1, r)))


BLOCKED = {(c, r) for c in range(GRID_COLS) for r in range(GRID_ROWS)
           if any(o.collidepoint(cell_center((c, r))) for o in OBSTACLES)}
HOME_CELL = nearest_cell(850, 235)                  # tempat asisten menunggu (dekat meja saji)


def table_cell(ti):
    tx, ty = TABLES[ti]
    return nearest_cell(tx, ty + 80)                # tempat berdiri pengantar di depan meja


def grid_successors(s):
    c, r = s
    for i, (dc, dr) in enumerate(DIRS):
        n = (c + dc, r + dr)
        if 0 <= n[0] < GRID_COLS and 0 <= n[1] < GRID_ROWS and n not in BLOCKED:
            yield i, n


def plan_route(start, goal_cell, record=True):
    """Rute DFS (dipakai asisten) + pembanding BFS terpendek."""
    def is_target(s):
        return s == goal_cell
    d = dfs(start, limit=DFS_DEPTH_LIMIT, record=record, succ=grid_successors, goal=is_target)
    b = bfs(start, record=False, succ=grid_successors, goal=is_target)
    d["bfs_len"] = b["d"]
    return d


class PengantarAI:
    """ASISTEN ANTAR (AI): rute dari meja saji ke meja pelanggan dicari dengan DFS."""

    def toggle_assist(self):
        a = self.asst
        a["on"] = not a["on"]
        self.assist_button.flash = 0.35
        if a["on"]:
            self.say("Asisten antar (DFS) AKTIF: piring di meja saji akan diantar otomatis.", GREEN)
        else:
            self.say("Asisten antar dimatikan (antaran yang sedang jalan diselesaikan).", TEXT)

    def assist_dispatch(self):
        """Ambil piring siap di meja saji, cari rute DFS ke meja pemesan."""
        a = self.asst
        plate = next((c for c in self.counter
                      if c["party"] in self.parties and c["party"].state == "waitfood"
                      and c["party"].table is not None), None)
        if plate is None:
            return
        self.counter.remove(plate)
        p = plate["party"]
        goal = table_cell(p.table)
        res = plan_route(HOME_CELL, goal, record=True)
        self.del_stats = res
        last = res["trace"][-1]
        inv = res["by_label"]
        a.update(state="go", plate=plate, party=p, goal=goal, path=res["states"], back_path=[],
                 closed=[inv[l] for l in last["closed"]], open=[inv[l] for l in last["open"]],
                 pts=[cell_center(c) for c in res["states"][1:]],
                 extra=res["d"] - res["bfs_len"], len=res["d"], bfs=res["bfs_len"])
        self.assist_info = f"Rute DFS: {res['d']} langkah (BFS: {res['bfs_len']})"
        self.say(f"Asisten DFS antar ke Meja {p.table + 1}: {res['d']} langkah (BFS terpendek "
                 f"{res['bfs_len']}). {res['generated']} dihasilkan, {res['expanded']} diperluas.", PURPLE)

    def assist_arrived(self):
        a, w = self.asst, self.assist
        if a["state"] == "go":
            p, plate = a["party"], a["plate"]
            if p in self.parties and p.state == "waitfood":
                self.deliver(p, plate, assist=dict(extra=a["extra"], len=a["len"], bfs=a["bfs"]))
            else:
                self.say("Pelanggan sudah pergi, asisten membawa piring kembali.", MUTED)
            a["plate"], a["party"] = None, None
            back = dfs(a["goal"], limit=DFS_DEPTH_LIMIT, record=False, succ=grid_successors,
                       goal=lambda s: s == HOME_CELL)
            a.update(state="back", back_path=back["states"], closed=[], open=[],
                     pts=[cell_center(c) for c in back["states"][1:]])
        else:
            a.update(state="idle", pts=[], back_path=[])
            w.x, w.y = cell_center(HOME_CELL)
            w.tx, w.ty = w.x, w.y
            w.walking = False

    def update_assistant(self, dt):
        a, w = self.asst, self.assist
        if a["state"] == "idle":
            w.walking = False
            if a["on"]:
                self.assist_dispatch()
            return
        if not a["pts"]:
            self.assist_arrived()
            return
        w.tx, w.ty = a["pts"][0]
        if w.step(dt, ASSIST_SPEED):
            a["pts"].pop(0)

    def draw_route_overlay(self):
        """Visual DFS: Closed (ungu), Open (hijau), garis rute yang sedang ditempuh asisten."""
        a = self.asst
        if not self.show_overlay or a["state"] == "idle":
            return
        sc = self.screen
        off = (CELL - 6) // 2
        for cells, surf in ((a["closed"], self.cell_closed), (a["open"], self.cell_open)):
            for cell in cells:
                x, y = cell_center(cell)
                sc.blit(surf, (x - off, y - off))
        path = a["path"] if a["state"] == "go" else a["back_path"]
        pts = [cell_center(c) for c in path]
        if len(pts) > 1:
            col = (110, 60, 170) if a["state"] == "go" else (150, 150, 170)
            pygame.draw.lines(sc, col, False, pts, 4)
            pygame.draw.circle(sc, GREEN, pts[0], 7)
            pygame.draw.circle(sc, RED, pts[-1], 7)

    def draw_assistant_extras(self, x, hy):
        sc = self.screen
        x = int(x)
        pygame.draw.rect(sc, (60, 160, 90), (x - 16, hy - 24, 32, 11), border_radius=5)
        pygame.draw.rect(sc, (40, 120, 70), (x - 23, hy - 15, 46, 4), border_radius=2)
        img = self.f_smallb.render("AI-DFS", True, PURPLE)
        sc.blit(img, (x - img.get_width() // 2, hy - 42))
