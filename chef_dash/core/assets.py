"""
Manajer Aset Gambar & Peta PyTMX (AssetManager)
Memuat seluruh sprite PNG pre-rendered dari folder `assets/`:
- Karakter 5-frame x 4-arah (`depan_0..4`, `belakang_0..4`, `kiri_0..4`, `kanan_0..4`):
  * `waitress` (Pelayan)
  * `ai_assistant` (Asisten AI Pengantar Makanan - DFS)
  * `ai_chef` (Koki AI Full-Body Berjalan - BFS)
  * `customer_0`, `customer_1`, `customer_2` (Pelanggan + pose duduk & ekspresi)
- Koki Dapur Portrait 5-Frame (`chef_normal_0..4`, `chef_happy_0..4`, `chef_sad_0..4`)
- Aset Masakan & Bumbu di Wajan (`assets/cooking/`):
  * `wajan_masak`, `piring_saji_besar`, `beras_0..3`, `bawang_0..2`, `telur_0..2`,
    `bumbu_garam`, `bumbu_kecap`, `garnish_sajian`
- Ikon Bahan Bergambar Asli (`assets/items/icon_0..5`), Piring Nasi Goreng, Hati Reputasi, Meja Restoran
- Peta Dunia PyTMX (`assets/maps/restoran.tmx` & `dapur.tmx`).
"""

import os
import pygame
from core.world_pytmx import TiledWorldMap

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


class AssetManager:
    """Mengelola pemuatan dan caching seluruh aset gambar PNG 5-frame, bahan masakan, dan peta PyTMX."""

    DIRECTIONS = ("depan", "belakang", "kiri", "kanan")
    MOODS = ("happy", "neutral", "angry", "eat")
    TOTAL_FRAMES = 5

    def __init__(self):
        self.char_sprites = {}      # (folder, direction, frame_idx) -> Surface
        self.customer_poses = {}    # (folder, 'duduk'/'berdiri', mood) -> Surface
        self.chef_sprites = {}      # (mood, frame_idx) -> Surface
        self.items = {}             # name -> Surface
        self.cooking = {}           # name -> Surface
        self.tiles = {}             # name -> Surface
        self.maps = {}              # 'restoran' / 'dapur' -> TiledWorldMap
        self.loaded = False

    def load_all(self):
        """Memuat seluruh file PNG 5-frame, aset bahan/nasi goreng, dan peta PyTMX dari `assets/`."""
        if self.loaded:
            return

        # 1. Karakter 4 arah x 5 frame (waitress, ai_assistant, ai_chef, customer_0..2)
        char_folders = ["waitress", "ai_assistant", "ai_chef", "customer_0", "customer_1", "customer_2"]
        for folder in char_folders:
            for d_name in self.DIRECTIONS:
                for f_idx in range(self.TOTAL_FRAMES):
                    path = os.path.join(ASSETS_DIR, "characters", folder, f"{d_name}_{f_idx}.png")
                    if os.path.exists(path):
                        self.char_sprites[(folder, d_name, f_idx)] = pygame.image.load(path).convert_alpha()

        # 2. Pose duduk & berdiri pelanggan berdasarkan ekspresi wajah
        for c_idx in range(3):
            folder = f"customer_{c_idx}"
            for pose in ("duduk", "berdiri"):
                for mood in self.MOODS:
                    path = os.path.join(ASSETS_DIR, "characters", folder, f"{pose}_{mood}.png")
                    if os.path.exists(path):
                        self.customer_poses[(folder, pose, mood)] = pygame.image.load(path).convert_alpha()

        # 3. Portrait Koki Dapur (3 mood x 5 frame)
        for mood in ("normal", "happy", "sad"):
            for f_idx in range(self.TOTAL_FRAMES):
                path = os.path.join(ASSETS_DIR, "characters", "chef", f"chef_{mood}_{f_idx}.png")
                if os.path.exists(path):
                    self.chef_sprites[(mood, f_idx)] = pygame.image.load(path).convert_alpha()

        # 4. Item & Ikon Kartu Bahan
        items_dir = os.path.join(ASSETS_DIR, "items")
        if os.path.isdir(items_dir):
            for fname in os.listdir(items_dir):
                if fname.endswith(".png"):
                    key = os.path.splitext(fname)[0]
                    self.items[key] = pygame.image.load(os.path.join(items_dir, fname)).convert_alpha()

        # 5. Aset Tahap Memasak, Bumbu, Wajan & Nasi Goreng
        cook_dir = os.path.join(ASSETS_DIR, "cooking")
        if os.path.isdir(cook_dir):
            for fname in os.listdir(cook_dir):
                if fname.endswith(".png"):
                    key = os.path.splitext(fname)[0]
                    self.cooking[key] = pygame.image.load(os.path.join(cook_dir, fname)).convert_alpha()

        # 6. Tile & Furnitur
        tiles_dir = os.path.join(ASSETS_DIR, "tiles")
        if os.path.isdir(tiles_dir):
            for fname in os.listdir(tiles_dir):
                if fname.endswith(".png"):
                    key = os.path.splitext(fname)[0]
                    self.tiles[key] = pygame.image.load(os.path.join(tiles_dir, fname)).convert_alpha()

        # 7. Peta Dunia PyTMX (.tmx)
        maps_dir = os.path.join(ASSETS_DIR, "maps")
        for mname in ("restoran", "dapur"):
            tmx_path = os.path.join(maps_dir, f"{mname}.tmx")
            if os.path.exists(tmx_path):
                self.maps[mname] = TiledWorldMap(tmx_path)

        self.loaded = True

    def get_char_sprite(self, folder: str, direction: str, frame_idx: int):
        return self.char_sprites.get((folder, direction, frame_idx % self.TOTAL_FRAMES))

    def get_customer_pose(self, folder: str, sitting: bool, mood: str):
        pose = "duduk" if sitting else "berdiri"
        return self.customer_poses.get((folder, pose, mood))

    def get_chef_sprite(self, mood: str, frame_idx: int):
        return self.chef_sprites.get((mood, frame_idx % self.TOTAL_FRAMES))
