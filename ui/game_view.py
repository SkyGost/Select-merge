"""
Herná scéna — Canvas s mriežkou kruhov, ovládanie myšou a animácia padu.

Komponenty v tomto súbore:
- Animator: spravuje plynulý pohyb kruhov (padanie) cez canvas.after()
- GameView: hlavná trieda — vykresľuje pole, spracúva myš, vykonáva merge

Princíp:
- Logika hry je v game.board.Board (model)
- GameView je VIEW — vykresľuje stav modelu a reaguje na vstup
- Animator beží asynchrónne — počas animácie je vstup myšou zablokovaný
"""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Dict, List, Optional, Tuple

import config
from game.board import Board, Circle
from ui import sounds

Cell = Tuple[int, int]


# ====================================================================
#  Animator — plynulý pohyb kruhov
# ====================================================================

class Animator:
    """
    Spravuje aktívne animácie pohybu kruhov.

    Každá animácia = jeden kruh, ktorý sa pohybuje z (x1, y1) do (x2, y2).
    Pri každom tick-u sa všetky kruhy posunú o krok bližšie k cieľu.
    Keď sú všetky animácie hotové, zavolá sa on_complete callback.
    """

    def __init__(self, canvas: tk.Canvas) -> None:
        self.canvas = canvas
        # zoznam: (group_id, target_y, speed) — group_id je ID skupiny
        # objektov na canvase (kruh + text), ktoré sa hýbu spoločne
        self._active: List[Dict] = []
        self._running = False
        self._on_complete: Optional[Callable[[], None]] = None

    def is_running(self) -> bool:
        return self._running

    def animate_falls(
        self,
        falls: List[Tuple[List[int], float]],
        on_complete: Callable[[], None],
    ) -> None:
        """
        Spustí animácie padu.

        Args:
            falls: zoznam (item_ids, target_y) — pre každú skupinu canvas
                   objektov (kruh + text), kam má spadnúť (cieľové y stredu).
            on_complete: zavolá sa, keď všetky animácie dobehnú.
        """
        if not falls:
            on_complete()
            return

        self._on_complete = on_complete
        for item_ids, target_y in falls:
            self._active.append({
                "items": item_ids,        # zoznam canvas IDs, ktoré sa hýbu spolu
                "target_y": target_y,
                "speed": config.FALL_SPEED,
            })
        self._running = True
        self._tick()

    def _tick(self) -> None:
        """Jeden krok animácie (~16 ms)."""
        still_animating: List[Dict] = []

        for anim in self._active:
            items = anim["items"]
            target_y = anim["target_y"]
            speed = anim["speed"]

            # Zoberieme y prvého itemu (kruhu) ako referenciu
            coords = self.canvas.coords(items[0])
            if not coords:
                continue
            # coords pre oval = [x1, y1, x2, y2] → stred y = (y1 + y2) / 2
            current_y = (coords[1] + coords[3]) / 2

            remaining = target_y - current_y
            if abs(remaining) <= speed:
                # Doraziť na cieľ
                dy = remaining
                done = True
            else:
                dy = speed if remaining > 0 else -speed
                done = False

            # Posunúť všetky položky v skupine
            for item_id in items:
                self.canvas.move(item_id, 0, dy)

            if not done:
                still_animating.append(anim)

        self._active = still_animating

        if self._active:
            # Pokračovať
            self.canvas.after(config.ANIMATION_INTERVAL_MS, self._tick)
        else:
            # Hotovo — zavolať callback
            self._running = False
            cb = self._on_complete
            self._on_complete = None
            if cb:
                cb()


# ====================================================================
#  GameView — hlavná herná obrazovka
# ====================================================================

class GameView(tk.Frame):
    """
    Frame s hracou plochou (Canvas) a info panelom.

    Args:
        parent: rodičovský widget
        on_game_over: callback(score, max_circle), volaný pri konci hry
        on_back_to_menu: callback(), volaný pri kliknutí na 'Späť'
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_game_over: Callable[[int, int], None],
        on_back_to_menu: Callable[[], None],
    ) -> None:
        super().__init__(parent, bg=config.BG_COLOR)
        self.on_game_over = on_game_over
        self.on_back_to_menu = on_back_to_menu

        # Model
        self.board = Board()
        self.board.fill_initial()

        # Mapa (row, col) → (oval_id, text_id) na canvas
        # — potrebujeme to, aby sme vedeli pohybovať a aktualizovať kruhy
        self.cell_items: Dict[Cell, Tuple[int, int]] = {}

        # Stav ťahania myšou
        self.current_path: List[Cell] = []
        self.dragging = False
        self.line_id: Optional[int] = None   # ID čiary na canvase počas ťahania

        # Animátor
        self.animator: Optional[Animator] = None

        self._build_ui()
        self._draw_board()

    # ----------------------------------------------------------------
    #  Vykreslenie UI
    # ----------------------------------------------------------------

    def _build_ui(self) -> None:
        """Vytvorí widgety: info panel hore + canvas pod ním."""
        # Horný info panel
        self.info_frame = tk.Frame(self, bg=config.BG_COLOR)
        self.info_frame.pack(fill="x", padx=10, pady=10)

        self.score_label = tk.Label(
            self.info_frame,
            text=f"{config.TXT_SCORE}: 0",
            font=("Helvetica", 20, "bold"),
            bg=config.BG_COLOR,
            fg=config.TEXT_COLOR_DARK,
        )
        self.score_label.pack(side="left")

        self.max_label = tk.Label(
            self.info_frame,
            text=f"{config.TXT_MAX_CIRCLE}: 2",
            font=("Helvetica", 16),
            bg=config.BG_COLOR,
            fg=config.TEXT_COLOR_DARK,
        )
        self.max_label.pack(side="left", padx=30)

        self.back_btn = tk.Button(
            self.info_frame,
            text=config.TXT_BACK,
            command=self.on_back_to_menu,
            font=("Helvetica", 13),
            padx=10,
        )
        self.back_btn.pack(side="right")

        # Canvas s hracím poľom
        canvas_size = config.BOARD_SIZE * config.CELL_SIZE + 2 * config.BOARD_PADDING
        self.canvas = tk.Canvas(
            self,
            width=canvas_size,
            height=canvas_size,
            bg=config.BOARD_BG_COLOR,
            highlightthickness=0,
        )
        self.canvas.pack(padx=10, pady=10)

        # Animátor pre tento canvas
        self.animator = Animator(self.canvas)

        # Eventy myši
        self.canvas.bind("<Button-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)

    def _draw_board(self) -> None:
        """Vykreslí celé pole od začiatku."""
        self.canvas.delete("all")
        self.cell_items.clear()

        # Zaoblené pozadie hracieho poľa (ako na referencii)
        canvas_size = self.board.size * config.CELL_SIZE + 2 * config.BOARD_PADDING
        self._draw_rounded_rect(
            config.BOARD_PADDING // 2,
            config.BOARD_PADDING // 2,
            canvas_size - config.BOARD_PADDING // 2,
            canvas_size - config.BOARD_PADDING // 2,
            config.BOARD_CORNER_RADIUS,
            fill=config.BOARD_BG_COLOR,
            outline=config.BOARD_BORDER_COLOR,
            width=2,
        )

        # Kruhy (bez prázdnych pozadí — pole je čisté biele)
        for r in range(self.board.size):
            for c in range(self.board.size):
                circle = self.board.grid[r][c]
                if circle is not None:
                    self._create_circle_visuals(circle, r, c)

        self._update_info()

    def _draw_rounded_rect(
        self, x1: int, y1: int, x2: int, y2: int, radius: int,
        fill: str = "", outline: str = "", width: int = 1,
    ) -> int:
        """
        Nakreslí obdĺžnik so zaoblenými rohmi pomocou polygonu so smoothom.
        Tkinter nemá natívnu funkciu, takže to robíme cez polygon.
        """
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        return self.canvas.create_polygon(
            points, smooth=True, fill=fill,
            outline=outline, width=width,
        )

    def _create_circle_visuals(
        self, circle: Circle, r: int, c: int,
        override_y: Optional[float] = None,
    ) -> Tuple[int, int]:
        """
        Vytvorí grafickú reprezentáciu kruhu (oval + text) na canvase.
        Vráti (oval_id, text_id) a zapíše do self.cell_items[(r, c)].

        Ak override_y nie je None, vytvorí sa na zadanej y-pozícii
        (používa sa pre animáciu padu zhora).
        """
        cx, cy = self._cell_center(r, c)
        if override_y is not None:
            cy = override_y

        radius = config.CIRCLE_RADIUS
        color = config.CIRCLE_COLORS.get(circle.value, config.DEFAULT_CIRCLE_COLOR)
        # Biely text na všetkých farebných kruhoch (podľa referencie)
        text_color = config.TEXT_COLOR_LIGHT

        oval_id = self.canvas.create_oval(
            cx - radius, cy - radius, cx + radius, cy + radius,
            fill=color, outline="",
        )
        text_id = self.canvas.create_text(
            cx, cy,
            text=self._format_value(circle.value),
            font=("Helvetica", self._font_size_for(circle.value), "bold"),
            fill=text_color,
        )
        self.cell_items[(r, c)] = (oval_id, text_id)
        return oval_id, text_id

    @staticmethod
    def _format_value(value: int) -> str:
        """Skráti veľké čísla: 1024 → '1K', 2048 → '2K'."""
        if value >= 1000:
            return f"{value // 1000}K"
        return str(value)

    @staticmethod
    def _font_size_for(value: int) -> int:
        """Menšie písmo pre viacciferné čísla."""
        s = GameView._format_value(value)
        if len(s) <= 2:
            return 32       # 2, 4, 8, 16, 32, 64
        if len(s) == 3:
            return 26       # 128, 256, 512
        return 22           # 1K, 2K, ...

    # ----------------------------------------------------------------
    #  Konverzia súradníc
    # ----------------------------------------------------------------

    def _cell_bbox(self, r: int, c: int) -> Tuple[int, int, int, int]:
        """Bounding box bunky (x1, y1, x2, y2)."""
        x1 = config.BOARD_PADDING + c * config.CELL_SIZE
        y1 = config.BOARD_PADDING + r * config.CELL_SIZE
        return x1, y1, x1 + config.CELL_SIZE, y1 + config.CELL_SIZE

    def _cell_center(self, r: int, c: int) -> Tuple[int, int]:
        """Stred bunky."""
        x1, y1, x2, y2 = self._cell_bbox(r, c)
        return (x1 + x2) // 2, (y1 + y2) // 2

    def _pixel_to_cell(self, x: float, y: float) -> Optional[Cell]:
        """
        Konvertuje pixel-pozíciu na (row, col).
        Vráti None, ak je mimo poľa alebo príliš ďaleko od stredu bunky.
        """
        # Najprv hrubo: ktorá bunka
        col = (x - config.BOARD_PADDING) // config.CELL_SIZE
        row = (y - config.BOARD_PADDING) // config.CELL_SIZE
        if not (0 <= row < self.board.size and 0 <= col < self.board.size):
            return None

        # Skontrolovať, či sme dostatočne blízko stredu kruhu
        cx, cy = self._cell_center(int(row), int(col))
        dist_sq = (x - cx) ** 2 + (y - cy) ** 2
        if dist_sq > config.CIRCLE_RADIUS ** 2:
            return None

        return int(row), int(col)

    # ----------------------------------------------------------------
    #  Aktualizácia info panelu
    # ----------------------------------------------------------------

    def _update_info(self) -> None:
        self.score_label.config(
            text=f"{config.TXT_SCORE}: {self.board.stats.score}"
        )
        self.max_label.config(
            text=f"{config.TXT_MAX_CIRCLE}: {self.board.stats.max_circle}"
        )

    # ----------------------------------------------------------------
    #  Spracovanie myši
    # ----------------------------------------------------------------

    def _is_input_blocked(self) -> bool:
        """Vstup je zablokovaný počas animácie."""
        return self.animator is not None and self.animator.is_running()

    def _on_mouse_down(self, event: tk.Event) -> None:
        if self._is_input_blocked():
            return
        cell = self._pixel_to_cell(event.x, event.y)
        if cell is None:
            return
        # Začať novú spojnicu
        self.current_path = [cell]
        self.dragging = True
        self._redraw_line()
        sounds.play_click()

    def _on_mouse_drag(self, event: tk.Event) -> None:
        if self._is_input_blocked() or not self.dragging:
            return
        cell = self._pixel_to_cell(event.x, event.y)
        if cell is None or not self.current_path:
            return

        # Ak sme stále nad rovnakou bunkou ako naposledy — ignoruj
        if cell == self.current_path[-1]:
            return

        # Vrátenie sa o krok späť (užívateľ "odčaroval" posledný kruh)
        if len(self.current_path) >= 2 and cell == self.current_path[-2]:
            self.current_path.pop()
            self._redraw_line()
            return

        # Inak skús pridať cell na koniec — musí byť:
        # - susedom posledného
        # - s rovnakou hodnotou
        # - nie už v ceste
        if cell in self.current_path:
            return
        last = self.current_path[-1]
        if not Board.are_adjacent(last, cell):
            return
        last_circle = self.board.get_circle(*last)
        new_circle = self.board.get_circle(*cell)
        if last_circle is None or new_circle is None:
            return
        if last_circle.value != new_circle.value:
            return

        self.current_path.append(cell)
        self._redraw_line()
        sounds.play_click()

    def _on_mouse_up(self, event: tk.Event) -> None:
        if self._is_input_blocked():
            return
        if not self.dragging:
            return
        self.dragging = False

        # Skontrolovať, či je spojnica platná a vykonať merge
        path = self.current_path
        self.current_path = []
        self._clear_line()

        if self.board.is_valid_path(path):
            self._execute_merge(path)

    def _redraw_line(self) -> None:
        """Prekreslí aktuálnu spojnicu (čiaru cez stredy buniek)."""
        self._clear_line()
        if len(self.current_path) < 1:
            return
        # Body čiary = stredy buniek
        points: List[float] = []
        for (r, c) in self.current_path:
            cx, cy = self._cell_center(r, c)
            points.extend([cx, cy])
        if len(points) >= 4:   # aspoň 2 body
            self.line_id = self.canvas.create_line(
                *points,
                fill=config.LINE_COLOR,
                width=config.LINE_WIDTH,
                capstyle="round",
                joinstyle="round",
            )

    def _clear_line(self) -> None:
        if self.line_id is not None:
            self.canvas.delete(self.line_id)
            self.line_id = None

    # ----------------------------------------------------------------
    #  Vykonanie merge + animácia
    # ----------------------------------------------------------------

    def _execute_merge(self, path: List[Cell]) -> None:
        """
        Spracuje validnú spojnicu:
        1. Vymaže kruhy z canvasu (okrem posledného)
        2. Aktualizuje posledný kruh na novú hodnotu
        3. Aplikuje gravitáciu + spawn nových kruhov
        4. Spustí animácie padu
        5. Po skončení skontroluje game over
        """
        # Zvuk merge
        sounds.play_merge()

        # 1. Vymazať canvas items pre kruhy okrem posledného
        for (r, c) in path[:-1]:
            if (r, c) in self.cell_items:
                oval_id, text_id = self.cell_items.pop((r, c))
                self.canvas.delete(oval_id)
                self.canvas.delete(text_id)

        # 2. Vykonať merge v modeli
        last_cell = path[-1]
        self.board.merge_line(path)
        self._update_info()

        # 3. Prekresliť posledný kruh s novou hodnotou
        if last_cell in self.cell_items:
            oval_id, text_id = self.cell_items.pop(last_cell)
            self.canvas.delete(oval_id)
            self.canvas.delete(text_id)
        new_circle = self.board.grid[last_cell[0]][last_cell[1]]
        if new_circle is not None:
            self._create_circle_visuals(new_circle, *last_cell)

        # 4. Gravitácia + spawn s animáciou
        self._apply_gravity_animated()

    def _apply_gravity_animated(self) -> None:
        """
        Vykoná gravitáciu na modeli, naanimuje pohyb existujúcich kruhov,
        potom spawne nové a naanimuje ich pád zhora.
        """
        moves = self.board.apply_gravity()   # list (circle, old_row, new_row)

        # Pripraviť animácie pre existujúce kruhy, ktoré padli nižšie
        falls: List[Tuple[List[int], float]] = []
        for circle, old_row, new_row in moves:
            col = circle.col
            # Canvas items sú stále na (old_row, col) — presunieme ich na (new_row, col)
            old_cell = (old_row, col)
            new_cell = (new_row, col)
            if old_cell in self.cell_items:
                items = self.cell_items.pop(old_cell)
                self.cell_items[new_cell] = items
                _, target_y = self._cell_center(new_row, col)
                falls.append((list(items), target_y))

        # Po animácii pádu existujúcich — spawn nových
        def after_falls():
            new_circles = self.board.spawn_new_circles()
            new_falls: List[Tuple[List[int], float]] = []
            for circle in new_circles:
                # Vytvoríme kruh nad poľom (mimo canvas vidlive oblasti)
                spawn_y = config.BOARD_PADDING - config.CELL_SIZE - circle.row * config.CELL_SIZE
                oval_id, text_id = self._create_circle_visuals(
                    circle, circle.row, circle.col, override_y=spawn_y,
                )
                _, target_y = self._cell_center(circle.row, circle.col)
                new_falls.append(([oval_id, text_id], target_y))

            # Po dopade nových — skontrolovať game over
            self.animator.animate_falls(new_falls, on_complete=self._check_game_over)

        if falls:
            self.animator.animate_falls(falls, on_complete=after_falls)
        else:
            after_falls()

    def _check_game_over(self) -> None:
        """Po každom merge skontroluje, či hra skončila."""
        if self.board.is_game_over():
            self.on_game_over(
                self.board.stats.score,
                self.board.stats.max_circle,
            )