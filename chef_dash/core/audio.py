"""
MANAJER AUDIO & MUSIK LATAR (`core/audio.py`)
Mengelola 2 musik latar (BGM) yang berbeda sesuai ruangan:
1. `bgm_restoran.wav` : Musik Bossa Nova / Cafe Jazz saat berada di LUAR DAPUR (Mode Restoran).
2. `bgm_dapur.wav`    : Musik Upbeat Cooking Arcade saat berada di DALAM DAPUR (Mode Dapur).
Juga mengelola efek suara (SFX): klik, masak berhasil, sajikan/antar, dan salah urutan.
"""

import os
import pygame

AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "audio")


class AudioManager:
    """Mengelola pemutaran 2 BGM berbeda (Restoran vs Dapur) dan SFX dengan kontrol volume."""

    def __init__(self):
        self.ready = False
        self.bgm_enabled = True
        self.sfx_enabled = True
        self.bgm_volume = 0.55
        self.sfx_volume = 0.70
        self.current_track = None
        self.bgm_sounds = {}
        self.sfx_sounds = {}
        self.bgm_channel = None
        self._init_mixer()

    def _init_mixer(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=1024)
            self.bgm_channel = pygame.mixer.Channel(0)
            for key, fname in [("floor", "bgm_restoran.wav"), ("kitchen", "bgm_dapur.wav")]:
                p = os.path.join(AUDIO_DIR, fname)
                if os.path.exists(p):
                    self.bgm_sounds[key] = pygame.mixer.Sound(p)
            for key, fname in [
                ("click", "sfx_click.wav"),
                ("cook", "sfx_cook.wav"),
                ("serve", "sfx_serve.wav"),
                ("error", "sfx_error.wav"),
            ]:
                p = os.path.join(AUDIO_DIR, fname)
                if os.path.exists(p):
                    self.sfx_sounds[key] = pygame.mixer.Sound(p)
            self.ready = True
        except Exception:
            self.ready = False

    def switch_bgm(self, scene_name: str):
        """
        Mengganti musik latar secara otomatis:
        - `floor` (Luar Dapur / Mode Restoran) -> memutar `bgm_restoran.wav`
        - `kitchen` (Dalam Dapur / Mode Dapur) -> memutar `bgm_dapur.wav`
        """
        if not self.ready or self.bgm_channel is None:
            return
        if not self.bgm_enabled:
            self.bgm_channel.stop()
            self.current_track = None
            return
        if self.current_track == scene_name and self.bgm_channel.get_busy():
            return
        snd = self.bgm_sounds.get(scene_name)
        if snd is not None:
            self.bgm_channel.stop()
            snd.set_volume(self.bgm_volume)
            self.bgm_channel.play(snd, loops=-1)
            self.current_track = scene_name

    def set_bgm_volume(self, vol: float):
        self.bgm_volume = max(0.0, min(1.0, round(float(vol), 2)))
        if self.ready and self.bgm_channel is not None:
            self.bgm_channel.set_volume(self.bgm_volume if self.bgm_enabled else 0.0)
            for snd in self.bgm_sounds.values():
                snd.set_volume(self.bgm_volume if self.bgm_enabled else 0.0)

    def set_sfx_volume(self, vol: float):
        self.sfx_volume = max(0.0, min(1.0, round(float(vol), 2)))

    def toggle_bgm(self, active_scene: str):
        self.bgm_enabled = not self.bgm_enabled
        if not self.bgm_enabled and self.ready and self.bgm_channel is not None:
            self.bgm_channel.stop()
            self.current_track = None
        else:
            self.switch_bgm(active_scene)

    def toggle_sfx(self):
        self.sfx_enabled = not self.sfx_enabled

    def play_sfx(self, name: str):
        if not self.ready or not self.sfx_enabled:
            return
        snd = self.sfx_sounds.get(name)
        if snd is not None:
            try:
                snd.set_volume(self.sfx_volume)
                snd.play()
            except Exception:
                pass
