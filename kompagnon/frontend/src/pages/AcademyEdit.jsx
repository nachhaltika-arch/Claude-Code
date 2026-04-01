import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

const COLORS = [
  { value: 'primary', label: 'Blau' }, { value: 'success', label: 'Grün' },
  { value: 'warning', label: 'Gelb' }, { value: 'danger', label: 'Rot' },
  { value: 'info', label: 'Cyan' }, { value: 'secondary', label: 'Grau' },
];

const inputStyle = {
  width: '100%', padding: '9px 12px', border: '1px solid var(--border-medium)',
  borderRadius: 'var(--radius-md)', fontSize: 13, fontFamily: 'var(--font-sans)',
  color: 'var(--text-primary)', background: 'var(--bg-surface)', outline: 'none', boxSizing: 'border-box',
};

const labelStyle = {
  display: 'block', fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)',
  textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5,
};

export default function AcademyEdit() {
  const { courseId } = useParams();
  const isNew = !courseId || courseId === 'neu';
  const navigate = useNavigate();
  const { token, user } = useAuth();
  const h = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    title: '', description: '', category: '', category_color: 'primary',
    audience: 'employee', formats: ['text'], content_text: '', video_url: '',
  });
  const [checklistItems, setChecklistItems] = useState(['']);

  useEffect(() => {
    if (!isNew) {
      fetch(`${API_BASE_URL}/api/academy/courses/${courseId}`, { headers: h })
        .then(r => r.json())
        .then(data => {
          setForm({
            title: data.title || '', description: data.description || '',
            category: data.category || '', category_color: data.category_color || 'primary',
            audience: data.audience || 'employee', formats: data.formats || ['text'],
            content_text: data.content_text || '', video_url: data.video_url || '',
          });
          const items = (data.checklist_items || []).map(i => i.label);
          setChecklistItems(items.length > 0 ? items : ['']);
        })
        .catch(() => navigate('/app/akademie/admin'))
        .finally(() => setLoading(false));
    }
  }, [courseId]); // eslint-disable-line

  const toggleFormat = (fmt) => {
    setForm(prev => ({
      ...prev,
      formats: prev.formats.includes(fmt) ? prev.formats.filter(f => f !== fmt) : [...prev.formats, fmt],
    }));
  };

  const save = async () => {
    if (!form.title.trim()) return;
    setSaving(true);
    try {
      const body = { ...form, checklist_items: checklistItems.filter(i => i.trim()) };
      const url = isNew ? `${API_BASE_URL}/api/academy/courses` : `${API_BASE_URL}/api/academy/courses/${courseId}`;
      const method = isNew ? 'POST' : 'PUT';
      const res = await fetch(url, { method, headers: h, body: JSON.stringify(body) });
      if (res.ok) navigate('/app/akademie/admin');
    } catch (e) { console.error(e); }
    finally { setSaving(false); }
  };

  if (user?.role !== 'admin') return (
    <div style={{ textAlign: 'center', padding: 60, color: 'var(--text-tertiary)' }}>
      <div style={{ fontSize: 48, marginBottom: 12 }}>🔒</div>
      <div style={{ fontSize: 14 }}>Nur für Administratoren</div>
    </div>
  );

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '40vh' }}>
      <div style={{ width: 28, height: 28, borderRadius: '50%', border: '3px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
    </div>
  );

  return (
    <div style={{ maxWidth: 700, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
          {isNew ? 'Neuen Kurs anlegen' : 'Kurs bearbeiten'}
        </h2>
        <button onClick={() => navigate('/app/akademie/admin')} style={{
          padding: '6px 14px', background: 'transparent', color: 'var(--text-secondary)',
          border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
          fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)',
        }}>← Zurück</button>
      </div>

      <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 20, display: 'flex', flexDirection: 'column', gap: 16 }}>

        {/* Title */}
        <div>
          <label style={labelStyle}>Titel *</label>
          <input value={form.title} onChange={e => setForm(p => ({ ...p, title: e.target.value }))} placeholder="Kurstitel..." style={inputStyle} />
        </div>

        {/* Description */}
        <div>
          <label style={labelStyle}>Beschreibung</label>
          <textarea value={form.description} onChange={e => setForm(p => ({ ...p, description: e.target.value }))} rows={3} placeholder="Kurzbeschreibung..." style={{ ...inputStyle, resize: 'vertical' }} />
        </div>

        {/* Row: Category + Color + Audience */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
          <div>
            <label style={labelStyle}>Kategorie</label>
            <input value={form.category} onChange={e => setForm(p => ({ ...p, category: e.target.value }))} placeholder="z.B. Audit" style={inputStyle} />
          </div>
          <div>
            <label style={labelStyle}>Farbe</label>
            <select value={form.category_color} onChange={e => setForm(p => ({ ...p, category_color: e.target.value }))} style={inputStyle}>
              {COLORS.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
            </select>
          </div>
          <div>
            <label style={labelStyle}>Zielgruppe</label>
            <select value={form.audience} onChange={e => setForm(p => ({ ...p, audience: e.target.value }))} style={inputStyle}>
              <option value="employee">Mitarbeiter</option>
              <option value="customer">Kunde</option>
            </select>
          </div>
        </div>

        {/* Formats */}
        <div>
          <label style={labelStyle}>Formate</label>
          <div style={{ display: 'flex', gap: 12 }}>
            {[{ id: 'text', label: '📄 Text' }, { id: 'video', label: '🎬 Video' }, { id: 'checklist', label: '✅ Checkliste' }].map(fmt => (
              <label key={fmt.id} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, cursor: 'pointer', color: 'var(--text-secondary)' }}>
                <input type="checkbox" checked={form.formats.includes(fmt.id)} onChange={() => toggleFormat(fmt.id)}
                  style={{ width: 16, height: 16, accentColor: 'var(--brand-primary)' }} />
                {fmt.label}
              </label>
            ))}
          </div>
        </div>

        {/* Content Text */}
        {form.formats.includes('text') && (
          <div>
            <label style={labelStyle}>Anleitungstext (HTML erlaubt)</label>
            <textarea value={form.content_text} onChange={e => setForm(p => ({ ...p, content_text: e.target.value }))} rows={8}
              placeholder="<h3>Schritt 1</h3><p>Beschreibung...</p>" style={{ ...inputStyle, resize: 'vertical', fontFamily: 'var(--font-mono)', fontSize: 12, lineHeight: 1.6 }} />
          </div>
        )}

        {/* Video URL */}
        {form.formats.includes('video') && (
          <div>
            <label style={labelStyle}>Video-URL (YouTube/Vimeo Embed)</label>
            <input value={form.video_url} onChange={e => setForm(p => ({ ...p, video_url: e.target.value }))} placeholder="https://www.youtube.com/embed/..." style={inputStyle} />
          </div>
        )}

        {/* Checklist Items */}
        {form.formats.includes('checklist') && (
          <div>
            <label style={labelStyle}>Checklisten-Punkte</label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {checklistItems.map((item, i) => (
                <div key={i} style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                  <span style={{ fontSize: 11, color: 'var(--text-tertiary)', width: 20, textAlign: 'center', flexShrink: 0 }}>{i + 1}</span>
                  <input value={item} onChange={e => { const n = [...checklistItems]; n[i] = e.target.value; setChecklistItems(n); }}
                    placeholder={`Punkt ${i + 1}...`} style={{ ...inputStyle, flex: 1 }} />
                  <button onClick={() => setChecklistItems(prev => prev.filter((_, j) => j !== i))}
                    disabled={checklistItems.length <= 1}
                    style={{ padding: '6px 8px', background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', border: 'none', borderRadius: 'var(--radius-sm)', fontSize: 11, cursor: 'pointer', flexShrink: 0, opacity: checklistItems.length <= 1 ? 0.3 : 1 }}>
                    ✕
                  </button>
                </div>
              ))}
              <button onClick={() => setChecklistItems(prev => [...prev, ''])} style={{
                padding: '7px 14px', background: 'var(--bg-app)', color: 'var(--brand-primary)',
                border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
                fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)', alignSelf: 'flex-start',
              }}>+ Punkt hinzufügen</button>
            </div>
          </div>
        )}
      </div>

      {/* Save */}
      <div style={{ display: 'flex', gap: 10 }}>
        <button onClick={save} disabled={saving || !form.title.trim()} style={{
          padding: '10px 24px', background: 'var(--brand-primary)', color: 'white', border: 'none',
          borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600, cursor: saving ? 'not-allowed' : 'pointer',
          fontFamily: 'var(--font-sans)', opacity: saving || !form.title.trim() ? 0.6 : 1,
        }}>{saving ? 'Speichert...' : isNew ? 'Kurs anlegen' : 'Änderungen speichern'}</button>
        <button onClick={() => navigate('/app/akademie/admin')} style={{
          padding: '10px 20px', background: 'transparent', color: 'var(--text-secondary)',
          border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
          fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)',
        }}>Abbrechen</button>
      </div>
    </div>
  );
}
