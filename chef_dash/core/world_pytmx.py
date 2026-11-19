"""
WORLD BUILDING DENGAN PYTMX (`core/world_pytmx.py`)
Mengimpor `pytmx` (`from pytmx.util_pygame import load_pygame`) untuk memuat dan me-render
peta dunia Tiled `.tmx` (`assets/maps/restoran.tmx` dan `assets/maps/dapur.tmx`).
Dilengkapi pula dengan parser TMX XML internal berbasis `xml.etree.ElementTree` + `pygame`
sehingga peta `.tmx` tetap ter-render 100% identik meskipun pengguna belum menginstal paket `pytmx`.
"""

import os
import xml.etree.ElementTree as ET
import pygame

try:
    import pytmx
    from pytmx.util_pygame import load_pygame as pytmx_load_pygame
    HAS_PYTMX = True
except ImportError:
    pytmx = None
    pytmx_load_pygame = None
    HAS_PYTMX = False


class TiledWorldMap:
    """
    Membaca dan me-render file peta `.tmx` (Tiled Map Editor) ke layar Pygame
    menggunakan `pytmx` (atau parser TMX fallback jika modul `pytmx` belum terpasang).
    """

    def __init__(self, tmx_path: str):
        self.tmx_path = tmx_path
        self.tmx_data = None
        self.fallback_tiles = {}     # gid -> pygame.Surface
        self.fallback_grid = []      # list of list of gid
        self.tile_w = 40
        self.tile_h = 40
        self.cols = 30
        self.rows = 18
        self.zones = {}              # name -> pygame.Rect
        self._cached_surface = None
        self._load_map()

    def _load_map(self) -> None:
        if not os.path.exists(self.tmx_path):
            return

        # 1. Gunakan pytmx jika tersedia
        if HAS_PYTMX and pytmx_load_pygame is not None:
            try:
                self.tmx_data = pytmx_load_pygame(self.tmx_path, pixelalpha=True)
                self.tile_w = self.tmx_data.tilewidth
                self.tile_h = self.tmx_data.tileheight
                self.cols = self.tmx_data.width
                self.rows = self.tmx_data.height
                for obj in self.tmx_data.objects:
                    if getattr(obj, "name", None):
                        self.zones[obj.name] = pygame.Rect(int(obj.x), int(obj.y), int(obj.width), int(obj.height))
                return
            except Exception:
                self.tmx_data = None

        # 2. Parser TMX XML terintegrasi (membaca file .tmx & tileset PNG yang sama)
        tree = ET.parse(self.tmx_path)
        root = tree.getroot()
        self.tile_w = int(root.attrib.get("tilewidth", 40))
        self.tile_h = int(root.attrib.get("tileheight", 40))
        self.cols = int(root.attrib.get("width", 30))
        self.rows = int(root.attrib.get("height", 18))

        map_dir = os.path.dirname(self.tmx_path)
        for ts in root.findall("tileset"):
            firstgid = int(ts.attrib.get("firstgid", 1))
            tw = int(ts.attrib.get("tilewidth", self.tile_w))
            th = int(ts.attrib.get("tileheight", self.tile_h))
            columns = int(ts.attrib.get("columns", 8))
            tilecount = int(ts.attrib.get("tilecount", 8))
            img_node = ts.find("image")
            if img_node is not None:
                img_path = os.path.join(map_dir, img_node.attrib["source"])
                if os.path.exists(img_path):
                    sheet = pygame.image.load(img_path).convert_alpha()
                    for idx in range(tilecount):
                        c = idx % columns
                        r = idx // columns
                        sub = pygame.Surface((tw, th), pygame.SRCALPHA)
                        sub.blit(sheet, (0, 0), pygame.Rect(c * tw, r * th, tw, th))
                        self.fallback_tiles[firstgid + idx] = sub

        layer = root.find("layer")
        if layer is not None:
            data_node = layer.find("data")
            if data_node is not None and data_node.text:
                lines = [ln.strip() for ln in data_node.text.strip().splitlines() if ln.strip()]
                for ln in lines:
                    row_gids = [int(v) for v in ln.split(",") if v.strip()]
                    self.fallback_grid.append(row_gids)

        for objgroup in root.findall("objectgroup"):
            for obj in objgroup.findall("object"):
                name = obj.attrib.get("name")
                if name:
                    x = int(float(obj.attrib.get("x", 0)))
                    y = int(float(obj.attrib.get("y", 0)))
                    w = int(float(obj.attrib.get("width", 0)))
                    h = int(float(obj.attrib.get("height", 0)))
                    self.zones[name] = pygame.Rect(x, y, w, h)

    def render(self, surface) -> None:
        """Me-render seluruh tile layer dari peta `.tmx` ke surface Pygame."""
        if self._cached_surface is None:
            w = self.cols * self.tile_w
            h = self.rows * self.tile_h
            cache = pygame.Surface((w, h), pygame.SRCALPHA)
            if self.tmx_data is not None and HAS_PYTMX:
                for layer in self.tmx_data.visible_layers:
                    if hasattr(layer, "tiles"):
                        for x, y, image in layer.tiles():
                            if image is not None:
                                cache.blit(image, (x * self.tile_w, y * self.tile_h))
            else:
                for r_idx, row in enumerate(self.fallback_grid):
                    for c_idx, gid in enumerate(row):
                        tile_surf = self.fallback_tiles.get(gid)
                        if tile_surf is not None:
                            cache.blit(tile_surf, (c_idx * self.tile_w, r_idx * self.tile_h))
            self._cached_surface = cache

        surface.blit(self._cached_surface, (0, 0))
