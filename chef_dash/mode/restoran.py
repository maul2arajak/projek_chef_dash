"""
MODE RESTORAN - kamu jadi PELAYAN: antrean, duduk, catat pesanan, ambil & antar piring.
Terintegrasi dengan:
- World Building PyTMX (`assets/maps/restoran.tmx`)
- 4 Pilar PBO (`AbstractGameMode`, `WaitressCharacter`, `AIAssistantCharacter`, `CustomerCharacter`)
- Aset sprite PNG 5-frame untuk jalan depan, belakang, kiri, kanan (utuh tidak terpotong).
- AI Pengantar Makanan (DFS).
"""

import random
import pygame

from ai.koki_bfs import AI_STEP_PENALTY, BAWANG, BERAS, GARAM, KECAP, TELUR
from ai.pengantar_dfs import ASSIST_EXTRA_PENALTY, ASSIST_FEE
from core.config import (
    BAR, BLUE, BORDER, COOK_POINT, COOK_RECT, CUSTOMER_PATIENCE, EXIT_X,
    FLOOR_RECT, GOLD, GREEN, H, MUTED, PANEL, PICKUP_POINT, PICKUP_RECT,
    PURPLE, QUEUE_SLOTS, RED, TABLES, TEXT, W, WHITE
)
from core.ui import Party, fmt_time
from pilar_pbo.abstraction.base_mode import AbstractGameMode
from pilar_pbo.polymorphism.render_polymorphism import render_entity_polymorphic


class RestoranMode(AbstractGameMode):
    """Logika dan tampilan mode restoran (implementasi AbstractGameMode)."""

    def handle_click(self, pos: tuple) -> None:
        self.click_floor(pos)

    def render_mode(self) -> None:
        self.draw_floor()

    def queue_list(self):
        return [p for p in self.parties if p.state == "queue"]

    def spawn_party(self):
        if len(self.queue_list()) >= len(QUEUE_SLOTS):
            return
        size = random.choice([1, 2, 2])
        order = dict(egg=random.random() < 0.6, kecap=random.random() < 0.5)
        pmax = CUSTOMER_PATIENCE
        self.parties.append(Party(size, order, pmax))

    def table_seats(self, ti, size):
        tx, ty = TABLES[ti]
        if size == 2:
            return [(tx - 78, ty + 12), (tx + 78, ty + 12)]
        return [random.choice([(tx - 78, ty + 12), (tx + 78, ty + 12)])]

    def purge_party(self, p):
        self.tickets = [t for t in self.tickets if t["party"] is not p]
        self.counter = [c for c in self.counter if c["party"] is not p]
        self.carry = [c for c in self.carry if c["party"] is not p]
        if self.sel_ticket and self.sel_ticket["party"] is p:
            self.sel_ticket = None
            self.order = None
            self.reset_state()
        if self.sel_party is p:
            self.sel_party = None

    def anger(self, p):
        p.angry = True
        self.rep -= 1
        mx = sum(m.x for m in p.members) / len(p.members)
        my = min(m.y for m in p.members) - 110
        self.popups.append(dict(text="Pelanggan marah!", x=mx, y=my, t=1.8, col=RED))
        self.say("Pelanggan pergi karena kelamaan menunggu! Reputasi -1", RED)
        self.leave(p)

    def leave(self, p):
        if p.table is not None:
            self.tables[p.table] = None
        self.purge_party(p)
        p.state = "leaving"
        for m in p.members:
            m.set_route(EXIT_X, max(240, min(620, m.y)), allow_seat_table=p.table)

    def set_task(self, kind, dest, **kw):
        dest = (dest[0], dest[1])
        self.task = dict(kind=kind, dest=dest, **kw)
        self.waitress.set_route(dest[0], dest[1], allow_seat_table=None)

    def arrive(self, task):
        kind = task["kind"]
        if kind == "order":
            p = task["party"]
            if p.state == "ready" and p in self.parties:
                p.state = "waitfood"
                self.tickets.append(dict(party=p))
                self.say(f"Pesanan Meja {p.table + 1} dicatat. Klik PINTU DAPUR untuk memasak.", BLUE)
                self.popups.append(dict(text="Pesanan dicatat", x=TABLES[p.table][0], y=TABLES[p.table][1] - 110,
                                        t=1.3, col=BLUE))
        elif kind == "deliver":
            p = task["party"]
            if p.state != "waitfood":
                return
            plate = next((c for c in self.carry if c["party"] is p), None)
            if plate is None:
                self.say(f"Kamu belum membawa piring untuk Meja {p.table + 1}.", RED)
                return
            self.carry.remove(plate)
            self.deliver(p, plate)
        elif kind == "pickup":
            n = 0
            while self.counter and len(self.carry) < 2:
                self.carry.append(self.counter.pop(0))
                n += 1
            if n:
                self.say(f"Mengambil {n} piring. Antar ke meja yang memesan!", GREEN)
            elif len(self.carry) >= 2:
                self.say("Tangan penuh! Antar dulu piring yang dibawa.", RED)
            else:
                self.say("Belum ada piring siap di meja saji.", MUTED)
        elif kind == "cook":
            if self.tickets:
                self.go("kitchen")
            else:
                self.say("Belum ada tiket. Ambil pesanan dari meja pelanggan dulu.", RED)

    def deliver(self, p, plate, assist=None):
        frac = max(0.0, p.p) / p.pmax
        tip = int(30 * frac)
        pay = 50 + tip
        over = max(0, plate["steps"] - plate["par"])
        pen = 0
        if plate["used_ai"]:
            pen = AI_STEP_PENALTY * over
            pay = max(10, pay // 2 - pen)
        else:
            pay = max(10, pay - 5 * max(0, plate["steps"] - plate["par"]) - 8 * plate["mistakes"])
        fee = 0
        if assist is not None:
            fee = int(ASSIST_FEE + ASSIST_EXTRA_PENALTY * assist["extra"])
            pay = max(10, pay - fee)
        self.money += pay
        self.served += 1
        p.state, p.eat = "eating", 4.0
        tx, ty = TABLES[p.table]
        self.popups.append(dict(text=f"+Rp {pay}", x=tx, y=ty - 100, t=1.8, col=GREEN))
        if plate["used_ai"]:
            algo = plate.get("algo") or "AI"
            extra = f" (koki {algo}: bayaran setengah"
            extra += f", {over} langkah lebih panjang -{pen})" if over else ", resep terpendek, tanpa potongan)"
        else:
            extra = f" (tip {tip})"
        if assist is not None:
            extra += (f" [asisten DFS: {assist['len']} langkah, terpendek {assist['bfs']}, "
                      f"biaya jasa -{fee}]")
        self.say(f"Meja {p.table + 1} puas! +Rp {pay}{extra}", GREEN)
        if self.served % 6 == 0 and self.rep < 3:
            self.rep += 1
            self.say(f"Meja {p.table + 1} puas! +Rp {pay}{extra}. Reputasi naik!", GREEN)

    def click_floor(self, pos):
        if self.assist_button.rect.collidepoint(pos):
            self.toggle_assist()
            return
        for p in self.queue_list():
            xs = [m.x for m in p.members]
            r = pygame.Rect(min(xs) - 28, min(m.y for m in p.members) - 105, max(xs) - min(xs) + 56, 125)
            if r.collidepoint(pos):
                self.sel_party = p
                self.say("Pelanggan dipilih. Sekarang klik meja kosong.", BLUE)
                return
        for i, (tx, ty) in enumerate(TABLES):
            if pygame.Rect(tx - 110, ty - 75, 220, 140).collidepoint(pos):
                self.click_table(i)
                return
        if COOK_RECT.collidepoint(pos):
            self.set_task("cook", COOK_POINT)
            self.say("Berjalan ke pintu dapur...", TEXT)
            return
        if PICKUP_RECT.collidepoint(pos):
            self.set_task("pickup", PICKUP_POINT)
            self.say("Berjalan ke meja saji...", TEXT)
            return
        if FLOOR_RECT.collidepoint(pos):
            self.set_task("move", pos)

    def click_table(self, i):
        tx, ty = TABLES[i]
        svc = (tx, ty + 80)
        p = self.tables[i]
        if p is None:
            if self.sel_party and self.sel_party.state == "queue":
                p = self.sel_party
                self.sel_party = None
                self.tables[i] = p
                p.table = i
                p.state = "walking"
                for m, seat in zip(p.members, self.table_seats(i, len(p.members))):
                    m.set_route(seat[0], seat[1], allow_seat_table=i)
                self.set_task("move", svc)
                self.say(f"Pelanggan menuju Meja {i + 1}.", GREEN)
            else:
                self.set_task("move", svc)
                self.say("Pilih pelanggan di antrean dulu, baru klik meja kosong.", MUTED)
        elif p.state == "ready":
            self.set_task("order", svc, party=p)
            self.say(f"Menuju Meja {i + 1} untuk mencatat pesanan...", TEXT)
        elif p.state == "waitfood":
            self.set_task("deliver", svc, party=p)
            if any(c["party"] is p for c in self.carry):
                self.say(f"Mengantar piring ke Meja {i + 1}...", TEXT)
            else:
                self.say(f"Meja {i + 1} menunggu makanan. Masak dulu di dapur.", MUTED)
        else:
            self.set_task("move", svc)

    def draw_person(self, x, y, m, face, sitting=False, apron=False):
        """Me-render karakter menggunakan Polymorphic Renderer & sprite PNG 5-frame."""
        return render_entity_polymorphic(
            m,
            self.screen,
            self.assets,
            face=face,
            sitting=sitting,
            apron=apron,
            font_badge=self.f_smallb,
            badge_color=PURPLE,
        )

    def draw_floor(self):
        sc = self.screen
        # 1. Render World Map dari PyTMX (`assets/maps/restoran.tmx`)
        tmx_map = self.assets.maps.get("restoran")
        if tmx_map is not None:
            tmx_map.render(sc)
        else:
            pygame.draw.rect(sc, (225, 188, 140), (0, 64, W, H - 64))

        # Konter & Pintu Dapur
        pygame.draw.rect(sc, (95, 170, 160), (230, 120, 700, 14), border_radius=4)
        pygame.draw.rect(sc, (190, 140, 80), (230, 134, 700, 50))
        for x in range(236, 930, 24):
            pygame.draw.rect(sc, (160, 110, 60), (x, 138, 12, 42))

        pygame.draw.rect(sc, (140, 100, 70), COOK_RECT, 3, border_radius=8)
        pygame.draw.rect(sc, (245, 235, 215), (270, 74, 240, 48), border_radius=6)
        # Tampilkan mini-sprite Koki AI di jendela Pintu Dapur
        chef_mini = self.assets.get_char_sprite("ai_chef", "depan", 0)
        if chef_mini is not None:
            sc.blit(chef_mini, (318, 66), pygame.Rect(0, 0, 76, 54))
        self.text("PINTU DAPUR", self.f_midb, BAR, 392, 78)
        self.text("klik untuk memasak", self.f_small, MUTED, 392, 98)
        if self.tickets:
            pygame.draw.circle(sc, RED, (520, 90), 14)
            img = self.f_midb.render(str(len(self.tickets)), True, WHITE)
            sc.blit(img, img.get_rect(center=(520, 90)))

        # Meja Saji
        pygame.draw.rect(sc, (140, 100, 70), PICKUP_RECT, 3, border_radius=8)
        self.text("MEJA SAJI", self.f_midb, BAR, 578, 78)
        self.text("klik untuk ambil piring", self.f_small, MUTED, 578, 98)
        plate_asset = self.assets.items.get("piring_nasi_goreng")
        for i, pl in enumerate(self.counter[:5]):
            cx = 690 + i * 46
            if plate_asset is not None:
                sc.blit(plate_asset, plate_asset.get_rect(center=(cx, 104)))
            img = self.f_smallb.render(str(pl["party"].table + 1), True, WHITE)
            pygame.draw.circle(sc, BAR, (cx, 88), 9)
            sc.blit(img, img.get_rect(center=(cx, 88)))

        # Pintu Masuk
        pygame.draw.rect(sc, (140, 90, 55), (6, 130, 80, 120), border_radius=6)
        pygame.draw.rect(sc, (185, 130, 85), (14, 138, 64, 104), border_radius=4)
        self.text("MASUK", self.f_smallb, WHITE, 22, 100)
        pygame.draw.line(sc, (190, 60, 60), (28, 290), (28, 670), 3)

        # Meja Restoran
        tbl_sprite = self.assets.tiles.get("meja_restoran")
        for i, (tx, ty) in enumerate(TABLES):
            p = self.tables[i]
            if tbl_sprite is not None:
                sc.blit(tbl_sprite, tbl_sprite.get_rect(center=(tx, ty - 2)))
            if p is None:
                pygame.draw.circle(sc, WHITE, (tx, ty), 14)
                pygame.draw.circle(sc, BORDER, (tx, ty), 14, 2)
                img = self.f_midb.render(str(i + 1), True, TEXT)
                sc.blit(img, img.get_rect(center=(tx, ty)))
            else:
                pygame.draw.circle(sc, WHITE, (tx, ty - 22), 9)
                self.text(str(i + 1), self.f_smallb, TEXT, tx - 4, ty + 18)
                if p.state == "eating" and plate_asset is not None:
                    for dx in (-32, 32)[: len(p.members)]:
                        sc.blit(plate_asset, plate_asset.get_rect(center=(tx + dx, ty - 2)))
                else:
                    for dx in (-34, 34):
                        pygame.draw.ellipse(sc, WHITE, (tx + dx - 14, ty - 8, 28, 16))
                        pygame.draw.ellipse(sc, BORDER, (tx + dx - 14, ty - 8, 28, 16), 1)

        self.draw_route_overlay()

        # Entitas diurutkan menurut Y supaya tampak berlapis (depth sorting)
        items = []
        for p in self.parties:
            sitting = p.state in ("ready", "waitfood", "eating")
            for m in p.members:
                items.append((m.y, "party", p, m, sitting))
        items.append((self.waitress.y, "waitress", None, self.waitress, False))
        items.append((self.assist.y, "assistant", None, self.assist, False))
        items.sort(key=lambda it: it[0])
        for _, kind, p, m, sitting in items:
            if kind == "waitress":
                self.draw_person(m.x, m.y, m, "happy", apron=True)
                self.draw_carry(m.x, m.y)
            elif kind == "assistant":
                self.draw_person(m.x, m.y, m, "happy", apron=True)
                if self.asst["plate"] is not None:
                    self.draw_carry(m.x, m.y, [self.asst["plate"]])
            else:
                self.draw_person(m.x, m.y, m, p.face, sitting=sitting)

        # Hati kesabaran, gelembung pesanan, seleksi
        for p in self.parties:
            if p.state in ("leaving", "eating", "walking"):
                continue
            mx = sum(m.x for m in p.members) / len(p.members)
            top = min(m.y for m in p.members) - (100 if p.state == "queue" else 90)
            n = p.hearts
            for k in range(3):
                col = (235, 70, 80) if k < n else (230, 225, 225)
                self.heart(int(mx + (k - 1) * 22), int(top), 5, col)
            self.text(fmt_time(p.p), self.f_smallb, RED if p.p / p.pmax < 0.25 else MUTED,
                      int(mx) + 40, int(top) - 8)
            if p is self.sel_party:
                xs = [m.x for m in p.members]
                r = pygame.Rect(min(xs) - 32, min(m.y for m in p.members) - 112, max(xs) - min(xs) + 64, 128)
                pygame.draw.rect(sc, GOLD, r, 4, border_radius=12)
            if p.state == "ready":
                self.bubble(mx, top - 18, ["!"], RED, big=True)
            elif p.state == "waitfood":
                o = p.order
                self.bubble(mx, top - 18, ["Nasi Goreng", f"Telur {'YA' if o['egg'] else 'TIDAK'}",
                                           f"Kecap {'YA' if o['kecap'] else 'TIDAK'}"], TEXT)
        for pp in self.popups:
            img = self.f_big.render(pp["text"], True, pp["col"])
            img.set_alpha(int(255 * min(1.0, pp["t"])))
            sc.blit(img, (pp["x"] - img.get_width() // 2, int(pp["y"])))

        # Bar pesan bawah
        pygame.draw.rect(sc, PANEL, (20, 684, 1140, 28), border_radius=8)
        pygame.draw.rect(sc, BORDER, (20, 684, 1140, 28), 2, border_radius=8)
        self.text(self.msg[:150], self.f_midb, self.msg_col, 30, 689)
        info = f"Dibawa: {len(self.carry)}/2   Siap di meja saji: {len(self.counter)}"
        self.text(info, self.f_smallb, MUTED, 930, 100)
        on = self.asst["on"]
        self.assist_button.label = "AI Antar (DFS): " + ("ON" if on else "OFF") + " (A)"
        self.assist_button.color = GREEN if on else PURPLE
        self.assist_button.draw(sc, self.f_smallb, self.assist_button.rect.collidepoint(pygame.mouse.get_pos()))
        self.text(self.assist_info, self.f_smallb, PURPLE, 944, 170)
        self.text("Ungu: Closed | Hijau: Open (V)", self.f_small, MUTED, 944, 187)

    def draw_carry(self, x, y, plates=None):
        sc = self.screen
        plates = self.carry if plates is None else plates
        plate_asset = self.assets.items.get("piring_nasi_goreng")
        for i, pl in enumerate(plates):
            cx, cy = int(x) + 28, int(y) - 68 - i * 24
            if plate_asset is not None:
                sc.blit(plate_asset, plate_asset.get_rect(center=(cx, cy)))
            img = self.f_smallb.render(str(pl["party"].table + 1), True, RED)
            sc.blit(img, (cx - 4, cy - 26))

    def bubble(self, cx, bottom, lines, col, big=False):
        fonts = self.f_title if big else self.f_smallb
        imgs = [fonts.render(s, True, col) for s in lines]
        w = max(i.get_width() for i in imgs) + 16
        h = sum(i.get_height() for i in imgs) + 10
        r = pygame.Rect(int(cx - w / 2), int(bottom - h), w, h)
        pygame.draw.rect(self.screen, WHITE, r, border_radius=10)
        pygame.draw.rect(self.screen, BORDER, r, 2, border_radius=10)
        y = r.y + 5
        for img in imgs:
            self.screen.blit(img, (r.centerx - img.get_width() // 2, y))
            y += img.get_height()

    def target_label(self, i):
        o = self.order
        if o is None:
            return "-"
        if i == BERAS:
            return "Nasi goreng"
        if i == BAWANG:
            return "Ditumis"
        if i == TELUR:
            return "Didadar" if o["egg"] else "Jangan dipakai!"
        if i == GARAM:
            return "Sudah"
        if i == KECAP:
            return "Sudah" if o["kecap"] else "Jangan ditambah!"
        return "Disajikan"
