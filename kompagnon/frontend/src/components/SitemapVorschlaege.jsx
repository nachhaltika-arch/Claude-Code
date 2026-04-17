import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';

export default function SitemapVorschlaege({ leadId, token, onAdded }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState({});

  const headers = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };

  const loadSuggestions = () => {
    if (!leadId) return;
    fetch(`${API_BASE_URL}/api/sitemap/${leadId}/suggest`, { headers })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setData(d); })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadSuggestions(); }, [leadId]); // eslint-disable-line

  const addPage = async (page) => {
    setAdding(p => ({ ...p, [page.page_name]: true }));
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/sitemap/${leadId}/add-suggested`,
        { method: 'POST', headers, body: JSON.stringify({ page_name: page.page_name }) },
      );
      if (res.ok) {
        toast.success(`"${page.page_name}" zur Sitemap hinzugefuegt`);
        if (onAdded) onAdded();
        loadSuggestions();
      } else {
        toast.error('Fehler beim Hinzufuegen');
      }
    } catch {
      toast.error('Verbindungsfehler');
    } finally {
      setAdding(p => ({ ...p, [page.page_name]: false }));
    }
  };

  if (loading || !data) return null;

  const bedingte = (data.bedingte_pflichtseiten || []).filter(p => !p.bereits_vorhanden);
  const optional = (data.optionale_seiten || []).filter(p => !p.bereits_vorhanden);

  if (bedingte.length === 0 && optional.length === 0) return null;

  return (
    <div style={{ marginTop: 20, fontFamily: 'var(--font-sans)' }}>

      {/* Bedingte Pflichtseiten */}
      {bedingte.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <div style={{
            fontSize: 10, fontWeight: 900,
            color: '#B8860B',
            textTransform: 'uppercase', letterSpacing: '.1em',
            marginBottom: 8,
            display: 'flex', alignItems: 'center', gap: 6,
          }}>
            ⚠️ Bedingte Pflichtseiten — unter Umstaenden gesetzlich erforderlich
          </div>
          {bedingte.map(p => (
            <PageChip key={p.page_name} page={p} isPflicht onAdd={addPage} adding={adding} />
          ))}
        </div>
      )}

      {/* Optionale Zusatzseiten */}
      {optional.length > 0 && (
        <div>
          <div style={{
            fontSize: 10, fontWeight: 900,
            color: 'var(--text-tertiary, #9AACAE)',
            textTransform: 'uppercase', letterSpacing: '.1em',
            marginBottom: 8,
          }}>
            Empfohlene Zusatzseiten
          </div>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
            gap: 6,
          }}>
            {optional.map(p => (
              <PageChip key={p.page_name} page={p} onAdd={addPage} adding={adding} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function PageChip({ page, isPflicht, onAdd, adding }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '10px 14px',
      background: isPflicht ? '#FFFBE0' : 'var(--bg-surface, #F0F4F5)',
      border: `0.5px solid ${isPflicht ? 'rgba(184,134,11,.2)' : 'var(--border-light, #D5E0E2)'}`,
      borderRadius: 8, marginBottom: 6,
    }}>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          fontSize: 13, fontWeight: 700,
          color: 'var(--text-primary, #000)',
          display: 'flex', alignItems: 'center', gap: 7,
        }}>
          {isPflicht && (
            <span style={{
              fontSize: 9, fontWeight: 900,
              background: '#B8860B', color: '#fff',
              padding: '2px 6px', borderRadius: 3,
              textTransform: 'uppercase', letterSpacing: '.06em',
              flexShrink: 0,
            }}>
              Bedingte Pflicht
            </span>
          )}
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {page.page_name}
          </span>
        </div>
        <div style={{
          fontSize: 11, color: 'var(--text-tertiary, #9AACAE)',
          marginTop: 2, lineHeight: 1.5,
        }}>
          {page.zweck}
        </div>
      </div>
      <button
        onClick={() => onAdd(page)}
        disabled={adding[page.page_name]}
        style={{
          background: isPflicht ? '#B8860B' : 'var(--brand-primary, #004F59)',
          color: '#fff', border: 'none',
          borderRadius: 6, padding: '6px 14px',
          fontSize: 11, fontWeight: 700,
          cursor: adding[page.page_name] ? 'not-allowed' : 'pointer',
          flexShrink: 0, marginLeft: 12,
          fontFamily: 'var(--font-sans)',
          opacity: adding[page.page_name] ? 0.6 : 1,
          textTransform: 'uppercase',
          letterSpacing: '.04em',
        }}
      >
        {adding[page.page_name] ? '…' : '+ Hinzufuegen'}
      </button>
    </div>
  );
}
