"""
Herná logika hry Connect-Merge.

Obsahuje:
- Circle      : jeden kruh na poli (hodnota + pozícia)
- GameStats   : skóre a najväčší dosiahnutý kruh
- Board       : model 5x5 poľa s celou hernou logikou
                (spawn, gravitácia, validácia spojnice, merge, koniec hry)

Žiadne závislosti na tkinter — model je úplne oddelený od UI.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import config


# Typové aliasy pre čitateľnosť
Cell = Tuple[int, int]              # (row, col)
Path = List[Cell]                   # postupnosť buniek tvoriaca spojnicu


# ====================================================================
#  Circle — jeden kruh
# ====================================================================

@dataclass
class Circle:
    """
    Jeden kruh v mriežke.

    Atribúty:
        value: číselná hodnota (mocnina dvojky: 2, 4, 8, 16, ...)
        row:   riadok v mriežke (0 = horný)
        col:   stĺpec v mriežke (0 = ľavý)
    """
    value: int
    row: int
    col: int

    def __repr__(self) -> str:
        return f"Circle(v={self.value}, r={self.row}, c={self.col})"


# ====================================================================
#  GameStats — skóre a štatistika hry
# ====================================================================

@dataclass
class GameStats:
    """Sleduje skóre a najväčší dosiahnutý kruh počas hry."""
    score: int = 0
    max_circle: int = 2

    def add_merge(self, new_value: int) -> None:
        """Pridá skóre po vykonaní merge a aktualizuje najväčší kruh."""
        self.score += new_value
        if new_value > self.max_circle:
            self.max_circle = new_value


# ====================================================================
#  Board — model hracieho poľa
# ====================================================================

class Board:
    """
    Model hracieho poľa veľkosti size x size.

    Drží mriežku kruhov a poskytuje všetky operácie hry.
    Súradnice: (row, col), kde row=0 je hore, col=0 vľavo.
    """

    def __init__(self, size: int = config.BOARD_SIZE) -> None:
        self.size: int = size
        # 2D mriežka: None = prázdne, Circle = kruh na tej pozícii
        self.grid: List[List[Optional[Circle]]] = [
            [None for _ in range(size)] for _ in range(size)
        ]
        # Aktuálne najvyššie číslo v hre — riadi spawn nových kruhov.
        # Nové kruhy musia byť MENŠIE ako toto (podľa pravidiel zo zadania:
        # "2^n, n ∈ N, nie je väčšia ako aktuálna najvyššia hodnota v kruhoch").
        self.current_max: int = config.INITIAL_MAX_VALUE
        # Štatistika tejto hry
        self.stats: GameStats = GameStats()
        # Náhodný generátor (možno nahradiť pri testovaní pre opakovateľnosť)
        self._rng = random.Random()

    # ----------------------------------------------------------------
    #  Inicializácia
    # ----------------------------------------------------------------

    def fill_initial(self) -> None:
        """Naplní celé pole náhodnými kruhmi na začiatku hry."""
        for r in range(self.size):
            for c in range(self.size):
                self.grid[r][c] = Circle(
                    value=self._random_spawn_value(),
                    row=r,
                    col=c,
                )

    def _random_spawn_value(self) -> int:
        """
        Vráti náhodnú mocninu dvojky 2^n, kde 2^n < current_max.
        Príklad: current_max = 8 → vráti 2 alebo 4
                 current_max = 16 → vráti 2, 4 alebo 8
        """
        # current_max je vždy mocnina dvojky; max_exp = log2(current_max)
        max_exp = self.current_max.bit_length() - 1   # napr. 8 -> 3
        if max_exp <= 1:
            return 2
        exp = self._rng.randint(1, max_exp - 1)
        return 2 ** exp

    # ----------------------------------------------------------------
    #  Susedstvo a prístup k bunkám
    # ----------------------------------------------------------------

    def in_bounds(self, r: int, c: int) -> bool:
        """Je súradnica vnútri poľa?"""
        return 0 <= r < self.size and 0 <= c < self.size

    def get_circle(self, r: int, c: int) -> Optional[Circle]:
        """Vráti kruh na danej pozícii, alebo None ak je prázdna/mimo."""
        if not self.in_bounds(r, c):
            return None
        return self.grid[r][c]

    def get_neighbors(self, r: int, c: int) -> List[Cell]:
        """
        Vráti zoznam 8 susedov bunky (r, c) — ortogonálne + diagonálne.
        Vynechá bunky mimo poľa.
        """
        neighbors: List[Cell] = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if self.in_bounds(nr, nc):
                    neighbors.append((nr, nc))
        return neighbors

    @staticmethod
    def are_adjacent(a: Cell, b: Cell) -> bool:
        """Sú dve bunky susedmi (orto alebo diagonálne)?"""
        dr = abs(a[0] - b[0])
        dc = abs(a[1] - b[1])
        return (dr, dc) != (0, 0) and dr <= 1 and dc <= 1

    # ----------------------------------------------------------------
    #  Validácia spojnice (path)
    # ----------------------------------------------------------------

    def is_valid_path(self, path: Path) -> bool:
        """
        Kontroluje, či je daná spojnica platná podľa pravidiel:
        1. Dĺžka >= MIN_LINE_LENGTH (aspoň 2 kruhy)
        2. Všetky bunky obsahujú kruh
        3. Všetky kruhy majú rovnakú hodnotu
        4. Po sebe idúce kruhy sú susedmi (8-súvislosť)
        5. Spojnica sa nepretína (žiadna bunka sa neopakuje)
        """
        # 1. Dĺžka
        if len(path) < config.MIN_LINE_LENGTH:
            return False

        # 5. Žiadne duplicity (kontrola pretínania)
        if len(set(path)) != len(path):
            return False

        # 2. + 3. Všetky bunky majú kruh s rovnakou hodnotou
        first_circle = self.get_circle(*path[0])
        if first_circle is None:
            return False
        target_value = first_circle.value

        for (r, c) in path:
            circle = self.get_circle(r, c)
            if circle is None or circle.value != target_value:
                return False

        # 4. Po sebe idúce bunky sú susedmi
        for i in range(len(path) - 1):
            if not self.are_adjacent(path[i], path[i + 1]):
                return False

        return True

    # ----------------------------------------------------------------
    #  Vykonanie merge
    # ----------------------------------------------------------------

    def merge_line(self, path: Path) -> int:
        """
        Vykoná spojenie kruhov pozdĺž danej cesty.

        - Všetky kruhy okrem posledného sa odstránia.
        - Posledný kruh sa zmení na 2x svoju pôvodnú hodnotu.
        - Aktualizuje skóre a current_max.

        Vracia: získané skóre (= nová hodnota kruhu).
        Predpokladá, že path je už zvalidovaná cez is_valid_path.
        """
        original_value = self.get_circle(*path[0]).value
        new_value = original_value * 2

        # Odstrániť všetky kruhy okrem posledného
        for (r, c) in path[:-1]:
            self.grid[r][c] = None

        # Posledný kruh dostane novú hodnotu
        last_r, last_c = path[-1]
        self.grid[last_r][last_c] = Circle(
            value=new_value, row=last_r, col=last_c,
        )

        # Aktualizovať skóre a max kruh
        self.stats.add_merge(new_value)

        # Aktualizovať current_max ak nový kruh prekonal doteraz najvyšší
        if new_value > self.current_max:
            self.current_max = new_value

        return new_value

    # ----------------------------------------------------------------
    #  Gravitácia a spawn
    # ----------------------------------------------------------------

    def apply_gravity(self) -> List[Tuple[Circle, int, int]]:
        """
        Kruhy padajú nadol do voľných miest.

        Vracia zoznam pohybov: [(circle, old_row, new_row), ...]
        — používa to animátor v UI na plynulé vykreslenie pádu.
        """
        moves: List[Tuple[Circle, int, int]] = []

        for c in range(self.size):
            # Zozbierať všetky kruhy v stĺpci zhora nadol
            circles_in_col = [
                self.grid[r][c] for r in range(self.size)
                if self.grid[r][c] is not None
            ]
            # Vyčistiť stĺpec
            for r in range(self.size):
                self.grid[r][c] = None
            # Uložiť kruhy späť — odspodu nahor
            # (posledný v zozname pôjde dolu, predposledný nad neho, ...)
            new_row = self.size - 1
            for circle in reversed(circles_in_col):
                old_row = circle.row
                if old_row != new_row:
                    moves.append((circle, old_row, new_row))
                circle.row = new_row
                self.grid[new_row][c] = circle
                new_row -= 1

        return moves

    def spawn_new_circles(self) -> List[Circle]:
        """
        Vyplní všetky prázdne bunky novými náhodnými kruhmi.
        Vracia zoznam nových kruhov (pre animáciu padania zhora).
        """
        new_circles: List[Circle] = []
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] is None:
                    circle = Circle(
                        value=self._random_spawn_value(),
                        row=r,
                        col=c,
                    )
                    self.grid[r][c] = circle
                    new_circles.append(circle)
        return new_circles

    # ----------------------------------------------------------------
    #  Koniec hry
    # ----------------------------------------------------------------

    def is_game_over(self) -> bool:
        """
        Hra končí, ak neexistujú dve susedné bunky s rovnakou hodnotou.
        (Vtedy sa nedá vytvoriť žiadna platná spojnica.)
        """
        for r in range(self.size):
            for c in range(self.size):
                circle = self.grid[r][c]
                if circle is None:
                    continue
                # Pozri len 4 susedov (dolu, vpravo, dolu-vpravo, dolu-vľavo) —
                # tým pokryjeme všetky dvojice bez duplicity.
                for (dr, dc) in ((0, 1), (1, 0), (1, 1), (1, -1)):
                    nr, nc = r + dr, c + dc
                    neighbor = self.get_circle(nr, nc)
                    if neighbor is not None and neighbor.value == circle.value:
                        return False
        return True

    # ----------------------------------------------------------------
    #  Pomocné — výpis pre debug
    # ----------------------------------------------------------------

    def __str__(self) -> str:
        """Pekný textový výpis pre debug v konzole."""
        lines = []
        for r in range(self.size):
            row_str = " ".join(
                f"{self.grid[r][c].value:>4}" if self.grid[r][c] else "   ."
                for c in range(self.size)
            )
            lines.append(row_str)
        lines.append(f"Skóre: {self.stats.score}  Max: {self.stats.max_circle}  "
                     f"current_max: {self.current_max}")
        return "\n".join(lines)