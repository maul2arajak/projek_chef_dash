"""
Fungsi bantu tampilan (teks, wrap) + integrasi kelas PBO (Person, Party, Button).
Menggunakan Pilar Encapsulation (`EncapsulatedOrderTicket`) dan Pilar Inheritance (`CustomerCharacter`).
"""

import pygame

from ai.koki_bfs import START, bfs_masak
from core.config import BORDER, QUEUE_SLOTS, WHITE
from pilar_pbo.encapsulation.ticket_order import EncapsulatedOrderTicket
from pilar_pbo.inheritance.characters import AnimatedCharacter, CustomerCharacter


def fmt_time(sec):
    sec = max(0, int(sec + 0.999))
    return f"{sec // 60}:{sec % 60:02d}"


def lighten(c, k=30):
    return tuple(min(255, v + k) for v in c)


def wrap(text, font, maxw):
    words, lines, cur = text.split(" "), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if font.size(t)[0] <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit(text, font, maxw):
    """Potong teks dengan '...' agar muat dalam lebar maxw."""
    if font.size(text)[0] <= maxw:
        return text
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if font.size(text[:mid] + "...")[0] <= maxw:
            lo = mid
        else:
            hi = mid - 1
    return text[:lo] + "..."


def wrap_lim(text, font, maxw, lim):
    lines = wrap(text, font, maxw)
    if len(lines) > lim:
        lines = lines[:lim]
        lines[-1] = fit(lines[-1], font, maxw - 24) + " ..."
    return lines


# Alias kompatibilitas ke class induk PBO beranimasi 4-frame
Person = AnimatedCharacter


class Party(EncapsulatedOrderTicket):
    """
    Rombongan pelanggan yang mewarisi `EncapsulatedOrderTicket` (Pilar Encapsulation & Inheritance)
    dan memiliki daftar anggota `CustomerCharacter` beranimasi 4-frame.
    """

    def __init__(self, size, order, pmax):
        par = len(bfs_masak(START, order, record=False)["path"])
        super().__init__(order=order, par=par, max_patience=pmax)
        self.state = "queue"   # queue, walking, ready, waitfood, eating, leaving
        self.table = None
        self.eat = 0.0
        self.angry = False
        self.members = [CustomerCharacter(-40 - k * 40, QUEUE_SLOTS[0][1], variant=(k % 3)) for k in range(size)]

    @property
    def p(self) -> float:
        """Getter kesabaran (dienkapsulasi di superclass EncapsulatedOrderTicket)."""
        return self.patience

    @p.setter
    def p(self, value: float) -> None:
        """Setter kesabaran dengan validasi rentang [0, pmax]."""
        self.patience = value

    @property
    def face(self):
        if self.state == "eating":
            return "eat"
        if self.angry:
            return "angry"
        f = self.patience_ratio
        return "happy" if f > 0.5 else ("neutral" if f > 0.25 else "angry")


class Button:
    def __init__(self, rect, label, color, key):
        self.rect = pygame.Rect(rect)
        self.label, self.color, self.key = label, color, key
        self.flash = 0.0

    def draw(self, surf, font, hover):
        col = lighten(self.color) if hover else self.color
        pygame.draw.rect(surf, (200, 180, 150), self.rect.move(0, 3), border_radius=10)
        pygame.draw.rect(surf, col, self.rect, border_radius=10)
        pygame.draw.rect(surf, WHITE if self.flash > 0 else BORDER, self.rect,
                         4 if self.flash > 0 else 2, border_radius=10)
        img = font.render(self.label, True, WHITE)
        surf.blit(img, img.get_rect(center=self.rect.center))
