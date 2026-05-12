"""
Игровая логика Connect-Merge. Этот файл — «мозг» игры,
он не знает ничего про визуальную часть (tkinter/canvas).

Содержит три класса:
- Circle    — один кружок на поле (значение + позиция)
- GameStats — счётчики: очки, максимальный кружок, количество ходов
- Board     — игровое поле 5×5 со всей логикой:
              спавн кружков, гравитация, проверка цепочки, мёрдж, конец игры
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import config


# Псевдонимы типов для читаемости кода
Cell = Tuple[int, int]   # координата клетки: (строка, столбец)
Path = List[Cell]        # цепочка клеток, которую провёл игрок


# ====================================================================
#  Circle — один кружок
# ====================================================================

@dataclass
class Circle:
    """
    Один кружок в сетке.

    Поля:
        value — числовое значение (степень двойки: 2, 4, 8, 16, ...)
        row   — строка в сетке (0 = верхняя)
        col   — столбец в сетке (0 = левый)
    """
    value: int
    row: int
    col: int

    def __repr__(self) -> str:
        # Удобное отображение при отладке в консоли
        return f"Circle(v={self.value}, r={self.row}, c={self.col})"


# ====================================================================
#  GameStats — статистика текущей игры
# ====================================================================

@dataclass
class GameStats:
    """
    Хранит статистику одной игровой сессии.
    Обновляется после каждого мёрджа через метод add_merge().
    """
    score: int = 0       # текущие очки
    max_circle: int = 2  # наибольшее значение кружка за игру
    moves: int = 0       # количество успешных мёрджей (ходов)

    def add_merge(self, new_value: int) -> None:
        """
        Вызывается после каждого мёрджа.
        Прибавляет очки, увеличивает счётчик ходов,
        обновляет максимальный кружок если нужно.
        """
        self.score += new_value   # очки = сумма всех новых значений
        self.moves += 1           # каждый мёрдж = один ход
        if new_value > self.max_circle:
            self.max_circle = new_value


# ====================================================================
#  Board — игровое поле
# ====================================================================

class Board:
    """
    Модель игрового поля размером size × size (по умолчанию 5×5).

    Хранит сетку кружков и предоставляет все операции игры.
    Координаты: (row, col), где row=0 — верхняя строка, col=0 — левый столбец.
    """

    def __init__(self, size: int = config.BOARD_SIZE) -> None:
        self.size: int = size

        # Двумерная сетка: None = пустая клетка, Circle = кружок на этой позиции
        self.grid: List[List[Optional[Circle]]] = [
            [None for _ in range(size)] for _ in range(size)
        ]

        # Текущий максимум на поле — управляет спавном новых кружков.
        # Новые кружки всегда МЕНЬШЕ этого значения.
        # Например: current_max = 16 → спавнятся только 2, 4, 8
        self.current_max: int = config.INITIAL_MAX_VALUE

        # Статистика этой игровой сессии
        self.stats: GameStats = GameStats()

        # Генератор случайных чисел (можно подменить при тестировании)
        self._rng = random.Random()

    # ----------------------------------------------------------------
    #  Инициализация поля
    # ----------------------------------------------------------------

    def fill_initial(self) -> None:
        """Заполняет всё поле случайными кружками в начале игры."""
        for r in range(self.size):
            for c in range(self.size):
                self.grid[r][c] = Circle(
                    value=self._random_spawn_value(),
                    row=r,
                    col=c,
                )

    def _random_spawn_value(self) -> int:
        """
        Возвращает случайную степень двойки (2^n), которая меньше current_max.
        Пример: current_max = 16 → вернёт одно из: 2, 4, 8
        """
        # bit_length() - 1 даёт log2 для степеней двойки: 8 → 3, 16 → 4
        max_exp = self.current_max.bit_length() - 1
        if max_exp <= 1:
            return 2  # минимальное возможное значение
        exp = self._rng.randint(1, max_exp - 1)
        return 2 ** exp

    # ----------------------------------------------------------------
    #  Соседство и доступ к клеткам
    # ----------------------------------------------------------------

    def in_bounds(self, r: int, c: int) -> bool:
        """Проверяет, находится ли координата внутри поля."""
        return 0 <= r < self.size and 0 <= c < self.size

    def get_circle(self, r: int, c: int) -> Optional[Circle]:
        """Возвращает кружок на позиции (r, c), или None если пусто / за границей."""
        if not self.in_bounds(r, c):
            return None
        return self.grid[r][c]

    def get_neighbors(self, r: int, c: int) -> List[Cell]:
        """
        Возвращает список всех 8 соседей клетки (r, c):
        вверх, вниз, влево, вправо и 4 диагонали.
        Клетки за пределами поля не включаются.
        """
        neighbors: List[Cell] = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue  # сама клетка — не сосед
                nr, nc = r + dr, c + dc
                if self.in_bounds(nr, nc):
                    neighbors.append((nr, nc))
        return neighbors

    @staticmethod
    def are_adjacent(a: Cell, b: Cell) -> bool:
        """Проверяет, являются ли две клетки соседними (включая диагонали)."""
        dr = abs(a[0] - b[0])
        dc = abs(a[1] - b[1])
        # Соседи — это клетки не дальше 1 шага по обоим осям, но не та же клетка
        return (dr, dc) != (0, 0) and dr <= 1 and dc <= 1

    # ----------------------------------------------------------------
    #  Проверка цепочки (path)
    # ----------------------------------------------------------------

    def is_valid_path(self, path: Path) -> bool:
        """
        Проверяет, можно ли выполнить мёрдж по данной цепочке.
        Цепочка валидна если:
        1. Длина >= MIN_LINE_LENGTH (минимум 2 кружка)
        2. Все клетки содержат кружок
        3. Все кружки имеют одинаковое значение
        4. Каждые два соседних кружка в цепочке являются соседями на поле
        5. Цепочка не пересекается (одна клетка встречается только один раз)
        """
        # Проверка 1: длина
        if len(path) < config.MIN_LINE_LENGTH:
            return False

        # Проверка 5: нет повторяющихся клеток
        if len(set(path)) != len(path):
            return False

        # Проверки 2 и 3: все кружки существуют и имеют одно значение
        first_circle = self.get_circle(*path[0])
        if first_circle is None:
            return False
        target_value = first_circle.value

        for (r, c) in path:
            circle = self.get_circle(r, c)
            if circle is None or circle.value != target_value:
                return False

        # Проверка 4: каждые два соседних кружка в цепочке — соседи на поле
        for i in range(len(path) - 1):
            if not self.are_adjacent(path[i], path[i + 1]):
                return False

        return True

    # ----------------------------------------------------------------
    #  Выполнение мёрджа
    # ----------------------------------------------------------------

    def merge_line(self, path: Path) -> int:
        """
        Выполняет слияние кружков по цепочке:
        - Все кружки кроме последнего удаляются с поля
        - Последний кружок получает значение = исходное × 2
        - Обновляется статистика и текущий максимум

        Возвращает: новое значение последнего кружка (= заработанные очки).
        Предполагается что цепочка уже проверена через is_valid_path().
        """
        original_value = self.get_circle(*path[0]).value
        new_value = original_value * 2

        # Убираем все кружки из цепочки кроме последнего
        for (r, c) in path[:-1]:
            self.grid[r][c] = None

        # Последний кружок получает удвоенное значение
        last_r, last_c = path[-1]
        self.grid[last_r][last_c] = Circle(
            value=new_value, row=last_r, col=last_c,
        )

        # Обновляем статистику: очки, ходы, максимум
        self.stats.add_merge(new_value)

        # Если новый кружок побил текущий максимум — обновляем
        # (влияет на диапазон спавна новых кружков)
        if new_value > self.current_max:
            self.current_max = new_value

        return new_value

    # ----------------------------------------------------------------
    #  Гравитация и спавн
    # ----------------------------------------------------------------

    def apply_gravity(self) -> List[Tuple[Circle, int, int]]:
        """
        Опускает все кружки вниз на свободные места (как в тетрисе).

        Возвращает список перемещений: [(кружок, старая_строка, новая_строка), ...]
        Этот список используется анимацией в UI для плавного показа падения.
        """
        moves: List[Tuple[Circle, int, int]] = []

        # Обрабатываем каждый столбец отдельно
        for c in range(self.size):
            # Собираем все кружки в столбце сверху вниз (пустые места пропускаем)
            circles_in_col = [
                self.grid[r][c] for r in range(self.size)
                if self.grid[r][c] is not None
            ]
            # Очищаем весь столбец
            for r in range(self.size):
                self.grid[r][c] = None

            # Расставляем кружки обратно снизу вверх (гравитация)
            new_row = self.size - 1
            for circle in reversed(circles_in_col):
                old_row = circle.row
                if old_row != new_row:
                    # Кружок сдвинулся — запоминаем для анимации
                    moves.append((circle, old_row, new_row))
                circle.row = new_row
                self.grid[new_row][c] = circle
                new_row -= 1

        return moves

    def spawn_new_circles(self) -> List[Circle]:
        """
        Заполняет все пустые клетки новыми случайными кружками.
        Возвращает список новых кружков (для анимации падения сверху).
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
    #  Конец игры
    # ----------------------------------------------------------------

    def is_game_over(self) -> bool:
        """
        Игра заканчивается когда нет ни одной пары соседних кружков
        с одинаковым значением — то есть невозможно сделать ни одного хода.
        """
        for r in range(self.size):
            for c in range(self.size):
                circle = self.grid[r][c]
                if circle is None:
                    continue
                # Проверяем только 4 направления (вниз, вправо, диагонали вниз)
                # чтобы не проверять каждую пару дважды
                for (dr, dc) in ((0, 1), (1, 0), (1, 1), (1, -1)):
                    nr, nc = r + dr, c + dc
                    neighbor = self.get_circle(nr, nc)
                    if neighbor is not None and neighbor.value == circle.value:
                        return False  # нашли пару — игра ещё не окончена
        return True  # пар нет — игра окончена

    # ----------------------------------------------------------------
    #  Вспомогательное — вывод для отладки
    # ----------------------------------------------------------------

    def __str__(self) -> str:
        """Выводит поле в консоль в читаемом виде (для отладки)."""
        lines = []
        for r in range(self.size):
            row_str = " ".join(
                f"{self.grid[r][c].value:>4}" if self.grid[r][c] else "   ."
                for c in range(self.size)
            )
            lines.append(row_str)
        lines.append(f"Очки: {self.stats.score}  Макс: {self.stats.max_circle}  "
                     f"Текущий макс: {self.current_max}")
        return "\n".join(lines)