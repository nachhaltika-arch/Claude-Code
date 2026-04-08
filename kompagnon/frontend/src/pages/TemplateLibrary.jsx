import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';
import { useAuth } from '../context/AuthContext';
import WebsiteDesigner from '../components/WebsiteDesigner';

const LS_KEY = 'kompagnon_deleted_local_tpl';

const LOCAL_TEMPLATES = [
  {
    id: 'local-1',
    name: 'Handwerker Klassik',
    category: 'Startseite',
    description: 'Sauberes Layout mit Hero, Leistungen und Kontakt',
    html: `<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, sans-serif; }
  .hero { background: #0d6efd; color: white; padding: 80px 40px; text-align: center; }
  .hero h1 { font-size: 2.5rem; margin-bottom: 16px; }
  .hero p { font-size: 1.2rem; opacity: 0.9; margin-bottom: 28px; }
  .btn { display: inline-block; background: white; color: #0d6efd; padding: 14px 32px; border-radius: 6px; text-decoration: none; font-weight: 600; }
  .services { padding: 60px 40px; background: #f8f9fa; }
  .services h2 { text-align: center; margin-bottom: 40px; font-size: 1.8rem; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; max-width: 1100px; margin: 0 auto; }
  .card { background: white; padding: 24px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
  .card h3 { margin-bottom: 10px; color: #0d6efd; }
  .contact { padding: 60px 40px; text-align: center; }
  .contact h2 { margin-bottom: 16px; }
</style></head><body>
<div class="hero">
  <h1>Ihr zuverlässiger Handwerksbetrieb</h1>
  <p>Qualität und Pünktlichkeit — seit über 20 Jahren</p>
  <a href="#kontakt" class="btn">Jetzt anfragen</a>
</div>
<div class="services">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><h3>Leistung 1</h3><p>Professionelle Ausführung mit jahrelanger Erfahrung.</p></div>
    <div class="card"><h3>Leistung 2</h3><p>Schnell, zuverlässig und zu fairen Preisen.</p></div>
    <div class="card"><h3>Leistung 3</h3><p>Qualitätsarbeit die überzeugt.</p></div>
  </div>
</div>
<div class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>Rufen Sie uns an oder schreiben Sie uns eine Nachricht.</p>
</div>
</body></html>`,
  },
  {
    id: 'local-2',
    name: 'Modern Dunkel',
    category: 'Startseite',
    description: 'Dunkles professionelles Design',
    html: `<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, sans-serif; background: #1a2332; color: #f0f4f5; }
  .hero { padding: 100px 40px; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.1); }
  .hero h1 { font-size: 3rem; margin-bottom: 20px; color: #40c4df; }
  .hero p { font-size: 1.2rem; opacity: 0.8; max-width: 600px; margin: 0 auto 32px; }
  .btn { background: #40c4df; color: #1a2332; padding: 14px 32px; border-radius: 6px; text-decoration: none; font-weight: 700; }
  .features { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; padding: 60px 40px; max-width: 1100px; margin: 0 auto; }
  .feature { background: rgba(255,255,255,0.05); padding: 32px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); }
  .feature h3 { color: #40c4df; margin-bottom: 12px; }
</style></head><body>
<div class="hero">
  <h1>Handwerk mit Niveau</h1>
  <p>Professionelle Lösungen für anspruchsvolle Kunden in Ihrer Region.</p>
  <a href="#" class="btn">Kostenlos beraten lassen</a>
</div>
<div class="features">
  <div class="feature"><h3>Erfahrung</h3><p>Über 15 Jahre Expertise in unserem Handwerk.</p></div>
  <div class="feature"><h3>Qualität</h3><p>Erstklassige Materialien und sorgfältige Arbeit.</p></div>
  <div class="feature"><h3>Service</h3><p>Schnelle Reaktionszeiten und faire Preise.</p></div>
</div>
</body></html>`,
  },
  {
    id: 'local-3',
    name: 'Leistungsseite',
    category: 'Leistungen',
    description: 'Detaillierte Leistungsdarstellung mit CTA',
    html: `<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, sans-serif; }
  .header { background: #0d6efd; color: white; padding: 60px 40px; }
  .header h1 { font-size: 2rem; margin-bottom: 10px; }
  .content { max-width: 900px; margin: 0 auto; padding: 60px 40px; }
  .benefit { display: flex; gap: 16px; margin-bottom: 24px; padding-bottom: 24px; border-bottom: 1px solid #eee; }
  .icon { width: 48px; height: 48px; background: #e6f1fb; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 24px; flex-shrink: 0; }
  .cta { background: #0d6efd; color: white; padding: 60px 40px; text-align: center; margin-top: 40px; border-radius: 10px; }
</style></head><body>
<div class="header"><h1>Unsere Leistung im Detail</h1><p>Was wir für Sie tun</p></div>
<div class="content">
  <div class="benefit"><div class="icon">✓</div><div><h3>Qualitätsgarantie</h3><p>Alle unsere Arbeiten werden mit Qualitätsgarantie ausgeführt.</p></div></div>
  <div class="benefit"><div class="icon">⚡</div><div><h3>Schnelle Ausführung</h3><p>Wir halten Deadlines ein und arbeiten effizient.</p></div></div>
  <div class="benefit"><div class="icon">💰</div><div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Gebühren.</p></div></div>
  <div class="cta"><h2>Bereit anzufangen?</h2><p style="margin:12px 0 24px">Kontaktieren Sie uns für ein kostenloses Erstgespräch.</p><a href="#" style="background:white;color:#0d6efd;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:600">Jetzt anfragen</a></div>
</div>
</body></html>`,
  },
  {
    id: 'local-4',
    name: 'Über uns',
    category: 'Über uns',
    description: 'Team und Geschichte',
    html: `<!DOCTYPE html><html><head><meta charset="UTF-8"><style>* { box-sizing: border-box; margin: 0; padding: 0; } body { font-family: -apple-system, sans-serif; } .hero { background: #1a2332; color: white; padding: 80px 40px; text-align: center; } .hero h1 { font-size: 2.5rem; margin-bottom: 16px; } .content { max-width: 800px; margin: 0 auto; padding: 60px 40px; } .content p { font-size: 1.1rem; line-height: 1.8; color: #555; margin-bottom: 20px; } .stats { display: grid; grid-template-columns: repeat(3,1fr); gap: 20px; margin: 40px 0; } .stat { text-align: center; padding: 24px; background: #f8f9fa; border-radius: 8px; } .stat .number { font-size: 2.5rem; font-weight: 700; color: #0d6efd; }</style></head><body><div class="hero"><h1>Über uns</h1><p>Lernen Sie uns kennen</p></div><div class="content"><p>Wir sind ein familiengeführter Handwerksbetrieb mit langer Tradition und modernem Anspruch. Seit unserer Gründung stehen wir für Qualität, Verlässlichkeit und persönlichen Service.</p><div class="stats"><div class="stat"><div class="number">20+</div><div>Jahre Erfahrung</div></div><div class="stat"><div class="number">500+</div><div>Zufriedene Kunden</div></div><div class="stat"><div class="number">100%</div><div>Qualitätsgarantie</div></div></div><p>Unser Team besteht aus erfahrenen Fachleuten, die ihr Handwerk mit Leidenschaft betreiben.</p></div></body></html>`,
  },
  {
    id: 'local-5',
    name: 'Kontaktseite',
    category: 'Kontakt',
    description: 'Kontaktformular und Infos',
    html: `<!DOCTYPE html><html><head><meta charset="UTF-8"><style>* { box-sizing: border-box; margin: 0; padding: 0; } body { font-family: -apple-system, sans-serif; } .hero { background: #059669; color: white; padding: 60px 40px; text-align: center; } .content { display: grid; grid-template-columns: 1fr 1fr; gap: 40px; max-width: 1000px; margin: 0 auto; padding: 60px 40px; } .info h2 { margin-bottom: 20px; } .info-item { display: flex; gap: 12px; margin-bottom: 16px; } .form input, .form textarea { width: 100%; padding: 10px 14px; border: 1px solid #ddd; border-radius: 6px; font-family: inherit; margin-bottom: 12px; } .form button { background: #059669; color: white; border: none; padding: 12px 28px; border-radius: 6px; cursor: pointer; font-size: 15px; }</style></head><body><div class="hero"><h1>Kontakt aufnehmen</h1><p>Wir freuen uns auf Ihre Anfrage</p></div><div class="content"><div class="info"><h2>So erreichen Sie uns</h2><div class="info-item"><span>📞</span><div><strong>Telefon</strong><br>+49 XXX XXXXXXX</div></div><div class="info-item"><span>✉️</span><div><strong>E-Mail</strong><br>info@beispiel.de</div></div><div class="info-item"><span>📍</span><div><strong>Adresse</strong><br>Musterstraße 1, 12345 Musterstadt</div></div></div><div class="form"><h2>Nachricht senden</h2><input placeholder="Ihr Name"><input placeholder="Ihre E-Mail"><textarea rows="5" placeholder="Ihre Nachricht"></textarea><button>Absenden</button></div></div></body></html>`,
  },
  {
    id: 'local-6',
    name: 'Referenzen',
    category: 'Referenzen',
    description: 'Kundenprojekte und Bewertungen',
    html: `<!DOCTYPE html><html><head><meta charset="UTF-8"><style>* { box-sizing: border-box; margin: 0; padding: 0; } body { font-family: -apple-system, sans-serif; } .hero { background: #7c3aed; color: white; padding: 60px 40px; text-align: center; } .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px,1fr)); gap: 24px; max-width: 1100px; margin: 0 auto; padding: 60px 40px; } .card { border: 1px solid #eee; border-radius: 10px; overflow: hidden; } .card-img { height: 180px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center; color: white; font-size: 2rem; } .card-body { padding: 20px; } .stars { color: #f59e0b; margin-bottom: 8px; } .quote { font-style: italic; color: #555; line-height: 1.6; }</style></head><body><div class="hero"><h1>Unsere Referenzen</h1><p>Was unsere Kunden sagen</p></div><div class="grid"><div class="card"><div class="card-img">⭐</div><div class="card-body"><div class="stars">★★★★★</div><div class="quote">"Hervorragende Arbeit, pünktlich und professionell. Sehr empfehlenswert!"</div><strong style="display:block;margin-top:12px">— Max Mustermann</strong></div></div><div class="card"><div class="card-img">🏆</div><div class="card-body"><div class="stars">★★★★★</div><div class="quote">"Qualität überzeugt. Wir sind sehr zufrieden mit dem Ergebnis."</div><strong style="display:block;margin-top:12px">— Anna Beispiel</strong></div></div></div></body></html>`,
  },
  {
    id: 'local-7',
    name: 'Landing Page Minimal',
    category: 'Startseite',
    description: 'Minimalistisches Design mit starkem CTA',
    html: `<!DOCTYPE html><html><head><meta charset="UTF-8"><style>* { box-sizing: border-box; margin: 0; padding: 0; } body { font-family: -apple-system, sans-serif; min-height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; padding: 40px; background: #f8f9fa; } h1 { font-size: 3rem; font-weight: 800; color: #1a2332; margin-bottom: 20px; } p { font-size: 1.3rem; color: #555; max-width: 600px; line-height: 1.7; margin-bottom: 40px; } .btn-group { display: flex; gap: 16px; justify-content: center; } .btn-primary { background: #0d6efd; color: white; padding: 16px 40px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 1.1rem; } .btn-secondary { border: 2px solid #0d6efd; color: #0d6efd; padding: 16px 40px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 1.1rem; } .badge { background: #dcfce7; color: #166534; padding: 6px 16px; border-radius: 99px; font-size: 14px; margin-bottom: 24px; display: inline-block; }</style></head><body><span class="badge">✓ Fertig in 14 Tagen</span><h1>Ihre neue Website.<br>Fertig in 2 Wochen.</h1><p>Professionelle Website für Ihren Handwerksbetrieb. Festpreis, keine Überraschungen.</p><div class="btn-group"><a href="#" class="btn-primary">Jetzt starten</a><a href="#" class="btn-secondary">Mehr erfahren</a></div></body></html>`,
  },
  {
    id: 'local-8',
    name: 'FAQ Seite',
    category: 'FAQ',
    description: 'Häufige Fragen mit Akkordeon-Stil',
    html: `<!DOCTYPE html><html><head><meta charset="UTF-8"><style>* { box-sizing: border-box; margin: 0; padding: 0; } body { font-family: -apple-system, sans-serif; } .hero { background: #0d6efd; color: white; padding: 60px 40px; text-align: center; } .content { max-width: 800px; margin: 0 auto; padding: 60px 40px; } .faq-item { border-bottom: 1px solid #eee; padding: 24px 0; } .faq-item h3 { font-size: 1.1rem; color: #1a2332; margin-bottom: 12px; display: flex; justify-content: space-between; } .faq-item p { color: #555; line-height: 1.7; }</style></head><body><div class="hero"><h1>Häufige Fragen</h1><p>Alles was Sie wissen müssen</p></div><div class="content"><div class="faq-item"><h3>Was kostet eine Website? <span>+</span></h3><p>Unsere Websites beginnen bei einem transparenten Festpreis. Im Erstgespräch klären wir Ihren genauen Bedarf.</p></div><div class="faq-item"><h3>Wie lange dauert die Erstellung? <span>+</span></h3><p>In der Regel 14 Werktage nach dem Briefing. Wir halten diesen Zeitplan zuverlässig ein.</p></div><div class="faq-item"><h3>Was muss ich selbst tun? <span>+</span></h3><p>Fast nichts. Sie beantworten einige Fragen zu Ihrem Betrieb, den Rest übernehmen wir komplett.</p></div><div class="faq-item"><h3>Kann ich die Website selbst bearbeiten? <span>+</span></h3><p>Ja. Wir übergeben die Website so, dass Sie einfache Änderungen selbst vornehmen können.</p></div></div></body></html>`,
  },
];

const CATEGORY_COLORS = {
  'Startseite': { bg: '#e7f1ff', color: '#0d6efd' },
  'Leistungen': { bg: '#fff3cd', color: '#856404' },
  'Über uns':   { bg: '#d1e7dd', color: '#0f5132' },
  'Kontakt':    { bg: '#d1f5ea', color: '#087850' },
  'Referenzen': { bg: '#ede9fe', color: '#5b21b6' },
  'FAQ':        { bg: '#fce7f3', color: '#9d174d' },
};

export default function TemplateLibrary() {
  const { token } = useAuth();
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const [apiTemplates, setApiTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showZipModal, setShowZipModal] = useState(false);
  const [showUrlModal, setShowUrlModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [zipForm, setZipForm] = useState({ name: '', description: '' });
  const [urlForm, setUrlForm] = useState({ name: '', url: '', description: '' });
  const [activeTab, setActiveTab] = useState('all');
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [deletedLocal, setDeletedLocal] = useState(
    () => new Set(JSON.parse(localStorage.getItem(LS_KEY) || '[]'))
  );
  const fileRef = useRef(null);

  const visibleLocalTemplates = LOCAL_TEMPLATES.filter(t => !deletedLocal.has(t.id));

  const deleteLocalTemplate = (id, name) => {
    if (!window.confirm(`Lokale Vorlage "${name}" wirklich entfernen?`)) return;
    const next = new Set(deletedLocal);
    next.add(id);
    setDeletedLocal(next);
    localStorage.setItem(LS_KEY, JSON.stringify([...next]));
    toast.success('Vorlage entfernt');
  };

  const load = async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API_BASE_URL}/api/templates/`, { headers });
      setApiTemplates(r.ok ? await r.json() : []);
    } catch { setApiTemplates([]); }
    setLoading(false);
  };

  useEffect(() => { load(); }, []); // eslint-disable-line

  const handleZipUpload = async () => {
    const file = fileRef.current?.files?.[0];
    if (!zipForm.name || !file) return toast.error('Name und ZIP-Datei sind Pflicht');
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('name', zipForm.name);
      fd.append('description', zipForm.description);
      const r = await fetch(`${API_BASE_URL}/api/templates/upload`, { method: 'POST', headers, body: fd });
      if (!r.ok) throw new Error((await r.json()).detail || 'Fehler');
      toast.success('Template hochgeladen');
      setShowZipModal(false);
      setZipForm({ name: '', description: '' });
      load();
    } catch (e) { toast.error(e.message); }
    setUploading(false);
  };

  const handleUrlImport = async () => {
    if (!urlForm.name || !urlForm.url) return toast.error('Name und URL sind Pflicht');
    setUploading(true);
    try {
      const r = await fetch(`${API_BASE_URL}/api/templates/import-url`, {
        method: 'POST',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify(urlForm),
      });
      if (!r.ok) throw new Error((await r.json()).detail || 'Fehler');
      toast.success('Template importiert');
      setShowUrlModal(false);
      setUrlForm({ name: '', url: '', description: '' });
      load();
    } catch (e) { toast.error(e.message); }
    setUploading(false);
  };

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Template "${name}" wirklich löschen?`)) return;
    try {
      await fetch(`${API_BASE_URL}/api/templates/${id}`, { method: 'DELETE', headers });
      toast.success('Gelöscht');
      load();
    } catch { toast.error('Fehler beim Löschen'); }
  };

  if (editingTemplate) {
    return (
      <WebsiteDesigner
        initialHtml={editingTemplate.html || ''}
        initialCss={editingTemplate.css || ''}
        onSave={() => setEditingTemplate(null)}
      />
    );
  }

  const inp = { padding: '10px 14px', border: '1px solid #ddd', borderRadius: 6, fontSize: 14, width: '100%', boxSizing: 'border-box' };
  const overlay = { position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center' };
  const modal = { background: '#fff', borderRadius: 12, padding: 28, width: '100%', maxWidth: 480, display: 'flex', flexDirection: 'column', gap: 16 };

  const tabs = [
    { key: 'all',   label: `Alle (${visibleLocalTemplates.length + apiTemplates.length})` },
    { key: 'local', label: `Lokale Vorlagen (${visibleLocalTemplates.length})` },
    { key: 'saved', label: `Gespeichert (${apiTemplates.length})` },
  ];

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700 }}>🗂️ Template-Bibliothek</h1>
        <div style={{ display: 'flex', gap: 10 }}>
          <button onClick={() => setShowZipModal(true)} style={{ padding: '9px 18px', background: '#0d6efd', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 600, cursor: 'pointer' }}>
            📁 ZIP hochladen
          </button>
          <button onClick={() => setShowUrlModal(true)} style={{ padding: '9px 18px', background: '#6c757d', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 600, cursor: 'pointer' }}>
            🌐 URL importieren
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '2px solid #e0e0e0', marginBottom: 28 }}>
        {tabs.map(tab => (
          <button key={tab.key} onClick={() => setActiveTab(tab.key)} style={{
            padding: '10px 22px', border: 'none', background: 'transparent', cursor: 'pointer',
            fontWeight: 600, fontSize: 14,
            color: activeTab === tab.key ? '#0d6efd' : '#666',
            borderBottom: activeTab === tab.key ? '2px solid #0d6efd' : '2px solid transparent',
            marginBottom: -2,
          }}>
            {tab.label}
          </button>
        ))}
      </div>

      {/* LOCAL TEMPLATES (shown in 'all' and 'local' tabs) */}
      {(activeTab === 'all' || activeTab === 'local') && (
        <>
          {activeTab === 'all' && (
            <h2 style={{ fontSize: 16, fontWeight: 700, color: '#555', marginBottom: 16, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Lokale Vorlagen
            </h2>
          )}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 18, marginBottom: activeTab === 'all' ? 36 : 0 }}>
            {visibleLocalTemplates.map(tpl => {
              const badge = CATEGORY_COLORS[tpl.category] || { bg: '#f0f0f0', color: '#555' };
              return (
                <div key={tpl.id} style={{ border: '1px solid #e0e0e0', borderRadius: 12, background: '#fff', boxShadow: '0 1px 4px rgba(0,0,0,0.06)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                  {/* Color stripe */}
                  <div style={{ height: 6, background: badge.color, opacity: 0.7 }} />
                  <div style={{ padding: '18px 20px', flex: 1, display: 'flex', flexDirection: 'column', gap: 10 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div style={{ fontWeight: 700, fontSize: 15, color: '#1a2332' }}>{tpl.name}</div>
                      <span style={{ fontSize: 11, padding: '3px 10px', borderRadius: 12, background: badge.bg, color: badge.color, fontWeight: 600, flexShrink: 0, marginLeft: 8 }}>
                        {tpl.category}
                      </span>
                    </div>
                    <p style={{ fontSize: 13, color: '#666', lineHeight: 1.5, flex: 1 }}>{tpl.description}</p>
                    <div style={{ display: 'flex', gap: 8, marginTop: 'auto' }}>
                      <button
                        onClick={() => setEditingTemplate(tpl)}
                        style={{ flex: 1, padding: '9px 14px', background: '#008eaa', color: '#fff', border: 'none', borderRadius: 8, cursor: 'pointer', fontWeight: 700, fontSize: 13 }}
                      >
                        ✏️ Im Website-Builder bearbeiten
                      </button>
                      <button
                        onClick={() => deleteLocalTemplate(tpl.id, tpl.name)}
                        style={{ padding: '9px 12px', background: '#fee2e2', color: '#b91c1c', border: 'none', borderRadius: 8, cursor: 'pointer', fontWeight: 700, fontSize: 13 }}
                        title="Vorlage entfernen"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}

      {/* API / SAVED TEMPLATES (shown in 'all' and 'saved' tabs) */}
      {(activeTab === 'all' || activeTab === 'saved') && (
        <>
          {activeTab === 'all' && (
            <h2 style={{ fontSize: 16, fontWeight: 700, color: '#555', marginBottom: 16, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Gespeicherte Templates
            </h2>
          )}
          {loading ? (
            <div style={{ textAlign: 'center', padding: 40, color: '#888' }}>Lade Templates...</div>
          ) : apiTemplates.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 48, color: '#888', background: '#f8f9fa', borderRadius: 12, border: '1px dashed #dee2e6' }}>
              <div style={{ fontSize: 40, marginBottom: 10 }}>🗂️</div>
              <div style={{ fontWeight: 600, marginBottom: 6 }}>Noch keine gespeicherten Templates</div>
              <div style={{ fontSize: 13 }}>Lade ein ZIP hoch oder importiere eine URL.</div>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 18 }}>
              {apiTemplates.map(tpl => (
                <div key={tpl.id} style={{ border: '1px solid #e0e0e0', borderRadius: 12, padding: 20, background: '#fff', boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                    <div style={{ fontWeight: 700, fontSize: 15 }}>{tpl.name}</div>
                    <span style={{ fontSize: 11, padding: '3px 9px', borderRadius: 10, background: tpl.source === 'url' ? '#e3f2fd' : '#e8f5e9', color: tpl.source === 'url' ? '#1565c0' : '#2e7d32', fontWeight: 600 }}>
                      {tpl.source === 'url' ? '🌐 URL' : '📁 ZIP'}
                    </span>
                  </div>
                  {tpl.category && <div style={{ fontSize: 12, color: '#888', marginBottom: 6 }}>{tpl.category}</div>}
                  {tpl.created_at && <div style={{ fontSize: 11, color: '#aaa', marginBottom: 14 }}>{new Date(tpl.created_at).toLocaleDateString('de-DE')}</div>}
                  <div style={{ display: 'flex', gap: 8 }}>
                    <Link to={`/app/settings/templates/${tpl.id}`} style={{ flex: 1, padding: '8px 12px', background: '#f0f0f0', color: '#333', border: 'none', borderRadius: 6, fontWeight: 600, fontSize: 13, textAlign: 'center', textDecoration: 'none', display: 'block' }}>
                      ✏️ Bearbeiten
                    </Link>
                    <button onClick={() => handleDelete(tpl.id, tpl.name)} style={{ padding: '8px 12px', background: '#fee2e2', color: '#b91c1c', border: 'none', borderRadius: 6, fontWeight: 600, fontSize: 13, cursor: 'pointer' }}>
                      🗑️
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* ZIP Modal */}
      {showZipModal && (
        <div style={overlay} onClick={e => e.target === e.currentTarget && setShowZipModal(false)}>
          <div style={modal}>
            <div style={{ fontWeight: 700, fontSize: 17 }}>📁 ZIP-Template hochladen</div>
            <input style={inp} placeholder="Template-Name *" value={zipForm.name} onChange={e => setZipForm(f => ({ ...f, name: e.target.value }))} />
            <input style={inp} placeholder="Beschreibung (optional)" value={zipForm.description} onChange={e => setZipForm(f => ({ ...f, description: e.target.value }))} />
            <input ref={fileRef} type="file" accept=".zip" style={inp} />
            <button onClick={handleZipUpload} disabled={uploading} style={{ padding: '11px', background: uploading ? '#ccc' : '#0d6efd', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, fontSize: 15, cursor: uploading ? 'not-allowed' : 'pointer' }}>
              {uploading ? 'Wird hochgeladen...' : 'Hochladen'}
            </button>
            <button onClick={() => setShowZipModal(false)} style={{ padding: '9px', background: '#f5f5f5', color: '#555', border: 'none', borderRadius: 8, cursor: 'pointer' }}>Abbrechen</button>
          </div>
        </div>
      )}

      {/* URL Modal */}
      {showUrlModal && (
        <div style={overlay} onClick={e => e.target === e.currentTarget && setShowUrlModal(false)}>
          <div style={modal}>
            <div style={{ fontWeight: 700, fontSize: 17 }}>🌐 Template per URL importieren</div>
            <input style={inp} placeholder="Template-Name *" value={urlForm.name} onChange={e => setUrlForm(f => ({ ...f, name: e.target.value }))} />
            <input style={inp} placeholder="URL (z.B. https://...) *" value={urlForm.url} onChange={e => setUrlForm(f => ({ ...f, url: e.target.value }))} />
            <input style={inp} placeholder="Beschreibung (optional)" value={urlForm.description} onChange={e => setUrlForm(f => ({ ...f, description: e.target.value }))} />
            <div style={{ background: '#fef3c7', border: '1px solid #fbbf24', borderRadius: 8, padding: '10px 14px', fontSize: 13, color: '#92400e' }}>
              ⚠️ Gib die öffentliche Demo-URL des Templates ein. Die KI rekonstruiert das Layout. Stelle sicher dass du eine Lizenz besitzt.
            </div>
            <button onClick={handleUrlImport} disabled={uploading} style={{ padding: '11px', background: uploading ? '#ccc' : '#6f42c1', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, fontSize: 15, cursor: uploading ? 'not-allowed' : 'pointer' }}>
              {uploading ? 'KI rekonstruiert (~10 Sek)...' : 'Importieren'}
            </button>
            <button onClick={() => setShowUrlModal(false)} style={{ padding: '9px', background: '#f5f5f5', color: '#555', border: 'none', borderRadius: 8, cursor: 'pointer' }}>Abbrechen</button>
          </div>
        </div>
      )}
    </div>
  );
}
