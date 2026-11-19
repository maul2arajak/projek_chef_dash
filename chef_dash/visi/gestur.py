"""
Kontrol gestur di game: kursor tangan, cubit = klik, cubit+seret bahan ke wajan, panel kamera.
Perbaikan Layout: Panel kamera ditempatkan berdampingan dengan karakter Koki AI (BFS)
di panel kiri bawah dapur sehingga Koki AI dan kamera webcam tampil bersamaan!
"""

import math
import pygame

from ai.koki_bfs import ACTIONS
from core.config import ARM_TIME, BLUE, DROP_RECT, GOLD, GREEN, H, RED, W, WHITE
from core.ui import wrap


class GestureMixin:
    """Kontrol gestur tangan (kursor, cubit, seret ke wajan) + panel kamera berdampingan dengan Koki AI."""

    def gesture_active(self):
        return self.gesture_on and self.hand is not None and self.hand.get()["ok"]

    def pointer(self):
        if self.gesture_active() and self.g_vis and self.scene == "kitchen":
            return int(self.g_pos[0]), int(self.g_pos[1])
        return pygame.mouse.get_pos()

    def update_gesture(self, dt):
        if self.hand is None:
            return
        s = self.hand.get()
        if s["frame"] is not None:
            raw_surf = pygame.image.frombuffer(
                s["frame"].tobytes(),
                (s["frame"].shape[1], s["frame"].shape[0]),
                "RGB"
            )
            self.cam_surf = pygame.transform.smoothscale(raw_surf, (148, 122))
        self.g_clock += dt
        if (not self.gesture_active() or self.scene != "kitchen" or self.trans
                or self.intro or self.over):
            self.drag, self.g_vis, self.g_pinch, self.arm = None, False, False, None
            return
        if not s["hand"]:
            self.g_lost += dt
            if self.g_lost > 0.6:
                self.g_vis, self.g_pinch, self.drag, self.arm = False, False, None, None
            return
        self.g_lost = 0.0
        tx = min(max((s["x"] - 0.12) / 0.76, 0), 1) * W
        ty = min(max((s["y"] - 0.12) / 0.76, 0), 1) * H
        if not self.g_vis:
            self.g_pos = [tx, ty]
        else:
            self.g_pos[0] += (tx - self.g_pos[0]) * 0.45
            self.g_pos[1] += (ty - self.g_pos[1]) * 0.45
        self.g_vis = True
        pos = (int(self.g_pos[0]), int(self.g_pos[1]))
        pinch = s["pinch"]
        if pinch:
            self.pinch_t += dt
        else:
            self.pinch_t = 0.0
        stable = pinch and self.pinch_t >= 0.12
        if stable and not self.g_pinch:
            self.pinch_down(pos)
            self.g_pinch = True
        elif not pinch and self.g_pinch:
            self.pinch_up(pos)
            self.g_pinch = False
            self.arm, self.arm_t, self.arm_lock = None, 0.0, False
        self.update_arm(dt)

    def pinch_down(self, pos):
        if not self.plan:
            for a, b in self.action_buttons.items():
                if b.rect.inflate(12, 12).collidepoint(pos):
                    self.drag = a
                    self.tab = "dish"
                    self.say(f"Seret '{ACTIONS[a].label}' ke wajan, lalu lepas cubitan.", BLUE)
                    return
        for b in self.ctrl_buttons + [self.back_button]:
            if b.rect.collidepoint(pos):
                if not self.arm_lock:
                    self.arm, self.arm_t = b, 0.0
                    self.say("Tahan cubitan di tombol untuk memilih...", BLUE)
                return
        self.click(pos)

    def pinch_up(self, pos):
        if self.drag is None:
            return
        a, self.drag = self.drag, None
        if DROP_RECT.collidepoint(pos):
            self.perform(a)
        else:
            self.say("Lepaskan di atas WAJAN (area tengah) supaya bahan dimasak.", RED)

    def update_arm(self, dt):
        if self.arm is None:
            return
        btn = self.arm
        pos = (int(self.g_pos[0]), int(self.g_pos[1]))
        if not self.g_pinch or not btn.rect.inflate(10, 10).collidepoint(pos):
            self.arm, self.arm_t = None, 0.0
            return
        self.arm_t += dt
        if self.arm_t >= ARM_TIME:
            self.arm, self.arm_t = None, 0.0
            self.arm_lock = True
            self.click(btn.rect.center)

    def draw_gesture(self):
        sc = self.screen
        if self.hand is None or not self.gesture_on:
            return
        s = self.hand.get()
        # Panel kamera di sebelah kanan Koki AI (x=142, y=515, w=154, h=185)
        # zodat Koki AI di sisi kiri (x=25..140) dan kamera webcam tampil berdampingan!
        r = pygame.Rect(142, 515, 154, 185)
        self.panel(r, (30, 25, 22))
        if self.cam_surf is not None and s["ok"]:
            sc.blit(self.cam_surf, self.cam_surf.get_rect(center=(r.centerx, r.y + 84)))
        else:
            for i, ln in enumerate(wrap(s["status"], self.f_small, 140)[:4]):
                self.text(ln, self.f_small, WHITE, r.x + 8, r.y + 26 + i * 16)
        strip = pygame.Surface((r.w - 4, 38), pygame.SRCALPHA)
        strip.fill((0, 0, 0, 180))
        sc.blit(strip, (r.x + 2, r.bottom - 40))
        self.text("Cubit+seret ke wajan", self.f_small, WHITE, r.x + 6, r.bottom - 38)
        self.text("Tahan = Auto BFS", self.f_small, GOLD, r.x + 6, r.bottom - 21)
        self.text("GESTUR " + ("ON" if s["ok"] else "..."), self.f_smallb,
                  GREEN if s["ok"] else GOLD, r.x + 8, r.y + 4)
        if not (s["ok"] and self.g_vis):
            return
        pos = (int(self.g_pos[0]), int(self.g_pos[1]))
        if self.drag is not None:
            pygame.draw.rect(sc, GREEN, DROP_RECT, 4, border_radius=12)
            img = self.f_big.render("LEPAS DI SINI", True, GREEN)
            sc.blit(img, img.get_rect(center=(DROP_RECT.centerx, DROP_RECT.y + 60)))
            b = self.action_buttons[self.drag]
            ghost = pygame.Rect(0, 0, b.rect.w, b.rect.h)
            ghost.center = pos
            pygame.draw.rect(sc, b.color, ghost, border_radius=10)
            pygame.draw.rect(sc, WHITE, ghost, 3, border_radius=10)
            img = self.f_midb.render(b.label, True, WHITE)
            sc.blit(img, img.get_rect(center=ghost.center))
        col = RED if self.g_pinch else (0, 190, 220)
        pygame.draw.circle(sc, WHITE, pos, 17)
        pygame.draw.circle(sc, col, pos, 15, 0 if self.g_pinch else 4)
        if self.arm is not None:
            frac = min(1.0, self.arm_t / ARM_TIME)
            rect = pygame.Rect(0, 0, 54, 54)
            rect.center = pos
            pygame.draw.arc(sc, GOLD, rect, math.pi / 2, math.pi / 2 + 2 * math.pi * max(frac, 0.02), 6)
