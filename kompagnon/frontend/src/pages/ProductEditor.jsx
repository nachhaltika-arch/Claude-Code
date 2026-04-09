import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

const FRONTEND_URL = 'https://kompagnon-frontend.onrender.com';

// Deutschen Namen in URL-sicheren Slug umwandeln
function generateSlug(name) {
  if (!name) return '';
  return name
    .toLowerCase()
    .trim()
    .replace(/ä/g, 'ae')
    .replace(/ö/g, 'oe')
    .replace(/ü/g, 'ue')
    .replace(/ß/g, 'ss')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

const STATUS_DOT = {
  live:     { bg: '#1D9E75', label: 'Live' },
  draft:    { bg: '#94a3b8', label: 'Entwurf' },
  archived: { bg: '#E24B4A', label: 'Archiviert' },
};

const TABS = [
  { id: 'produktdaten', label: 'Produktdaten' },
  { id: 'preis',        label: 'Preis & Stripe' },
  { id: 'checkout',     label: 'Checkout' },
  { id: 'assets',       label: 'Assets & URLs' },
  { id: 'checkliste',   label: 'Checkliste' },
];

// ── Shared style helpers ─────────────────────────────────────────────────────
const LBL = {
  display: 'block', fontSize: 11, fontWeight: 600,
  color: '#64748b', textTransform: 'uppercase',
  letterSpacing: '.06em', marginBottom: 5,
};
const INP = {
  width: '100%', padding: '9px 12px',
  border: '1.5px solid var(--border-light)',
  borderRadius: 8, fontSize: 13,
  fontFamily: 'inherit', color: 'var(--text-primary)',
  background: 'var(--bg-app)',
  boxSizing: 'border-box', outline: 'none',
};
const FIELD = { marginBottom: 14 };

export default function ProductEditor() {
  const [products, setProducts]       = useState([]);
  const [selected, setSelected]       = useState(null);
  const [product, setProduct]         = useState(null);
  const [activeTab, setActiveTab]     = useState('produktdaten');
  const [saving, setSaving]           = useState(false);
  const [msg, setMsg]                 = useState('');
  const [confirmDelete, setConfirmDelete] = useState(false);
  const { token } = useAuth();

  const h = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };

  useEffect(() => { loadProducts(); }, []); // eslint-disable-line

  // Auto-compute price_netto when price_brutto or tax_rate changes
  useEffect(() => {
    if (!product) return;
    const brutto = parseFloat(product.price_brutto) || 0;
    const tax    = parseFloat(product.tax_rate) || 0;
    const netto  = +(brutto / (1 + tax / 100)).toFixed(2);
    if (netto !== product.price_netto) {
      setProduct(p => ({ ...p, price_netto: netto }));
    }
  }, [product?.price_brutto, product?.tax_rate]); // eslint-disable-line

  const loadProducts = async () => {
    const r = await fetch(`${API_BASE_URL}/api/products/`, { headers: h });
    if (r.ok) setProducts(await r.json());
  };

  const selectProduct = (p) => {
    setSelected(p.slug);
    setProduct({ ...p });
    setActiveTab('produktdaten');
    setMsg('');
    setConfirmDelete(false);
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
      webhook_actions: ['create_lead', 'create_user', 'create_project',
                        'send_welcome_email', 'send_pdf'],
      status: 'draft', sort_order: 0,
    });
    setActiveTab('produktdaten');
    setMsg('');
  };

  const set = (field) => (val) =>
    setProduct(p => ({ ...p, [field]: val }));

  const deleteProduct = async () => {
    if (!confirmDelete) { setConfirmDelete(true); return; }
    try {
      const r = await fetch(`${API_BASE_URL}/api/products/${selected}`, {
        method: 'DELETE', headers: h,
      });
      if (r.ok) {
        setProduct(null); setSelected(null); setConfirmDelete(false);
        await loadProducts();
      }
    } catch {}
  };

  const moveSortOrder = async (slug, direction) => {
    const idx   = products.findIndex(p => p.slug === slug);
    const other = products[idx + direction];
    if (!other) return;
    const newSo      = other.sort_order;
    const otherNewSo = products[idx].sort_order;
    await Promise.all([
      fetch(`${API_BASE_URL}/api/products/${slug}`, {
        method: 'PUT', headers: h,
        body: JSON.stringify({ sort_order: newSo }),
      }),
      fetch(`${API_BASE_URL}/api/products/${other.slug}`, {
        method: 'PUT', headers: h,
        body: JSON.stringify({ sort_order: otherNewSo }),
      }),
    ]);
    await loadProducts();
  };

  const save = async () => {
    setSaving(true); setMsg('');
    try {
      const isNew = selected === '__new__';
      if (!product.name?.trim()) {
        setMsg('Bitte einen Produktnamen eingeben');
        setSaving(false);
        return;
      }
      // Slug sicherstellen — falls leer, aus Namen generieren
      const payload = {
        ...product,
        slug: (product.slug && product.slug.trim()) || generateSlug(product.name),
      };
      // Internes Flag nicht an Backend schicken
      delete payload._slugManuallyEdited;

      const url   = isNew
        ? `${API_BASE_URL}/api/products/`
        : `${API_BASE_URL}/api/products/${selected}`;
      const r = await fetch(url, {
        method: isNew ? 'POST' : 'PUT',
        headers: h,
        body: JSON.stringify(payload),
      });
      const d = await r.json();
      if (!r.ok) { setMsg(d.detail || 'Fehler'); return; }
      setMsg('✓ Gespeichert');
      await loadProducts();
      setSelected(d.slug);
      setProduct(d);
    } catch { setMsg('Verbindungsfehler'); }
    finally { setSaving(false); }
  };

  // ── Left sidebar ───────────────────────────────────────────────────────────
  const Sidebar = () => (
    <div style={{
      width: 260, flexShrink: 0,
      background: 'var(--bg-surface)',
      border: '0.5px solid var(--border-light)',
      borderRadius: 12, overflow: 'hidden',
      display: 'flex', flexDirection: 'column',
    }}>
      <div style={{
        padding: '12px 14px',
        borderBottom: '0.5px solid var(--border-light)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
          Produkte
        </span>
        <button
          onClick={newProduct}
          style={{
            padding: '4px 10px', borderRadius: 6, border: 'none',
            background: '#008eaa', color: 'white',
            fontSize: 11, fontWeight: 600, cursor: 'pointer',
          }}
        >
          + Neu
        </button>
      </div>

      <div style={{ flex: 1, overflowY: 'auto' }}>
        {products.length === 0 && (
          <div style={{ padding: '20px 14px', fontSize: 12, color: '#94a3b8', textAlign: 'center' }}>
            Noch keine Produkte
          </div>
        )}
        {products.map((p, idx) => {
          const dot = STATUS_DOT[p.status] || STATUS_DOT.draft;
          const isActive = selected === p.slug;
          return (
            <div
              key={p.slug}
              style={{
                padding: '8px 10px 8px 14px',
                borderBottom: '0.5px solid var(--border-light)',
                background: isActive ? 'var(--brand-primary-light, #e6f1fb)' : 'transparent',
                borderLeft: isActive ? '3px solid #008eaa' : '3px solid transparent',
                display: 'flex', alignItems: 'center', gap: 6,
              }}
            >
              {/* Sort up/down */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 1, flexShrink: 0 }}>
                <button
                  onClick={e => { e.stopPropagation(); moveSortOrder(p.slug, -1); }}
                  disabled={idx === 0}
                  title="Nach oben"
                  style={{
                    width: 16, height: 14, padding: 0, border: 'none',
                    background: 'transparent', cursor: idx === 0 ? 'default' : 'pointer',
                    color: idx === 0 ? '#d1d5db' : '#94a3b8', fontSize: 9, lineHeight: 1,
                  }}
                >▲</button>
                <button
                  onClick={e => { e.stopPropagation(); moveSortOrder(p.slug, 1); }}
                  disabled={idx === products.length - 1}
                  title="Nach unten"
                  style={{
                    width: 16, height: 14, padding: 0, border: 'none',
                    background: 'transparent', cursor: idx === products.length - 1 ? 'default' : 'pointer',
                    color: idx === products.length - 1 ? '#d1d5db' : '#94a3b8', fontSize: 9, lineHeight: 1,
                  }}
                >▼</button>
              </div>

              {/* Product info (clickable) */}
              <div
                onClick={() => selectProduct(p)}
                style={{ flex: 1, minWidth: 0, cursor: 'pointer' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                  <span style={{
                    width: 8, height: 8, borderRadius: '50%',
                    background: dot.bg, flexShrink: 0,
                  }} />
                  <span style={{
                    fontSize: 13, fontWeight: isActive ? 600 : 400,
                    color: 'var(--text-primary)',
                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                  }}>
                    {p.name}
                  </span>
                </div>
                <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2, paddingLeft: 15 }}>
                  {p.price_brutto ? `${parseFloat(p.price_brutto).toFixed(2)} €` : '—'} · {dot.label}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  // ── Placeholder ────────────────────────────────────────────────────────────
  if (!product) {
    return (
      <div style={{ display: 'flex', gap: 16, height: '100%' }}>
        <Sidebar />
        <div style={{
          flex: 1, display: 'flex', alignItems: 'center',
          justifyContent: 'center', color: '#94a3b8', fontSize: 14,
        }}>
          Produkt auswählen oder neu anlegen
        </div>
      </div>
    );
  }

  const statusDot = STATUS_DOT[product.status] || STATUS_DOT.draft;

  // ── Tab: Produktdaten ──────────────────────────────────────────────────────
  const TabProduktdaten = () => (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 14 }}>
        <div style={FIELD}>
          <label style={LBL}>Produktname *</label>
          <input
            value={product.name}
            onChange={e => {
              const name = e.target.value;
              setProduct(p => {
                const autoSlug = generateSlug(name);
                // Slug nur auto-generieren wenn noch nicht manuell bearbeitet
                const nextSlug = p._slugManuallyEdited ? p.slug : autoSlug;
                return { ...p, name, slug: nextSlug };
              });
            }}
            placeholder="z.B. KOMPAGNON-Paket"
            style={INP}
          />
        </div>
        <div style={FIELD}>
          <label style={LBL}>URL-Slug {selected === '__new__' ? '(automatisch aus Name)' : '(nicht änderbar)'}</label>
          <input
            value={product.slug}
            onChange={e => setProduct(p => ({ ...p, slug: e.target.value, _slugManuallyEdited: true }))}
            placeholder="wird automatisch generiert"
            disabled={selected !== '__new__'}
            style={{ ...INP, opacity: selected !== '__new__' ? 0.6 : 1, fontFamily: 'monospace', fontSize: 12 }}
          />
        </div>
      </div>

      <div style={FIELD}>
        <label style={LBL}>Kurzbeschreibung</label>
        <input
          value={product.short_desc || ''}
          onChange={e => set('short_desc')(e.target.value)}
          placeholder="Wird in der Preisübersicht angezeigt"
          style={INP}
        />
      </div>

      <div style={FIELD}>
        <label style={LBL}>Langbeschreibung</label>
        <textarea
          rows={4}
          value={product.long_desc || ''}
          onChange={e => set('long_desc')(e.target.value)}
          placeholder="Ausführliche Produktbeschreibung"
          style={{ ...INP, resize: 'vertical' }}
        />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 80px', gap: 14, marginBottom: 14 }}>
        <div style={FIELD}>
          <label style={LBL}>Zahlungsart</label>
          <select
            value={product.payment_type || 'once'}
            onChange={e => set('payment_type')(e.target.value)}
            style={INP}
          >
            <option value="once">Einmalig</option>
            <option value="monthly">Monatlich</option>
            <option value="yearly">Jährlich</option>
          </select>
        </div>
        <div style={FIELD}>
          <label style={LBL}>Lieferzeit (Tage)</label>
          <input
            type="number"
            min={1}
            value={product.delivery_days || 14}
            onChange={e => set('delivery_days')(parseInt(e.target.value) || 14)}
            style={INP}
          />
        </div>
        <div style={FIELD}>
          <label style={LBL}>Status</label>
          <select
            value={product.status || 'draft'}
            onChange={e => set('status')(e.target.value)}
            style={INP}
          >
            <option value="draft">Entwurf</option>
            <option value="live">Live</option>
            <option value="archived">Archiviert</option>
          </select>
        </div>
        <div style={FIELD}>
          <label style={LBL}>Reihenfolge</label>
          <input
            type="number"
            min={0}
            value={product.sort_order ?? 0}
            onChange={e => set('sort_order')(parseInt(e.target.value) || 0)}
            style={INP}
          />
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 20, marginBottom: 20 }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 13 }}>
          <input
            type="checkbox"
            checked={!!product.highlighted}
            onChange={e => set('highlighted')(e.target.checked)}
          />
          Empfehlung hervorheben
        </label>
        {product.highlighted && (
          <div style={{ flex: 1 }}>
            <input
              value={product.highlight_label || ''}
              onChange={e => set('highlight_label')(e.target.value)}
              placeholder="Label (z.B. Empfehlung)"
              style={{ ...INP, marginBottom: 0 }}
            />
          </div>
        )}
      </div>

      {/* Features */}
      <div>
        <div style={{
          fontSize: 12, fontWeight: 600, color: '#64748b',
          textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 10,
        }}>
          Leistungsumfang
        </div>
        {(product.features || []).map((f, i) => (
          <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
            <input
              value={f}
              onChange={e => {
                const next = [...product.features];
                next[i] = e.target.value;
                set('features')(next);
              }}
              placeholder={`Feature ${i + 1}`}
              style={{ ...INP, flex: 1, marginBottom: 0 }}
            />
            <button
              onClick={() => set('features')(product.features.filter((_, j) => j !== i))}
              style={{
                padding: '0 10px', borderRadius: 7,
                border: '1px solid #FECACA', background: '#FFF1F1',
                color: '#A32D2D', fontSize: 16, cursor: 'pointer',
                flexShrink: 0,
              }}
              title="Entfernen"
            >
              ×
            </button>
          </div>
        ))}
        <button
          onClick={() => set('features')([...(product.features || []), ''])}
          style={{
            padding: '7px 14px', borderRadius: 7,
            border: '1.5px dashed var(--border-light)',
            background: 'transparent', color: '#64748b',
            fontSize: 12, cursor: 'pointer', marginTop: 4,
          }}
        >
          + Feature hinzufügen
        </button>
      </div>
    </div>
  );

  // ── Tab: Preis & Stripe ────────────────────────────────────────────────────
  const TabPreis = () => {
    const [syncing, setSyncing]   = useState(false);
    const [syncMsg, setSyncMsg]   = useState('');

    const doStripeSync = async () => {
      setSyncing(true); setSyncMsg('');
      try {
        const r = await fetch(`${API_BASE_URL}/api/products/${product.slug}/stripe-sync`, {
          method: 'POST', headers: h,
        });
        const d = await r.json();
        if (!r.ok) { setSyncMsg(d.detail || 'Fehler'); return; }
        setSyncMsg(`✓ Product: ${d.stripe_product_id} · Price: ${d.stripe_price_id}`);
        setProduct(p => ({
          ...p,
          stripe_product_id: d.stripe_product_id,
          stripe_price_id:   d.stripe_price_id,
        }));
      } catch { setSyncMsg('Verbindungsfehler'); }
      finally { setSyncing(false); }
    };

    return (
      <div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 14 }}>
          <div style={FIELD}>
            <label style={LBL}>Brutto inkl. MwSt. (EUR)</label>
            <input
              type="number"
              min={0}
              step={0.01}
              value={product.price_brutto || 0}
              onChange={e => set('price_brutto')(parseFloat(e.target.value) || 0)}
              style={INP}
            />
          </div>
          <div style={FIELD}>
            <label style={LBL}>Mehrwertsteuer</label>
            <select
              value={product.tax_rate ?? 19}
              onChange={e => set('tax_rate')(parseFloat(e.target.value))}
              style={INP}
            >
              <option value={19}>19%</option>
              <option value={7}>7%</option>
              <option value={0}>0%</option>
            </select>
          </div>
        </div>

        <div style={{ ...FIELD, marginBottom: 24 }}>
          <label style={LBL}>Netto (berechnet)</label>
          <input
            value={`${(product.price_netto || 0).toFixed(2)} €`}
            readOnly
            style={{ ...INP, opacity: 0.6, cursor: 'default' }}
          />
        </div>

        {/* Stripe section */}
        <div style={{
          background: 'var(--bg-surface)',
          border: '0.5px solid var(--border-light)',
          borderRadius: 10, padding: 16,
        }}>
          <div style={{
            fontSize: 12, fontWeight: 600, color: '#64748b',
            textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 14,
          }}>
            Stripe-Verknüpfung
          </div>

          <div style={FIELD}>
            <label style={LBL}>Stripe Product ID</label>
            <input
              value={product.stripe_product_id || ''}
              onChange={e => set('stripe_product_id')(e.target.value)}
              placeholder="prod_..."
              readOnly={!!product.stripe_product_id}
              style={{ ...INP, opacity: product.stripe_product_id ? 0.6 : 1, cursor: product.stripe_product_id ? 'default' : 'text' }}
            />
          </div>

          <div style={{ ...FIELD, marginBottom: 16 }}>
            <label style={LBL}>Stripe Price ID</label>
            <input
              value={product.stripe_price_id || ''}
              readOnly
              placeholder="price_..."
              style={{ ...INP, opacity: 0.6, cursor: 'default' }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button
              onClick={doStripeSync}
              disabled={syncing || selected === '__new__'}
              style={{
                padding: '9px 18px', borderRadius: 8, border: 'none',
                background: syncing || selected === '__new__' ? '#94a3b8' : '#635bff',
                color: 'white', fontSize: 13, fontWeight: 600,
                cursor: syncing || selected === '__new__' ? 'not-allowed' : 'pointer',
              }}
            >
              {syncing ? 'Synchronisiert...' : '⚡ In Stripe erstellen / aktualisieren'}
            </button>
            {selected === '__new__' && (
              <span style={{ fontSize: 11, color: '#94a3b8' }}>Erst speichern</span>
            )}
          </div>

          {syncMsg && (
            <div style={{
              marginTop: 10, fontSize: 12,
              color: syncMsg.startsWith('✓') ? '#1D9E75' : '#E24B4A',
              fontWeight: 500,
            }}>
              {syncMsg}
            </div>
          )}

          <div style={{
            marginTop: 14, padding: '8px 12px',
            background: '#FFF8E1', borderRadius: 7,
            fontSize: 11, color: '#856404',
            border: '1px solid #FFEAA7',
          }}>
            ℹ Stripe API Key (STRIPE_SECRET_KEY) muss in Render gesetzt sein
          </div>
        </div>
      </div>
    );
  };

  // ── Tab: Checkout ──────────────────────────────────────────────────────────
  const CHECKOUT_FIELD_OPTIONS = [
    { value: 'name',    label: 'Name' },
    { value: 'company', label: 'Firmenname' },
    { value: 'email',   label: 'E-Mail' },
    { value: 'phone',   label: 'Telefon' },
    { value: 'website', label: 'Website' },
    { value: 'message', label: 'Nachricht' },
  ];

  const WEBHOOK_ACTION_OPTIONS = [
    { value: 'create_lead',        label: 'Lead anlegen' },
    { value: 'create_user',        label: 'Kunden-Account anlegen' },
    { value: 'create_project',     label: 'Projekt in Phase 1 anlegen' },
    { value: 'send_welcome_email', label: 'Willkommens-E-Mail senden' },
    { value: 'send_pdf',           label: 'Auftragsbestätigung PDF' },
    { value: 'start_sequence',     label: 'E-Mail-Sequenz starten' },
  ];

  const toggleArrayItem = (field, val) => {
    const arr = product[field] || [];
    set(field)(arr.includes(val) ? arr.filter(x => x !== val) : [...arr, val]);
  };

  const TabCheckout = () => (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* Checkout fields */}
        <div>
          <div style={{
            fontSize: 12, fontWeight: 600, color: '#64748b',
            textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 12,
          }}>
            Checkout-Felder
          </div>
          {CHECKOUT_FIELD_OPTIONS.map(opt => (
            <label
              key={opt.value}
              style={{
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '8px 12px', marginBottom: 4,
                borderRadius: 8, cursor: 'pointer',
                background: (product.checkout_fields || []).includes(opt.value)
                  ? '#e6f1fb' : 'transparent',
                border: '1px solid',
                borderColor: (product.checkout_fields || []).includes(opt.value)
                  ? '#008eaa44' : 'var(--border-light)',
                fontSize: 13,
              }}
            >
              <input
                type="checkbox"
                checked={(product.checkout_fields || []).includes(opt.value)}
                onChange={() => toggleArrayItem('checkout_fields', opt.value)}
                style={{ accentColor: '#008eaa' }}
              />
              {opt.label}
            </label>
          ))}
        </div>

        {/* Webhook actions */}
        <div>
          <div style={{
            fontSize: 12, fontWeight: 600, color: '#64748b',
            textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 12,
          }}>
            Nach dem Kauf ausführen
          </div>
          {WEBHOOK_ACTION_OPTIONS.map(opt => (
            <label
              key={opt.value}
              style={{
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '8px 12px', marginBottom: 4,
                borderRadius: 8, cursor: 'pointer',
                background: (product.webhook_actions || []).includes(opt.value)
                  ? '#e6f1fb' : 'transparent',
                border: '1px solid',
                borderColor: (product.webhook_actions || []).includes(opt.value)
                  ? '#008eaa44' : 'var(--border-light)',
                fontSize: 13,
              }}
            >
              <input
                type="checkbox"
                checked={(product.webhook_actions || []).includes(opt.value)}
                onChange={() => toggleArrayItem('webhook_actions', opt.value)}
                style={{ accentColor: '#008eaa' }}
              />
              {opt.label}
            </label>
          ))}
        </div>
      </div>
    </div>
  );

  // ── Tab: Assets & URLs ─────────────────────────────────────────────────────
  const TabAssets = () => {
    const [copied, setCopied] = useState('');

    const copyToClipboard = (url, key) => {
      navigator.clipboard.writeText(url).then(() => {
        setCopied(key);
        setTimeout(() => setCopied(''), 2000);
      });
    };

    const urlRows = [
      {
        key:   'landing',
        label: 'Landing Page URL',
        url:   `${FRONTEND_URL}/paket/${product.slug}`,
      },
      {
        key:   'checkout',
        label: 'Checkout-URL (direkt)',
        url:   `${FRONTEND_URL}/checkout?package=${product.slug}`,
      },
      {
        key:   'api',
        label: 'API Checkout (POST)',
        url:   'https://claude-code-znq2.onrender.com/api/payments/create-checkout',
      },
    ];

    const assetGrid = [
      { label: 'Landing Page',    status: product.status === 'live' ? 'live' : 'ausstehend' },
      { label: 'Checkout-Form',   status: product.status === 'live' ? 'live' : 'ausstehend' },
      { label: 'Stripe Price',    status: product.stripe_price_id   ? 'verknüpft' : 'ausstehend' },
      { label: 'PDF-Template',    status: 'Bereit' },
      { label: 'E-Mail-Template', status: 'Bereit' },
      { label: 'QR-Code',         status: 'Ausstehend' },
    ];

    const statusColor = (s) => {
      if (s === 'live' || s === 'Bereit' || s === 'verknüpft') return { bg: '#dcfce7', color: '#166534' };
      return { bg: '#f1f5f9', color: '#64748b' };
    };

    return (
      <div>
        {/* URL rows */}
        <div style={{ marginBottom: 24 }}>
          {urlRows.map(row => (
            <div key={row.key} style={{ marginBottom: 10 }}>
              <label style={LBL}>{row.label}</label>
              <div style={{ display: 'flex', gap: 8 }}>
                <input
                  value={row.url}
                  readOnly
                  style={{ ...INP, flex: 1, opacity: 0.75, cursor: 'text', fontFamily: 'monospace', fontSize: 12 }}
                />
                <button
                  onClick={() => copyToClipboard(row.url, row.key)}
                  style={{
                    padding: '0 14px', borderRadius: 8, border: '1.5px solid var(--border-light)',
                    background: copied === row.key ? '#dcfce7' : 'var(--bg-surface)',
                    color: copied === row.key ? '#166534' : '#64748b',
                    fontSize: 12, cursor: 'pointer', flexShrink: 0, fontWeight: 500,
                    transition: 'all 0.2s',
                  }}
                >
                  {copied === row.key ? '✓ Kopiert' : 'Kopieren'}
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Asset status grid */}
        <div style={{
          fontSize: 12, fontWeight: 600, color: '#64748b',
          textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 12,
        }}>
          Asset-Status
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
          {assetGrid.map(a => {
            const sc = statusColor(a.status);
            return (
              <div key={a.label} style={{
                padding: '12px 14px',
                background: 'var(--bg-surface)',
                border: '0.5px solid var(--border-light)',
                borderRadius: 9,
                display: 'flex', flexDirection: 'column', gap: 6,
              }}>
                <span style={{ fontSize: 12, color: 'var(--text-primary)', fontWeight: 500 }}>
                  {a.label}
                </span>
                <span style={{
                  fontSize: 11, fontWeight: 600, padding: '2px 8px',
                  borderRadius: 6, alignSelf: 'flex-start',
                  background: sc.bg, color: sc.color,
                }}>
                  {a.status}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  // ── Tab: Checkliste ────────────────────────────────────────────────────────
  const TabCheckliste = () => {
    const items = [
      { text: 'Produktdaten vollständig', done: !!(product.name && product.short_desc) },
      { text: 'Preis gesetzt',            done: parseFloat(product.price_brutto) > 0 },
      { text: 'Features eingetragen',     done: (product.features?.length || 0) > 0 },
      { text: 'Stripe verknüpft',         done: !!product.stripe_price_id },
      { text: 'Checkout-Felder gesetzt',  done: (product.checkout_fields?.length || 0) > 0 },
      { text: 'Status auf Live',          done: product.status === 'live' },
      { text: 'Test-Kauf durchführen',    done: false },
    ];

    const doneCount = items.filter(i => i.done).length;

    const goLive = async () => {
      set('status')('live');
      // Delay slightly so state update propagates before save
      setTimeout(() => {
        setProduct(p => {
          const updated = { ...p, status: 'live' };
          // Slug sicherstellen + internes Flag entfernen
          const payload = {
            ...updated,
            slug: (updated.slug && updated.slug.trim()) || generateSlug(updated.name || ''),
          };
          delete payload._slugManuallyEdited;
          // trigger save with updated product
          setSaving(true); setMsg('');
          const isNew = selected === '__new__';
          const url = isNew
            ? `${API_BASE_URL}/api/products/`
            : `${API_BASE_URL}/api/products/${selected}`;
          fetch(url, {
            method: isNew ? 'POST' : 'PUT',
            headers: h,
            body: JSON.stringify(payload),
          }).then(r => r.json()).then(d => {
            if (d.slug) { setMsg('✓ Produkt ist jetzt Live'); loadProducts(); setSelected(d.slug); }
            else setMsg(d.detail || 'Fehler');
          }).catch(() => setMsg('Verbindungsfehler'))
            .finally(() => setSaving(false));
          return updated;
        });
      }, 0);
    };

    return (
      <div>
        {/* Progress */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20,
          padding: '12px 16px',
          background: doneCount >= 6 ? '#dcfce7' : 'var(--bg-surface)',
          border: `1px solid ${doneCount >= 6 ? '#86efac' : 'var(--border-light)'}`,
          borderRadius: 10,
        }}>
          <div style={{
            width: 44, height: 44, borderRadius: '50%',
            background: doneCount >= 6 ? '#1D9E75' : '#008eaa',
            color: 'white', display: 'flex', alignItems: 'center',
            justifyContent: 'center', fontSize: 15, fontWeight: 700, flexShrink: 0,
          }}>
            {doneCount}
          </div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
              {doneCount} von {items.length} erledigt
            </div>
            <div style={{ fontSize: 12, color: '#64748b' }}>
              {doneCount < 5 ? 'Noch nicht bereit für Live' :
               doneCount < items.length ? 'Fast fertig — gut gemacht!' :
               'Alles erledigt!'}
            </div>
          </div>
          {/* Progress bar */}
          <div style={{ flex: 1, height: 6, background: '#e2e8f0', borderRadius: 3, overflow: 'hidden' }}>
            <div style={{
              height: '100%', borderRadius: 3,
              background: doneCount >= 6 ? '#1D9E75' : '#008eaa',
              width: `${(doneCount / items.length) * 100}%`,
              transition: 'width 0.3s',
            }} />
          </div>
        </div>

        {/* Checklist items */}
        <div style={{ marginBottom: 24 }}>
          {items.map((item, i) => (
            <div key={i} style={{
              display: 'flex', alignItems: 'center', gap: 12,
              padding: '10px 14px', marginBottom: 6,
              background: item.done ? '#f0fdf4' : 'var(--bg-surface)',
              border: `1px solid ${item.done ? '#bbf7d0' : 'var(--border-light)'}`,
              borderRadius: 9,
            }}>
              <span style={{
                width: 22, height: 22, borderRadius: '50%', flexShrink: 0,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                background: item.done ? '#1D9E75' : '#e2e8f0',
                color: item.done ? 'white' : '#94a3b8',
                fontSize: 13, fontWeight: 700,
              }}>
                {item.done ? '✓' : '○'}
              </span>
              <span style={{
                fontSize: 13,
                color: item.done ? '#166534' : 'var(--text-primary)',
                fontWeight: item.done ? 500 : 400,
              }}>
                {item.text}
              </span>
            </div>
          ))}
        </div>

        {/* Go live button */}
        <button
          onClick={goLive}
          disabled={doneCount < 5 || product.status === 'live' || saving}
          style={{
            padding: '10px 24px', borderRadius: 9, border: 'none',
            background: doneCount >= 5 && product.status !== 'live' ? '#1D9E75' : '#94a3b8',
            color: 'white', fontSize: 13, fontWeight: 600,
            cursor: doneCount >= 5 && product.status !== 'live' ? 'pointer' : 'not-allowed',
          }}
        >
          {product.status === 'live' ? '✓ Bereits Live' : '🚀 Produkt live schalten'}
        </button>
        {doneCount < 5 && (
          <div style={{ marginTop: 8, fontSize: 11, color: '#94a3b8' }}>
            Mindestens 5 Punkte müssen erledigt sein
          </div>
        )}
      </div>
    );
  };

  return (
    <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
      <Sidebar />

      {/* ── Editor ── */}
      <div style={{ flex: 1, minWidth: 0 }}>

        {/* Header */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 12,
          marginBottom: 16, flexWrap: 'wrap',
        }}>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: 'var(--text-primary)' }}>
            {product.name || 'Neues Produkt'}
          </h2>
          <span style={{
            padding: '3px 10px', borderRadius: 10, fontSize: 11, fontWeight: 600,
            background: statusDot.bg + '22', color: statusDot.bg,
            border: `1px solid ${statusDot.bg}55`,
          }}>
            {statusDot.label}
          </span>
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 10 }}>
            {msg && (
              <span style={{
                fontSize: 12,
                color: msg.startsWith('✓') ? '#1D9E75' : '#E24B4A',
                fontWeight: 500,
              }}>
                {msg}
              </span>
            )}
            {selected !== '__new__' && (
              confirmDelete ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: 12, color: '#E24B4A', fontWeight: 600 }}>Wirklich löschen?</span>
                  <button
                    onClick={deleteProduct}
                    style={{
                      padding: '6px 14px', borderRadius: 7, border: 'none',
                      background: '#E24B4A', color: 'white',
                      fontSize: 12, fontWeight: 600, cursor: 'pointer',
                    }}
                  >Ja, löschen</button>
                  <button
                    onClick={() => setConfirmDelete(false)}
                    style={{
                      padding: '6px 12px', borderRadius: 7,
                      border: '1px solid var(--border-light)',
                      background: 'transparent', color: '#64748b',
                      fontSize: 12, cursor: 'pointer',
                    }}
                  >Abbrechen</button>
                </div>
              ) : (
                <button
                  onClick={() => setConfirmDelete(true)}
                  style={{
                    padding: '7px 14px', borderRadius: 8,
                    border: '1px solid #FECACA', background: '#FFF1F1',
                    color: '#A32D2D', fontSize: 12, fontWeight: 500, cursor: 'pointer',
                  }}
                >
                  🗑 Löschen
                </button>
              )
            )}
            <button
              onClick={save}
              disabled={saving}
              style={{
                padding: '8px 20px', borderRadius: 8, border: 'none',
                background: saving ? '#94a3b8' : '#008eaa',
                color: 'white', fontSize: 13, fontWeight: 600,
                cursor: saving ? 'not-allowed' : 'pointer',
              }}
            >
              {saving ? 'Speichert...' : '💾 Speichern'}
            </button>
          </div>
        </div>

        {/* Tab bar */}
        <div style={{
          display: 'flex', gap: 4, marginBottom: 20,
          borderBottom: '1.5px solid var(--border-light)',
          paddingBottom: 0,
        }}>
          {TABS.map(t => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              style={{
                padding: '8px 14px', border: 'none', background: 'transparent',
                fontSize: 12, fontWeight: activeTab === t.id ? 600 : 400,
                color: activeTab === t.id ? '#008eaa' : '#64748b',
                borderBottom: activeTab === t.id ? '2px solid #008eaa' : '2px solid transparent',
                cursor: 'pointer', fontFamily: 'inherit',
                marginBottom: -1.5, transition: 'all 0.15s',
              }}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        {activeTab === 'produktdaten' && <TabProduktdaten />}
        {activeTab === 'preis'        && <TabPreis />}
        {activeTab === 'checkout'     && <TabCheckout />}
        {activeTab === 'assets'       && <TabAssets />}
        {activeTab === 'checkliste'   && <TabCheckliste />}
      </div>
    </div>
  );
}
