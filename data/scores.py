"""
Сохранение и загрузка таблицы рекордов.

Формат файла assets/highscores.json:
[
  {"nick": "Vova", "score": 11100, "max_circle": 1024, "moves": 42},
  ...
]

Функции:
- load_scores()                             — загрузить список рекордов
- save_score(nick, score, max_circle, moves) — сохранить новый рекорд
- is_high_score(score)                      — попадает ли результат в топ-10
"""

from __future__ import annotations

import json
import os
from typing import List, Dict

import config

# Абсолютный путь к файлу рекордов — работает при любом способе запуска (F5, терминал и тд)
# __file__ — это путь к данному файлу (scores.py)
# dirname дважды — поднимаемся из data/ в корень проекта
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SCORES_PATH = os.path.join(_BASE_DIR, config.HIGHSCORES_PATH)


def load_scores() -> List[Dict]:
    """
    Загружает таблицу рекордов из JSON-файла.
    Если файл не существует или повреждён — возвращает пустой список.
    """
    if not os.path.exists(_SCORES_PATH):
        return []
    try:
        with open(_SCORES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, OSError):
        # Повреждённый файл — начинаем с чистого листа, игра не падает
        return []


def save_score(nick: str, score: int, max_circle: int, moves: int = 0) -> List[Dict]:
    """
    Добавляет новый рекорд в таблицу и сохраняет файл.

    - Записи сортируются по убыванию очков (при равных — по max_circle)
    - Хранится только топ MAX_HIGHSCORES (по умолчанию 10)
    """
    entries = load_scores()
    entries.append({
        "nick":       nick.strip() or "???",
        "score":      int(score),
        "max_circle": int(max_circle),
        "moves":      int(moves),
    })

    # Сортируем: сначала больше очков, при равных — больший кружок
    entries.sort(
        key=lambda e: (e.get("score", 0), e.get("max_circle", 0)),
        reverse=True,
    )

    # Оставляем только топ N
    entries = entries[:config.MAX_HIGHSCORES]

    # Создаём папку assets если её нет
    os.makedirs(os.path.dirname(_SCORES_PATH), exist_ok=True)

    with open(_SCORES_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    return entries


def is_high_score(score: int) -> bool:
    """
    Проверяет, попадает ли результат в топ-10.
    Используется после конца игры — если да, просим ввести никнейм.
    """
    entries = load_scores()
    if len(entries) < config.MAX_HIGHSCORES:
        return True  # таблица ещё не заполнена — любой результат попадает
    lowest = min(e.get("score", 0) for e in entries)
    return score > lowest