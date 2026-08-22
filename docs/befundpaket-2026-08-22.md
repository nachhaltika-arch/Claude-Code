# Befundpaket 22.08.2026 — nachgemessen am Code

Grundlage: acht Prompt-Dokumente zur Repository-Analyse von `staging` @ `157549f`,
eingegangen am 22.08.2026. Dieses Dokument hält fest, **was davon am Code standhält**
und was beim Nachmessen anders aussah.

Der Unterschied ist die eigentliche Nachricht. Vier der Befunde stimmen Zeile für
Zeile. Vier stimmen in der Sache, aber nicht in der Begründung — und bei zweien
führt die falsche Begründung zu einer falschen Reparatur.

---

## 1. Bestätigt, Zeile für Zeile

| Befund | Belegstelle | Gemessen |
|---|---|---|
| **N-01** Doppelte Route | `routers/projects.py:1041` und `:3252` | beide Male `@router.post("/{project_id}/request-approval")`, beide Funktionen heißen `request_approval` |
| **N-02** `main.py` ist eine Funktion | `main.py:102–1329` | `_run_migrations()` = 1.228 der 2.201 Zeilen |
| **N-03** Freigabe-Schritt wird nie fertig | `ProzessFlow.jsx:307` | `.some(v => v === true)` gegen ein Backend, das `{status, freigegeben_am}` schreibt |
| **SEC-02** Schlüssel im Quelltext | `utils/studioEditorConfig.js:22–24` | Rückfall auf `'251e7a07…'`, wenn die Variable fehlt |
| **N-01/Fehler 3** Statusbegriffe | `customer/Freigaben.jsx:85–86` | Filter auf `'ausstehend'`, Backend schreibt `'angefragt'` |
| **B-02/03/04** Wurzelverzeichnis | `ls -1 \| wc -l` | 53 Einträge, 12,5 MB — kein Programmcode darunter |

`projects.py` hat 4.847 Zeilen. Auch das stimmt.

---

## 2. Was beim Nachmessen anders aussah

### 2.1 Die Route trägt schon eine Sperre — der Auditor ist der Einzige, den es trifft

Das Dokument schreibt: *„Ein Mitarbeiter ohne Adminrechte bekommt dort heute eine
Abweisung."* Das ist zu weit gefasst. `projects.py:121–122`:

```python
router = APIRouter(prefix="/api/projects", tags=["projects"],
                   dependencies=[Depends(require_innendienst)])
```

Jede Route an diesem Router läuft bereits durch `require_innendienst`.
`require_admin` auf `request_approval` ist eine **zweite** Sperre obendrauf.
Wen die beiden zusammen ausschließen, ist gemessen und nicht geschätzt:

| Rolle | `view_leads` | Router | `require_admin` | Ergebnis |
|---|---|---|---|---|
| superadmin, admin | ✓ | durch | durch | kommt an |
| **auditor** | ✓ | durch | **403** | **einzige betroffene Rolle** |
| nutzer | ✗ | **403** | — | scheitert schon am Router |
| kunde | ✗ | **403** | — | scheitert schon am Router |

**Folge für die Reparatur:** Die erste Fassung von Prompt 02 wollte `require_admin`
durch `get_current_user` ersetzen. Das hätte den Auditor freigeschaltet und für
`nutzer` nichts geändert — aber im Quelltext „jeder Angemeldete" behauptet, während
der Router weiterhin nur den Innendienst durchlässt. Die zweite Fassung lässt die
Sperre stehen, mit der richtigen Begründung: Die Antwort enthält den Freigabe-Token,
und der gilt über `POST /approve-content/{token}` **ohne Anmeldung**. Wer die Anfrage
stellen darf, kann sich die Freigabe selbst erteilen.

Festgehalten als Kommentar in `tests/test_freigabe_durch_kunden.py`, damit die
Abwägung nicht beim nächsten Aufräumen als Nachlässigkeit gelesen wird.

### 2.2 `ProzessFlowV3.jsx` existiert nicht mehr — der Kommentar sagt das Gegenteil

Prompt 06 baut darauf auf, dass `ProzessFlow.jsx` und `ProzessFlowV3.jsx`
nebeneinander liegen und ein Umbau unfertig steckengeblieben sei. Gemessen:

```
kompagnon/frontend/src/components/ProzessFlow.jsx     129.686 Bytes
kompagnon/frontend/src/components/ProzessFlowV3.jsx   existiert nicht
```

V3 wurde in `c333576` entfernt — dem drittletzten Commit auf `staging`. Der zitierte
Kommentar in `OnlineFertigEditor.jsx:5` lautet vollständig:

> Seit dem 21.08.2026 der einzige Projekt-Editor: `ProzessFlowV3` und der Bildschirm,
> der ihn hielt (`pages/ProjectDetail.jsx`, …), **sind entfernt**.

Subjekt des Satzes ist `OnlineFertigEditor` — *er* ist der einzige Editor, **weil** V3
entfernt wurde. Der Bericht las V3 als Subjekt und schloss daraus auf eine Baustelle.

Und `ProzessFlow.jsx` ist kein Rest, sondern trägt aktiv den Schritt-Renderer.
`OnlineFertigEditor.jsx:31–34` sagt es ausdrücklich:

> `SchrittInhalt` … ist der gemeinsame Renderer beider Editor-Generationen gewesen
> und jetzt der einzige.

**Folge:** Prompt 06 in der vorliegenden Form geht ins Leere — es gibt keine zwei
Dateien mehr zu entflechten. Die verbleibende Frage ist eine andere und kleinere:
Wie viel der 129 KB hält noch etwas, das gebraucht wird, außer `SchrittInhalt`?

### 2.3 Ruff hat den Doppelbefund die ganze Zeit gemeldet — die CI filtert ihn weg

`ruff check routers/projects.py` meldete:

```
F811 Redefinition of unused `request_approval` from line 1042
```

Die CI führt aber `.github/workflows/ci.yml:32` aus:

```
ruff check --select E9,F63,F7,F82 --output-format=github .
```

`F811` ist in dieser Auswahl nicht enthalten. Das Werkzeug sah den Fehler, das Tor
ließ ihn durch. Gemessen: Nach Behebung ist `F811` im gesamten Backend sauber —
die Regel lässt sich also aufnehmen, ohne dass etwas anderes rot wird.

### 2.4 Der vorhandene Kollisionstest kann diese Bauart nicht finden

`tests/test_router_kollisionen.py` prüft seit dem 21.08.2026 auf Adresskollisionen und
hat damals 19 gefunden. Diese hier nicht — aus einem strukturellen Grund: Er zählt,
**wie viele Router** eine Adresse beanspruchen.

```python
belegt[(methode, adresse)].add(herkunft)   # ein Set von Router-Namen
... if len(wer) > 1
```

Beide `request-approval` sitzen an *demselben* Router. Die Menge der Herkünfte bleibt
einelementig, der Test bleibt grün.

Ergänzt um `test_kein_router_belegt_dieselbe_adresse_zweimal`, das Registrierungen
zählt statt Router. Statisch über alle Router-Dateien gemessen: **genau ein**
Duplikat dieser Art in der gesamten Codebase — das hier. Der Test wird nach der
Reparatur grün und bleibt es.

---

## 3. Wo die Kette wirklich reißt

Die vier Fehler von N-01 greifen ineinander, und der Bericht der zweiten Fassung hat
das richtig zusammengesetzt. Ergänzend gemessen, wer `content_freigaben` überhaupt
beschreibt:

| Stelle | schreibt | erreichbar |
|---|---|---|
| `projects.py:3291` (Variante B) | `status: "angefragt"` | **nein** — von Variante A überdeckt |
| `projects.py:3395` (`confirm_approval`) | `"freigegeben"` / `"abgelehnt"` | ja |

Der Zustand „angefragt" entsteht also **nie**. Die Freigabeliste im Kundenportal kann
nur Einträge zeigen, die `confirm_approval` selbst angelegt hat — also solche, die
bereits entschieden sind. Selbst nach Behebung der Kollision bliebe sie unbrauchbar,
solange `Freigaben.jsx:85` auf `'ausstehend'` filtert.

Deshalb ist die zweite Fassung von Prompt 02 die richtige: **B umbenennen statt
löschen.** Löschen würde die Schreib-Hälfte eines Verfahrens entfernen, dessen
Lese-Hälfte erreichbar ist und dessen Oberfläche existiert.

---

## 4. Reihenfolge — mit Anmerkungen

| Nr. | Stand | Anmerkung |
|---|---|---|
| 01 Projektanweisungen | nichts zu tun | bestätigt: `claude/kompagnon-automation-system-FapM9` gibt es remote nicht mehr; vorhanden sind `main`, `staging`, `claude/setup-mac-staging-local-N2oaA` |
| 08 Freigabe-Schritt | ausführbar | Schritt 1c entfällt — `ProzessFlowV3.jsx` gibt es nicht |
| 02 Freigabe-Verfahren | ausführbar | zweite Fassung; Regressionstest liegt bereits vor |
| 03 GrapesJS | **blockiert** | erst nach Widerruf beim Anbieter und Render-Rebuild — sonst stehen die Editoren |
| 04 `main.py` | ausführbar | Grenzen bestätigt: `102–1329` |
| 05 `projects.py` | vorbereitet | Etappe 0 zuerst; Prompt 02 muss vorher durch sein |
| 06 `ProzessFlow` | **überholt** | siehe 2.2 — die Grundannahme trägt nicht mehr |
| 07 Wurzelverzeichnis | ausführbar | 53 statt 51 Einträge, sonst wie beschrieben |

---

## 5. Was dieses Paket über die Fehlerklasse sagt

Drei der vier echten Fehler sind derselbe Vorgang: **Eine Seite ändert ein Format oder
eine Adresse, die andere bleibt stehen.**

* Backend schreibt `{status: …}`, `ProzessFlow.jsx` liest `=== true`
* Backend schreibt `"angefragt"`, `Freigaben.jsx` filtert `"ausstehend"`
* Zwei Verfahren wachsen auf eine Adresse, weil in 4.847 Zeilen niemand sieht, dass
  die Adresse schon vergeben ist

Der dritte Punkt erklärt die ersten beiden mit: In einer Datei dieser Größe wird
abschnittsweise gelesen und abschnittsweise geändert. Das ist der Grund, warum
Prompt 05 (Zerlegen) unter den Aufräumarbeiten steht und nicht unter Kosmetik.

Was dagegen hilft, ist nicht Sorgfalt, sondern ein Tor, das die Frage stellt, wenn
niemand daran denkt — wie `test_router_kollisionen.py` es seit dem 21.08. für
Adressen tut. Deshalb sind die Ergänzungen aus 2.3 und 2.4 kein Beiwerk: Sie sind
der Teil dieser Sitzung, der beim nächsten Mal noch wirkt.
