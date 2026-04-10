import { useState } from 'react';
import API_BASE_URL from '../config';

const STILRICHTUNGEN = [
  { id: 'modern-minimalistisch', label: 'Modern & Minimalistisch', desc: 'Viel Weißraum, klare Linien, reduzierte Farben', emoji: '⬜' },
  { id: 'handwerklich-warm',     label: 'Handwerklich & Warm',     desc: 'Erdtöne, Holz-Optik, authentisch, bodenständig', emoji: '🪵' },
  { id: 'professionell-serioes', label: 'Professionell & Seriös',  desc: 'Dunkelblau/Grau, klar strukturiert, vertrauenswürdig', emoji: '🔵' },
  { id: 'frisch-modern',         label: 'Frisch & Modern',         desc: 'Kräftige Farben, dynamisch, energiegeladen', emoji: '🟢' },
  { id: 'premium-exklusiv',      label: 'Premium & Exklusiv',      desc: 'Schwarz/Gold, hochwertig, anspruchsvoll', emoji: '🖤' },
  { id: 'regional-traditionell', label: 'Regional & Traditionell', desc: 'Heimatstil, klassisch, familiär', emoji: '🏘️' },
];

const FARBSTIMMUNGEN = [
  { id: 'blau',    label: 'Blau-Töne',    hex: ['#1e3a5f','#2563eb','#bfdbfe'], desc: 'Vertrauen, Kompetenz' },
  { id: 'gruen',   label: 'Grün-Töne',    hex: ['#14532d','#16a34a','#bbf7d0'], desc: 'Natur, Wachstum' },
  { id: 'orange',  label: 'Orange-Töne',  hex: ['#7c2d12','#ea580c','#fed7aa'], desc: 'Energie, Handwerk' },
  { id: 'grau',    label: 'Grau-Töne',    hex: ['#1f2937','#6b7280','#f3f4f6'], desc: 'Neutral, Professionalität' },
  { id: 'rot',     label: 'Rot-Töne',     hex: ['#7f1d1d','#dc2626','#fecaca'], desc: 'Stärke, Leidenschaft' },
  { id: 'custom',  label: 'Eigene Farben', hex: [], desc: 'Aus Brand-Design übernehmen' },
];

const TYPOGRAFIE = [
  { id: 'sans-modern',   label: 'Modern Sans-Serif',   example: 'Inter, Nunito, Outfit', desc: 'Zeitgemäß, gut lesbar' },
  { id: 'serif-klassisch', label: 'Klassische Serif',   example: 'Playfair, Lora',         desc: 'Traditionell, Vertrauen' },
  { id: 'handwerk',      label: 'Handwerk-Schriften',  example: 'Oswald, Raleway Bold',   desc: 'Kraftvoll, markant' },
  { id: 'regional',      label: 'Regional & Freundlich', example: 'Poppins, Quicksand',  desc: 'Sympathisch, nahbar' },
];

const BILDSPRACHE = [
  { id: 'team-echte-fotos',   label: 'Echte Team-Fotos',      icon: '👷', desc: 'Mitarbeiter und Betrieb authentisch zeigen' },
  { id: 'arbeit-in-aktion',   label: 'Arbeit in Aktion',      icon: '🔧', desc: 'Bei der Arbeit, Handwerk zeigen' },
  { id: 'vorher-nachher',     label: 'Vorher/Nachher',         icon: '🔄', desc: 'Ergebnisse demonstrieren' },
  { id: 'material-nahaufnahme', label: 'Material-Nahaufnahmen', icon: '🪨', desc: 'Qualität und Details zeigen' },
  { id: 'stockfotos',         label: 'Stock-Fotos (Platzhalter)', icon: '🖼️', desc: 'Solange keine eigenen Fotos vorhanden' },
];

export default function MoodboardPanel({ projectId, leadId, token }) {
  const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };

  const [stilrichtung, setStilrichtung] = useState(null);
  const [farbstimmung, setFarbstimmung] = useState(null);
  const [typografie, setTypografie]     = useState(null);
  const [bildsprache, setBildsprache]   = useState([]);
  const [notizen, setNotizen]           = useState('');
  const [referenzUrls, setReferenzUrls] = useState('');
  const [saving, setSaving]             = useState(false);
  const [saved, setSaved]               = useState(false);
  const [generating, setGenerating]     = useState(false);
  const [preview, setPreview]           = useState(null);

  const toggleBildsprache = (id) => {
    setBildsprache(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const saveMoodboard = async () => {
    setSaving(true);
    try {
      await fetch(`${API_BASE_URL}/api/projects/${projectId}/moodboard`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          stilrichtung,
          farbstimmung,
          typografie,
          bildsprache,
          notizen,
          referenz_urls: referenzUrls,
        }),
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  const generatePreview = async () => {
    if (!stilrichtung || !farbstimmung) {
      alert('Bitte Stilrichtung und Farbstimmung auswählen.');
      return;
    }
    setGenerating(true);
    setPreview(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/projects/${projectId}/moodboard/preview`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ stilrichtung, farbstimmung, typografie, bildsprache, notizen }),
      });
      if (res.ok) {
        const data = await res.json();
        setPreview(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setGenerating(false);
    }
  };

  const Card = ({ children, style }) => (
    <div style={{
      background: 'var(--bg-surface)', border: '0.5px solid var(--border-light)',
      borderRadius: 12, padding: '20px 22px', ...style,
    }}>
      {children}
    </div>
  );

  const SectionTitle = ({ children }) => (
    <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.08em', color: 'var(--text-tertiary)', marginBottom: 14 }}>
      {children}
    </div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>
            Moodboard — Stilrichtung festlegen
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6, maxWidth: 560 }}>
            Definiere die visuelle Richtung der Website bevor Design und Content erstellt werden.
            Alles hier wird als Grundlage für die KI-Texterstellung und den Designer genutzt.
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button
            onClick={generatePreview}
            disabled={generating}
            style={{
              padding: '9px 18px', borderRadius: 8, border: '1px solid var(--border-light)',
              background: 'var(--bg-surface)', color: 'var(--text-primary)',
              fontSize: 12, fontWeight: 600, cursor: generating ? 'not-allowed' : 'pointer',
              fontFamily: 'inherit',
            }}
          >
            {generating ? '⏳ Generiert…' : 'Vorschau generieren'}
          </button>
          <button
            onClick={saveMoodboard}
            disabled={saving}
            style={{
              padding: '9px 18px', borderRadius: 8, border: 'none',
              background: saved ? '#16a34a' : '#008eaa',
              color: 'white', fontSize: 12, fontWeight: 700,
              cursor: saving ? 'not-allowed' : 'pointer',
              fontFamily: 'inherit',
            }}
          >
            {saved ? '✓ Gespeichert' : saving ? '…' : 'Moodboard speichern'}
          </button>
        </div>
      </div>

      {/* 1. Stilrichtung */}
      <Card>
        <SectionTitle>1. Stilrichtung</SectionTitle>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 10 }}>
          {STILRICHTUNGEN.map(s => (
            <button
              key={s.id}
              onClick={() => setStilrichtung(stilrichtung === s.id ? null : s.id)}
              style={{
                padding: '14px 16px', borderRadius: 10, border: 'none', textAlign: 'left',
                background: stilrichtung === s.id ? '#e0f2fe' : 'var(--bg-app)',
                outline: stilrichtung === s.id ? '2px solid #008eaa' : 'none',
                cursor: 'pointer', transition: 'all 0.15s', fontFamily: 'inherit',
              }}
            >
              <div style={{ fontSize: 22, marginBottom: 6 }}>{s.emoji}</div>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 3 }}>{s.label}</div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)', lineHeight: 1.5 }}>{s.desc}</div>
            </button>
          ))}
        </div>
      </Card>

      {/* 2. Farbstimmung */}
      <Card>
        <SectionTitle>2. Farbstimmung</SectionTitle>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 10 }}>
          {FARBSTIMMUNGEN.map(f => (
            <button
              key={f.id}
              onClick={() => setFarbstimmung(farbstimmung === f.id ? null : f.id)}
              style={{
                padding: '14px 16px', borderRadius: 10, border: 'none', textAlign: 'left',
                background: farbstimmung === f.id ? '#e0f2fe' : 'var(--bg-app)',
                outline: farbstimmung === f.id ? '2px solid #008eaa' : 'none',
                cursor: 'pointer', transition: 'all 0.15s', fontFamily: 'inherit',
              }}
            >
              {f.hex.length > 0 ? (
                <div style={{ display: 'flex', gap: 4, marginBottom: 8 }}>
                  {f.hex.map((hex, i) => (
                    <div key={i} style={{ width: 28, height: 28, borderRadius: 6, background: hex, border: '1px solid rgba(0,0,0,0.08)' }} />
                  ))}
                </div>
              ) : (
                <div style={{ fontSize: 22, marginBottom: 6 }}>🎨</div>
              )}
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>{f.label}</div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{f.desc}</div>
            </button>
          ))}
        </div>
      </Card>

      {/* 3. Typografie */}
      <Card>
        <SectionTitle>3. Typografie</SectionTitle>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 10 }}>
          {TYPOGRAFIE.map(t => (
            <button
              key={t.id}
              onClick={() => setTypografie(typografie === t.id ? null : t.id)}
              style={{
                padding: '14px 16px', borderRadius: 10, border: 'none', textAlign: 'left',
                background: typografie === t.id ? '#e0f2fe' : 'var(--bg-app)',
                outline: typografie === t.id ? '2px solid #008eaa' : 'none',
                cursor: 'pointer', transition: 'all 0.15s', fontFamily: 'inherit',
              }}
            >
              <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 3 }}>{t.label}</div>
              <div style={{ fontSize: 11, color: '#008eaa', marginBottom: 4, fontStyle: 'italic' }}>{t.example}</div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{t.desc}</div>
            </button>
          ))}
        </div>
      </Card>

      {/* 4. Bildsprache */}
      <Card>
        <SectionTitle>4. Bildsprache (Mehrfachauswahl)</SectionTitle>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 10 }}>
          {BILDSPRACHE.map(b => (
            <button
              key={b.id}
              onClick={() => toggleBildsprache(b.id)}
              style={{
                padding: '14px 16px', borderRadius: 10, border: 'none', textAlign: 'left',
                background: bildsprache.includes(b.id) ? '#e0f2fe' : 'var(--bg-app)',
                outline: bildsprache.includes(b.id) ? '2px solid #008eaa' : 'none',
                cursor: 'pointer', transition: 'all 0.15s', fontFamily: 'inherit',
              }}
            >
              <div style={{ fontSize: 22, marginBottom: 6 }}>{b.icon}</div>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 3 }}>{b.label}</div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)', lineHeight: 1.5 }}>{b.desc}</div>
            </button>
          ))}
        </div>
      </Card>

      {/* 5. Referenz-Websites + Notizen */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <Card>
          <SectionTitle>5. Referenz-Websites (optional)</SectionTitle>
          <textarea
            value={referenzUrls}
            onChange={e => setReferenzUrls(e.target.value)}
            placeholder={'https://beispiel.de\nhttps://weitereseite.com'}
            rows={4}
            style={{
              width: '100%', padding: '10px 12px', borderRadius: 8,
              border: '1px solid var(--border-light)', fontSize: 13,
              fontFamily: 'monospace', color: 'var(--text-primary)',
              background: 'var(--bg-app)', resize: 'vertical', boxSizing: 'border-box',
            }}
          />
          <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 6 }}>
            Eine URL pro Zeile. Diese Websites dienen als Inspiration für das Design.
          </div>
        </Card>
        <Card>
          <SectionTitle>6. Notizen & Besondere Wünsche</SectionTitle>
          <textarea
            value={notizen}
            onChange={e => setNotizen(e.target.value)}
            placeholder={'z.B. „Bitte keine runden Ecken", „Logo muss prominent sein", „Kunden sind Senioren → große Schrift"'}
            rows={4}
            style={{
              width: '100%', padding: '10px 12px', borderRadius: 8,
              border: '1px solid var(--border-light)', fontSize: 13,
              fontFamily: 'inherit', color: 'var(--text-primary)',
              background: 'var(--bg-app)', resize: 'vertical', boxSizing: 'border-box',
            }}
          />
        </Card>
      </div>

      {/* Zusammenfassung */}
      {(stilrichtung || farbstimmung || typografie || bildsprache.length > 0) && (
        <Card style={{ background: '#f0f9ff', border: '1px solid #bae6fd' }}>
          <SectionTitle>Gewählte Stilrichtung — Zusammenfassung</SectionTitle>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {stilrichtung && (
              <span style={{ padding: '4px 12px', background: '#008eaa', color: 'white', borderRadius: 20, fontSize: 12, fontWeight: 600 }}>
                {STILRICHTUNGEN.find(s => s.id === stilrichtung)?.emoji} {STILRICHTUNGEN.find(s => s.id === stilrichtung)?.label}
              </span>
            )}
            {farbstimmung && (
              <span style={{ padding: '4px 12px', background: '#0369a1', color: 'white', borderRadius: 20, fontSize: 12, fontWeight: 600 }}>
                {FARBSTIMMUNGEN.find(f => f.id === farbstimmung)?.label}
              </span>
            )}
            {typografie && (
              <span style={{ padding: '4px 12px', background: '#0c4a6e', color: 'white', borderRadius: 20, fontSize: 12, fontWeight: 600 }}>
                Aa {TYPOGRAFIE.find(t => t.id === typografie)?.label}
              </span>
            )}
            {bildsprache.map(b => (
              <span key={b} style={{ padding: '4px 12px', background: '#075985', color: 'white', borderRadius: 20, fontSize: 12, fontWeight: 600 }}>
                {BILDSPRACHE.find(x => x.id === b)?.icon} {BILDSPRACHE.find(x => x.id === b)?.label}
              </span>
            ))}
          </div>
        </Card>
      )}

      {/* KI-generierte Vorschau */}
      {preview && (
        <Card>
          <SectionTitle>KI-Moodboard Vorschau</SectionTitle>
          <div style={{ fontSize: 14, color: 'var(--text-primary)', lineHeight: 1.75, whiteSpace: 'pre-wrap' }}>
            {preview.description}
          </div>
          {preview.color_palette && (
            <div style={{ marginTop: 14 }}>
              <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.06em', color: 'var(--text-tertiary)', marginBottom: 8 }}>Empfohlene Farbpalette</div>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                {preview.color_palette.map((c, i) => (
                  <div key={i} style={{ textAlign: 'center' }}>
                    <div style={{ width: 52, height: 52, borderRadius: 10, background: c.hex, border: '1px solid rgba(0,0,0,0.1)', marginBottom: 4 }} />
                    <div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{c.hex}</div>
                    <div style={{ fontSize: 10, color: 'var(--text-secondary)', fontWeight: 600 }}>{c.role}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
