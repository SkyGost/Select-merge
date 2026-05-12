"""
Vstupný bod hry Connect-Merge.

Spustenie:  python main.py
"""

from ui import sounds
from ui.app import App


def main() -> None:
    sounds.init()
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()