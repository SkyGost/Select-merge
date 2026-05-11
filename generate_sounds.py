"""
Generátor zvukových súborov pre hru.
Spustí sa raz a vytvorí WAV súbory v assets/.

Spustenie:  python generate_sounds.py
"""

import math
import os
import struct
import wave


SAMPLE_RATE = 22050   # Hz
AMPLITUDE = 16000     # hlasitosť (max 32767)


def write_wav(filename: str, samples: list) -> None:
    """Zapíše zoznam float vzoriek (-1..1) do mono 16-bit WAV súboru."""
    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
    with wave.open(filename, "w") as wf:
        wf.setnchannels(1)               # mono
        wf.setsampwidth(2)               # 16-bit
        wf.setframerate(SAMPLE_RATE)
        for s in samples:
            # Orezať na rozsah a previesť na int16
            value = int(max(-1.0, min(1.0, s)) * AMPLITUDE)
            wf.writeframes(struct.pack("<h", value))


def make_click_sound(filename: str) -> None:
    """
    Krátky, jemný "klik" zvuk pre pridanie kruhu do spojnice.
    Vysoký tón (1000 Hz), veľmi krátky (40 ms), rýchle stíšenie.
    """
    duration = 0.04           # 40 ms — veľmi krátky
    frequency = 1000          # Hz
    n_samples = int(SAMPLE_RATE * duration)

    samples = []
    for i in range(n_samples):
        t = i / SAMPLE_RATE
        # Sínusový tón
        wave_val = math.sin(2 * math.pi * frequency * t)
        # Exponenciálne stíšenie (envelope)
        envelope = math.exp(-30 * t)
        samples.append(wave_val * envelope * 0.5)   # 0.5 = polovičná hlasitosť

    write_wav(filename, samples)
    print(f"✓ Vytvorený: {filename}")


def make_merge_sound(filename: str) -> None:
    """
    "Pop" / "ding" zvuk pre úspešný merge.
    Dva tóny po sebe (klesajúce/stúpajúce), trochu dlhší (200 ms).
    """
    duration = 0.2            # 200 ms
    n_samples = int(SAMPLE_RATE * duration)

    samples = []
    for i in range(n_samples):
        t = i / SAMPLE_RATE
        # Stúpajúca frekvencia: 600 → 1200 Hz (efekt "vzostupu", odmena)
        freq = 600 + 600 * (t / duration)
        wave_val = math.sin(2 * math.pi * freq * t)
        # Pridáme druhú harmonickú pre bohatší zvuk
        wave_val += 0.3 * math.sin(2 * math.pi * freq * 2 * t)
        # Envelope: rýchly atak, pomalé stíšenie
        if t < 0.01:
            envelope = t / 0.01            # nábeh
        else:
            envelope = math.exp(-8 * (t - 0.01))
        samples.append(wave_val * envelope * 0.4)

    write_wav(filename, samples)
    print(f"✓ Vytvorený: {filename}")


if __name__ == "__main__":
    make_click_sound("assets/click.wav")
    make_merge_sound("assets/merge.wav")
    print("\nHotovo. Zvuky sú pripravené v priečinku assets/")