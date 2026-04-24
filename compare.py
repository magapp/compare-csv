#!/usr/bin/env python3
"""Jämför CSV-filer och hittar värden som förekommer i alla filer."""

import csv
import sys
import os
from collections import defaultdict


def read_csv(path):
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        rows = list(reader)
    return rows


def main():
    # Hitta alla *_utf8.csv-filer i samma katalog, eller ange filer som argument
    if len(sys.argv) > 1:
        files = sys.argv[1:]
    else:
        directory = os.path.dirname(os.path.abspath(__file__))
        files = sorted(
            os.path.join(directory, f)
            for f in os.listdir(directory)
            if f.endswith("_utf8.csv")
        )

    if len(files) < 2:
        print("Behöver minst 2 CSV-filer att jämföra.")
        sys.exit(1)

    print(f"Läser {len(files)} filer:")
    all_data = {}
    for path in files:
        rows = read_csv(path)
        all_data[os.path.basename(path)] = rows
        print(f"  {os.path.basename(path)}: {len(rows)} rader")

    # Visa tillgängliga kolumner
    first_file = list(all_data.values())[0]
    columns = list(first_file[0].keys())
    print(f"\nTillgängliga kolumner:")
    for i, col in enumerate(columns, 1):
        print(f"  {i}. {col}")

    choice = input("\nVilken kolumn vill du jämföra? (nummer eller namn): ").strip()
    if choice.isdigit():
        col_name = columns[int(choice) - 1]
    else:
        col_name = choice

    print(f"\nJämför på kolumn: {col_name}\n")

    # Samla unika värden per fil (exkludera tomma)
    sets_per_file = {}
    for fname, rows in all_data.items():
        values = {row[col_name].strip() for row in rows if row[col_name].strip()}
        sets_per_file[fname] = values
        print(f"  {fname}: {len(values)} unika värden")

    # Hitta gemensamma värden (finns i ALLA filer)
    common = set.intersection(*sets_per_file.values())
    print(f"\n{'='*60}")
    print(f"Värden som förekommer i ALLA {len(files)} filer: {len(common)}")
    print(f"{'='*60}")

    if common:
        for val in sorted(common):
            print(f"  {val}")

    # Visa även parvis överlapp
    filenames = list(sets_per_file.keys())
    print(f"\nParvis överlapp:")
    for i in range(len(filenames)):
        for j in range(i + 1, len(filenames)):
            overlap = sets_per_file[filenames[i]] & sets_per_file[filenames[j]]
            print(f"  {filenames[i]} & {filenames[j]}: {len(overlap)} gemensamma")

    # Exportera gemensamma rader till en ny fil
    if common:
        export = input("\nVill du exportera alla rader med gemensamma värden? (j/n): ").strip().lower()
        if export == "j":
            outpath = os.path.join(
                os.path.dirname(os.path.abspath(files[0])),
                f"gemensamma_{col_name}.csv",
            )
            with open(outpath, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["Källa"] + columns, delimiter=";")
                writer.writeheader()
                for fname, rows in all_data.items():
                    for row in rows:
                        if row[col_name].strip() in common:
                            writer.writerow({"Källa": fname, **row})
            print(f"Exporterat till {outpath}")


if __name__ == "__main__":
    main()
