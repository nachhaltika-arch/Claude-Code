/**
 * Technik-Schritte: Zugangsdaten, Netlify, DNS, Live-Daten.
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
import Spinner from './Spinner';




export function ZugangsdatenEmbed({ project, headers }) {
  const [creds, setCreds]       = useState([]);
  const [loading, setLoading]   = useState(true);
  const [saving, setSaving]     = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm]         = useState({ label: '', typ: 'hosting', username: '', password: '', url: '', notes: '' });

  const TYP_OPTIONS = [
    { value: 'hosting',   label: 'Hosting / cPanel' },
    { value: 'ftp',       label: 'FTP / SFTP' },
    { value: 'cms',       label: 'CMS / WordPress' },
    { value: 'domain',    label: 'Domain-Registrar' },
    { value: 'netlify',   label: 'Netlify' },
    { value: 'email',     label: 'E-Mail / SMTP' },
    { value: 'sonstiges', label: 'Sonstiges' },
  ];

  useEffect(() => {
    loadJson(`${API_BASE_URL}/api/projects/${project.id}/credentials`, { headers }, { context: 'Zugangsdaten', fallback: [] })
      .then(d => setCreds(Array.isArray(d) ? d : []))
      .finally(() => setLoading(false));
  }, []); // eslint-disable-line

  const save = async () => {
    if (!form.label.trim()) return;
    setSaving(true);
    const neu = await loadJson(
      `${API_BASE_URL}/api/projects/${project.id}/credentials`,
      { method: 'POST', headers, body: JSON.stringify(form) },
      { context: 'Zugangsdaten speichern', emptyOn: [] }
    );
    if (neu) {
      setCreds(prev => [...prev, neu]);
      setForm({ label: '', typ: 'hosting', username: '', password: '', url: '', notes: '' });
      setShowForm(false);
    }
    setSaving(false);
  };

  const del = async (id) => {
    await fetch(`${API_BASE_URL}/api/projects/${project.id}/credentials/${id}`, { method: 'DELETE', headers });
    setCreds(prev => prev.filter(c => c.id !== id));
  };

  if (loading) return <Spinner />;

  return (
    <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ fontSize: 12, color: 'var(--text-secondary)', background: 'var(--bg-app)', borderRadius: 8, padding: '10px 14px', borderLeft: '3px solid var(--brand-primary)' }}>
        Zugangsdaten werden verschluesselt gespeichert.
      </div>

      {creds.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {creds.map(c => (
            <div key={c.id} style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 8, padding: '12px 14px', display: 'flex', alignItems: 'flex-start', gap: 12 }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>{c.label}</span>
                  <span style={{ fontSize: 12, padding: '1px 7px', borderRadius: 99, background: 'var(--bg-elevated)', color: 'var(--text-tertiary)', fontWeight: 600 }}>
                    {TYP_OPTIONS.find(t => t.value === c.typ)?.label || c.typ || 'Sonstiges'}
                  </span>
                </div>
                {c.username && <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{c.username}</div>}
                {c.url && <a href={c.url} target="_blank" rel="noreferrer" style={{ fontSize: 12, color: 'var(--brand-primary-mid)', textDecoration: 'none', display: 'block' }}>{c.url}</a>}
                {c.notes && <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 4 }}>{c.notes}</div>}
              </div>
              <button onClick={() => del(c.id)} style={{ fontSize: 14, background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)', padding: 4 }}>X</button>
            </div>
          ))}
        </div>
      )}

      {showForm ? (
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 10, padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>Neuen Zugang hinzufuegen</div>
          {[
            { key: 'label', label: 'Bezeichnung *', placeholder: 'z.B. IONOS cPanel' },
            { key: 'username', label: 'Benutzername', placeholder: 'user@domain.de' },
            { key: 'password', label: 'Passwort', placeholder: '', type: 'password' },
            { key: 'url', label: 'URL / Panel', placeholder: 'https://login.ionos.de' },
            { key: 'notes', label: 'Notizen', placeholder: 'Weitere Infos' },
          ].map(f => (
            <div key={f.key}>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.07em', marginBottom: 4 }}>{f.label}</div>
              <input aria-label={f.placeholder} type={f.type || 'text'} value={form[f.key]} onChange={e => setForm(p => ({ ...p, [f.key]: e.target.value }))} placeholder={f.placeholder}
                style={{ width: '100%', padding: '8px 10px', fontSize: 13, border: '1px solid var(--border-light)', borderRadius: 6, background: 'var(--bg-app)', color: 'var(--text-primary)', fontFamily: 'var(--font-sans)', boxSizing: 'border-box' }} />
            </div>
          ))}
          <div>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.07em', marginBottom: 4 }}>Typ</div>
            <select aria-label="Typ" value={form.typ} onChange={e => setForm(p => ({ ...p, typ: e.target.value }))}
              style={{ width: '100%', padding: '8px 10px', fontSize: 13, border: '1px solid var(--border-light)', borderRadius: 6, background: 'var(--bg-app)', color: 'var(--text-primary)', fontFamily: 'var(--font-sans)' }}>
              {TYP_OPTIONS.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
            <button onClick={() => setShowForm(false)} style={{ flex: 1, padding: 8, borderRadius: 6, border: '1px solid var(--border-light)', background: 'transparent', color: 'var(--text-secondary)', fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>Abbrechen</button>
            <button onClick={save} disabled={saving || !form.label.trim()}
              style={{ flex: 2, padding: 8, borderRadius: 6, border: 'none', background: form.label.trim() ? 'var(--brand-primary)' : 'var(--border-medium)', color: 'var(--text-on-brand)', fontSize: 12, fontWeight: 700, cursor: form.label.trim() ? 'pointer' : 'not-allowed', fontFamily: 'var(--font-sans)' }}>
              {saving ? 'Speichert...' : 'Speichern'}
            </button>
          </div>
        </div>
      ) : (
        <button onClick={() => setShowForm(true)}
          style={{ padding: '10px 20px', borderRadius: 8, border: '1.5px dashed var(--border-medium)', background: 'transparent', color: 'var(--brand-primary-mid)', fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', gap: 8 }}>
          + Zugang hinzufuegen
        </button>
      )}

      {creds.length === 0 && !showForm && (
        <div style={{ textAlign: 'center', padding: '24px 0', color: 'var(--text-tertiary)', fontSize: 13 }}>Noch keine Zugangsdaten gespeichert.</div>
      )}
    </div>
  );
}


export function NetlifyEmbed({ project, headers }) {
  const [status, setStatus]             = useState(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const [creating, setCreating]         = useState(false);
  const [deployHtml, setDeployHtml]     = useState('');
  const [deploying, setDeploying]       = useState(false);
  const [deployResult, setDeployResult] = useState(null);
  const [domain, setDomain]             = useState('');
  const [dnsGuide, setDnsGuide]         = useState(null);
  const [error, setError]               = useState('');

  const inputStyle = { width:'100%', padding:'9px 12px', fontSize:13, border:'1px solid var(--border-light)', borderRadius:8, background:'var(--bg-app)', color:'var(--text-primary)', fontFamily:'var(--font-sans)', boxSizing:'border-box' };
  const btnStyle = (disabled) => ({ padding:'9px 20px', borderRadius:8, border:'none', background: disabled ? 'var(--border-medium)' : 'var(--brand-primary)', color:'#fff', fontSize:13, fontWeight:700, cursor: disabled ? 'not-allowed' : 'pointer', fontFamily:'var(--font-sans)', display:'flex', alignItems:'center', gap:6 });
  const cardStyle = { background:'var(--bg-surface)', border:'1px solid var(--border-light)', borderRadius:10, padding:16, display:'flex', flexDirection:'column', gap:10 };

  useEffect(() => {
    loadJson(`${API_BASE_URL}/api/projects/${project.id}/netlify/status`, { headers }, { context: 'Netlify-Status' })
      .then(d => { if (d) setStatus(d); })
      .finally(() => setStatusLoading(false));
  }, []); // eslint-disable-line

  if (statusLoading) return <Spinner />;

  const noToken   = status?.status === 'no_token';
  const siteId    = status?.netlify_site_id;
  const siteUrl   = status?.netlify_site_url;

  return (
    <div style={{ padding:'20px 24px', display:'flex', flexDirection:'column', gap:16 }}>
      {error && <div style={{ fontSize:12, color:'var(--status-danger-text)', background:'var(--status-danger-bg)', padding:'8px 12px', borderRadius:6 }}>{error}</div>}

      {/* 1: Netlify-Status */}
      <div style={{ ...cardStyle, background: noToken ? 'var(--status-danger-bg)' : '#E3F6EF', border: `1px solid ${noToken ? 'var(--status-danger-text)' : '#00875A33'}` }}>
        <div style={{ fontSize:13, fontWeight:700, color: noToken ? 'var(--status-danger-text)' : '#00875A' }}>
          {noToken ? '⚠️ NETLIFY_API_TOKEN nicht konfiguriert' : '✅ Netlify ist konfiguriert und bereit'}
        </div>
        {noToken && (
          <div style={{ fontSize:12, color:'var(--text-secondary)' }}>
            Bitte <code>NETLIFY_API_TOKEN</code> als Umgebungsvariable auf dem Server setzen.
          </div>
        )}
      </div>

      {/* 2: Site anlegen */}
      {!noToken && (
        <div style={cardStyle}>
          <div style={{ fontSize:13, fontWeight:700, color:'var(--text-primary)' }}>
            {siteId ? '✅ Netlify-Site angelegt' : '1. Site anlegen'}
          </div>
          {siteId
            ? <a href={siteUrl} target="_blank" rel="noreferrer" style={{ fontSize:12, color:'var(--brand-primary-mid)' }}>{siteUrl}</a>
            : <button onClick={async () => {
                setCreating(true); setError('');
                try {
                  const r = await fetch(`${API_BASE_URL}/api/projects/${project.id}/netlify/create-site`, { method:'POST', headers });
                  if (!r.ok) throw new Error((await r.json().catch(()=>({}))).detail || 'Fehler');
                  const d = await r.json();
                  setStatus(s => ({ ...s, netlify_site_id: d.site_id, netlify_site_url: d.site_url }));
                } catch (e) { setError(e.message); } finally { setCreating(false); }
              }} disabled={creating} style={btnStyle(creating)}>
                {creating ? 'Anlegen...' : 'Site anlegen'}
              </button>
          }
        </div>
      )}

      {/* 3: Deploy */}
      {siteId && (
        <div style={cardStyle}>
          <div style={{ fontSize:13, fontWeight:700, color:'var(--text-primary)' }}>2. HTML deployen</div>
          <textarea aria-label={'Nur den Body-Inhalt einfügen (kein DOCTYPE nötig — wird automatisch ergänzt)'} value={deployHtml} onChange={e => setDeployHtml(e.target.value)}
            placeholder={'Nur den Body-Inhalt einfügen (kein DOCTYPE nötig — wird automatisch ergänzt)'} rows={5}
            style={{ ...inputStyle, resize:'vertical', fontFamily:'monospace', fontSize:12 }} />
          <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
            Nur den Body-Inhalt aus GrapesJS einfügen. DOCTYPE, head und CSS-Link
            werden automatisch vom System ergänzt.
          </div>
          <button onClick={async () => {
            if (!deployHtml.trim()) { setError('HTML fehlt'); return; }
            setDeploying(true); setError('');
            try {
              const r = await fetch(`${API_BASE_URL}/api/projects/${project.id}/netlify/deploy`, { method:'POST', headers, body: JSON.stringify({ html: deployHtml }) });
              if (!r.ok) throw new Error((await r.json().catch(()=>({}))).detail || 'Fehler');
              setDeployResult(await r.json());
            } catch (e) { setError(e.message); } finally { setDeploying(false); }
          }} disabled={deploying || !deployHtml.trim()} style={btnStyle(deploying || !deployHtml.trim())}>
            {deploying ? (<><span style={{ width:12, height:12, border:'2px solid rgba(255,255,255,.3)', borderTopColor:'#fff', borderRadius:'50%', animation:'spin .8s linear infinite', display:'inline-block' }} />Deploy laeuft...</>) : 'Jetzt deployen'}
          </button>
          {deployResult && (
            <div style={{ background:'var(--status-success-bg)', borderRadius:8, padding:'10px 14px', fontSize:13 }}>
              Deployed: <a href={deployResult.deploy_url} target="_blank" rel="noreferrer" style={{ color:'var(--status-success-text)', fontWeight:600 }}>{deployResult.deploy_url}</a>
            </div>
          )}
        </div>
      )}

      {/* 3b: Multi-Page Deploy — alle Sitemap-Seiten auf einmal */}
      {siteId && (
        <div style={cardStyle}>
          <div style={{ fontSize:13, fontWeight:700, color:'var(--text-primary)' }}>3b. Alle Seiten deployen</div>
          <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
            Deployt alle Seiten aus dem Seitenmanager auf einmal — jede Seite als eigene URL.
            Voraussetzung: Seiten im GrapesJS-Editor gespeichert.
          </div>
          <button onClick={async () => {
            setDeploying(true); setError('');
            try {
              const r = await fetch(`${API_BASE_URL}/api/projects/${project.id}/netlify/deploy-all`, { method:'POST', headers });
              if (!r.ok) throw new Error((await r.json().catch(()=>({}))).detail || `HTTP ${r.status}`);
              const d = await r.json();
              setDeployResult(d);
            } catch (e) { setError(e.message); } finally { setDeploying(false); }
          }} disabled={deploying} style={{
            padding: '10px 18px', borderRadius: 8, border: 'none',
            background: '#7c3aed', opacity: deploying ? 0.5 : 1,
            color: '#fff', fontSize: 13, fontWeight: 700,
            cursor: deploying ? 'not-allowed' : 'pointer',
            fontFamily: 'var(--font-sans)',
            display: 'inline-flex', alignItems: 'center', gap: 8,
          }}>
            {deploying ? (<><span style={{ width:12, height:12, border:'2px solid rgba(255,255,255,.3)', borderTopColor:'#fff', borderRadius:'50%', animation:'spin .8s linear infinite', display:'inline-block' }} />Deploy laeuft...</>) : 'Alle Seiten deployen'}
          </button>
          {deployResult?.pages_deployed && (
            <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
              <strong>{deployResult.pages_deployed.length} Seiten deployed:</strong>{' '}
              {deployResult.pages_deployed.join(' · ')}
            </div>
          )}
        </div>
      )}

      {/* 4: Domain */}
      {siteId && (
        <div style={cardStyle}>
          <div style={{ fontSize:13, fontWeight:700, color:'var(--text-primary)' }}>3. Eigene Domain verbinden</div>
          <div style={{ display:'flex', gap:8 }}>
            <input aria-label="Eigene Domain" value={domain} onChange={e => setDomain(e.target.value)} placeholder="www.kundenwebsite.de" style={{ ...inputStyle, flex:1 }} />
            <button onClick={async () => {
              if (!domain.trim()) return;
              try {
                const r = await fetch(`${API_BASE_URL}/api/projects/${project.id}/netlify/set-domain`, { method:'POST', headers, body: JSON.stringify({ domain: domain.trim() }) });
                if (!r.ok) throw new Error((await r.json().catch(()=>({}))).detail || 'Fehler');
                setDnsGuide(await r.json());
              } catch (e) { setError(e.message); }
            }} disabled={!domain.trim()} style={btnStyle(!domain.trim())}>Verbinden</button>
          </div>
          {dnsGuide && (
            <div style={{ background:'#E6F1FB', border:'1px solid #93c5fd', borderRadius:8, padding:14 }}>
              <div style={{ fontSize:12, fontWeight:700, color:'#185FA5', marginBottom:8 }}>DNS-Eintrag beim Domain-Anbieter setzen:</div>
              {[['Typ','CNAME'],['Name','www'],['Ziel',dnsGuide.cname_target],['TTL','3600']].map(([k,v]) => (
                <div key={k} style={{ display:'flex', gap:16, fontSize:12, padding:'3px 0' }}>
                  <span style={{ width:50, fontWeight:700, color:'#185FA5', flexShrink:0 }}>{k}</span>
                  <span style={{ fontFamily:'monospace' }}>{v}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}


export function DNSEmbed({ project, lead, headers }) {
  const [domain, setDomain]       = useState(lead?.website_url?.replace(/https?:\/\/(www\.)?/,'').split('/')[0] || '');
  const [netlifyUrl, setNetlifyUrl] = useState('');
  const [sent, setSent]           = useState(false);
  const [sending, setSending]     = useState(false);

  useEffect(() => {
    loadJson(`${API_BASE_URL}/api/projects/${project.id}/netlify/status`, { headers }, { context: 'Netlify-Status' })
      .then(d => { if (d?.url) setNetlifyUrl(d.url.replace('https://', '')); });
  }, []); // eslint-disable-line

  return (
    <div style={{ padding:'20px 24px', display:'flex', flexDirection:'column', gap:20 }}>
      <div style={{ fontSize:13, color:'var(--text-secondary)', lineHeight:1.7 }}>
        Der Kunde muss bei seinem Domain-Anbieter einen CNAME-Eintrag setzen, der auf die Netlify-URL zeigt. Das kann 24-48 Stunden dauern.
      </div>

      <div style={{ background:'var(--bg-surface)', border:'1px solid var(--border-light)', borderRadius:10, padding:16 }}>
        <div style={{ fontSize:12, fontWeight:700, color:'var(--text-tertiary)', textTransform:'uppercase', letterSpacing:'.07em', marginBottom:6 }}>Netlify-URL (CNAME-Ziel)</div>
        <div style={{ fontFamily:'monospace', fontSize:14, color:'var(--text-primary)', padding:'8px 12px', background:'var(--bg-app)', borderRadius:6 }}>
          {netlifyUrl || '— Erst Schritt 10 (Netlify deploy) abschliessen —'}
        </div>
      </div>

      {netlifyUrl && (
        <div style={{ background:'#E6F1FB', border:'1px solid #93c5fd', borderRadius:10, padding:16 }}>
          <div style={{ fontSize:13, fontWeight:700, color:'#185FA5', marginBottom:12 }}>DNS-Eintrag beim Domain-Anbieter:</div>
          <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13 }}>
            <tbody>
              {[['Typ','CNAME'],['Name','www'],['Ziel',netlifyUrl],['TTL','3600']].map(([k,v]) => (
                <tr key={k}><td style={{ padding:'6px 16px 6px 0', fontWeight:700, color:'#185FA5', width:80 }}>{k}</td><td style={{ padding:'6px 0', fontFamily:'monospace', color:'#1e3a5f' }}>{v}</td></tr>
              ))}
            </tbody>
          </table>
          <div style={{ marginTop:14 }}>
            <div style={{ fontSize:12, fontWeight:700, color:'var(--text-tertiary)', textTransform:'uppercase', letterSpacing:'.07em', marginBottom:6 }}>Domain des Kunden</div>
            <input aria-label="www.kundenwebsite.de" value={domain} onChange={e => setDomain(e.target.value)} placeholder="www.kundenwebsite.de"
              style={{ width:'100%', padding:'8px 12px', fontSize:13, border:'1px solid var(--border-light)', borderRadius:6, background:'var(--bg-app)', color:'var(--text-primary)', fontFamily:'var(--font-sans)', boxSizing:'border-box' }} />
          </div>
          <button onClick={async () => {
            setSending(true);
            // Der Knopf meldete "Anleitung gesendet", auch wenn die Anfrage
            // scheiterte — der Kunde wartete dann auf eine E-Mail, die nie kam.
            const sentOk = await saveJson(
              `${API_BASE_URL}/api/projects/${project.id}/request-approval`,
              { method: 'POST', headers, body: JSON.stringify({ topic: 'DNS-Einrichtung', notes: `CNAME: www -> ${netlifyUrl}` }) },
              { context: 'Anleitung senden' }
            );
            if (sentOk) setSent(true);
            setSending(false);
          }} disabled={sending || sent || !domain.trim()}
            style={{ marginTop:12, padding:'9px 18px', borderRadius:8, border:'none', background: sent ? 'var(--status-success-bg)' : '#185FA5', color: sent ? 'var(--status-success-text)' : '#fff', fontSize:12, fontWeight:700, cursor: sent ? 'default' : 'pointer', fontFamily:'var(--font-sans)' }}>
            {sent ? 'Anleitung gesendet' : sending ? 'Sendet...' : 'Anleitung per E-Mail senden'}
          </button>
        </div>
      )}

      <div style={{ background:'var(--bg-surface)', border:'1px solid var(--border-light)', borderRadius:10, padding:16 }}>
        <div style={{ fontSize:13, fontWeight:700, color:'var(--text-primary)', marginBottom:8 }}>Domain-Erreichbarkeit pruefen</div>
        <div style={{ fontSize:12, color:'var(--text-secondary)', marginBottom:10 }}>
          {project.domain_reachable
            ? <span style={{ color:'var(--status-success-text)' }}>Domain ist erreichbar (HTTP {project.domain_status_code})</span>
            : <span style={{ color:'var(--text-tertiary)' }}>Noch nicht erreichbar — DNS-Propagation kann bis zu 48h dauern</span>}
        </div>
        <button onClick={async () => { await fetch(`${API_BASE_URL}/api/projects/${project.id}/domain-check`, { method:'POST', headers }); window.location.reload(); }}
          style={{ padding:'7px 16px', borderRadius:6, border:'1px solid var(--border-light)', background:'var(--bg-surface)', color:'var(--text-secondary)', fontSize:12, cursor:'pointer', fontFamily:'var(--font-sans)' }}>
          Jetzt pruefen
        </button>
      </div>
    </div>
  );
}


// ── Live-Daten ────────────────────────────────────────────────────────────────
export function LiveDatenEmbed({ project }) {
  const fields = [
    { label: 'Phase',             value: project?.status?.replace('phase_', 'Phase ') || '—' },
    { label: 'PageSpeed Mobile',  value: project?.pagespeed_mobile  != null ? `${project.pagespeed_mobile}/100`  : '—' },
    { label: 'PageSpeed Desktop', value: project?.pagespeed_desktop != null ? `${project.pagespeed_desktop}/100` : '—' },
    { label: 'Domain erreichbar', value: project?.domain_reachable === true ? '✅ Ja' : project?.domain_reachable === false ? '❌ Nein' : '—' },
    { label: 'Go-Live Datum',     value: project?.abnahme_datum ? new Date(project.abnahme_datum).toLocaleDateString('de-DE') : '—' },
    { label: 'Abnahme durch',     value: project?.abnahme_durch || '—' },
  ];
  return (
    <div style={{ padding: '20px 24px' }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>
        {fields.map(f => (
          <div key={f.label} style={{ padding: 14, background: 'var(--bg-app)', border: '1px solid var(--border-light)', borderRadius: 10 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 4 }}>{f.label}</div>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums' }}>{f.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}


// Nur hier drin gebraucht (Zeile ~895). Das `export` davor nutzte
// niemand — ein Export, den keiner holt, behauptet eine Schnittstelle,
// die es nicht gibt (L-25, 22.08.2026).
