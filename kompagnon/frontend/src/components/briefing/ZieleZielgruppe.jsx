import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import API_BASE_URL from '../../config';

const CTA_OPTIONS = [
  'Anrufen', 'Kontaktformular ausfüllen', 'WhatsApp schreiben',
  'Termin buchen', 'Angebot anfragen', 'Newsletter abonnieren',
];

export default function ZieleZielgruppe({ leadId, token, briefing, onSaved }) {
  const [data, setData]       = useState({
    hauptziel:          briefing?.hauptziel || '',
    cta_aktion:         briefing?.aktionen  || '',
    zielgruppe_typ:     '',
    typischer_kunde:    briefing?.typischer_kunde   || '',
    haeufigste_anfrage: briefing?.haeufige_anfrage  || '',
  });
  const [ki,        setKi]        = useState(null);
  const [loading,   setLoading]   = useState(false);
  const [saving,    setSaving]    = useState(false);

  const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };

  useEffect(() => {
    if (!leadId) return;
    const hasData = briefing?.hauptziel || briefing?.aktionen;
    if (hasData) {
      setData(p => ({
        ...p,
        hauptziel:          briefing.hauptziel         || '',
        cta_aktion:         briefing.aktionen          || '',
        typischer_kunde:    briefing.typischer_kunde   || '',
        haeufigste_anfrage: briefing.haeufige_anfrage  || '',
      }));
      return;
    }
    loadKi();
  }, [leadId]); // eslint-disable-line

  const loadKi = async () => {
    setLoading(true);
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/briefings/${leadId}/ki-prefill-ziele`,
        { method: 'POST', headers }
      );
      if (!res.ok) return;
      const d = await res.json();
      setKi(d);
      setData({
        hauptziel:          d.hauptziel          || '',
        cta_aktion:         d.cta_aktion         || '',
        zielgruppe_typ:     d.zielgruppe_typ      || '',
        typischer_kunde:    d.typischer_kunde     || '',
        haeufigste_anfrage: d.haeufigste_anfrage  || '',
      });
    } catch { /* silent */ }
    finally { setLoading(false); }
  };

  const save = async () => {
    setSaving(true);
    try {
      await fetch(`${API_BASE_URL}/api/briefings/${leadId}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify({
          hauptziel:       data.hauptziel,
          aktionen:        data.cta_aktion,
          typischer_kunde: data.typischer_kunde,
          haeufige_anfrage: data.haeufigste_anfrage,
        }),
      });
      toast.success('Gespeichert');
      if (onSaved) onSaved(data);
    } catch {
      toast.error('Speichern fehlgeschlagen');
    } finally {
      setSaving(false);
    }
  };

  const isKi = (field) =>
    ki && ki[field] === data[field === 'cta_aktion' ? 'cta_aktion' : field] &&
    (ki[field + '_konfidenz'] || ki[field.replace('cta_aktion', 'cta_aktion') + '_konfidenz'] || 0) > 0.7;

  const konfidenz = (field) => ki?.[field + '_konfidenz'] || 0;

  const FIELDS = [
    { key: 'hauptziel', label: 'Hauptziel der Website', type: 'textarea',
      placeholder: 'z.B. Mehr Anfragen für Badsanierungen in Koblenz generieren',
      hint: 'Was soll die neue Website primär erreichen?',
      kiKey: 'hauptziel' },
    { key: 'cta_aktion', label: 'Primäre Handlung für den Besucher', type: 'select',
      options: CTA_OPTIONS,
      hint: 'Was soll ein Besucher als Erstes tun?',
      kiKey: 'cta_aktion' },
    { key: 'zielgruppe_typ', label: 'Zielgruppe', type: 'select',
      options: ['B2C (Privatkunden)', 'B2B (Geschäftskunden)', 'Beides'],
      kiKey: 'zielgruppe_typ' },
    { key: 'typischer_kunde', label: 'Typischer Kunde', type: 'textarea',
      placeholder: 'z.B. Eigenheimbesitzer, 40–60 Jahre, plant Badsanierung, sucht lokalen Fachbetrieb',
      hint: 'Wer ruft typischerweise an?',
      kiKey: 'typischer_kunde' },
    { key: 'haeufigste_anfrage', label: 'Häufigste Anfragen', type: 'text',
      placeholder: 'z.B. Heizungstausch, Rohrbruch-Notdienst, Badsanierung',
      hint: 'Top 2–3 Anfrage-Typen — wichtig für Content-KI',
      kiKey: 'haeufigste_anfrage' },
  ];

  const kiMatch = (kiKey) => {
    if (!ki) return false;
    const val = ki[kiKey];
    const dataVal = data[kiKey] || data['cta_aktion'];
    return val && val === (data[kiKey] ?? data['cta_aktion']) && konfidenz(kiKey) > 0.7;
  };

  const inputStyle = (kiKey) => ({
    width: '100%',
    padding: '9px 12px',
    border: kiMatch(kiKey) ? '1.5px solid #00875A55' : '1px solid var(--border-light)',
    borderRadius: 8,
    fontSize: 13,
    fontFamily: 'var(--font-sans)',
    background: kiMatch(kiKey) ? '#F0FDF4' : 'var(--bg-surface)',
    color: 'var(--text-primary)',
    boxSizing: 'border-box',
  });

  return (
    <div style={{ fontFamily: 'var(--font-sans)' }}>

      {loading && (
        <div style={{ padding: '12px 16px', background: '#E0F4F8', borderRadius: 8,
                      marginBottom: 16, fontSize: 12, color: '#004F59' }}>
          🤖 KI analysiert Website-Daten und füllt Felder vor…
        </div>
      )}

      {ki && !loading && (
        <div style={{ padding: '10px 14px', background: '#E3F6EF',
                      border: '0.5px solid #00875A33', borderRadius: 8, marginBottom: 16,
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
          <div style={{ fontSize: 12, color: '#00875A' }}>
            🤖 KI hat alle Felder vorausgefüllt — {ki.ki_begruendung}
          </div>
          <button
            onClick={loadKi}
            style={{ fontSize: 10, fontWeight: 700, background: 'transparent',
                     border: '0.5px solid #00875A44', borderRadius: 5, padding: '3px 9px',
                     cursor: 'pointer', color: '#00875A', fontFamily: 'var(--font-sans)' }}
          >
            ↻ Neu
          </button>
        </div>
      )}

      {FIELDS.map(({ key, label, type, placeholder, hint, options, kiKey }) => (
        <div key={key} style={{ marginBottom: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 5 }}>
            <label style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-secondary)',
                            textTransform: 'uppercase', letterSpacing: '.06em' }}>
              {label}
            </label>
            {ki && ki[kiKey] && konfidenz(kiKey) > 0.7 && (
              <span style={{ fontSize: 9, fontWeight: 900, padding: '1px 6px',
                             borderRadius: 3, background: '#E3F6EF', color: '#00875A' }}>
                🤖 KI · {Math.round(konfidenz(kiKey) * 100)}%
              </span>
            )}
          </div>

          {type === 'textarea' ? (
            <textarea
              value={data[key]}
              onChange={e => setData(p => ({ ...p, [key]: e.target.value }))}
              placeholder={placeholder}
              rows={3}
              style={{ ...inputStyle(kiKey), resize: 'vertical' }}
            />
          ) : type === 'select' ? (
            <select
              value={data[key]}
              onChange={e => setData(p => ({ ...p, [key]: e.target.value }))}
              style={inputStyle(kiKey)}
            >
              <option value="">— bitte wählen —</option>
              {options.map(o => <option key={o} value={o}>{o}</option>)}
            </select>
          ) : (
            <input
              type="text"
              value={data[key]}
              onChange={e => setData(p => ({ ...p, [key]: e.target.value }))}
              placeholder={placeholder}
              style={inputStyle(kiKey)}
            />
          )}

          {hint && (
            <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginTop: 3 }}>{hint}</div>
          )}
        </div>
      ))}

      <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
        <button
          onClick={save}
          disabled={saving}
          style={{
            flex: 1, padding: '12px',
            background: '#FAE600', color: '#000',
            border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 900,
            cursor: saving ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)',
            textTransform: 'uppercase', letterSpacing: '.05em',
          }}
        >
          {saving ? 'Wird gespeichert…' : ki ? '✓ Alles korrekt — weiter' : '→ Speichern & weiter'}
        </button>
        <button
          onClick={save}
          disabled={saving}
          style={{
            padding: '12px 16px', background: 'transparent',
            color: 'var(--text-tertiary)',
            border: '0.5px solid var(--border-light)', borderRadius: 8,
            fontSize: 12, cursor: saving ? 'not-allowed' : 'pointer',
            fontFamily: 'var(--font-sans)',
          }}
        >
          Entwurf
        </button>
      </div>
    </div>
  );
}
