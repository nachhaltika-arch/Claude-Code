import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import API_BASE_URL from '../../config';

const TOOL_OPTIONS = [
  'Trustpilot', 'Google Maps', 'Instagram', 'Facebook',
  'WhatsApp', 'Calendly', 'Tidio', 'Intercom', 'YouTube',
];

export default function Funktionen({ leadId, token, onSaved }) {
  const [loading, setLoading]       = useState(true);
  const [saving,  setSaving]        = useState(false);
  const [terminbuchung, setTermin]  = useState(false);
  const [terminHint,    setTerminHint]  = useState(null);
  const [terminAuto,    setTerminAuto]  = useState(false);
  const [onlineShop,    setShop]    = useState(false);
  const [shopAuto,      setShopAuto]    = useState(false);
  const [mehrsprachig,  setMehr]    = useState(false);
  const [mehrAuto,      setMehrAuto]    = useState(false);
  const [tools,         setTools]   = useState([]);
  const [toolsAuto,     setToolsAuto]   = useState([]);
  const [toolsDetails,  setToolsDetails] = useState('');

  const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };

  useEffect(() => {
    if (!leadId) return;
    fetch(`${API_BASE_URL}/api/briefings/${leadId}/ki-prefill-funktionen`, { headers })
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (!d) return;
        setTermin(d.terminbuchung.vorhanden);
        setTerminAuto(d.terminbuchung.auto_erkannt);
        setTerminHint(d.terminbuchung.empfohlen ? 'Empfohlen für dein Gewerk' : null);
        setShop(d.online_shop.vorhanden);
        setShopAuto(d.online_shop.auto_erkannt);
        setMehr(d.mehrsprachig.vorhanden);
        setMehrAuto(d.mehrsprachig.auto_erkannt);
        setTools(d.externe_tools.liste || []);
        setToolsAuto(d.externe_tools.liste || []);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [leadId]); // eslint-disable-line

  const toggleTool = (name) => {
    setTools(prev =>
      prev.includes(name) ? prev.filter(t => t !== name) : [...prev, name]
    );
  };

  const save = async () => {
    setSaving(true);
    const parts = [];
    if (terminbuchung) parts.push('Terminbuchung');
    if (onlineShop)    parts.push('Online-Shop');
    if (mehrsprachig)  parts.push('Mehrsprachig');
    if (tools.length)  parts.push(tools.join(', '));

    const hinweis = parts.length
      ? `Funktionen: ${parts.join(' · ')}${toolsDetails ? '. ' + toolsDetails : ''}`
      : toolsDetails || '';

    try {
      await fetch(`${API_BASE_URL}/api/briefings/${leadId}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify({ sonstige_hinweise: hinweis }),
      });
      toast.success('Funktionen gespeichert');
      if (onSaved) onSaved({ terminbuchung, onlineShop, mehrsprachig, tools });
    } catch {
      toast.error('Fehler beim Speichern');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return (
    <div style={{ padding: 20, color: 'var(--text-tertiary)', fontSize: 13 }}>Erkenne Funktionen…</div>
  );

  return (
    <div style={{ fontFamily: 'var(--font-sans)' }}>

      <FnRow
        icon="📅"
        label="Terminbuchung"
        desc="Online-Kalender oder Buchungssystem"
        checked={terminbuchung}
        onChange={setTermin}
        autoDetected={terminAuto}
        hint={terminHint}
      />

      <FnRow
        icon="🛒"
        label="Online-Shop"
        desc="Produkte kaufen, Warenkorb, Kasse"
        checked={onlineShop}
        onChange={setShop}
        autoDetected={shopAuto}
      />

      <FnRow
        icon="🌍"
        label="Mehrsprachig"
        desc="Website in mehreren Sprachen"
        checked={mehrsprachig}
        onChange={setMehr}
        autoDetected={mehrAuto}
      />

      <div style={{
        border: '0.5px solid var(--border-light)', borderRadius: 10,
        marginBottom: 10, overflow: 'hidden',
      }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 12, padding: '12px 14px',
          background: 'var(--bg-surface)',
        }}>
          <span style={{ fontSize: 20 }}>🔗</span>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
              <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>Externe Tools</span>
              {toolsAuto.length > 0 && (
                <span style={{ fontSize: 9, fontWeight: 900, padding: '1px 6px', borderRadius: 3, background: '#E3F6EF', color: '#00875A' }}>
                  🤖 {toolsAuto.length} erkannt
                </span>
              )}
            </div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {TOOL_OPTIONS.map(name => {
                const active = tools.includes(name);
                const auto   = toolsAuto.includes(name);
                return (
                  <button
                    key={name}
                    onClick={() => toggleTool(name)}
                    style={{
                      padding: '4px 10px', borderRadius: 20, fontSize: 11, fontWeight: 700,
                      cursor: 'pointer', fontFamily: 'var(--font-sans)',
                      border: active ? '1.5px solid #00875A' : '1px solid var(--border-light)',
                      background: active ? '#E3F6EF' : 'var(--bg-app)',
                      color: active ? '#00875A' : 'var(--text-secondary)',
                      display: 'flex', alignItems: 'center', gap: 4,
                    }}
                  >
                    {auto && <span style={{ fontSize: 8 }}>🤖</span>}
                    {name}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      <div style={{ marginTop: 16, marginBottom: 16 }}>
        <label style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-secondary)',
                        textTransform: 'uppercase', letterSpacing: '.06em',
                        display: 'block', marginBottom: 5 }}>
          Zusätzliche Hinweise zu Funktionen
        </label>
        <textarea
          value={toolsDetails}
          onChange={e => setToolsDetails(e.target.value)}
          placeholder="z.B. Kontaktformular mit Datei-Upload, Newsletter-Anmeldung, Mitgliederbereich"
          rows={2}
          style={{ width: '100%', padding: '9px 12px', border: '1px solid var(--border-light)',
                   borderRadius: 8, fontSize: 13, fontFamily: 'var(--font-sans)',
                   background: 'var(--bg-surface)', color: 'var(--text-primary)',
                   resize: 'none', boxSizing: 'border-box' }}
        />
      </div>

      <button
        onClick={save}
        disabled={saving}
        style={{
          width: '100%', padding: '12px',
          background: '#FAE600', color: '#000',
          border: 'none', borderRadius: 8,
          fontSize: 13, fontWeight: 900,
          cursor: saving ? 'not-allowed' : 'pointer',
          fontFamily: 'var(--font-sans)',
          textTransform: 'uppercase', letterSpacing: '.05em',
        }}
      >
        {saving ? 'Wird gespeichert…' : '✓ Funktionen bestätigen & weiter'}
      </button>
    </div>
  );
}

function FnRow({ icon, label, desc, checked, onChange, autoDetected, hint }) {
  return (
    <div style={{
      border: '0.5px solid var(--border-light)', borderRadius: 10,
      marginBottom: 10, overflow: 'hidden',
    }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 12, padding: '12px 14px',
        background: checked ? '#F0FDF4' : 'var(--bg-surface)',
      }}>
        <span style={{ fontSize: 20, flexShrink: 0 }}>{icon}</span>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>{label}</span>
            {autoDetected && (
              <span style={{ fontSize: 9, fontWeight: 900, padding: '1px 6px',
                             borderRadius: 3, background: '#E3F6EF', color: '#00875A' }}>
                🤖 Crawler erkannt
              </span>
            )}
            {!autoDetected && hint && (
              <span style={{ fontSize: 9, fontWeight: 900, padding: '1px 6px',
                             borderRadius: 3, background: '#FFF7D6', color: '#B45309' }}>
                💡 {hint}
              </span>
            )}
          </div>
          <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginTop: 2 }}>{desc}</div>
        </div>
        <div
          onClick={() => onChange(!checked)}
          style={{
            width: 44, height: 24, borderRadius: 12, flexShrink: 0,
            background: checked ? '#00875A' : 'var(--border-light)',
            position: 'relative', cursor: 'pointer', transition: 'background .15s',
          }}
        >
          <div style={{
            position: 'absolute', top: 3, borderRadius: '50%',
            width: 18, height: 18, background: '#fff',
            left: checked ? 23 : 3, transition: 'left .15s',
          }} />
        </div>
      </div>
    </div>
  );
}
