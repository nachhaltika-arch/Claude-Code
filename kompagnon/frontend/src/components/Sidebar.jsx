import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const AREAS = {
  sales: {
    label: 'Sales', icon: '💼', color: '#008EAA',
    items: [
      { label: 'Dashboard', path: '/app/dashboard', icon: '🏠' },
      { label: 'Lead Pipeline', path: '/app/leads', icon: '👥' },
      { label: 'Website Audit', path: '/app/audit', icon: '🔍' },
      { label: 'Kontakt Import', path: '/app/import', icon: '📥' },
      { label: 'Massen Export', path: '/app/export', icon: '📤' },
    ],
  },
  delivery: {
    label: 'Delivery', icon: '🚀', color: '#7c3aed',
    items: [
      { label: 'Dashboard', path: '/app/dashboard', icon: '🏠' },
      { label: 'Kundenprojekte', path: '/app/projects', icon: '📋' },
      { label: 'Website Audit', path: '/app/audit', icon: '🔍' },
    ],
  },
  quality: {
    label: 'Quality', icon: '✅', color: '#059669',
    items: [
      { label: 'Dashboard', path: '/app/dashboard', icon: '🏠' },
      { label: 'Support Tickets', path: '/app/tickets', icon: '🎫' },
      { label: 'Checklisten', path: '/app/checklists', icon: '📝' },
    ],
  },
  upsales: {
    label: 'Upsales', icon: '📈', color: '#d97706',
    items: [
      { label: 'Dashboard', path: '/app/dashboard', icon: '🏠' },
      { label: 'Kunden', path: '/app/customers', icon: '👤' },
    ],
  },
  product: {
    label: 'Produkt', icon: '🛠️', color: '#0891b2', adminOnly: true,
    items: [
      { label: 'Dashboard', path: '/app/dashboard', icon: '🏠' },
      { label: 'Produktentwicklung', path: '/app/product', icon: '🛠️' },
      { label: 'Support Tickets', path: '/app/tickets', icon: '🎫' },
    ],
  },
};

export default function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, hasRole } = useAuth();
  const [activeArea, setActiveArea] = useState(localStorage.getItem('kompagnon_area') || 'sales');
  const [areaOpen, setAreaOpen] = useState(false);

  const switchArea = (id) => { setActiveArea(id); localStorage.setItem('kompagnon_area', id); setAreaOpen(false); navigate('/app/dashboard'); };
  const currentArea = AREAS[activeArea] || AREAS.sales;

  // Close dropdown on outside click
  useEffect(() => {
    if (!areaOpen) return;
    const close = () => setAreaOpen(false);
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, [areaOpen]);

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="px-4 py-5 border-b border-white/10">
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/app/dashboard')}>
          <div className="w-9 h-9 rounded-xl bg-white/15 flex items-center justify-center">
            <span className="text-white font-black text-sm">HS</span>
          </div>
          <div>
            <div className="text-white font-bold text-sm tracking-wide">KOMPAGNON</div>
            <div className="text-kompagnon-300 text-xs">Automation System</div>
          </div>
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
        {currentArea.items.map((item) => {
          const active = location.pathname === item.path || location.pathname.startsWith(item.path + '/');
          return (
            <button key={item.path} onClick={() => navigate(item.path)} style={{
              width: '100%', display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px',
              background: active ? `${currentArea.color}20` : 'transparent', border: 'none', borderRadius: 8, cursor: 'pointer',
              color: active ? '#fff' : 'rgba(255,255,255,0.65)', textAlign: 'left',
              borderLeft: active ? `3px solid ${currentArea.color}` : '3px solid transparent',
              fontWeight: active ? 600 : 400, fontSize: 14, transition: 'all 0.15s',
            }}>
              <span style={{ fontSize: 18, flexShrink: 0 }}>{item.icon}</span>
              {item.label}
            </button>
          );
        })}

        {/* Admin section — always visible */}
        {hasRole('admin') && (
          <>
            <div style={{ height: 1, background: 'rgba(255,255,255,0.08)', margin: '12px 8px' }} />
            {[
              { label: 'Benutzerverwaltung', path: '/app/settings/users', icon: '🧑‍💼' },
              { label: 'Einstellungen', path: '/app/settings', icon: '⚙️' },
            ].map((item) => (
              <button key={item.path} onClick={() => navigate(item.path)} style={{
                width: '100%', display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px',
                background: location.pathname.startsWith(item.path) ? 'rgba(255,255,255,0.08)' : 'transparent',
                border: 'none', borderRadius: 8, cursor: 'pointer', color: 'rgba(255,255,255,0.55)', textAlign: 'left', fontSize: 13,
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
