import React, { useState, useEffect, useRef } from 'react';
import toast from 'react-hot-toast';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

export default function ProductManager() {
  const { token } = useAuth();
  const fetchedRef = useRef(false);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [editProduct, setEditProduct] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const emptyForm = { name: '', beschreibung: '', leistungsumfang: '', typ: 'paket', zielgruppe: 'oeffentlich', preis_einmalig: '', preis_monatlich: '', landing_page_url: '', sort_order: 0 };
  const [form, setForm] = useState(emptyForm);

  const mkH = () => ({ 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) });

  const load = () => fetch(`${API_BASE_URL}/api/products/`, { headers: mkH() })
    .then(r => r.json()).then(d => setProducts(Array.isArray(d) ? d : []))
    .catch(() => toast.error('Produkte konnten nicht geladen werden'));

  useEffect(() => { if (fetchedRef.current) return; fetchedRef.current = true; load().finally(() => setLoading(false)); }, []); // eslint-disable-line

  const save = async () => {
    if (!form.name.trim()) { toast.error('Name erforderlich'); return; }
    setSubmitting(true);
    try {
      const body = { ...form };
      if (body.preis_einmalig) body.preis_einmalig = parseInt(body.preis_einmalig);
      else delete body.preis_einmalig;
      if (body.preis_monatlich) body.preis_monatlich = parseInt(body.preis_monatlich);
      else delete body.preis_monatlich;

      const url = editProduct ? `${API_BASE_URL}/api/products/${editProduct.id}` : `${API_BASE_URL}/api/products/`;
      const method = editProduct ? 'PUT' : 'POST';
      const r = await fetch(url, { method, headers: mkH(), body: JSON.stringify(body) });
      if (r.ok) { toast.success(editProduct ? 'Gespeichert' : 'Produkt erstellt'); setShowCreate(false); setEditProduct(null); setForm(emptyForm); load(); }
      else toast.error((await r.json()).detail || 'Fehler');
    } catch { toast.error('Speichern fehlgeschlagen'); }
    setSubmitting(false);
  };

  const del = async (id) => {
    if (!window.confirm('Produkt loeschen?')) return;
    const r = await fetch(`${API_BASE_URL}/api/products/${id}`, { method: 'DELETE', headers: mkH() });
    if (r.ok) { toast.success('Geloescht'); load(); }
    else toast.error((await r.json()).detail || 'Fehler');
  };

  const stripeConnect = async (id) => {
    toast.loading('Stripe wird verbunden...', { id: 'stripe' });
    try {
      const r = await fetch(`${API_BASE_URL}/api/products/${id}/stripe-connect`, { method: 'POST', headers: mkH() });
      if (r.ok) { const d = await r.json(); toast.success(`Stripe verbunden: ${d.stripe_payment_link || 'OK'}`, { id: 'stripe' }); load(); }
      else { toast.error((await r.json()).detail || 'Stripe Fehler', { id: 'stripe' }); }
    } catch { toast.error('Stripe-Verbindung fehlgeschlagen', { id: 'stripe' }); }
  };

  const toggleLive = async (id) => {
    const r = await fetch(`${API_BASE_URL}/api/products/${id}/toggle-live`, { method: 'POST', headers: mkH() });
    if (r.ok) { const d = await r.json(); toast.success(d.ist_live ? 'Produkt ist jetzt live' : 'Produkt zurueck auf Entwurf'); load(); }
    else toast.error('Fehler');
  };

  const openEdit = (p) => {
    setForm({ name: p.name || '', beschreibung: p.beschreibung || '', leistungsumfang: p.leistungsumfang || '', typ: p.typ || 'paket', zielgruppe: p.zielgruppe || 'oeffentlich', preis_einmalig: p.preis_einmalig || '', preis_monatlich: p.preis_monatlich || '', landing_page_url: p.landing_page_url || '', sort_order: p.sort_order || 0 });
    setEditProduct(p);
    setShowCreate(true);
  };

  const fmtPrice = (v) => v ? `${(v / 100).toFixed(2)} EUR` : '-';

  const card = { background: 'var(--bg-surface)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' };
  const btnPrimary = { background: 'var(--brand-primary)', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)' };
  const btnSecondary = { background: 'transparent', color: 'var(--text-secondary)', border: '1px solid var(--border-light)', padding: '6px 12px', borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)' };
  const overlay = { position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center' };
  const modal = { background: 'var(--bg-surface)', borderRadius: 12, padding: 28, width: '100%', maxWidth: 560, maxHeight: '90vh', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 14 };
  const input = { width: '100%', padding: '8px 12px', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', fontSize: 13, fontFamily: 'var(--font-sans)', background: 'var(--bg-surface)', color: 'var(--text-primary)', boxSizing: 'border-box' };
  const label = { fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)', display: 'block', marginBottom: 4 };
  const thStyle = { fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-tertiary)' };

  if (loading) return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '40vh', color: 'var(--text-tertiary)', fontSize: 14 }}>Laden...</div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>Produkte & Pakete</h1>
        <button style={btnPrimary} onClick={() => { setForm(emptyForm); setEditProduct(null); setShowCreate(true); }}>+ Neues Produkt</button>
      </div>

      {/* Product cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 14 }}>
        {products.map(p => (
          <div key={p.id} style={{ ...card, padding: 20, display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)' }}>{p.name}</div>
                <div style={{ fontSize: 11, color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', marginTop: 2 }}>/{p.slug}</div>
              </div>
              <span style={{ padding: '2px 10px', borderRadius: 999, fontSize: 11, fontWeight: 500, background: p.ist_live ? 'var(--status-success-bg)' : 'var(--bg-app)', color: p.ist_live ? 'var(--status-success-text)' : 'var(--text-secondary)' }}>
                {p.ist_live ? 'Live' : 'Entwurf'}
              </span>
            </div>

            {p.beschreibung && <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{p.beschreibung.slice(0, 120)}{p.beschreibung.length > 120 ? '...' : ''}</div>}

            <div style={{ display: 'flex', gap: 16, fontSize: 12 }}>
              {p.preis_einmalig && <div><span style={{ color: 'var(--text-tertiary)' }}>Einmalig:</span> <strong>{fmtPrice(p.preis_einmalig)}</strong></div>}
              {p.preis_monatlich && <div><span style={{ color: 'var(--text-tertiary)' }}>Monatlich:</span> <strong>{fmtPrice(p.preis_monatlich)}</strong></div>}
            </div>

            {p.stripe_payment_link && (
              <div style={{ fontSize: 11, color: 'var(--brand-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                Stripe: {p.stripe_payment_link}
              </div>
            )}

            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 'auto', paddingTop: 8, borderTop: '1px solid var(--border-light)' }}>
              <button style={btnSecondary} onClick={() => openEdit(p)}>Bearbeiten</button>
              <button style={btnSecondary} onClick={() => toggleLive(p.id)}>{p.ist_live ? 'Deaktivieren' : 'Aktivieren'}</button>
              {!p.stripe_product_id && <button style={{ ...btnSecondary, color: 'var(--brand-primary)', borderColor: 'var(--brand-primary)' }} onClick={() => stripeConnect(p.id)}>Stripe verbinden</button>}
              {!p.ist_live && <button style={{ ...btnSecondary, color: 'var(--status-danger-text)', borderColor: 'var(--status-danger-text)' }} onClick={() => del(p.id)}>Loeschen</button>}
            </div>
          </div>
        ))}
        {products.length === 0 && (
          <div style={{ ...card, padding: 40, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13, gridColumn: '1 / -1' }}>Noch keine Produkte vorhanden.</div>
        )}
      </div>

      {/* Create/Edit Modal */}
      {showCreate && (
        <div style={overlay} onClick={e => e.target === e.currentTarget && setShowCreate(false)}>
          <div style={modal}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>{editProduct ? 'Produkt bearbeiten' : 'Neues Produkt'}</h3>
            <div><label style={label}>Name</label><input style={input} value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} placeholder="z.B. KOMPAGNON Starter" /></div>
            <div><label style={label}>Beschreibung</label><textarea style={{ ...input, minHeight: 60, resize: 'vertical' }} value={form.beschreibung} onChange={e => setForm(f => ({ ...f, beschreibung: e.target.value }))} /></div>
            <div><label style={label}>Leistungsumfang</label><textarea style={{ ...input, minHeight: 80, resize: 'vertical' }} value={form.leistungsumfang} onChange={e => setForm(f => ({ ...f, leistungsumfang: e.target.value }))} placeholder="Bullet Points der Leistungen" /></div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              <div><label style={label}>Typ</label><select style={input} value={form.typ} onChange={e => setForm(f => ({ ...f, typ: e.target.value }))}><option value="paket">Paket</option><option value="retainer">Retainer</option><option value="addon">Add-on</option></select></div>
              <div><label style={label}>Zielgruppe</label><select style={input} value={form.zielgruppe} onChange={e => setForm(f => ({ ...f, zielgruppe: e.target.value }))}><option value="oeffentlich">Oeffentlich</option><option value="intern">Intern</option></select></div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              <div><label style={label}>Preis einmalig (Cent)</label><input style={input} type="number" value={form.preis_einmalig} onChange={e => setForm(f => ({ ...f, preis_einmalig: e.target.value }))} placeholder="249000" /></div>
              <div><label style={label}>Preis monatlich (Cent)</label><input style={input} type="number" value={form.preis_monatlich} onChange={e => setForm(f => ({ ...f, preis_monatlich: e.target.value }))} placeholder="8900" /></div>
            </div>
            <div><label style={label}>Landing Page URL</label><input style={input} value={form.landing_page_url} onChange={e => setForm(f => ({ ...f, landing_page_url: e.target.value }))} placeholder="https://kompagnon.eu/paket/..." /></div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button style={btnSecondary} onClick={() => { setShowCreate(false); setEditProduct(null); }}>Abbrechen</button>
              <button style={btnPrimary} onClick={save} disabled={submitting}>{submitting ? 'Speichern...' : 'Speichern'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
