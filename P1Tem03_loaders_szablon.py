# -*- coding: utf-8 -*-
"""
Warstwa wczytywania danych dla tematu 03 (wykres linearny).

Każdy obsługiwany format (CSV, tekst, arkusz XLSX, JSON, plik 'rc')
sprowadzamy do wspólnego pandas.DataFrame, na którym pracuje GUI.
Funkcje są czyste (wejście -> DataFrame), bez efektów ubocznych w GUI.
"""

import json
from pathlib import Path

import pandas as pd

# Kolejność prób dekodowania tekstu - najpierw UTF-8, potem kodowania PL.
_ENCODINGS = ("utf-8-sig", "utf-8", "cp1250", "latin-1")


def _read_table(path: str) -> pd.DataFrame:
    """Czyta CSV/tekst z auto-detekcją separatora i fallbackiem kodowania."""
    last_error = None
    for enc in _ENCODINGS:
        try:
            # sep=None + engine='python' -> sniffer rozpozna ',', ';', tab, spacje
            return pd.read_csv(path, sep=None, engine="python", encoding=enc)
        except (UnicodeDecodeError, UnicodeError) as err:
            last_error = err
    raise last_error


def _read_excel(path: str) -> pd.DataFrame:
    """Czyta pierwszy arkusz pliku XLSX/XLS (silnik openpyxl)."""
    return pd.read_excel(path)


def _json_to_frame(data) -> pd.DataFrame:
    """Sprowadza dowolną strukturę JSON do tabeli (płaskiej)."""
    # 1) lista rekordów: [{...}, {...}] - najczęstszy przypadek
    if isinstance(data, list):
        return pd.json_normalize(data)

    if isinstance(data, dict):
        # 2) obiekt z zagnieżdżoną listą rekordów -> bierzemy pierwszą listę
        for value in data.values():
            if isinstance(value, list):
                return pd.json_normalize(value)
        # 3) słownik słowników (rekordy pod kluczami) -> spłaszczamy
        if any(isinstance(value, dict) for value in data.values()):
            return pd.json_normalize(data)
        # 4) prosta mapa klucz->wartość -> dwie kolumny
        return pd.DataFrame({"klucz": list(data.keys()),
                             "wartosc": list(data.values())})

    # 5) wartość skalarna
    return pd.DataFrame({"wartosc": [data]})


def _read_json(path: str) -> pd.DataFrame:
    """Wczytuje JSON i deleguje spłaszczenie do _json_to_frame."""
    for enc in _ENCODINGS:
        try:
            with open(path, encoding=enc) as handle:
                return _json_to_frame(json.load(handle))
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise ValueError("Nie udało się zdekodować pliku JSON.")


def _read_rc(path: str) -> pd.DataFrame:
    """
    Plik 'rc' nie ma w projekcie ustalonego formatu - przyjmujemy konwencję
    plików konfiguracyjnych 'klucz=wartosc' (linie '#' to komentarze),
    z fallbackiem do zwykłej tabeli rozdzielanej białymi znakami.
    """
    rows = []
    for enc in _ENCODINGS:
        try:
            with open(path, encoding=enc) as handle:
                for line in handle:
                    line = line.strip()
                    if not line or line.startswith(("#", ";")):
                        continue
                    for sep in ("=", ":"):
                        if sep in line:
                            key, value = line.split(sep, 1)
                            rows.append((key.strip(), value.strip()))
                            break
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    if rows:
        return pd.DataFrame(rows, columns=["klucz", "wartosc"])
    # brak par klucz=wartosc -> traktujemy plik jak tabelę tekstową
    return _read_table(path)


# Mapowanie rozszerzenie -> funkcja czytająca.
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
    reader = _READERS.get(Path(path).suffix.lower(), _read_table)
    df = reader(path)
    if df.empty:
        raise ValueError("Plik nie zawiera żadnych danych.")
    return df


def numeric_columns(df: pd.DataFrame) -> list:
    """
    Zwraca kolumny nadające się na oś liczbową - takie, których większość
    wartości da się rzutować na liczby. Kolumny tekstowe (nazwy) pomijamy,
    bo nie da się ich sensownie nanieść na wykres linearny.
    """
    result = []
    for column in df.columns:
        coerced = pd.to_numeric(df[column], errors="coerce")
        if coerced.notna().sum() >= max(1, len(coerced) // 2):
            result.append(column)
    return result
