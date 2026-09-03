# CrossMatch

Web app for finding matching rows across multiple Excel or CSV files.

## Features

- Drag-and-drop Excel (`.xlsx`, `.xlsm`) and CSV files
- Automatic column selection — no need to pick a key column manually
- Datetime columns (e.g. export timestamps) are excluded automatically
- Matches rows that appear in **at least two** of the uploaded files
- Shows pairwise overlap between files
- Download results as Excel or CSV

## Getting started

### With Docker

```bash
docker compose up --build
```

The app is available at [http://localhost:5002](http://localhost:5002).

### Without Docker

```bash
pip install -r requirements.txt
python app.py
```

## Tech

- Python 3.12
- Flask
- openpyxl
