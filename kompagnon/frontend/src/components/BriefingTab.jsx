import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';

const SECTIONS = [

  // 1. Unternehmen & Projekt
  { id: 'projektrahmen', label: 'Unternehmen & Projekt', icon: '🏢', fields: [
    { key: 'kunde', label: 'Unternehmensname', type: 'text', placeholder: 'z.B. Sanitaer Mueller GmbH', hint: 'Wird automatisch aus der Kundenkartei uebernommen.' },
    { key: 'url_aktuell', label: 'Aktuelle Website-URL', type: 'text', placeholder: 'https://www.beispiel.de' },
    { key: 'branche', label: 'Branche / Gewerk', type: 'text', placeholder: 'z.B. Sanitaer & Heizung, Steuerberatung, Kosmetikstudio' },
    { key: 'ansprechpartner', label: 'Ansprechpartner (Name, Telefon, E-Mail)', type: 'textarea', placeholder: 'Wer ist fuer Freigaben und Rueckfragen zustaendig?', rows: 3 },
  ]},

  // 2. Ziele & Erfolg
  { id: 'positionierung', label: 'Ziele & Erfolg', icon: '🎯', fields: [
    { key: 'hauptziel', label: 'Was ist das Hauptziel der neuen Website?', type: 'textarea', placeholder: 'z.B. Mehr Anfragen generieren, Vertrauen aufbauen, Mitarbeiter gewinnen', rows: 3 },
    { key: 'aktionen', label: 'Was soll ein Besucher auf der Website als Erstes tun?', type: 'text', options: ['Anrufen', 'Kontaktformular ausfuellen', 'WhatsApp schreiben', 'Termin buchen', 'Angebot anfragen', 'Newsletter abonnieren'], placeholder: 'Primaere Call-to-Action' },
    { key: 'problem', label: 'Welches Problem loest das Unternehmen fuer seine Kunden?', type: 'textarea', placeholder: 'z.B. Kunden wissen nicht, an wen sie sich bei einem Rohrbruch wenden sollen — wir sind 24/7 erreichbar.', rows: 3 },
    { key: 'erfolg', label: 'Woran messen wir gemeinsam, ob die Website erfolgreich ist?', type: 'textarea', placeholder: 'z.B. 20 Anfragen/Monat, Sichtbarkeit fuer "Elektriker Koblenz", Bewerbungen ueber die Website', rows: 3 },
  ]},

  // 3. Zielgruppe
  { id: 'zielgruppe', label: 'Zielgruppe', icon: '👥', fields: [
    { key: 'primaer', label: 'Wer ist die primaere Zielgruppe?', type: 'text', options: ['Privatkunden (B2C)', 'Geschaeftskunden (B2B)', 'Beides'] },
    { key: 'typischer_kunde', label: 'Beschreibe deinen idealen Kunden', type: 'textarea', placeholder: 'z.B. Eigenheimbesitzer, 40-60 Jahre, plant Badsanierung, sucht lokalen Fachbetrieb dem er vertrauen kann.', rows: 3 },
    { key: 'haeufigste_anfrage', label: 'Was fragen Kunden am haeufigsten an?', type: 'text', placeholder: 'z.B. Kostenanfrage Heizungstausch, Notdienst Rohrbruch, Jahreswartung' },
    { key: 'region', label: 'Fuer welche Region wird die Website optimiert?', type: 'text', placeholder: 'z.B. Koblenz und Umgebung, ca. 40 km Radius' },
  ]},

  // 4. Alleinstellung & Wettbewerb
  { id: 'wettbewerb', label: 'Alleinstellung & Wettbewerb', icon: '🏆', fields: [
    { key: 'usp', label: 'Was macht das Unternehmen einzigartig? (USP)', type: 'textarea', placeholder: 'z.B. 25 Jahre Erfahrung, 24h-Notdienst, Festpreisgarantie, familiengefuehrt seit 3 Generationen', rows: 4 },
    { key: 'mitbewerber', label: 'Welche Mitbewerber sind bekannt?', type: 'textarea', placeholder: 'z.B. Firma Schmidt Sanitaer (stark: guenstiger Preis), Installateur Meyer (stark: gute Google-Bewertungen)', rows: 3 },
    { key: 'vorbilder', label: 'Gibt es Websites, die als Vorbild dienen? (URLs)', type: 'textarea', placeholder: 'Was gefaellt daran besonders? z.B. https://www.beispiel.de — tolle Bildsprache, klar strukturiert', rows: 3 },
  ]},

  // 5. Seiten & Struktur
  { id: 'inhalte', label: 'Seiten & Struktur', icon: '🗺️', fields: [
    { key: 'seiten', label: 'Welche Seiten soll die neue Website haben?', type: 'textarea', placeholder: 'z.B. Startseite, Ueber uns, Leistungen (je Seite: Badsanierung / Heizung / Notdienst), Referenzen, Stellenangebote, Kontakt', rows: 4 },
    { key: 'hauptbotschaft', label: 'Was ist die Hauptbotschaft der Startseite?', type: 'textarea', placeholder: 'Was soll ein Besucher in den ersten 3 Sekunden verstehen?', rows: 3 },
    { key: 'besondere_seiten', label: 'Gibt es besondere Seiten oder Funktionen die unbedingt rein muessen?', type: 'textarea', placeholder: 'z.B. Bewerbungsseite, Bildergalerie, Preisliste, Terminbuchung, Referenz-Projekte mit Vorher/Nachher-Fotos', rows: 3 },
    { key: 'nicht_migrieren', label: 'Was von der alten Website soll NICHT uebernommen werden?', type: 'textarea', placeholder: 'z.B. veraltete Preislisten, alte Teamfotos, nicht mehr angebotene Leistungen', rows: 2 },
  ]},

  // 6. Design & Stil
  { id: 'branding', label: 'Design & Stil', icon: '🎨', fields: [
    { key: 'stil', label: 'Welche Stilrichtung passt zum Unternehmen?', type: 'text', options: ['Modern & Minimalistisch', 'Klassisch & Serioes', 'Frisch & Freundlich', 'Industriell & Handwerklich', 'Hochwertig & Premium', 'Noch offen — Vorschlag gewuenscht'] },
    { key: 'stimmung', label: 'Welche Stimmung soll die Website transportieren?', type: 'textarea', placeholder: 'z.B. Vertrauen und Sicherheit, modern aber nicht kalt, handwerklich-bodenstaendig', rows: 3 },
    { key: 'farben', label: 'Gibt es Farbvorgaben oder Praeferenzen?', type: 'textarea', placeholder: 'z.B. Firmenfarbe Blau (#0056b3), kein Rot, gerne erdige Toene, aus CI-Handbuch', rows: 2 },
    { key: 'schrift', label: 'Gibt es Vorgaben zur Typografie / Schrift?', type: 'text', placeholder: 'z.B. serifenlos und modern, oder aus bestehendem CI uebernehmen' },
    { key: 'bildsprache', label: 'Welche Bildsprache ist gewuenscht?', type: 'textarea', placeholder: 'z.B. echte Mitarbeiterfotos statt Stockfotos, Baustellen-Atmosphaere, helle Stimmung', rows: 3 },
  ]},

  // 7. Inhalte & Assets
  { id: 'funktionen', label: 'Inhalte & Assets', icon: '📦', fields: [
    { key: 'logo', label: 'Logo vorhanden?', type: 'text', options: ['Ja, als Vektordatei (SVG/AI/EPS)', 'Ja, nur als PNG/JPG', 'Nein — Logo muss neu erstellt werden', 'Logo soll ueberarbeitet werden'] },
    { key: 'fotos', label: 'Fotos vorhanden?', type: 'text', options: ['Ja, professionelle Fotos', 'Ja, aber nur Handy-Fotos', 'Nein — Fotoshooting wird organisiert', 'Stockfotos sind okay'] },
    { key: 'texte', label: 'Wer liefert die Texte?', type: 'text', options: ['Kunde liefert fertige Texte', 'Agentur erstellt Texte (KI-gestuetzt)', 'Gemeinsam — Kunde liefert Infos, Agentur textet'] },
    { key: 'sonstige_assets', label: 'Weitere Assets vorhanden? (Videos, PDFs, Zertifikate, Auszeichnungen)', type: 'textarea', placeholder: 'z.B. Imagefilm vorhanden, Zertifikat Meisterbetrieb, Innungsauszeichnung', rows: 3 },
  ]},

  // 8. Technik & Funktionen
  { id: 'struktur', label: 'Technik & Funktionen', icon: '⚙️', fields: [
    { key: 'formulare', label: 'Welche Formulare oder Funktionen werden benoetigt?', type: 'textarea', placeholder: 'z.B. Kontaktformular, Terminbuchung, Rueckruf-Button, WhatsApp-Chat, Bewerbungsformular', rows: 3 },
    { key: 'mehrsprachigkeit', label: 'Mehrsprachigkeit gewuenscht?', type: 'text', options: ['Nein, nur Deutsch', 'Ja — Deutsch + Englisch', 'Ja — andere Sprache(n)'] },
    { key: 'rechtliches', label: 'Impressum & Datenschutz — wer ist zustaendig?', type: 'text', options: ['Wir erstellen (Standard)', 'Kunde hat eigenen Anwalt', 'Bestehendes Impressum uebernehmen'] },
    { key: 'integrationen', label: 'Sollen externe Dienste eingebunden werden?', type: 'textarea', placeholder: 'z.B. Google Maps, Instagram-Feed, Trustpilot-Widget, Calendly, Mailchimp', rows: 3 },
  ]},

  // 9. SEO & Marketing
  { id: 'seo', label: 'SEO & Marketing', icon: '📈', fields: [
    { key: 'keywords', label: 'Fuer welche Suchbegriffe soll die Website gefunden werden?', type: 'textarea', placeholder: 'z.B. "Sanitaer Koblenz", "Heizung installieren Neuwied", "Notdienst Rohrbruch"', rows: 3 },
    { key: 'google_business', label: 'Ist ein Google Business Profil vorhanden?', type: 'text', options: ['Ja, aktiv gepflegt', 'Ja, aber veraltet', 'Nein — wird angelegt', 'Weiss ich nicht'] },
    { key: 'social_media', label: 'Welche Social-Media-Kanaele sind aktiv?', type: 'textarea', placeholder: 'z.B. Facebook (500 Follower, aktiv), Instagram (kaum genutzt), kein LinkedIn', rows: 2 },
  ]},

  // 10. Zeitplan & Sonstiges
  { id: 'projektplan', label: 'Zeitplan & Sonstiges', icon: '📅', fields: [
    { key: 'go_live', label: 'Gewuenschter Go-Live Termin', type: 'date', hint: 'Realistisch einplanen: Briefing > Design > Content > Entwicklung > Abnahme = 6-10 Wochen.' },
    { key: 'besonderheiten', label: 'Gibt es zeitliche Einschraenkungen oder besondere Ereignisse?', type: 'textarea', placeholder: 'z.B. Messe im Maerz, Betriebsurlaub im August, Jubilaeum im Oktober', rows: 2 },
    { key: 'wartung', label: 'Wer pflegt die Website nach dem Go-Live?', type: 'text', options: ['Kunde selbst', 'Agentur uebernimmt Wartung', 'Noch offen'] },
    { key: 'anmerkungen', label: 'Weitere Anmerkungen, Wuensche oder offene Fragen', type: 'textarea', placeholder: 'Alles was noch wichtig ist — auch wenn es noch keine Antwort gibt.', rows: 4 },
  ]},

];

const FREIGABEN = [
  { key: 'auftragserteilung',    label: 'Auftragserteilung & Anzahlung',         phase: '1.0' },
  { key: 'assets_geliefert',     label: 'Logo, Fotos & Texte eingegangen',        phase: '1.2' },
  { key: 'sitemap_freigabe',     label: 'Seitenstruktur & Sitemap freigegeben',   phase: '2.0' },
  { key: 'design_entwurf',       label: 'Design-Entwurf Startseite freigegeben',  phase: '3.0' },
  { key: 'design_final',         label: 'Finales Design aller Seiten freigegeben',phase: '3.2' },
  { key: 'content_freigabe',     label: 'Alle Inhalte geprueft & freigegeben',    phase: '4.0' },
  { key: 'testphase',            label: 'Testversion auf Staging geprueft',        phase: '5.0' },
  { key: 'rechtliches',          label: 'Impressum & Datenschutz geprueft',        phase: '5.1' },
  { key: 'google_business',      label: 'Google Business Profil aktualisiert',    phase: '6.0' },
  { key: 'abnahme_go_live',      label: 'Finale Abnahme & Go-Live Freigabe',      phase: '6.2' },
  { key: 'einweisung',           label: 'Einweisung CMS / Website-Pflege',        phase: '7.0' },
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
  const [prefilling, setPrefilling] = useState(false);
  const [prefillDone, setPrefillDone] = useState(false);

  useEffect(() => { loadBriefing(); }, [lead.id]); // eslint-disable-line

  const loadBriefing = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/briefings/${lead.id}`, { headers: h });
      if (res.ok) {
        const data = await res.json();
        const autoFilled = { ...data };

        // Schicht 1 — Stammdaten aus Lead auto-fill
        autoFilled.projektrahmen = {
          ...(autoFilled.projektrahmen || {}),
          kunde:       autoFilled.projektrahmen?.kunde || lead.display_name || lead.company_name || '',
          url_aktuell: autoFilled.projektrahmen?.url_aktuell || lead.website_url || '',
          branche:     autoFilled.projektrahmen?.branche || lead.trade || '',
          ansprechpartner: autoFilled.projektrahmen?.ansprechpartner || lead.contact_name || '',
        };

        // Schicht 2 — Flat Wizard-Felder in JSON-Sektionen uebernehmen (nur leere Felder)
        const fill = (section, key, flatKey) => {
          if (!autoFilled[section]?.[key] && data[flatKey]) {
            autoFilled[section] = { ...(autoFilled[section] || {}), [key]: data[flatKey] };
          }
        };
        fill('wettbewerb', 'usp', 'usp');
        fill('wettbewerb', 'mitbewerber', 'mitbewerber');
        fill('wettbewerb', 'vorbilder', 'vorbilder');
        fill('branding', 'stil', 'stil');
        fill('branding', 'farben', 'farben');
        fill('positionierung', 'hauptziel', 'leistungen');
        fill('zielgruppe', 'region', 'einzugsgebiet');
        fill('inhalte', 'seiten', 'wunschseiten');

        // Schicht 3 — Projekt-Flags in Assets-Sektion
        if (data.logo_vorhanden && !autoFilled.funktionen?.logo) {
          autoFilled.funktionen = { ...(autoFilled.funktionen || {}), logo: 'Ja, als Vektordatei (SVG/AI/EPS)' };
        }
        if (data.fotos_vorhanden && !autoFilled.funktionen?.fotos) {
          autoFilled.funktionen = { ...(autoFilled.funktionen || {}), fotos: 'Ja, professionelle Fotos' };
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

  const prefillFromWebsite = async () => {
    if (!lead?.project_id && !lead?.id) return;
    setPrefilling(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/leads/${lead.id}/briefing-prefill`, { method: 'POST', headers: h });
      if (!res.ok) { const err = await res.json().catch(() => ({})); toast.error(err.detail || 'Vorausfüllen fehlgeschlagen'); return; }
      const data = await res.json();
      const updates = {};
      for (const field of ['gewerk', 'leistungen', 'einzugsgebiet', 'usp', 'wunschseiten', 'zielgruppe']) {
        if (data[field] && !localData[field]?.trim?.()) updates[field] = data[field];
      }
      if (Object.keys(updates).length === 0) { toast('Alle Felder bereits ausgefüllt', { icon: 'ℹ️' }); return; }
      setLocalData(prev => ({ ...prev, ...updates }));
      setPrefillDone(true);
      toast.success(`${Object.keys(updates).length} Felder aus Website vorausgefüllt`);
    } catch { toast.error('Verbindungsfehler beim Vorausfüllen'); }
    finally { setPrefilling(false); }
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

  // Mobile step navigation
  const ALL_SECTIONS = [...SECTIONS.map(s => s.id), 'freigaben'];
  const currentMobileIndex = ALL_SECTIONS.indexOf(activeSection);
  const isLastMobileSection = currentMobileIndex === ALL_SECTIONS.length - 1;

  const handleMobileBack = () => {
    if (currentMobileIndex > 0) setActiveSection(ALL_SECTIONS[currentMobileIndex - 1]);
  };

  const handleMobileNext = async () => {
    if (activeSection !== 'freigaben') await saveSection(activeSection);
    if (!isLastMobileSection) setActiveSection(ALL_SECTIONS[currentMobileIndex + 1]);
  };

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

      {/* Prefill from website button */}
      <button onClick={prefillFromWebsite} disabled={prefilling} style={{
        padding: '8px 16px', background: prefillDone ? 'var(--status-success-bg)' : 'var(--brand-primary-light)',
        color: prefillDone ? 'var(--status-success-text)' : 'var(--brand-primary-dark)',
        border: `1px solid ${prefillDone ? 'var(--status-success-text)' : 'var(--brand-primary-mid, var(--border-light))'}`,
        borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 600,
        cursor: prefilling ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)',
        display: 'flex', alignItems: 'center', gap: 6, alignSelf: 'flex-start',
      }}>
        {prefilling ? (<><span style={{ width: 12, height: 12, border: '2px solid currentColor', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.8s linear infinite', display: 'inline-block' }} />Analysiere Website…</>) : prefillDone ? '✓ Vorausgefüllt' : '🔍 Aus Website vorausfüllen'}
      </button>

      {/* ── MOBILE: Step counter + progress bar ── */}
      {isMobile && (
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: '14px 16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>
              {activeSection === 'freigaben'
                ? '⭐ Freigaben'
                : (() => { const s = SECTIONS.find(x => x.id === activeSection); return s ? `${s.icon} ${s.label}` : ''; })()
              }
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
              {currentMobileIndex + 1} / {ALL_SECTIONS.length}
            </div>
          </div>
          <div style={{ height: 4, background: 'var(--border-light)', borderRadius: 2, overflow: 'hidden' }}>
            <div style={{ width: `${((currentMobileIndex + 1) / ALL_SECTIONS.length) * 100}%`, height: '100%', background: 'var(--brand-primary)', borderRadius: 2, transition: 'width 0.3s ease' }} />
          </div>
        </div>
      )}

      <div style={{ display: 'flex', gap: 12, flexDirection: 'row', alignItems: 'flex-start' }}>

        {/* Section Nav — desktop only */}
        {!isMobile && (
          <div style={{ flexShrink: 0, width: 180 }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
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
                    textAlign: 'left', width: '100%',
                  }}>
                    <span style={{ fontSize: 14 }}>{s.icon}</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 12, fontWeight: isActive ? 600 : 400, color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)', whiteSpace: 'nowrap' }}>{s.label}</div>
                      <div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{filledFields}/{s.fields.length}</div>
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
                textAlign: 'left', width: '100%',
              }}>
                <span style={{ fontSize: 14 }}>⭐</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 12, fontWeight: activeSection === 'freigaben' ? 600 : 400, color: activeSection === 'freigaben' ? 'var(--text-primary)' : 'var(--text-secondary)', whiteSpace: 'nowrap' }}>Freigaben</div>
                  <div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{freigabenCount}/{FREIGABEN.length}</div>
                </div>
              </button>
            </div>
          </div>
        )}

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
                    padding: '9px 18px', background: loadingWettbewerb ? 'var(--bg-surface)' : 'var(--status-warning-text)',
                    color: loadingWettbewerb ? 'var(--text-tertiary)' : 'white', border: '1px solid var(--border-medium)',
                    borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 600,
                    cursor: loadingWettbewerb ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)',
                    display: 'inline-flex', alignItems: 'center', gap: 8,
                  }}>
                    {loadingWettbewerb ? <><span style={{ width: 10, height: 10, borderRadius: '50%', border: '2px solid var(--border-light)', borderTopColor: 'var(--status-warning-text)', animation: 'spin 0.8s linear infinite', display: 'inline-block' }} />Analyse läuft...</> : '🔍 KI-Wettbewerbsanalyse starten'}
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
                  const ph = field.placeholder || `${field.label}...`;
                  const inputStyle = { width: '100%', padding: isMobile ? '12px' : '9px 12px', minHeight: isMobile ? 44 : undefined, background: 'var(--bg-app)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', fontSize: 13, color: 'var(--text-primary)', fontFamily: 'var(--font-sans)', boxSizing: 'border-box', outline: 'none' };
                  return (
                    <div key={field.key}>
                      <label style={{ display: 'block', fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 5 }}>{field.label}</label>
                      {field.hint && <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 6, lineHeight: 1.5 }}>{field.hint}</div>}
                      {field.options ? (
                        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                          {field.options.map(opt => (
                            <button key={opt} onClick={() => updateField(activeSection, field.key, opt)} style={{
                              padding: isMobile ? '10px 16px' : '5px 12px', minHeight: isMobile ? 44 : undefined,
                              background: val === opt ? 'var(--brand-primary)' : 'var(--bg-app)',
                              color: val === opt ? 'white' : 'var(--text-secondary)', border: '1px solid var(--border-medium)',
                              borderRadius: 'var(--radius-full)', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)', transition: 'all 0.15s',
                            }}>{opt}</button>
                          ))}
                        </div>
                      ) : field.type === 'textarea' ? (
                        <textarea value={val} onChange={e => updateField(activeSection, field.key, e.target.value)}
                          rows={field.rows || 3} placeholder={ph}
                          style={{ ...inputStyle, resize: 'vertical', lineHeight: 1.5, minHeight: isMobile ? 88 : undefined }} />
                      ) : (
                        <input type={field.type || 'text'} value={val} onChange={e => updateField(activeSection, field.key, e.target.value)}
                          placeholder={ph} style={inputStyle} />
                      )}
                    </div>
                  );
                })}
              </div>
              {/* Desktop save button */}
              {!isMobile && (
                <div style={{ padding: '12px 18px', borderTop: '1px solid var(--border-light)', display: 'flex', justifyContent: 'flex-end' }}>
                  <button onClick={() => saveSection(activeSection)} disabled={saving} style={{
                    padding: '9px 20px', background: saved ? 'var(--status-success-text)' : 'var(--brand-primary)',
                    color: 'white', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600,
                    cursor: saving ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)', transition: 'background 0.2s',
                  }}>{saved ? '✓ Gespeichert' : saving ? 'Speichert...' : 'Abschnitt speichern'}</button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ── MOBILE: Back / Next navigation ── */}
      {isMobile && (
        <div style={{ display: 'flex', gap: 10 }}>
          <button
            onClick={handleMobileBack}
            disabled={currentMobileIndex === 0}
            style={{
              flex: 1, minHeight: 48, padding: '12px 16px',
              background: 'var(--bg-surface)', border: '1.5px solid var(--border-medium)',
              borderRadius: 'var(--radius-md)', fontSize: 14, fontWeight: 500,
              color: currentMobileIndex === 0 ? 'var(--text-tertiary)' : 'var(--text-primary)',
              cursor: currentMobileIndex === 0 ? 'not-allowed' : 'pointer',
              fontFamily: 'var(--font-sans)',
            }}
          >
            ← Zurück
          </button>
          <button
            onClick={handleMobileNext}
            disabled={saving}
            style={{
              flex: 2, minHeight: 48, padding: '12px 16px',
              background: saving ? 'var(--border-medium)' : 'var(--brand-primary)',
              border: 'none', borderRadius: 'var(--radius-md)', fontSize: 14, fontWeight: 700,
              color: saving ? 'var(--text-tertiary)' : 'white',
              cursor: saving ? 'not-allowed' : 'pointer',
              fontFamily: 'var(--font-sans)', transition: 'background 0.15s',
            }}
          >
            {saving ? 'Speichert…' : isLastMobileSection ? '✓ Fertig' : 'Weiter →'}
          </button>
        </div>
      )}
    </div>
  );
}
