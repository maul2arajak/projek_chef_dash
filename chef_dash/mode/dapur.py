"""
MODE DAPUR - kamu jadi KOKI: masak manual atau minta koki AI (BFS); tab Trace & Analisis.
Fitur Baru v3:
1. **Arahan Urutan Memasak Nasi Goreng Interaktif (Step-by-Step Cooking Guide)**:
   - Menghitung urutan langkah optimal dari kondisi masakan saat ini sampai disajikan (`bfs_masak`).
   - Menampilkan papan **"ARAHAAN URUTAN MASAK"** dengan langkah ke-1, ke-2, dst. beserta penjelasan
     mengapa langkah tersebut dilakukan (misal: Siapkan Nasi & Bumbu -> Goreng Nasi -> Beri Garam/Kecap -> Sajikan).
   - Memberikan **Highlight Bingkai Emas Berkedip + Badge `LANGKAH BERIKUTNYA`** langsung pada tombol aksi
     di sebelah kanan agar siapa pun yang bermain langsung paham cara memasak nasi goreng yang benar!
2. Menggunakan 100% aset PNG bahan, bumbu, wajan, piring, nasi goreng, Koki AI 5-frame, dan peta PyTMX.
"""

import math
import pygame

from ai.koki_bfs import (
    ACTIONS, BAWANG, BERAS, GARAM, ICON_COL, KECAP, NAMES, PIRING,
    STAGES, START, TELUR, apply_action, bfs_masak, describe, is_goal
)
from ai.pengantar_dfs import cell_center
from core.config import BAR, BLUE, BORDER, GOLD, GREEN, H, MUTED, PANEL, PURPLE, RED, TEXT, W, WHITE
from core.ui import fit, lighten, wrap, wrap_lim
from pilar_pbo.polymorphism.render_polymorphism import render_entity_polymorphic


TAB_LABELS = {"dish": "Wajan & Piring", "trace": "Trace Open/Closed (T)", "analisis": "Analisis"}
TAB_ORDER = ["dish", "trace", "analisis"]

ICON_KEYS = {
    BERAS: "icon_0_beras",
    BAWANG: "icon_1_bawang",
    TELUR: "icon_2_telur",
    GARAM: "icon_3_garam",
    KECAP: "icon_4_kecap",
    PIRING: "icon_5_piring",
}

BERAS_STAGE_KEYS = {
    0: "beras_0_mentah",
    1: "beras_1_dicuci",
    2: "beras_2_nasi_matang",
    3: "beras_3_nasi_goreng",
}

BAWANG_STAGE_KEYS = {
    0: "bawang_0_utuh",
    1: "bawang_1_diiris",
    2: "bawang_2_ditumis",
}

TELUR_STAGE_KEYS = {
    0: "telur_0_mentah",
    1: "telur_1_dikocok",
    2: "telur_2_didadar",
}

ACTION_EXPLANATIONS = {
    0: "Taburkan Garam (wajib agar nasi goreng gurih sebelum disajikan)",
    1: "Tuang Kecap Manis (sesuai permintaan tiket pesanan meja)",
    2: "Kocok Telur mentah terlebih dahulu sebelum didadar",
    3: "Dadar Telur yang sudah dikocok agar siap digoreng bersama nasi",
    4: "Iris Bawang merah utuh terlebih dahulu sebelum ditumis",
    5: "Tumis Bawang iris hingga harum",
    6: "Cuci Beras mentah terlebih dahulu sebelum dimasak",
    7: "Masak Beras yang sudah dicuci menjadi Nasi Matang",
    8: "Goreng Nasi! (Dilakukan setelah Nasi matang, Bawang tumis & Telur siap)",
    9: "Sajikan ke Piring! (Setelah Nasi Goreng matang & bumbu sesuai pesanan)",
    10: "Jalan Pintas Cepat: Gunakan Nasi Sisa (langsung jadi Nasi Matang!)",
    11: "Jalan Pintas Cepat: Gunakan Bumbu Instan (bawang langsung siap ditumis!)",
}


class DapurMode:
    """Logika dan tampilan mode dapur (kamu jadi KOKI / minta koki AI BFS + Panduan Urutan Masak)."""

    def reset_state(self):
        self.state = START
        self.steps = 0
        self.mistakes = 0
        self.used_ai = False
        self.ai_name = None
        self.plan = []
        self.plan_i = 0
        self.plan_t = 0.0
        self.mood = ("normal", 0)

    def get_recommended_path(self) -> list:
        """
        Menghitung urutan langkah memasak yang benar dari kondisi `self.state` saat ini
        menggunakan BFS agar pemain selalu mendapat arahan langkah terpendek yang akurat.
        """
        if self.sel_ticket is None or self.order is None:
            return []
        if is_goal(self.state):
            return []
        res = bfs_masak(self.state, self.order, record=False)
        if not res["found"]:
            return None  # None berarti masakan rusak (perlu tekan Ulang / R)
        return res["path"]

    def select_ticket(self, t):
        if self.plan or t is self.sel_ticket:
            return
        self.sel_ticket = t
        self.order = t["party"].order
        self.par = t["party"].par
        self.reset_state()
        self.stats = {}
        self.last_plan = []
        if hasattr(self, "audio"):
            self.audio.play_sfx("click")
        self.say(f"Memasak untuk Meja {t['party'].table + 1}. Ikuti tombol bertanda EMAS untuk urutan masak!", BLUE)

    def perform(self, a, by_ai=False):
        if self.sel_ticket is None:
            if hasattr(self, "audio"):
                self.audio.play_sfx("error")
            self.say("Pilih tiket pesanan di kiri dulu!", RED)
            return
        n = apply_action(self.state, a, self.order)
        if n is None:
            if not by_ai:
                self.mistakes += 1
                self.mood = ("sad", 1.2)
                if hasattr(self, "audio"):
                    self.audio.play_sfx("error")
                self.say("Salah urutan! " + ACTIONS[a].why, RED)
            return
        self.state = n
        self.steps += 1
        self.action_buttons[a].flash = 0.35
        if hasattr(self, "audio"):
            self.audio.play_sfx("cook")
        self.say(f"{ACTIONS[a].label}: berhasil.", GREEN)
        if is_goal(n):
            self.finish_dish()
        elif not bfs_masak(n, self.order, record=False)["found"]:
            self.plan = []
            self.mood = ("sad", 99)
            if hasattr(self, "audio"):
                self.audio.play_sfx("error")
            self.say("Masakan RUSAK! Bahan tidak sesuai pesanan. Klik 'Ulang (R)' untuk masak dari awal.", RED)

    def finish_dish(self):
        t = self.sel_ticket
        self.counter.append(dict(party=t["party"], used_ai=self.used_ai, steps=self.steps,
                                 mistakes=self.mistakes, par=self.par, algo=self.ai_name))
        self.tickets.remove(t)
        if hasattr(self, "audio"):
            self.audio.play_sfx("serve")
        self.say(f"Piring Meja {t['party'].table + 1} siap di Meja Saji! Klik 'Kembali ke Restoran'.", GREEN)
        self.sel_ticket = None
        self.order = None
        self.reset_state()
        self.mood = ("happy", 1.5)

    def do_reset(self):
        if self.sel_ticket is None:
            return
        self.reset_state()
        self.stats = {}
        self.last_plan = []
        if hasattr(self, "audio"):
            self.audio.play_sfx("click")
        self.say("Masakan dibuang, mulai dari awal.", TEXT)

    def click_kitchen(self, pos):
        if self.back_button.rect.collidepoint(pos):
            self.plan = []
            if hasattr(self, "audio"):
                self.audio.play_sfx("click")
            self.go("floor")
            return
        if self.click_center(pos):
            if hasattr(self, "audio"):
                self.audio.play_sfx("click")
            return
        for b in self.ctrl_buttons:
            if b.rect.collidepoint(pos):
                kind, val = b.key
                if kind == "ai":
                    self.run_ai(val)
                else:
                    self.plan = []
                    self.do_reset()
                return
        for i, t in enumerate(self.tickets[:5]):
            if pygame.Rect(30, 112 + i * 40, 260, 36).collidepoint(pos):
                self.select_ticket(t)
                return
        if self.plan:
            return
        for a, b in self.action_buttons.items():
            if b.rect.collidepoint(pos):
                if self.gesture_active():
                    self.say("Mode gestur: CUBIT tombol ini, seret ke wajan. (G = matikan gestur)", BLUE)
                else:
                    self.perform(a)
                return

    def get_stat(self, name):
        return self.stats.get("BFS") if name == "BFS" else self.del_stats

    def trace_len(self):
        res = self.get_stat(self.trace_algo)
        return len(res["trace"]) if res else 0

    def trace_move(self, i):
        n = self.trace_len()
        self.trace_i = max(0, min(i, n - 1)) if n else 0

    def click_center(self, pos):
        for key, rect in self.tab_rects.items():
            if rect.collidepoint(pos):
                self.tab = key
                return True
        if self.tab != "trace":
            return False
        for key, rect in self.trace_btns.items():
            if not rect.collidepoint(pos):
                continue
            if key in ("BFS", "DFS"):
                self.trace_algo, self.trace_i, self.trace_play = key, 0, False
            elif key == "first":
                self.trace_move(0)
                self.trace_play = False
            elif key == "prev":
                self.trace_move(self.trace_i - 1)
                self.trace_play = False
            elif key == "next":
                self.trace_move(self.trace_i + 1)
                self.trace_play = False
            elif key == "last":
                self.trace_move(self.trace_len() - 1)
                self.trace_play = False
            elif key == "play" and self.trace_len():
                if self.trace_i >= self.trace_len() - 1:
                    self.trace_i = 0
                self.trace_play = not self.trace_play
            return True
        return False

    def draw_chef(self, cx, cy, scale_size=None):
        self.chef_actor.x, self.chef_actor.y = cx, cy
        render_entity_polymorphic(self.chef_actor, self.screen, self.assets, mood=self.mood[0], scale_size=scale_size)

    def draw_rail(self):
        r = pygame.Rect(20, 80, 280, 250)
        self.panel(r)
        self.text("Antrean Tiket Dapur", self.f_midb, TEXT, r.x + 12, r.y + 8)
        if not self.tickets:
            for k, ln in enumerate(wrap("Tidak ada tiket. Kembali ke restoran dan catat pesanan dari meja.",
                                        self.f_small, 250)):
                self.text(ln, self.f_small, MUTED, r.x + 14, r.y + 40 + k * 18)
        for i, t in enumerate(self.tickets[:5]):
            p = t["party"]
            rr = pygame.Rect(30, 112 + i * 40, 260, 36)
            sel = t is self.sel_ticket
            pygame.draw.rect(sc := self.screen, (255, 245, 205) if sel else WHITE, rr, border_radius=8)
            pygame.draw.rect(sc, GOLD if sel else BORDER, rr, 3 if sel else 1, border_radius=8)
            o = p.order
            self.text(f"Meja {p.table + 1}: telur {'Y' if o['egg'] else 'T'}, kecap {'Y' if o['kecap'] else 'T'}",
                      self.f_smallb, TEXT, rr.x + 8, rr.y + 10)
            for k in range(3):
                self.heart(rr.right - 62 + k * 18, rr.y + 16, 4, (235, 70, 80) if k < p.hearts else (225, 220, 220))

    def draw_ticket_detail(self):
        r = pygame.Rect(20, 340, 280, 160)
        self.panel(r, (255, 253, 235))
        pygame.draw.rect(self.screen, BAR, (r.x, r.y, r.w, 30), border_top_left_radius=12, border_top_right_radius=12)
        if self.sel_ticket is None:
            self.text("TIKET TERPILIH", self.f_big, WHITE, r.x + 12, r.y + 4)
            self.text("Pilih tiket di atas.", self.f_mid, MUTED, r.x + 14, r.y + 46)
            return
        o = self.order
        self.text(f"MEJA {self.sel_ticket['party'].table + 1}", self.f_big, WHITE, r.x + 12, r.y + 4)
        self.text("Nasi Goreng", self.f_big, TEXT, r.x + 12, r.y + 38)
        rows = [("Garam", "WAJIB", GREEN),
                ("Telur dadar", "YA" if o["egg"] else "TIDAK", GREEN if o["egg"] else RED),
                ("Kecap manis", "YA" if o["kecap"] else "TIDAK", GREEN if o["kecap"] else RED)]
        for i, (k, v, c) in enumerate(rows):
            self.text("- " + k, self.f_mid, TEXT, r.x + 16, r.y + 68 + i * 21)
            self.text(v, self.f_midb, c, r.x + 160, r.y + 68 + i * 21)
        self.text(f"Langkah terbaik (BFS): {self.par}", self.f_midb, BLUE, r.x + 12, r.y + 132)

    def draw_cards(self):
        for i in range(6):
            col, row = divmod(i, 3)
            r = pygame.Rect(310 + col * 235, 80 + row * 66, 225, 58)
            self.panel(r)
            icon_surf = self.assets.items.get(ICON_KEYS[i])
            if icon_surf is not None:
                self.screen.blit(icon_surf, icon_surf.get_rect(center=(r.x + 25, r.y + 29)))
            else:
                pygame.draw.circle(self.screen, ICON_COL[i], (r.x + 24, r.y + 29), 16)
                pygame.draw.circle(self.screen, BORDER, (r.x + 24, r.y + 29), 16, 2)
            self.text(NAMES[i], self.f_smallb, TEXT, r.x + 52, r.y + 5)
            st = self.state[i]
            self.text(STAGES[i][st], self.f_mid, BLUE, r.x + 52, r.y + 20)
            tgt = self.target_label(i)
            self.text("target: " + tgt, self.f_small, RED if tgt.startswith("Jangan") else MUTED, r.x + 52, r.y + 40)
            bar = pygame.Rect(r.x + 144, r.y + 9, 70, 8)
            pygame.draw.rect(self.screen, (225, 215, 200), bar, border_radius=4)
            frac = st / (len(STAGES[i]) - 1)
            if frac > 0:
                pygame.draw.rect(self.screen, GREEN, (bar.x, bar.y, int(bar.w * frac), bar.h), border_radius=4)

    def draw_cooking_guide_box(self, r, rec_path):
        """
        Menampilkan kotak PANDUAN URUTAN MASAK NASI GORENG secara jelas di bagian atas panel wajan
        agar pemain tahu persis urutan langkah memasak yang benar.
        """
        if not getattr(self, "guide_enabled", True):
            return
        sc = self.screen
        gbox = pygame.Rect(r.x + 10, r.y + 40, r.w - 20, 62)
        pygame.draw.rect(sc, (255, 249, 222), gbox, border_radius=8)
        pygame.draw.rect(sc, (225, 165, 35), gbox, 2, border_radius=8)

        if self.sel_ticket is None:
            self.text("PANDUAN CARA MASAK NASI GORENG:", self.f_smallb, BAR, gbox.x + 10, gbox.y + 6)
            self.text("1. Klik tiket pesanan di kiri -> 2. Ikuti tombol bertanda EMAS di kanan!", self.f_small, TEXT, gbox.x + 10, gbox.y + 24)
            self.text("Aturan dasar: Siapkan Nasi & Bawang (& Telur jika diminta) -> Goreng Nasi -> Garam (& Kecap) -> Sajikan.",
                      self.f_small, MUTED, gbox.x + 10, gbox.y + 42)
            return

        if rec_path is None:
            self.text("MASAKAN RUSAK (Bahan tidak sesuai pesanan meja)!", self.f_smallb, RED, gbox.x + 10, gbox.y + 8)
            self.text("Solusi: Klik tombol coklat 'Ulang (R)' di kanan untuk mengulang dari awal.", self.f_smallb, TEXT, gbox.x + 10, gbox.y + 30)
            return

        if not rec_path:
            self.text("NASI GORENG SELESAI DIMASAK!", self.f_smallb, GREEN, gbox.x + 10, gbox.y + 18)
            return

        next_act = rec_path[0]
        act_label = ACTIONS[next_act].label
        chain_str = " -> ".join(ACTIONS[a].label for a in rec_path)
        self.text(f"LANGKAH BERIKUTNYA ({self.steps + 1}/{self.steps + len(rec_path)}): Klik [{act_label}]",
                  self.f_smallb, BLUE, gbox.x + 10, gbox.y + 5)
        self.text(fit(ACTION_EXPLANATIONS.get(next_act, ""), self.f_small, gbox.w - 20),
                  self.f_small, TEXT, gbox.x + 10, gbox.y + 23)
        self.text(fit("Urutan sisa: " + chain_str, self.f_smallb, gbox.w - 20),
                  self.f_smallb, (150, 95, 30), gbox.x + 10, gbox.y + 41)

    def draw_center(self, rec_path):
        sc = self.screen
        r = pygame.Rect(310, 325, 460, 380)
        self.panel(r, (250, 240, 225))
        for key, rect in self.tab_rects.items():
            on = self.tab == key
            pygame.draw.rect(sc, BAR if on else (205, 185, 160), rect, border_radius=8)
            pygame.draw.rect(sc, BORDER, rect, 2, border_radius=8)
            img = self.f_smallb.render(TAB_LABELS[key], True, WHITE if on else TEXT)
            sc.blit(img, img.get_rect(center=rect.center))
        if self.tab == "dish":
            self.draw_dish(r, rec_path)
        elif self.tab == "trace":
            self.draw_trace(r)
        else:
            self.draw_analysis(r)

    def draw_trace(self, r):
        sc = self.screen
        mx, my = pygame.mouse.get_pos()
        res = self.get_stat(self.trace_algo)
        tr = res["trace"] if res else []
        n = len(tr)
        names = {"first": "|<", "prev": "<", "next": ">", "last": ">|",
                 "play": "Jeda" if self.trace_play else "Putar"}
        for key, rect in self.trace_btns.items():
            on = key in ("BFS", "DFS") and self.trace_algo == key
            if key in ("BFS", "DFS"):
                col = (BLUE if key == "BFS" else PURPLE) if on else (185, 175, 165)
                label = key
            else:
                col, label = (150, 100, 70), names[key]
            if rect.collidepoint((mx, my)):
                col = lighten(col)
            pygame.draw.rect(sc, col, rect, border_radius=6)
            pygame.draw.rect(sc, WHITE if on else BORDER, rect, 3 if on else 1, border_radius=6)
            img = self.f_smallb.render(label, True, WHITE)
            sc.blit(img, img.get_rect(center=rect.center))
        if not res:
            if self.trace_algo == "BFS":
                kosong = ("Trace BFS (memasak) belum ada. Pilih tiket, lalu klik Auto BFS (B). "
                          "Di sini tampil isi Open dan Closed pada setiap iterasi, seperti slide Trace BFS.")
            else:
                kosong = ("Trace DFS (mengantar) belum ada. Di restoran nyalakan tombol AI Antar (DFS), "
                          "lalu tunggu ada piring di meja saji. Di sini tampil Open/Closed "
                          "pencarian rute, seperti slide Trace of DFS.")
            for k, ln in enumerate(wrap(kosong, self.f_mid, r.w - 30)):
                self.text(ln, self.f_mid, MUTED, r.x + 15, r.y + 90 + k * 22)
            return
        i = max(0, min(self.trace_i, n - 1))
        self.trace_i = i
        self.text(f"{i + 1}/{n} " + ("masak" if self.trace_algo == "BFS" else "antar"),
                  self.f_smallb, TEXT, r.x + 360, r.y + 48)

        shown = 7
        first = max(0, min(i - 3, n - shown))
        for k in range(first, min(n, first + shown)):
            t = tr[k]
            y = r.y + 78 + (k - first) * 18
            if k == i:
                pygame.draw.rect(sc, (255, 236, 175), (r.x + 8, y - 2, r.w - 16, 18), border_radius=4)
            s = f"{k + 1}. open=[{','.join(t['open'])}]; closed=[{','.join(t['closed'])}]"
            font = self.f_smallb if k == i else self.f_small
            self.text(fit(s, font, r.w - 28), font, TEXT, r.x + 12, y)

        t = tr[i]
        inv = res["by_label"]
        y = r.y + 212
        pygame.draw.line(sc, BORDER, (r.x + 10, y - 4), (r.right - 10, y - 4), 1)
        if t["x"] is None:
            head, node = "Awal: Open berisi state awal (I), Closed kosong.", t["open"][0]
        elif t["goal"]:
            head, node = f"Iterasi {i + 1}: {t['x']} lolos Goal(x) -> GOAL, pencarian selesai.", t["x"]
        else:
            head, node = f"Iterasi {i + 1}: ambil {t['x']} dari Open, cek goal, masuk Closed, perluas anak.", t["x"]
        colr = BLUE if self.trace_algo == "BFS" else PURPLE
        for ln in wrap_lim(head, self.f_smallb, r.w - 24, 2):
            self.text(ln, self.f_smallb, colr, r.x + 12, y)
            y += 16
        for ln in wrap_lim(f"{node} = " + self.describe_node(inv[node]), self.f_small, r.w - 24, 2):
            self.text(ln, self.f_small, MUTED, r.x + 12, y)
            y += 16
        kind = "Queue FIFO, depan di kiri" if self.trace_algo == "BFS" else "Stack LIFO, puncak di kiri"
        y += 4
        for title, lst, col in ((f"Open ({kind})", t["open"], GREEN),
                                ("Closed (terbaru di kiri)", t["closed"], RED)):
            body = f"{title} = [{', '.join(lst)}]"
            for ln in wrap_lim(body, self.f_small, r.w - 24, 3):
                self.text(ln, self.f_small, col, r.x + 12, y)
                y += 16
            y += 4

    def describe_node(self, s):
        if self.trace_algo == "BFS":
            return describe(s)
        c, r = s
        x, y = cell_center(s)
        return f"petak lantai kolom {c}, baris {r} (piksel {x},{y})"

    def analysis_rows(self):
        b, d = self.get_stat("BFS"), self.get_stat("DFS")

        def col(res, f):
            return "-" if res is None else f(res)
        return [
            ("d  (kedalaman solusi)", col(b, lambda r: str(r["d"])), col(d, lambda r: str(r["d"]))),
            ("W  (biaya jalur)", col(b, lambda r: str(r["cost"])), col(d, lambda r: str(r["cost"]))),
            ("Node dihasilkan (waktu)", col(b, lambda r: str(r["generated"])), col(d, lambda r: str(r["generated"]))),
            ("Node diperluas", col(b, lambda r: str(r["expanded"])), col(d, lambda r: str(r["expanded"]))),
            ("Open maks (ruang)", col(b, lambda r: str(r["max_open"])), col(d, lambda r: str(r["max_open"]))),
            ("b  maks (percabangan)", col(b, lambda r: str(r["b_max"])), col(d, lambda r: str(r["b_max"]))),
            ("b  rata-rata", col(b, lambda r: f"{r['b_avg']:.2f}"), col(d, lambda r: f"{r['b_avg']:.2f}")),
            ("m  (kedalaman maks)", col(b, lambda r: str(r["m"])), col(d, lambda r: str(r["m"]))),
            ("Completeness", col(b, lambda r: "Ya" if r["found"] else "Tidak"),
             col(d, lambda r: "Ya" if r["found"] else "Tidak")),
            ("Optimality", col(b, lambda r: "Ya" if r["found"] else "-"),
             col(d, lambda r: ("Ya" if r["cost"] == r["bfs_len"] else "Tidak") if r["found"] else "-")),
        ]

    def draw_analysis(self, r):
        sc = self.screen
        y = r.y + 42
        self.text("Ukuran (slide)", self.f_smallb, TEXT, r.x + 14, y)
        self.text("BFS (masak)", self.f_smallb, BLUE, r.x + 262, y)
        self.text("DFS (antar)", self.f_smallb, PURPLE, r.x + 358, y)
        pygame.draw.line(sc, BORDER, (r.x + 10, y + 18), (r.right - 10, y + 18), 1)
        for k, (label, bv, dv) in enumerate(self.analysis_rows()):
            yy = y + 24 + k * 18
            if k % 2 == 0:
                pygame.draw.rect(sc, (245, 232, 210), (r.x + 8, yy - 2, r.w - 16, 18), border_radius=4)
            self.text(label, self.f_small, TEXT, r.x + 14, yy)
            self.text(bv, self.f_smallb, BLUE, r.x + 262, yy)
            self.text(dv, self.f_smallb, PURPLE, r.x + 358, yy)
        yy = y + 24 + 10 * 18 + 8
        notes = [
            "BFS (masak): S = tuple 6 bahan, P = 12 aksi, I = START, G = piring disajikan, W = 1 per aksi.",
            "DFS (antar): S = petak lantai, P = geser bawah/kanan/kiri/atas, I = meja saji, G = meja pemesan, W = 1.",
            "Waktu = node dihasilkan, ruang = Open maks. DFS bisa lebih panjang dari BFS (tidak optimal).",
        ]
        for nt in notes:
            for ln in wrap_lim(nt, self.f_small, r.w - 28, 2):
                self.text(ln, self.f_small, MUTED, r.x + 14, yy)
                yy += 15
            yy += 3

    def draw_dish(self, r, rec_path):
        sc = self.screen
        # 1. Kotak Panduan Urutan Masak Nasi Goreng di atas wajan
        self.draw_cooking_guide_box(r, rec_path)

        cx, cy = r.centerx, r.y + 220
        st = self.state
        ck = self.assets.cooking

        # 2. Alas Wajan Masak atau Piring Saji Besar
        base_key = "piring_saji_besar" if st[PIRING] == 1 else "wajan_masak"
        base_surf = ck.get(base_key)
        if base_surf is not None:
            sc.blit(base_surf, base_surf.get_rect(center=(cx, cy)))

        # 3. Layer Beras / Nasi Putih / Nasi Goreng
        b_surf = ck.get(BERAS_STAGE_KEYS.get(st[BERAS], "beras_0_mentah"))
        if b_surf is not None:
            sc.blit(b_surf, b_surf.get_rect(center=(cx, cy)))

        # 4. Layer Bawang (Utuh / Diiris / Ditumis)
        w_surf = ck.get(BAWANG_STAGE_KEYS.get(st[BAWANG], "bawang_0_utuh"))
        if w_surf is not None:
            sc.blit(w_surf, w_surf.get_rect(center=(cx, cy)))

        # 5. Layer Telur (Mentah / Dikocok / Didadar)
        e_surf = ck.get(TELUR_STAGE_KEYS.get(st[TELUR], "telur_0_mentah"))
        if e_surf is not None:
            sc.blit(e_surf, e_surf.get_rect(center=(cx, cy)))

        # 6. Layer Bumbu Garam & Kecap Manis
        if st[GARAM] == 1:
            g_surf = ck.get("bumbu_garam")
            if g_surf is not None:
                sc.blit(g_surf, g_surf.get_rect(center=(cx, cy)))

        if st[KECAP] == 1:
            k_surf = ck.get("bumbu_kecap")
            if k_surf is not None:
                sc.blit(k_surf, k_surf.get_rect(center=(cx, cy)))

        # 7. Garnish Sajian Lengkap
        if st[PIRING] == 1:
            gar_surf = ck.get("garnish_sajian")
            if gar_surf is not None:
                sc.blit(gar_surf, gar_surf.get_rect(center=(cx, cy)))

        # 8. Karakter Koki AI (BFS) Full-Body 5-Frame berjalan di koridor dapur
        walker = self.chef_actor.walker
        w_sprite = self.assets.get_char_sprite("ai_chef", walker.direction, walker.frame_index)
        if w_sprite is not None:
            small_walker = pygame.transform.smoothscale(w_sprite, (46, 68))
            sc.blit(small_walker, small_walker.get_rect(midbottom=(int(walker.x), r.bottom - 18)))
            lbl = self.f_smallb.render("Koki AI (BFS)", True, BLUE)
            sc.blit(lbl, (int(walker.x) - lbl.get_width() // 2, r.bottom - 96))

        self.text(self.dish_hint(), self.f_small, MUTED, r.x + 12, r.bottom - 18)

    def dish_hint(self):
        if self.sel_ticket is None:
            return "Pilih tiket pesanan di kiri untuk melihat panduan urutan masak."
        return "Tips: Tombol berlampu EMAS di kanan adalah urutan langkah memasak yang benar."

    def draw_stats(self):
        r = pygame.Rect(780, 520, 380, 185)
        self.panel(r)
        x = r.x + 12
        self.text("Statistik pencarian AI", self.f_midb, TEXT, x, r.y + 8)
        for j, name in enumerate(("BFS", "DFS")):
            y = r.y + 34 + j * 36
            res = self.get_stat(name)
            colr = BLUE if name == "BFS" else PURPLE
            lab = "BFS (koki)" if name == "BFS" else "DFS (antar)"
            if res is None:
                self.text(f"{lab}: belum dijalankan", self.f_small, MUTED, x, y)
            elif not res["found"]:
                self.text(f"{lab}: tidak ada solusi", self.f_small, RED, x, y)
            else:
                self.text(f"{lab}: {len(res['path'])} langkah", self.f_smallb, colr, x, y)
                self.text(f"{res['generated']} dihasilkan | {res['expanded']} diperluas | Open maks {res['max_open']}",
                          self.f_small, colr, x, y + 16)
        b, d = self.get_stat("BFS"), self.get_stat("DFS")
        if d and d["found"]:
            diff = d["d"] - d["bfs_len"]
            note = (f"Rute DFS {diff} langkah lebih panjang dari BFS terpendek."
                    if diff > 0 else "Rute DFS sama panjang dengan BFS.")
            self.text(note, self.f_smallb, TEXT, x, r.y + 108)
        if self.last_plan:
            labels = " > ".join(ACTIONS[a].label for a in self.last_plan)
            for k, ln in enumerate(wrap("Resep: " + labels, self.f_small, 355)[:3]):
                self.text(ln, self.f_small, MUTED, x, r.y + 126 + k * 16)
        else:
            self.text("Open BFS = Queue (FIFO) | Open DFS = Stack (LIFO)", self.f_small, MUTED, x, r.y + 130)

    def draw_kitchen(self):
        sc = self.screen
        tmx_map = self.assets.maps.get("dapur")
        if tmx_map is not None:
            tmx_map.render(sc)
        else:
            sc.fill((250, 232, 205))
            pygame.draw.rect(sc, (235, 215, 185), (0, 64, W, H - 64))

        rec_path = self.get_recommended_path()
        next_recommended_act = rec_path[0] if (rec_path and len(rec_path) > 0) else None
        second_recommended_act = rec_path[1] if (rec_path and len(rec_path) > 1) else None

        self.draw_rail()
        self.draw_ticket_detail()

        bot_rect = pygame.Rect(20, 510, 280, 195)
        self.panel(bot_rect)
        if self.hand is not None and self.gesture_on:
            self.text("Koki AI (BFS)", self.f_smallb, BLUE, 32, 516)
            self.draw_chef(82, 614, scale_size=(115, 115))
        else:
            self.text("Koki AI (BFS) - 5 Frame", self.f_smallb, BLUE, 88, 516)
            self.draw_chef(160, 612, scale_size=(148, 148))

        self.draw_cards()
        pygame.draw.rect(sc, PANEL, (310, 285, 460, 30), border_radius=8)
        pygame.draw.rect(sc, BORDER, (310, 285, 460, 30), 2, border_radius=8)
        msg = self.msg
        while self.f_smallb.size(msg)[0] > 440 and len(msg) > 4:
            msg = msg[:-4] + "..."
        self.text(msg, self.f_smallb, self.msg_col, 318, 292)
        self.draw_center(rec_path)

        mx, my = self.pointer()
        pulse = int(abs(math.sin(pygame.time.get_ticks() / 180.0)) * 4)
        for a, b in self.action_buttons.items():
            b.draw(sc, self.f_midb, b.rect.collidepoint((mx, my)) and not self.plan)
            # Highlight Arahan Urutan Memasak pada tombol aksi berikutnya!
            if getattr(self, "guide_enabled", True) and not self.plan:
                if a == next_recommended_act:
                    hl = b.rect.inflate(4 + pulse, 4 + pulse)
                    pygame.draw.rect(sc, GOLD, hl, 4, border_radius=12)
                    badge = pygame.Rect(b.rect.x + 6, b.rect.y - 11, 104, 18)
                    pygame.draw.rect(sc, GOLD, badge, border_radius=6)
                    pygame.draw.rect(sc, BORDER, badge, 1, border_radius=6)
                    b_img = self.f_smallb.render(f"LANGKAH {self.steps + 1}", True, TEXT)
                    sc.blit(b_img, b_img.get_rect(center=badge.center))
                elif a == second_recommended_act:
                    pygame.draw.rect(sc, (120, 190, 245), b.rect.inflate(2, 2), 2, border_radius=10)
                    badge2 = pygame.Rect(b.rect.right - 78, b.rect.y - 10, 72, 16)
                    pygame.draw.rect(sc, (70, 130, 200), badge2, border_radius=5)
                    b2_img = self.f_small.render(f"Berikut: #{self.steps + 2}", True, WHITE)
                    sc.blit(b2_img, b2_img.get_rect(center=badge2.center))

        for b in self.ctrl_buttons:
            b.draw(sc, self.f_smallb, b.rect.collidepoint((mx, my)))
            # Jika masakan rusak (rec_path is None), beri highlight tombol Ulang (R)
            if getattr(self, "guide_enabled", True) and rec_path is None and b.key[0] == "reset":
                pygame.draw.rect(sc, RED, b.rect.inflate(6, 6), 4, border_radius=12)

        self.back_button.draw(sc, self.f_midb, self.back_button.rect.collidepoint((mx, my)))
        self.draw_stats()
        urgent = [t for t in self.tickets if t["party"].p / t["party"].pmax < 0.3]
        if urgent:
            self.text("Ada pelanggan hampir marah!", self.f_midb, RED, 780, 60)
        self.draw_gesture()
