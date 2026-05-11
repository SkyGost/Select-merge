"""
Hlavné okno aplikácie.

Obsahuje:
- App           : root okno + prepínanie medzi obrazovkami (menu / hra / rebríček)
- MenuFrame     : úvodné menu (Hrať / Rebríček / Koniec)
- HallOfFame    : tabuľka top-10 rekordov
- GameOverDialog: modálne okno po skončení hry (zadanie prezývky)
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

import config
from data import scores
from ui.game_view import GameView


# ====================================================================
#  Hlavná aplikácia — root okno + prepínanie scén
# ====================================================================

class App(tk.Tk):
    """Root okno aplikácie. Spravuje prechody medzi obrazovkami."""

    def __init__(self) -> None:
        super().__init__()
        self.title(config.TXT_TITLE)
        self.configure(bg=config.BG_COLOR)
        self.resizable(False, False)

        # Kontajner pre aktuálnu obrazovku
        self.current_frame: Optional[tk.Frame] = None

        self.show_menu()

    def _swap_frame(self, new_frame: tk.Frame) -> None:
        """Nahradí aktuálnu obrazovku novou."""
        if self.current_frame is not None:
            self.current_frame.destroy()
        self.current_frame = new_frame
        self.current_frame.pack(fill="both", expand=True)

    # ----------------------------------------------------------------
    #  Prepínače obrazoviek
    # ----------------------------------------------------------------

    def show_menu(self) -> None:
        self._swap_frame(MenuFrame(self, self))

    def show_game(self) -> None:
        view = GameView(
            self,
            on_game_over=self.on_game_over,
            on_back_to_menu=self.show_menu,
        )
        self._swap_frame(view)

    def show_hall_of_fame(self) -> None:
        self._swap_frame(HallOfFameFrame(self, self.show_menu))

    def on_game_over(self, score: int, max_circle: int) -> None:
        """Po skončení hry: ukázať dialóg na zadanie prezývky."""
        dialog = GameOverDialog(self, score, max_circle)
        self.wait_window(dialog)        # počká, kým dialóg zatvoria
        # Po dialógu sa vrátime na menu
        self.show_menu()


# ====================================================================
#  Úvodné menu
# ====================================================================

class MenuFrame(tk.Frame):
    """Úvodné menu s tlačidlami Hrať / Rebríček / Koniec."""

    def __init__(self, parent: tk.Widget, app: App) -> None:
        super().__init__(parent, bg=config.BG_COLOR, padx=60, pady=60)
        self.app = app

        title = tk.Label(
            self,
            text=config.TXT_TITLE,
            font=("Helvetica", 36, "bold"),
            bg=config.BG_COLOR,
            fg=config.TEXT_COLOR_DARK,
        )
        title.pack(pady=(20, 40))

        btn_style = {
            "font": ("Helvetica", 16),
            "width": 18,
            "height": 2,
            "bg": "#8f7a66",
            "fg": "white",
            "activebackground": "#9f8a76",
            "bd": 0,
        }

        tk.Button(
            self, text=config.TXT_PLAY,
            command=self.app.show_game,
            **btn_style,
        ).pack(pady=8)

        tk.Button(
            self, text=config.TXT_HIGHSCORES,
            command=self.app.show_hall_of_fame,
            **btn_style,
        ).pack(pady=8)

        tk.Button(
            self, text=config.TXT_EXIT,
            command=self.app.destroy,
            **btn_style,
        ).pack(pady=8)


# ====================================================================
#  Rebríček rekordov
# ====================================================================

class HallOfFameFrame(tk.Frame):
    """Obrazovka s tabuľkou top-10 hráčov."""

    def __init__(self, parent: tk.Widget, on_back) -> None:
        super().__init__(parent, bg=config.BG_COLOR, padx=40, pady=40)
        self.on_back = on_back

        title = tk.Label(
            self,
            text=config.TXT_HIGHSCORES,
            font=("Helvetica", 28, "bold"),
            bg=config.BG_COLOR,
            fg=config.TEXT_COLOR_DARK,
        )
        title.pack(pady=(0, 20))

        # Tabuľka cez ttk.Treeview
        columns = ("rank", "nick", "score", "max_circle", "date")
        tree = ttk.Treeview(
            self, columns=columns, show="headings", height=10,
        )
        tree.heading("rank", text="#")
        tree.heading("nick", text=config.TXT_NICK)
        tree.heading("score", text=config.TXT_SCORE)
        tree.heading("max_circle", text=config.TXT_MAX_CIRCLE)
        tree.heading("date", text=config.TXT_DATE)

        tree.column("rank", width=40, anchor="center")
        tree.column("nick", width=140, anchor="w")
        tree.column("score", width=100, anchor="e")
        tree.column("max_circle", width=120, anchor="e")
        tree.column("date", width=110, anchor="center")

        entries = scores.load_scores()
        if not entries:
            tree.insert("", "end", values=("—", "(prázdne)", "—", "—", "—"))
        else:
            for i, entry in enumerate(entries, start=1):
                tree.insert("", "end", values=(
                    i,
                    entry.get("nick", "???"),
                    entry.get("score", 0),
                    entry.get("max_circle", 0),
                    entry.get("date", ""),
                ))

        tree.pack(pady=10)

        tk.Button(
            self, text=config.TXT_BACK,
            command=self.on_back,
            font=("Helvetica", 12),
            width=12,
        ).pack(pady=20)


# ====================================================================
#  Dialóg konca hry
# ====================================================================

class GameOverDialog(tk.Toplevel):
    """
    Modálne okno zobrazené po skončení hry.

    Ukáže skóre + najväčší kruh, a ak je skóre dosť dobré, opýta sa na
    prezývku a uloží záznam do rebríčka.
    """

    def __init__(self, parent: tk.Widget, score: int, max_circle: int) -> None:
        super().__init__(parent, bg=config.BG_COLOR)
        self.title(config.TXT_GAME_OVER)
        self.score = score
        self.max_circle = max_circle
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()                  # urobí okno modálne

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
        ).pack(pady=5)

        tk.Label(
            self, text=f"{config.TXT_MAX_CIRCLE}: {max_circle}",
            font=("Helvetica", 14),
            bg=config.BG_COLOR, fg=config.TEXT_COLOR_DARK,
        ).pack(pady=5)

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
            ).pack(pady=20)
        else:
            tk.Button(
                self, text=config.TXT_BACK,
                command=self.destroy,
                font=("Helvetica", 12), width=12,
            ).pack(pady=20)

    def _save_and_close(self) -> None:
        nick = self.nick_var.get().strip() or "???"
        scores.save_score(nick, self.score, self.max_circle)
        self.destroy()