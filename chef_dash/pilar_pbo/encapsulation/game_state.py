"""
PILAR PBO 2: ENCAPSULATION (Encapsulated Game State)
Melindungi data penting restoran (uang, reputasi, jumlah pelanggan dilayani, dan state bahan masakan)
agar tidak diubah sembarangan dari luar class tanpa validasi Getter/Setter.
"""


class EncapsulatedGameState:
    """
    Menyimpan state finansial, reputasi restoran, dan tuple ruang keadaan memasak
    menggunakan atribut private (`__money`, `__rep`, `__served`, `__cooking_state`).
    """

    MAX_REPUTATION = 3
    MIN_REPUTATION = 0

    def __init__(self, initial_state=(0, 0, 0, 0, 0, 0)):
        self.__money = 0
        self.__served = 0
        self.__rep = self.MAX_REPUTATION
        self.__cooking_state = tuple(initial_state)
        self.__steps = 0
        self.__mistakes = 0

    # --- Getter & Setter untuk Uang (Money) ---
    @property
    def money(self) -> int:
        return self.__money

    @money.setter
    def money(self, value: int) -> None:
        # Validasi: uang tidak boleh negatif
        self.__money = max(0, int(value))

    def add_money(self, amount: int) -> int:
        self.money = self.__money + int(amount)
        return self.__money

    # --- Getter & Setter untuk Pelanggan Dilayani (Served) ---
    @property
    def served(self) -> int:
        return self.__served

    @served.setter
    def served(self, value: int) -> None:
        self.__served = max(0, int(value))

    # --- Getter & Setter untuk Reputasi (Reputation 0..3) ---
    @property
    def rep(self) -> int:
        return self.__rep

    @rep.setter
    def rep(self, value: int) -> None:
        # Validasi batas reputasi antara 0 dan 3 hati
        self.__rep = max(self.MIN_REPUTATION, min(self.MAX_REPUTATION, int(value)))

    # --- Getter & Setter untuk State Memasak (Tuple 6 Bahan) ---
    @property
    def cooking_state(self) -> tuple:
        return self.__cooking_state

    @cooking_state.setter
    def cooking_state(self, new_state: tuple) -> None:
        if not isinstance(new_state, (tuple, list)) or len(new_state) != 6:
            raise ValueError("State memasak harus berupa 6-tuple (beras, bawang, telur, garam, kecap, piring).")
        self.__cooking_state = tuple(int(v) for v in new_state)

    # --- Getter & Setter untuk Langkah & Kesalahan ---
    @property
    def steps(self) -> int:
        return self.__steps

    @steps.setter
    def steps(self, value: int) -> None:
        self.__steps = max(0, int(value))

    @property
    def mistakes(self) -> int:
        return self.__mistakes

    @mistakes.setter
    def mistakes(self, value: int) -> None:
        self.__mistakes = max(0, int(value))
