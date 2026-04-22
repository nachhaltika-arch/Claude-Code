import { useState, useEffect, useCallback } from 'react';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';

export default function BrandGuideline({ leadId, token, brandData }) {
  const [guideline,    setGuideline]    = useState(null);
  const [loading,      setLoading]      = useState(true);
  const [generating,   setGenerating]   = useState(false);
  const [savedAt,      setSavedAt]      = useState(null);
  const [editedColors, setEditedColors] = useState({});

  const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };

  const load = useCallback(async () => {
    if (!leadId) return;
    setLoading(true);
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/branddesign/${leadId}/guideline`,
        { headers }
      );
      if (res.ok) {
        const d = await res.json();
        if (d.generated && d.guideline) {
          setGuideline(d.guideline);
          if (d.generated_at) setSavedAt(new Date(d.generated_at));
        }
      }
    } catch { /* silent */ }
    finally { setLoading(false); }
  }, [leadId]); // eslint-disable-line

  useEffect(() => { load(); }, [load]);

  const generate = async () => {
    setGenerating(true);
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/branddesign/${leadId}/guideline/generate`,
        { method: 'POST', headers }
      );
      if (!res.ok) throw new Error((await res.json()).detail || 'Fehler');
      const d = await res.json();
      setGuideline(d.guideline);
      setEditedColors({});
      setSavedAt(new Date());
      toast.success('Brand Guideline gespeichert ✓');
    } catch (e) {
      toast.error(e.message || 'Generierung fehlgeschlagen');
    } finally {
      setGenerating(false);
    }
  };

  const saveEdits = async () => {
    const updated = {
      ...guideline,
      colors: { ...guideline.colors, ...editedColors },
    };
    try {
      await fetch(`${API_BASE_URL}/api/branddesign/${leadId}/guideline`, {
        method: 'PUT',
        headers,
        body: JSON.stringify({ guideline: updated }),
      });
      setGuideline(updated);
      setEditedColors({});
      setSavedAt(new Date());
      toast.success('Änderungen gespeichert ✓');
    } catch {
      toast.error('Speichern fehlgeschlagen');
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '24px 0', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>
        Lädt…
      </div>
    );
  }

  if (!guideline) {
    return (
      <div style={{ padding: '28px 0', textAlign: 'center' }}>
        <div style={{ fontSize: 32, marginBottom: 10 }}>🎨</div>
        <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 6 }}>
          Noch keine Guideline generiert
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 18, lineHeight: 1.6 }}>
          Die KI erstellt eine vollständige Brand Guideline<br />
          auf Basis der gespeicherten Brand-Daten.
        </div>
        <button
          onClick={generate}
          disabled={generating}
          style={{
            background: generating ? 'var(--border-light)' : 'var(--brand-primary, #004F59)',
            color: generating ? 'var(--text-tertiary)' : '#fff',
            border: 'none', borderRadius: 8,
            padding: '11px 22px', fontSize: 13, fontWeight: 900,
            cursor: generating ? 'not-allowed' : 'pointer',
            fontFamily: 'var(--font-sans)',
          }}
        >
          {generating ? '🤖 KI generiert Guideline…' : 'Guideline generieren →'}
        </button>
      </div>
    );
  }

  const g = guideline;
  const allColors = { ...g.colors, ...editedColors };

  return (
    <div style={{ fontFamily: 'var(--font-sans)' }}>

      {/* ── Status-Bar ── */}
      <div style={{
        background: 'var(--status-success-bg, #E3F6EF)',
        border: '0.5px solid #00875A33',
        borderRadius: 8, padding: '10px 14px', marginBottom: 16,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 14 }}>✓</span>
          <div>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#00875A' }}>
              Automatisch gespeichert
            </div>
            {savedAt && (
              <div style={{ fontSize: 10, color: '#4A7A5C', marginTop: 1 }}>
                {savedAt.toLocaleString('de-DE', { dateStyle: 'medium', timeStyle: 'short' })}
                {g.meta?.style_keyword ? ` · ${g.meta.style_keyword}` : ''}
                {g.meta?.farb_stimmung ? ` · ${g.meta.farb_stimmung}` : ''}
              </div>
            )}
          </div>
        </div>
        <button
          onClick={generate}
          disabled={generating}
          style={{
            background: 'transparent', color: '#00875A',
            border: '1px solid #00875A44', borderRadius: 6,
            padding: '5px 12px', fontSize: 11, fontWeight: 700,
            cursor: generating ? 'not-allowed' : 'pointer',
            fontFamily: 'var(--font-sans)', flexShrink: 0,
          }}
        >
          {generating ? '⏳ Generiert…' : '↻ Neu generieren'}
        </button>
      </div>

      {/* ── Farb-Tokens ── */}
      {Object.keys(allColors).length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 9, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.1em', marginBottom: 8 }}>
            Farb-Tokens — klick zum Kopieren · Doppelklick zum Bearbeiten
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(80px, 1fr))', gap: 8 }}>
            {Object.entries(allColors).slice(0, 16).map(([tk, hex]) => {
              const isEdited = editedColors[tk] !== undefined;
              return (
                <div key={tk} style={{ textAlign: 'center' }}>
                  <div
                    onClick={() => navigator.clipboard?.writeText(hex)}
                    onDoubleClick={() => {
                      const newHex = window.prompt(`Farbe für "${tk}":`, hex);
                      if (newHex && newHex.startsWith('#')) {
                        setEditedColors(prev => ({ ...prev, [tk]: newHex }));
                      }
                    }}
                    title={`${tk}: ${hex} — Klick zum Kopieren, Doppelklick zum Bearbeiten`}
                    style={{
                      height: 44, borderRadius: 7,
                      background: hex,
                      border: isEdited
                        ? '2px solid var(--brand-primary, #004F59)'
                        : '0.5px solid rgba(0,0,0,.08)',
                      cursor: 'pointer', marginBottom: 4,
                    }}
                  />
                  <div style={{ fontSize: 8, color: 'var(--text-tertiary)', fontFamily: 'monospace' }}>{hex}</div>
                  <div style={{ fontSize: 8, color: isEdited ? 'var(--brand-primary)' : 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.03em', fontWeight: isEdited ? 700 : 400 }}>
                    {tk.replace(/_/g, ' ')}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Änderungen speichern */}
          {Object.keys(editedColors).length > 0 && (
            <button
              onClick={saveEdits}
              style={{
                marginTop: 10, padding: '9px 18px',
                background: 'var(--brand-accent, #FAE600)', color: '#000',
                border: 'none', borderRadius: 7,
                fontSize: 11, fontWeight: 900, cursor: 'pointer',
                fontFamily: 'var(--font-sans)',
              }}
            >
              Änderungen speichern
            </button>
          )}
        </div>
      )}

      {/* ── Typografie-Vorschau ── */}
      {(g.typography || brandData) && (
        <div style={{ border: '0.5px solid var(--border-light)', borderRadius: 8, padding: '12px 14px', marginBottom: 12 }}>
          <div style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 10 }}>
            Typografie
          </div>
          {[
            { label: 'Überschrift', font: g.typography?.heading || brandData?.font_heading || brandData?.font_primary, size: 18, weight: 700 },
            { label: 'Unterüberschrift', font: g.typography?.heading || brandData?.font_heading, size: 14, weight: 600 },
            { label: 'Fließtext', font: g.typography?.body || brandData?.font_body || brandData?.font_secondary, size: 12, weight: 400 },
          ].filter(r => r.font).map(({ label, font, size, weight }) => (
            <div key={label} style={{ marginBottom: 10 }}>
              <div style={{ fontSize: 9, color: 'var(--text-tertiary)', marginBottom: 2 }}>{label} — {font}</div>
              <div style={{ fontFamily: font, fontSize: size, fontWeight: weight, color: 'var(--text-primary)', lineHeight: 1.4 }}>
                {label === 'Fließtext'
                  ? 'Fließtext mit gewähltem Font — klar, lesbar und professionell.'
                  : label === 'Unterüberschrift'
                  ? 'Unterüberschrift — Unsere Leistungen'
                  : 'Hauptüberschrift — Ihr Handwerksbetrieb'}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Stil-Keywords ── */}
      {g.meta && (
        <div style={{ padding: '10px 14px', background: 'var(--bg-app)', borderRadius: 8, fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
          {g.meta.style_keyword && <span style={{ marginRight: 8 }}>Stil: <strong>{g.meta.style_keyword}</strong></span>}
          {g.meta.farb_stimmung && <span style={{ marginRight: 8 }}>· Stimmung: <strong>{g.meta.farb_stimmung}</strong></span>}
          {g.meta.radius_label  && <span>· Radius: <strong>{g.meta.radius_label}</strong></span>}
        </div>
      )}
    </div>
  );
}
