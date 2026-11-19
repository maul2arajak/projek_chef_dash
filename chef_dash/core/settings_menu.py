"""
MENU PENGATURAN GAME (`core/settings_menu.py`)
Menyediakan modal Pengaturan (Settings) yang dapat dibuka kapan saja lewat tombol `Pengaturan (P)`
di kanan atas Topbar atau tombol keyboard `P` / `ESC`:
1. Musik Latar (BGM Restoran & Dapur): ON/OFF + Tombol Volume (`-` / `+`)
2. Efek Suara (SFX Masak & Klik): ON/OFF + Tombol Volume (`-` / `+`)
3. Panduan Urutan Masak Nasi Goreng: ON/OFF (Menampilkan arahan langkah & highlight tombol emas)
4. Kecepatan Game: Santai (0.8x) / Normal (1.0x) / Cepat (1.3x)
5. Kontrol Gestur Kamera (CV): ON/OFF
6. Visual Rute Open/Closed DFS: ON/OFF
7. Tombol `Lanjutkan Permainan` & `Mulai Ulang Game Baru`.
"""

import pygame
from core.config import BAR, BLUE, BORDER, GOLD, GREEN, H, MUTED, PANEL, PURPLE, RED, TEXT, W, WHITE
from core.ui import lighten


class SettingsMenuMixin:
    """Mixin untuk menampilkan dan menangani interaksi Menu Pengaturan Game."""

    def init_settings_menu(self):
        self.settings_open = False
        self.guide_enabled = True
        self.game_speed_idx = 1
        self.game_speeds = [(0.8, "Santai (0.8x)"), (1.0, "Normal (1.0x)"), (1.3, "Cepat (1.3x)")]
        # Tombol Pengaturan di Topbar
        self.settings_top_btn = pygame.Rect(1035, 14, 130, 36)
        self._build_settings_rects()

    def _build_settings_rects(self):
        cx = W // 2
        y0 = 175
        dy = 56
        self.set_rects = {
            "bgm_toggle": pygame.Rect(cx + 30, y0, 90, 36),
            "bgm_minus": pygame.Rect(cx + 135, y0, 40, 36),
            "bgm_plus": pygame.Rect(cx + 265, y0, 40, 36),

            "sfx_toggle": pygame.Rect(cx + 30, y0 + dy, 90, 36),
            "sfx_minus": pygame.Rect(cx + 135, y0 + dy, 40, 36),
            "sfx_plus": pygame.Rect(cx + 265, y0 + dy, 40, 36),

            "guide_toggle": pygame.Rect(cx + 30, y0 + dy * 2, 275, 36),
            "speed_cycle": pygame.Rect(cx + 30, y0 + dy * 3, 275, 36),
            "gesture_toggle": pygame.Rect(cx + 30, y0 + dy * 4, 275, 36),
            "dfs_vis_toggle": pygame.Rect(cx + 30, y0 + dy * 5, 275, 36),

            "resume": pygame.Rect(cx - 250, y0 + dy * 6 + 18, 235, 46),
            "restart": pygame.Rect(cx + 15, y0 + dy * 6 + 18, 235, 46),
        }

    @property
    def speed_mult(self) -> float:
        return self.game_speeds[self.game_speed_idx][0]

    def toggle_settings(self):
        self.settings_open = not self.settings_open
        if hasattr(self, "audio"):
            self.audio.play_sfx("click")

    def handle_settings_click(self, pos) -> bool:
        """Mengembalikan True jika klik ditangani oleh Menu Pengaturan."""
        if self.settings_top_btn.collidepoint(pos):
            self.toggle_settings()
            return True
        if not self.settings_open:
            return False

        r = self.set_rects
        if r["bgm_toggle"].collidepoint(pos):
            self.audio.toggle_bgm(self.scene)
            self.audio.play_sfx("click")
        elif r["bgm_minus"].collidepoint(pos):
            self.audio.set_bgm_volume(self.audio.bgm_volume - 0.1)
            self.audio.play_sfx("click")
        elif r["bgm_plus"].collidepoint(pos):
            self.audio.set_bgm_volume(self.audio.bgm_volume + 0.1)
            self.audio.play_sfx("click")
        elif r["sfx_toggle"].collidepoint(pos):
            self.audio.toggle_sfx()
            self.audio.play_sfx("click")
        elif r["sfx_minus"].collidepoint(pos):
            self.audio.set_sfx_volume(self.audio.sfx_volume - 0.1)
            self.audio.play_sfx("click")
        elif r["sfx_plus"].collidepoint(pos):
            self.audio.set_sfx_volume(self.audio.sfx_volume + 0.1)
            self.audio.play_sfx("click")
        elif r["guide_toggle"].collidepoint(pos):
            self.guide_enabled = not self.guide_enabled
            self.audio.play_sfx("click")
        elif r["speed_cycle"].collidepoint(pos):
            self.game_speed_idx = (self.game_speed_idx + 1) % len(self.game_speeds)
            self.audio.play_sfx("click")
        elif r["gesture_toggle"].collidepoint(pos):
            if self.hand is not None and not self.hand.get()["error"]:
                self.gesture_on = not self.gesture_on
            self.audio.play_sfx("click")
        elif r["dfs_vis_toggle"].collidepoint(pos):
            self.show_overlay = not self.show_overlay
            self.audio.play_sfx("click")
        elif r["resume"].collidepoint(pos):
            self.settings_open = False
            self.audio.play_sfx("click")
        elif r["restart"].collidepoint(pos):
            self.settings_open = False
            self.audio.play_sfx("click")
            self.new_game()
        return True

    def _draw_set_btn(self, rect, label, col, mx, my):
        sc = self.screen
        hover = rect.collidepoint((mx, my))
        c = lighten(col, 24) if hover else col
        pygame.draw.rect(sc, (195, 175, 148), rect.move(0, 2), border_radius=8)
        pygame.draw.rect(sc, c, rect, border_radius=8)
        pygame.draw.rect(sc, BORDER, rect, 2, border_radius=8)
        img = self.f_smallb.render(label, True, WHITE)
        sc.blit(img, img.get_rect(center=rect.center))

    def draw_settings_modal(self):
        if not self.settings_open:
            return
        sc = self.screen
        mx, my = pygame.mouse.get_pos()
        shade = pygame.Surface((W, H), pygame.SRCALPHA)
        shade.fill((35, 22, 14, 210))
        sc.blit(shade, (0, 0))

        box = pygame.Rect(230, 88, 720, 545)
        self.panel(box, (255, 250, 238))
        pygame.draw.rect(sc, BAR, (box.x, box.y, box.w, 54), border_top_left_radius=12, border_top_right_radius=12)
        title = self.f_title.render("PENGATURAN GAME (SETTINGS)", True, WHITE)
        sc.blit(title, title.get_rect(center=(box.centerx, box.y + 27)))

        cx = W // 2
        y0 = 175
        dy = 56
        r = self.set_rects

        # 1. Musik Latar (2 BGM: Restoran & Dapur)
        track_lbl = "Restoran (Cafe Jazz)" if self.scene == "floor" else "Dapur (Upbeat Cooking)"
        self.text(f"1. Musik Latar ({track_lbl})", self.f_midb, TEXT, box.x + 32, y0 + 7)
        self._draw_set_btn(r["bgm_toggle"], "ON" if self.audio.bgm_enabled else "OFF",
                           GREEN if self.audio.bgm_enabled else RED, mx, my)
        self._draw_set_btn(r["bgm_minus"], "-", (150, 105, 75), mx, my)
        vol_bgm = f"{int(round(self.audio.bgm_volume * 100))}%"
        self.text(vol_bgm, self.f_midb, BLUE, cx + 198, y0 + 7)
        self._draw_set_btn(r["bgm_plus"], "+", (150, 105, 75), mx, my)

        # 2. Efek Suara (SFX)
        self.text("2. Efek Suara (SFX Klik & Masak)", self.f_midb, TEXT, box.x + 32, y0 + dy + 7)
        self._draw_set_btn(r["sfx_toggle"], "ON" if self.audio.sfx_enabled else "OFF",
                           GREEN if self.audio.sfx_enabled else RED, mx, my)
        self._draw_set_btn(r["sfx_minus"], "-", (150, 105, 75), mx, my)
        vol_sfx = f"{int(round(self.audio.sfx_volume * 100))}%"
        self.text(vol_sfx, self.f_midb, BLUE, cx + 198, y0 + dy + 7)
        self._draw_set_btn(r["sfx_plus"], "+", (150, 105, 75), mx, my)

        # 3. Panduan Urutan Masak Nasi Goreng
        self.text("3. Arahan Urutan Masak Nasi Goreng", self.f_midb, TEXT, box.x + 32, y0 + dy * 2 + 7)
        self._draw_set_btn(
            r["guide_toggle"],
            "AKTIF (Highlight + Panduan Langkah)" if self.guide_enabled else "NONAKTIF (Mode Ahli)",
            GREEN if self.guide_enabled else MUTED, mx, my
        )

        # 4. Kecepatan Permainan
        self.text("4. Kecepatan Waktu Permainan", self.f_midb, TEXT, box.x + 32, y0 + dy * 3 + 7)
        self._draw_set_btn(r["speed_cycle"], self.game_speeds[self.game_speed_idx][1], BLUE, mx, my)

        # 5. Gestur Kamera Computer Vision
        self.text("5. Kontrol Gestur Kamera (OpenCV)", self.f_midb, TEXT, box.x + 32, y0 + dy * 4 + 7)
        cam_ok = self.hand is not None and not self.hand.get()["error"]
        g_lbl = ("AKTIF (Webcam)" if self.gesture_on else "MATI (Pakai Mouse)") if cam_ok else "Kamera Tidak Tersedia"
        self._draw_set_btn(r["gesture_toggle"], g_lbl, GREEN if (cam_ok and self.gesture_on) else MUTED, mx, my)

        # 6. Visual Rute DFS
        self.text("6. Visual Rute Open/Closed AI Antar (DFS)", self.f_midb, TEXT, box.x + 32, y0 + dy * 5 + 7)
        self._draw_set_btn(
            r["dfs_vis_toggle"],
            "TAMPILKAN DI LANTAI (V)" if self.show_overlay else "SEMBUNYIKAN (V)",
            PURPLE if self.show_overlay else MUTED, mx, my
        )

        # Tombol Bawah
        self._draw_set_btn(r["resume"], "Lanjutkan Game (ESC / P)", GREEN, mx, my)
        self._draw_set_btn(r["restart"], "Mulai Ulang Game Baru", BAR, mx, my)
