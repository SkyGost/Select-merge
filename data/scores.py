"""
Сохранение и загрузка таблицы рекордов.

Формат файла assets/highscores.json:
[
  {"nick": "Vova", "score": 11100, "max_circle": 1024, "moves": 42},
  ...
]

Функции:
- load_scores()                        — загрузить список рекордов
- save_score(nick, score, max_circle, moves) — сохранить новый рекорд
- is_high_score(score)                 — попадает ли результат в топ-10
"""

from __future__ import annotations

import json
import os
from typing import List, Dict

import config


def load_scores() -> List[Dict]:
    """
    Загружает таблицу рекордов из JSON-файла.
    Если файл не существует или повреждён — возвращает пустой список.
    """
    path = config.HIGHSCORES_PATH
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
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

    - Записи сортируются по убыванию очков (при равных очках — по max_circle)
    - Хранится только топ MAX_HIGHSCORES (по умолчанию 10)
    - Дата убрана — храним только игровые данные

    Возвращает обновлённый список рекордов.
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
    os.makedirs(os.path.dirname(config.HIGHSCORES_PATH), exist_ok=True)

    with open(config.HIGHSCORES_PATH, "w", encoding="utf-8") as f:
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
    # Сравниваем с наименьшим результатом в таблице
    lowest = min(e.get("score", 0) for e in entries)
    return score > lowest