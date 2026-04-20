import React, { useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import API_BASE_URL from '../config';
import toast from 'react-hot-toast';

const STAGES = [
  { key: 'neu',              label: 'Neu',              color: 'var(--text-tertiary)' },
  { key: 'kontaktiert',      label: 'Kontaktiert',      color: '#3b82f6' },
  { key: 'angebot_gesendet', label: 'Angebot gesendet', color: '#f59e0b' },
  { key: 'gewonnen',         label: 'Gewonnen',         color: '#1D9E75' },
  { key: 'verloren',         label: 'Verloren',         color: '#E24B4A' },
];

const fmtEUR = (v) => Number(v || 0).toLocaleString('de-DE', { style: 'currency', currency: 'EUR' });

export default function Deals() {
  const { token } = useAuth();
  const [deals, setDeals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingDeal, setEditingDeal] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const h = { Authorization: `Bearer ${token}` };

  const handleDeleteDeal = async () => {
    if (!deleteConfirm) return;
    setDeleting(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/deals/${deleteConfirm.id}`, {
        method: 'DELETE', headers: h,
      });
      if (!res.ok) throw new Error('Löschen fehlgeschlagen');
      toast.success(`Deal "${deleteConfirm.title}" gelöscht`);
      setDeleteConfirm(null);
      // Auch das Edit-Modal schließen falls es offen ist für genau diesen Deal
      if (editingDeal?.id === deleteConfirm.id) {
        setShowModal(false);
        setEditingDeal(null);
      }
      loadDeals();
    } catch (e) {
      toast.error(e.message);
    }
    setDeleting(false);
  };

  const loadDeals = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/deals/`, { headers: h });
      if (res.ok) setDeals(await res.json());
    } catch (e) { console.error(e); }
    setLoading(false);
  }, [token]); // eslint-disable-line

  useEffect(() => { loadDeals(); }, [loadDeals]);

  const openNew = () => {
    setEditingDeal({
      title: '', company_id: null, status: 'neu', notes: '',
      product_type: 'website',
      items: [{ position: '', quantity: 1, unit_price: 0 }],
    });
    setShowModal(true);
  };

  const openEdit = async (dealId) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/deals/${dealId}`, { headers: h });
      if (res.ok) {
        const d = await res.json();
        if (!d.items || d.items.length === 0) d.items = [{ position: '', quantity: 1, unit_price: 0 }];
        setEditingDeal(d);
        setShowModal(true);
      }
    } catch (e) { console.error(e); }
  };

  const stageStats = STAGES.map(stage => {
    const dealsInStage = deals.filter(d => d.status === stage.key);
    const total = dealsInStage.reduce((sum, d) => sum + (d.total_value || 0), 0);
    return { ...stage, deals: dealsInStage, total, count: dealsInStage.length };
  });

  return (
    <div style={{ padding: '24px 32px', maxWidth: 1600, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)' }}>💼 Deals</div>
          <div style={{ fontSize: 13, color: 'var(--text-tertiary)', marginTop: 4 }}>
            {deals.length} Deals · Pipeline-Wert {fmtEUR(
              deals.filter(d => !['gewonnen', 'verloren'].includes(d.status))
                   .reduce((s, d) => s + (d.total_value || 0), 0)
            )}
          </div>
        </div>
        <button
          onClick={openNew}
          style={{
            padding: '10px 20px', background: 'var(--brand-primary)', color: '#fff',
            border: 'none', borderRadius: 'var(--radius-md)', fontSize: 14, fontWeight: 600,
            cursor: 'pointer', fontFamily: 'var(--font-sans)',
          }}
        >
          + Neuer Deal
        </button>
      </div>

      {/* Kanban */}
      {loading ? (
        <div style={{ color: 'var(--text-tertiary)', padding: 40, textAlign: 'center' }}>Wird geladen…</div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${STAGES.length}, minmax(240px, 1fr))`,
          gap: 14,
          overflowX: 'auto',
        }}>
          {stageStats.map(stage => (
            <div key={stage.key} style={{
              background: 'var(--bg-app)',
              border: '1px solid var(--border-light)',
              borderRadius: 'var(--radius-lg)',
              padding: 12,
              minHeight: 400,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12, paddingBottom: 10, borderBottom: `2px solid ${stage.color}` }}>
                <div>
                  <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    {stage.label}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>
                    {stage.count} · {fmtEUR(stage.total)}
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {stage.deals.length === 0 ? (
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)', textAlign: 'center', padding: '20px 0', fontStyle: 'italic' }}>
                    Keine Deals
                  </div>
                ) : stage.deals.map(deal => (
                  <div
                    key={deal.id}
                    onClick={() => openEdit(deal.id)}
                    style={{
                      background: 'var(--bg-surface)',
                      border: '1px solid var(--border-light)',
                      borderRadius: 'var(--radius-md)',
                      padding: '12px 14px',
                      cursor: 'pointer',
                      transition: 'all 0.15s',
                      position: 'relative',
                    }}
                    onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--brand-primary)'}
                    onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border-light)'}
                  >
                    {deal.company_name && (
                      <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 3 }}>
                        {deal.company_name}
                      </div>
                    )}
                    <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 6, lineHeight: 1.3, paddingRight: 20 }}>
                      {deal.title}
                    </div>
                    <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--brand-primary)' }}>
                      {fmtEUR(deal.total_value)}
                    </div>
                    {deal.created_at && (
                      <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginTop: 4 }}>
                        {deal.created_at.slice(0, 10)}
                      </div>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setDeleteConfirm({ id: deal.id, title: deal.title });
                      }}
                      title="Deal löschen"
                      style={{
                        position: 'absolute', top: 8, right: 8,
                        width: 22, height: 22,
                        background: 'none', border: 'none',
                        cursor: 'pointer',
                        color: 'var(--text-tertiary)',
                        fontSize: 14, lineHeight: 1,
                        borderRadius: 4,
                        opacity: 0.5,
                        transition: 'opacity 0.15s, background 0.15s, color 0.15s',
                        fontFamily: 'var(--font-sans)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                      }}
                      onMouseEnter={e => {
                        e.currentTarget.style.opacity = '1';
                        e.currentTarget.style.background = 'var(--status-danger-bg)';
                        e.currentTarget.style.color = 'var(--status-danger-text)';
                      }}
                      onMouseLeave={e => {
                        e.currentTarget.style.opacity = '0.5';
                        e.currentTarget.style.background = 'none';
                        e.currentTarget.style.color = 'var(--text-tertiary)';
                      }}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {showModal && editingDeal && (
        <DealModal
          deal={editingDeal}
          onClose={() => { setShowModal(false); setEditingDeal(null); }}
          onSaved={() => { setShowModal(false); setEditingDeal(null); loadDeals(); }}
          onRequestDelete={() => setDeleteConfirm({ id: editingDeal.id, title: editingDeal.title || 'Dieser Deal' })}
        />
      )}

      {/* Delete-Confirmation Dialog */}
      {deleteConfirm && createPortal(
        <div
          style={{
            position: 'fixed',
            top: 0, right: 0, bottom: 0, left: 0,
            zIndex: 2100,
            background: 'rgba(15, 28, 32, 0.55)',
            backdropFilter: 'blur(4px)',
            WebkitBackdropFilter: 'blur(4px)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            padding: 20,
            animation: 'dealOverlayIn 0.18s ease',
          }}
          onClick={() => !deleting && setDeleteConfirm(null)}
        >
          <div
            onClick={e => e.stopPropagation()}
            style={{
              position: 'relative',
              background: 'var(--bg-surface)',
              borderRadius: 16,
              padding: '28px 32px',
              maxWidth: 400,
              width: '100%',
              textAlign: 'center',
              boxShadow: '0 32px 80px rgba(0,0,0,0.28), 0 8px 24px rgba(0,0,0,0.14)',
              animation: 'dealModalIn 0.22s cubic-bezier(0.34, 1.56, 0.64, 1)',
            }}
          >
            <div style={{
              width: 56, height: 56, borderRadius: '50%',
              background: 'var(--status-danger-bg)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 26, margin: '0 auto 16px',
            }}>
              🗑️
            </div>
            <h3 style={{
              fontSize: 17, fontWeight: 700,
              color: 'var(--text-primary)', margin: '0 0 8px',
              fontFamily: 'var(--font-sans)',
            }}>
              Deal löschen?
            </h3>
            <p style={{
              fontSize: 13, color: 'var(--text-primary)',
              margin: '0 0 6px', lineHeight: 1.55,
              fontFamily: 'var(--font-sans)',
            }}>
              <strong>{deleteConfirm.title}</strong>
            </p>
            <p style={{
              fontSize: 12, color: 'var(--text-tertiary)',
              margin: '0 0 24px', lineHeight: 1.6,
              fontFamily: 'var(--font-sans)',
            }}>
              Alle Positionen werden ebenfalls gelöscht.
              Diese Aktion kann nicht rückgängig gemacht werden.
            </p>
            <div style={{ display: 'flex', gap: 10 }}>
              <button
                onClick={() => setDeleteConfirm(null)}
                disabled={deleting}
                style={{
                  flex: 1, padding: '10px 0',
                  background: 'var(--bg-app)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border-medium)',
                  borderRadius: 8, fontSize: 13, fontWeight: 500,
                  cursor: deleting ? 'not-allowed' : 'pointer',
                  fontFamily: 'var(--font-sans)',
                }}
              >
                Abbrechen
              </button>
              <button
                onClick={handleDeleteDeal}
                disabled={deleting}
                style={{
                  flex: 1, padding: '10px 0',
                  background: 'var(--status-danger-text)',
                  color: '#fff',
                  border: 'none', borderRadius: 8,
                  fontSize: 13, fontWeight: 700,
                  cursor: deleting ? 'not-allowed' : 'pointer',
                  fontFamily: 'var(--font-sans)',
                  opacity: deleting ? 0.6 : 1,
                }}
              >
                {deleting ? 'Löschen…' : 'Ja, löschen'}
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}


function DealModal({ deal, onClose, onSaved, onRequestDelete }) {
  const { token } = useAuth();
  const { isMobile } = useScreenSize();
  const [form, setForm] = useState({ product_type: 'website', ...deal });
  const [companies, setCompanies] = useState([]);
  const [saving, setSaving] = useState(false);
  const h = { Authorization: `Bearer ${token}` };
  const isEdit = !!deal.id;

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/leads/`, { headers: h })
      .then(r => r.ok ? r.json() : [])
      .then(d => setCompanies(Array.isArray(d) ? d : (d.leads || [])))
      .catch(() => setCompanies([]));
  }, []); // eslint-disable-line

  const total = form.items.reduce(
    (sum, item) => sum + (parseFloat(item.quantity) || 0) * (parseFloat(item.unit_price) || 0),
    0
  );

  const updateItem = (idx, key, val) => {
    const items = [...form.items];
    items[idx] = { ...items[idx], [key]: val };
    setForm({ ...form, items });
  };

  const addItem = () => {
    setForm({ ...form, items: [...form.items, { position: '', quantity: 1, unit_price: 0 }] });
  };

  const removeItem = (idx) => {
    setForm({ ...form, items: form.items.filter((_, i) => i !== idx) });
  };

  const save = async () => {
    if (!form.title?.trim()) {
      toast.error('Titel ist erforderlich');
      return;
    }
    setSaving(true);
    try {
      const payload = {
        title: form.title,
        company_id: form.company_id || null,
        status: form.status || 'neu',
        notes: form.notes || '',
        product_type: form.product_type || 'website',
        items: form.items
          .filter(i => i.position?.trim())
          .map(i => ({
            position: i.position,
            quantity: parseFloat(i.quantity) || 0,
            unit_price: parseFloat(i.unit_price) || 0,
            product_id: i.product_id || null,
            sort_order: i.sort_order || 0,
          })),
      };
      const url = isEdit
        ? `${API_BASE_URL}/api/deals/${deal.id}`
        : `${API_BASE_URL}/api/deals/`;
      const res = await fetch(url, {
        method: isEdit ? 'PUT' : 'POST',
        headers: { ...h, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        toast.success(isEdit ? 'Deal aktualisiert' : 'Deal angelegt');
        onSaved();
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || 'Speichern fehlgeschlagen');
      }
    } catch { toast.error('Verbindungsfehler'); }
    setSaving(false);
  };

  const handleDelete = () => {
    if (!isEdit) return;
    // Delegate to parent confirmation dialog
    if (onRequestDelete) onRequestDelete();
  };

  const createProject = async () => {
    if (!isEdit) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/deals/${deal.id}/create-project`, {
        method: 'POST', headers: h,
      });
      if (res.ok) {
        const d = await res.json();
        toast.success(d.already_exists ? 'Projekt existiert bereits' : 'Projekt angelegt');
        window.location.href = `/app/projects/${d.project_id}`;
      }
    } catch { toast.error('Projekt-Anlage fehlgeschlagen'); }
  };

  const inputStyle = {
    width: '100%', boxSizing: 'border-box', padding: '9px 12px',
    border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)',
    background: 'var(--bg-app)', color: 'var(--text-primary)',
    fontSize: 13, fontFamily: 'var(--font-sans)', outline: 'none',
  };
  const labelStyle = { fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5, display: 'block' };

  return createPortal(
    <div
      onClick={e => e.target === e.currentTarget && onClose()}
      style={{
        position: 'fixed',
        top: 0, right: 0, bottom: 0, left: 0,
        zIndex: 2000,
        background: 'rgba(0,0,0,0.55)',
        backdropFilter: 'blur(4px)',
        WebkitBackdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 16,
        animation: 'dealOverlayIn 0.18s ease',
      }}
    >
      <style>{`
        @keyframes dealOverlayIn {
          from { opacity: 0; }
          to   { opacity: 1; }
        }
        @keyframes dealModalIn {
          from { opacity: 0; transform: scale(0.96) translateY(8px); }
          to   { opacity: 1; transform: scale(1) translateY(0); }
        }
      `}</style>
      <div style={{
        position: 'relative',
        background: 'var(--bg-surface)', borderRadius: 16,
        width: '100%', maxWidth: 780, maxHeight: '90vh',
        display: 'flex', flexDirection: 'column', overflow: 'hidden',
        boxShadow: '0 32px 80px rgba(0,0,0,0.28), 0 8px 24px rgba(0,0,0,0.14)',
        animation: 'dealModalIn 0.22s cubic-bezier(0.34, 1.56, 0.64, 1)',
      }}>
        {/* Header */}
        <div style={{ padding: '20px 28px', borderBottom: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--brand-primary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 3 }}>
              {isEdit ? 'Deal bearbeiten' : 'Neuer Deal'}
            </div>
            <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)' }}>
              {form.title || 'Unbenannter Deal'}
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'var(--bg-app)', border: '1px solid var(--border-light)', width: 32, height: 32, borderRadius: 8, cursor: 'pointer', fontSize: 18, color: 'var(--text-secondary)' }}>×</button>
        </div>

        {/* Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: 24 }}>

          {/* Produkttyp */}
          <div style={{ marginBottom: 16 }}>
            <label style={labelStyle}>Produkttyp</label>
            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 8 }}>
              {[
                { value: 'website', label: '🌐 Online Fertig', sub: 'Website-Paket · Stripe-Checkout möglich' },
                { value: 'impuls',  label: '📋 IMPULS',        sub: 'ISB-158 Beratung · Angebot/Annahme' },
              ].map(opt => (
                <div
                  key={opt.value}
                  onClick={() => setForm(f => ({ ...f, product_type: opt.value }))}
                  style={{
                    padding: '10px 12px', borderRadius: 8, cursor: 'pointer',
                    border: `2px solid ${form.product_type === opt.value ? (opt.value === 'impuls' ? '#004F59' : 'var(--brand-primary)') : 'var(--border-light)'}`,
                    background: form.product_type === opt.value ? (opt.value === 'impuls' ? '#004F5910' : 'var(--bg-active)') : 'var(--bg-surface)',
                  }}
                >
                  <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 3 }}>{opt.label}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{opt.sub}</div>
                </div>
              ))}
            </div>
            {form.product_type === 'impuls' && (
              <div style={{ marginTop: 8, padding: '8px 12px', background: '#FAE60015', border: '1px solid #FAE60060', borderRadius: 6, fontSize: 12, color: '#854F0B' }}>
                ⚠️ IMPULS läuft über Angebot/Annahme — kein Stripe-Checkout. Deal erst auf "Gewonnen" setzen wenn ISB-Antrag bewilligt ist.
              </div>
            )}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '2fr 1fr', gap: 14, marginBottom: 14 }}>
            <div>
              <label style={labelStyle}>Titel *</label>
              <input style={inputStyle} value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} placeholder="z.B. Website-Relaunch Müller GmbH" />
            </div>
            <div>
              <label style={labelStyle}>Status</label>
              <select style={inputStyle} value={form.status} onChange={e => setForm({ ...form, status: e.target.value })}>
                {STAGES.map(s => <option key={s.key} value={s.key}>{s.label}</option>)}
              </select>
            </div>
          </div>

          <div style={{ marginBottom: 14 }}>
            <label style={labelStyle}>Unternehmen</label>
            <select style={inputStyle} value={form.company_id || ''} onChange={e => setForm({ ...form, company_id: e.target.value ? parseInt(e.target.value) : null })}>
              <option value="">— Kein Unternehmen —</option>
              {companies.map(c => <option key={c.id} value={c.id}>{c.company_name || `Lead #${c.id}`}</option>)}
            </select>
          </div>

          <div style={{ marginBottom: 14 }}>
            <label style={labelStyle}>Notizen</label>
            <textarea style={{ ...inputStyle, minHeight: 70, resize: 'vertical' }} value={form.notes || ''} onChange={e => setForm({ ...form, notes: e.target.value })} placeholder="Interne Notizen zum Deal…" />
          </div>

          {/* Positionen */}
          <div style={{ marginTop: 20, marginBottom: 14 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
              <label style={labelStyle}>Positionen</label>
              <button onClick={addItem} style={{ fontSize: 11, color: 'var(--brand-primary)', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 600 }}>+ Position hinzufügen</button>
            </div>

            <div style={{ background: 'var(--bg-app)', borderRadius: 'var(--radius-md)', padding: 12, border: '1px solid var(--border-light)', overflowX: 'auto' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 80px 110px 110px 36px', gap: 8, fontSize: 10, color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6, padding: '0 4px', minWidth: isMobile ? 440 : undefined }}>
                <div>Position</div>
                <div style={{ textAlign: 'right' }}>Menge</div>
                <div style={{ textAlign: 'right' }}>EP €</div>
                <div style={{ textAlign: 'right' }}>GP €</div>
                <div></div>
              </div>
              {form.items.map((item, i) => (
                <div key={i} style={{ display: 'grid', gridTemplateColumns: '1fr 80px 110px 110px 36px', gap: 8, marginBottom: 6, alignItems: 'center', minWidth: isMobile ? 440 : undefined }}>
                  <input
                    style={{ ...inputStyle, padding: '7px 10px', fontSize: 12 }}
                    value={item.position}
                    onChange={e => updateItem(i, 'position', e.target.value)}
                    placeholder="z.B. Website-Design"
                  />
                  <input
                    type="number" step="0.5"
                    style={{ ...inputStyle, padding: '7px 10px', fontSize: 12, textAlign: 'right' }}
                    value={item.quantity}
                    onChange={e => updateItem(i, 'quantity', e.target.value)}
                  />
                  <input
                    type="number" step="0.01"
                    style={{ ...inputStyle, padding: '7px 10px', fontSize: 12, textAlign: 'right' }}
                    value={item.unit_price}
                    onChange={e => updateItem(i, 'unit_price', e.target.value)}
                  />
                  <div style={{ textAlign: 'right', fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', padding: '7px 4px' }}>
                    {fmtEUR((parseFloat(item.quantity) || 0) * (parseFloat(item.unit_price) || 0))}
                  </div>
                  <button
                    onClick={() => removeItem(i)}
                    disabled={form.items.length <= 1}
                    style={{ background: 'none', border: 'none', color: 'var(--text-tertiary)', cursor: form.items.length <= 1 ? 'not-allowed' : 'pointer', fontSize: 16, opacity: form.items.length <= 1 ? 0.3 : 1 }}
                    title="Position entfernen"
                  >×</button>
                </div>
              ))}
              <div style={{ borderTop: '1px solid var(--border-light)', paddingTop: 10, marginTop: 10, display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 12 }}>
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>Gesamt:</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--brand-primary)' }}>{fmtEUR(total)}</div>
              </div>
            </div>
          </div>

          {/* Gewonnen → Projekt anlegen */}
          {isEdit && form.status === 'gewonnen' && (
            <div style={{ marginTop: 14, padding: 14, background: 'var(--status-success-bg)', borderRadius: 'var(--radius-md)', border: '1px solid var(--status-success-text)' }}>
              <div style={{ fontSize: 12, color: 'var(--status-success-text)', fontWeight: 600, marginBottom: 8 }}>
                ✓ Deal gewonnen — Projekt starten?
              </div>
              <button onClick={createProject} style={{ padding: '8px 18px', background: 'var(--status-success-text)', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>
                📋 Projekt anlegen
              </button>
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{ padding: '16px 28px', borderTop: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'var(--bg-surface)' }}>
          {isEdit ? (
            <button onClick={handleDelete} style={{ padding: '9px 16px', background: 'none', border: '1px solid var(--status-danger-text)', color: 'var(--status-danger-text)', borderRadius: 'var(--radius-md)', fontSize: 12, cursor: 'pointer' }}>
              Löschen
            </button>
          ) : <div />}
          <div style={{ display: 'flex', gap: 10 }}>
            <button onClick={onClose} style={{ padding: '9px 18px', background: 'var(--bg-app)', border: '1px solid var(--border-light)', color: 'var(--text-secondary)', borderRadius: 'var(--radius-md)', fontSize: 13, cursor: 'pointer' }}>
              Abbrechen
            </button>
            <button
              onClick={save}
              disabled={saving}
              style={{ padding: '9px 22px', background: saving ? 'var(--text-tertiary)' : 'var(--brand-primary)', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600, cursor: saving ? 'wait' : 'pointer' }}
            >
              {saving ? 'Speichern…' : 'Speichern'}
            </button>
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}
