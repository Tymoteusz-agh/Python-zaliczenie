# -*- coding: utf-8 -*-
"""
Warstwa prezentacji dla tematu 03 (wykres linearny).

Rozdzielona na dwie części:
  * build_figure(...) - czysta funkcja budująca wykres matplotlib (testowalna
    bez okna, w trybie headless),
  * build_gui(...)    - lekki interfejs tkinter spinający wczytywanie danych,
    wybór osi, zamianę osi i osadzenie wykresu.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

try:
    from .P1Tem03_loaders import load_data, numeric_columns
except ImportError:  # uruchomienie standalone (py P1Tem03.py)
    from P1Tem03_loaders import load_data, numeric_columns


def build_figure(df: pd.DataFrame, x_col: str, y_col: str) -> Figure:
    """
    Buduje wykres linearny y(x). Brakujące wartości Y nie przerywają linii,
    a dodatkowo są zaznaczane czerwoną kropką u dołu osi (z wpisem w legendzie).
    """
    fig = Figure(figsize=(7.5, 4.5), dpi=100)
    ax = fig.add_subplot(111)

    y = pd.to_numeric(df[y_col], errors="coerce").to_numpy(dtype=float)

    # Oś X: liczbowa, jeśli się da; w przeciwnym razie pozycje + etykiety tekstowe.
    x_numeric = pd.to_numeric(df[x_col], errors="coerce")
    if x_numeric.notna().all():
        x = x_numeric.to_numpy(dtype=float)
        labels = None
    else:
        x = np.arange(len(df), dtype=float)
        labels = df[x_col].astype(str).to_list()

    # Linia główna - matplotlib sam pozostawia przerwy w miejscach NaN.
    ax.plot(x, y, marker="o", markersize=3, linewidth=1.6,
            color="#2c6fbb", label=y_col)

    # Zaznaczenie brakujących wartości u dołu osi.
    missing = np.isnan(y)
    if missing.any():
        base = np.nanmin(y) if np.isfinite(y).any() else 0.0
        ax.scatter(x[missing], np.full(missing.sum(), base),
                   color="#d62728", marker="o", zorder=5,
                   label="Brak danych")

    if labels is not None:
        # Przy wielu etykietach pokazujemy co n-tą, by oś pozostała czytelna.
        step = max(1, len(labels) // 12)
        ax.set_xticks(x[::step])
        ax.set_xticklabels(labels[::step], rotation=30, ha="right")

    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title(f"{y_col} w funkcji {x_col}")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    return fig


def build_gui(root: tk.Misc) -> None:
    """Buduje interfejs w przekazanym oknie (Tk lub Toplevel)."""
    root.title("Temat 03 - Wykres linearny")
    root.geometry("820x560")

    # Lekkie upiększenie: motyw 'clam' + odrobina stylu na nagłówku/przyciskach.
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")
    style.configure("Accent.TButton", padding=6)
    style.configure("Header.TLabel", font=("Segoe UI", 13, "bold"),
                    foreground="#2c6fbb")

    # Stan aplikacji trzymamy w słowniku (styl funkcyjny, bez klas).
    state = {"df": None, "canvas": None}

    ttk.Label(root, text="Wykres linearny danych",
              style="Header.TLabel").pack(pady=(10, 4))

    panel = ttk.Frame(root, padding=8)
    panel.pack(fill="x")

    ttk.Label(panel, text="Oś X:").grid(row=0, column=1, padx=(12, 4))
    cb_x = ttk.Combobox(panel, state="readonly", width=18)
    cb_x.grid(row=0, column=2)

    ttk.Label(panel, text="Oś Y:").grid(row=0, column=3, padx=(12, 4))
    cb_y = ttk.Combobox(panel, state="readonly", width=18)
    cb_y.grid(row=0, column=4)

    plot_frame = ttk.Frame(root, padding=(8, 4))
    plot_frame.pack(fill="both", expand=True)

    def redraw(*_event) -> None:
        """Przerysowuje wykres dla aktualnie wybranych kolumn."""
        if state["df"] is None or not cb_x.get() or not cb_y.get():
            return
        if state["canvas"] is not None:
            state["canvas"].get_tk_widget().destroy()
        fig = build_figure(state["df"], cb_x.get(), cb_y.get())
        canvas = FigureCanvasTkAgg(fig, master=plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        state["canvas"] = canvas

    def load() -> None:
        """Wybór pliku, wczytanie danych i ustawienie domyślnych osi."""
        path = filedialog.askopenfilename(
            title="Wybierz plik z danymi",
            filetypes=[("Wszystkie obsługiwane",
                        "*.csv *.txt *.dat *.tsv *.xlsx *.xls *.json *.rc"),
                       ("CSV / tekst", "*.csv *.txt *.dat *.tsv"),
                       ("Arkusz Excel", "*.xlsx *.xls"),
                       ("JSON", "*.json"), ("Plik rc", "*.rc"),
                       ("Wszystkie pliki", "*.*")])
        if not path:
            return
        try:
            df = state["df"] = load_data(path)
        except Exception as err:
            messagebox.showerror("Błąd wczytywania", str(err))
            return

        cols = list(df.columns)
        numeric = numeric_columns(df)
        cb_x["values"] = cols
        cb_y["values"] = cols
        # Domyślnie: X = pierwsza kolumna, Y = pierwsza sensowna (liczbowa).
        cb_x.set(cols[0])
        cb_y.set(next((c for c in numeric if c != cols[0]),
                      numeric[0] if numeric else cols[-1]))
        redraw()

    def swap() -> None:
        """Zamienia osie miejscami (wartości X <-> Y) i przerysowuje."""
        x, y = cb_x.get(), cb_y.get()
        cb_x.set(y)
        cb_y.set(x)
        redraw()

    ttk.Button(panel, text="Wczytaj plik…", style="Accent.TButton",
               command=load).grid(row=0, column=0)
    ttk.Button(panel, text="⇄ Zamień osie", command=swap).grid(
        row=0, column=5, padx=(12, 0))

    cb_x.bind("<<ComboboxSelected>>", redraw)
    cb_y.bind("<<ComboboxSelected>>", redraw)
