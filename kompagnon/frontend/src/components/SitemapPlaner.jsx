import { useState, useEffect, useCallback } from 'react';
import API_BASE_URL from '../config';
import { useScreenSize } from '../utils/responsive';

// ── Constants ─────────────────────────────────────────────────────────────────

const TYPE_META = {
  startseite:  { label: 'Startseite',      color: '#008EAA', icon: '🏠' },
  leistung:    { label: 'Leistungsseite',  color: '#2563EB', icon: '🔧' },
  info:        { label: 'Info-Seite',      color: '#059669', icon: 'ℹ️' },
  vertrauen:   { label: 'Vertrauensseite', color: '#D97706', icon: '⭐' },
  conversion:  { label: 'Kontakt',         color: '#DC2626', icon: '📞' },
  rechtlich:   { label: 'Rechtlich',       color: '#6B7280', icon: '⚖️' },
  sonstige:    { label: 'Sonstige',        color: '#8B5CF6', icon: '📄' },
};

const TYPE_OPTIONS = [
  { value: 'startseite', label: 'Startseite' },
  { value: 'leistung',   label: 'Leistungsseite' },
  { value: 'info',       label: 'Info-Seite' },
  { value: 'vertrauen',  label: 'Vertrauensseite' },
  { value: 'conversion', label: 'Kontakt' },
  { value: 'sonstige',   label: 'Sonstige' },
];

const STATUS_OPTIONS = [
  { value: 'geplant',        label: 'Geplant' },
  { value: 'in_bearbeitung', label: 'In Bearbeitung' },
  { value: 'freigegeben',    label: 'Freigegeben' },
  { value: 'live',           label: 'Live' },
];

const STATUS_STYLE = {
  geplant:        { bg: '#EFF6FF', text: '#1D4ED8' },
  in_bearbeitung: { bg: '#FEF9C3', text: '#92400E' },
  freigegeben:    { bg: '#FEF3C7', text: '#B45309' },
  live:           { bg: '#DCFCE7', text: '#166534' },
};

function statusLabel(s) {
  return STATUS_OPTIONS.find(o => o.value === s)?.label || 'Geplant';
}

const authHeaders = () => {
  const token = localStorage.getItem('kompagnon_token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
};

// ── Shared style helpers ──────────────────────────────────────────────────────

const inp = {
  width: '100%', padding: '8px 10px', fontSize: 13, borderRadius: 8,
  border: '1.5px solid #DDE4E8', outline: 'none', boxSizing: 'border-box',
  fontFamily: 'var(--font-sans, system-ui)', background: '#FAFCFD', color: '#1A2C32',
};
const lbl = {
  fontSize: 11, fontWeight: 700, color: '#5A7080',
  textTransform: 'uppercase', letterSpacing: '0.06em',
  marginBottom: 4, display: 'block',
};
const divider = { border: 'none', borderTop: '1px solid #EEF2F4', margin: '4px 0' };

// ── Sub-components ────────────────────────────────────────────────────────────

function TypeDot({ type }) {
  const meta = TYPE_META[type] || TYPE_META.info;
  return (
    <div style={{
      width: 32, height: 32, borderRadius: '50%', flexShrink: 0,
      background: meta.color + '20', border: `2px solid ${meta.color}`,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: 14,
    }}>
      {meta.icon}
    </div>
  );
}

function StatusBadge({ status }) {
  const s = STATUS_STYLE[status] || STATUS_STYLE.geplant;
  return (
    <span style={{
      padding: '2px 8px', borderRadius: 12, fontSize: 11, fontWeight: 600,
      background: s.bg, color: s.text, whiteSpace: 'nowrap',
    }}>
      {statusLabel(status)}
    </span>
  );
}

// ── Content page card ─────────────────────────────────────────────────────────

function PageCard({ page, isChild, onEdit, onDelete }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 12,
      background: '#fff', border: '1px solid #E5E7EB',
      borderRadius: 8, padding: '10px 14px',
      boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
      marginLeft: isChild ? 32 : 0,
      position: 'relative',
    }}>
      {isChild && (
        <div style={{
          position: 'absolute', left: -16, top: '50%',
          width: 12, height: 1, background: '#D1D5DB',
        }} />
      )}
      <TypeDot type={page.page_type} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 700, fontSize: 14, color: '#1A2C32', lineHeight: 1.3 }}>
          {page.page_name}
        </div>
        {page.ziel_keyword && (
          <div style={{ fontSize: 11, color: '#6B7280', marginTop: 2 }}>🔑 {page.ziel_keyword}</div>
        )}
        {page.zweck && (
          <div style={{ fontSize: 11, color: '#9CA3AF', marginTop: 1, fontStyle: 'italic' }}>{page.zweck}</div>
        )}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
        <StatusBadge status={page.status} />
        <button
          onClick={() => onEdit(page)}
          style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 16, padding: '2px 4px', lineHeight: 1 }}
          title="Bearbeiten"
        >✏️</button>
        <button
          onClick={() => onDelete(page)}
          style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 16, padding: '2px 4px', lineHeight: 1 }}
          title="Löschen"
        >🗑️</button>
      </div>
    </div>
  );
}

function PageTree({ pages, onEdit, onDelete }) {
  if (!pages.length) {
    return (
      <div style={{ textAlign: 'center', padding: '40px 24px', color: '#9CA3AF', fontSize: 14 }}>
        <div style={{ fontSize: 32, marginBottom: 10 }}>🗺️</div>
        <div style={{ fontWeight: 600, marginBottom: 4 }}>Noch keine Seiten geplant</div>
        <div style={{ fontSize: 12 }}>Klicke auf „KI-Vorlage laden" oder füge Seiten manuell hinzu.</div>
      </div>
    );
  }

  const roots    = pages.filter(p => !p.parent_id).sort((a, b) => a.position - b.position);
  const byParent = {};
  pages.forEach(p => { if (p.parent_id) (byParent[p.parent_id] = byParent[p.parent_id] || []).push(p); });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {roots.map(root => (
        <div key={root.id} style={{ position: 'relative' }}>
          <PageCard page={root} isChild={false} onEdit={onEdit} onDelete={onDelete} />
          {(byParent[root.id] || []).sort((a, b) => a.position - b.position).map(child => (
            <div key={child.id} style={{ marginTop: 6, position: 'relative' }}>
              <div style={{ position: 'absolute', left: 16, top: -6, bottom: '50%', width: 1, background: '#D1D5DB' }} />
              <PageCard page={child} isChild={true} onEdit={onEdit} onDelete={onDelete} />
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

// ── Pflichtseiten area ────────────────────────────────────────────────────────

function PflichtseiteRow({ page, onEdit }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 12,
      padding: '8px 12px', borderRadius: 8,
      background: '#fff', border: '1px solid #E5E7EB',
      cursor: 'default',
    }}>
      <span style={{ fontSize: 16, flexShrink: 0, color: '#9CA3AF' }}>🔒</span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <span style={{ fontWeight: 700, fontSize: 13, color: '#6B7280' }}>{page.page_name}</span>
      </div>
      <span style={{
        fontSize: 10, fontWeight: 700, padding: '2px 7px', borderRadius: 10,
        background: '#F3F4F6', color: '#6B7280', whiteSpace: 'nowrap',
      }}>⚖️ Pflicht</span>
      <StatusBadge status={page.status} />
      <button
        onClick={() => onEdit(page)}
        style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 15, padding: '2px 4px', lineHeight: 1 }}
        title="Notizen bearbeiten"
      >✏️</button>
    </div>
  );
}

// ── Inline Add Form ───────────────────────────────────────────────────────────

const EMPTY_FORM = { page_name: '', page_type: 'info', parent_id: '' };

function AddPageForm({ contentPages, leadId, onAdded, onCancel }) {
  const [form, setForm]     = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [error, setError]   = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.page_name.trim()) { setError('Seitenname ist erforderlich.'); return; }
    setSaving(true); setError('');
    try {
      const body = {
        page_name: form.page_name.trim(),
        page_type: form.page_type,
        position:  contentPages.length,
        parent_id: form.parent_id ? Number(form.parent_id) : null,
      };
      const res = await fetch(`${API_BASE_URL}/api/sitemap/${leadId}/pages`, {
        method: 'POST', headers: authHeaders(), body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `Fehler ${res.status}`);
      onAdded(await res.json());
      setForm(EMPTY_FORM);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{
      background: '#F8FAFC', border: '1.5px solid #DDE4E8',
      borderRadius: 10, padding: 16, display: 'flex', flexDirection: 'column', gap: 10,
    }}>
      <div style={{ fontWeight: 700, fontSize: 13, color: '#1A2C32' }}>Neue Seite anlegen</div>
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        <input
          style={{ ...inp, flex: '1 1 160px' }}
          placeholder="Seitenname *"
          value={form.page_name}
          onChange={e => setForm(f => ({ ...f, page_name: e.target.value }))}
        />
        <select
          style={{ ...inp, flex: '0 0 auto', cursor: 'pointer' }}
          value={form.page_type}
          onChange={e => setForm(f => ({ ...f, page_type: e.target.value }))}
        >
          {TYPE_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <select
          style={{ ...inp, flex: '0 0 auto', cursor: 'pointer' }}
          value={form.parent_id}
          onChange={e => setForm(f => ({ ...f, parent_id: e.target.value }))}
        >
          <option value="">– Kein Elternelement –</option>
          {contentPages.filter(p => !p.parent_id).map(p => (
            <option key={p.id} value={p.id}>{p.page_name}</option>
          ))}
        </select>
      </div>
      {error && <div style={{ fontSize: 12, color: '#DC2626' }}>{error}</div>}
      <div style={{ display: 'flex', gap: 8 }}>
        <button
          type="submit" disabled={saving}
          style={{
            padding: '8px 20px', borderRadius: 8, border: 'none',
            background: saving ? '#DDE4E8' : '#008EAA',
            color: saving ? '#8A9BA8' : '#fff',
            fontSize: 13, fontWeight: 600,
            cursor: saving ? 'not-allowed' : 'pointer',
            fontFamily: 'var(--font-sans, system-ui)',
          }}
        >
          {saving ? 'Anlegen…' : 'Anlegen'}
        </button>
        <button
          type="button" onClick={onCancel}
          style={{
            padding: '8px 16px', borderRadius: 8,
            border: '1.5px solid #DDE4E8', background: '#fff',
            color: '#5A7080', fontSize: 13, cursor: 'pointer',
            fontFamily: 'var(--font-sans, system-ui)',
          }}
        >
          Abbrechen
        </button>
      </div>
    </form>
  );
}

// ── Edit Modal ────────────────────────────────────────────────────────────────

function EditModal({ page, contentPages, onSaved, onClose }) {
  const isPflicht = !!page.ist_pflichtseite;

  const [form, setForm] = useState({
    page_name:    page.page_name,
    page_type:    page.page_type,
    zweck:        page.zweck || '',
    ziel_keyword: page.ziel_keyword || '',
    cta_text:     page.cta_text || '',
    cta_ziel:     page.cta_ziel || 'kontaktformular',
    notizen:      page.notizen || '',
    status:       page.status || 'geplant',
    parent_id:    page.parent_id ? String(page.parent_id) : '',
    position:     page.position != null ? page.position : 0,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError]   = useState('');

  const handleSave = async () => {
    if (!isPflicht && !form.page_name.trim()) { setError('Seitenname ist erforderlich.'); return; }
    setSaving(true); setError('');
    try {
      const body = isPflicht
        ? { zweck: form.zweck, notizen: form.notizen, status: form.status }
        : {
            ...form,
            parent_id: form.parent_id ? Number(form.parent_id) : null,
            position:  Number(form.position),
          };
      const res = await fetch(`${API_BASE_URL}/api/sitemap/pages/${page.id}`, {
        method: 'PUT', headers: authHeaders(), body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `Fehler ${res.status}`);
      onSaved();
    } catch (err) {
      setError(err.message);
      setSaving(false);
    }
  };

  const parentOptions = contentPages.filter(p => p.id !== page.id && !p.parent_id);

  return (
    <div
      style={{
        position: 'fixed', inset: 0, zIndex: 3000,
        background: 'rgba(0,0,0,0.5)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16,
      }}
      onClick={e => e.target === e.currentTarget && onClose()}
    >
      <div style={{
        background: '#fff', borderRadius: 14, width: '100%', maxWidth: 560,
        maxHeight: '90vh', display: 'flex', flexDirection: 'column',
        boxShadow: '0 20px 60px rgba(0,0,0,0.25)', overflow: 'hidden',
      }}>
        {/* Header */}
        <div style={{
          padding: '16px 20px', borderBottom: '1px solid #EEF2F4',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <span style={{ fontWeight: 700, fontSize: 15, color: '#1A2C32' }}>
            Seite bearbeiten — {page.page_name}
          </span>
          <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', color: '#8A9BA8' }}>×</button>
        </div>

        {/* Body */}
        <div style={{ padding: 20, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 14 }}>

          {/* Pflichtseiten-Banner */}
          {isPflicht && (
            <div style={{
              background: '#FFFBEB', border: '1.5px solid #F59E0B',
              borderRadius: 8, padding: '10px 14px',
              fontSize: 13, color: '#92400E', fontWeight: 500,
            }}>
              ⚖️ Pflichtseite — Name und Typ können nicht geändert werden.
            </div>
          )}

          {/* Seitenname */}
          <div>
            <label style={lbl}>Seitenname {!isPflicht && '*'}</label>
            {isPflicht
              ? <div style={{ fontSize: 14, fontWeight: 600, color: '#9CA3AF', padding: '8px 0' }}>{form.page_name}</div>
              : <input style={inp} value={form.page_name} onChange={e => setForm(f => ({ ...f, page_name: e.target.value }))} />
            }
          </div>

          {/* Seitentyp + Status */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={lbl}>Seitentyp</label>
              {isPflicht
                ? <div style={{ fontSize: 13, color: '#9CA3AF', padding: '8px 0' }}>Rechtlich</div>
                : (
                  <select style={{ ...inp, cursor: 'pointer' }} value={form.page_type} onChange={e => setForm(f => ({ ...f, page_type: e.target.value }))}>
                    {TYPE_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                )
              }
            </div>
            <div>
              <label style={lbl}>Status</label>
              <select style={{ ...inp, cursor: 'pointer' }} value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))}>
                {STATUS_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>
          </div>

          {/* Strukturfelder – nur für freie Seiten */}
          {!isPflicht && (
            <>
              <hr style={divider} />
              <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 12 }}>
                <div>
                  <label style={lbl}>Übergeordnete Seite</label>
                  <select style={{ ...inp, cursor: 'pointer' }} value={form.parent_id} onChange={e => setForm(f => ({ ...f, parent_id: e.target.value }))}>
                    <option value="">– Keine (Top-Level) –</option>
                    {parentOptions.map(p => <option key={p.id} value={p.id}>{p.page_name}</option>)}
                  </select>
                </div>
                <div>
                  <label style={lbl}>Reihenfolge</label>
                  <input style={inp} type="number" min={0} value={form.position} onChange={e => setForm(f => ({ ...f, position: e.target.value }))} />
                </div>
              </div>
            </>
          )}

          <hr style={divider} />

          {/* Zweck */}
          <div>
            <label style={lbl}>Zweck der Seite</label>
            {isPflicht
              ? (
                <textarea
                  style={{ ...inp, resize: 'vertical', lineHeight: 1.5 }}
                  rows={3}
                  value={form.zweck}
                  onChange={e => setForm(f => ({ ...f, zweck: e.target.value }))}
                  placeholder="Gesetzliche Beschreibung…"
                />
              )
              : (
                <input style={inp} value={form.zweck} onChange={e => setForm(f => ({ ...f, zweck: e.target.value }))} placeholder="Was soll diese Seite erreichen?" />
              )
            }
          </div>

          {/* SEO & CTA – nur für freie Seiten */}
          {!isPflicht && (
            <>
              <div>
                <label style={lbl}>Ziel-Keyword</label>
                <input style={inp} value={form.ziel_keyword} onChange={e => setForm(f => ({ ...f, ziel_keyword: e.target.value }))} placeholder="z.B. Klempner Berlin" />
              </div>

              <hr style={divider} />

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label style={lbl}>CTA-Text</label>
                  <input style={inp} value={form.cta_text} onChange={e => setForm(f => ({ ...f, cta_text: e.target.value }))} placeholder="z.B. Jetzt anfragen" />
                </div>
                <div>
                  <label style={lbl}>CTA-Ziel</label>
                  <select style={{ ...inp, cursor: 'pointer' }} value={form.cta_ziel} onChange={e => setForm(f => ({ ...f, cta_ziel: e.target.value }))}>
                    <option value="kontaktformular">Kontaktformular</option>
                    <option value="telefon">Telefon</option>
                    <option value="whatsapp">WhatsApp</option>
                    <option value="angebotsseite">Angebotsseite</option>
                  </select>
                </div>
              </div>

              <hr style={divider} />
            </>
          )}

          {/* Notizen */}
          <div>
            <label style={lbl}>Notizen</label>
            <textarea
              style={{ ...inp, resize: 'vertical', lineHeight: 1.5 }}
              rows={3}
              value={form.notizen}
              onChange={e => setForm(f => ({ ...f, notizen: e.target.value }))}
              placeholder={isPflicht ? 'z.B. Rechtsbeistand prüft Text am 01.05.' : 'Interne Notizen…'}
            />
          </div>

          {error && <div style={{ fontSize: 12, color: '#DC2626' }}>{error}</div>}
        </div>

        {/* Footer */}
        <div style={{
          padding: '14px 20px', borderTop: '1px solid #EEF2F4',
          display: 'flex', gap: 10, justifyContent: 'flex-end', background: '#FAFCFD',
        }}>
          <button
            onClick={onClose}
            style={{ padding: '9px 18px', borderRadius: 8, border: '1.5px solid #DDE4E8', background: '#fff', color: '#5A7080', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans, system-ui)' }}
          >
            Abbrechen
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            style={{ padding: '9px 22px', borderRadius: 8, border: 'none', background: saving ? '#DDE4E8' : '#008EAA', color: saving ? '#8A9BA8' : '#fff', fontSize: 13, fontWeight: 600, cursor: saving ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans, system-ui)' }}
          >
            {saving ? 'Speichern…' : 'Speichern'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function SitemapPlaner({ leadId, leadData, onClose }) {
  const { isMobile } = useScreenSize();
  const [pages, setPages]           = useState([]);
  const [loading, setLoading]       = useState(true);
  const [generating, setGenerating] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editPage, setEditPage]     = useState(null);
  const [error, setError]           = useState('');

  const companyName = leadData?.display_name || leadData?.company_name || `Lead #${leadId}`;

  const load = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/sitemap/${leadId}`, { headers: authHeaders() });
      if (!res.ok) throw new Error(`Fehler ${res.status}`);
      setPages(await res.json() || []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [leadId]);

  useEffect(() => { load(); }, [load]);

  const contentPages  = pages.filter(p => !p.ist_pflichtseite);
  const pflichtPages  = pages.filter(p =>  p.ist_pflichtseite);

  const handleGenerate = async () => {
    if (!window.confirm(
      'Inhaltliche Seiten werden durch den KI-Vorschlag ersetzt.\n' +
      'Pflichtseiten (Impressum, Datenschutz, AGB, Barrierefreiheit) bleiben erhalten.\n\n' +
      'Fortfahren?'
    )) return;
    setGenerating(true); setError('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/sitemap/${leadId}/generate`, {
        method: 'POST', headers: authHeaders(),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `Fehler ${res.status}`);
      const data = await res.json();
      setPages(data.pages || []);
    } catch (e) {
      setError(e.message);
    } finally {
      setGenerating(false);
    }
  };

  const handleDelete = async (page) => {
    if (!window.confirm(`„${page.page_name}" wirklich löschen?`)) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/sitemap/pages/${page.id}`, {
        method: 'DELETE', headers: authHeaders(),
      });
      if (res.status === 403) { setError('Pflichtseiten können nicht gelöscht werden.'); return; }
      setPages(prev => prev.filter(p => p.id !== page.id && p.parent_id !== page.id));
    } catch (e) {
      setError(e.message);
    }
  };

  const handleAdded = (created) => {
    setPages(prev => [...prev, created]);
    setShowAddForm(false);
  };

  const handleSaved = () => {
    setEditPage(null);
    load();
  };

  const downloadPdf = async () => {
    setError('');
    try {
      const token = localStorage.getItem('kompagnon_token');
      const res = await fetch(`${API_BASE_URL}/api/sitemap/${leadId}/pdf`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('PDF konnte nicht geladen werden');
      const blob = await res.blob();
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement('a');
      a.href = url; a.download = `sitemap-${leadId}.pdf`; a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e.message);
    }
  };

  const btnPrimary = {
    padding: '8px 16px', borderRadius: 8, border: 'none',
    background: '#008EAA', color: '#fff',
    fontSize: 13, fontWeight: 600, cursor: 'pointer',
    fontFamily: 'var(--font-sans, system-ui)',
    display: 'inline-flex', alignItems: 'center', gap: 6,
  };
  const btnSecondary = {
    padding: '8px 16px', borderRadius: 8,
    border: '1.5px solid #DDE4E8', background: '#fff', color: '#5A7080',
    fontSize: 13, fontWeight: 500, cursor: 'pointer',
    fontFamily: 'var(--font-sans, system-ui)',
    display: 'inline-flex', alignItems: 'center', gap: 6,
  };

  return (
    <div
      style={{
        position: 'fixed', inset: 0, zIndex: 2000,
        background: 'rgba(0,0,0,0.5)',
        display: 'flex', alignItems: isMobile ? 'flex-end' : 'center', justifyContent: 'center',
        padding: isMobile ? 0 : 16,
      }}
      onClick={e => e.target === e.currentTarget && onClose?.()}
    >
      <div style={{
        background: '#F8FAFC', borderRadius: isMobile ? '16px 16px 0 0' : 16,
        width: '100%', maxWidth: 900, maxHeight: isMobile ? '94vh' : '92vh',
        display: 'flex', flexDirection: 'column',
        boxShadow: '0 24px 80px rgba(0,0,0,0.25)', overflow: 'hidden',
      }}>

        {/* Header */}
        <div style={{
          background: '#fff', borderBottom: '1px solid #EEF2F4',
          padding: '14px 20px',
          display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0,
        }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 11, color: '#8A9BA8', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 2 }}>
              Seitenstruktur planen
            </div>
            <div style={{ fontSize: 16, fontWeight: 700, color: '#1A2C32', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {companyName}
            </div>
          </div>

          <button
            onClick={handleGenerate}
            disabled={generating}
            style={{ ...btnPrimary, opacity: generating ? 0.7 : 1, cursor: generating ? 'not-allowed' : 'pointer' }}
          >
            {generating
              ? <><span style={{ width: 11, height: 11, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: '#fff', animation: 'spin 0.8s linear infinite', display: 'inline-block' }} />Generiere…</>
              : '🤖 KI-Vorlage laden'
            }
          </button>

          <button onClick={downloadPdf} style={btnSecondary}>
            📄 PDF exportieren
          </button>

          <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 22, cursor: 'pointer', color: '#8A9BA8', lineHeight: 1, padding: 4 }}>
            ×
          </button>
        </div>

        {/* Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: 20, display: 'flex', flexDirection: 'column', gap: 24 }}>
          {error && (
            <div style={{ background: '#FFF0F0', border: '1px solid #FFBDBD', borderRadius: 8, padding: '10px 14px', fontSize: 13, color: '#C0392B' }}>
              {error}
            </div>
          )}

          {loading ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '60px 0' }}>
              <div style={{ width: 28, height: 28, borderRadius: '50%', border: '3px solid #DDE4E8', borderTopColor: '#008EAA', animation: 'spin 0.8s linear infinite' }} />
            </div>
          ) : contentPages.length === 0 && !generating ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '48px 24px', textAlign: 'center' }}>
              <div style={{ fontSize: 48, marginBottom: 16 }}>🗺️</div>
              <div style={{ fontSize: 16, fontWeight: 700, color: '#1A2C32', marginBottom: 8 }}>Noch keine Sitemap geplant</div>
              <div style={{ fontSize: 13, color: '#9CA3AF', marginBottom: 24, maxWidth: 300 }}>
                Klicke auf „KI-Vorlage laden" um automatisch eine passende Seitenstruktur zu erstellen, oder füge Seiten manuell hinzu.
              </div>
              <button
                onClick={() => setShowAddForm(true)}
                style={{ padding: '8px 20px', borderRadius: 8, border: '1px dashed #CBD5E1', background: '#F8FAFC', color: '#374151', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}
              >
                + Seite manuell hinzufügen
              </button>
            </div>
          ) : (
            <>
              {/* ── Bereich A: Inhaltliche Seiten ── */}
              <div>
                <div style={{ fontSize: 14, fontWeight: 700, color: '#1A2C32', marginBottom: 12 }}>
                  Inhaltliche Seiten
                </div>
                <PageTree pages={contentPages} onEdit={setEditPage} onDelete={handleDelete} />
              </div>

              {/* ── Bereich B: Pflichtseiten ── */}
              <div>
                <div style={{ borderTop: '2px solid #EEF2F4', paddingTop: 20 }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: '#374151', marginBottom: 6 }}>
                    ⚖️ Rechtlich vorgeschriebene Seiten
                  </div>
                  <div style={{ fontSize: 12, color: '#9CA3AF', marginBottom: 14, lineHeight: 1.5 }}>
                    Diese Seiten sind gesetzlich verpflichtend und werden von KOMPAGNON mit rechtskonformem Inhalt befüllt.
                  </div>
                  <div style={{
                    background: '#F8F9FA', borderRadius: 12, padding: 16,
                    display: 'flex', flexDirection: 'column', gap: 8,
                  }}>
                    {pflichtPages.length === 0
                      ? <div style={{ fontSize: 13, color: '#9CA3AF', textAlign: 'center', padding: '12px 0' }}>Keine Pflichtseiten geladen.</div>
                      : pflichtPages.map(p => (
                          <PflichtseiteRow key={p.id} page={p} onEdit={setEditPage} />
                        ))
                    }
                  </div>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        {!loading && (
          <div style={{ background: '#fff', borderTop: '1px solid #EEF2F4', padding: '14px 20px', flexShrink: 0 }}>
            {showAddForm ? (
              <AddPageForm
                contentPages={contentPages}
                leadId={leadId}
                onAdded={handleAdded}
                onCancel={() => setShowAddForm(false)}
              />
            ) : (
              <button onClick={() => setShowAddForm(true)} style={{ ...btnSecondary, borderStyle: 'dashed' }}>
                + Seite hinzufügen
              </button>
            )}
          </div>
        )}
      </div>

      {/* Edit Modal */}
      {editPage && (
        <EditModal
          page={editPage}
          contentPages={contentPages}
          onSaved={handleSaved}
          onClose={() => setEditPage(null)}
        />
      )}
    </div>
  );
}
