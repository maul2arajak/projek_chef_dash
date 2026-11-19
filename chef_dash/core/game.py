"""
Kelas Game Chef Dash PBO v3:
- 4 Pilar PBO Terpisah (`pilar_pbo/`)
- Aset Gambar 5-Frame (`assets/`) + Peta Dunia PyTMX (`restoran.tmx` & `dapur.tmx`)
- Sistem Anti-Tembus Meja & Kursi (`core/collision.py`)
- 2 Musik Latar Berbeda (`bgm_restoran.wav` di Luar Dapur & `bgm_dapur.wav` di Dalam Dapur) + SFX (`core/audio.py`)
- Fitur Arahan Urutan Memasak Nasi Goreng Interaktif (`mode/dapur.py`)
- Menu Pengaturan Game / Settings (`core/settings_menu.py`).
"""

import random
import sys
import pygame

from ai.koki_bfs import ACTIONS, DISPLAY_ORDER, START, KokiAI
from ai.pengantar_dfs import CELL, HOME_CELL, PengantarAI, cell_center
from core.assets import AssetManager
from core.audio import AudioManager
from core.config import BAR, BLUE, BORDER, FPS, GOLD, GREEN, H, PANEL, PURPLE, QUEUE_SLOTS, RED, TABLES, TEXT, W, WHITE
from core.settings_menu import SettingsMenuMixin
from core.ui import Button, lighten, wrap
from mode.dapur import DapurMode, TAB_ORDER
from mode.restoran import RestoranMode
from pilar_pbo.encapsulation.game_state import EncapsulatedGameState
from pilar_pbo.inheritance.characters import AIAssistantCharacter, ChefCharacter, WaitressCharacter
from visi.gestur import GestureMixin
from visi.pelacak_tangan import HandTracker


class Game(RestoranMode, DapurMode, KokiAI, PengantarAI, GestureMixin, SettingsMenuMixin):
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("Chef Dash PBO v3 (Anti-Tembus + 2 Musik BGM + Panduan Masak + Settings + 5-Frame)")
        self.clock = pygame.time.Clock()
        self.f_title = pygame.font.SysFont("arial", 26, bold=True)
        self.f_big = pygame.font.SysFont("arial", 20, bold=True)
        self.f_mid = pygame.font.SysFont("arial", 16)
        self.f_midb = pygame.font.SysFont("arial", 16, bold=True)
        self.f_small = pygame.font.SysFont("arial", 13)
        self.f_smallb = pygame.font.SysFont("arial", 13, bold=True)
        self.f_huge = pygame.font.SysFont("arial", 46, bold=True)

        # Muat aset gambar 5-frame, bahan masakan PNG, dan peta PyTMX
        self.assets = AssetManager()
        self.assets.load_all()

        # Inisialisasi AudioManager (2 BGM: Restoran & Dapur + SFX) dan Menu Pengaturan
        self.audio = AudioManager()
        self.init_settings_menu()

        # Enkapsulasi Game State (Pilar Encapsulation)
        self._game_state = EncapsulatedGameState(START)

        self.action_buttons = {}
        for i, a in enumerate(DISPLAY_ORDER):
            col, row = divmod(i, 6)
            self.action_buttons[a] = Button((780 + col * 196, 80 + row * 52, 184, 46),
                                            ACTIONS[a].label, ACTIONS[a].color, ("act", a))
        self.ctrl_buttons = [
            Button((780, 400, 185, 44), "Koki AI: Auto BFS (B)", BLUE, ("ai", "BFS")),
            Button((975, 400, 185, 44), "Ulang (R)", (150, 100, 70), ("reset", None)),
        ]
        self.assist_button = Button((940, 126, 224, 40), "AI Antar (DFS): OFF (A)", PURPLE, ("assist", None))
        self.cell_closed = pygame.Surface((CELL - 6, CELL - 6), pygame.SRCALPHA)
        self.cell_closed.fill((130, 80, 170, 80))
        self.cell_open = pygame.Surface((CELL - 6, CELL - 6), pygame.SRCALPHA)
        self.cell_open.fill((60, 190, 100, 110))
        self.back_button = Button((780, 455, 380, 48), "Kembali ke Restoran", (60, 130, 90), ("back", None))
        self.tab_rects = {"dish": pygame.Rect(318, 333, 128, 26),
                          "trace": pygame.Rect(452, 333, 172, 26),
                          "analisis": pygame.Rect(630, 333, 132, 26)}
        self.trace_btns = {"BFS": pygame.Rect(318, 367, 52, 26), "DFS": pygame.Rect(374, 367, 52, 26),
                           "first": pygame.Rect(440, 367, 32, 26), "prev": pygame.Rect(476, 367, 32, 26),
                           "next": pygame.Rect(512, 367, 32, 26), "last": pygame.Rect(548, 367, 32, 26),
                           "play": pygame.Rect(590, 367, 76, 26)}
        self.intro = True
        cam = int(sys.argv[sys.argv.index("--cam") + 1]) if "--cam" in sys.argv else 0
        self.hand = None
        if "--no-cam" not in sys.argv:
            self.hand = HandTracker(cam=cam)
            self.hand.start()
        self.gesture_on = self.hand is not None
        self.g_pos, self.g_vis, self.g_pinch, self.g_lost = [W / 2, H / 2], False, False, 0.0
        self.g_clock, self.last_pinch_t = 0.0, -9.0
        self.drag = None
        self.arm, self.arm_t, self.arm_lock, self.pinch_t = None, 0.0, False, 0.0
        self.cam_surf = None
        self.new_game()

    # --- Properti Enkapsulasi ke EncapsulatedGameState ---
    @property
    def money(self) -> int:
        return self._game_state.money

    @money.setter
    def money(self, val: int) -> None:
        self._game_state.money = val

    @property
    def served(self) -> int:
        return self._game_state.served

    @served.setter
    def served(self, val: int) -> None:
        self._game_state.served = val

    @property
    def rep(self) -> int:
        return self._game_state.rep

    @rep.setter
    def rep(self, val: int) -> None:
        self._game_state.rep = val

    @property
    def state(self) -> tuple:
        return self._game_state.cooking_state

    @state.setter
    def state(self, val: tuple) -> None:
        self._game_state.cooking_state = val

    @property
    def steps(self) -> int:
        return self._game_state.steps

    @steps.setter
    def steps(self, val: int) -> None:
        self._game_state.steps = val

    @property
    def mistakes(self) -> int:
        return self._game_state.mistakes

    @mistakes.setter
    def mistakes(self, val: int) -> None:
        self._game_state.mistakes = val

    def new_game(self):
        self.t = 0.0
        self._game_state = EncapsulatedGameState(START)
        self.over = False
        self.scene = "floor"
        self.trans = None
        self.parties = []
        self.tables = [None] * len(TABLES)
        self.tickets = []
        self.counter = []
        self.carry = []

        self.waitress = WaitressCharacter(640, 230)
        self.assist = AIAssistantCharacter(*cell_center(HOME_CELL))
        self.chef_actor = ChefCharacter(160, 608)

        self.asst = dict(on=False, state="idle", pts=[], plate=None, party=None, goal=None,
                         path=[], back_path=[], closed=[], open=[], extra=0, len=0, bfs=0)
        self.del_stats = None
        self.assist_info = "Rute DFS: belum ada"
        self.show_overlay = True
        self.task = None
        self.sel_party = None
        self.popups = []
        self.next_arrival = 1.0
        self.sel_ticket = None
        self.order = None
        self.par = 0
        self.stats = {}
        self.last_plan = []
        self.tab = "dish"
        self.trace_algo = "BFS"
        self.trace_i = 0
        self.trace_play = False
        self.trace_t = 0.0
        self.reset_state()
        # Putar BGM Restoran (Luar Dapur)
        self.audio.switch_bgm("floor")
        self.say("Klik pelanggan di antrean kiri, lalu klik meja kosong. (Tombol Pengaturan di kanan atas / tekan P)", TEXT)

    def say(self, text, color=TEXT):
        self.msg, self.msg_col = text, color

    def go(self, scene):
        if self.trans or self.scene == scene:
            return
        self.trans = dict(to=scene, t=0.0, switched=False)

    def click(self, pos):
        # 1. Cek klik pada tombol/modal Pengaturan (Settings) terlebih dahulu
        if self.handle_settings_click(pos):
            return
        if self.intro:
            self.intro = False
            self.audio.play_sfx("click")
            return
        if self.over or self.trans:
            return
        if self.scene == "floor":
            self.click_floor(pos)
        else:
            self.click_kitchen(pos)

    def key(self, k):
        if k == pygame.K_p:
            self.toggle_settings()
            return
        if k == pygame.K_ESCAPE:
            if self.settings_open:
                self.toggle_settings()
                return
            if self.scene == "kitchen" and self.plan:
                self.plan = []
                self.say("Auto-masak dibatalkan.", TEXT)
                return
            self.toggle_settings()
            return
        if self.settings_open:
            return
        if self.intro:
            self.intro = False
            self.audio.play_sfx("click")
            return
        if self.over:
            if k == pygame.K_RETURN:
                self.new_game()
            return
        if self.trans:
            return
        if k == pygame.K_a:
            self.toggle_assist()
            return
        if k == pygame.K_v:
            self.show_overlay = not self.show_overlay
            self.say("Visual DFS " + ("ditampilkan." if self.show_overlay else "disembunyikan."), PURPLE)
            return
        if self.scene != "kitchen":
            return
        if k == pygame.K_b:
            self.run_ai("BFS")
        elif k == pygame.K_d:
            self.run_ai("DFS")
        elif k == pygame.K_r:
            self.plan = []
            self.do_reset()
        elif k == pygame.K_g:
            if self.hand is None or self.hand.get()["error"]:
                self.say("Kamera tidak tersedia, memakai mouse.", RED)
            else:
                self.gesture_on = not self.gesture_on
                self.drag = None
                self.say("Mode gestur " + ("AKTIF." if self.gesture_on else "mati, pakai mouse."), BLUE)
        elif k == pygame.K_t:
            self.tab = TAB_ORDER[(TAB_ORDER.index(self.tab) + 1) % len(TAB_ORDER)]
        elif k == pygame.K_RIGHT:
            self.trace_play = False
            self.trace_move(self.trace_i + 1)
        elif k == pygame.K_LEFT:
            self.trace_play = False
            self.trace_move(self.trace_i - 1)
        elif k == pygame.K_HOME:
            self.trace_play = False
            self.trace_move(0)
        elif k == pygame.K_END:
            self.trace_play = False
            self.trace_move(self.trace_len() - 1)

    def update(self, dt):
        self.update_gesture(dt)
        if self.settings_open:
            return

        dt_scaled = dt * self.speed_mult
        self.chef_actor.update_idle_anim(dt_scaled, active_cooking=bool(self.plan))
        for b in list(self.action_buttons.values()) + self.ctrl_buttons + [self.back_button, self.assist_button]:
            b.flash = max(0, b.flash - dt)
        for p in self.popups:
            p["t"] -= dt
            p["y"] -= 28 * dt
        self.popups = [p for p in self.popups if p["t"] > 0]

        if self.trans:
            tr = self.trans
            tr["t"] += dt
            if tr["t"] >= 0.35 and not tr["switched"]:
                tr["switched"] = True
                self.scene = tr["to"]
                # Otomatis ganti musik latar antara Luar Dapur (Restoran) dan Dalam Dapur!
                self.audio.switch_bgm(self.scene)
                if self.scene == "kitchen":
                    if self.sel_ticket is None and self.tickets:
                        self.select_ticket(self.tickets[0])
                    self.say("Mode DAPUR (Musik Dapur Aktif): ikuti tombol bertanda EMAS untuk memasak!", BLUE)
                else:
                    self.say("Mode RESTORAN (Musik Restoran Aktif): klik MEJA SAJI untuk ambil piring.", BLUE)
            if tr["t"] >= 0.7:
                self.trans = None

        if self.trace_play and self.scene == "kitchen":
            self.trace_t += dt
            if self.trace_t >= 0.18:
                self.trace_t = 0.0
                if self.trace_i >= self.trace_len() - 1:
                    self.trace_play = False
                else:
                    self.trace_i += 1

        if self.intro or self.over:
            return
        self.t += dt_scaled

        mode, mt = self.mood
        if mode != "normal" and mt < 90:
            mt -= dt_scaled
            self.mood = ("normal", 0) if mt <= 0 else (mode, mt)

        # Pelanggan datang
        if self.t >= self.next_arrival:
            self.spawn_party()
            gap = max(5.0, 11.0 - self.served * 0.25)
            self.next_arrival = self.t + random.uniform(gap, gap + 5)

        # Pelayan (5-frame animasi jalan + anti-tembus meja/kursi)
        w = self.waitress
        if self.task and not self.trans:
            if w.step(dt_scaled, 300):
                task, self.task = self.task, None
                self.arrive(task)
        else:
            w.walking = False
            w.frame_index = 0

        # Pelanggan (5-frame animasi jalan + anti-tembus meja/kursi)
        slots = {id(p): QUEUE_SLOTS[i] for i, p in enumerate(self.queue_list())}
        for p in list(self.parties):
            n = len(p.members)
            if p.state == "queue":
                sx, sy = slots[id(p)]
                for k, m in enumerate(p.members):
                    m.use_collision = False
                    m.tx, m.ty = sx + (k - (n - 1) / 2) * 40, sy
                p.p -= dt_scaled
                for m in p.members:
                    m.step(dt_scaled, 220)
                if p.p <= 0:
                    self.anger(p)
            elif p.state == "walking":
                for m in p.members:
                    m.use_collision = True
                done = [m.step(dt_scaled, 260) for m in p.members]
                if all(done):
                    p.state = "ready"
            elif p.state in ("ready", "waitfood"):
                p.p -= dt_scaled
                if p.p <= 0:
                    self.anger(p)
            elif p.state == "eating":
                p.eat -= dt_scaled
                if p.eat <= 0:
                    self.leave(p)
            elif p.state == "leaving":
                for m in p.members:
                    m.use_collision = True
                done = [m.step(dt_scaled, 240) for m in p.members]
                if all(done):
                    self.parties.remove(p)

        self.update_assistant(dt_scaled)

        if self.rep <= 0:
            self.over = True
            self.plan = []

        if self.plan:
            self.plan_t += dt_scaled
            if self.plan_t >= 0.8:
                self.plan_t = 0
                a = self.plan[self.plan_i]
                self.plan_i += 1
                if self.plan_i >= len(self.plan):
                    self.plan = []
                self.perform(a, by_ai=True)

    def panel(self, rect, color=PANEL):
        pygame.draw.rect(self.screen, color, rect, border_radius=12)
        pygame.draw.rect(self.screen, BORDER, rect, 2, border_radius=12)

    def text(self, s, font, color, x, y):
        self.screen.blit(font.render(s, True, color), (x, y))

    def heart(self, x, y, r, col):
        sc = self.screen
        pygame.draw.circle(sc, col, (x - r, y), r)
        pygame.draw.circle(sc, col, (x + r, y), r)
        pygame.draw.polygon(sc, col, [(x - 2 * r, y + r // 2), (x + 2 * r, y + r // 2), (x, y + 3 * r)])

    def draw_topbar(self):
        sc = self.screen
        pygame.draw.rect(sc, BAR, (0, 0, W, 64))
        self.text("CHEF DASH", self.f_title, WHITE, 18, 17)
        mode = "RESTORAN (BGM 1)" if self.scene == "floor" else "DAPUR (BGM 2)"
        self.text(f"Mode: {mode}", self.f_smallb, (255, 225, 195), 182, 25)
        self.text(f"Uang: Rp {self.money}", self.f_big, WHITE, 375, 20)
        self.text(f"Dilayani: {self.served}", self.f_big, WHITE, 570, 20)
        self.text(f"Tiket: {len(self.tickets)}", self.f_big, WHITE, 725, 20)
        self.text("Reputasi:", self.f_big, WHITE, 845, 20)
        for i in range(3):
            self.heart(955 + i * 24, 28, 5, (255, 120, 120) if i < self.rep else (130, 60, 55))

        # Tombol Pengaturan (Settings) di kanan atas Topbar
        mx, my = pygame.mouse.get_pos()
        hov = self.settings_top_btn.collidepoint((mx, my))
        bcol = lighten((75, 50, 40), 25) if hov else (75, 50, 40)
        pygame.draw.rect(sc, bcol, self.settings_top_btn, border_radius=8)
        pygame.draw.rect(sc, GOLD if self.settings_open else WHITE, self.settings_top_btn, 2, border_radius=8)
        s_img = self.f_smallb.render("Pengaturan (P)", True, WHITE)
        sc.blit(s_img, s_img.get_rect(center=self.settings_top_btn.center))

    def draw_overlay(self, title, lines, foot):
        sc = self.screen
        shade = pygame.Surface((W, H), pygame.SRCALPHA)
        shade.fill((40, 25, 15, 205))
        sc.blit(shade, (0, 0))
        r = pygame.Rect(200, 100, 780, 500)
        self.panel(r, (255, 250, 235))
        img = self.f_huge.render(title, True, BAR)
        sc.blit(img, img.get_rect(center=(W // 2, r.y + 55)))
        y = r.y + 115
        for ln in lines:
            for sub in wrap(ln, self.f_mid, 720):
                self.text(sub, self.f_mid, TEXT, r.x + 30, y)
                y += 24
            y += 8
        img = self.f_big.render(foot, True, BLUE)
        sc.blit(img, img.get_rect(center=(W // 2, r.bottom - 35)))

    def draw(self):
        sc = self.screen
        if self.scene == "floor":
            self.draw_floor()
        else:
            self.draw_kitchen()
        self.draw_topbar()
        if self.trans:
            tr = self.trans
            a = 1 - abs(tr["t"] - 0.35) / 0.35
            shade = pygame.Surface((W, H))
            shade.fill((20, 12, 8))
            shade.set_alpha(int(255 * max(0, min(1, a))))
            sc.blit(shade, (0, 0))
        if self.intro:
            self.draw_overlay("CHEF DASH PBO v3", [
                "1. ANTI-TEMBUS OBJEK: Pelayan, Pelanggan, dan Asisten AI berjalan memutari meja & kursi (tidak menembus objek).",
                "2. DUA MUSIK LATAR (BGM): Musik Cafe Jazz hangat saat di LUAR DAPUR (Restoran) dan Musik Upbeat Cooking saat di DALAM DAPUR.",
                "3. ARAHAN URUTAN MASAK NASI GORENG: Di dapur terdapat kotak Panduan Langkah Memasak + Highlight Emas pada tombol aksi berikutnya agar mudah dipahami!",
                "4. MENU PENGATURAN (SETTINGS): Klik tombol 'Pengaturan (P)' di kanan atas atau tekan P / ESC untuk mengatur volume musik, SFX, kecepatan, gestur kamera, dan panduan masak.",
                "5. ALGORITMA BFS & DFS + COMPUTER VISION: Koki AI memasak dengan BFS (resep terpendek), Asisten AI mengantar dengan DFS, serta mendukung kontrol gestur tangan webcam."],
                "Klik atau tekan tombol apa saja untuk mulai")
        if self.over:
            self.draw_overlay("RESTO TUTUP!", [
                f"Total uang: Rp {self.money}",
                f"Pelanggan dilayani: {self.served}",
                "Reputasi restoran habis karena terlalu banyak pelanggan marah."],
                "Tekan ENTER untuk main lagi")
        self.draw_settings_modal()
        pygame.display.flip()

    def run(self):
        while True:
            dt = min(self.clock.tick(FPS) / 1000, 0.1)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    if self.hand:
                        self.hand.stop()
                    pygame.quit()
                    sys.exit()
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    self.click(e.pos)
                if e.type == pygame.KEYDOWN:
                    self.key(e.key)
            self.update(dt)
            self.draw()
