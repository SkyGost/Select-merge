"""
Konfiguračné konštanty pre hru Connect-Merge.
Tu sú všetky "magické čísla" a hodnoty na jednom mieste.
"""

# --- Rozmery hracieho poľa ---
BOARD_SIZE = 5          # 5x5 mriežka
CELL_SIZE = 120         # veľkosť bunky v pixeloch (väčšie ako predtým)
CIRCLE_RADIUS = 48      # polomer kruhu v pixeloch (väčšie kruhy)
BOARD_PADDING = 30      # okraj okolo poľa
BOARD_CORNER_RADIUS = 25   # zaoblenie rohov hracieho poľa

# --- Herná logika ---
INITIAL_MAX_VALUE = 64  # maximálna hodnota kruhov pri štarte hry
                        # spawnujú sa hodnoty 2, 4, 8, 16, 32 (menšie ako 64)
MIN_LINE_LENGTH = 2     # minimálna dĺžka spojnice (aspoň 2 kruhy)

# --- Farby pre jednotlivé hodnoty kruhov (podľa referencie) ---
# Sýte, jasné farby — biely text na všetkých
CIRCLE_COLORS = {
    2:    "#f5b942",   # oranžová
    4:    "#e85d3a",   # červená
    8:    "#5cc35c",   # zelená
    16:   "#5db9e8",   # svetlo modrá
    32:   "#e85a8c",   # ružová
    64:   "#4dc9a8",   # tyrkysová
    128:  "#6680d4",   # tmavšie modrá
    256:  "#c97fd4",   # fialová
    512:  "#f5c842",   # zlatá
    1024: "#ff8c00",   # tmavo oranžová
    2048: "#3c3a32",   # tmavá
    4096: "#2c2a22",   # ešte tmavšia
}
DEFAULT_CIRCLE_COLOR = "#3c3a32"

# --- Farby textu ---
# Podľa referencie: biely text na všetkých farebných kruhoch
TEXT_COLOR_LIGHT = "#ffffff"       # biely text (vždy na kruhoch)
TEXT_COLOR_DARK = "#776e65"        # tmavý text (pre nadpisy a UI)

# --- Farby UI ---
BG_COLOR = "#ffffff"               # biele pozadie okna
BOARD_BG_COLOR = "#f7f7f7"         # svetlo-sivé pozadie hracieho poľa
BOARD_BORDER_COLOR = "#e0e0e0"     # jemný okraj okolo poľa
EMPTY_CELL_COLOR = "#f7f7f7"       # prázdna bunka splýva s pozadím
LINE_COLOR = "#999999"             # jemnejšia farba spojnice
LINE_WIDTH = 8                     # hrubšia čiara

# --- Animácia ---
ANIMATION_FPS = 60
ANIMATION_INTERVAL_MS = 1000 // ANIMATION_FPS
FALL_SPEED = 30

# --- Rebríček ---
MAX_HIGHSCORES = 10
HIGHSCORES_PATH = "assets/highscores.json"

# --- Texty (slovenčina) ---
TXT_TITLE = "Connect-Merge"
TXT_PLAY = "Hrať"
TXT_HIGHSCORES = "Rebríček"
TXT_EXIT = "Koniec"
TXT_SCORE = "Skóre"
TXT_MAX_CIRCLE = "Najväčší kruh"
TXT_GAME_OVER = "Koniec hry"
TXT_ENTER_NICK = "Zadajte prezývku:"
TXT_SAVE = "Uložiť"
TXT_BACK = "Späť"
TXT_NICK = "Prezývka"
TXT_DATE = "Dátum"