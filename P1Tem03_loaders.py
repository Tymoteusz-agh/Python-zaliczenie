# -*- coding: utf-8 -*-
"""
Warstwa wczytywania danych dla tematu 03 (wykres linearny).

Każdy obsługiwany format (CSV, tekst, arkusz XLSX, JSON, plik 'rc')
sprowadzamy do wspólnego pandas.DataFrame, na którym pracuje GUI.
Funkcje są czyste (wejście -> DataFrame), bez efektów ubocznych w GUI.

SZABLON: uzupełnij ciała funkcji zgodnie z P1Tem03_loaders_SPEC.md.
Nazw funkcji, nazw/typów parametrów ani typów zwracanych NIE zmieniaj.
"""

import json
from pathlib import Path

import pandas as pd

# Kolejność prób dekodowania tekstu - najpierw UTF-8, potem kodowania PL.
# (sekcja 4 specyfikacji) - krotka kodowań próbowanych po kolei.
_ENCODINGS = ("utf-8-sig", "utf-8", "cp1250", "latin-1")


def _read_table(path: str) -> pd.DataFrame:
    """Czyta CSV/tekst z auto-detekcją separatora i fallbackiem kodowania."""
    pass


def _read_excel(path: str) -> pd.DataFrame:
    """Czyta pierwszy arkusz pliku XLSX/XLS (silnik openpyxl)."""
    pass


def _json_to_frame(data) -> pd.DataFrame:
    """Sprowadza dowolną strukturę JSON do tabeli (płaskiej)."""
    pass


def _read_json(path: str) -> pd.DataFrame:
    """Wczytuje JSON i deleguje spłaszczenie do _json_to_frame."""
    pass


def _read_rc(path: str) -> pd.DataFrame:
    """
    Plik 'rc' nie ma w projekcie ustalonego formatu - przyjmujemy konwencję
    plików konfiguracyjnych 'klucz=wartosc' (linie '#' to komentarze),
    z fallbackiem do zwykłej tabeli rozdzielanej białymi znakami.
    """
    pass


# Mapowanie rozszerzenie -> funkcja czytająca (sekcja 6).
_READERS = {
    ".csv": _read_table,
    ".txt": _read_table,
    ".dat": _read_table,
    ".tsv": _read_table,
    ".xlsx": _read_excel,
    ".xls": _read_excel,
    ".json": _read_json,
    ".rc": _read_rc,
}


def load_data(path: str) -> pd.DataFrame:
    """Wczytuje plik na podstawie rozszerzenia i zwraca DataFrame."""
    pass


def numeric_columns(df: pd.DataFrame) -> list:
    """
    Zwraca kolumny nadające się na oś liczbową - takie, których większość
    wartości da się rzutować na liczby. Kolumny tekstowe (nazwy) pomijamy,
    bo nie da się ich sensownie nanieść na wykres linearny.
    """
    
    pass
