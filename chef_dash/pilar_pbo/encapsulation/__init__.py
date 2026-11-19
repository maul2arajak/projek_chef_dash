"""
Pilar 2: ENCAPSULATION
Melindungi data internal dengan atribut private (`__attr`) dan menyediakan akses terkontrol
melalui Getter / Setter (`@property`).
"""
from pilar_pbo.encapsulation.game_state import EncapsulatedGameState
from pilar_pbo.encapsulation.ticket_order import EncapsulatedOrderTicket

__all__ = ["EncapsulatedGameState", "EncapsulatedOrderTicket"]
