"""
PILAR PBO 2: ENCAPSULATION (Encapsulated Order & Patience)
Melindungi data pesanan pelanggan dan waktu kesabaran (`__patience`, `__max_patience`, `__order`)
dengan properti tervalidasi.
"""

import math


class EncapsulatedOrderTicket:
    """
    Enkapsulasi data pesanan meja dan kesabaran pelanggan.
    Menggunakan atribut private (`__order`, `__patience`, `__max_patience`, `__par`)
    serta properti Getter/Setter.
    """

    def __init__(self, order: dict, par: int, max_patience: float):
        self.__order = dict(egg=bool(order.get("egg", False)), kecap=bool(order.get("kecap", False)))
        self.__par = max(1, int(par))
        self.__max_patience = max(1.0, float(max_patience))
        self.__patience = self.__max_patience

    @property
    def order(self) -> dict:
        """Mengembalikan salinan dictionary pesanan agar data internal aman dari mutasi langsung."""
        return dict(self.__order)

    @property
    def par(self) -> int:
        return self.__par

    @property
    def pmax(self) -> float:
        return self.__max_patience

    @property
    def patience(self) -> float:
        return self.__patience

    @patience.setter
    def patience(self, value: float) -> None:
        # Kesabaran selalu dijaga dalam rentang [0.0, max_patience]
        self.__patience = max(0.0, min(self.__max_patience, float(value)))

    @property
    def patience_ratio(self) -> float:
        return self.__patience / self.__max_patience

    @property
    def hearts(self) -> int:
        return max(1, math.ceil(3 * self.patience_ratio))
