"""
SISTEM COLLISION & PATHFINDING ANTI-TEMBUS OBJEK (`core/collision.py`)
Memastikan Pelayan, Pelanggan, dan Asisten AI TIDAK MENEMBUS meja, kursi, maupun konter restoran:
1. `TABLE_COLLIDERS`: Kotak rintangan fisik setiap meja + kursi kiri/kanan.
2. `find_walk_waypoints(start_xy, goal_xy, allow_seat_table=None)`:
   Mencari titik-titik belok (waypoints) di koridor lantai agar karakter berjalan memutari meja & kursi
   secara rapi tanpa pernah memotong/menembus tengah meja atau kursi.
3. `resolve_obstacle_collision(x, y, nx, ny, allow_seat_table=None)`:
   Penjaga fisik (*sliding collision*) per frame yang menggeser posisi karakter di sepanjang tepi luar meja/kursi
   apabila lintasan menyentuh batas meja/kursi.
"""

from collections import deque
import pygame
from core.config import FLOOR_RECT, TABLES

# Kotak collision fisik untuk masing-masing dari 6 set meja + kursi (lebar 196, tinggi 78)
TABLE_COLLIDERS = [
    pygame.Rect(tx - 98, ty - 38, 196, 78)
    for tx, ty in TABLES
]

# Kotak collision meja tengah saja (tanpa kursi samping, dipakai saat pelanggan masuk ke kursi duduknya)
TABLE_CENTER_ONLY = [
    pygame.Rect(tx - 56, ty - 34, 112, 68)
    for tx, ty in TABLES
]

# Batas atas konter restoran agar tidak ditembus
COUNTER_COLLIDER = pygame.Rect(225, 64, 710, 124)

NAV_CELL = 20
NAV_COLS = 1180 // NAV_CELL
NAV_ROWS = 720 // NAV_CELL


def is_point_blocked(px: float, py: float, allow_seat_table: int = None, margin: int = 8) -> bool:
    """Mengecek apakah titik `(px, py)` berada di dalam area meja, kursi, atau konter."""
    ix, iy = int(px), int(py)
    if COUNTER_COLLIDER.inflate(margin, margin).collidepoint(ix, iy):
        return True
    for idx, rect in enumerate(TABLE_COLLIDERS):
        if allow_seat_table is not None and idx == allow_seat_table:
            # Jika pelanggan sedang menuju/keluar kursi di meja `allow_seat_table`,
            # kursi boleh dimasuki tetapi badan meja tengah tetap tidak boleh ditembus!
            if TABLE_CENTER_ONLY[idx].inflate(margin, margin).collidepoint(ix, iy):
                return True
        else:
            if rect.inflate(margin, margin).collidepoint(ix, iy):
                return True
    return False


def find_walk_waypoints(start_xy: tuple, goal_xy: tuple, allow_seat_table: int = None) -> list:
    """
    Mencari rute waypoints di koridor lantai restoran agar karakter (Pelayan / Pelanggan)
    berjalan memutari meja & kursi tanpa menembus objek.
    """
    sx, sy = float(start_xy[0]), float(start_xy[1])
    gx, gy = float(goal_xy[0]), float(goal_xy[1])

    # Cek apakah garis lurus dari start ke goal bebas dari rintangan meja/kursi
    steps_check = max(1, int(((gx - sx) ** 2 + (gy - sy) ** 2) ** 0.5 // 10))
    clear_line = True
    for k in range(1, steps_check):
        t = k / steps_check
        px = sx + (gx - sx) * t
        py = sy + (gy - sy) * t
        if is_point_blocked(px, py, allow_seat_table=allow_seat_table, margin=10):
            clear_line = False
            break
    if clear_line:
        return [(gx, gy)]

    # Jika garis lurus terhalang meja/kursi, cari rute koridor dengan grid navigasi
    def to_cell(x, y):
        c = max(0, min(NAV_COLS - 1, int(x // NAV_CELL)))
        r = max(3, min(NAV_ROWS - 1, int(y // NAV_CELL)))
        return (c, r)

    def to_xy(cell):
        return (cell[0] * NAV_CELL + NAV_CELL // 2, cell[1] * NAV_CELL + NAV_CELL // 2)

    s_cell = to_cell(sx, sy)
    g_cell = to_cell(gx, gy)

    q = deque([s_cell])
    parent = {s_cell: None}
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)]

    found = None
    while q:
        cur = q.popleft()
        if cur == g_cell:
            found = cur
            break
        cx, cy = cur
        for dc, dr in dirs:
            nc, nr = cx + dc, cy + dr
            nxt = (nc, nr)
            if 0 <= nc < NAV_COLS and 9 <= nr < NAV_ROWS - 1 and nxt not in parent:
                px, py = to_xy(nxt)
                if nxt == g_cell or not is_point_blocked(px, py, allow_seat_table=allow_seat_table, margin=10):
                    parent[nxt] = cur
                    q.append(nxt)

    if found is None:
        # Fallback: berjalan lewat koridor horizontal aman (y=235 atau y=440 atau y=645)
        corridors = [235.0, 440.0, 645.0]
        best_cy = min(corridors, key=lambda cy_val: abs(sy - cy_val) + abs(gy - cy_val))
        return [(sx, best_cy), (gx, best_cy), (gx, gy)]

    raw_cells = []
    cur = found
    while cur is not None:
        raw_cells.append(cur)
        cur = parent[cur]
    raw_cells.reverse()

    pts = [to_xy(c) for c in raw_cells[1:]]
    if not pts:
        return [(gx, gy)]
    pts[-1] = (gx, gy)

    # Sederhanakan waypoints (string-pulling) agar gerakan karakter mulus & tidak patah-patah
    simplified = [pts[0]]
    cur_anchor = (sx, sy)
    for i in range(1, len(pts)):
        cand = pts[i]
        dist_steps = max(1, int(((cand[0] - cur_anchor[0]) ** 2 + (cand[1] - cur_anchor[1]) ** 2) ** 0.5 // 10))
        ok = True
        for k in range(1, dist_steps):
            t = k / dist_steps
            px = cur_anchor[0] + (cand[0] - cur_anchor[0]) * t
            py = cur_anchor[1] + (cand[1] - cur_anchor[1]) * t
            if is_point_blocked(px, py, allow_seat_table=allow_seat_table, margin=8):
                ok = False
                break
        if ok:
            simplified[-1] = cand
        else:
            cur_anchor = simplified[-1]
            simplified.append(cand)

    return simplified


def resolve_obstacle_collision(old_x: float, old_y: float, new_x: float, new_y: float, allow_seat_table: int = None) -> tuple:
    """
    Sliding Collision Resolver:
    Jika posisi `(new_x, new_y)` menabrak meja/kursi, coba geser di sumbu X saja atau sumbu Y saja,
    atau dorong keluar ke tepi terdekat agar karakter tidak pernah menembus meja/kursi.
    """
    if not is_point_blocked(new_x, new_y, allow_seat_table=allow_seat_table, margin=4):
        return new_x, new_y
    if not is_point_blocked(new_x, old_y, allow_seat_table=allow_seat_table, margin=4):
        return new_x, old_y
    if not is_point_blocked(old_x, new_y, allow_seat_table=allow_seat_table, margin=4):
        return old_x, new_y
    return old_x, old_y
