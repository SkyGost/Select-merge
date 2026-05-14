# Главный файл игры содержит в себе корневой класс App, который управляет окнами и переходами между ними

import config
import tkinter as tk

from data import scores            # Подключает файл data/scores.py — отвечает за загрузку и сохранение рекордов
from ui.game_view import GameView  # Подключает класс GameView из ui/game_view.py — это экран самой игры


# App — начальный экран + управление экранами

class App(tk.Tk):

    def __init__(self) -> None:             # -> None означает что функция ничего не возвращает
        super().__init__()                  # запускает инициализацию tk.Tk и создает само окно
        self.title(config.TXT_TITLE)        # заголовок окна "Connect-Merge"
        self.configure(bg=config.BG_COLOR)  # цвет фона окна
        self.resizable(False, False)        # запрещает растягивать окно мышью
        self.current_frame = None           # пока никакого экрана нет None это пустое значение
        self.show_menu()                    # сразу показываем меню при запуске

    def _swap_frame(self, new_frame: tk.Frame) -> None:
        if self.current_frame is not None:       # если экран уже есть то
            self.current_frame.destroy()         # уничтожаем старый экран
        self.current_frame = new_frame           # запоминаем новый экран
        self.current_frame.pack(fill="both", expand=True)  # добавляем экран в окно и растягиваем на всю область

    def show_menu(self) -> None: 
        self._swap_frame(MenuFrame(self, self))  # создаем новый экран 

    def show_game(self) -> None:         
        self._swap_frame(GameView(
            self,
            on_game_over = self.on_game_over,      # передаем функцию которая сработает когда игра закончится
            on_back_to_menu = self.show_menu,      # передаем функцию для кнопки "назад"
        ))

    def show_hall_of_fame(self) -> None:         # показывает экран таблицы рекордов
        self._swap_frame(LeaderboardFrame(self, self.show_menu))

    def on_game_over(self, score: int, max_circle: int, moves: int = 0) -> None:      # Вызывается из game_view.py когда игра закончена
        result_text = Gameovertext(self, score, max_circle, moves)                  # открываем диалог с результатами
        self.wait_window(result_text)                                                 # ждём пока игрок закроет диалог
        self.show_menu()                                                              # после закрытия возвращаемся в меню


# MenuFrame — экран главного меню

class MenuFrame(tk.Frame):

    # Декоративные кружки на фоне: (x, y, радиус, значение):

    BG_CIRCLES = [
        (555, 120, 62, 16),   # большой справа вверху
        (30,  400, 68, 32),   # большой слева внизу
        (80,   80, 36,  4),   # маленький слева вверху
        (540, 450, 38, 64),   # маленький справа внизу
        (310, 540, 32,  8),   # маленький снизу по центру
    ]

    def __init__(self, parent: tk.Widget, app: App) -> None:
        super().__init__(parent, bg=config.BG_COLOR)        # создаём контейнер Frame и задаём цвет его фона (переменная parent это типо папки в которую мы положим все виджеты этого экрана)
        self.app = app                                      # сохраняем ссылку на App чтобы вызывать show_game, show_hall_of_fame

        # Canvas — это холст на котором рисуем кружки и поверх которого кладём кнопки
        
        self.canvas = tk.Canvas(
            self,
            bg=config.BG_COLOR,
            highlightthickness = 0,  # убираем рамку вокруг canvas
            width=630,
            height=630,
        )
        self.canvas.pack(fill="both", expand=True) # растягивает по ширине и высоте и занимает всё свободное место внутри MenuFrame

        self._draw_bg_circles()  # сначала рисуем фоновые кружки — они будут под кнопками

        # Рисуем заголовок:
        self.canvas.create_text(
            315, 100,                          # координаты центра текста (x, y)
            text=config.TXT_TITLE,             # текст из config а именно "Connect-Merge"
            font=("Helvetica", 36, "bold"),
            fill=config.TEXT_COLOR_DARK,
        )

        # Общий стиль для всех трёх кнопок в основном меню:
        main_button_style = {
            "font": ("Helvetica", 16),
            "width": 18,                      # ширина кнопки в символах
            "height": 2,                      # высота кнопки в строках
            "bg": "#8f7a66",                # цвет кнопки
            "fg": "white",                    # цвет текста на кнопке
            "activebackground": "#9f8a76",  # цвет кнопки при нажатии
            "relief": "flat",                 # убирает объёмный эффект чтобы кнопка была плоская
            "bd": 0,                          # убирает рамку вокруг кнопки
        }

        # create_window помещает виджет (кнопку) поверх canvas по координатам (x, y)
        self.canvas.create_window(315, 240, window=tk.Button(
            self.canvas, text=config.TXT_PLAY,
            command=self.app.show_game, **main_button_style,  # **main_button_style собирает общий стиль для кнопок типа main_button_style
        ))
        self.canvas.create_window(315, 320, window=tk.Button(
            self.canvas, text=config.TXT_HIGHSCORES,
            command=self.app.show_hall_of_fame, **main_button_style,
        ))
        self.canvas.create_window(315, 400, window=tk.Button(
            self.canvas, text=config.TXT_EXIT,
            command=self.app.destroy, **main_button_style,  # destroy — закрывает всё окно
        ))

    def _draw_bg_circles(self) -> None:
        # Проходим по каждому кружку из списка BG_CIRCLES
        for (x, y, r, value) in self.BG_CIRCLES:
            color = config.CIRCLE_COLORS.get(value, config.DEFAULT_CIRCLE_COLOR)  # берём цвет по значению
            self.canvas.create_oval(
                x - r, y - r, x + r, y + r,  # координаты овала: левый верх и правый низ
                fill=color, outline="",      # outline="" убирает обводку в круге
            )
            if r >= 55:
                font_size = 20
            elif r >= 40:
                font_size = 16
            else:
                font_size = 13  # размер шрифта зависит от радиуса

            self.canvas.create_text(
                x, y,
                text=str(value),                        # преобразования обычного числа в строку для отображения этого числа внутри кружка (немного запутаннно но вы поняли)
                font=("Helvetica", font_size, "bold"),  # стиль текста внутри кружков
                fill="#ffffff",                       # белый текст внутри 
            )


# LeaderboardFrame — экран таблицы рекордов

class LeaderboardFrame(tk.Frame):

    def __init__(self, parent: tk.Widget, on_back) -> None:
        super().__init__(parent, bg=config.BG_COLOR)
        self.on_back = on_back  # сохраняем функцию для кнопки "назад"

        # Заголовок экрана
        tk.Label(
            self,
            text=config.TXT_HIGHSCORES,
            font=("Helvetica", 28, "bold"), # дефолт дизайн выше рассписывал что за что отвечает почитайте если не понятно
            bg=config.BG_COLOR,
            fg=config.TEXT_COLOR_DARK,
        ).pack(pady=(30, 20))

        # Контейнер для таблицы отдельный Frame внутри основного
        table_frame = tk.Frame(self, bg=config.BG_COLOR)  # создаём новый Frame (Frame если что это пустой прямоугольник) для таблицы рекордов внутри LeaderboardFrame
        table_frame.pack(pady=10)                         # отступ сверху и снизу 10 пикселей

        # Стиль заголовочной строки слегка темнее фона чтобы отличалась от данных
        header_style = {
            "font": ("Helvetica", 13, "bold"),
            "bg": "#e8e4de",
            "fg": config.TEXT_COLOR_DARK,   # опять же дизайн текста для заголовков в таблице рекордов
            "pady": 6,
            "relief": "flat",
        }

        # Ширины колонок в символах  фиксированные чтобы таблица не уезжала в Казахтан, возможно будет ломаться при ультра больших числах надо будет обсудить 
        col_widths = {"rank": 4, "nick": 14, "score": 10, "max": 12, "moves": 8}

        # Заголовочная строка grid (grid это способ размещения виджетов по сетке самой простой пример таблица Excel) расставляет Label (Label это просто текст на экране) по сетке (row=строка, column=столбец)
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

        # Тонкая разделительная линия между заголовком и данными
        divider_line = tk.Frame(table_frame, bg="#d0ccc6", height=1)
        divider_line.grid(row=1, column=0, columnspan=5, sticky="ew", pady=(0, 4))

        # Стиль строк с данными
        row_style = {
            "font": ("Helvetica", 13),
            "bg": config.BG_COLOR,
            "fg": config.TEXT_COLOR_DARK,
            "pady": 5,
            "relief": "flat",
        }

        entries = scores.load_scores()  # загружаем рекорды из файла

        if not entries:
            # Если рекордов нет  показываем заглушку
            tk.Label (
                table_frame,
                text=config.TXT_EMPTY,
                font=("Helvetica", 13),
                bg=config.BG_COLOR,
                fg="#aaa",
            ).grid(row=2, column=0, columnspan=5, pady=20)
        else:
            for i, entry in enumerate(entries, start=1):  # enumerate даёт номер строки начиная с 1
                row_bg = "#f7f5f2" if i % 2 == 0 else config.BG_COLOR  # чередуем цвет строк
                rs = {**row_style, "bg": row_bg}  # копируем стиль и меняем только фон

                tk.Label(table_frame, text=str(i),
                        width=col_widths["rank"],  **rs).grid(row=i+1, column=0, padx=2)
                tk.Label(table_frame, text=entry.get("nick", "???"),
                        width=col_widths["nick"],  **rs).grid(row=i+1, column=1, padx=2)
                tk.Label(table_frame, text=str(entry.get("score", 0)),
                        width=col_widths["score"], **rs).grid(row=i+1, column=2, padx=2)
                tk.Label(table_frame, text=str(entry.get("max_circle", 0)),
                        width=col_widths["max"],   **rs).grid(row=i+1, column=3, padx=2)
                tk.Label(table_frame, text=str(entry["moves"]),
                        width=col_widths["moves"], **rs).grid(row=i+1, column=4, padx=2)

        # Кнопка назад
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


# Gameovertext всплывающее окно когда игра закончена

class Gameovertext(tk.Toplevel):

    def __init__(self, parent: tk.Widget, score: int, max_circle: int, moves: int = 0) -> None:
        super().__init__(parent, bg=config.BG_COLOR)
        self.title(config.TXT_GAME_OVER)
        self.score      = score       # сохраняем результаты чтобы потом записать в файл
        self.max_circle = max_circle  # сохраняем результаты чтобы потом записать в файл
        self.moves      = moves       # сохраняем результаты чтобы потом записать в файл
        self.resizable(False, False)  # запрещаем менять размер окна
        self.transient(parent)  # окно привязано к родительскому окну сворачивается вместе с ним
        self.grab_set()         # блокирует клики на основное окно пока текст открыт

        is_high = scores.is_high_score(score)  # проверяем попадает ли результат в топ 5, 10 либо сколько рекордов мы сохраняем 

        # Показываем результаты игры
        tk.Label(
            self, text=config.TXT_GAME_OVER,
            font=("Helvetica", 22, "bold"),
            bg=config.BG_COLOR, fg=config.TEXT_COLOR_DARK,
            padx=40, pady=20,
        ).pack()

        tk.Label(
            self, text=f"{config.TXT_SCORE}: {score}",  # f"" потому что строка с переменной внутри
            font=("Helvetica", 16),
            bg=config.BG_COLOR, fg=config.TEXT_COLOR_DARK,
        ).pack(pady=4)

        tk.Label(
            self, text=f"{config.TXT_MAX_CIRCLE}: {max_circle}",
            font=("Helvetica", 14),
            bg=config.BG_COLOR, fg=config.TEXT_COLOR_DARK,
        ).pack(pady=4)

        tk.Label(
            self, text=f"{config.TXT_MOVES}: {moves}",
            font=("Helvetica", 14),
            bg=config.BG_COLOR, fg=config.TEXT_COLOR_DARK,
        ).pack(pady=4)

        if is_high:
            # Результат в топ 5 просим ввести никнейм
            tk.Label(
                self, text=config.TXT_ENTER_NICK,
                font=("Helvetica", 12),
                bg=config.BG_COLOR, fg=config.TEXT_COLOR_DARK,
            ).pack(pady=(20, 5))

            self.nick_var = tk.StringVar()  # переменная привязанная к полю ввода
            entry = tk.Entry(
                self, textvariable=self.nick_var,
                font=("Helvetica", 14), width=20, justify="center",
            )
            entry.pack(pady=5)
            entry.focus_set()  # курсор сразу в поле ввода
            entry.bind("<Return>", lambda e: self._save_and_close())  # Enter = сохранить

            tk.Button(
                self, text=config.TXT_SAVE,
                command=self._save_and_close,
                font=("Helvetica", 12), width=12,
                bg="#8f7a66", fg="white",
                activebackground="#9f8a76",
                relief="flat", bd=0,
            ).pack(pady=20)
        else:
            # Результат не в топ 5  просто кнопка назад
            tk.Button(
                self, text=config.TXT_BACK,
                command=self.destroy,  # destroy закрывает текст конца игры  когда результат не попал в топ 5
                font=("Helvetica", 12), width=12,
                bg="#8f7a66", fg="white",
                activebackground="#9f8a76",
                relief="flat", bd=0,
            ).pack(pady=20)

    def _save_and_close(self) -> None:
        nick = self.nick_var.get().strip() or "Mister X"  # берём никнейм если пустой — ставим "Mister X"
        scores.save_score(nick, self.score, self.max_circle, self.moves)  # сохраняем в файл
        self.destroy()  # закрываем текст конца игры после сохранения рекорда