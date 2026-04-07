import csv, json, os

csv_path = os.path.join(os.path.dirname(__file__), "WZ_2025-DE-2026-03-30-Gliederung__1_.csv")
out_path = os.path.join(os.path.dirname(__file__), "../../frontend/src/data/wz2025.json")

entries = []
with open(csv_path, encoding="utf-8-sig") as f:
    reader = csv.reader(f, delimiter=";")
    for i, row in enumerate(reader):
        if i < 9: continue
        if len(row) < 3: continue
        code  = row[0].strip().strip('"')
        level = row[1].strip().strip('"')
        title = row[2].strip().strip('"')
        if not code or not title or not level: continue
        try:
            entries.append({"code": code, "level": int(level), "title": title})
        except ValueError:
            continue

os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(entries, f, ensure_ascii=False, indent=2)

print(f"{len(entries)} Einträge exportiert nach {out_path}")
