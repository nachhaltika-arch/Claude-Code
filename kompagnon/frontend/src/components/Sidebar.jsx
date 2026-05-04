import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import KompagnonLogo from './KompagnonLogo';

// Sidebar-Bereiche aligned mit der 5-Stage-Vision (siehe docs/audit-2026-05-04.md)
//   AKQUISE     — Stage 1: Lead-Quellen & Audit
//   PROJEKTE    — Stage 2: Briefing → Asset → Go-Live
//   PERFORMANCE — Stage 3: Ads, Funnels, Tracking, Reports
//   BESTAND     — Stage 4: Aktive Kunden, Upsell, Tickets
//   KOMPAGNON   — Eigen-Marketing (admin only)
//
// Items mit comingSoon=true sind im Konzept verankert, aber noch nicht gebaut —
// werden im Menü greyed-out angezeigt und sind nicht klickbar.
const AREAS = {
  akquise: {
    label: 'Akquise', icon: '🎯', color: 'var(--brand-primary)',
    items: [
      { label: 'Dashboard',           path: '/app/dashboard', icon: '🏠' },
      { label: 'Lead-Inbox',          path: '/app/leads',     icon: '📥' },
      { label: 'Vertriebspipeline',   path: '/app/deals',     icon: '💼' },
      { label: 'Kampagnen',           path: '/app/campaigns', icon: '📊', adminOnly: true },
      { label: 'Website-Audit',       path: '/app/audit',     icon: '🔍' },
      { label: 'Unternehmen',         path: '/app/companies', icon: '🏢' },
      { label: 'Akademie',            path: '/app/academy',   icon: '🎓' },
    ],
  },
  projekte: {
    label: 'Projekte', icon: '🚀', color: '#7c3aed',
    items: [
      { label: 'Dashboard',           path: '/app/dashboard',  icon: '🏠' },
      { label: 'Aktive Projekte',     path: '/app/projects',   icon: '📋' },
      { label: 'Briefings',           path: '/app/briefings',  icon: '✏️', comingSoon: true },
      { label: 'Checklisten',         path: '/app/checklists', icon: '✅' },
      { label: 'Public Pages',        path: '/app/pages',      icon: '🎨', adminOnly: true },
      { label: 'Akademie',            path: '/app/academy',    icon: '🎓' },
    ],
  },
  performance: {
    label: 'Performance', icon: '📊', color: '#059669',
    items: [
      { label: 'Dashboard',             path: '/app/dashboard', icon: '🏠' },
      { label: 'Ads-Kampagnen',         path: '/app/ads',       icon: '💰', comingSoon: true },
      { label: 'Funnels',               path: '/app/funnels',   icon: '🔄', comingSoon: true },
      { label: 'A/B-Tests',             path: '/app/ab-tests',  icon: '🧪', comingSoon: true },
      { label: 'Performance-Reports',   path: '/app/retainer',  icon: '📈', adminOnly: true },
      { label: 'Webhook-Status',        path: '/app/webhooks',  icon: '⚡', adminOnly: true },
      { label: 'Akademie',              path: '/app/academy',   icon: '🎓' },
    ],
  },
  bestand: {
    label: 'Bestand', icon: '🏢', color: '#d97706',
    items: [
      { label: 'Dashboard',         path: '/app/dashboard',  icon: '🏠' },
      { label: 'Aktive Kunden',     path: '/app/customers',  icon: '👤' },
      { label: 'Upsell-Pipeline',   path: '/app/retainer',   icon: '💎', adminOnly: true },
      { label: 'Support-Tickets',   path: '/app/tickets',    icon: '🎫' },
      { label: 'Newsletter',        path: '/app/newsletter', icon: '📧' },
      { label: 'Akademie',          path: '/app/academy',    icon: '🎓' },
    ],
  },
  kompagnon: {
    label: 'KOMPAGNON', icon: '🔧', color: '#0891b2', adminOnly: true,
    items: [
      { label: 'Dashboard',           path: '/app/dashboard',            icon: '🏠' },
      { label: 'KAS-Website',         path: '/app/settings/kas-website', icon: '🌐' },
      { label: 'Eigene Funnels',      path: '/app/pages',                icon: '🎯' },
      { label: 'Newsletter',          path: '/app/newsletter',           icon: '📧' },
      { label: 'Akademie-Admin',      path: '/app/academy/admin',        icon: '🎓' },
      { label: 'Produktentwicklung',  path: '/app/product',              icon: '🛠️' },
      { label: 'Produkte & Preise',   path: '/app/products',             icon: '📦' },
    ],
  },
};

// Migration der alten Bereichs-Namen aus localStorage auf neue 5-Stage-Vision-Bereiche.
// Beim ersten Login nach Deploy mappen wir alte Bereiche → neue Bereiche, damit User
// nicht in einem nicht-existenten Bereich landen.
const LEGACY_AREA_MAP = {
  sales:    'akquise',
  delivery: 'projekte',
  quality:  'projekte',
  upsales:  'bestand',
  product:  'kompagnon',
};

function _resolveInitialArea() {
  const stored = localStorage.getItem('kompagnon_area');
  if (stored && AREAS[stored]) return stored;
  if (stored && LEGACY_AREA_MAP[stored]) return LEGACY_AREA_MAP[stored];
  return 'akquise';
}

export default function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, hasRole } = useAuth();
  const [activeArea, setActiveArea] = useState(_resolveInitialArea);
  const [areaOpen, setAreaOpen] = useState(false);

  // Close area dropdown on outside click (must be before early return to satisfy rules-of-hooks)
  useEffect(() => {
    if (!areaOpen) return;
    const close = () => setAreaOpen(false);
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, [areaOpen]);

  if (user?.role === 'kunde') {
    const kundeItems = [
      { label: 'Dashboard', path: '/app/dashboard', icon: '🏠' },
      { label: 'Meine Kartei', path: user.lead_id ? `/app/leads/${user.lead_id}` : '/app/dashboard', icon: '📋' },
      { label: 'Akademie', path: '/app/academy', icon: '🎓' },
      { label: 'Einstellungen', path: '/app/settings', icon: '⚙️' },
    ];
    return (
      <aside className="sidebar">
        <div className="px-4 py-5 border-b border-white/10">
          <div className="cursor-pointer" onClick={() => navigate('/app/dashboard')}>
            {/* Dark sidebar background → white variant */}
            <KompagnonLogo height={32} variant="white" />
          </div>
        </div>
        <nav className="flex-1 px-2 py-3 overflow-y-auto" style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {kundeItems.map((item) => {
            const active = location.pathname === item.path || location.pathname.startsWith(item.path + '/');
            return (
              <button key={item.path} onClick={() => navigate(item.path)} style={{
                width: '100%', display: 'flex', alignItems: 'center', gap: 10,
                padding: '10px 12px', background: active ? 'rgba(13,110,253,0.2)' : 'transparent',
                border: 'none', borderRadius: 'var(--radius-md)', cursor: 'pointer',
                color: active ? '#fff' : 'rgba(255,255,255,0.65)', textAlign: 'left',
                borderLeft: active ? '3px solid #0d6efd' : '3px solid transparent',
                fontWeight: active ? 600 : 400, fontSize: 14,
              }}>
                <span style={{ fontSize: 18, flexShrink: 0 }} aria-hidden="true">{item.icon}</span>
                {item.label}
              </button>
            );
          })}
        </nav>
        <div style={{ padding: '12px 16px', borderTop: '1px solid rgba(255,255,255,0.08)', display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 32, height: 32, borderRadius: '50%', background: '#0d6efd', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 700, fontSize: 13 }}>
            {(user.first_name?.[0] || 'K').toUpperCase()}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: '#fff' }}>{user.first_name} {user.last_name}</div>
            <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)' }}>Kunde</div>
          </div>
          <button onClick={logout} style={{ background: 'none', border: 'none', color: 'rgba(255,255,255,0.4)', cursor: 'pointer', fontSize: 18 }} title="Abmelden">⏻</button>
        </div>
      </aside>
    );
  }

  const switchArea = (id) => { setActiveArea(id); localStorage.setItem('kompagnon_area', id); setAreaOpen(false); navigate('/app/dashboard'); };
  const currentArea = AREAS[activeArea] || AREAS.akquise;

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="px-4 py-5 border-b border-white/10">
        <div className="cursor-pointer" onClick={() => navigate('/app/dashboard')}>
          {/* Dark sidebar background → white variant */}
          <KompagnonLogo height={32} variant="white" />
        </div>
      </div>

      {/* Area Selector */}
      <div style={{ padding: 12, borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
        <div style={{ fontSize: 10, fontWeight: 700, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: 6, paddingLeft: 4 }}>
          Bereich
        </div>
        <div style={{ position: 'relative' }} onMouseDown={(e) => e.stopPropagation()}>
          <button onClick={() => setAreaOpen(!areaOpen)} style={{
            width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '10px 12px', background: `${currentArea.color}25`, border: `1px solid ${currentArea.color}50`,
            borderRadius: 10, cursor: 'pointer', color: '#fff',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 18 }}>{currentArea.icon}</span>
              <span style={{ fontSize: 14, fontWeight: 700 }}>{currentArea.label}</span>
            </div>
            <span style={{ color: 'rgba(255,255,255,0.5)', fontSize: 12, transition: 'transform 0.2s', transform: areaOpen ? 'rotate(180deg)' : 'rotate(0)' }}>▼</span>
          </button>
          {areaOpen && (
            <div style={{ position: 'absolute', top: 'calc(100% + 6px)', left: 0, right: 0, background: '#1e3a5f', borderRadius: 10, overflow: 'hidden', zIndex: 100, boxShadow: '0 8px 32px rgba(0,0,0,0.4)', border: '1px solid rgba(255,255,255,0.1)' }}>
              {Object.entries(AREAS).filter(([, a]) => !a.adminOnly || hasRole('admin')).map(([id, area]) => (
                <button key={id} onClick={() => switchArea(id)} style={{
                  width: '100%', display: 'flex', alignItems: 'center', gap: 10, padding: '11px 14px',
                  background: activeArea === id ? `${area.color}30` : 'transparent', border: 'none', cursor: 'pointer', color: '#fff', textAlign: 'left',
                  borderLeft: activeArea === id ? `3px solid ${area.color}` : '3px solid transparent',
                }}>
                  <span style={{ fontSize: 18 }}>{area.icon}</span>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: activeArea === id ? 700 : 500 }}>{area.label}</div>
                    <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.45)' }}>{area.items.length} Menuepunkte</div>
                  </div>
                  {activeArea === id && <span style={{ marginLeft: 'auto', color: area.color, fontSize: 14 }}>✓</span>}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Navigation from active area */}
      <nav className="flex-1 px-2 py-3 overflow-y-auto" style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {currentArea.items
          .filter((item) => !item.adminOnly || hasRole('admin'))
          .map((item) => {
            const active   = !item.comingSoon && (location.pathname === item.path || location.pathname.startsWith(item.path + '/'));
            const disabled = !!item.comingSoon;
            return (
              <button
                key={item.path}
                onClick={disabled ? (e) => e.preventDefault() : () => navigate(item.path)}
                title={disabled ? 'In Entwicklung — Sprint 2-3' : undefined}
                aria-disabled={disabled}
                style={{
                  width: '100%', display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px',
                  background: active ? `${currentArea.color}20` : 'transparent', border: 'none', borderRadius: 'var(--radius-md)',
                  cursor: disabled ? 'not-allowed' : 'pointer',
                  color: disabled ? 'rgba(255,255,255,0.30)' : (active ? '#fff' : 'rgba(255,255,255,0.65)'),
                  textAlign: 'left',
                  borderLeft: active ? `3px solid ${currentArea.color}` : '3px solid transparent',
                  fontWeight: active ? 600 : 400, fontSize: 14, transition: 'all 0.15s',
                  opacity: disabled ? 0.55 : 1,
                }}
              >
                <span style={{ fontSize: 18, flexShrink: 0 }} aria-hidden="true">{item.icon}</span>
                <span style={{ flex: 1 }}>{item.label}</span>
                {disabled && (
                  <span style={{
                    fontSize: 9, fontWeight: 700, letterSpacing: '0.06em',
                    padding: '2px 6px', borderRadius: 4,
                    background: 'rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.45)',
                    textTransform: 'uppercase',
                  }}>Bald</span>
                )}
              </button>
            );
          })}

        {/* Admin section — always visible */}
        {hasRole('admin') && (
          <>
            <div style={{ height: 1, background: 'rgba(255,255,255,0.08)', margin: '12px 8px' }} />
            {[
              { label: 'Einstellungen', path: '/app/settings', icon: '⚙️' },
            ].map((item) => (
              <button key={item.path} onClick={() => navigate(item.path)} style={{
                width: '100%', display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px',
                background: location.pathname.startsWith(item.path) ? 'rgba(255,255,255,0.08)' : 'transparent',
                border: 'none', borderRadius: 'var(--radius-md)', cursor: 'pointer', color: 'rgba(255,255,255,0.55)', textAlign: 'left', fontSize: 13,
              }}>
                <span style={{ fontSize: 16 }}>{item.icon}</span>
                {item.label}
              </button>
            ))}
          </>
        )}
      </nav>

      {/* User Footer */}
      <div className="px-3 py-4 border-t border-white/10">
        {user && (
          <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-white/5 mb-2">
            <div className="w-8 h-8 rounded-full bg-kompagnon-400 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
              {user.first_name?.[0] || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-white text-sm font-medium truncate">{user.first_name} {user.last_name}</div>
              <div className="text-kompagnon-300 text-xs truncate">{user.role}</div>
            </div>
          </div>
        )}
        <button onClick={() => { logout(); navigate('/'); }} className="w-full nav-item text-red-400 hover:bg-red-500/10 hover:text-red-300">
          <span>🚪</span>
          <span>Abmelden</span>
        </button>
      </div>
    </aside>
  );
}
