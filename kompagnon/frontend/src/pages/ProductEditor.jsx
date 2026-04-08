import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

export default function ProductEditor() {
  const [products, setProducts] = useState([]);
  const [selected, setSelected] = useState(null);
  const [product, setProduct] = useState(null);
  const [activeTab, setActiveTab] = useState('produktdaten');
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');
  const { token } = useAuth();
  const h = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };

  useEffect(() => { loadProducts(); }, []); // eslint-disable-line

  const loadProducts = async () => {
    try {
      const r = await fetch(`${API_BASE_URL}/api/products/`, { headers: h });
      if (r.ok) setProducts(await r.json());
    } catch {}
  };

  const selectProduct = (p) => {
    setSelected(p.slug);
    setProduct({ ...p, features: Array.isArray(p.features) ? p.features : [] });
    setActiveTab('produktdaten');
    setMsg('');
  };

  const newProduct = () => {
    setSelected('__new__');
    setProduct({
      slug: '', name: '', short_desc: '', long_desc: '',
      price_brutto: 0, price_netto: 0, tax_rate: 19,
      payment_type: 'once', delivery_days: 14,
      highlighted: false, highlight_label: 'Empfehlung',
      features: [],
      checkout_fields: ['name', 'company', 'email', 'phone'],
      webhook_actions: ['create_lead', 'create_user', 'create_project', 'send_welcome_email', 'send_pdf'],
      status: 'draft', sort_order: 0,
    });
    setActiveTab('produktdaten');
    setMsg('');
  };

  const save = async () => {
    setSaving(true); setMsg('');
    try {
      const isNew = selected === '__new__';
      const url = isNew ? `${API_BASE_URL}/api/products/` : `${API_BASE_URL}/api/products/${selected}`;
      const r = await fetch(url, { method: isNew ? 'POST' : 'PUT', headers: h, body: JSON.stringify(product) });
      const d = await r.json();
      if (!r.ok) { setMsg(d.detail || 'Fehler'); return; }
      setMsg('\u2713 Gespeichert');
      await loadProducts();
      setSelected(d.slug);
      setProduct({ ...d, features: Array.isArray(d.features) ? d.features : [] });
    } catch { setMsg('Verbindungsfehler'); }
    finally { setSaving(false); }
  };

  const set = (k, v) => setProduct(p => ({ ...p, [k]: v }));

  const TABS = [
    { id: 'produktdaten', label: 'Produktdaten' },
    { id: 'preis', label: 'Preis & Stripe' },
    { id: 'checkout', label: 'Checkout' },
    { id: 'assets', label: 'Assets & URLs' },
    { id: 'checkliste', label: 'Checkliste' },
  ];

  // Styles
  const inputS = { width: '100%', padding: '8px 12px', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', fontSize: 13, fontFamily: 'var(--font-sans)', background: 'var(--bg-surface)', color: 'var(--text-primary)', boxSizing: 'border-box' };
  const labelS = { fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 4, display: 'block' };
  const statusDot = (s) => ({ width: 8, height: 8, borderRadius: '50%', background: s === 'live' ? '#22C55E' : s === 'archived' ? '#EF4444' : '#94a3b8', flexShrink: 0 });

  return (
    <div style={{ display: 'flex', gap: 0, height: 'calc(100vh - 100px)', overflow: 'hidden' }}>
      {/* ── Left: Product list ──────────────────────────────────── */}
      <div style={{ width: 260, flexShrink: 0, borderRight: '1px solid var(--border-light)', display: 'flex', flexDirection: 'column', overflowY: 'auto', background: 'var(--bg-surface)' }}>
        <div style={{ padding: '14px 16px', borderBottom: '1px solid var(--border-light)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>Produkte</span>
          <button onClick={newProduct} style={{ padding: '4px 10px', border: 'none', borderRadius: 'var(--radius-md)', background: 'var(--brand-primary)', color: '#fff', fontSize: 11, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>+ Neu</button>
        </div>
        {products.map(p => (
          <div key={p.slug} onClick={() => selectProduct(p)} style={{
            padding: '10px 16px', cursor: 'pointer', borderBottom: '1px solid var(--border-light)',
            background: selected === p.slug ? 'var(--bg-active)' : 'transparent',
            borderLeft: selected === p.slug ? '3px solid var(--brand-primary)' : '3px solid transparent',
          }}
            onMouseEnter={e => { if (selected !== p.slug) e.currentTarget.style.background = 'var(--bg-hover)'; }}
            onMouseLeave={e => { if (selected !== p.slug) e.currentTarget.style.background = 'transparent'; }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div style={statusDot(p.status)} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.name}</div>
                <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{p.price_brutto ? `${Number(p.price_brutto).toFixed(2)} EUR` : '\u2014'}</div>
              </div>
            </div>
          </div>
        ))}
        {products.length === 0 && <div style={{ padding: 20, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 12 }}>Keine Produkte</div>}
      </div>

      {/* ── Right: Editor ──────────────────────────────────────── */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {!product ? (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-tertiary)', fontSize: 14 }}>
            Produkt auswaehlen oder neu anlegen
          </div>
        ) : (
          <>
            {/* Header */}
            <div style={{ padding: '12px 20px', borderBottom: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0 }}>
              <h2 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', margin: 0, flex: 1 }}>{product.name || 'Neues Produkt'}</h2>
              <span style={{ padding: '2px 10px', borderRadius: 999, fontSize: 11, fontWeight: 500, background: product.status === 'live' ? 'var(--status-success-bg)' : product.status === 'archived' ? 'var(--status-danger-bg)' : 'var(--bg-app)', color: product.status === 'live' ? 'var(--status-success-text)' : product.status === 'archived' ? 'var(--status-danger-text)' : 'var(--text-secondary)' }}>
                {product.status}
              </span>
              {msg && <span style={{ fontSize: 12, color: msg.startsWith('\u2713') ? 'var(--status-success-text)' : 'var(--status-danger-text)' }}>{msg}</span>}
              <button onClick={save} disabled={saving} style={{ padding: '6px 16px', border: 'none', borderRadius: 'var(--radius-md)', background: 'var(--brand-primary)', color: '#fff', fontSize: 12, fontWeight: 600, cursor: saving ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)' }}>
                {saving ? 'Speichern...' : 'Speichern'}
              </button>
            </div>

            {/* Tabs */}
            <div style={{ display: 'flex', gap: 0, borderBottom: '1px solid var(--border-light)', flexShrink: 0 }}>
              {TABS.map(t => (
                <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
                  padding: '10px 16px', border: 'none', background: 'none', cursor: 'pointer',
                  fontSize: 12, fontWeight: activeTab === t.id ? 600 : 400,
                  color: activeTab === t.id ? 'var(--brand-primary)' : 'var(--text-secondary)',
                  borderBottom: activeTab === t.id ? '2px solid var(--brand-primary)' : '2px solid transparent',
                  fontFamily: 'var(--font-sans)',
                }}>{t.label}</button>
              ))}
            </div>

            {/* Tab content */}
            <div style={{ flex: 1, overflowY: 'auto', padding: 20 }}>
              {/* ── Produktdaten ── */}
              {activeTab === 'produktdaten' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 14, maxWidth: 700 }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                    <div><label style={labelS}>Slug</label><input style={inputS} value={product.slug} onChange={e => set('slug', e.target.value)} placeholder="z-b-mein-paket" /></div>
                    <div><label style={labelS}>Name</label><input style={inputS} value={product.name} onChange={e => set('name', e.target.value)} placeholder="Paketname" /></div>
                  </div>
                  <div><label style={labelS}>Kurzbeschreibung</label><input style={inputS} value={product.short_desc || ''} onChange={e => set('short_desc', e.target.value)} /></div>
                  <div><label style={labelS}>Langbeschreibung</label><textarea style={{ ...inputS, minHeight: 80, resize: 'vertical' }} value={product.long_desc || ''} onChange={e => set('long_desc', e.target.value)} /></div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
                    <div>
                      <label style={labelS}>Zahlungsart</label>
                      <select style={inputS} value={product.payment_type} onChange={e => set('payment_type', e.target.value)}>
                        <option value="once">Einmalig</option><option value="monthly">Monatlich</option><option value="yearly">Jaehrlich</option>
                      </select>
                    </div>
                    <div><label style={labelS}>Liefertage</label><input style={inputS} type="number" value={product.delivery_days} onChange={e => set('delivery_days', parseInt(e.target.value) || 0)} /></div>
                    <div>
                      <label style={labelS}>Status</label>
                      <select style={inputS} value={product.status} onChange={e => set('status', e.target.value)}>
                        <option value="draft">Entwurf</option><option value="live">Live</option><option value="archived">Archiviert</option>
                      </select>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', fontSize: 13 }}>
                      <input type="checkbox" checked={product.highlighted || false} onChange={e => set('highlighted', e.target.checked)} style={{ accentColor: '#008eaa' }} />
                      Hervorgehoben
                    </label>
                    {product.highlighted && <input style={{ ...inputS, width: 200 }} value={product.highlight_label || ''} onChange={e => set('highlight_label', e.target.value)} placeholder="Badge-Text" />}
                  </div>
                  <div><label style={labelS}>Sortierung</label><input style={{ ...inputS, width: 80 }} type="number" value={product.sort_order} onChange={e => set('sort_order', parseInt(e.target.value) || 0)} /></div>

                  {/* Features */}
                  <div>
                    <label style={labelS}>Leistungsumfang</label>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                      {(product.features || []).map((f, i) => (
                        <div key={i} style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                          <input style={{ ...inputS, flex: 1 }} value={f} onChange={e => {
                            const next = [...product.features]; next[i] = e.target.value; set('features', next);
                          }} placeholder={`Feature ${i + 1}`} />
                          <button onClick={() => set('features', product.features.filter((_, j) => j !== i))} style={{ background: 'none', border: 'none', color: 'var(--text-tertiary)', cursor: 'pointer', fontSize: 16, padding: '0 4px' }} title="Entfernen">&times;</button>
                        </div>
                      ))}
                      <button onClick={() => set('features', [...(product.features || []), ''])} style={{ alignSelf: 'flex-start', padding: '6px 12px', border: '1px dashed var(--border-light)', borderRadius: 'var(--radius-md)', background: 'none', color: 'var(--brand-primary)', fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>+ Feature hinzufuegen</button>
                    </div>
                  </div>
                </div>
              )}

              {/* ── Preis & Stripe ── */}
              {activeTab === 'preis' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 14, maxWidth: 500 }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
                    <div><label style={labelS}>Brutto (EUR)</label><input style={inputS} type="number" step="0.01" value={product.price_brutto} onChange={e => set('price_brutto', parseFloat(e.target.value) || 0)} /></div>
                    <div><label style={labelS}>Netto (EUR)</label><input style={inputS} type="number" step="0.01" value={product.price_netto} onChange={e => set('price_netto', parseFloat(e.target.value) || 0)} /></div>
                    <div><label style={labelS}>MwSt. %</label><input style={inputS} type="number" value={product.tax_rate} onChange={e => set('tax_rate', parseFloat(e.target.value) || 19)} /></div>
                  </div>
                  <div style={{ background: 'var(--bg-app)', borderRadius: 'var(--radius-md)', padding: '12px 16px' }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>Stripe-Verbindung</div>
                    {product.stripe_product_id ? (
                      <div style={{ fontSize: 12, color: 'var(--status-success-text)' }}>
                        <div>Product: <code style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>{product.stripe_product_id}</code></div>
                        <div>Price: <code style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>{product.stripe_price_id || '\u2014'}</code></div>
                      </div>
                    ) : (
                      <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>Noch nicht mit Stripe verbunden</div>
                    )}
                    <button onClick={async () => {
                      try {
                        const r = await fetch(`${API_BASE_URL}/api/products/${product.slug}/stripe-sync`, { method: 'POST', headers: h });
                        const d = await r.json();
                        if (r.ok) { setMsg('\u2713 Stripe synchronisiert'); set('stripe_product_id', d.stripe_product_id); set('stripe_price_id', d.stripe_price_id); }
                        else setMsg(d.detail || 'Stripe Fehler');
                      } catch { setMsg('Stripe-Verbindung fehlgeschlagen'); }
                    }} style={{ marginTop: 8, padding: '6px 14px', border: 'none', borderRadius: 'var(--radius-md)', background: '#635BFF', color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                      {product.stripe_product_id ? 'Stripe aktualisieren' : 'Mit Stripe verbinden'}
                    </button>
                  </div>
                </div>
              )}

              {/* ── Checkout ── */}
              {activeTab === 'checkout' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 14, maxWidth: 600 }}>
                  <div>
                    <label style={labelS}>Checkout-Felder</label>
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                      {['name', 'company', 'email', 'phone', 'website_url', 'message'].map(f => (
                        <label key={f} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, cursor: 'pointer' }}>
                          <input type="checkbox" checked={(product.checkout_fields || []).includes(f)} onChange={e => {
                            const arr = product.checkout_fields || [];
                            set('checkout_fields', e.target.checked ? [...arr, f] : arr.filter(x => x !== f));
                          }} style={{ accentColor: '#008eaa' }} />
                          {f}
                        </label>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label style={labelS}>Webhook-Aktionen nach Zahlung</label>
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                      {['create_lead', 'create_user', 'create_project', 'send_welcome_email', 'send_pdf', 'start_audit', 'start_scraper'].map(a => (
                        <label key={a} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, cursor: 'pointer' }}>
                          <input type="checkbox" checked={(product.webhook_actions || []).includes(a)} onChange={e => {
                            const arr = product.webhook_actions || [];
                            set('webhook_actions', e.target.checked ? [...arr, a] : arr.filter(x => x !== a));
                          }} style={{ accentColor: '#008eaa' }} />
                          {a}
                        </label>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* ── Assets & URLs ── */}
              {activeTab === 'assets' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 14, maxWidth: 600 }}>
                  <div style={{ background: 'var(--bg-app)', borderRadius: 'var(--radius-md)', padding: '12px 16px', fontSize: 12, color: 'var(--text-secondary)' }}>
                    URLs werden automatisch generiert. Der Checkout ist erreichbar unter:<br />
                    <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--brand-primary)', fontSize: 11 }}>
                      {window.location.origin}/checkout/{product.slug}
                    </code>
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
                    Landing Pages und weitere Assets koennen spaeter hier verwaltet werden.
                  </div>
                </div>
              )}

              {/* ── Checkliste ── */}
              {activeTab === 'checkliste' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10, maxWidth: 500 }}>
                  {[
                    { ok: !!product.name, label: 'Name vergeben' },
                    { ok: !!product.slug, label: 'Slug gesetzt' },
                    { ok: product.price_brutto > 0, label: 'Preis eingetragen' },
                    { ok: (product.features || []).length >= 3, label: 'Mind. 3 Features' },
                    { ok: !!product.short_desc, label: 'Kurzbeschreibung' },
                    { ok: !!product.stripe_product_id, label: 'Stripe verbunden' },
                    { ok: product.status === 'live', label: 'Status auf Live' },
                  ].map((c, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', borderRadius: 'var(--radius-md)', background: c.ok ? 'var(--status-success-bg)' : 'var(--bg-app)' }}>
                      <span style={{ fontSize: 14 }}>{c.ok ? '\u2705' : '\u2B1C'}</span>
                      <span style={{ fontSize: 13, color: c.ok ? 'var(--status-success-text)' : 'var(--text-secondary)', textDecoration: c.ok ? 'line-through' : 'none' }}>{c.label}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
