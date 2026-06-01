# -*- coding: utf-8 -*-
"""
Temat 03 - wykres linearny (pandas + matplotlib + tkinter).

Plik wejściowy modułu. Cienka warstwa spinająca:
  * P1Tem03_loaders - wczytywanie danych z różnych formatów,
  * P1Tem03_gui     - interfejs graficzny i rysowanie wykresu.

Uruchomienie:
  * z aplikacji głównej: App2026N wywołuje eXecute(win, label),
  * samodzielnie z konsoli: py P1Tem03.py
"""

import os
from pathlib import Path

# Ujednolicenie katalogu roboczego - działa zarówno w pakiecie, jak i standalone.
os.chdir(Path(__file__).resolve().parent)

try:
    from .P1Tem03_gui import build_gui
except ImportError:  # uruchomienie bezpośrednie (py P1Tem03.py)
    from P1Tem03_gui import build_gui


def eXecute(wn=None, _ml=None):
    """
    Punkt wejścia wywoływany przez aplikację główną.
    Gdy podano okno rodzica (wn) - tworzymy Toplevel (pętla zdarzeń już działa).
    W trybie samodzielnym tworzymy własne okno Tk i uruchamiamy mainloop.
    """
    import tkinter as tk

    if wn is None:
        root = tk.Tk()
        build_gui(root)
        root.mainloop()
    else:
        root = tk.Toplevel(wn)
        root.focus()
        build_gui(root)


# =======================

if __name__ == "__main__":
    eXecute()
