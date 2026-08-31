import { useState, useEffect, useCallback } from 'react';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';
import { saveJson } from '../utils/apiRequest';
import { aufTaste } from '../utils/tastaturBedienung';

const KATEGORIEN = [
  {
    id:    'rechtliches',
    label: 'Rechtliches',
    icon:  '⚖️',
    items: [
      {
        id:    'impressum',
        label: 'Impressum vorhanden und korrekt (Name, Adresse, USt-ID)',
        info:  null,
      },
      {
        id:    'datenschutz',
        label: 'Datenschutzerklärung DSGVO-konform',
        info:  { text: 'Generator', url: 'https://www.datenschutz-generator.de' },
      },
      {
        id:    'cookie_banner',
        label: 'Cookie-Banner aktiv (Borlabs / Usercentrics / CookieYes)',
        info:  null,
      },
    ],
  },
  {
    id:    'browser',
    label: 'Browser-Tests',
    icon:  '🌐',
    items: [
      { id: 'chrome_desktop',  label: 'Chrome Desktop',          info: null },
      { id: 'firefox_desktop', label: 'Firefox Desktop',         info: null },
      { id: 'safari_desktop',  label: 'Safari Desktop',          info: null },
      { id: 'chrome_mobile',   label: 'Chrome Mobile (Android)', info: null },
      { id: 'safari_mobile',   label: 'Safari Mobile (iPhone)',  info: null },
    ],
  },
  {
    id:    'performance',
    label: 'Performance & Bilder',
    icon:  '⚡',
    items: [
      { id: 'bilder_200kb',      label: 'Alle Bilder unter 200 KB (WebP-Format)', info: null },
      { id: 'pagespeed_mobile',  label: 'PageSpeed Mobile > 70',                  info: null },
      { id: 'pagespeed_desktop', label: 'PageSpeed Desktop > 85',                 info: null },
    ],
  },
  {
    id:    'analytics',
    label: 'Analytics & SEO',
    icon:  '📈',
    items: [
      { id: 'ga_eingerichtet',     label: 'Google Analytics eingerichtet',               info: null },
      { id: 'search_console',      label: 'Google Search Console verifiziert',           info: null },
      { id: 'sitemap_eingereicht', label: 'Sitemap.xml über Search Console eingereicht', info: null },
    ],
  },
  // ── Übernommen aus der kurzen Checkliste (L-95, 24.08.2026) ─────────
  //
  // Diese Liste tritt an die Stelle von `QmChecklisteEmbed` (53 Zeilen).
  // Die reichere Fassung deckte aber **sieben** ihrer zehn Punkte nicht ab —
  // SSL, Links, Formular, Favicon, Maps, Social und die Mobilprüfung. Ein
  // glatter Tausch hätte sie stillschweigend fallen lassen, und niemand hätte
  // gemerkt, dass seit dem Tausch niemand mehr prüft, ob das Kontaktformular
  // sendet.
  //
  // **Die Kennungen sind bewusst die alten** (`ssl`, `links`, `forms`, …).
  // Beide Listen speichern ein Verzeichnis aus Kennung → Haken; damit werden
  // bereits gesetzte Haken beim Umstieg übernommen, statt zurückgesetzt.
  {
    id:    'technik',
    label: 'Technik & Auffindbarkeit',
    icon:  '🔧',
    items: [
      { id: 'ssl',     label: 'SSL-Zertifikat aktiv (https://)',            info: null },
      { id: 'links',   label: 'Alle Links funktionieren (kein 404)',        info: null },
      { id: 'forms',   label: 'Kontaktformular sendet korrekt',             info: null },
      { id: 'mobile',  label: 'Mobile Ansicht korrekt auf iOS & Android',   info: null },
      { id: 'favicon', label: 'Favicon + Meta-Titel korrekt',              info: null },
      { id: 'maps',    label: 'Google Maps / Adresse stimmt',              info: null },
      { id: 'social',  label: 'Social-Media-Links korrekt',                info: null },
    ],
  },
];

const TOTAL = KATEGORIEN.reduce((acc, k) => acc + k.items.length, 0);

// Kennungen, die in der kurzen Checkliste anders hiessen (L-95, 24.08.2026).
//
// **`impressum` wird bewusst NICHT auf `datenschutz` uebertragen.** Die alte
// Zeile lautete „Impressum + Datenschutz vorhanden", die neue verlangt
// „Datenschutzerklaerung DSGVO-konform" — das ist mehr als Vorhandensein. Ein
// uebernommener Haken waere dort eine Behauptung, die niemand geprueft hat.
//
// Die PageSpeed-Punkte werden ebenfalls nicht uebernommen: Sie setzt die
// Komponente unten aus den tatsaechlichen Messwerten.
const ALTE_KENNUNGEN = {
  analytics: 'ga_eingerichtet',
};

/**
 * Haken aus der kurzen Checkliste in die Kennungen dieser Liste bringen.
 *
 * @param {string|null|undefined} altesJson Inhalt von `gbp_checklist_json`.
 * @returns {Record<string, boolean>} Nur gesetzte Haken, mit den Kennungen
 *   dieser Liste. Beschaedigtes JSON ergibt ein leeres Verzeichnis.
 */
export function altenStandUebernehmen(altesJson) {
  if (!altesJson) return {};
  let alt;
  try {
    alt = JSON.parse(altesJson);
  } catch {
    return {};
  }
  if (!alt || typeof alt !== 'object' || Array.isArray(alt)) return {};

  const uebernommen = {};
  for (const [kennung, gesetzt] of Object.entries(alt)) {
    if (!gesetzt) continue;
    if (kennung === 'speed' || kennung === 'impressum') {
      if (kennung === 'impressum') uebernommen.impressum = true;
      continue;
    }
    uebernommen[ALTE_KENNUNGEN[kennung] || kennung] = true;
  }
  return uebernommen;
}


export default function QAChecklist({ projectId, token, qaChecklistJson, gbpChecklistJson, pagespeedMobile, pagespeedDesktop }) {
  const h = {
    'Content-Type': 'application/json',
    Authorization:  `Bearer ${token}`,
  };

  const [checked, setChecked] = useState({});
  const [saving, setSaving]   = useState(false);

  // Vorhandene Daten aus Prop laden.
  //
  // **Der Stand der kurzen Checkliste zaehlt mit (L-95).** Diese Liste tritt
  // an ihre Stelle; wer dort schon Haken gesetzt hatte, soll sie hier
  // wiederfinden und nicht von vorn anfangen. Der eigene Stand hat Vorrang —
  // wurde hier bereits gespeichert, ist der alte ueberholt.
  useEffect(() => {
    const alt = altenStandUebernehmen(gbpChecklistJson);
    if (!qaChecklistJson) {
      setChecked(alt);
      return;
    }
    try {
      const parsed = JSON.parse(qaChecklistJson);
      setChecked({ ...alt, ...(parsed || {}) });
    } catch {
      toast.error('Die gespeicherte QA-Checkliste ist beschädigt und wurde zurückgesetzt.', {
        id: 'qa-checkliste-beschaedigt',
      });
      setChecked(alt);
    }
  }, [qaChecklistJson, gbpChecklistJson]);

  // PageSpeed-Punkte automatisch setzen
  useEffect(() => {
    setChecked(prev => {
      const next = { ...prev };
      if (pagespeedMobile !== undefined && pagespeedMobile !== null) {
        next['pagespeed_mobile'] = Number(pagespeedMobile) >= 70;
      }
      if (pagespeedDesktop !== undefined && pagespeedDesktop !== null) {
        next['pagespeed_desktop'] = Number(pagespeedDesktop) >= 85;
      }
      return next;
    });
  }, [pagespeedMobile, pagespeedDesktop]); // eslint-disable-line

  // Auto-Save nach 800ms Debounce
  const save = useCallback(async (newChecked) => {
    if (!projectId) return;
    setSaving(true);
    // Ein fehlgeschlagenes Speichern liess die Haken stehen — beim naechsten
    // Oeffnen waren sie weg, ohne dass je etwas gemeldet wurde.
    await saveJson(
      `${API_BASE_URL}/api/projects/${projectId}/qa-checklist`,
      { method: 'PATCH', headers: h, body: JSON.stringify({ checked: newChecked }) },
      { context: 'QA-Checkliste speichern' }
    );
    setSaving(false);
  }, [projectId]); // eslint-disable-line

  useEffect(() => {
    if (Object.keys(checked).length === 0) return;
    const t = setTimeout(() => save(checked), 800);
    return () => clearTimeout(t);
  }, [checked]); // eslint-disable-line

  const toggle = (itemId) => {
    setChecked(prev => ({ ...prev, [itemId]: !prev[itemId] }));
  };

  const checkedCount = Object.values(checked).filter(Boolean).length;
  const pct          = Math.round(checkedCount / TOTAL * 100);
  const allDone      = checkedCount === TOTAL;
  const barColor     = allDone ? '#1D9E75' : pct >= 70 ? 'var(--kc-mid)' : pct >= 40 ? '#BA7517' : '#E24B4A';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

      {/* ── FORTSCHRITT ── */}
      <div style={{
        background: allDone ? '#EAF3DE' : 'var(--bg-surface)',
        border: `0.5px solid ${allDone ? '#97C459' : 'var(--border-light)'}`,
        borderRadius: 12, padding: '14px 18px',
      }}>
        <div style={{
          display: 'flex', alignItems: 'center',
          justifyContent: 'space-between', marginBottom: 8,
        }}>
          <div>
            <div style={{
              fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)',
              textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 2,
            }}>
              QA-Checkliste Technik-Phase
            </div>
            <div style={{ fontSize: 20, fontWeight: 500, color: 'var(--text-primary)' }}>
              {checkedCount} von {TOTAL} Punkte erledigt
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 26, fontWeight: 500, color: barColor }}>
              {pct}%
            </div>
            {saving && (
              <div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>
                Wird gespeichert…
              </div>
            )}
          </div>
        </div>

        <div style={{
          height: 6, background: 'var(--border-light)',
          borderRadius: 3, overflow: 'hidden',
        }}>
          <div style={{
            height: '100%', width: `${pct}%`,
            background: barColor, borderRadius: 3, transition: 'width .4s',
          }} />
        </div>

        {allDone && (
          <div style={{
            marginTop: 10, fontSize: 13, fontWeight: 600,
            color: '#1D9E75', display: 'flex', alignItems: 'center', gap: 6,
          }}>
            ✓ Alle Punkte erledigt — bereit für Go-Live!
          </div>
        )}
      </div>

      {/* ── KATEGORIEN ── */}
      {KATEGORIEN.map(kat => {
        const katCount = kat.items.filter(item => checked[item.id]).length;
        const katDone  = katCount === kat.items.length;

        return (
          <div key={kat.id} style={{
            background: 'var(--bg-surface)',
            border: `0.5px solid ${katDone ? '#97C459' : 'var(--border-light)'}`,
            borderRadius: 12, overflow: 'hidden',
          }}>
            {/* Kategorie-Header */}
            <div style={{
              display: 'flex', alignItems: 'center',
              justifyContent: 'space-between',
              padding: '11px 16px',
              background: katDone ? '#EAF3DE' : 'var(--bg-app)',
              borderBottom: '0.5px solid var(--border-light)',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 15 }}>{kat.icon}</span>
                <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                  {kat.label}
                </span>
              </div>
              <span style={{
                fontSize: 12, fontWeight: 600, padding: '2px 9px', borderRadius: 10,
                background: katDone ? '#97C459' : 'var(--border-light)',
                color:      katDone ? '#27500A' : 'var(--text-secondary)',
              }}>
                {katCount}/{kat.items.length}
              </span>
            </div>

            {/* Items */}
            {kat.items.map((item, idx) => {
              const isChecked = !!checked[item.id];
              const isAuto    = item.id === 'pagespeed_mobile' || item.id === 'pagespeed_desktop';

              return (
                <div role="button" tabIndex={0} onKeyDown={aufTaste(() => !isAuto && toggle(item.id))}
                  key={item.id}
                  onClick={() => !isAuto && toggle(item.id)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 12,
                    padding: '10px 16px',
                    borderBottom: idx < kat.items.length - 1
                      ? '0.5px solid var(--border-light)' : 'none',
                    cursor:     isAuto ? 'default' : 'pointer',
                    background: isChecked ? 'rgba(29,158,117,0.04)' : 'transparent',
                    transition: 'background .1s',
                  }}
                >
                  {/* Checkbox */}
                  <div style={{
                    width: 18, height: 18, borderRadius: 4, flexShrink: 0,
                    border:      isChecked ? 'none' : '1.5px solid var(--border-medium)',
                    background:  isChecked ? '#1D9E75' : 'transparent',
                    display:     'flex', alignItems: 'center', justifyContent: 'center',
                    transition:  'all .15s',
                    opacity:     isAuto ? 0.7 : 1,
                  }}>
                    {isChecked && (
                      <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
                        <path d="M1 4L3.5 6.5L9 1" stroke="white"
                              strokeWidth="1.8" strokeLinecap="round"
                              strokeLinejoin="round" />
                      </svg>
                    )}
                  </div>

                  {/* Label */}
                  <span style={{
                    flex: 1, fontSize: 13,
                    color:           isChecked ? 'var(--text-secondary)' : 'var(--text-primary)',
                    textDecoration:  isChecked ? 'line-through' : 'none',
                    transition:      'all .15s',
                  }}>
                    {item.label}
                    {isAuto && (
                      <span style={{ fontSize: 10, color: 'var(--text-tertiary)', marginLeft: 6 }}>
                        (automatisch)
                      </span>
                    )}
                  </span>

                  {/* Info-Link */}
                  {item.info && (
                    <a
                      href={item.info.url}
                      target="_blank"
                      rel="noreferrer"
                      onClick={e => e.stopPropagation()}
                      style={{
                        fontSize: 12, color: 'var(--kc-mid)',
                        textDecoration: 'none', flexShrink: 0,
                        padding: '2px 8px', borderRadius: 6,
                        border: '0.5px solid var(--kc-mid)',
                      }}
                    >
                      {item.info.text} ↗
                    </a>
                  )}
                </div>
              );
            })}
          </div>
        );
      })}

      <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
        Änderungen werden automatisch gespeichert.
        PageSpeed-Punkte werden automatisch gesetzt wenn Werte vorhanden.
      </div>
    </div>
  );
}
