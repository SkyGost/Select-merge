"""
Zvukový systém pre Connect-Merge.
Používa iba winsound — žiadne externé knižnice.

Opravy:
- zvuk funguje okamžite pri prvom zažmúrení (vlastné vlákno)
- žiadne hromadenie vlákien pri rýchlom klikání (max 2 súčasne)
- pitch efekt cez kratšie WAV (načítané do pamäti ako bytes)
"""

import os
import threading
import time
import wave
import struct

SOUND_ENABLED = True

_BASE = os.path.dirname(os.path.abspath(__file__))
_CLICK_PATH = os.path.join(_BASE, "..", "assets", "click.wav")
_MERGE_PATH  = os.path.join(_BASE, "..", "assets", "merge.wav")

try:
    import winsound
    _WINSOUND_OK = True
except ImportError:
    _WINSOUND_OK = False

# Počet aktívnych vlákien — aby sa nehromadili
_active_threads = 0
_thread_lock = threading.Lock()
MAX_THREADS = 2

# Čas posledného kliku — na pitch efekt
_last_click_time: float = 0.0

# Cache pre upravené WAV dáta (speed -> bytes)
_click_cache: dict = {}
_merge_bytes: bytes = b""


def _read_wav_bytes(path: str) -> bytes:
    """Načíta WAV súbor ako raw bytes pre winsound.PlaySound."""
    try:
        with open(path, "rb") as f:
            return f.read()
    except Exception:
        return b""


def _change_wav_speed(data: bytes, speed: float) -> bytes:
    """
    Zmení rýchlosť WAV súboru zmenou sample rate v hlavičke.
    Jednoduchý pitch shift — rovnaký trik ako zmena frekvencie mixera.
    Funguje iba so štandardnými PCM WAV súbormi.
    """
    try:
        import io
        with wave.open(io.BytesIO(data)) as wf:
            nchannels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            frames    = wf.readframes(wf.getnframes())

        new_rate = int(framerate * speed)

        out = io.BytesIO()
        with wave.open(out, "wb") as wf2:
            wf2.setnchannels(nchannels)
            wf2.setsampwidth(sampwidth)
            wf2.setframerate(new_rate)
            wf2.writeframes(frames)

        return out.getvalue()
    except Exception:
        return data


def init() -> None:
    """
    Predpripraví zvukové dáta do pamäti.
    Zavolaj raz v main.py pred app.mainloop().
    """
    global _merge_bytes

    if not _WINSOUND_OK or not SOUND_ENABLED:
        return

    # Načítať merge zvuk
    if os.path.exists(_MERGE_PATH):
        _merge_bytes = _read_wav_bytes(_MERGE_PATH)

    # Predpripraviť click zvuky pre rôzne rýchlosti
    if os.path.exists(_CLICK_PATH):
        raw = _read_wav_bytes(_CLICK_PATH)
        for speed in [1.0, 1.3, 1.6, 2.0]:
            _click_cache[speed] = _change_wav_speed(raw, speed)

    # Predhriatie winsound — tichý prázdny zvuk
    try:
        winsound.PlaySound(None, winsound.SND_PURGE)
    except Exception:
        pass


def _get_pitch_speed() -> float:
    """Vráti faktor rýchlosti podľa intervalu medzi klikmi."""
    global _last_click_time
    now = time.monotonic()
    interval = now - _last_click_time
    _last_click_time = now

    if interval < 0.10:
        return 2.0
    elif interval < 0.20:
        return 1.6
    elif interval < 0.35:
        return 1.3
    else:
        return 1.0


def _play_bytes(data: bytes) -> None:
    """Prehrá WAV bytes v samostatnom vlákne."""
    global _active_threads

    if not data:
        return

    with _thread_lock:
        if _active_threads >= MAX_THREADS:
            return
        _active_threads += 1

    def _run():
        global _active_threads
        try:
            winsound.PlaySound(data, winsound.SND_MEMORY)
        except Exception:
            pass
        finally:
            with _thread_lock:
                global _active_threads
                _active_threads -= 1

    t = threading.Thread(target=_run, daemon=True)
    t.start()


def play_click() -> None:
    """Prehrá klik — okamžite, s pitch efektom pri rýchlom klikání."""
    if not _WINSOUND_OK or not SOUND_ENABLED or not _click_cache:
        return
    speed = _get_pitch_speed()
    # Nájsť najbližšiu predpripravenú rýchlosť
    closest = min(_click_cache.keys(), key=lambda s: abs(s - speed))
    _play_bytes(_click_cache[closest])


def play_merge() -> None:
    """Prehrá merge pop zvuk."""
    if not _WINSOUND_OK or not SOUND_ENABLED:
        return
    _play_bytes(_merge_bytes)