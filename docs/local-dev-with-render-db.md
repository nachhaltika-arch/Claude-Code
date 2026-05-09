# Local Development mit Render-Postgres

Ziel: Lokal im Browser arbeiten, dabei echte Daten aus der Render-Postgres anzeigen.

⚠️ **Wichtig vorab:** Render hat zwei DBs:
- **Produktiv-DB** — versorgt `kompagnon-frontend.onrender.com` (Live-Customer-Daten)
- **Staging-DB** (`kompagnon-staging-db`, Postgres 18, Frankfurt) — Demo-Daten, keine Live-Customer

**Die Staging-DB ist 99% der Zeit das richtige Werkzeug.** Local Dev gegen Produktiv-DB nur wenn du genau weißt was du tust und das Risiko verstehst.

---

## Welches Szenario brauchst du?

| Szenario | Anwendungsfall | Risiko | Empfehlung |
|----------|----------------|--------|------------|
| **A) Frontend-only** | UI-Änderungen testen mit echten Daten | gering (read-only Frontend, Mutations gehen ans Live-Backend) | Standard für Frontend-Arbeit |
| **B) Full-Stack lokal** | Backend-Änderungen testen | hoch wenn Prod, mittel wenn Staging | Nur mit Staging-DB |
| **C) DB-GUI direkt** | SQL-Queries, Datenanalyse | nur Read-Risiko wenn Read-Only-User | DBeaver/TablePlus + Read-Only-Role |
| **D) DB-Dump lokal** | Offline-Arbeit, Migration testen | null (lokale Kopie) | für invasive Tests |

---

## A) Frontend lokal ↔ Render-Backend (Standard)

Schnell, sicher für UI-Arbeit. Frontend läuft lokal, hits prod oder staging Backend.

```bash
cd kompagnon/frontend

# .env.local erstellen (NICHT committed, .gitignore)
cat > .env.local <<EOF
# Wahl: produktiv ODER staging Backend
REACT_APP_API_URL=https://claude-code-znq2.onrender.com    # PRODUKTIV
# REACT_APP_API_URL=https://kompagnon-backend-staging.onrender.com  # STAGING
EOF

npm install
npm start
# → http://localhost:3000 mit Daten vom gewählten Backend
```

**Was passiert:** Browser hält localhost:3000, alle API-Calls gehen an Render-Backend. Daten werden gelesen und angezeigt.

⚠️ **Mutations gehen LIVE.** Wenn du auf der lokalen UI einen Lead löschst, einen Newsletter sendest, einen Kunden anlegst — das geht direkt in die produktive DB. Wer "nur gucken" will, sollte sich auf Read-Only-Aktionen beschränken.

---

## B) Full-Stack lokal ↔ Render-Postgres direkt

Lokales Backend connectet zu Render-DB. Frontend dev-server hits lokales Backend.

**Setup:**

```bash
# 1. DB-Connection-String aus Render holen
#    Dashboard → kompagnon-staging-db → Connect → External Database URL
#    Format: postgresql://user:pass@host.frankfurt-postgres.render.com/dbname

# 2. Backend lokal starten
cd kompagnon/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cat > .env <<EOF
DATABASE_URL=postgresql://user:pass@host.frankfurt-postgres.render.com/dbname
ANTHROPIC_API_KEY=sk-ant-...
ENVIRONMENT=local-dev
ADMIN_EMAIL=nachhaltika@gmail.com
ADMIN_PASSWORD=...
SECRET_KEY=$(openssl rand -hex 32)
FRONTEND_URL=http://localhost:3000
CORS_ALLOWED_ORIGINS=http://localhost:3000
EOF

uvicorn main:app --reload --port 8000

# 3. Frontend auf lokales Backend zeigen lassen
cd ../frontend
echo "REACT_APP_API_URL=http://localhost:8000" > .env.local
npm start
```

⚠️ **Wichtig bei Render Basic-Tier-DB:** External Connections werden in **Frankfurt-Postgres** ohne IP-Allowlisting erlaubt — aber Latency ist hoch (~50-100ms pro Query). Lokales Backend wirkt langsam.

⚠️ **Wenn du gegen die Produktiv-DB connectest:** Migrations beim Backend-Boot würden Live-Schema modifizieren. Sehr riskant. Nur Staging-DB nutzen.

---

## C) DB-GUI direkt (DBeaver auf Mac)

Für SQL-Queries, Daten-Inspektion, ad-hoc Reports — kein Code nötig.

**DBeaver Mac-Install:**

```bash
brew install --cask dbeaver-community
```

**Connection einrichten:**

1. Open DBeaver → New Database Connection → PostgreSQL
2. Felder aus Render-Connection-String füllen:
   - Host: `host.frankfurt-postgres.render.com`
   - Port: `5432`
   - Database: aus Connection-String
   - Username: aus Connection-String
   - Password: aus Connection-String
3. SSL: required (Render erzwingt SSL)
4. Test Connection → Save

**Read-Only-User für sicheres Browsen:**

```sql
-- Auf Render-DB als admin ausführen (einmalig)
CREATE USER david_readonly WITH PASSWORD 'erzeuge_sicheres_pw';
GRANT CONNECT ON DATABASE kompagnon_staging TO david_readonly;
GRANT USAGE ON SCHEMA public TO david_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO david_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT ON TABLES TO david_readonly;
```

Dann in DBeaver mit `david_readonly` connecten — kein Risiko von Mutations.

**Alternative GUIs:** TablePlus (Mac-popular), Postico (Mac-only), pgAdmin 4 (Cross-Platform), Beekeeper Studio.

---

## D) DB-Dump lokal — vollständig offline

Für invasive Tests (Migrations testen, Backups verifizieren).

```bash
# 1. Lokales Postgres installieren
brew install postgresql@18
brew services start postgresql@18
createdb kompagnon_local

# 2. Dump von Render holen
pg_dump "postgresql://user:pass@host.frankfurt-postgres.render.com/kompagnon_staging" \
  > /tmp/kompagnon_dump.sql

# 3. In lokales Postgres importieren
psql kompagnon_local < /tmp/kompagnon_dump.sql

# 4. Backend mit lokaler DB starten
cd kompagnon/backend
echo "DATABASE_URL=postgresql://localhost/kompagnon_local" >> .env
uvicorn main:app --reload --port 8000
```

Vorteil: alles lokal, keine Latency, keine Mutationsgefahr. Nachteil: Daten sind Snapshot, nicht live.

---

## Render-MCP für DB-Queries (in Claude)

Wenn Claude Code ad-hoc SQL ausführen soll (z.B. Datenanalyse-Sessions), nutze den Render-MCP:

```
mcp__render__query_render_postgres
  postgresId: "<dpg-...>" (aus list_postgres_instances holen)
  sql: "SELECT COUNT(*) FROM leads WHERE created_at > NOW() - INTERVAL '7 days'"
```

→ Read-only, sicher, keine extra Tools auf dem Rechner nötig.

---

## Empfehlung für KOMPAGNON

**Für 95% deiner lokalen Arbeit:**

1. **Frontend-Änderungen testen:** Szenario A mit Staging-Backend
2. **Daten anschauen:** Szenario C mit DBeaver + Read-Only-User auf Staging-DB
3. **SQL-Queries ad-hoc:** Render-MCP via Claude

**Nur in Sonderfällen:**

- Backend-Schema-Änderungen → Szenario D (Dump lokal)
- Live-Bug nachstellen → Szenario A mit Produktiv-Backend, Read-Only-Aktionen

**Niemals:** Produktiv-DB direkt mit Schreibrechten lokal verbinden.
