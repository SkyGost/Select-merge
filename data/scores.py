"""
Ukladanie rebríčka top-10 hráčov do JSON súboru.

Formát súboru:
[
  {"nick": "Marek", "score": 10520, "date": "2026-05-11", "max_circle": 1024},
  ...
]

Funkcie:
- load_scores() — načítať zoznam (alebo prázdny, ak súbor neexistuje)
- save_score(nick, score, max_circle) — pridať nový záznam, ponechať top-10
"""

from __future__ import annotations

import json
import os
from datetime import date
from typing import List, Dict

import config


def load_scores() -> List[Dict]:
    """
    Načíta rebríček zo súboru.
    Ak súbor neexistuje alebo je poškodený, vráti prázdny zoznam.
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
        # Poškodený súbor — radšej začneme od nuly, než aby hra spadla
        return []


def save_score(nick: str, score: int, max_circle: int) -> List[Dict]:
    """
    Pridá nový záznam do rebríčka a uloží súbor.

    - Záznamy sa zoradia zostupne podľa skóre, pri zhode podľa max_circle.
    - Uchová sa len top MAX_HIGHSCORES (predvolene 10).

    Vracia: aktualizovaný zoznam rekordov.
    """
    entries = load_scores()
    entries.append({
        "nick": nick.strip() or "???",
        "score": int(score),
        "date": date.today().isoformat(),
        "max_circle": int(max_circle),
    })

    # Zoradiť: najprv vyššie skóre, pri zhode vyšší max_circle
    entries.sort(
        key=lambda e: (e.get("score", 0), e.get("max_circle", 0)),
        reverse=True,
    )

    # Orezať na top N
    entries = entries[:config.MAX_HIGHSCORES]

    # Uistiť sa, že priečinok existuje
    os.makedirs(os.path.dirname(config.HIGHSCORES_PATH), exist_ok=True)

    with open(config.HIGHSCORES_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    return entries


def is_high_score(score: int) -> bool:
    """
    Zistí, či dané skóre patrí do top-10.
    Použijeme po skončení hry — ak áno, opýtame sa hráča na meno.
    """
    entries = load_scores()
    if len(entries) < config.MAX_HIGHSCORES:
        return True   # rebríček ešte nie je plný
    # Inak musí byť skóre vyššie ako najnižšie v rebríčku
    lowest = min(e.get("score", 0) for e in entries)
    return score > lowest