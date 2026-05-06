# Relume — REMOVED (Lizenz-Compliance)

Dieses Verzeichnis wurde am **2026-05-06** geleert.

## Begruendung

Relume's [Licensing Agreement](https://www.relume.io/legal/licensing-agreement)
verbietet folgende Nutzung, die mit dem KAS-Use-Case kollidiert:

> "Under no circumstances should the Item be re-distributed,
> regardless of any modifications"

> "You may NOT distribute any components to others or create a
> similar / competing product"

> "Each component has a unique encoded signature, which we use to
> pragmatically discover if this has been violated"

KAS ist als Site-Generator mit integrierter Komponenten-Bibliothek per
Definition ein "similar product" — die Sections werden nicht in **einem**
Kundenprojekt einmalig genutzt (was die Lizenz erlaubt), sondern in einer
geteilten SaaS-Library wiederverwendet.

Das Token-Mapping (`border-border-primary` → `border-gray-200`) zaehlt
laut Klausel 1 explizit nicht als ausreichende Modifikation.

## Was passiert ist

- `relume-navbar-1.html`, `relume-navbar-2.html`, `relume-navbar-3.html` aus dem Repo entfernt
- `index.json` auf `components: []` gesetzt → die `seed_component_library.py`
  Auto-Cleanup-Pipeline loescht beim naechsten Backend-Start die zugehoerigen
  DB-Eintraege (Tag `relume` ohne Manifest-Match)
- Tools `relume-bulk-downloader.user.js` + `import-relume-bulk.mjs`
  generisch umbenannt (`bulk-html-walker.user.js`, `import-html-bulk.mjs`),
  funktionieren weiterhin, aber neutral fuer beliebige HTML-Quellen

## Ersatz-Strategie

Migration auf rechtlich saubere Quellen — alle MIT-lizenziert oder
kommerziell mit White-Label-Recht:

| Quelle | Lizenz | Anzahl Sections | Status |
|---|---|---|---|
| HyperUI | MIT | ~50 | bereits integriert |
| Flowbite Blocks | MIT | ~400 | naechster Schritt |
| Preline UI | MIT | ~300 | folgt |
| DaisyUI | MIT | (Components) | folgt |
| Tailblocks | MIT | ~50 | folgt |
| KAS-eigene SHK-Templates | proprietaer | wachsend | parallel kuratiert |

Damit kommt KAS auf ~750-1000 white-label-faehige Sections plus eigene
SHK-spezifische Differentiator-Templates.

## Folder behalten?

Folder bleibt als Marker — falls jemand spaeter nach `external/relume`
greift, sieht er sofort warum nichts mehr da ist und welche
Lizenz-Erwaegungen das Verzeichnis ausgeschlossen haben.
