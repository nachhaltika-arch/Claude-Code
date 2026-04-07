import csv, json, sys

entries = []
with open("WZ_2025-DE-2026-03-30-Gliederung__1_.csv", encoding="utf-8-sig") as f:
    reader = csv.reader(f, delimiter=";")
    for i, row in enumerate(reader):
        if i < 9: continue  # Kopfzeilen überspringen
        if len(row) < 3: continue
        code  = row[0].strip().strip('"')
        level = row[1].strip().strip('"')
        title = row[2].strip().strip('"')
        if not code or not title: continue
        entries.append({"code": code, "level": int(level), "title": title})

with open("wz2025.json", "w", encoding="utf-8") as f:
    json.dump(entries, f, ensure_ascii=False, indent=2)

print(f"{len(entries)} Einträge exportiert.")
