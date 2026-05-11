"""
Jednoduchý prehrávač zvukov.

Používa winsound (vstavaný v Pythone na Windows) — bez závislostí.
Ak winsound nie je dostupný (Linux/Mac), zvuky sa proste neprehrávajú,
hra však funguje ďalej.

Funkcie:
- play_click() — krátky klik pri pridaní kruhu do spojnice
- play_merge() — "pop" zvuk pri úspešnom spojení
"""

import os

# Pokúsime sa naimportovať winsound — funguje len na Windows
try:
    import winsound
    _SOUND_AVAILABLE = True
except ImportError:
    _SOUND_AVAILABLE = False


# Príznak — ak chceš zvuky vypnúť, daj na False
SOUND_ENABLED = True

# Cesty k súborom (relatívne ku koreňu projektu)
_CLICK_PATH = os.path.join("assets", "click.wav")
_MERGE_PATH = os.path.join("assets", "merge.wav")


def _play(path: str) -> None:
    """Prehrá zvuk asynchrónne (nezablokuje UI)."""
    if not SOUND_ENABLED or not _SOUND_AVAILABLE:
        return
    if not os.path.exists(path):
        return
    try:
        # SND_ASYNC = nečakaj, kým dohrá
        # SND_FILENAME = path je názov súboru
        winsound.PlaySound(
            path,
            winsound.SND_FILENAME | winsound.SND_ASYNC,
        )
    except Exception:
        # Tichá chyba — zvuky nie sú kritické pre hru
        pass


def play_click() -> None:
    """Krátky klik pri pridaní kruhu do spojnice."""
    _play(_CLICK_PATH)


def play_merge() -> None:
    """Zvuk pri úspešnom merge."""
    _play(_MERGE_PATH)