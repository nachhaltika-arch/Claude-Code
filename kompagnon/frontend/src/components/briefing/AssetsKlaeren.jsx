import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import API_BASE_URL from '../../config';

export default function AssetsKlaeren({ leadId, token, onSaved }) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [logo,    setLogo]    = useState(false);
  const [fotos,   setFotos]   = useState(false);
  const [ci,      setCi]      = useState(false);
  const [hinweis, setHinweis] = useState('');
  const [saving,  setSaving]  = useState(false);

  const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };

  useEffect(() => {
    if (!leadId) return;
    fetch(`${API_BASE_URL}/api/briefings/${leadId}/assets-status`, { headers })
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (!d) return;
        setStatus(d);
        setLogo(d.logo.vorhanden);
        setFotos(d.fotos.vorhanden);
        setCi(d.ci_handbuch.vorhanden || false);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [leadId]); // eslint-disable-line

  const save = async () => {
    setSaving(true);
    try {
      await fetch(`${API_BASE_URL}/api/briefings/${leadId}/assets-save`, {
        method: 'POST', headers,
        body: JSON.stringify({ logo_vorhanden: logo, fotos_vorhanden: fotos, sonstige_hinweise: hinweis }),
      });
      toast.success('Assets gespeichert');
      if (onSaved) onSaved({ logo, fotos, ci });
    } catch {
      toast.error('Fehler beim Speichern');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return (
    <div style={{ padding: 20, color: 'var(--text-tertiary)', fontSize: 13 }}>Erkenne Assets…</div>
  );

  return (
    <div style={{ fontFamily: 'var(--font-sans)' }}>

      <AssetRow
        icon="🏷️"
        label="Firmen-Logo"
        checked={logo}
        onChange={setLogo}
        autoDetected={status?.logo?.auto_erkannt}
        autoLabel={status?.logo?.auto_erkannt ? 'Aus Website erkannt' : null}
        detail={
          status?.logo?.url ? (
            <img
              src={status.logo.url}
              alt="Logo"
              style={{ height: 32, maxWidth: 120, objectFit: 'contain',
                       background: '#f0f0f0', borderRadius: 4, padding: 4, marginTop: 6 }}
              onError={e => { e.target.style.display = 'none'; }}
            />
          ) : null
        }
        uncheckedHint="Logo fehlt → bitte als SVG, AI oder EPS liefern"
      />

      <AssetRow
        icon="📷"
        label="Professionelle Fotos"
        checked={fotos}
        onChange={setFotos}
        autoDetected
        autoLabel={status?.fotos?.einschaetzung}
        detail={
          status?.fotos?.vorschau?.length > 0 ? (
            <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginTop: 6 }}>
              {status.fotos.vorschau.slice(0, 3).map((src, i) => (
                <img key={i} src={src} alt=""
                  style={{ width: 48, height: 48, objectFit: 'cover', borderRadius: 4,
                           border: '0.5px solid var(--border-light)' }}
                  onError={e => { e.target.style.display = 'none'; }}
                />
              ))}
              {status.fotos.anzahl > 3 && (
                <div style={{ width: 48, height: 48, borderRadius: 4,
                              background: 'var(--bg-app)',
                              border: '0.5px solid var(--border-light)',
                              display: 'flex', alignItems: 'center', justifyContent: 'center',
                              fontSize: 10, color: 'var(--text-tertiary)' }}>
                  +{status.fotos.anzahl - 3}
                </div>
              )}
            </div>
          ) : null
        }
        uncheckedHint="Kein Fotograf? → Handy-Fotos als Platzhalter möglich, professionelle Fotos empfohlen"
      />

      <AssetRow
        icon="📋"
        label="CI-Handbuch / Styleguide"
        checked={ci}
        onChange={setCi}
        autoDetected={false}
        autoLabel={status?.ci_handbuch?.dateiname ? `PDF vorhanden: ${status.ci_handbuch.dateiname}` : null}
        uncheckedHint="Kein CI-Handbuch? → Brand Design Schritt übernimmt das automatisch"
      />

      <div style={{ marginTop: 16, marginBottom: 16 }}>
        <label style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-secondary)',
                        textTransform: 'uppercase', letterSpacing: '.06em',
                        display: 'block', marginBottom: 5 }}>
          Zusätzliche Hinweise zu Medien
        </label>
        <textarea
          value={hinweis}
          onChange={e => setHinweis(e.target.value)}
          placeholder="z.B. Fotos werden nachgeliefert, Logo kommt per E-Mail, CI-Handbuch in Arbeit"
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
        {saving ? 'Wird gespeichert…' : '✓ Assets bestätigen & weiter'}
      </button>
    </div>
  );
}

function AssetRow({ icon, label, checked, onChange, autoDetected, autoLabel, detail, uncheckedHint }) {
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
            {autoDetected && autoLabel && (
              <span style={{ fontSize: 9, fontWeight: 900, padding: '1px 6px',
                             borderRadius: 3, background: '#E3F6EF', color: '#00875A' }}>
                🤖 {autoLabel}
              </span>
            )}
          </div>
          {!checked && uncheckedHint && (
            <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginTop: 2 }}>{uncheckedHint}</div>
          )}
          {detail}
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
