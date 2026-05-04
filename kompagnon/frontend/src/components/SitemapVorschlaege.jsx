import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';

function KiEmpfehlung({ leadId, token, onAdded }) {
  const [empfehlungen, setEmpfehlungen] = useState(null);
  const [loading, setLoading]           = useState(false);
  const [adding, setAdding]             = useState({});

  const headers = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };

  const laden = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/sitemap/${leadId}/ki-empfehlung`, { headers });
      if (res.ok) {
        const d = await res.json();
        setEmpfehlungen(d);
      }
    } catch { /* silent */ }
    finally { setLoading(false); }
  };

  const addPage = async (page) => {
    setAdding(p => ({ ...p, [page.page_name]: true }));
    try {
      const res = await fetch(`${API_BASE_URL}/api/sitemap/${leadId}/add-suggested`, {
        method: 'POST', headers,
        body: JSON.stringify({
          page_name:    page.page_name,
          page_type:    page.page_type,
          zweck:        page.zweck,
          ziel_keyword: page.ziel_keyword,
          position:     page.position,
        }),
      });
      if (res.ok) {
        toast.success(`"${page.page_name}" hinzugefügt`);
        setEmpfehlungen(prev => ({
          ...prev,
          empfehlungen: prev.empfehlungen.filter(e => e.page_name !== page.page_name),
        }));
        if (onAdded) onAdded();
      }
    } catch { toast.error('Fehler'); }
    finally { setAdding(p => ({ ...p, [page.page_name]: false })); }
  };

  return (
    <div style={{
      background: 'linear-gradient(135deg, #004F59 0%, #008EAA 100%)',
      borderRadius: 12,
      padding: '16px 18px',
      marginBottom: 18,
    }}>
      <div style={{
        display: 'flex', alignItems: 'center',
        justifyContent: 'space-between', marginBottom: 10,
      }}>
        <div>
          <div style={{
            fontFamily: 'var(--font-display, "Barlow Condensed")',
            fontSize: 15, fontWeight: 700, color: '#FAE600',
            textTransform: 'uppercase', letterSpacing: '.04em',
          }}>
            KI-Empfehlung für {empfehlungen?.company || 'diesen Kunden'}
          </div>
          <div style={{ fontSize: 11, color: 'rgba(255,255,255,.6)', marginTop: 2 }}>
            Claude analysiert Gewerk, USP und Zielgruppe und empfiehlt individuelle Seiten
          </div>
        </div>
        {!empfehlungen && (
          <button
            onClick={laden}
            disabled={loading}
            style={{
              background: '#FAE600', color: '#000',
              border: 'none', borderRadius: 7,
              padding: '9px 18px',
              fontSize: 12, fontWeight: 900,
              cursor: loading ? 'not-allowed' : 'pointer',
              flexShrink: 0,
              fontFamily: 'var(--font-sans)',
              opacity: loading ? 0.7 : 1,
            }}
          >
            {loading ? 'Analysiert…' : 'Empfehlung generieren'}
          </button>
        )}
      </div>

      {empfehlungen?.empfehlungen?.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {empfehlungen.empfehlungen.map(page => (
            <div key={page.page_name} style={{
              background: 'rgba(255,255,255,.1)',
              borderRadius: 8,
              padding: '10px 14px',
              display: 'flex', alignItems: 'flex-start',
              justifyContent: 'space-between', gap: 12,
            }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: '#fff', marginBottom: 3 }}>
                  {page.page_name}
                </div>
                <div style={{ fontSize: 11, color: 'rgba(255,255,255,.65)', lineHeight: 1.5 }}>
                  {page.ki_begruendung || page.zweck}
                </div>
              </div>
              <button
                onClick={() => addPage(page)}
                disabled={adding[page.page_name]}
                style={{
                  background: 'rgba(255,255,255,.15)',
                  color: '#fff', border: '1px solid rgba(255,255,255,.3)',
                  borderRadius: 6, padding: '6px 14px',
                  fontSize: 11, fontWeight: 700,
                  cursor: adding[page.page_name] ? 'not-allowed' : 'pointer',
                  flexShrink: 0,
                  fontFamily: 'var(--font-sans)',
                  whiteSpace: 'nowrap',
                }}
              >
                {adding[page.page_name] ? '…' : '+ Hinzufügen'}
              </button>
            </div>
          ))}
        </div>
      )}

      {empfehlungen?.empfehlungen?.length === 0 && (
        <div style={{ fontSize: 12, color: 'rgba(255,255,255,.6)', textAlign: 'center', padding: '8px 0' }}>
          ✓ Alle empfohlenen Seiten sind bereits in der Sitemap
        </div>
      )}
    </div>
  );
}

export default function SitemapVorschlaege({ leadId, token, onAdded }) {
  const [data, setData]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState({});

  const headers = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };

  const loadSuggestions = () =>
    fetch(`${API_BASE_URL}/api/sitemap/${leadId}/suggest`, { headers })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setData(d); })
      .catch(() => {});

  useEffect(() => {
    if (!leadId) return;
    loadSuggestions().finally(() => setLoading(false));
  }, [leadId]); // eslint-disable-line

  const addPage = async (page) => {
    setAdding(p => ({ ...p, [page.page_name]: true }));
    try {
      const res = await fetch(`${API_BASE_URL}/api/sitemap/${leadId}/add-suggested`, {
        method: 'POST', headers,
        body: JSON.stringify({ page_name: page.page_name }),
      });
      if (res.ok) {
        toast.success(`"${page.page_name}" zur Sitemap hinzugefügt`);
        if (onAdded) onAdded();
        loadSuggestions();
      } else {
        toast.error('Fehler beim Hinzufügen');
      }
    } catch {
      toast.error('Verbindungsfehler');
    } finally {
      setAdding(p => ({ ...p, [page.page_name]: false }));
    }
  };

  if (loading) return null;
  if (!data) return null;

  const bedingte = (data.bedingte_pflichtseiten || []).filter(p => !p.bereits_vorhanden);
  const optional = (data.optionale_seiten || []).filter(p => !p.bereits_vorhanden);

  if (bedingte.length === 0 && optional.length === 0) return (
    <div style={{ marginTop: 20 }}>
      <KiEmpfehlung leadId={leadId} token={token} onAdded={onAdded} />
    </div>
  );

  const PageChip = ({ page, isPflicht }) => (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '10px 14px',
      background: isPflicht ? '#FFFBE0' : 'var(--bg-surface, #F0F4F5)',
      border: `0.5px solid ${isPflicht ? '#B8860B33' : 'var(--border-light)'}`,
      borderRadius: 8, marginBottom: 6,
    }}>
      <div style={{ flex: 1 }}>
        <div style={{
          fontSize: 13, fontWeight: 700,
          color: 'var(--text-primary)',
          display: 'flex', alignItems: 'center', gap: 7,
        }}>
          {isPflicht && (
            <span style={{
              fontSize: 9, fontWeight: 900,
              background: '#B8860B', color: '#fff',
              padding: '2px 6px', borderRadius: 3,
              textTransform: 'uppercase', letterSpacing: '.06em',
            }}>
              Bedingte Pflicht
            </span>
          )}
          {page.page_name}
        </div>
        <div style={{
          fontSize: 11, color: 'var(--text-tertiary)',
          marginTop: 2, lineHeight: 1.5,
        }}>
          {page.zweck}
        </div>
      </div>
      <button
        onClick={() => addPage(page)}
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
        }}
      >
        {adding[page.page_name] ? 'Wird hinzugefügt…' : '+ Hinzufügen'}
      </button>
    </div>
  );

  return (
    <div style={{ marginTop: 20 }}>

      <KiEmpfehlung leadId={leadId} token={token} onAdded={onAdded} />

      {bedingte.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <div style={{
            fontSize: 10, fontWeight: 900,
            color: '#B8860B',
            textTransform: 'uppercase', letterSpacing: '.1em',
            marginBottom: 8,
            display: 'flex', alignItems: 'center', gap: 6,
          }}>
            Bedingte Pflichtseiten — unter Umständen gesetzlich erforderlich
          </div>
          {bedingte.map(p => (
            <PageChip key={p.page_name} page={p} isPflicht={true} />
          ))}
        </div>
      )}

      {optional.length > 0 && (
        <div>
          <div style={{
            fontSize: 10, fontWeight: 900,
            color: 'var(--text-tertiary)',
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
              <PageChip key={p.page_name} page={p} isPflicht={false} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
