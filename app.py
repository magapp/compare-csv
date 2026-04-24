#!/usr/bin/env python3
"""Webapp för att jämföra CSV-filer och hitta gemensamma värden."""

import csv
import io
import os
from flask import Flask, render_template_string, request, Response

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

HTML = """
<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSV-jämförare</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: system-ui, sans-serif; background: #f5f5f5; color: #333; padding: 2rem; }
        h1 { margin-bottom: 1.5rem; }
        .drop-zone {
            border: 3px dashed #aaa; border-radius: 12px; padding: 3rem;
            text-align: center; background: #fff; cursor: pointer;
            transition: border-color .2s, background .2s; margin-bottom: 1rem;
        }
        .drop-zone.over { border-color: #2563eb; background: #eff6ff; }
        .drop-zone p { font-size: 1.1rem; color: #666; }
        .file-list { margin: 1rem 0; }
        .file-list span {
            display: inline-block; background: #e0e7ff; color: #3730a3;
            padding: .3rem .7rem; border-radius: 6px; margin: .2rem; font-size: .9rem;
        }
        .file-list span button {
            background: none; border: none; color: #6366f1; cursor: pointer;
            font-weight: bold; margin-left: .3rem;
        }
        select, button[type=submit] {
            font-size: 1rem; padding: .5rem 1rem; border-radius: 6px; border: 1px solid #ccc;
        }
        button[type=submit] {
            background: #2563eb; color: #fff; border: none; cursor: pointer;
            margin-left: .5rem;
        }
        button[type=submit]:hover { background: #1d4ed8; }
        button[type=submit]:disabled { background: #93c5fd; cursor: not-allowed; }
        .controls { margin: 1rem 0; display: flex; align-items: center; gap: .5rem; flex-wrap: wrap; }
        .results { margin-top: 2rem; }
        .results h2 { margin-bottom: .5rem; }
        .summary { background: #fff; padding: 1rem 1.5rem; border-radius: 8px; margin-bottom: 1rem; }
        .summary p { margin: .3rem 0; }
        table {
            width: 100%; border-collapse: collapse; background: #fff;
            border-radius: 8px; overflow: hidden; font-size: .85rem;
        }
        th, td { padding: .5rem .7rem; border-bottom: 1px solid #eee; text-align: left; }
        th { background: #f8fafc; position: sticky; top: 0; }
        .table-wrap { max-height: 500px; overflow: auto; border-radius: 8px; border: 1px solid #ddd; }
        .download-btn {
            display: inline-block; margin-top: 1rem; padding: .5rem 1.2rem;
            background: #16a34a; color: #fff; border-radius: 6px;
            text-decoration: none; font-size: .95rem;
        }
        .download-btn:hover { background: #15803d; }
        .pair { display: inline-block; background: #fef3c7; padding: .2rem .6rem; border-radius: 4px; margin: .15rem; font-size: .85rem; }
    </style>
</head>
<body>
    <h1>CSV-jämförare</h1>

    <form id="form" method="POST" enctype="multipart/form-data">
        <div class="drop-zone" id="dropZone">
            <p>Dra och släpp CSV-filer här, eller klicka för att välja</p>
            <input type="file" name="files" id="fileInput" multiple accept=".csv" style="display:none">
        </div>
        <div class="file-list" id="fileList"></div>

        {% if columns %}
        <div class="controls">
            <label for="column">Jämför på kolumn:</label>
            <select name="column" id="column">
                {% for col in columns %}
                <option value="{{ col }}" {{ 'selected' if col == selected_column }}>{{ col }}</option>
                {% endfor %}
            </select>
            <button type="submit" name="action" value="compare">Jämför</button>
        </div>
        {% endif %}
    </form>

    {% if results %}
    <div class="results">
        <div class="summary">
            <h2>Resultat</h2>
            <p><strong>Kolumn:</strong> {{ selected_column }}</p>
            <p><strong>Antal filer:</strong> {{ results.file_count }}</p>
            {% for fname, count in results.file_stats %}
            <p>&nbsp;&nbsp;{{ fname }}: {{ count }} unika värden</p>
            {% endfor %}
            <p style="margin-top:.5rem"><strong>Gemensamma värden (finns i alla filer):</strong> {{ results.common_count }}</p>
            <p style="margin-top:.5rem"><strong>Parvis överlapp:</strong></p>
            {% for pair, count in results.pairwise %}
            <span class="pair">{{ pair }}: {{ count }}</span>
            {% endfor %}
        </div>

        {% if results.common_count > 0 %}
        <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>Källa</th>
                        {% for col in results.headers %}
                        <th>{{ col }}</th>
                        {% endfor %}
                    </tr>
                </thead>
                <tbody>
                    {% for row in results.rows %}
                    <tr>
                        {% for cell in row %}
                        <td>{{ cell }}</td>
                        {% endfor %}
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        <a class="download-btn" href="/download" target="_blank">Ladda ner som CSV</a>
        {% endif %}
    </div>
    {% endif %}

    <script>
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const fileList = document.getElementById('fileList');
        const form = document.getElementById('form');
        let storedFiles = [];

        // Restore files from previous upload if we have columns but no compare results
        {% if columns and not results %}
        // Auto-submit happens server-side, no need to restore
        {% endif %}

        dropZone.addEventListener('click', () => fileInput.click());
        dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('over'); });
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('over'));
        dropZone.addEventListener('drop', e => {
            e.preventDefault();
            dropZone.classList.remove('over');
            addFiles(e.dataTransfer.files);
        });
        fileInput.addEventListener('change', () => addFiles(fileInput.files));

        function addFiles(newFiles) {
            for (const f of newFiles) {
                if (!storedFiles.some(s => s.name === f.name && s.size === f.size)) {
                    storedFiles.push(f);
                }
            }
            renderList();
            if (storedFiles.length >= 2) autoSubmit();
        }

        function removeFile(idx) {
            storedFiles.splice(idx, 1);
            renderList();
        }

        function renderList() {
            fileList.innerHTML = storedFiles.map((f, i) =>
                `<span>${f.name} <button onclick="removeFile(${i})">✕</button></span>`
            ).join('');
        }

        function autoSubmit() {
            const dt = new DataTransfer();
            storedFiles.forEach(f => dt.items.add(f));
            fileInput.files = dt.files;
            // Submit to get columns
            const fd = new FormData(form);
            fd.delete('files');
            storedFiles.forEach(f => fd.append('files', f));
            fd.set('action', 'upload');

            fetch('/', { method: 'POST', body: fd })
                .then(r => r.text())
                .then(html => {
                    const doc = new DOMParser().parseFromString(html, 'text/html');
                    const newControls = doc.querySelector('.controls');
                    const oldControls = document.querySelector('.controls');
                    if (newControls) {
                        if (oldControls) oldControls.replaceWith(newControls);
                        else form.appendChild(newControls);
                    }
                    // Re-bind submit
                    rebindForm();
                });
        }

        function rebindForm() {
            const btn = form.querySelector('button[type=submit]');
            if (btn) {
                btn.addEventListener('click', e => {
                    // Make sure files are attached
                    const dt = new DataTransfer();
                    storedFiles.forEach(f => dt.items.add(f));
                    fileInput.files = dt.files;
                });
            }
        }
        rebindForm();
    </script>
</body>
</html>
"""

# Global store for the last comparison result (for download)
last_result = {}


def parse_csv(file_storage):
    text = file_storage.read().decode("utf-8-sig")
    # Detect delimiter
    first_line = text.split("\n", 1)[0]
    delimiter = ";" if ";" in first_line else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    rows = list(reader)
    return rows, list(reader.fieldnames) if reader.fieldnames else []


@app.route("/", methods=["GET", "POST"])
def index():
    columns = []
    selected_column = None
    results = None

    if request.method == "POST":
        files = request.files.getlist("files")
        files = [f for f in files if f.filename]

        if len(files) < 2:
            return render_template_string(HTML, columns=[], results=None, selected_column=None)

        all_data = {}
        headers = []
        for f in files:
            rows, hdrs = parse_csv(f)
            all_data[f.filename] = rows
            if not headers:
                headers = hdrs

        columns = headers
        action = request.form.get("action", "upload")

        if action == "compare":
            selected_column = request.form.get("column", headers[0])
            sets_per_file = {}
            for fname, rows in all_data.items():
                values = {row.get(selected_column, "").strip() for row in rows}
                values.discard("")
                sets_per_file[fname] = values

            common = set.intersection(*sets_per_file.values()) if sets_per_file else set()

            # Pairwise
            filenames = list(sets_per_file.keys())
            pairwise = []
            for i in range(len(filenames)):
                for j in range(i + 1, len(filenames)):
                    overlap = sets_per_file[filenames[i]] & sets_per_file[filenames[j]]
                    pairwise.append((f"{filenames[i]} & {filenames[j]}", len(overlap)))

            # Build result rows
            result_rows = []
            for fname, rows in all_data.items():
                for row in rows:
                    if row.get(selected_column, "").strip() in common:
                        result_rows.append([fname] + [row.get(h, "") for h in headers])

            results = {
                "file_count": len(all_data),
                "file_stats": [(fn, len(s)) for fn, s in sets_per_file.items()],
                "common_count": len(common),
                "pairwise": pairwise,
                "headers": headers,
                "rows": result_rows,
            }

            # Store for download
            last_result["headers"] = headers
            last_result["rows"] = result_rows

    return render_template_string(HTML, columns=columns, results=results, selected_column=selected_column)


@app.route("/download")
def download():
    if not last_result.get("rows"):
        return "Inget resultat att ladda ner", 404

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["Källa"] + last_result["headers"])
    for row in last_result["rows"]:
        writer.writerow(row)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=gemensamma.csv"},
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5002)
