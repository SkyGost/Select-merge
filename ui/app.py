"""
Главное окно приложения Connect-Merge.

Содержит:
- App             — корневое окно + переключение между экранами
- MenuFrame       — главное меню с декоративными кружками на фоне
- HallOfFameFrame — таблица рекордов через простые Label (без Treeview)
- GameOverDialog  — диалог конца игры (ввод никнейма)
"""

from __future__ import annotations

import tkinter as tk
from typing import Optional

import config
from data import scores
from ui.game_view import GameView


# ====================================================================
#  App — корневое окно + управление экранами
# ====================================================================

class App(tk.Tk):
    """Корневое окно. Управляет переходами между экранами."""

    def __init__(self) -> None:
        super().__init__()
        self.title(config.TXT_TITLE)
        self.configure(bg=config.BG_COLOR)
        self.resizable(False, False)

        # Текущий активный экран
        self.current_frame: Optional[tk.Frame] = None
        self.show_menu()

    def _swap_frame(self, new_frame: tk.Frame) -> None:
        """Заменяет текущий экран новым, старый уничтожается."""
        if self.current_frame is not None:
            self.current_frame.destroy()
        self.current_frame = new_frame
        self.current_frame.pack(fill="both", expand=True)

    def show_menu(self) -> None:
        self._swap_frame(MenuFrame(self, self))

    def show_game(self) -> None:
        self._swap_frame(GameView(
            self,
            on_game_over=self.on_game_over,
            on_back_to_menu=self.show_menu,
        ))

    def show_hall_of_fame(self) -> None:
        self._swap_frame(HallOfFameFrame(self, self.show_menu))

    def on_game_over(self, score: int, max_circle: int, moves: int = 0) -> None:
        """Вызывается когда игра закончена — показывает диалог с никнеймом."""
        dialog = GameOverDialog(self, score, max_circle, moves)
        self.wait_window(dialog)
        self.show_menu()


# ====================================================================
#  MenuFrame — главное меню
# ====================================================================

class MenuFrame(tk.Frame):
    """Экран главного меню с декоративными кружками на фоне."""

    # Декоративные кружки: (x, y, радиус, значение)
    # Два больших по краям, три маленьких в углах
    _BG_CIRCLES = [
        (555, 120, 62, 16),   # большой справа вверху
        (30,  400, 68, 32),   # большой слева внизу
        (80,   80, 36,  4),   # маленький слева вверху
        (540, 450, 38, 64),   # маленький справа внизу
        (310, 540, 32,  8),   # маленький снизу по центру
    ]

    def __init__(self, parent: tk.Widget, app: App) -> None:
        super().__init__(parent, bg=config.BG_COLOR)
        self.app = app

        # Canvas на весь экран — кружки рисуются на нём, виджеты поверх
        self.canvas = tk.Canvas(
            self,
            bg=config.BG_COLOR,
            highlightthickness=0,
            width=630,
            height=630,
        )
        self.canvas.pack(fill="both", expand=True)

        # Сначала фоновые кружки (они под всеми виджетами)
        self._draw_bg_circles()

        # Заголовок через create_text — нет белого фона как у Label
        self.canvas.create_text(
            315, 100,
            text=config.TXT_TITLE,
            font=("Helvetica", 36, "bold"),
            fill=config.TEXT_COLOR_DARK,
        )

        # Стиль кнопок
        btn_style = {
            "font": ("Helvetica", 16),
            "width": 18,
            "height": 2,
            "bg": "#8f7a66",
            "fg": "white",
            "activebackground": "#9f8a76",
            "relief": "flat",
            "bd": 0,
        }

        # Кнопки поверх canvas через create_window
        self.canvas.create_window(315, 240, window=tk.Button(
            self.canvas, text=config.TXT_PLAY,
            command=self.app.show_game, **btn_style,
        ))
        self.canvas.create_window(315, 320, window=tk.Button(
            self.canvas, text=config.TXT_HIGHSCORES,
            command=self.app.show_hall_of_fame, **btn_style,
        ))
        self.canvas.create_window(315, 400, window=tk.Button(
            self.canvas, text=config.TXT_EXIT,
            command=self.app.destroy, **btn_style,
        ))

    def _draw_bg_circles(self) -> None:
        """
        Рисует декоративные кружки на фоне меню.
        Полные цвета из игровой палитры, белые цифры внутри — как в игре.
        """
        for (x, y, r, value) in self._BG_CIRCLES:
            color = config.CIRCLE_COLORS.get(value, config.DEFAULT_CIRCLE_COLOR)
            self.canvas.create_oval(
                x - r, y - r, x + r, y + r,
                fill=color, outline="",
            )
            font_size = 20 if r >= 55 else (16 if r >= 40 else 13)
            self.canvas.create_text(
                x, y,
                text=str(value),
                font=("Helvetica", font_size, "bold"),
                fill="#ffffff",
            )


# ====================================================================
#  HallOfFameFrame — таблица рекордов
# ====================================================================

class HallOfFameFrame(tk.Frame):
    """
    Экран рекордов — без Treeview.
    Каждая строка — набор Label, выровненных по центру.
    Никакого ресайза, никакого выделения, никаких глюков.
    """

    def __init__(self, parent: tk.Widget, on_back) -> None:
        super().__init__(parent, bg=config.BG_COLOR)
        self.on_back = on_back

        # Заголовок
        tk.Label(
            self,
            text=config.TXT_HIGHSCORES,
            font=("Helvetica", 28, "bold"),
            bg=config.BG_COLOR,
            fg=config.TEXT_COLOR_DARK,
        ).pack(pady=(30, 20))

        # Контейнер для таблицы — фиксированной ширины, по центру
        table_frame = tk.Frame(self, bg=config.BG_COLOR)
        table_frame.pack(pady=10)

        # ── Заголовочная строка ──────────────────────────────────────
        header_style = {
            "font": ("Helvetica", 13, "bold"),
            "bg": "#e8e4de",           # чуть темнее фона — отделяет заголовок
            "fg": config.TEXT_COLOR_DARK,
            "pady": 6,
            "relief": "flat",
        }

        # Ширины колонок в символах (фиксированные — не зависят от данных)
        col_widths = {"rank": 4, "nick": 14, "score": 10, "max": 12, "moves": 8}

        tk.Label(table_frame, text="#",
                 width=col_widths["rank"],  **header_style).grid(row=0, column=0, padx=2)
        tk.Label(table_frame, text=config.TXT_NICK,
                 width=col_widths["nick"],  **header_style).grid(row=0, column=1, padx=2)
        tk.Label(table_frame, text=config.TXT_SCORE,
                 width=col_widths["score"], **header_style).grid(row=0, column=2, padx=2)
        tk.Label(table_frame, text=config.TXT_MAX_CIRCLE,
                 width=col_widths["max"],   **header_style).grid(row=0, column=3, padx=2)
        tk.Label(table_frame, text=config.TXT_MOVES,
                 width=col_widths["moves"], **header_style).grid(row=0, column=4, padx=2)

        # Разделительная линия под заголовком
        sep = tk.Frame(table_frame, bg="#d0ccc6", height=1)
        sep.grid(row=1, column=0, columnspan=5, sticky="ew", pady=(0, 4))

        # ── Строки с данными ─────────────────────────────────────────
        row_style = {
            "font": ("Helvetica", 13),
            "bg": config.BG_COLOR,
            "fg": config.TEXT_COLOR_DARK,
            "pady": 5,
            "relief": "flat",
        }

        entries = scores.load_scores()

        if not entries:
            # Таблица пустая — показываем заглушку
            tk.Label(
                table_frame,
                text="— пусто —",
                font=("Helvetica", 13),
                bg=config.BG_COLOR,
                fg="#aaa",
            ).grid(row=2, column=0, columnspan=5, pady=20)
        else:
            for i, entry in enumerate(entries, start=1):
                # Чередуем цвет строк для читаемости
                row_bg = "#f7f5f2" if i % 2 == 0 else config.BG_COLOR
                rs = {**row_style, "bg": row_bg}

                tk.Label(table_frame, text=str(i),
                         width=col_widths["rank"],  **rs).grid(row=i+1, column=0, padx=2)
                tk.Label(table_frame, text=entry.get("nick", "???"),
                         width=col_widths["nick"],  **rs).grid(row=i+1, column=1, padx=2)
                tk.Label(table_frame, text=str(entry.get("score", 0)),
                         width=col_widths["score"], **rs).grid(row=i+1, column=2, padx=2)
                tk.Label(table_frame, text=str(entry.get("max_circle", 0)),
                         width=col_widths["max"],   **rs).grid(row=i+1, column=3, padx=2)
                tk.Label(table_frame, text=str(entry.get("moves", "—")),
                         width=col_widths["moves"], **rs).grid(row=i+1, column=4, padx=2)

        # Кнопка «Назад»
        tk.Button(
            self, text=config.TXT_BACK,
            command=self.on_back,
            font=("Helvetica", 12),
            width=12,
            bg="#8f7a66",
            fg="white",
            activebackground="#9f8a76",
            relief="flat",
            bd=0,
        ).pack(pady=30)


# ====================================================================
#  GameOverDialog — диалог конца игры
# ====================================================================

class GameOverDialog(tk.Toplevel):
    """
    Модальное окно после конца игры.
    Показывает итоги и если результат в топ-10 — просит ввести никнейм.
    """

    def __init__(self, parent: tk.Widget, score: int, max_circle: int, moves: int = 0) -> None:
        super().__init__(parent, bg=config.BG_COLOR)
        self.title(config.TXT_GAME_OVER)
        self.score      = score
        self.max_circle = max_circle
        self.moves      = moves
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()  # делает окно модальным

        is_high = scores.is_high_score(score)

        tk.Label(
            self, text=config.TXT_GAME_OVER,
            font=("Helvetica", 22, "bold"),
            bg=config.BG_COLOR, fg=config.TEXT_COLOR_DARK,
            padx=40, pady=20,
        ).pack()

        tk.Label(
            self, text=f"{config.TXT_SCORE}: {score}",
            font=("Helvetica", 16),
            bg=config.BG_COLOR, fg=config.TEXT_COLOR_DARK,
        ).pack(pady=4)

        tk.Label(
            self, text=f"{config.TXT_MAX_CIRCLE}: {max_circle}",
            font=("Helvetica", 14),
            bg=config.BG_COLOR, fg=config.TEXT_COLOR_DARK,
        ).pack(pady=4)

        # Показываем количество ходов
        tk.Label(
            self, text=f"{config.TXT_MOVES}: {moves}",
            font=("Helvetica", 14),
            bg=config.BG_COLOR, fg=config.TEXT_COLOR_DARK,
        ).pack(pady=4)

        if is_high:
            tk.Label(
                self, text=config.TXT_ENTER_NICK,
                font=("Helvetica", 12),
                bg=config.BG_COLOR, fg=config.TEXT_COLOR_DARK,
            ).pack(pady=(20, 5))

            self.nick_var = tk.StringVar()
            entry = tk.Entry(
                self, textvariable=self.nick_var,
                font=("Helvetica", 14), width=20, justify="center",
            )
            entry.pack(pady=5)
            entry.focus_set()
            entry.bind("<Return>", lambda e: self._save_and_close())

            tk.Button(
                self, text=config.TXT_SAVE,
                command=self._save_and_close,
                font=("Helvetica", 12), width=12,
                bg="#8f7a66", fg="white",
                activebackground="#9f8a76",
                relief="flat", bd=0,
            ).pack(pady=20)
        else:
            tk.Button(
                self, text=config.TXT_BACK,
                command=self.destroy,
                font=("Helvetica", 12), width=12,
                bg="#8f7a66", fg="white",
                activebackground="#9f8a76",
                relief="flat", bd=0,
            ).pack(pady=20)

    def _save_and_close(self) -> None:
        """Сохраняет рекорд с никнеймом и закрывает диалог."""
        nick = self.nick_var.get().strip() or "???"
        scores.save_score(nick, self.score, self.max_circle, self.moves)
        self.destroy()