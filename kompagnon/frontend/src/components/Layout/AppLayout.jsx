import React, { useState, useEffect } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useScreenSize } from '../../utils/responsive';
import Logo from '../Logo';

// ── SVG Icons (16x16) ──────────────────────────────────────────

const icons = {
  grid: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="1.5" y="1.5" width="5" height="5" rx="1"/><rect x="9.5" y="1.5" width="5" height="5" rx="1"/>
      <rect x="1.5" y="9.5" width="5" height="5" rx="1"/><rect x="9.5" y="9.5" width="5" height="5" rx="1"/>
    </svg>
  ),
  chart: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="8" width="3" height="6" rx="0.5"/><rect x="6.5" y="4" width="3" height="10" rx="0.5"/>
      <rect x="11" y="2" width="3" height="12" rx="0.5"/>
    </svg>
  ),
  users: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="6" cy="5" r="2.5"/><path d="M1.5 14c0-2.5 2-4.5 4.5-4.5s4.5 2 4.5 4.5"/>
      <circle cx="11" cy="5.5" r="1.8"/><path d="M11 9.5c1.8 0 3.5 1.3 3.5 3.5"/>
    </svg>
  ),
  docCheck: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 1.5H4a1.5 1.5 0 00-1.5 1.5v10A1.5 1.5 0 004 14.5h8a1.5 1.5 0 001.5-1.5V6L9 1.5z"/>
      <path d="M6 10l1.5 1.5L10 8"/>
    </svg>
  ),
  gradCap: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M8 2L1.5 6 8 10l6.5-4L8 2z"/><path d="M4 8v3.5c0 1 1.8 2 4 2s4-1 4-2V8"/>
      <path d="M14.5 6v4.5"/>
    </svg>
  ),
  gear: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="8" cy="8" r="2"/><path d="M13.4 10a1.2 1.2 0 00.2 1.3l.04.04a1.44 1.44 0 11-2.04 2.04l-.04-.04a1.2 1.2 0 00-1.3-.2 1.2 1.2 0 00-.72 1.1v.12a1.44 1.44 0 01-2.88 0v-.06a1.2 1.2 0 00-.78-1.1 1.2 1.2 0 00-1.3.2l-.04.04a1.44 1.44 0 11-2.04-2.04l.04-.04a1.2 1.2 0 00.2-1.3 1.2 1.2 0 00-1.1-.72h-.12a1.44 1.44 0 010-2.88h.06a1.2 1.2 0 001.1-.78 1.2 1.2 0 00-.2-1.3l-.04-.04A1.44 1.44 0 114.3 2.24l.04.04a1.2 1.2 0 001.3.2h.06a1.2 1.2 0 00.72-1.1V1.26a1.44 1.44 0 012.88 0v.06a1.2 1.2 0 00.72 1.1 1.2 1.2 0 001.3-.2l.04-.04a1.44 1.44 0 112.04 2.04l-.04.04a1.2 1.2 0 00-.2 1.3v.06a1.2 1.2 0 001.1.72h.12a1.44 1.44 0 010 2.88h-.06a1.2 1.2 0 00-1.1.72z"/>
    </svg>
  ),
  key: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="10.5" cy="5.5" r="3"/><path d="M2 14l5.3-5.3"/><path d="M5.8 10.2l1.5 1.5"/>
    </svg>
  ),
  dots: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
      <circle cx="4" cy="8" r="1.2"/><circle cx="8" cy="8" r="1.2"/><circle cx="12" cy="8" r="1.2"/>
    </svg>
  ),
  logout: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 14H3a1 1 0 01-1-1V3a1 1 0 011-1h3"/><path d="M10.5 11.5L14 8l-3.5-3.5"/><path d="M14 8H6"/>
    </svg>
  ),
};

// ── Nav structure ──────────────────────────────────────────────

const NAV_SECTIONS = [
  {
    title: 'ÜBERSICHT',
    items: [
      { label: 'Dashboard', path: '/app/dashboard', icon: 'grid' },
    ],
  },
  {
    title: 'SALES',
    items: [
      { label: 'Vertriebspipeline', path: '/app/sales', icon: 'chart' },
      { label: 'Domain Import', path: '/app/import', icon: 'users' },
      { label: 'Export', path: '/app/export', icon: 'docCheck' },
      { label: 'Website Audit', path: '/app/audit', icon: 'docCheck' },
    ],
  },
  {
    title: 'DELIVERY',
    items: [
      { label: 'Projektpipeline', path: '/app/leads', icon: 'chart' },
      { label: 'Kundenprojekte', path: '/app/projects', icon: 'users' },
    ],
  },
  {
    title: 'QUALITÄT',
    items: [
      { label: 'Support Tickets', path: '/app/tickets', icon: 'docCheck' },
      { label: 'Produktentwicklung', path: '/app/product', icon: 'gear', adminOnly: true },
    ],
  },
  {
    title: 'AKADEMIE',
    items: [
      { label: 'Akademy', path: '/app/academy', icon: 'gradCap' },
    ],
  },
  {
    title: 'EINSTELLUNGEN',
    items: [
      { label: 'Einstellungen', path: '/app/settings', icon: 'gear' },
      { label: 'Benutzerverwaltung', path: '/app/settings/users', icon: 'key', adminOnly: true },
    ],
  },
];

const PAGE_NAMES = {
  '/app/dashboard': 'Dashboard',
  '/app/sales': 'Vertriebspipeline',
  '/app/leads': 'Projektpipeline',
  '/app/customers': 'Kunden',
  '/app/audit': 'Website Audit',
  '/app/akademie': 'Akademy',
  '/app/academy': 'Akademy',
  '/app/settings': 'Einstellungen',
  '/app/projects': 'Kundenprojekte',
  '/app/import': 'Domain Import',
  '/app/export': 'Export',
  '/app/tickets': 'Support Tickets',
  '/app/profile': 'Profil',
  '/app/checklists': 'Checklisten',
  '/app/product': 'Produktentwicklung',
};

const MOBILE_TABS = [
  { label: 'Dashboard', path: '/app/dashboard', icon: 'grid' },
  { label: 'Vertrieb', path: '/app/sales', icon: 'chart' },
  { label: 'Projekte', path: '/app/leads', icon: 'users' },
  { label: 'Audit', path: '/app/audit', icon: 'docCheck' },
  { label: 'Tickets', path: '/app/tickets', icon: 'key' },
];

// ── Sidebar ────────────────────────────────────────────────────

function SidebarNav({ badges }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, hasRole } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  const isActive = (path) => location.pathname === path || location.pathname.startsWith(path + '/');

  return (
    <aside style={{
      position: 'fixed', left: 0, top: 0, bottom: 0,
      width: 'var(--sidebar-width)', background: 'var(--bg-sidebar)',
      borderRight: '1px solid var(--border-light)',
      display: 'flex', flexDirection: 'column',
      zIndex: 40, overflowY: 'auto',
    }}>
      {/* Logo */}
      <div style={{
        padding: '20px 16px', borderBottom: '1px solid var(--border-light)',
        cursor: 'pointer',
      }} onClick={() => navigate('/app/dashboard')}>
        <div style={{ color: 'var(--brand-primary)' }}>
          <Logo size="small" />
        </div>
        <div style={{
          fontSize: 10, color: 'var(--text-tertiary)',
          letterSpacing: '0.06em', textTransform: 'uppercase',
          marginTop: 4,
        }}>
          Automation System
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1, padding: '12px 8px', overflowY: 'auto' }}>
        {NAV_SECTIONS.map((section) => {
          const visibleItems = section.items.filter(i => !i.adminOnly || hasRole('admin'));
          if (visibleItems.length === 0) return null;
          return (
            <div key={section.title} style={{ marginBottom: 16 }}>
              <div style={{
                fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)',
                letterSpacing: '0.08em', textTransform: 'uppercase',
                padding: '0 10px', marginBottom: 4,
              }}>
                {section.title}
              </div>
              {visibleItems.map((item) => {
                const active = isActive(item.path);
                return (
                  <button
                    key={item.path}
                    onClick={() => navigate(item.path)}
                    style={{
                      width: '100%', display: 'flex', alignItems: 'center', gap: 8,
                      padding: '7px 10px', border: 'none', borderRadius: 'var(--radius-md)',
                      cursor: 'pointer', fontSize: 13, textAlign: 'left',
                      fontFamily: 'var(--font-sans)',
                      background: active ? 'var(--bg-active)' : 'transparent',
                      color: active ? 'var(--brand-primary)' : 'var(--text-secondary)',
                      fontWeight: active ? 500 : 400,
                      transition: 'background 0.15s, color 0.15s',
                    }}
                    onMouseEnter={e => { if (!active) { e.currentTarget.style.background = 'var(--bg-hover)'; e.currentTarget.style.color = 'var(--text-primary)'; }}}
                    onMouseLeave={e => { if (!active) { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text-secondary)'; }}}
                  >
                    <span style={{ flexShrink: 0, display: 'flex' }}>{icons[item.icon]}</span>
                    <span>{item.label}</span>
                    {item.badgeKey && badges[item.badgeKey] > 0 && (
                      <span style={{
                        marginLeft: 'auto', fontSize: 10, padding: '1px 6px',
                        borderRadius: 10,
                        background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)',
                        fontWeight: 600,
                      }}>
                        {badges[item.badgeKey]}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          );
        })}
      </nav>

      {/* Footer */}
      {user && (
        <div style={{
          marginTop: 'auto', borderTop: '1px solid var(--border-light)',
          padding: '12px 8px', position: 'relative',
        }}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: 10, padding: '6px 8px',
            borderRadius: 'var(--radius-md)',
          }}>
            <div style={{
              width: 32, height: 32, borderRadius: '50%',
              background: 'var(--brand-primary-light)', color: 'var(--brand-primary)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 13, fontWeight: 600, flexShrink: 0,
            }}>
              {(user.first_name?.[0] || 'U').toUpperCase()}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {user.first_name} {user.last_name}
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)', textTransform: 'capitalize' }}>
                {user.role}
              </div>
            </div>
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              style={{
                background: 'none', border: 'none', padding: 4,
                color: 'var(--text-tertiary)', cursor: 'pointer',
                display: 'flex', borderRadius: 'var(--radius-sm)',
              }}
            >
              {icons.dots}
            </button>
          </div>

          {menuOpen && (
            <>
              <div style={{ position: 'fixed', inset: 0, zIndex: 50 }} onClick={() => setMenuOpen(false)} />
              <div style={{
                position: 'absolute', bottom: '100%', left: 8, right: 8,
                background: 'var(--bg-elevated)', border: '1px solid var(--border-light)',
                borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-elevated)',
                padding: 4, zIndex: 51, marginBottom: 4,
              }}>
                <button
                  onClick={() => { navigate('/app/profile'); setMenuOpen(false); }}
                  style={{
                    width: '100%', display: 'flex', alignItems: 'center', gap: 8,
                    padding: '7px 10px', border: 'none', borderRadius: 'var(--radius-sm)',
                    background: 'transparent', cursor: 'pointer', fontSize: 13,
                    color: 'var(--text-secondary)', fontFamily: 'var(--font-sans)',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  Profil
                </button>
                <button
                  onClick={() => { logout(); navigate('/'); setMenuOpen(false); }}
                  style={{
                    width: '100%', display: 'flex', alignItems: 'center', gap: 8,
                    padding: '7px 10px', border: 'none', borderRadius: 'var(--radius-sm)',
                    background: 'transparent', cursor: 'pointer', fontSize: 13,
                    color: 'var(--status-danger-text)', fontFamily: 'var(--font-sans)',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--status-danger-bg)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  {icons.logout}
                  <span>Abmelden</span>
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </aside>
  );
}

// ── Topbar ─────────────────────────────────────────────────────

function Topbar({ pageName, ctaLabel, ctaAction }) {
  const now = new Date();
  const dateStr = now.toLocaleDateString('de-DE', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });

  return (
    <header style={{
      height: 'var(--topbar-height)', minHeight: 56,
      borderBottom: '1px solid var(--border-light)',
      background: 'var(--bg-surface)',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 24px',
      position: 'sticky', top: 0, zIndex: 30,
    }}>
      <span style={{ fontSize: 15, fontWeight: 500, color: 'var(--text-primary)' }}>
        {pageName}
      </span>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>{dateStr}</span>
        {ctaLabel && (
          <button
            onClick={ctaAction}
            style={{
              background: 'var(--brand-primary)', color: 'var(--text-inverse)',
              border: 'none', padding: '7px 16px', borderRadius: 'var(--radius-md)',
              fontSize: 13, fontWeight: 500, cursor: 'pointer',
              fontFamily: 'var(--font-sans)',
              transition: 'background 0.15s',
            }}
            onMouseEnter={e => e.currentTarget.style.background = 'var(--brand-primary-dark)'}
            onMouseLeave={e => e.currentTarget.style.background = 'var(--brand-primary)'}
          >
            {ctaLabel}
          </button>
        )}
      </div>
    </header>
  );
}

// ── Bottom Nav (Mobile) ────────────────────────────────────────

function BottomNav() {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <nav style={{
      position: 'fixed', bottom: 0, left: 0, right: 0,
      background: 'var(--bg-surface)',
      borderTop: '1px solid var(--border-light)',
      display: 'flex', justifyContent: 'space-around',
      padding: '6px 0 calc(6px + env(safe-area-inset-bottom))',
      zIndex: 100,
    }}>
      {MOBILE_TABS.map((tab) => {
        const active = location.pathname === tab.path || location.pathname.startsWith(tab.path + '/');
        return (
          <button
            key={tab.path}
            onClick={() => navigate(tab.path)}
            style={{
              background: 'none', border: 'none',
              display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2,
              padding: '4px 8px', cursor: 'pointer', minWidth: 48,
              color: active ? 'var(--brand-primary)' : 'var(--text-tertiary)',
              transition: 'color 0.15s',
            }}
          >
            <span style={{ display: 'flex' }}>{icons[tab.icon]}</span>
            <span style={{ fontSize: 9, fontWeight: active ? 600 : 400 }}>{tab.label}</span>
          </button>
        );
      })}
    </nav>
  );
}

// ── Main Layout ────────────────────────────────────────────────

export default function AppLayout() {
  const { isMobile } = useScreenSize();
  const { user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [badges, setBadges] = useState({ pipeline: 0, audits: 0 });

  const pageName = PAGE_NAMES[location.pathname] ||
    Object.entries(PAGE_NAMES).find(([p]) => location.pathname.startsWith(p + '/'))?.[1] ||
    'KOMPAGNON';

  // CTA mapping per page
  const ctaMap = {
    '/app/dashboard': null,
    '/app/leads': { label: '+ Neuer Lead', action: () => navigate('/app/import') },
    '/app/audit': { label: '+ Neues Audit', action: () => {} },
    '/app/customers': null,
  };
  const cta = ctaMap[location.pathname];

  return (
    <div style={{ height: '100vh', overflow: 'hidden', display: 'flex' }}>
      {/* Sidebar — desktop only */}
      {!isMobile && user && <SidebarNav badges={badges} />}

      {/* Main area */}
      <div style={{
        flex: 1,
        marginLeft: !isMobile && user ? 'var(--sidebar-width)' : 0,
        display: 'flex', flexDirection: 'column',
        height: '100vh', overflow: 'hidden',
      }}>
        {/* Topbar — desktop only */}
        {!isMobile && (
          <Topbar
            pageName={pageName}
            ctaLabel={cta?.label}
            ctaAction={cta?.action}
          />
        )}

        {/* Mobile header */}
        {isMobile && (
          <header style={{
            padding: '12px 16px', background: 'var(--bg-surface)',
            borderBottom: '1px solid var(--border-light)',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            position: 'sticky', top: 0, zIndex: 30,
          }}>
            <div style={{ color: 'var(--brand-primary)' }}>
              <Logo size="small" />
            </div>
            <span style={{ fontSize: 14, fontWeight: 500, color: 'var(--text-primary)' }}>
              {pageName}
            </span>
          </header>
        )}

        {/* Content */}
        <main style={{
          flex: 1, overflowY: 'auto', overflowX: 'hidden',
          padding: isMobile ? 16 : '20px 28px',
          paddingBottom: isMobile ? 80 : 20,
        }}>
          <Outlet />
        </main>
      </div>

      {/* Bottom nav — mobile only */}
      {isMobile && user && <BottomNav />}
    </div>
  );
}
