---
name: Lizenz-Entscheidung Relume aussetzen 2026-05-06
description: Entscheidung Relume nicht weiter zu nutzen, basierend auf Lizenz-Pruefung; Migration auf MIT-Quellen
type: project
originSessionId: 359a3eba-9502-445f-ac0d-5f56a98ca841
---
**Why:** Relume's [Licensing Agreement](https://www.relume.io/legal/licensing-agreement) verbietet:
1. *"Under no circumstances should the Item be re-distributed, regardless of any modifications"* — Token-Mapping/Re-Brand zaehlt nicht als ausreichende Modifikation
2. *"You may NOT distribute any components to others or create a similar / competing product"* — KAS als Site-Generator mit Component-Library faellt darunter
3. *"Each component has a unique encoded signature"* — aktive Fingerprint-Detection, Verschleierung wuerde im Streitfall als Vorsatz gewertet

User hat die Lizenz nach Hinweis selbst gepruef und Cleanup beauftragt.

**How to apply:** Bei zukuenftigen Library-Erweiterungen NICHT mehr auf Relume zurueckgreifen, auch nicht "nur ein paar Snippets". Dem User KEINE Plan-A-Variante mehr anbieten ("verschleieren reicht doch") — die Frage ist final beantwortet. Wenn der User selber wieder anfaengt, freundlich auf diese Notiz verweisen.

---

## Cleanup durchgefuehrt am 2026-05-06

- HTML-Files entfernt: `relume-navbar-1/-2/-3.html` aus `kompagnon/frontend/src/components/library/external/relume/`
- `index.json` in dem Folder auf `components: []` gesetzt → triggert Auto-Cleanup-Pipeline beim Backend-Start, die 3 DB-Eintraege werden geloescht
- Folder + neuer README.md bleibt als Marker (zeigt warum nichts mehr da ist)
- Tools komplett entfernt: `tools/bulk-html-walker.user.js` (vorher `relume-bulk-downloader.user.js`), `tools/import-html-bulk.mjs`, `tools/README.md`
- `LIBRARY_VERSION_LOG` in `seed_component_library.py` um Removal-Eintrag erweitert
- Memory `relume_token_mapping.md` bleibt (technische Doku, kann fuer eigenes Referenz-Wissen relevant bleiben — nicht fuer Re-Import)

---

## Plan B — Migration auf MIT-Quellen

| Quelle | Lizenz | Anzahl Sections | URL |
|---|---|---|---|
| HyperUI | MIT | ~50 | bereits integriert |
| Flowbite Blocks | MIT | ~400 | https://flowbite.com/blocks/ |
| Preline UI | MIT | ~300 | https://preline.co/ |
| DaisyUI | MIT | (Components) | https://daisyui.com/ |
| Tailblocks | MIT | ~50 | https://tailblocks.cc/ |

Ziel: ~750-1000 white-label-faehige Sections plus eigene SHK-Templates.

---

## Was der User PERSOENLICH weiterhin darf

Relume-Lizenz erlaubt: *"Create End Products for clients or personal projects"*. Das heisst:
- David darf seine Subscription nutzen, um Sections in EINZELNE Kundenprojekte einzubauen (manuell, ein-zu-eins)
- Nicht erlaubt: in die KAS-SaaS-Library aufnehmen oder als "KAS-Template" wieder ausspielen

Das ist eine wichtige Nuance — Relume bleibt fuer Davids individuelle Nutzung legal, nur die SaaS-Integration ist verboten.
