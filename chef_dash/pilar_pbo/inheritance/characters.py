"""
PILAR PBO 3: INHERITANCE (Pewarisan Karakter Beranimasi 5-Frame + Anti-Tembus Meja/Kursi)
Class Induk `AnimatedCharacter` mewariskan atribut posisi, antrean waypoints anti-tembus (`waypoints`),
deteksi arah 4-mata angin (`depan`, `belakang`, `kiri`, `kanan`), dan siklus 5-frame jalan (`0, 1, 2, 3, 4`)
kepada Class Anak:
- `WaitressCharacter` (Pelayan Restoran)
- `AIAssistantCharacter` (Asisten Pengantar Makanan AI - DFS)
- `CustomerCharacter` (Pelanggan Restoran)
- `ChefCharacter` (Koki AI Dapur - Portrait & Full-Body Walker 5-Frame)
"""

import math
import random
from pilar_pbo.abstraction.base_entity import AbstractAnimatedEntity
from core.config import HAIRS, SHIRTS, SKINS
from core.collision import find_walk_waypoints, resolve_obstacle_collision


class AnimatedCharacter(AbstractAnimatedEntity):
    """
    Class Induk (Parent/Superclass) untuk semua karakter bergerak 5-frame.
    Dilengkapi dengan `set_route()` dan `waypoints` agar selalu berjalan memutari meja & kursi
    (tidak menembus objek).
    """

    FRAME_DURATION = 0.095

    def __init__(self, x: float, y: float, sprite_folder: str = "waitress"):
        self.x = float(x)
        self.y = float(y)
        self.tx = float(x)
        self.ty = float(y)
        self.waypoints = []
        self.allow_seat_table = None
        self.use_collision = True
        self.walking = False
        self.direction = "depan"
        self.frame_index = 0
        self._anim_timer = 0.0
        self.sprite_folder = sprite_folder

        self.shirt = random.choice(SHIRTS)
        self.hair = random.choice(HAIRS)
        self.skin = random.choice(SKINS)

    def set_route(self, dest_x: float, dest_y: float, allow_seat_table: int = None) -> None:
        """Menghitung rute waypoints bebas tembus meja/kursi menuju `(dest_x, dest_y)`."""
        self.allow_seat_table = allow_seat_table
        self.waypoints = find_walk_waypoints((self.x, self.y), (dest_x, dest_y), allow_seat_table=allow_seat_table)
        if self.waypoints:
            self.tx, self.ty = self.waypoints[0]
        else:
            self.tx, self.ty = float(dest_x), float(dest_y)

    def _update_direction(self, dx: float, dy: float) -> None:
        if abs(dx) < 1e-4 and abs(dy) < 1e-4:
            return
        if abs(dx) > abs(dy) * 0.95:
            self.direction = "kanan" if dx > 0 else "kiri"
        else:
            self.direction = "depan" if dy >= 0 else "belakang"

    def step(self, dt: float, speed: float) -> bool:
        """
        Memindahkan karakter mengikuti `waypoints` menuju `(tx, ty)` tanpa menembus meja/kursi,
        serta memperbarui siklus 5-frame jalan (`0..4`).
        """
        if self.waypoints:
            self.tx, self.ty = self.waypoints[0]

        dx = self.tx - self.x
        dy = self.ty - self.y
        d = math.hypot(dx, dy)
        if d <= speed * dt:
            self.x, self.y = self.tx, self.ty
            if self.waypoints:
                self.waypoints.pop(0)
                if self.waypoints:
                    self.tx, self.ty = self.waypoints[0]
                    return False
            self.walking = False
            self.frame_index = 0
            self._anim_timer = 0.0
            return True

        self._update_direction(dx, dy)
        nx = self.x + (dx / d) * speed * dt
        ny = self.y + (dy / d) * speed * dt
        if self.use_collision:
            nx, ny = resolve_obstacle_collision(self.x, self.y, nx, ny, allow_seat_table=self.allow_seat_table)
        self.x, self.y = nx, ny

        if not self.walking:
            self.walking = True
            self.frame_index = 1

        self._anim_timer += dt
        if self._anim_timer >= self.FRAME_DURATION:
            self._anim_timer %= self.FRAME_DURATION
            self.frame_index = (self.frame_index + 1) % self.TOTAL_FRAMES
        return False

    def get_sprite_key(self) -> tuple:
        f_idx = self.frame_index if self.walking else 0
        return (self.sprite_folder, self.direction, f_idx)

    def render(self, surface, asset_manager, **kwargs) -> int:
        folder, direction, f_idx = self.get_sprite_key()
        sprite = asset_manager.get_char_sprite(folder, direction, f_idx)
        ix, iy = int(self.x), int(self.y)
        if sprite is not None:
            rect = sprite.get_rect(midbottom=(ix, iy + 8))
            surface.blit(sprite, rect)
        return iy - 94


class WaitressCharacter(AnimatedCharacter):
    """Class Anak 1 (Subclass): Pelayan Restoran (5-frame x 4-arah + anti-tembus meja/kursi)."""

    def __init__(self, x: float, y: float):
        super().__init__(x, y, sprite_folder="waitress")
        self.shirt = (70, 130, 210)
        self.hair = (115, 65, 35)
        self.skin = (248, 210, 175)
        self.role_label = "Pelayan"


class AIAssistantCharacter(AnimatedCharacter):
    """Class Anak 2 (Subclass): Asisten Pengantar Makanan AI (DFS) dengan 5-frame x 4-arah."""

    def __init__(self, x: float, y: float):
        super().__init__(x, y, sprite_folder="ai_assistant")
        self.shirt = (55, 168, 105)
        self.hair = (35, 35, 45)
        self.skin = (230, 182, 140)
        self.role_label = "AI-DFS"

    def render(self, surface, asset_manager, font_badge=None, badge_color=(130, 80, 170), **kwargs) -> int:
        hy = super().render(surface, asset_manager, **kwargs)
        if font_badge is not None:
            img = font_badge.render(self.role_label, True, badge_color)
            surface.blit(img, (int(self.x) - img.get_width() // 2, hy - 18))
        return hy


class CustomerCharacter(AnimatedCharacter):
    """Class Anak 3 (Subclass): Pelanggan Restoran (5-frame x 4-arah + anti-tembus meja/kursi)."""

    PRESETS = [
        dict(shirt=(225, 85, 85), hair=(55, 38, 30), skin=(248, 210, 175)),
        dict(shirt=(235, 160, 65), hair=(95, 62, 40), skin=(230, 182, 140)),
        dict(shirt=(165, 105, 205), hair=(35, 35, 48), skin=(252, 222, 192)),
    ]

    def __init__(self, x: float, y: float, variant: int = None):
        if variant is None:
            variant = random.randint(0, 2)
        self.variant = variant % 3
        super().__init__(x, y, sprite_folder=f"customer_{self.variant}")
        preset = self.PRESETS[self.variant]
        self.shirt = preset["shirt"]
        self.hair = preset["hair"]
        self.skin = preset["skin"]

    def render(self, surface, asset_manager, face: str = "happy", sitting: bool = False, **kwargs) -> int:
        ix, iy = int(self.x), int(self.y)
        if sitting:
            sprite = asset_manager.get_customer_pose(self.sprite_folder, sitting=True, mood=face)
            hy_offset = 76
        elif not self.walking and self.direction == "depan":
            sprite = asset_manager.get_customer_pose(self.sprite_folder, sitting=False, mood=face)
            hy_offset = 94
        else:
            sprite = asset_manager.get_char_sprite(self.sprite_folder, self.direction, self.frame_index)
            hy_offset = 94

        if sprite is not None:
            rect = sprite.get_rect(midbottom=(ix, iy + 8))
            surface.blit(sprite, rect)
        return iy - hy_offset


class ChefCharacter(AnimatedCharacter):
    """Class Anak 4 (Subclass): Koki AI Dapur (BFS) Portrait 5-Frame + Full-Body Walker 5-Frame."""

    PATROL_POINTS = [(345, 300), (480, 300), (610, 300), (735, 300)]

    def __init__(self, x: float = 92, y: float = 612):
        super().__init__(x, y, sprite_folder="ai_chef")
        self.use_collision = False
        self.mood = "normal"
        self.w_target_idx = 1
        self.walker = AnimatedCharacter(345.0, 222.0, sprite_folder="ai_chef")
        self.walker.use_collision = False

    def update_idle_anim(self, dt: float, active_cooking: bool = False) -> None:
        self._anim_timer += dt
        interval = 0.10 if active_cooking else 0.18
        if self._anim_timer >= interval:
            self._anim_timer %= interval
            self.frame_index = (self.frame_index + 1) % self.TOTAL_FRAMES

        tx, _ = self.PATROL_POINTS[self.w_target_idx]
        self.walker.tx, self.walker.ty = float(tx), self.walker.y
        spd = 175.0 if active_cooking else 85.0
        if self.walker.step(dt, spd):
            self.w_target_idx = (self.w_target_idx + 1) % len(self.PATROL_POINTS)

    def render(self, surface, asset_manager, mood: str = "normal", scale_size=None, **kwargs) -> int:
        self.mood = mood if mood in ("normal", "happy", "sad") else "normal"
        sprite = asset_manager.get_chef_sprite(self.mood, self.frame_index)
        ix, iy = int(self.x), int(self.y)
        if sprite is not None:
            if scale_size is not None:
                import pygame
                sprite = pygame.transform.smoothscale(sprite, scale_size)
            rect = sprite.get_rect(center=(ix, iy))
            surface.blit(sprite, rect)
        return iy - 70
