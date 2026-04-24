# CSV-jämförare

Webbapp och CLI-verktyg för att jämföra CSV-filer och hitta gemensamma värden baserat på en vald kolumn.

## Funktioner

- Dra-och-släpp av CSV-filer i webbgränssnittet
- Automatisk detektering av delimiter (`;` eller `,`)
- Jämförelse på valfri kolumn
- Visar parvis överlapp mellan filer
- Exportera gemensamma rader som CSV
- CLI-version för terminalanvändning

## Kom igång

### Med Docker

```bash
docker compose up --build
```

Appen finns sedan på [http://localhost:5002](http://localhost:5002).

### Utan Docker

```bash
pip install -r requirements.txt
python app.py
```

### CLI

```bash
python compare.py fil1.csv fil2.csv
```

Utan argument letar skriptet efter `*_utf8.csv`-filer i samma katalog.

## Teknik

- Python 3.12
- Flask
