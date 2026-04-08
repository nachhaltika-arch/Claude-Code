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
              {activeTab === 'preis' && (() => {
                const autoNetto = product.price_brutto > 0 ? +(product.price_brutto / (1 + product.tax_rate / 100)).toFixed(2) : 0;
                return (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 14, maxWidth: 560 }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
                      <div>
                        <label style={labelS}>Brutto inkl. MwSt. (EUR)</label>
                        <input style={inputS} type="number" step="0.01" value={product.price_brutto} onChange={e => {
                          const brutto = parseFloat(e.target.value) || 0;
                          setProduct(p => ({ ...p, price_brutto: brutto, price_netto: +(brutto / (1 + p.tax_rate / 100)).toFixed(2) }));
                        }} />
                      </div>
                      <div>
                        <label style={labelS}>MwSt.-Satz</label>
                        <select style={inputS} value={product.tax_rate} onChange={e => {
                          const tax = parseFloat(e.target.value);
                          setProduct(p => ({ ...p, tax_rate: tax, price_netto: +(p.price_brutto / (1 + tax / 100)).toFixed(2) }));
                        }}>
                          <option value={19}>19 %</option><option value={7}>7 %</option><option value={0}>0 %</option>
                        </select>
                      </div>
                      <div>
                        <label style={labelS}>Netto (berechnet)</label>
                        <input style={{ ...inputS, background: 'var(--bg-app)', color: 'var(--text-tertiary)' }} type="number" step="0.01" value={autoNetto} readOnly />
                      </div>
                    </div>
                    <div style={{ background: 'var(--bg-app)', borderRadius: 'var(--radius-md)', padding: '14px 16px' }}>
                      <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 10 }}>Stripe-Verbindung</div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                        <div>
                          <label style={{ ...labelS, fontSize: 10 }}>Stripe Product ID</label>
                          <input style={{ ...inputS, background: product.stripe_product_id ? 'var(--bg-app)' : 'var(--bg-surface)', color: product.stripe_product_id ? 'var(--text-secondary)' : 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', fontSize: 11 }} value={product.stripe_product_id || ''} readOnly={!!product.stripe_product_id} onChange={e => { if (!product.stripe_product_id) set('stripe_product_id', e.target.value); }} placeholder="Wird automatisch gesetzt" />
                        </div>
                        <div>
                          <label style={{ ...labelS, fontSize: 10 }}>Stripe Price ID</label>
                          <input style={{ ...inputS, background: 'var(--bg-app)', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', fontSize: 11 }} value={product.stripe_price_id || ''} readOnly placeholder="Wird automatisch gesetzt" />
                        </div>
                      </div>
                      <button onClick={async () => {
                        try {
                          const r = await fetch(`${API_BASE_URL}/api/products/${product.slug}/stripe-sync`, { method: 'POST', headers: h });
                          const d = await r.json();
                          if (r.ok) { setMsg('\u2713 Stripe synchronisiert'); setProduct(p => ({ ...p, stripe_product_id: d.stripe_product_id, stripe_price_id: d.stripe_price_id })); }
                          else setMsg(d.detail || 'Stripe Fehler');
                        } catch { setMsg('Stripe-Verbindung fehlgeschlagen'); }
                      }} style={{ marginTop: 10, padding: '8px 16px', border: 'none', borderRadius: 'var(--radius-md)', background: '#635BFF', color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                        {product.stripe_product_id ? 'Stripe aktualisieren' : 'In Stripe erstellen'}
                      </button>
                      <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 6 }}>STRIPE_SECRET_KEY muss in Render gesetzt sein.</div>
                    </div>
                  </div>
                );
              })()}

              {/* ── Checkout ── */}
              {activeTab === 'checkout' && (() => {
                const FIELD_LABELS = { name: 'Name', company: 'Firma', email: 'E-Mail', phone: 'Telefon', website: 'Website', message: 'Nachricht' };
                const ACTION_LABELS = { create_lead: 'Lead anlegen', create_user: 'Kunden-Account anlegen', create_project: 'Projekt in Phase 1 anlegen', send_welcome_email: 'Willkommens-E-Mail senden', send_pdf: 'Auftragsbestaetigung PDF', start_sequence: 'E-Mail-Sequenz starten' };
                const toggleArr = (key, val) => {
                  const arr = product[key] || [];
                  set(key, arr.includes(val) ? arr.filter(x => x !== val) : [...arr, val]);
                };
                return (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 600 }}>
                    <div>
                      <label style={labelS}>Checkout-Felder</label>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        {Object.entries(FIELD_LABELS).map(([k, l]) => (
                          <label key={k} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, cursor: 'pointer', padding: '4px 0' }}>
                            <input type="checkbox" checked={(product.checkout_fields || []).includes(k)} onChange={() => toggleArr('checkout_fields', k)} style={{ accentColor: '#008eaa', width: 16, height: 16 }} />
                            {l}
                          </label>
                        ))}
                      </div>
                    </div>
                    <div>
                      <label style={labelS}>Webhook-Aktionen nach Zahlung</label>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        {Object.entries(ACTION_LABELS).map(([k, l]) => (
                          <label key={k} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, cursor: 'pointer', padding: '4px 0' }}>
                            <input type="checkbox" checked={(product.webhook_actions || []).includes(k)} onChange={() => toggleArr('webhook_actions', k)} style={{ accentColor: '#008eaa', width: 16, height: 16 }} />
                            {l}
                          </label>
                        ))}
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* ── Assets & URLs ── */}
              {activeTab === 'assets' && (() => {
                const FE = 'https://kompagnon-frontend.onrender.com';
                const BE = 'https://claude-code-znq2.onrender.com';
                const urls = [
                  { label: 'Landing Page URL', url: `${FE}/paket/${product.slug}` },
                  { label: 'Checkout-URL (direkt)', url: `${FE}/checkout?package=${product.slug}` },
                  { label: 'API Checkout (POST)', url: `${BE}/api/payments/create-checkout` },
                ];
                const assets = [
                  { label: 'Landing Page', ok: product.status === 'live' },
                  { label: 'Checkout-Form', ok: product.status === 'live' },
                  { label: 'Stripe Price', ok: !!product.stripe_price_id },
                  { label: 'PDF-Template', ok: true },
                  { label: 'E-Mail-Template', ok: true },
                  { label: 'QR-Code', ok: false },
                ];
                const copy = (url) => { navigator.clipboard.writeText(url); setMsg('\u2713 Kopiert'); setTimeout(() => setMsg(''), 1500); };
                return (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 16, maxWidth: 650 }}>
                    {urls.map(u => (
                      <div key={u.label}>
                        <label style={labelS}>{u.label}</label>
                        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                          <input style={{ ...inputS, flex: 1, fontFamily: 'var(--font-mono)', fontSize: 11, background: 'var(--bg-app)', color: 'var(--text-secondary)' }} value={u.url} readOnly />
                          <button onClick={() => copy(u.url)} style={{ padding: '6px 12px', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface)', color: 'var(--brand-primary)', fontSize: 11, cursor: 'pointer', fontFamily: 'var(--font-sans)', flexShrink: 0 }}>Kopieren</button>
                        </div>
                      </div>
                    ))}
                    <div>
                      <label style={labelS}>Asset-Status</label>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
                        {assets.map(a => (
                          <div key={a.label} style={{ padding: '10px 12px', borderRadius: 'var(--radius-md)', background: a.ok ? 'var(--status-success-bg)' : 'var(--bg-app)', textAlign: 'center' }}>
                            <div style={{ fontSize: 16, marginBottom: 4 }}>{a.ok ? '\u2705' : '\u23F3'}</div>
                            <div style={{ fontSize: 11, fontWeight: 500, color: a.ok ? 'var(--status-success-text)' : 'var(--text-tertiary)' }}>{a.label}</div>
                            <div style={{ fontSize: 10, color: a.ok ? 'var(--status-success-text)' : 'var(--text-tertiary)' }}>{a.ok ? (a.label === 'Stripe Price' ? 'Verknuepft' : 'Bereit') : 'Ausstehend'}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* ── Checkliste ── */}
              {activeTab === 'checkliste' && (() => {
                const checks = [
                  { text: 'Produktdaten vollstaendig', done: !!(product.name && product.short_desc) },
                  { text: 'Preis gesetzt', done: product.price_brutto > 0 },
                  { text: 'Features eingetragen', done: (product.features || []).length > 0 },
                  { text: 'Stripe verknuepft', done: !!product.stripe_price_id },
                  { text: 'Checkout-Felder gesetzt', done: (product.checkout_fields || []).length > 0 },
                  { text: 'Status auf Live', done: product.status === 'live' },
                  { text: 'Test-Kauf durchfuehren', done: false },
                ];
                const doneCount = checks.filter(c => c.done).length;
                const pct = Math.round(doneCount / checks.length * 100);
                return (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12, maxWidth: 500 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <div style={{ flex: 1, height: 6, background: 'var(--border-light)', borderRadius: 3, overflow: 'hidden' }}>
                        <div style={{ width: `${pct}%`, height: '100%', background: doneCount === checks.length ? '#22C55E' : '#008eaa', transition: 'width 0.4s', borderRadius: 3 }} />
                      </div>
                      <span style={{ fontSize: 12, fontWeight: 600, color: doneCount === checks.length ? 'var(--status-success-text)' : 'var(--text-secondary)', whiteSpace: 'nowrap' }}>{doneCount} von {checks.length} erledigt</span>
                    </div>
                    {checks.map((c, i) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', borderRadius: 'var(--radius-md)', background: c.done ? 'var(--status-success-bg)' : 'var(--bg-app)' }}>
                        <span style={{ fontSize: 14 }}>{c.done ? '\u2705' : '\u2B1C'}</span>
                        <span style={{ fontSize: 13, color: c.done ? 'var(--status-success-text)' : 'var(--text-secondary)', textDecoration: c.done ? 'line-through' : 'none' }}>{c.text}</span>
                      </div>
                    ))}
                    <button onClick={() => { set('status', 'live'); setTimeout(save, 100); }} disabled={doneCount < 5} style={{ marginTop: 8, padding: '10px 20px', border: 'none', borderRadius: 'var(--radius-md)', background: doneCount < 5 ? 'var(--bg-app)' : 'var(--brand-primary)', color: doneCount < 5 ? 'var(--text-tertiary)' : '#fff', fontSize: 13, fontWeight: 600, cursor: doneCount < 5 ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)' }}>
                      Produkt live schalten
                    </button>
                  </div>
                );
              })()}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
