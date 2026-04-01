import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

const SECTIONS = [
  { id: 'projektrahmen', label: 'Projektrahmen', icon: '🏗️', fields: [
    { key: 'kunde', label: 'Kunde / Unternehmen', type: 'text' },
    { key: 'url_aktuell', label: 'URL der bestehenden Website', type: 'text' },
    { key: 'branche_zielgruppe', label: 'Branche / Zielgruppe', type: 'text' },
    { key: 'ansprechpartner', label: 'Ansprechpartner (Design, Content, Technik)', type: 'textarea' },
  ]},
  { id: 'positionierung', label: 'Positionierung & Ziele', icon: '🎯', fields: [
    { key: 'usps', label: 'USPs des Unternehmens', type: 'textarea' },
    { key: 'ziele', label: 'Ziele der neuen Website (Leads, Verkäufe, Branding)', type: 'textarea' },
    { key: 'aktionen', label: 'Welche Aktionen soll die Website auslösen?', type: 'textarea' },
    { key: 'marketing', label: 'Wie kann die Website das Marketing entlasten?', type: 'textarea' },
  ]},
  { id: 'zielgruppe', label: 'Zielgruppe', icon: '👥', fields: [
    { key: 'primaer', label: 'Primäre Zielgruppe (B2B, B2C, beides)', type: 'text' },
    { key: 'informationen', label: 'Verfügbare Infos zur Zielgruppe', type: 'textarea' },
    { key: 'erwartungen', label: 'Erwartungen der Kunden an die Website', type: 'textarea' },
  ]},
  { id: 'wettbewerb', label: 'Wettbewerb', icon: '🔍', fields: [
    { key: 'top5', label: 'Top 5 Mitbewerber', type: 'textarea' },
    { key: 'gut_schlecht', label: 'Was machen Mitbewerber gut / schlecht?', type: 'textarea' },
    { key: 'vorbild', label: 'Vorbilder aus dem Wettbewerb', type: 'textarea' },
  ]},
  { id: 'inhalte', label: 'Inhalte & Content', icon: '📝', fields: [
    { key: 'uebernehmen', label: 'Inhalte von bestehender Seite übernehmen', type: 'textarea' },
    { key: 'fehlen', label: 'Fehlende Inhalte', type: 'textarea' },
    { key: 'nicht_migrieren', label: 'Inhalte die NICHT migriert werden sollen', type: 'textarea' },
    { key: 'lieferant', label: 'Wer liefert die fehlenden Inhalte?', type: 'text', options: ['Kunde', 'Agentur', 'Beides'] },
    { key: 'medientypen', label: 'Medientypen (Text, Bild, Video, Karten)', type: 'text' },
    { key: 'llm_content', label: 'Content für Mensch UND KI/LLM?', type: 'textarea' },
  ]},
  { id: 'funktionen', label: 'Funktionen & Features', icon: '⚙️', fields: [
    { key: 'seo_umfang', label: 'SEO — gewünschter Umfang', type: 'textarea' },
    { key: 'social_media', label: 'Social Media Integration gewünscht?', type: 'text', options: ['Ja', 'Nein', 'Ggf. später'] },
    { key: 'newsletter', label: 'Newsletter Integration? (z.B. Mailchimp)', type: 'text', options: ['Ja', 'Nein', 'Ggf. später'] },
    { key: 'funktionale_anforderungen', label: 'Funktionale Anforderungen (Shop, Buchung...)', type: 'textarea' },
    { key: 'mehrsprachigkeit', label: 'Mehrsprachigkeit gewünscht?', type: 'text', options: ['Nein', 'DE + EN', 'DE + EN + weitere'] },
    { key: 'drittsysteme', label: 'Drittsysteme im Einsatz?', type: 'textarea' },
  ]},
  { id: 'branding', label: 'Branding & Design', icon: '🎨', fields: [
    { key: 'styleguide', label: 'Marken-Styleguide / CI-CD vorhanden?', type: 'text', options: ['Ja', 'Nein', 'In Arbeit'] },
    { key: 'schriften', label: 'Schriften vorhanden?', type: 'text' },
    { key: 'logo_formate', label: 'Logo-Dateien vorhanden? Welche Formate?', type: 'text' },
    { key: 'farben', label: 'Farbwerte definiert?', type: 'text' },
    { key: 'design_gefallt', label: 'Websites die vom Design gefallen', type: 'textarea' },
    { key: 'design_nicht_gefallt', label: 'Websites die NICHT gefallen', type: 'textarea' },
  ]},
  { id: 'hosting', label: 'Hosting & Technik', icon: '🖥️', fields: [
    { key: 'provider', label: 'Aktueller Hosting-Provider', type: 'text' },
    { key: 'zugangsdaten', label: 'Zugangsdaten verfügbar?', type: 'text', options: ['Ja', 'Nein', 'Wird nachgereicht'] },
    { key: 'cookie_banner', label: 'Cookie-Consent Anforderungen', type: 'textarea' },
    { key: 'datenschutz_lieferant', label: 'Wer liefert Datenschutz & Impressum?', type: 'text', options: ['Kunde', 'Anwalt', 'Wir erstellen'] },
  ]},
  { id: 'seo', label: 'SEO & Analytics', icon: '📈', fields: [
    { key: 'analytics_vorhanden', label: 'Google Analytics bereits im Einsatz?', type: 'text', options: ['Ja', 'Nein'] },
    { key: 'ga_konto', label: 'Google Analytics Konto vorhanden?', type: 'text', options: ['Ja', 'Nein', 'Neu anlegen'] },
    { key: 'search_console', label: 'Push über Search Console bei Go-Live?', type: 'text', options: ['Ja', 'Nein'] },
    { key: 'social_media_pflege', label: 'Social Media aktiv? Welche Kanäle?', type: 'textarea' },
  ]},
  { id: 'projektplan', label: 'Projektplan & Timeline', icon: '📅', fields: [
    { key: 'go_live', label: 'Gewünschter Go-Live Termin', type: 'date' },
    { key: 'design_von_bis', label: 'Design-Erstellung: von / bis', type: 'text' },
    { key: 'content_von_bis', label: 'Inhalte erstellen: von / bis', type: 'text' },
    { key: 'programmierung_von_bis', label: 'Entwicklung: von / bis', type: 'text' },
    { key: 'testphase_von_bis', label: 'Preview / Testphase: von / bis', type: 'text' },
    { key: 'go_live_termin', label: 'Finaler Go-Live: Datum', type: 'date' },
  ]},
];

const FREIGABEN = [
  { key: 'auftragserteilung', label: 'Auftragserteilung', phase: '1.1' },
  { key: 'branding_materialien', label: 'Lieferung Branding-Materialien', phase: '1.2' },
  { key: 'pflichtenheft', label: 'Freigabe Pflichtenheft & Sitemap', phase: '1.3' },
  { key: 'sitemap_navigation', label: 'Freigabe finale Sitemap', phase: '2.2' },
  { key: 'content_verantwortung', label: 'Content-Verantwortung klären', phase: '2.3' },
  { key: 'stilrichtung', label: 'Auswahl Stilrichtung', phase: '3.1' },
  { key: 'wireframes', label: 'Freigabe Wireframes', phase: '3.2' },
  { key: 'design_final', label: 'Finale Design-Freigabe', phase: '3.4' },
  { key: 'hosting_domain', label: 'Hosting & Domain gewählt', phase: '4.1' },
  { key: 'content_freigabe', label: 'Content-Freigabe', phase: '6.3' },
  { key: 'google_business', label: 'Google Business Profile', phase: '7.2' },
  { key: 'rechtliches', label: 'Rechtliche Inhalte geprüft', phase: '10.7' },
  { key: 'abnahme_go_live', label: 'Finale Abnahme & Go-Live', phase: '11.2' },
];

export default function BriefingTab({ lead, isMobile }) {
  const { token } = useAuth();
  const h = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeSection, setActiveSection] = useState('projektrahmen');
  const [localData, setLocalData] = useState({});
  const [saved, setSaved] = useState(false);
  const [loadingZielgruppe, setLoadingZielgruppe] = useState(false);
  const [loadingWettbewerb, setLoadingWettbewerb] = useState(false);

  useEffect(() => { loadBriefing(); }, [lead.id]); // eslint-disable-line

  const loadBriefing = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/briefings/${lead.id}`, { headers: h });
      if (res.ok) {
        const data = await res.json();
        // Auto-fill from contact data
        const autoFilled = { ...data };
        if (!autoFilled.projektrahmen?.kunde) {
          autoFilled.projektrahmen = {
            ...(autoFilled.projektrahmen || {}),
            kunde: lead.display_name || lead.company_name || '',
            url_aktuell: lead.website_url || '',
          };
        }
        setLocalData(autoFilled);
      }
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const saveSection = async (sectionId) => {
    setSaving(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/briefings/${lead.id}`, {
        method: 'PATCH', headers: h, body: JSON.stringify({ [sectionId]: localData[sectionId] || {} }),
      });
      if (res.ok) { setSaved(true); setTimeout(() => setSaved(false), 2000); }
    } catch (e) { console.error(e); }
    finally { setSaving(false); }
  };

  const toggleFreigabe = async (key) => {
    const current = localData.freigaben || {};
    const existing = current[key] || {};
    const updated = { ...current, [key]: existing.datum ? {} : { datum: new Date().toLocaleDateString('de-DE'), durch: 'KOMPAGNON' } };
    setLocalData(prev => ({ ...prev, freigaben: updated }));
    try {
      await fetch(`${API_BASE_URL}/api/briefings/${lead.id}`, { method: 'PATCH', headers: h, body: JSON.stringify({ freigaben: updated }) });
    } catch (e) { console.error(e); }
  };

  const updateField = (sectionId, fieldKey, value) => {
    setLocalData(prev => ({ ...prev, [sectionId]: { ...(prev[sectionId] || {}), [fieldKey]: value } }));
  };

  const runZielgruppenanalyse = async () => {
    setLoadingZielgruppe(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/briefings/${lead.id}/zielgruppenanalyse`, { method: 'POST', headers: h });
      if (res.ok) {
        const data = await res.json();
        setLocalData(prev => ({ ...prev, zielgruppe: { ...(prev.zielgruppe || {}), analyse: data.analyse, analyse_datum: data.datum } }));
      }
    } catch (e) { console.error(e); }
    finally { setLoadingZielgruppe(false); }
  };

  const runWettbewerbsanalyse = async () => {
    setLoadingWettbewerb(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/briefings/${lead.id}/wettbewerbsanalyse`, { method: 'POST', headers: h });
      if (res.ok) {
        const data = await res.json();
        setLocalData(prev => ({ ...prev, wettbewerb: { ...(prev.wettbewerb || {}), analyse: data.analyse, analyse_datum: data.datum, region: data.region } }));
      }
    } catch (e) { console.error(e); }
    finally { setLoadingWettbewerb(false); }
  };

  const calcProgress = () => {
    let filled = 0, total = 0;
    SECTIONS.forEach(s => { s.fields.forEach(f => { total++; const val = (localData[s.id] || {})[f.key]; if (val && (typeof val === 'string' ? val.trim() : val)) filled++; }); });
    return total > 0 ? Math.round((filled / total) * 100) : 0;
  };

  const progress = calcProgress();
  const freigaben = localData.freigaben || {};
  const freigabenCount = FREIGABEN.filter(f => freigaben[f.key]?.datum).length;

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 200 }}>
      <div style={{ width: 24, height: 24, borderRadius: '50%', border: '2px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
    </div>
  );

  const currentSection = SECTIONS.find(s => s.id === activeSection);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

      {/* Progress Header */}
      <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: '16px 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10, flexWrap: 'wrap', gap: 8 }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>Briefing-Fragenkatalog</div>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>{lead.display_name || lead.company_name} · {freigabenCount}/{FREIGABEN.length} Freigaben</div>
          </div>
          <div style={{ fontSize: 20, fontWeight: 700, color: progress >= 80 ? 'var(--status-success-text)' : progress >= 40 ? 'var(--status-warning-text)' : 'var(--text-tertiary)' }}>{progress}%</div>
        </div>
        <div style={{ height: 6, background: 'var(--border-light)', borderRadius: 3, overflow: 'hidden' }}>
          <div style={{ width: `${progress}%`, height: '100%', background: progress >= 80 ? 'var(--status-success-text)' : progress >= 40 ? 'var(--status-warning-text)' : 'var(--brand-primary)', borderRadius: 3, transition: 'width 0.4s ease' }} />
        </div>
      </div>

      <div style={{ display: 'flex', gap: 12, flexDirection: isMobile ? 'column' : 'row', alignItems: 'flex-start' }}>

        {/* Section Nav */}
        <div style={{ flexShrink: 0, width: isMobile ? '100%' : 180 }}>
          <div style={{ display: 'flex', flexDirection: isMobile ? 'row' : 'column', gap: 4, overflowX: isMobile ? 'auto' : 'visible' }}>
            {SECTIONS.map(s => {
              const data = localData[s.id] || {};
              const filledFields = s.fields.filter(f => { const v = data[f.key]; return v && (typeof v === 'string' ? v.trim() : v); }).length;
              const isActive = activeSection === s.id;
              return (
                <button key={s.id} onClick={() => setActiveSection(s.id)} style={{
                  display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px',
                  background: isActive ? 'var(--bg-active)' : 'transparent',
                  border: isActive ? '1px solid var(--border-medium)' : '1px solid transparent',
                  borderRadius: 'var(--radius-md)', cursor: 'pointer', fontFamily: 'var(--font-sans)',
                  textAlign: 'left', flexShrink: 0, width: isMobile ? 'auto' : '100%',
                }}>
                  <span style={{ fontSize: 14 }}>{s.icon}</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 12, fontWeight: isActive ? 600 : 400, color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)', whiteSpace: 'nowrap' }}>{s.label}</div>
                    {!isMobile && <div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{filledFields}/{s.fields.length}</div>}
                  </div>
                  {filledFields === s.fields.length && <span style={{ fontSize: 10, color: 'var(--status-success-text)' }}>✓</span>}
                </button>
              );
            })}
            <button onClick={() => setActiveSection('freigaben')} style={{
              display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px',
              background: activeSection === 'freigaben' ? 'var(--bg-active)' : 'transparent',
              border: activeSection === 'freigaben' ? '1px solid var(--border-medium)' : '1px solid transparent',
              borderRadius: 'var(--radius-md)', cursor: 'pointer', fontFamily: 'var(--font-sans)',
              textAlign: 'left', flexShrink: 0, width: isMobile ? 'auto' : '100%',
            }}>
              <span style={{ fontSize: 14 }}>⭐</span>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 12, fontWeight: activeSection === 'freigaben' ? 600 : 400, color: activeSection === 'freigaben' ? 'var(--text-primary)' : 'var(--text-secondary)', whiteSpace: 'nowrap' }}>Freigaben</div>
                {!isMobile && <div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{freigabenCount}/{FREIGABEN.length}</div>}
              </div>
            </button>
          </div>
        </div>

        {/* Content Area */}
        <div style={{ flex: 1, minWidth: 0 }}>

          {/* Freigaben */}
          {activeSection === 'freigaben' && (
            <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
              <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border-light)', fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                ⭐ Kundenentscheidungen & Freigaben
              </div>
              {FREIGABEN.map((f, i) => {
                const fg = freigaben[f.key] || {};
                const done = !!fg.datum;
                return (
                  <div key={f.key} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 18px', borderBottom: i < FREIGABEN.length - 1 ? '1px solid var(--border-light)' : 'none', background: done ? 'var(--status-success-bg)' : 'transparent' }}>
                    <button onClick={() => toggleFreigabe(f.key)} style={{
                      width: 22, height: 22, borderRadius: 4, border: done ? 'none' : '2px solid var(--border-medium)',
                      background: done ? 'var(--status-success-text)' : 'transparent', cursor: 'pointer', flexShrink: 0,
                      display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: 12, fontWeight: 700,
                    }}>{done ? '✓' : ''}</button>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 12, fontWeight: 500, color: done ? 'var(--status-success-text)' : 'var(--text-primary)' }}>{f.label}</div>
                      {done && fg.datum && <div style={{ fontSize: 10, color: 'var(--status-success-text)', opacity: 0.8, marginTop: 1 }}>Freigegeben am {fg.datum}</div>}
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', flexShrink: 0 }}>Phase {f.phase}</div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Section Form */}
          {activeSection !== 'freigaben' && currentSection && (
            <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
              <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span>{currentSection.icon}</span>{currentSection.label}
                </div>
                <button onClick={() => saveSection(activeSection)} disabled={saving} style={{
                  padding: '6px 14px', background: saved ? 'var(--status-success-text)' : 'var(--brand-primary)',
                  color: 'white', border: 'none', borderRadius: 'var(--radius-sm)', fontSize: 12, fontWeight: 500,
                  cursor: saving ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)', transition: 'background 0.2s',
                }}>{saved ? '✓ Gespeichert' : saving ? 'Speichert...' : 'Speichern'}</button>
              </div>

              {/* AI Zielgruppenanalyse */}
              {activeSection === 'zielgruppe' && (
                <div style={{ padding: '12px 18px', borderBottom: '1px solid var(--border-light)', background: 'var(--bg-app)' }}>
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 8 }}>
                    KI-Analyse basierend auf Branche "{lead.trade || '—'}" und Standort "{lead.city || '—'}"
                  </div>
                  <button onClick={runZielgruppenanalyse} disabled={loadingZielgruppe} style={{
                    padding: '9px 18px', background: loadingZielgruppe ? 'var(--bg-surface)' : '#008eaa',
                    color: loadingZielgruppe ? 'var(--text-tertiary)' : 'white', border: '1px solid var(--border-medium)',
                    borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 600,
                    cursor: loadingZielgruppe ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)',
                    display: 'inline-flex', alignItems: 'center', gap: 8,
                  }}>
                    {loadingZielgruppe ? <><span style={{ width: 10, height: 10, borderRadius: '50%', border: '2px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite', display: 'inline-block' }} />Analyse läuft...</> : '🤖 KI-Zielgruppenanalyse starten'}
                  </button>
                  {localData.zielgruppe?.analyse && (
                    <div style={{ marginTop: 12, padding: '12px 14px', background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>
                      <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginBottom: 6, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                        KI-Analyse{localData.zielgruppe?.analyse_datum && ` · ${localData.zielgruppe.analyse_datum}`}
                      </div>
                      {localData.zielgruppe.analyse}
                    </div>
                  )}
                </div>
              )}

              {/* AI Wettbewerbsanalyse */}
              {activeSection === 'wettbewerb' && (
                <div style={{ padding: '12px 18px', borderBottom: '1px solid var(--border-light)', background: 'var(--bg-app)' }}>
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 8 }}>
                    Wettbewerbsanalyse für Region "{lead.city || '—'}" + 50 km Umkreis
                  </div>
                  <button onClick={runWettbewerbsanalyse} disabled={loadingWettbewerb} style={{
                    padding: '9px 18px', background: loadingWettbewerb ? 'var(--bg-surface)' : '#d4a017',
                    color: loadingWettbewerb ? 'var(--text-tertiary)' : 'white', border: '1px solid var(--border-medium)',
                    borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 600,
                    cursor: loadingWettbewerb ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)',
                    display: 'inline-flex', alignItems: 'center', gap: 8,
                  }}>
                    {loadingWettbewerb ? <><span style={{ width: 10, height: 10, borderRadius: '50%', border: '2px solid var(--border-light)', borderTopColor: '#d4a017', animation: 'spin 0.8s linear infinite', display: 'inline-block' }} />Analyse läuft...</> : '🔍 KI-Wettbewerbsanalyse starten'}
                  </button>
                  {localData.wettbewerb?.analyse && (
                    <div style={{ marginTop: 12, padding: '12px 14px', background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>
                      <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginBottom: 6, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                        KI-Wettbewerbsanalyse{localData.wettbewerb?.region && ` · ${localData.wettbewerb.region}`}{localData.wettbewerb?.analyse_datum && ` · ${localData.wettbewerb.analyse_datum}`}
                      </div>
                      {localData.wettbewerb.analyse}
                    </div>
                  )}
                </div>
              )}

              <div style={{ padding: '16px 18px', display: 'flex', flexDirection: 'column', gap: 14 }}>
                {currentSection.fields.map(field => {
                  const val = (localData[activeSection] || {})[field.key] || '';
                  return (
                    <div key={field.key}>
                      <label style={{ display: 'block', fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 5 }}>{field.label}</label>
                      {field.options ? (
                        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                          {field.options.map(opt => (
                            <button key={opt} onClick={() => updateField(activeSection, field.key, opt)} style={{
                              padding: '5px 12px', background: val === opt ? 'var(--brand-primary)' : 'var(--bg-app)',
                              color: val === opt ? 'white' : 'var(--text-secondary)', border: '1px solid var(--border-medium)',
                              borderRadius: 'var(--radius-full)', fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)', transition: 'all 0.15s',
                            }}>{opt}</button>
                          ))}
                        </div>
                      ) : field.type === 'textarea' ? (
                        <textarea value={val} onChange={e => updateField(activeSection, field.key, e.target.value)} rows={3}
                          placeholder={`${field.label}...`}
                          style={{ width: '100%', padding: '9px 12px', background: 'var(--bg-app)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', fontSize: 13, color: 'var(--text-primary)', fontFamily: 'var(--font-sans)', resize: 'vertical', lineHeight: 1.5, boxSizing: 'border-box' }} />
                      ) : (
                        <input type={field.type || 'text'} value={val} onChange={e => updateField(activeSection, field.key, e.target.value)}
                          placeholder={`${field.label}...`}
                          style={{ width: '100%', padding: '9px 12px', background: 'var(--bg-app)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', fontSize: 13, color: 'var(--text-primary)', fontFamily: 'var(--font-sans)', boxSizing: 'border-box' }} />
                      )}
                    </div>
                  );
                })}
              </div>
              <div style={{ padding: '12px 18px', borderTop: '1px solid var(--border-light)', display: 'flex', justifyContent: 'flex-end' }}>
                <button onClick={() => saveSection(activeSection)} disabled={saving} style={{
                  padding: '9px 20px', background: saved ? 'var(--status-success-text)' : 'var(--brand-primary)',
                  color: 'white', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600,
                  cursor: saving ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)', transition: 'background 0.2s',
                }}>{saved ? '✓ Gespeichert' : saving ? 'Speichert...' : 'Abschnitt speichern'}</button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
