import React, { useState, useEffect } from 'react';
import { useScreenSize } from '../utils/responsive';

const N = '#0F1E3A';
const STAGES = [
  { id: 'idea', label: 'Idee', icon: '💡', color: '#7c3aed', bg: '#faf5ff' },
  { id: 'planned', label: 'Geplant', icon: '📋', color: '#2563eb', bg: '#eff6ff' },
  { id: 'in_progress', label: 'In Entwicklung', icon: '⚙️', color: '#d97706', bg: '#fffbeb' },
  { id: 'testing', label: 'Testing', icon: '🧪', color: '#0891b2', bg: '#ecfeff' },
  { id: 'done', label: 'Fertig', icon: '✅', color: '#059669', bg: '#f0fdf4' },
];
const CATS = [
  { id: 'feature', label: 'Feature', icon: '⭐', color: '#2563eb' },
  { id: 'bug', label: 'Bug Fix', icon: '🐛', color: '#dc2626' },
  { id: 'improvement', label: 'Verbesserung', icon: '🔧', color: '#d97706' },
  { id: 'design', label: 'Design', icon: '🎨', color: '#7c3aed' },
  { id: 'integration', label: 'Integration', icon: '🔗', color: '#059669' },
];
const PRIOS = [{ id: 'low', label: 'Niedrig', color: '#64748b' }, { id: 'medium', label: 'Mittel', color: '#d97706' }, { id: 'high', label: 'Hoch', color: '#dc2626' }];
const KEY = 'kompagnon_product_items';
const load = () => { try { return JSON.parse(localStorage.getItem(KEY) || '[]'); } catch { return []; } };
const save = (items) => localStorage.setItem(KEY, JSON.stringify(items));

export default function ProductDevelopment() {
  const { isMobile } = useScreenSize();
  const [items, setItems] = useState(load);
  const [showForm, setShowForm] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [dragging, setDragging] = useState(null);
  const [dragOver, setDragOver] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  const [form, setForm] = useState({ title: '', description: '', category: 'feature', priority: 'medium', stage: 'idea', due_date: '', tags: '', ticket_ref: '' });

  useEffect(() => { save(items); }, [items]);

  const openForm = (stage = 'idea', item = null) => {
    if (item) { setForm({ ...item, tags: Array.isArray(item.tags) ? item.tags.join(', ') : item.tags || '' }); setEditItem(item); }
    else { setForm((p) => ({ ...p, stage, title: '', description: '', tags: '', ticket_ref: '' })); setEditItem(null); }
    setShowForm(true);
  };

  const saveItem = () => {
    if (!form.title) return;
    const proc = { ...form, tags: form.tags ? form.tags.split(',').map((t) => t.trim()).filter(Boolean) : [] };
    if (editItem) setItems((p) => p.map((i) => (i.id === editItem.id ? { ...proc, id: editItem.id } : i)));
    else setItems((p) => [...p, { ...proc, id: Date.now().toString(), created_at: new Date().toISOString().slice(0, 10) }]);
    setShowForm(false); setEditItem(null);
  };

  const deleteItem = (id) => setItems((p) => p.filter((i) => i.id !== id));
  const moveItem = (id, stage) => setItems((p) => p.map((i) => (i.id === id ? { ...i, stage } : i)));
  const handleDragStart = (e, item) => { setDragging(item); e.dataTransfer.effectAllowed = 'move'; };
  const handleDrop = (e, stageId) => { e.preventDefault(); if (dragging && dragging.stage !== stageId) moveItem(dragging.id, stageId); setDragging(null); setDragOver(null); };

  const getStageItems = (stageId) => items.filter((i) => i.stage === stageId);
  const stats = { total: items.length, wip: items.filter((i) => i.stage === 'in_progress').length, done: items.filter((i) => i.stage === 'done').length, high: items.filter((i) => i.priority === 'high' && i.stage !== 'done').length };

  const inp = { width: '100%', padding: '10px 12px', border: '1.5px solid #e2e8f0', borderRadius: 8, fontSize: 13, boxSizing: 'border-box', outline: 'none' };

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: N, margin: '0 0 4px' }}>Produktentwicklung</h1>
          <p style={{ fontSize: 13, color: '#64748b', margin: 0 }}>Roadmap & Feature-Planung</p>
        </div>
        <button onClick={() => openForm()} style={{ background: N, color: '#fff', border: 'none', borderRadius: 8, padding: '9px 18px', fontSize: 13, fontWeight: 700, cursor: 'pointer' }}>+ Neues Feature</button>
      </div>

      {/* KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 10, marginBottom: 20 }}>
        {[{ l: 'Gesamt', v: stats.total, c: '#2563eb', i: '📦' }, { l: 'In Entwicklung', v: stats.wip, c: '#d97706', i: '⚙️' }, { l: 'Abgeschlossen', v: stats.done, c: '#059669', i: '✅' }, { l: 'Hohe Prio', v: stats.high, c: '#dc2626', i: '🔴' }].map((k) => (
          <div key={k.l} style={{ background: '#fff', borderRadius: 10, padding: '14px 16px', border: '1px solid #e2e8f0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}><span style={{ fontSize: 20 }}>{k.i}</span><span style={{ fontSize: 22, fontWeight: 900, color: k.c }}>{k.v}</span></div>
            <div style={{ fontSize: 11, fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{k.l}</div>
          </div>
        ))}
      </div>

      {/* Board */}
      {isMobile ? (
        <div>
          <div style={{ display: 'flex', gap: 6, overflowX: 'auto', paddingBottom: 4, marginBottom: 16, scrollbarWidth: 'none' }}>
            {STAGES.map((s, idx) => (
              <button key={s.id} onClick={() => setActiveTab(idx)} style={{
                flexShrink: 0, padding: '8px 14px', borderRadius: 20, border: 'none',
                background: activeTab === idx ? s.color : '#f1f5f9', color: activeTab === idx ? '#fff' : '#475569',
                fontSize: 13, fontWeight: 600, cursor: 'pointer', minHeight: 36, whiteSpace: 'nowrap',
              }}>{s.icon} {s.label} ({getStageItems(s.id).length})</button>
            ))}
          </div>
          <div>
            {getStageItems(STAGES[activeTab].id).map((item) => <ItemCard key={item.id} item={item} onEdit={() => openForm(item.stage, item)} onDelete={() => deleteItem(item.id)} onDragStart={() => {}} />)}
            <button onClick={() => openForm(STAGES[activeTab].id)} style={{ width: '100%', padding: 10, background: 'none', border: '1.5px dashed #e2e8f0', borderRadius: 8, color: '#64748b', fontSize: 12, fontWeight: 600, cursor: 'pointer', marginTop: 8, minHeight: 44 }}>+ Hinzufuegen</button>
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', gap: 12, width: '100%', alignItems: 'flex-start' }}>
          {STAGES.map((stage) => {
            const si = getStageItems(stage.id);
            const over = dragOver === stage.id;
            return (
              <div key={stage.id} onDragOver={(e) => { e.preventDefault(); setDragOver(stage.id); }} onDrop={(e) => handleDrop(e, stage.id)} onDragLeave={() => setDragOver(null)}
                style={{ flex: '1 1 0', minWidth: 170, background: over ? stage.bg : '#f8fafc', borderRadius: 12, border: over ? `2px dashed ${stage.color}` : '2px solid transparent', transition: 'all 0.15s' }}>
                <div style={{ padding: '12px 14px 0', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, minWidth: 0 }}>
                    <span style={{ fontSize: 14 }}>{stage.icon}</span>
                    <span style={{ fontSize: 12, fontWeight: 700, color: N, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{stage.label}</span>
                  </div>
                  <span style={{ background: stage.color + '20', color: stage.color, borderRadius: 20, padding: '2px 7px', fontSize: 11, fontWeight: 700 }}>{si.length}</span>
                </div>
                <div style={{ height: 3, background: stage.color, margin: '8px 14px', borderRadius: 2 }} />
                <div style={{ padding: '0 8px 8px', display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {si.map((item) => <ItemCard key={item.id} item={item} onEdit={() => openForm(item.stage, item)} onDelete={() => deleteItem(item.id)} onDragStart={handleDragStart} />)}
                  <button onClick={() => openForm(stage.id)} style={{ width: '100%', padding: 8, background: 'none', border: `1.5px dashed ${stage.color}50`, borderRadius: 8, color: stage.color, fontSize: 12, fontWeight: 600, cursor: 'pointer', minHeight: 36 }}>+ Hinzufuegen</button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Form Modal */}
      {showForm && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }} onClick={(e) => { if (e.target === e.currentTarget) setShowForm(false); }}>
          <div style={{ background: '#fff', borderRadius: 16, width: '100%', maxWidth: 520, maxHeight: '90vh', overflowY: 'auto', boxShadow: '0 20px 60px rgba(0,0,0,0.2)' }}>
            <div style={{ background: N, padding: '16px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderRadius: '16px 16px 0 0' }}>
              <span style={{ color: '#fff', fontWeight: 800, fontSize: 15 }}>{editItem ? 'Bearbeiten' : 'Neues Feature'}</span>
              <button onClick={() => setShowForm(false)} style={{ background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: '50%', width: 28, height: 28, color: '#fff', cursor: 'pointer', fontSize: 14, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>✕</button>
            </div>
            <div style={{ padding: 20 }}>
              <Lbl>Titel *</Lbl><input value={form.title} onChange={(e) => setForm((p) => ({ ...p, title: e.target.value }))} placeholder="Feature-Titel..." style={{ ...inp, marginBottom: 14 }} />
              <Lbl>Beschreibung</Lbl><textarea value={form.description} onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))} placeholder="Details..." rows={3} style={{ ...inp, resize: 'vertical', marginBottom: 14 }} />
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 14 }}>
                <div><Lbl>Kategorie</Lbl><select value={form.category} onChange={(e) => setForm((p) => ({ ...p, category: e.target.value }))} style={inp}>{CATS.map((c) => <option key={c.id} value={c.id}>{c.icon} {c.label}</option>)}</select></div>
                <div><Lbl>Phase</Lbl><select value={form.stage} onChange={(e) => setForm((p) => ({ ...p, stage: e.target.value }))} style={inp}>{STAGES.map((s) => <option key={s.id} value={s.id}>{s.icon} {s.label}</option>)}</select></div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 14 }}>
                <div><Lbl>Prioritaet</Lbl><select value={form.priority} onChange={(e) => setForm((p) => ({ ...p, priority: e.target.value }))} style={inp}>{PRIOS.map((p) => <option key={p.id} value={p.id}>{p.label}</option>)}</select></div>
                <div><Lbl>Faellig am</Lbl><input type="date" value={form.due_date} onChange={(e) => setForm((p) => ({ ...p, due_date: e.target.value }))} style={inp} /></div>
              </div>
              <Lbl>Ticket-Referenz</Lbl><input value={form.ticket_ref} onChange={(e) => setForm((p) => ({ ...p, ticket_ref: e.target.value }))} placeholder="TKT-2603-1234" style={{ ...inp, marginBottom: 14 }} />
              <Lbl>Tags (kommagetrennt)</Lbl><input value={form.tags} onChange={(e) => setForm((p) => ({ ...p, tags: e.target.value }))} placeholder="frontend, api..." style={{ ...inp, marginBottom: 20 }} />
              <div style={{ display: 'flex', gap: 10 }}>
                <button onClick={() => setShowForm(false)} style={{ flex: 1, padding: 11, background: '#f1f5f9', color: N, border: 'none', borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: 'pointer', minHeight: 44 }}>Abbrechen</button>
                <button onClick={saveItem} disabled={!form.title} style={{ flex: 2, padding: 11, background: !form.title ? '#64748b' : N, color: '#fff', border: 'none', borderRadius: 8, fontSize: 14, fontWeight: 700, cursor: !form.title ? 'not-allowed' : 'pointer', minHeight: 44 }}>{editItem ? 'Speichern' : '+ Anlegen'}</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ItemCard({ item, onEdit, onDelete, onDragStart }) {
  const cat = CATS.find((c) => c.id === item.category);
  const prio = PRIOS.find((p) => p.id === item.priority);
  return (
    <div draggable onDragStart={(e) => onDragStart(e, item)} style={{ background: '#fff', borderRadius: 8, border: '1px solid #e2e8f0', padding: '10px 12px', cursor: 'grab', boxShadow: '0 1px 3px rgba(0,0,0,0.06)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6, gap: 4 }}>
        <span style={{ fontSize: 10, fontWeight: 700, color: cat?.color || '#64748b', background: (cat?.color || '#64748b') + '15', padding: '2px 6px', borderRadius: 4 }}>{cat?.icon} {cat?.label}</span>
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: prio?.color || '#64748b', flexShrink: 0 }} title={prio?.label} />
      </div>
      <div style={{ fontSize: 12, fontWeight: 700, color: '#0F1E3A', marginBottom: 4, lineHeight: 1.3 }}>{item.title}</div>
      {item.description && <div style={{ fontSize: 11, color: '#64748b', lineHeight: 1.4, marginBottom: 6, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>{item.description}</div>}
      {item.tags?.length > 0 && <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 6 }}>{item.tags.map((t) => <span key={t} style={{ fontSize: 10, color: '#64748b', background: '#f1f5f9', padding: '1px 6px', borderRadius: 4 }}>#{t}</span>)}</div>}
      {item.ticket_ref && <div style={{ fontSize: 10, color: '#008EAA', marginBottom: 6 }}>🎫 {item.ticket_ref}</div>}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: 6, borderTop: '1px solid #f1f5f9' }}>
        <span style={{ fontSize: 10, color: '#94a3b8' }}>{item.due_date || item.created_at || ''}</span>
        <div style={{ display: 'flex', gap: 4 }}>
          <button onClick={(e) => { e.stopPropagation(); onEdit(); }} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 12, padding: '2px 4px', color: '#64748b' }}>✏️</button>
          <button onClick={(e) => { e.stopPropagation(); onDelete(); }} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 12, padding: '2px 4px', color: '#94a3b8' }}>🗑️</button>
        </div>
      </div>
    </div>
  );
}

function Lbl({ children }) { return <div style={{ fontSize: 11, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>{children}</div>; }
