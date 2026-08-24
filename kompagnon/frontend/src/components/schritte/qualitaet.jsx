/**
 * Qualitaets-Schritte: QA, Abnahme, Checkliste, Vergleich.
 *
 * **Warum eigene Datei (L-25, 22.08.2026).** `ProzessFlow.jsx` hatte 2.307
 * Zeilen. 493 davon waren tot — `PHASEN`, `ALLE_SCHRITTE` und die
 * Standardkomponente, die niemand importierte. Der Rest bestand aus einem
 * Verteiler (`SchrittInhalt`) und siebzehn Einbettungen, die je einen
 * Schritt des Online-Editors anzeigen.
 *
 * Geschnitten ist nach **Thema**, nicht nach Groesse: Die Einbettungen
 * teilen untereinander nichts ausser den Bibliotheks-Importen — nachgemessen
 * vor dem Schnitt. `SchrittInhalt` bleibt in `ProzessFlow.jsx` und holt sie
 * von hier.
 */
import API_BASE_URL from '../../config';
import { loadJson, saveJson } from '../../utils/apiRequest';
import { useEffect, useState } from 'react';


export function QAEmbed({ project, headers, qaResult: initialResult }) {
  const [result, setResult]   = useState(initialResult || null);
  const [running, setRunning] = useState(false);
  const [error, setError]     = useState('');
  // Die KI-Beurteilung des QA-Ergebnisses (L-105). Der Agent war gebaut und
  // hatte keinen Zugang — `POST /api/agents/{id}/qa` rief im ganzen Frontend
  // niemand auf. Seine Eingabe liegt genau hier: die Pruefergebnisse, die der
  // Scan darueber erzeugt hat.
  const [urteil, setUrteil]       = useState(null);
  const [urteilLaeuft, setLaeuft] = useState(false);
  const [urteilFehler, setFehler] = useState('');

  const CHECKS = [
    { key:'ssl', label:'SSL / HTTPS aktiv' },
    { key:'impressum', label:'Impressum vorhanden' },
    { key:'datenschutz', label:'Datenschutz vorhanden' },
    { key:'kontakt', label:'Kontakt-Formular / Telefon' },
    { key:'mobile', label:'Mobile-Ansicht korrekt' },
    { key:'links', label:'Keine defekten Links' },
    { key:'pagespeed', label:'PageSpeed > 70' },
  ];

  const run = async () => {
    setRunning(true); setError('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/projects/${project.id}/qa/run`, { method:'POST', headers });
      const d = await res.json();
      if (!res.ok) throw new Error(d.detail || 'Fehler');
      setResult(d);
    } catch (e) { setError(e.message); }
    finally { setRunning(false); }
  };

  const beurteilen = async () => {
    setLaeuft(true); setFehler(''); setUrteil(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/agents/${project.id}/qa`, {
        method: 'POST', headers,
        body: JSON.stringify({
          checklist_data: Object.fromEntries(CHECKS.map(c => [c.key, c.label])),
          test_results: result || {},
        }),
      });
      const d = await res.json();
      if (!res.ok) throw new Error(d.detail || 'Fehler');
      setUrteil(d.result || d);
    } catch (e) { setFehler(e.message); }
    finally { setLaeuft(false); }
  };

  return (
    <div style={{ padding:'20px 24px', display:'flex', flexDirection:'column', gap:16 }}>
      <button onClick={run} disabled={running}
        style={{ alignSelf:'flex-start', padding:'10px 22px', borderRadius:8, border:'none', background: running ? 'var(--border-medium)' : 'var(--brand-primary)', color:'#fff', fontSize:13, fontWeight:700, cursor: running ? 'not-allowed' : 'pointer', fontFamily:'var(--font-sans)', display:'flex', alignItems:'center', gap:8 }}>
        {running ? (<><span style={{ width:14, height:14, border:'2px solid rgba(255,255,255,.3)', borderTopColor:'#fff', borderRadius:'50%', animation:'spin .8s linear infinite', display:'inline-block' }} />QA-Scan laeuft...</>) : result ? 'Erneut scannen' : 'QA-Check starten'}
      </button>
      {error && <div style={{ fontSize:12, color:'var(--status-danger-text)', background:'var(--status-danger-bg)', padding:'8px 12px', borderRadius:6 }}>{error}</div>}
      {result ? (
        <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
          {CHECKS.map(c => {
            const passed = result[c.key] === true || result[c.key] === 'ok';
            const warn = result[c.key] === 'warn';
            return (
              <div key={c.key} style={{ display:'flex', alignItems:'center', gap:12, padding:'10px 14px', background:'var(--bg-surface)', border:'1px solid var(--border-light)', borderRadius:8 }}>
                <span style={{ fontSize:16, flexShrink:0 }}>{passed ? '\u2705' : warn ? '\u26A0\uFE0F' : '\u274C'}</span>
                <span style={{ fontSize:13, color:'var(--text-primary)', flex:1 }}>{c.label}</span>
                {result[c.key + '_detail'] && <span style={{ fontSize:11, color:'var(--text-tertiary)' }}>{result[c.key + '_detail']}</span>}
              </div>
            );
          })}
          {result.ai_summary && (
            <div style={{ marginTop:8, padding:'12px 14px', background:'var(--bg-app)', borderRadius:8, borderLeft:'3px solid var(--brand-primary)', fontSize:12, color:'var(--text-secondary)', lineHeight:1.7 }}>
              {result.ai_summary}
            </div>
          )}

          <div style={{ marginTop:12, paddingTop:16, borderTop:'1px solid var(--border-light)' }}>
            <button onClick={beurteilen} disabled={urteilLaeuft}
              style={{ padding:'8px 18px', borderRadius:8, border:'1px solid var(--border-medium)', background:'var(--bg-surface)', color:'var(--text-primary)', fontSize:12, fontWeight:600, cursor: urteilLaeuft ? 'wait' : 'pointer', fontFamily:'var(--font-sans)' }}>
              {urteilLaeuft ? 'Beurteilung laeuft...' : urteil ? 'Erneut beurteilen' : 'KI-Beurteilung anfordern'}
            </button>
            <div style={{ fontSize:11, color:'var(--text-tertiary)', marginTop:6 }}>
              Liest die Ergebnisse oben und sagt, was davon vor der Abnahme wirklich zaehlt.
            </div>
            {urteilFehler && <div style={{ fontSize:12, color:'var(--status-danger-text)', background:'var(--status-danger-bg)', padding:'8px 12px', borderRadius:6, marginTop:10 }}>{urteilFehler}</div>}
            {urteil && (
              <div style={{ marginTop:12, padding:'12px 14px', background:'var(--bg-app)', borderRadius:8, borderLeft:'3px solid var(--brand-primary-mid)', fontSize:12, color:'var(--text-secondary)', lineHeight:1.7, whiteSpace:'pre-wrap' }}>
                {typeof urteil === 'string' ? urteil : (urteil.summary || urteil.assessment || JSON.stringify(urteil, null, 2))}
              </div>
            )}
          </div>
        </div>
      ) : (
        <div style={{ textAlign:'center', padding:'32px 0', color:'var(--text-tertiary)', fontSize:13 }}>
          QA-Scan noch nicht durchgefuehrt. Prueft SSL, Impressum, Datenschutz, Links, Mobile und PageSpeed.
        </div>
      )}
    </div>
  );
}


export function AbnahmeEmbed({ project, lead, headers, netlify }) {
  const [confirmed, setConfirmed] = useState(project?.status === 'fertig');
  const [saving, setSaving]       = useState(false);
  // Die Bewertungsanfrage (L-105). `POST /api/agents/{id}/review` war gebaut
  // und hatte keinen Zugang; „Trustpilot-Bewertung anfragen" stand hier als
  // blosser Text in einer Liste. Alles, was der Agent braucht, liegt vor:
  // Ansprechpartner, Betrieb und was gemacht wurde.
  const [anfrage, setAnfrage]       = useState('');
  const [anfrageLaeuft, setLaeuft]  = useState(false);
  const [anfrageFehler, setFehler]  = useState('');
  const [kopiert, setKopiert]       = useState(false);

  const liveUrl = netlify?.url || project?.website_url;

  const bewertungAnfragen = async () => {
    setLaeuft(true); setFehler(''); setAnfrage(''); setKopiert(false);
    try {
      const res = await fetch(`${API_BASE_URL}/api/agents/${project.id}/review`, {
        method: 'POST', headers,
        body: JSON.stringify({
          customer_name: lead?.contact_name || lead?.company_name || '',
          company_name: lead?.company_name || '',
          project_summary: `Neue Website fuer ${lead?.company_name || 'den Betrieb'}`
            + (lead?.trade ? ` (${lead.trade})` : '')
            + (liveUrl ? `, jetzt online unter ${liveUrl}` : ''),
          platform: 'google',
        }),
      });
      const d = await res.json();
      if (!res.ok) throw new Error(d.detail || 'Fehler');
      const r = d.result || d;
      setAnfrage(typeof r === 'string' ? r : (r.message || r.text || JSON.stringify(r, null, 2)));
    } catch (e) { setFehler(e.message); }
    finally { setLaeuft(false); }
  };

  const goLive = async () => {
    setSaving(true);
    // Vorher zeigte der Bildschirm "Website ist live! 🎉" auch dann, wenn der
    // Server die Statusaenderung nie bekommen hat.
    const saved = await saveJson(
      `${API_BASE_URL}/api/projects/${project.id}`,
      {
        method: 'PUT', headers,
        body: JSON.stringify({ status: 'fertig', go_live_date: new Date().toISOString().slice(0, 10) }),
      },
      { context: 'Go-Live' }
    );
    if (saved) setConfirmed(true);
    setSaving(false);
  };

  return (
    <div style={{ padding:'20px 24px', display:'flex', flexDirection:'column', gap:20 }}>
      {confirmed ? (
        <div style={{ textAlign:'center', padding:'32px 20px' }}>
          <div style={{ fontSize:56, marginBottom:12 }}>🎉</div>
          <div style={{ fontSize:22, fontWeight:800, color:'var(--text-primary)', marginBottom:8 }}>Website ist live!</div>
          {liveUrl && <a href={liveUrl} target="_blank" rel="noreferrer" style={{ fontSize:14, color:'var(--brand-primary-mid)', fontWeight:600 }}>{liveUrl}</a>}
          <div style={{ marginTop:24, display:'flex', flexDirection:'column', gap:10, alignItems:'center' }}>
            <div style={{ fontSize:13, color:'var(--text-secondary)', fontWeight:600 }}>Naechste Schritte:</div>
            {['Google Business Profil aktualisieren', 'Google Analytics einrichten', 'Vorher/Nachher-Screenshot fuer Portfolio'].map(s => (
              <div key={s} style={{ fontSize:13, color:'var(--text-secondary)' }}>{s}</div>
            ))}
          </div>

          <div style={{ marginTop:24, textAlign:'left', maxWidth:560, marginLeft:'auto', marginRight:'auto', paddingTop:20, borderTop:'1px solid var(--border-light)' }}>
            <div style={{ fontSize:13, fontWeight:700, color:'var(--text-primary)', marginBottom:6 }}>Bewertung anfragen</div>
            <div style={{ fontSize:12, color:'var(--text-tertiary)', marginBottom:12 }}>
              Formuliert die Anfrage aus Betrieb, Ansprechpartner und dem, was gemacht wurde.
            </div>
            <button onClick={bewertungAnfragen} disabled={anfrageLaeuft}
              style={{ padding:'8px 18px', borderRadius:8, border:'1px solid var(--border-medium)', background:'var(--bg-surface)', color:'var(--text-primary)', fontSize:12, fontWeight:600, cursor: anfrageLaeuft ? 'wait' : 'pointer', fontFamily:'var(--font-sans)' }}>
              {anfrageLaeuft ? 'Wird formuliert...' : anfrage ? 'Neu formulieren' : 'Text erzeugen'}
            </button>
            {anfrageFehler && <div style={{ fontSize:12, color:'var(--status-danger-text)', background:'var(--status-danger-bg)', padding:'8px 12px', borderRadius:6, marginTop:10 }}>{anfrageFehler}</div>}
            {anfrage && (
              <div style={{ marginTop:12 }}>
                <div style={{ padding:'12px 14px', background:'var(--bg-app)', borderRadius:8, borderLeft:'3px solid var(--brand-primary-mid)', fontSize:12, color:'var(--text-secondary)', lineHeight:1.7, whiteSpace:'pre-wrap' }}>
                  {anfrage}
                </div>
                <button onClick={() => { navigator.clipboard?.writeText(anfrage); setKopiert(true); }}
                  style={{ marginTop:8, padding:'6px 14px', borderRadius:6, border:'1px solid var(--border-light)', background:'transparent', color:'var(--text-secondary)', fontSize:11, cursor:'pointer', fontFamily:'var(--font-sans)' }}>
                  {kopiert ? 'Kopiert' : 'In die Zwischenablage'}
                </button>
              </div>
            )}
          </div>
        </div>
      ) : (<>
        <div>
          <div style={{ fontSize:13, fontWeight:700, color:'var(--text-primary)', marginBottom:12 }}>Vor der Abnahme pruefen:</div>
          {[
            { label:'QA-Check bestanden', done: !!project?.qa_result },
            { label:'Domain erreichbar', done: !!project?.domain_reachable },
            { label:'Netlify deployed', done: !!netlify?.url },
            { label:'Kunde informiert', done: false },
          ].map(c => (
            <div key={c.label} style={{ display:'flex', alignItems:'center', gap:10, padding:'8px 0', borderBottom:'1px solid var(--border-light)' }}>
              <span style={{ fontSize:16 }}>{c.done ? '\u2705' : '\u25CB'}</span>
              <span style={{ fontSize:13, color: c.done ? 'var(--text-primary)' : 'var(--text-tertiary)' }}>{c.label}</span>
            </div>
          ))}
        </div>
        {liveUrl && (
          <div style={{ background:'var(--bg-surface)', border:'1px solid var(--border-light)', borderRadius:10, padding:14 }}>
            <div style={{ fontSize:12, color:'var(--text-tertiary)', marginBottom:4 }}>Live-URL</div>
            <a href={liveUrl} target="_blank" rel="noreferrer" style={{ fontSize:14, color:'var(--brand-primary-mid)', fontWeight:600 }}>{liveUrl}</a>
          </div>
        )}
        <button onClick={goLive} disabled={saving}
          style={{ padding:'14px 0', borderRadius:10, border:'none', background: saving ? 'var(--border-medium)' : 'var(--success)', color: 'var(--text-on-brand)', fontSize:15, fontWeight:700, cursor: saving ? 'not-allowed' : 'pointer', fontFamily:'var(--font-sans)' }}>
          {saving ? 'Wird gespeichert...' : 'Go Live — Projekt abschliessen'}
        </button>
        <div style={{ fontSize:11, color:'var(--text-tertiary)', textAlign:'center' }}>
          Das Projekt wird als Fertig markiert.
        </div>
      </>)}
    </div>
  );
}

// ── QM-Checkliste ─────────────────────────────────────────────────────────────


// ── QM-Checkliste ─────────────────────────────────────────────────────────────
export function QmChecklisteEmbed({ project, headers }) {
  const ITEMS = [
    { id: 'speed',     label: 'PageSpeed > 80 (Mobile + Desktop)' },
    { id: 'links',     label: 'Alle Links funktionieren (kein 404)' },
    { id: 'mobile',    label: 'Mobile Ansicht korrekt auf iOS & Android' },
    { id: 'impressum', label: 'Impressum + Datenschutz vorhanden' },
    { id: 'ssl',       label: 'SSL-Zertifikat aktiv (https://)' },
    { id: 'forms',     label: 'Kontaktformular sendet korrekt' },
    { id: 'analytics', label: 'Google Analytics / GA4 eingebunden' },
    { id: 'favicon',   label: 'Favicon + Meta-Titel korrekt' },
    { id: 'maps',      label: 'Google Maps / Adresse stimmt' },
    { id: 'social',    label: 'Social Media Links korrekt' },
  ];
  const [checked, setChecked] = useState(() => {
    try { return JSON.parse(project?.gbp_checklist_json || '{}'); } catch { return {}; }
  });

  const toggle = (id) => {
    const previous = checked;
    const next = { ...checked, [id]: !checked[id] };
    setChecked(next);
    saveJson(
      `${API_BASE_URL}/api/projects/${project.id}/gbp-checklist`,
      { method: 'PATCH', headers, body: JSON.stringify({ checked: next }) },
      { context: 'Checkliste speichern', onError: () => setChecked(previous) }
    );
  };

  const done = ITEMS.filter(i => checked[i.id]).length;
  return (
    <div style={{ padding: '20px 24px' }}>
      <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 16 }}>
        {done}/{ITEMS.length} Punkte abgehakt
        <div style={{ marginTop: 6, height: 4, background: 'var(--border-light)', borderRadius: 2, overflow: 'hidden' }}>
          <div style={{ height: '100%', width: `${Math.round(done / ITEMS.length * 100)}%`, background: '#059669', borderRadius: 2, transition: 'width .3s' }} />
        </div>
      </div>
      {ITEMS.map(item => (
        <label key={item.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 0', borderBottom: '1px solid var(--border-light)', cursor: 'pointer' }}>
          <input type="checkbox" checked={!!checked[item.id]} onChange={() => toggle(item.id)} style={{ width: 16, height: 16, cursor: 'pointer', accentColor: '#059669' }} />
          <span style={{ fontSize: 13, color: checked[item.id] ? 'var(--text-tertiary)' : 'var(--text-primary)', textDecoration: checked[item.id] ? 'line-through' : 'none' }}>
            {item.label}
          </span>
        </label>
      ))}
    </div>
  );
}

// ── GBP + QR-Code ─────────────────────────────────────────────────────────────


// ── Website-Vergleich ─────────────────────────────────────────────────────────
export function WebsiteVergleichEmbed({ project, headers }) {
  const [screenshots, setScreenshots] = useState({ before: null, after: null });
  const [takingBefore, setTakingBefore] = useState(false);
  const [takingAfter, setTakingAfter]   = useState(false);

  useEffect(() => {
    loadJson(`${API_BASE_URL}/api/projects/${project.id}/screenshots`, { headers }, { context: 'Screenshots' })
      .then(d => d && setScreenshots(d));
  }, [project.id]); // eslint-disable-line

  const takeScreenshot = async (zeitpunkt, setBusy) => {
    setBusy(true);
    const d = await loadJson(
      `${API_BASE_URL}/api/projects/${project.id}/screenshot/${zeitpunkt}`,
      { method: 'POST', headers },
      { context: 'Screenshot aufnehmen', emptyOn: [] }
    );
    if (d) {
      setScreenshots(s => ({ ...s, [zeitpunkt]: { data: d.screenshot_url, date: new Date().toISOString() } }));
    }
    setBusy(false);
  };

  const takeBefore = () => takeScreenshot('before', setTakingBefore);
  const takeAfter  = () => takeScreenshot('after', setTakingAfter);

  const fmtDate = (iso) => iso ? new Date(iso).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' }) : null;
  const Placeholder = ({ text }) => (
    <div style={{ height: 160, background: 'var(--bg-app)', border: '1.5px dashed var(--border-medium)', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>{text}</span>
    </div>
  );

  return (
    <div style={{ padding: '20px 24px' }}>
      <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 16 }}>📸 Website-Vergleich</div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', marginBottom: 8 }}>VORHER</div>
          {screenshots.before?.data
            ? <img src={screenshots.before.data} alt="Vorher" style={{ width: '100%', borderRadius: 8, border: '1px solid var(--border-light)' }} />
            : <Placeholder text="Noch kein Screenshot" />}
          <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
            <button onClick={takeBefore} disabled={takingBefore}
              style={{ flex: 1, padding: '8px 0', background: 'var(--bg-elevated)', border: '1px solid var(--border-medium)', borderRadius: 7, fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
              {takingBefore ? 'Erstelle...' : '📷 Screenshot erstellen'}
            </button>
          </div>
          {screenshots.before?.date && <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>{fmtDate(screenshots.before.date)}</div>}
        </div>
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, color: '#059669', marginBottom: 8 }}>NACHHER</div>
          {screenshots.after?.data
            ? <img src={screenshots.after.data} alt="Nachher" style={{ width: '100%', borderRadius: 8, border: '1px solid var(--border-light)' }} />
            : <Placeholder text="Noch kein Screenshot" />}
          <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
            <button onClick={takeAfter} disabled={takingAfter}
              style={{ flex: 1, padding: '8px 0', background: 'var(--success)', color: 'var(--text-on-brand)', border: 'none', borderRadius: 7, fontSize: 12, fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
              {takingAfter ? 'Erstelle...' : '📷 Screenshot erstellen'}
            </button>
          </div>
          {screenshots.after?.date && <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>{fmtDate(screenshots.after.date)}</div>}
        </div>
      </div>
    </div>
  );
}

// ── Upsell ────────────────────────────────────────────────────────────────────
