import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
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
    audience: 'employee', formats: ['text'], linear_progress: false,
  });
  const [checklistItems, setChecklistItems] = useState(['']);
  const [modules, setModules] = useState([]);
  const [moduleLoading, setModuleLoading] = useState(false);
  const [newModuleTitle, setNewModuleTitle] = useState('');
  const [addingModule, setAddingModule] = useState(false);

  useEffect(() => {
    if (!isNew) {
      Promise.all([
        fetch(`${API_BASE_URL}/api/academy/courses/${courseId}`, { headers: h }).then(r => r.json()),
        fetch(`${API_BASE_URL}/api/academy/courses/${courseId}/modules`, { headers: h }).then(r => r.json()),
      ])
        .then(([data, mods]) => {
          setForm({
            title: data.title || '', description: data.description || '',
            category: data.category || '', category_color: data.category_color || 'primary',
            audience: data.audience || 'employee', formats: data.formats || ['text'],
            linear_progress: data.linear_progress || false,
          });
          const items = (data.checklist_items || []).map(i => i.label);
          setChecklistItems(items.length > 0 ? items : ['']);
          setModules(Array.isArray(mods) ? mods : []);
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

  const addModule = async () => {
    if (!newModuleTitle.trim() || addingModule) return;
    setAddingModule(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/academy/courses/${courseId}/modules`, {
        method: 'POST', headers: h,
        body: JSON.stringify({ title: newModuleTitle.trim(), sort_order: modules.length }),
      });
      const mod = await res.json();
      setModules(prev => [...prev, mod]);
      setNewModuleTitle('');
    } catch (e) { console.error(e); }
    finally { setAddingModule(false); }
  };

  const updateModuleTitle = async (mod, title) => {
    setModules(prev => prev.map(m => m.id === mod.id ? { ...m, title } : m));
    try {
      await fetch(`${API_BASE_URL}/api/academy/modules/${mod.id}`, {
        method: 'PUT', headers: h, body: JSON.stringify({ title }),
      });
    } catch (e) { console.error(e); }
  };

  const deleteModule = async (modId) => {
    if (!window.confirm('Modul und alle Lektionen darin löschen?')) return;
    try {
      await fetch(`${API_BASE_URL}/api/academy/modules/${modId}`, { method: 'DELETE', headers: h });
      setModules(prev => prev.filter(m => m.id !== modId));
    } catch (e) { console.error(e); }
  };

  const moveModule = async (idx, dir) => {
    const newMods = [...modules];
    const target = idx + dir;
    if (target < 0 || target >= newMods.length) return;
    [newMods[idx], newMods[target]] = [newMods[target], newMods[idx]];
    const updated = newMods.map((m, i) => ({ ...m, sort_order: i }));
    setModules(updated);
    setModuleLoading(true);
    try {
      await fetch(`${API_BASE_URL}/api/academy/courses/${courseId}/modules/reorder`, {
        method: 'PUT', headers: h,
        body: JSON.stringify({ order: updated.map(m => ({ id: m.id, sort_order: m.sort_order })) }),
      });
    } catch (e) { console.error(e); }
    finally { setModuleLoading(false); }
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

      {/* Course form */}
      <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 20, display: 'flex', flexDirection: 'column', gap: 16 }}>

        <div>
          <label style={labelStyle}>Titel *</label>
          <input value={form.title} onChange={e => setForm(p => ({ ...p, title: e.target.value }))} placeholder="Kurstitel..." style={inputStyle} />
        </div>

        <div>
          <label style={labelStyle}>Beschreibung</label>
          <textarea value={form.description} onChange={e => setForm(p => ({ ...p, description: e.target.value }))} rows={3} placeholder="Kurzbeschreibung..." style={{ ...inputStyle, resize: 'vertical' }} />
        </div>

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

        {/* Formats + linear_progress */}
        <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', alignItems: 'center' }}>
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
          <div>
            <label style={labelStyle}>Freischaltung</label>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, cursor: 'pointer', color: 'var(--text-secondary)' }}>
              <input type="checkbox" checked={form.linear_progress} onChange={e => setForm(p => ({ ...p, linear_progress: e.target.checked }))}
                style={{ width: 16, height: 16, accentColor: 'var(--brand-primary)' }} />
              Lineare Freischaltung
            </label>
          </div>
        </div>

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

      {/* Modules management (only for existing courses) */}
      {!isNew && (
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>Module verwalten</h3>
            <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{modules.length} Module</span>
          </div>

          {/* Module list */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 16 }}>
            {modules.length === 0 && (
              <div style={{ fontSize: 13, color: 'var(--text-tertiary)', textAlign: 'center', padding: '12px 0' }}>
                Noch keine Module angelegt
              </div>
            )}
            {modules.map((mod, idx) => (
              <div key={mod.id} style={{ display: 'flex', gap: 8, alignItems: 'center', padding: '8px 12px', background: 'var(--bg-app)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' }}>
                {/* Sort arrows */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 2, flexShrink: 0 }}>
                  <button onClick={() => moveModule(idx, -1)} disabled={idx === 0 || moduleLoading} style={{ padding: '1px 5px', background: 'none', border: '1px solid var(--border-medium)', borderRadius: 3, fontSize: 10, cursor: 'pointer', opacity: idx === 0 ? 0.3 : 1 }}>▲</button>
                  <button onClick={() => moveModule(idx, 1)} disabled={idx === modules.length - 1 || moduleLoading} style={{ padding: '1px 5px', background: 'none', border: '1px solid var(--border-medium)', borderRadius: 3, fontSize: 10, cursor: 'pointer', opacity: idx === modules.length - 1 ? 0.3 : 1 }}>▼</button>
                </div>
                {/* Inline title edit */}
                <input
                  value={mod.title}
                  onChange={e => updateModuleTitle(mod, e.target.value)}
                  style={{ ...inputStyle, flex: 1, padding: '6px 10px' }}
                />
                {/* Edit lessons button */}
                <Link
                  to={`/app/akademie/admin/modul/${mod.id}`}
                  style={{ padding: '6px 12px', background: 'var(--brand-primary)', color: 'white', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 11, cursor: 'pointer', fontFamily: 'var(--font-sans)', textDecoration: 'none', whiteSpace: 'nowrap' }}
                >
                  Lektionen
                </Link>
                <button onClick={() => deleteModule(mod.id)} style={{ padding: '6px 8px', background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', border: 'none', borderRadius: 'var(--radius-sm)', fontSize: 12, cursor: 'pointer', flexShrink: 0 }}>✕</button>
              </div>
            ))}
          </div>

          {/* Add new module */}
          <div style={{ display: 'flex', gap: 8 }}>
            <input
              value={newModuleTitle}
              onChange={e => setNewModuleTitle(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && addModule()}
              placeholder="Neues Modul..."
              style={{ ...inputStyle, flex: 1 }}
            />
            <button onClick={addModule} disabled={addingModule || !newModuleTitle.trim()} style={{
              padding: '9px 16px', background: 'var(--brand-primary)', color: 'white', border: 'none',
              borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 500, cursor: 'pointer',
              fontFamily: 'var(--font-sans)', opacity: !newModuleTitle.trim() ? 0.5 : 1, whiteSpace: 'nowrap',
            }}>+ Modul hinzufügen</button>
          </div>
        </div>
      )}
    </div>
  );
}
