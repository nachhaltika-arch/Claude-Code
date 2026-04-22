import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import API_BASE_URL from '../../config';
import { useConfirmStep } from '../../hooks/useConfirmStep';

const ALL_SOCIAL = [
  'Facebook', 'Instagram', 'LinkedIn', 'YouTube', 'TikTok',
  'Pinterest', 'X/Twitter', 'Xing', 'WhatsApp Business', 'Keine',
];

export default function SeoZiele({ leadId, token, onSaved, projectId, onStepConfirmed }) {
  const [ki,       setKi]       = useState(null);
  const [loading,  setLoading]  = useState(true);
  const [saving,   setSaving]   = useState(false);
  const { confirmStep, loading: confirming } = useConfirmStep({ projectId, token });
  const [keywords, setKeywords] = useState([]);
  const [kwInput,  setKwInput]  = useState('');
  const [social,   setSocial]   = useState([]);
  const [gbStatus, setGbStatus] = useState('');

  const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };

  useEffect(() => {
    if (!leadId) return;
    fetch(`${API_BASE_URL}/api/briefings/${leadId}/ki-prefill-seo`, { method: 'POST', headers })
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (!d) return;
        setKi(d);
        setKeywords(d.keywords || []);
        setSocial(d.social_media?.gefunden || []);
        setGbStatus(d.google_business?.status || '');
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [leadId]); // eslint-disable-line

  const addKeyword = () => {
    const kw = kwInput.trim();
    if (!kw || keywords.includes(kw)) return;
    setKeywords(p => [...p, kw]);
    setKwInput('');
  };

  const removeKeyword = (kw) => setKeywords(p => p.filter(k => k !== kw));

  const toggleSocial = (s) =>
    setSocial(p => p.includes(s) ? p.filter(x => x !== s) : [...p, s]);

  const saveSeoData = async (bestaetigt = false) => {
    await fetch(`${API_BASE_URL}/api/briefings/${leadId}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify({
        seo_json: JSON.stringify({
          keywords,
          google_business: gbStatus,
          social_media: social,
          bestaetigt,
        }),
      }),
    });
  };

  const save = async () => {
    setSaving(true);
    try {
      await saveSeoData(false);
      toast.success('SEO-Ziele gespeichert');
      if (onSaved) onSaved({ keywords, social, gbStatus });
    } catch {
      toast.error('Fehler');
    } finally {
      setSaving(false);
    }
  };

  const saveAndConfirm = async () => {
    setSaving(true);
    try {
      await saveSeoData(true);
      toast.success('SEO-Ziele abgeschlossen');
      if (onSaved) onSaved({ keywords, social, gbStatus });
      await confirmStep('seo-ziele', onStepConfirmed);
    } catch {
      toast.error('Fehler');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return (
    <div style={{ padding: 20, color: 'var(--text-tertiary)', fontSize: 13 }}>
      🤖 Generiere Keywords und prüfe Google Business…
    </div>
  );

  return (
    <div style={{ fontFamily: 'var(--font-sans)' }}>

      {ki && (
        <div style={{ padding: '10px 14px', background: '#E3F6EF', borderRadius: 8,
                      marginBottom: 16, fontSize: 12, color: '#00875A' }}>
          🤖 Keywords automatisch generiert · Google Business und Social Media aus Website erkannt
        </div>
      )}

      {/* KEYWORDS */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <label style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-secondary)',
                          textTransform: 'uppercase', letterSpacing: '.06em' }}>
            Top-Suchbegriffe für Google
          </label>
          <span style={{ fontSize: 9, fontWeight: 900, padding: '1px 6px', borderRadius: 3,
                         background: '#E3F6EF', color: '#00875A' }}>
            🤖 Automatisch · {ki?.keywords_quelle}
          </span>
        </div>

        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 8 }}>
          {keywords.map(kw => (
            <div key={kw} style={{
              display: 'flex', alignItems: 'center', gap: 4,
              padding: '5px 10px', borderRadius: 20,
              background: '#004F59', color: '#fff',
              fontSize: 12, fontWeight: 700,
            }}>
              {kw}
              <span
                onClick={() => removeKeyword(kw)}
                style={{ cursor: 'pointer', opacity: 0.6, fontSize: 14, lineHeight: 1 }}
              >×</span>
            </div>
          ))}
        </div>

        <div style={{ display: 'flex', gap: 6 }}>
          <input
            value={kwInput}
            onChange={e => setKwInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && addKeyword()}
            placeholder="Keyword eingeben + Enter"
            style={{
              flex: 1, padding: '8px 12px',
              border: '1px solid var(--border-light)', borderRadius: 7,
              fontSize: 13, fontFamily: 'var(--font-sans)',
              background: 'var(--bg-surface)', color: 'var(--text-primary)',
            }}
          />
          <button onClick={addKeyword} style={{
            padding: '8px 14px', background: 'var(--brand-primary)', color: '#fff',
            border: 'none', borderRadius: 7, fontSize: 12, fontWeight: 700,
            cursor: 'pointer', fontFamily: 'var(--font-sans)',
          }}>
            + Hinzufügen
          </button>
        </div>
      </div>

      {/* GOOGLE BUSINESS */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
          <label style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-secondary)',
                          textTransform: 'uppercase', letterSpacing: '.06em' }}>
            Google Business Profil
          </label>
          <span style={{ fontSize: 9, fontWeight: 900, padding: '1px 6px', borderRadius: 3,
                         background: '#E3F6EF', color: '#00875A' }}>
            🤖 Aus Crawler
          </span>
        </div>
        <div style={{
          padding: '10px 14px', borderRadius: 8,
          border: '0.5px solid var(--border-light)',
          background: gbStatus.includes('Vorhanden') ? '#F0FDF4' : '#FFFBE0',
          fontSize: 13, color: 'var(--text-primary)',
          display: 'flex', alignItems: 'center', gap: 10,
        }}>
          <span style={{ fontSize: 18 }}>
            {gbStatus.includes('Vorhanden') ? '✅' : gbStatus === 'unbekannt' ? '❓' : '⚠️'}
          </span>
          <div style={{ flex: 1 }}>{gbStatus || 'Nicht geprüft'}</div>
          <select
            value={gbStatus}
            onChange={e => setGbStatus(e.target.value)}
            style={{
              padding: '5px 8px', border: '0.5px solid var(--border-light)',
              borderRadius: 6, fontSize: 12, background: 'var(--bg-surface)',
              color: 'var(--text-primary)',
            }}
          >
            <option>Vorhanden, aktiv gepflegt</option>
            <option>Vorhanden, veraltet</option>
            <option>Nicht vorhanden — wird angelegt</option>
            <option>unbekannt</option>
          </select>
        </div>
      </div>

      {/* SOCIAL MEDIA */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <label style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-secondary)',
                          textTransform: 'uppercase', letterSpacing: '.06em' }}>
            Social Media (aktiv)
          </label>
          {ki?.social_media?.auto && (
            <span style={{ fontSize: 9, fontWeight: 900, padding: '1px 6px', borderRadius: 3,
                           background: '#E3F6EF', color: '#00875A' }}>
              🤖 {ki.social_media.quelle}
            </span>
          )}
        </div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {ALL_SOCIAL.map(s => (
            <button
              key={s}
              onClick={() => toggleSocial(s)}
              style={{
                padding: '5px 12px', borderRadius: 20, fontSize: 11, fontWeight: 700,
                cursor: 'pointer', fontFamily: 'var(--font-sans)',
                background: social.includes(s) ? '#004F59' : 'var(--bg-surface)',
                color:      social.includes(s) ? '#fff'    : 'var(--text-secondary)',
                border:     social.includes(s) ? 'none'    : '0.5px solid var(--border-light)',
              }}
            >
              {s}{social.includes(s) ? ' ✓' : ''}
            </button>
          ))}
        </div>
      </div>

      {/* GA Analytics — read-only info */}
      {ki?.ga_analytics?.status && ki.ga_analytics.status !== 'unbekannt' && (
        <div style={{ padding: '8px 12px', borderRadius: 7, background: '#E0F4F8',
                      fontSize: 11, color: '#004F59', marginBottom: 14 }}>
          📊 Google Analytics: {ki.ga_analytics.type} · {ki.ga_analytics.status}
          <span style={{ opacity: 0.6, marginLeft: 6 }}>(aus Analyse-Zentrale)</span>
        </div>
      )}

      <div style={{ display: 'flex', gap: 8 }}>
        <button
          onClick={save}
          disabled={saving || confirming}
          style={{
            flex: '0 0 auto', padding: '12px 18px',
            background: 'var(--bg-surface)', color: 'var(--text-primary)',
            border: '0.5px solid var(--border-light)', borderRadius: 8,
            fontSize: 13, fontWeight: 700,
            cursor: (saving || confirming) ? 'not-allowed' : 'pointer',
            fontFamily: 'var(--font-sans)',
          }}
        >
          {saving ? 'Speichert…' : 'Zwischenspeichern'}
        </button>
        <button
          onClick={saveAndConfirm}
          disabled={saving || confirming}
          style={{
            flex: 1, padding: '12px',
            background: '#FAE600', color: '#000',
            border: 'none', borderRadius: 8,
            fontSize: 13, fontWeight: 900,
            cursor: (saving || confirming) ? 'not-allowed' : 'pointer',
            fontFamily: 'var(--font-sans)',
            textTransform: 'uppercase', letterSpacing: '.05em',
          }}
        >
          {(saving || confirming) ? 'Wird gespeichert…' : '✓ SEO abschließen & weiter →'}
        </button>
      </div>
    </div>
  );
}
