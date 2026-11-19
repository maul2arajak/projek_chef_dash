"""Konstanta layar, warna, dan data tata letak restoran."""


import random

import pygame


W, H = 1180, 720
DROP_RECT = pygame.Rect(310, 325, 460, 380)     # area wajan tempat bahan dilepas
CUSTOMER_PATIENCE = 10 * 60.0                    # detik kesabaran pelanggan (10 menit)
ARM_TIME = 0.6                                   # detik menahan cubitan di tombol Auto/Ulang/Kembali
FPS = 60

BG = (255, 241, 214)
BAR = (176, 58, 46)
PANEL = (255, 250, 240)
BORDER = (120, 85, 60)
TEXT = (60, 40, 30)
MUTED = (140, 115, 95)
GREEN = (60, 160, 90)
RED = (200, 50, 50)
BLUE = (50, 100, 180)
PURPLE = (130, 80, 170)
GOLD = (240, 190, 40)
WHITE = (255, 255, 255)



# ====================================================================
# DATA RESTORAN
# ====================================================================
TABLE_XS = [400, 660, 920]
TABLE_YS = [335, 545]
TABLES = [(x, y) for y in TABLE_YS for x in TABLE_XS]        # 6 meja
QUEUE_SLOTS = [(80, 285 + i * 105) for i in range(4)]
EXIT_X = -90
COOK_POINT = (390, 225)
PICKUP_POINT = (760, 225)
COOK_RECT = pygame.Rect(240, 72, 300, 108)
PICKUP_RECT = pygame.Rect(560, 72, 360, 108)
FLOOR_RECT = pygame.Rect(150, 215, 1000, 460)       # area jalan pelayan
SHIRTS = [(220, 90, 90), (90, 150, 220), (110, 190, 120), (230, 160, 70), (170, 110, 200), (90, 190, 190)]
HAIRS = [(50, 35, 30), (90, 60, 40), (30, 30, 40), (200, 160, 80), (150, 60, 50)]
SKINS = [(245, 205, 170), (225, 175, 130), (190, 140, 100), (250, 220, 190)]

_rng = random.Random(5)
DISH_PTS = [(_rng.uniform(-1, 1), _rng.uniform(-1, 1)) for _ in range(120)]
DISH_PTS = [(x, y) for x, y in DISH_PTS if x * x + y * y <= 1][:60]
