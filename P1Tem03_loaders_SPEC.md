# Specyfikacja modułu `P1Tem03_loaders.py`

Dokument przeznaczony dla developera implementującego moduł od zera.
Należy odtworzyć moduł **dokładnie** według poniższych nazw, sygnatur, typów
i zachowań. Nazwy funkcji, nazwy parametrów, kolejność parametrów oraz typy
zwracane są częścią kontraktu (moduł jest importowany przez GUI) i **nie wolno
ich zmieniać**.

---

## 1. Cel i rola modułu

Moduł stanowi **warstwę wczytywania danych** dla tematu 03 (rysowanie wykresu
liniowego). Jego zadaniem jest sprowadzenie różnych formatów plików wejściowych
(CSV, tekst, arkusz Excel, JSON, plik typu „rc”) do **jednego wspólnego
`pandas.DataFrame`**, na którym dalej pracuje GUI.

Zasady ogólne:

- Funkcje są **czyste**: wejście (ścieżka / dane) → `DataFrame`. Brak efektów
  ubocznych związanych z GUI, brak `print`, brak okien dialogowych.
- Obsługa kodowań tekstu odbywa się przez próbowanie listy kodowań po kolei.
- Błędy sygnalizowane są wyjątkami (patrz sekcja 7) — GUI łapie je samo.

---

## 2. Kontekst użycia (kontrakt z GUI)

Plik `P1Tem03_gui.py` importuje z tego modułu **dwie funkcje publiczne**:

```python
from P1Tem03_loaders import load_data, numeric_columns
```

i używa ich tak:

```python
df = load_data(path)            # path: str ze ścieżką do pliku
cols = list(df.columns)         # lista nazw kolumn
numeric = numeric_columns(df)   # lista nazw kolumn liczbowych
```

Wnioski wiążące dla implementacji:

- `load_data` przyjmuje **jeden** argument typu `str` (ścieżka) i zwraca
  `pandas.DataFrame`.
- `numeric_columns` przyjmuje `DataFrame` i zwraca **listę nazw kolumn**
  (a nie listę `Series`), tak żeby dało się je podstawić do listy rozwijanej.
- GUI obsługuje rozszerzenia: `*.csv *.txt *.dat *.tsv *.xlsx *.xls *.json *.rc`
  — moduł musi je wszystkie umieć wczytać.

---

## 3. Zależności (importy)

Na górze pliku, w tej kolejności:

```python
# -*- coding: utf-8 -*-
import json
from pathlib import Path

import pandas as pd
```

- `json` — wczytywanie plików JSON.
- `pathlib.Path` — wyłącznie do wyciągnięcia rozszerzenia (`.suffix`).
- `pandas` (alias `pd`) — główna biblioteka tabel; wymaga też zainstalowanego
  `openpyxl` dla obsługi `.xlsx`.

---

## 4. Stała modułu

```python
_ENCODINGS = ("utf-8-sig", "utf-8", "cp1250", "latin-1")
```

- **Nazwa:** `_ENCODINGS` (z podkreślnikiem — prywatna dla modułu).
- **Typ:** `tuple[str, ...]`.
- **Znaczenie:** kolejność prób dekodowania tekstu. Najpierw UTF-8
  (z BOM i bez), potem typowe kodowania polskie (`cp1250`), na końcu
  `latin-1` jako ostateczny fallback (praktycznie zawsze „się uda”, choć
  może źle zmapować znaki — dlatego jest ostatni).
- **Kolejność jest istotna** i nie należy jej zmieniać.

---

## 5. Funkcje pomocnicze (prywatne, prefiks `_`)

Wszystkie poniższe są wewnętrzne — nie są importowane przez GUI, ale ich nazwy
i zachowania są elementem specyfikacji (są używane w słowniku `_READERS`).

### 5.1 `_read_table(path: str) -> pd.DataFrame`

- **Cel:** wczytać CSV/plik tekstowy z **automatyczną detekcją separatora**
  i fallbackiem kodowania.
- **Parametr:** `path: str` — ścieżka do pliku.
- **Zwraca:** `pd.DataFrame`.
- **Logika:**
  1. Iteruj po kodowaniach z `_ENCODINGS`.
  2. Dla każdego spróbuj:
     `pd.read_csv(path, sep=None, engine="python", encoding=enc)`.
     - `sep=None` + `engine="python"` uruchamia sniffer, który sam rozpozna
       separator: `,`, `;`, tabulator, spacje.
  3. Jeśli rzucony zostanie `UnicodeDecodeError` lub `UnicodeError` — zapamiętaj
     wyjątek w zmiennej `last_error` i próbuj kolejne kodowanie.
  4. Jeśli wszystkie kodowania zawiodły — `raise last_error` (przekaż ostatni
     złapany wyjątek dalej).
- **Uwaga:** inne wyjątki niż dekodowania (np. `ParserError`) **nie są**
  łapane — mają się propagować na zewnątrz.

### 5.2 `_read_excel(path: str) -> pd.DataFrame`

- **Cel:** wczytać **pierwszy arkusz** pliku XLSX/XLS.
- **Parametr:** `path: str`.
- **Zwraca:** `pd.DataFrame`.
- **Logika:** jednolinijkowo `return pd.read_excel(path)` (domyślny silnik,
  pierwszy arkusz). Nie obsługujemy kodowań — to format binarny.

### 5.3 `_json_to_frame(data) -> pd.DataFrame`

- **Cel:** sprowadzić **dowolną** strukturę JSON (już zdeserializowaną do
  obiektów Pythona) do płaskiej tabeli.
- **Parametr:** `data` — bez adnotacji typu (może być `list`, `dict`,
  lub wartość skalarna).
- **Zwraca:** `pd.DataFrame`.
- **Logika — kolejność warunków jest istotna:**
  1. Jeśli `isinstance(data, list)`: `return pd.json_normalize(data)`
     (lista rekordów `[{...}, {...}]` — najczęstszy przypadek).
  2. Jeśli `isinstance(data, dict)`:
     - a) Iteruj po `data.values()`; jeśli któraś wartość jest `list` —
       `return pd.json_normalize(value)` (obiekt z zagnieżdżoną listą rekordów;
       bierzemy **pierwszą** napotkaną listę).
     - b) Jeśli którakolwiek wartość jest `dict`
       (`any(isinstance(value, dict) for value in data.values())`) —
       `return pd.json_normalize(data)` (słownik słowników → spłaszczenie).
     - c) W przeciwnym razie — prosta mapa klucz→wartość, zwróć:
       ```python
       pd.DataFrame({"klucz": list(data.keys()),
                     "wartosc": list(data.values())})
       ```
  3. W przeciwnym razie (wartość skalarna):
     `return pd.DataFrame({"wartosc": [data]})`.
- **Nazwy kolumn:** dosłownie `"klucz"` i `"wartosc"` (bez polskich znaków
  w nazwie `wartosc` — celowo, jak w oryginale).

### 5.4 `_read_json(path: str) -> pd.DataFrame`

- **Cel:** wczytać plik JSON i oddelegować spłaszczenie do `_json_to_frame`.
- **Parametr:** `path: str`.
- **Zwraca:** `pd.DataFrame`.
- **Logika:**
  1. Iteruj po `_ENCODINGS`.
  2. Dla każdego kodowania: otwórz plik
     (`with open(path, encoding=enc) as handle:`),
     wczytaj `json.load(handle)` i zwróć `_json_to_frame(...)` z wyniku.
  3. Przy `UnicodeDecodeError` / `UnicodeError` — `continue` (kolejne kodowanie).
  4. Jeśli żadne kodowanie nie zadziała —
     `raise ValueError("Nie udało się zdekodować pliku JSON.")`
     (komunikat dosłownie taki).

### 5.5 `_read_rc(path: str) -> pd.DataFrame`

- **Cel:** wczytać plik typu „rc” (konfiguracyjny). Projekt nie ma ustalonego
  formatu, więc przyjmujemy konwencję `klucz=wartosc` z fallbackiem do tabeli.
- **Parametr:** `path: str`.
- **Zwraca:** `pd.DataFrame`.
- **Logika:**
  1. Utwórz pustą listę `rows = []`.
  2. Iteruj po `_ENCODINGS`; dla każdego kodowania otwórz plik i czytaj linia
     po linii:
     - `line = line.strip()`.
     - Pomiń linie puste oraz zaczynające się od `#` lub `;`
       (`line.startswith(("#", ";"))`) — to komentarze.
     - Dla separatora ze zbioru `("=", ":")` (w tej kolejności): jeśli separator
       występuje w linii, rozbij **raz** (`line.split(sep, 1)`), dodaj krotkę
       `(key.strip(), value.strip())` do `rows` i przerwij pętlę po separatorach
       (`break`).
     - Po udanym przejściu całego pliku — `break` z pętli po kodowaniach.
     - Przy `UnicodeDecodeError` / `UnicodeError` — `continue`.
  3. Jeśli `rows` niepuste — zwróć
     `pd.DataFrame(rows, columns=["klucz", "wartosc"])`.
  4. Jeśli brak par klucz=wartość (`rows` puste) — fallback:
     `return _read_table(path)` (potraktuj plik jak zwykłą tabelę tekstową).

---

## 6. Słownik mapujący `_READERS`

Po zdefiniowaniu funkcji pomocniczych, przed funkcjami publicznymi:

```python
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
```

- **Nazwa:** `_READERS`.
- **Typ:** `dict[str, Callable[[str], pd.DataFrame]]`.
- **Znaczenie:** mapuje rozszerzenie pliku (małe litery, z kropką) na funkcję
  czytającą. Klucze i przypisania muszą być dokładnie takie jak wyżej.

---

## 7. Funkcje publiczne (importowane przez GUI)

### 7.1 `load_data(path: str) -> pd.DataFrame`

- **Cel:** punkt wejścia modułu — wczytać plik na podstawie rozszerzenia
  i zwrócić `DataFrame`.
- **Parametr:** `path: str` — ścieżka do pliku.
- **Zwraca:** `pd.DataFrame` (niepusty).
- **Logika:**
  1. Wyznacz funkcję czytającą:
     `reader = _READERS.get(Path(path).suffix.lower(), _read_table)`
     — rozszerzenie sprowadzone do małych liter; **domyślnie** (nieznane
     rozszerzenie) używamy `_read_table`.
  2. `df = reader(path)`.
  3. Jeśli `df.empty` — `raise ValueError("Plik nie zawiera żadnych danych.")`
     (komunikat dosłownie).
  4. `return df`.

### 7.2 `numeric_columns(df: pd.DataFrame) -> list`

- **Cel:** zwrócić nazwy kolumn nadających się na **oś liczbową** wykresu.
  Kolumny czysto tekstowe (np. nazwy) są pomijane, bo nie da się ich sensownie
  nanieść na wykres liniowy.
- **Parametr:** `df: pd.DataFrame`.
- **Zwraca:** `list` — lista **nazw kolumn** (elementy to etykiety kolumn
  `df.columns`, najczęściej `str`).
- **Logika:**
  1. `result = []`.
  2. Dla każdej `column` w `df.columns`:
     - `coerced = pd.to_numeric(df[column], errors="coerce")`
       (wartości niekonwertowalne stają się `NaN`).
     - Jeśli liczba wartości niepustych jest **co najmniej połową** długości
       kolumny (a przynajmniej 1):
       `if coerced.notna().sum() >= max(1, len(coerced) // 2):`
       — dodaj `column` do `result`.
  3. `return result`.
- **Kryterium „większość”:** próg to `max(1, len(coerced) // 2)` — dzielenie
  całkowite. Należy zachować dokładnie ten warunek.

---

## 8. Kolejność elementów w pliku (wymagana struktura)

1. Nagłówek `# -*- coding: utf-8 -*-` i docstring modułu.
2. Importy (`json`, `pathlib.Path`, `pandas as pd`).
3. Stała `_ENCODINGS`.
4. Funkcje pomocnicze: `_read_table`, `_read_excel`, `_json_to_frame`,
   `_read_json`, `_read_rc` (w tej kolejności).
5. Słownik `_READERS`.
6. Funkcje publiczne: `load_data`, potem `numeric_columns`.

---

## 9. Lista kontrolna zgodności (acceptance criteria)

- [ ] Plik importuje się bez błędów: `import P1Tem03_loaders`.
- [ ] `load_data("dane.csv")` zwraca `DataFrame` dla CSV z separatorem `,`,
      `;`, tabulatorem lub spacjami.
- [ ] `load_data` na pliku `.xlsx` wczytuje pierwszy arkusz.
- [ ] `load_data` na `.json` obsługuje: listę rekordów, dict z zagnieżdżoną
      listą, dict dictów oraz prostą mapę klucz→wartość.
- [ ] `load_data` na `.rc` z liniami `klucz=wartosc` zwraca dwie kolumny
      `klucz`, `wartosc`; komentarze (`#`, `;`) są pomijane.
- [ ] Pusty plik → `ValueError("Plik nie zawiera żadnych danych.")`.
- [ ] Nieznane rozszerzenie trafia do `_read_table`.
- [ ] `numeric_columns` zwraca tylko kolumny, w których ≥ połowa wartości
      jest liczbowa; zwraca listę nazw, nie obiektów `Series`.
- [ ] Żadna funkcja nie wypisuje nic na ekran ani nie otwiera GUI.
