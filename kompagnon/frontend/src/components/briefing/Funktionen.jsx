import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import API_BASE_URL from '../../config';

const TOOL_OPTIONS = [
  'Trustpilot','Google Maps','Instagram-Feed','Facebook-Feed',
  'WhatsApp Chat','Calendly','YouTube-Video','Chat-Widget','Elfsight',
];

export default function Funktionen({ leadId, token, onSaved }) {
  const [data, setData] = useState({
    terminbuchung: false,
    online_shop:   false,
    mehrsprachig:  false,
    externe_tools: [],
    tools_details: '',
  });
  const [ki, setKi] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving,  setSaving]  = useState(false);

  const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/briefings/${leadId}/ki-prefill-funktionen`, { headers })
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (!d) return;
        setKi(d);
        setData({
          terminbuchung: d.terminbuchung.vorhanden,
          online_shop:   d.online_shop.vorhanden,
          mehrsprachig:  d.mehrsprachig.vorhanden,
          externe_tools: d.externe_tools.liste || [],
          tools_details: '',
        });
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [leadId]); // eslint-disable-line

  const toggleTool = (tool) => {
    setData(p => ({
      ...p,
      externe_tools: p.externe_tools.includes(tool)
        ? p.externe_tools.filter(t => t !== tool)
        : [...p.externe_tools, tool],
    }));
  };

  const save = async () => {
    setSaving(true);
    try {
      await fetch(`${API_BASE_URL}/api/briefings/${leadId}`, {
        method: 'PUT', headers,
        body: JSON.stringify({
          funktionen_json: JSON.stringify({
            terminbuchung: data.terminbuchung,
            online_shop:   data.online_shop,
            mehrsprachig:  data.mehrsprachig,
            externe_tools: data.externe_tools,
            details:       data.tools_details,
            bestaetigt:    true,
          }),
        }),
      });
      toast.success('Funktionen gespeichert');
      if (onSaved) onSaved(data);
    } catch { toast.error('Fehler'); }
    finally { setSaving(false); }
  };

  if (loading) return (
    <div style={{ padding: 20, color: 'var(--text-tertiary)', fontSize: 13 }}>
      Erkenne Funktionen auf der Website…
    </div>
  );

  return (
    <div style={{ fontFamily: 'var(--font-sans)' }}>

      {ki && (
        <div style={{ padding: '10px 14px', background: '#E3F6EF', borderRadius: 8,
                      marginBottom: 14, fontSize: 12, color: '#00875A' }}>
          Funktionen automatisch aus Website-Scan erkannt — bitte prüfen
        </div>
      )}

      <FnRow field="terminbuchung" label="Online-Terminbuchung" icon="📅"
             checked={data.terminbuchung} ki_data={ki?.terminbuchung}
             onToggle={() => setData(p => ({ ...p, terminbuchung: !p.terminbuchung }))} />

      <FnRow field="online_shop" label="Online-Shop / Produkte" icon="🛒"
             checked={data.online_shop} ki_data={ki?.online_shop}
             onToggle={() => setData(p => ({ ...p, online_shop: !p.online_shop }))} />

      <FnRow field="mehrsprachig" label="Mehrsprachige Website" icon="🌍"
             checked={data.mehrsprachig} ki_data={ki?.mehrsprachig}
             onToggle={() => setData(p => ({ ...p, mehrsprachig: !p.mehrsprachig }))} />

      <div style={{ border: '0.5px solid var(--border-light)', borderRadius: 10,
                    marginBottom: 8, overflow: 'hidden' }}>
        <div style={{ padding: '10px 14px', background: 'var(--surface)',
                      borderBottom: '0.5px solid var(--border-light)',
                      display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 20 }}>🔌</span>
          <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', flex: 1 }}>
            Externe Tools & Widgets
          </span>
          {ki?.externe_tools?.auto_erkannt && (
            <span style={{ fontSize: 9, fontWeight: 900, padding: '1px 6px', borderRadius: 3,
                           background: '#E3F6EF', color: '#00875A' }}>
              KI · {ki.externe_tools.quelle}
            </span>
          )}
        </div>
        <div style={{ padding: '10px 14px', display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {TOOL_OPTIONS.map(tool => (
            <button
              key={tool}
              onClick={() => toggleTool(tool)}
              style={{
                padding: '5px 12px', borderRadius: 20, fontSize: 11, fontWeight: 700,
                cursor: 'pointer', fontFamily: 'var(--font-sans)',
                background: data.externe_tools.includes(tool) ? '#004F59' : 'var(--surface)',
                color:      data.externe_tools.includes(tool) ? '#fff'     : 'var(--text-secondary)',
                border:     data.externe_tools.includes(tool) ? 'none'     : '0.5px solid var(--border-light)',
              }}
            >
              {tool}
              {data.externe_tools.includes(tool) && ' ✓'}
            </button>
          ))}
        </div>
      </div>

      <textarea
        value={data.tools_details}
        onChange={e => setData(p => ({ ...p, tools_details: e.target.value }))}
        placeholder="Weitere Hinweise zu gewünschten Funktionen…"
        rows={2}
        style={{ width: '100%', padding: '9px 12px', border: '1px solid var(--border-light)',
                 borderRadius: 8, fontSize: 13, fontFamily: 'var(--font-sans)',
                 background: 'var(--bg-surface)', color: 'var(--text-primary)',
                 resize: 'none', boxSizing: 'border-box', marginBottom: 14 }}
      />

      <button
        onClick={save}
        disabled={saving}
        style={{
          width: '100%', padding: '12px', background: '#FAE600', color: '#000',
          border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 900,
          cursor: saving ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)',
          textTransform: 'uppercase', letterSpacing: '.05em',
        }}
      >
        {saving ? 'Wird gespeichert…' : 'Funktionen bestätigen & weiter'}
      </button>
    </div>
  );
}

function FnRow({ label, icon, checked, ki_data, onToggle }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 14,
      padding: '14px',
      border: '0.5px solid var(--border-light)',
      borderRadius: 10, marginBottom: 8,
      background: checked ? '#F0FDF4' : 'var(--bg-surface)',
    }}>
      <span style={{ fontSize: 22, flexShrink: 0 }}>{icon}</span>
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>{label}</span>
          {ki_data?.auto_erkannt && (
            <span style={{ fontSize: 9, fontWeight: 900, padding: '1px 6px', borderRadius: 3,
                           background: '#E3F6EF', color: '#00875A' }}>
              KI · {ki_data.quelle}
            </span>
          )}
          {!ki_data?.auto_erkannt && ki_data?.empfohlen && (
            <span style={{ fontSize: 9, fontWeight: 900, padding: '1px 6px', borderRadius: 3,
                           background: '#FFFBE0', color: '#B8860B' }}>
              {ki_data.quelle}
            </span>
          )}
        </div>
        {!checked && (
          <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginTop: 2 }}>
            {ki_data?.quelle || 'Nicht erkannt'}
          </div>
        )}
      </div>
      <div
        onClick={onToggle}
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
  );
}
