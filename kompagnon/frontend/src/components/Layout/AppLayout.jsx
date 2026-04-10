import React, { useState, useEffect, useCallback } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useScreenSize } from '../../utils/responsive';
import { useTheme } from '../../context/ThemeContext';
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts';
import { usePullToRefresh } from '../../hooks/useTouch';
import PullIndicator from '../ui/PullIndicator';
import CommandPalette from '../CommandPalette';
import ShortcutHelp from '../ShortcutHelp';
import API_BASE_URL from '../../config';
import Logo from '../Logo';
import KompagnonLogo from '../KompagnonLogo';

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
  book: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 2.5A1.5 1.5 0 013.5 1h9A1.5 1.5 0 0114 2.5v11a1.5 1.5 0 01-1.5 1.5h-9A1.5 1.5 0 012 13.5V2.5z"/>
      <path d="M5 1v14M5 5h6M5 8h6M5 11h4"/>
    </svg>
  ),
  newspaper: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="1.5" y="2.5" width="13" height="11" rx="1.5"/>
      <path d="M4.5 6h7M4.5 8.5h7M4.5 11h4"/>
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
  menu: (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <line x1="3" y1="5" x2="15" y2="5"/><line x1="3" y1="9" x2="15" y2="9"/><line x1="3" y1="13" x2="15" y2="13"/>
    </svg>
  ),
  gear: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="8" cy="8" r="2.5"/><path d="M8 1.5v1.5M8 13v1.5M1.5 8H3M13 8h1.5M3.05 3.05l1.06 1.06M11.89 11.89l1.06 1.06M3.05 12.95l1.06-1.06M11.89 4.11l1.06-1.06"/>
    </svg>
  ),
};

// ── Nav structure ──────────────────────────────────────────────

const NAV_SECTIONS = [
  {
    title: 'Übersicht',
    items: [
      { label: 'Dashboard', path: '/app/dashboard', icon: 'grid' },
    ],
  },
  {
    title: 'Sales',
    items: [
      { label: 'Deals',         path: '/app/deals',     icon: 'chart' },
      { label: 'Kampagnen',     path: '/app/campaigns', icon: 'chart', adminOnly: true },
      { label: 'Unternehmen',   path: '/app/companies', icon: 'users', activePaths: ['/app/companies', '/app/leads/'] },
      { label: 'Domain Import', path: '/app/import',    icon: 'users' },
      { label: 'Export',        path: '/app/export',    icon: 'docCheck' },
      { label: 'Website Audit', path: '/app/audit',     icon: 'docCheck' },
      { label: 'Newsletter',    path: '/app/newsletter', icon: 'newspaper' },
    ],
  },
  {
    title: 'Delivery',
    items: [
      { label: 'Projektpipeline', path: '/app/leads', icon: 'chart', exactMatch: true },
      { label: 'Kundenprojekte', path: '/app/projects', icon: 'users' },
    ],
  },
  {
    title: 'Qualität',
    items: [
      { label: 'Support Tickets', path: '/app/tickets', icon: 'docCheck' },
      { label: 'Produktentwicklung', path: '/app/product',        icon: 'gear', adminOnly: true },
      { label: 'Produkteditor',      path: '/app/product-editor', icon: 'gear', adminOnly: true },
      { label: 'QR-Generator',       path: '/app/qr-generator',  icon: 'qr',   adminOnly: true },
    ],
  },
  {
    title: 'Website',
    items: [
      { label: 'Seiten-Manager', path: '/app/pages', icon: 'newspaper', adminOnly: true },
    ],
  },
  // Inhalte / Akademie — ausgeblendet, wird später aktiviert
  // {
  //   title: 'Inhalte',
  //   items: [
  //     { label: 'Kurse', path: '/app/courses', icon: 'book' },
  //     { label: 'Akademy', path: '/app/academy', icon: 'gradCap' },
  //     { label: 'Kurse verwalten', path: '/app/akademie/admin', icon: 'gear', adminOnly: true },
  //   ],
  // },
  {
    title: 'Einstellungen',
    items: [
      { label: 'Einstellungen', path: '/app/settings', icon: 'gear' },
    ],
  },
];

const PAGE_NAMES = {
  '/app/dashboard': 'Dashboard',
  '/app/portal': 'Mein Projekt',
  '/app/deals': 'Deals',
  '/app/campaigns': 'Kampagnen',
  '/app/sales': 'Vertriebspipeline',
  '/app/leads': 'Projektpipeline',
  '/app/customers': 'Kunden',
  '/app/audit': 'Website Audit',
  '/app/akademie': 'Akademy',
  '/app/courses': 'Kurse',
  '/app/academy': 'Akademy',
  '/app/akademie/admin': 'Kurse verwalten',
  '/app/academy/admin': 'Kurse verwalten',
  '/app/settings': 'Einstellungen',
  '/app/projects': 'Kundenprojekte',
  '/app/companies': 'Unternehmen',
  '/app/import': 'Domain Import',
  '/app/export': 'Export',
  '/app/tickets': 'Support Tickets',
  '/app/profile': 'Profil',
  '/app/checklists': 'Checklisten',
  '/app/product':         'Produktentwicklung',
  '/app/product-editor':  'Produkteditor',
  '/app/pages':           'Seiten-Manager',
};

function getMobileTabs(role, leadId) {
  if (role === 'kunde') {
    return [
      { label: 'Start', path: '/app/dashboard', icon: 'grid' },
      { label: 'Mein Projekt', path: leadId ? `/app/leads/${leadId}` : '/app/dashboard', icon: 'users' },
      { label: 'Einstellungen', path: '/app/settings', icon: 'gear' },
    ];
  }
  return [
    { label: 'Dashboard', path: '/app/dashboard', icon: 'grid' },
    { label: 'Projekte', path: '/app/projects', icon: 'users' },
    { label: 'Vertrieb', path: '/app/deals', icon: 'chart' },
    { label: 'Audit', path: '/app/audit', icon: 'docCheck' },
    { label: 'Mehr', path: '__more__', icon: 'menu' },
  ];
}

const MORE_ITEMS = [
  { label: 'Unternehmen', path: '/app/companies', icon: '🏢' },
  { label: 'Newsletter', path: '/app/newsletter', icon: '📧' },
  { label: 'Tickets', path: '/app/tickets', icon: '🎫' },
  { label: 'Akademie', path: '/app/academy', icon: '🎓' },
  { label: 'Einstellungen', path: '/app/settings', icon: '⚙️' },
  { label: 'Profil', path: '/app/profile', icon: '👤' },
];

const MORE_ITEMS_ADMIN = [
  ...MORE_ITEMS,
  { label: 'Produkteditor', path: '/app/product-editor', icon: '🛒' },
  { label: 'Domain Import', path: '/app/import', icon: '⬆️' },
];

// ── Sidebar ────────────────────────────────────────────────────

function SidebarNav({ badges }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, hasRole } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [menuOpen, setMenuOpen] = useState(false);

  const isActive = (path) => {
    if (path === '/app/leads') {
      return location.pathname === '/app/leads';
    }
    if (path === '/app/projects') {
      return location.pathname === '/app/projects' || location.pathname.startsWith('/app/projects/');
    }
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

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
        padding: '20px 16px 18px', borderBottom: '1px solid var(--border-light)',
        cursor: 'pointer',
      }} onClick={() => navigate('/app/dashboard')}>
        <KompagnonLogo height={36} variant={theme === 'dark' ? 'white' : 'color'} />
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1, padding: '12px 10px', overflowY: 'auto' }}>
        {user?.role === 'kunde' ? (
          /* ── Kunde: only these four items ── */
          <div style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-tertiary)', padding: '0 10px', marginBottom: 4 }}>
              Mein Bereich
            </div>
            {[
              { label: 'Dashboard',    path: '/app/dashboard',                                            icon: '🏠' },
              { label: 'Meine Kartei', path: user.lead_id ? `/app/leads/${user.lead_id}` : '/app/dashboard', icon: '📋' },
              { label: 'Freigaben',    path: '/app/freigaben',                                            icon: '✅' },
              { label: 'Support',      path: '/app/support',                                              icon: '🎫' },
              { label: 'Rechnungen',   path: '/app/rechnungen',                                           icon: '💳' },
              { label: 'Akademie',     path: '/app/academy',                                              icon: '🎓' },
              { label: 'Einstellungen',path: '/app/settings',                                             icon: '⚙️' },
            ].map((item) => {
              const active = isActive(item.path);
              return (
                <button key={item.path} onClick={() => navigate(item.path)}
                className={`kc-nav-item${active ? ' kc-nav-item--active' : ''}`}
                style={{
                  width: '100%', display: 'flex', alignItems: 'center', gap: 10,
                  padding: '7px 10px', border: 'none', borderRadius: 'var(--radius-md)',
                  cursor: 'pointer', textAlign: 'left', fontSize: 13, fontFamily: 'var(--font-sans)',
                }}
                >
                  <span style={{ fontSize: 16, flexShrink: 0 }}>{item.icon}</span>
                  {item.label}
                </button>
              );
            })}
          </div>
        ) : (
          /* ── All other roles: full NAV_SECTIONS ── */
          NAV_SECTIONS.map((section) => {
            const visibleItems = section.items.filter(i => !i.adminOnly || hasRole('admin'));
            if (visibleItems.length === 0) return null;
            return (
              <div key={section.title} style={{ marginBottom: 20 }}>
                <div style={{
                  fontSize: 11, fontWeight: 500, color: 'var(--text-tertiary)',
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
                        width: '100%', display: 'flex', alignItems: 'center',
                        padding: '7px 10px', border: 'none', borderRadius: 'var(--radius-md)',
                        cursor: 'pointer', fontSize: 13, textAlign: 'left',
                        fontFamily: 'var(--font-sans)',
                      }}
                      className={`kc-nav-item${active ? ' kc-nav-item--active' : ''}`}
                    >
                      <span>{item.label}</span>
                      {item.badgeKey && badges[item.badgeKey] > 0 && (
                        <span style={{
                          marginLeft: 'auto', fontSize: 10, padding: '1px 6px', borderRadius: 10,
                          background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', fontWeight: 600,
                        }}>
                          {badges[item.badgeKey]}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            );
          })
        )}
      </nav>

      {/* Footer */}
      {user && (
        <div style={{
          marginTop: 'auto', borderTop: '1px solid var(--border-light)',
          padding: '12px 10px', position: 'relative',
        }}>
          {/* Theme toggle */}
          <div style={{ borderBottom: '1px solid var(--border-light)', paddingBottom: 8, marginBottom: 8 }}>
            <button
              onClick={toggleTheme}
              style={{
                width: '100%', display: 'flex', alignItems: 'center', gap: 10,
                padding: '6px 8px', border: 'none', borderRadius: 'var(--radius-md)',
                cursor: 'pointer', fontFamily: 'var(--font-sans)',
              }}
              className="kc-btn-ghost"
            >
              <span style={{ fontSize: 16, display: 'flex', flexShrink: 0 }}>
                {theme === 'dark' ? '☀️' : '🌙'}
              </span>
              <span style={{ fontSize: 13, fontWeight: 400 }}>
                {theme === 'dark' ? 'Hell' : 'Dunkel'}
              </span>
            </button>
          </div>

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
                transition: 'color var(--transition-fast)',
              }}
            >
              {icons.dots}
            </button>
          </div>

          {menuOpen && (
            <>
              <div style={{ position: 'fixed', inset: 0, zIndex: 50 }} onClick={() => setMenuOpen(false)} />
              <div style={{
                position: 'absolute', bottom: '100%', left: 10, right: 10,
                background: 'var(--bg-elevated)', border: '1px solid var(--border-light)',
                borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-lg)',
                padding: 4, zIndex: 51, marginBottom: 4,
              }}>
                <div
                  onClick={toggleTheme}
                  style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '10px 10px', cursor: 'pointer', fontSize: 13,
                    color: 'var(--text-primary)', borderBottom: '1px solid var(--border-light)',
                    marginBottom: 4,
                  }}
                >
                  <span>{theme === 'dark' ? '☀️ Hell' : '🌙 Dunkel'}</span>
                  <div style={{
                    width: 36, height: 20, borderRadius: 10,
                    background: theme === 'dark' ? 'var(--brand-primary)' : 'var(--border-light)',
                    position: 'relative', transition: 'background 0.2s',
                  }}>
                    <div style={{
                      position: 'absolute', top: 2, left: theme === 'dark' ? 18 : 2,
                      width: 16, height: 16, borderRadius: '50%',
                      background: '#fff', transition: 'left 0.2s',
                    }} />
                  </div>
                </div>
                <button
                  onClick={() => { navigate('/app/profile'); setMenuOpen(false); }}
                  style={{
                    width: '100%', display: 'flex', alignItems: 'center', gap: 8,
                    padding: '7px 10px', border: 'none', borderRadius: 'var(--radius-sm)',
                    cursor: 'pointer', fontSize: 13, fontFamily: 'var(--font-sans)',
                  }}
                  className="kc-btn-ghost"
                >
                  Profil
                </button>
                <button
                  onClick={() => { logout(); navigate('/'); setMenuOpen(false); }}
                  style={{
                    width: '100%', display: 'flex', alignItems: 'center', gap: 8,
                    padding: '7px 10px', border: 'none', borderRadius: 'var(--radius-sm)',
                    cursor: 'pointer', fontSize: 13,
                    color: 'var(--status-danger-text)', fontFamily: 'var(--font-sans)',
                  }}
                  className="kc-btn-danger-ghost"
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

function Topbar({ breadcrumbs = [], ctaLabel, ctaAction }) {
  const navigate = useNavigate();
  return (
    <header style={{
      height: 52,
      borderBottom: '1px solid var(--border-light)',
      background: 'var(--bg-surface)',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 24px',
      position: 'sticky', top: 0, zIndex: 30,
      flexShrink: 0,
    }}>
      {/* Breadcrumb */}
      <nav style={{ display: 'flex', alignItems: 'center', gap: 6, minWidth: 0 }}>
        {breadcrumbs.map((crumb, i) => {
          const isLast = i === breadcrumbs.length - 1;
          return (
            <React.Fragment key={i}>
              {i > 0 && (
                <span style={{ color: 'var(--text-tertiary)', fontSize: 13, flexShrink: 0, userSelect: 'none' }}>›</span>
              )}
              {isLast ? (
                <span style={{
                  fontSize: 14, fontWeight: 600, color: 'var(--text-primary)',
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                }}>
                  {crumb.label}
                </span>
              ) : (
                <button
                  onClick={() => crumb.path && navigate(crumb.path)}
                  className="kc-btn-ghost"
                  style={{
                    background: 'none', border: 'none', padding: 0,
                    fontSize: 14, fontWeight: 400, color: 'var(--text-tertiary)',
                    cursor: crumb.path ? 'pointer' : 'default',
                    fontFamily: 'var(--font-sans)', whiteSpace: 'nowrap', flexShrink: 0,
                  }}
                >
                  {crumb.label}
                </button>
              )}
            </React.Fragment>
          );
        })}
      </nav>
      {ctaLabel && (
        <button
          onClick={ctaAction}
          className="kc-btn-primary"
          style={{
            background: 'var(--brand-primary)', color: 'var(--text-inverse)',
            border: 'none', padding: '6px 14px', borderRadius: 'var(--radius-md)',
            fontSize: 13, fontWeight: 500, cursor: 'pointer',
            fontFamily: 'var(--font-sans)', flexShrink: 0,
          }}
        >
          {ctaLabel}
        </button>
      )}
    </header>
  );
}

// ── Bottom Nav (Mobile) ────────────────────────────────────────

function BottomNav() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [moreOpen, setMoreOpen] = useState(false);

  const role = user?.role || 'nutzer';
  const tabs = getMobileTabs(role, user?.lead_id);
  const moreItems = role === 'admin' ? MORE_ITEMS_ADMIN : MORE_ITEMS;

  const isActive = (path) => {
    if (path === '__more__') return false;
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  const handleTab = (path) => {
    if (path === '__more__') { setMoreOpen(v => !v); return; }
    setMoreOpen(false);
    navigate(path);
  };

  useEffect(() => { setMoreOpen(false); }, [location.pathname]);

  return (
    <>
      {/* Mehr-Drawer */}
      {moreOpen && (
        <>
          <div onClick={() => setMoreOpen(false)} style={{ position: 'fixed', inset: 0, zIndex: 98, background: 'rgba(0,0,0,0.3)', backdropFilter: 'blur(2px)' }} />
          <div style={{
            position: 'fixed', bottom: 'calc(56px + env(safe-area-inset-bottom))',
            left: 0, right: 0, zIndex: 99,
            background: 'var(--bg-surface)', borderTop: '1px solid var(--border-light)',
            borderRadius: 'var(--radius-xl, 16px) var(--radius-xl, 16px) 0 0',
            padding: '16px 16px 8px',
            boxShadow: '0 -8px 32px rgba(0,0,0,0.12)',
          }}>
            <div style={{ width: 36, height: 4, background: 'var(--border-medium)', borderRadius: 2, margin: '-8px auto 16px' }} />
            <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 12 }}>Weitere Bereiche</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
              {moreItems.map(item => {
                const active = location.pathname === item.path || location.pathname.startsWith(item.path + '/');
                return (
                  <button key={item.path} onClick={() => { navigate(item.path); setMoreOpen(false); }} style={{
                    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6,
                    padding: '12px 6px', background: active ? 'var(--brand-primary-light)' : 'var(--bg-app)',
                    border: active ? '1px solid var(--brand-primary-mid, var(--border-light))' : '1px solid transparent',
                    borderRadius: 'var(--radius-lg)', cursor: 'pointer', fontFamily: 'var(--font-sans)', minHeight: 72,
                  }}>
                    <span style={{ fontSize: 22 }}>{item.icon}</span>
                    <span style={{ fontSize: 10, fontWeight: active ? 700 : 400, color: active ? 'var(--brand-primary-dark)' : 'var(--text-secondary)', textAlign: 'center', lineHeight: 1.3 }}>{item.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </>
      )}

      {/* Bottom Bar */}
      <nav style={{
        position: 'fixed', bottom: 0, left: 0, right: 0,
        background: 'var(--bg-surface)', borderTop: '1px solid var(--border-light)',
        display: 'flex', justifyContent: 'space-around',
        height: 'calc(56px + env(safe-area-inset-bottom))',
        paddingBottom: 'env(safe-area-inset-bottom)',
        alignItems: 'flex-start', paddingTop: 8, zIndex: 100,
      }}>
        {tabs.map((tab) => {
          const active = tab.path === '__more__' ? moreOpen : isActive(tab.path);
          return (
            <button key={tab.path} onClick={() => handleTab(tab.path)} style={{
              background: 'none', border: 'none',
              display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2,
              padding: '4px 8px', cursor: 'pointer', minWidth: 48, flex: 1,
              color: active ? 'var(--brand-primary)' : 'var(--text-tertiary)',
              transition: 'color var(--transition-fast)',
            }}>
              <span style={{ display: 'flex', position: 'relative' }}>
                {icons[tab.icon]}
                {tab.path === '__more__' && moreOpen && (
                  <span style={{ position: 'absolute', top: -2, right: -2, width: 6, height: 6, borderRadius: '50%', background: 'var(--brand-primary)' }} />
                )}
              </span>
              <span style={{ fontSize: 10, fontWeight: active ? 700 : 400 }}>{tab.label}</span>
            </button>
          );
        })}
      </nav>
    </>
  );
}

// ── Main Layout ────────────────────────────────────────────────

export default function AppLayout() {
  const { isMobile } = useScreenSize();
  const { user, logout, token } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();
  const navigate = useNavigate();
  const [badges] = useState({ pipeline: 0, audits: 0 });
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [shortcutHelpOpen, setShortcutHelpOpen] = useState(false);

  const togglePalette = useCallback(() => setPaletteOpen(p => !p), []);
  const goSettings = useCallback(() => navigate('/app/settings'), [navigate]);
  const goDashboard = useCallback(() => navigate('/app/dashboard'), [navigate]);
  const toggleHelp = useCallback(() => setShortcutHelpOpen(p => !p), []);

  const handleRefresh = useCallback(async () => {
    window.dispatchEvent(new CustomEvent('kompagnon:refresh'));
    await new Promise(r => setTimeout(r, 800));
  }, []);
  const { containerRef: mainRef } = usePullToRefresh(handleRefresh, { disabled: !isMobile, threshold: 72 });

  useKeyboardShortcuts([
    { key: 'k', meta: true, action: togglePalette },
    { key: ',', meta: true, action: goSettings },
    { key: 'h', meta: true, action: goDashboard },
    { key: '?', action: toggleHelp },
  ]);

  const [projectName, setProjectName] = useState(null);
  const [leadName, setLeadName] = useState(null);

  useEffect(() => {
    const projectMatch = location.pathname.match(/^\/app\/projects\/(\d+)/);
    const leadMatch = location.pathname.match(/^\/app\/leads\/(\d+)/);
    if (projectMatch) {
      setProjectName(null);
      fetch(`${API_BASE_URL}/api/projects/${projectMatch[1]}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
        .then(r => r.ok ? r.json() : null)
        .then(d => { if (d?.company_name) setProjectName(d.company_name); })
        .catch(() => {});
    } else if (leadMatch) {
      setLeadName(null);
      fetch(`${API_BASE_URL}/api/leads/${leadMatch[1]}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
        .then(r => r.ok ? r.json() : null)
        .then(d => { if (d?.company_name || d?.display_name) setLeadName(d.display_name || d.company_name); })
        .catch(() => {});
    } else {
      setProjectName(null);
      setLeadName(null);
    }
  }, [location.pathname, token]);

  const breadcrumbs = (() => {
    const path = location.pathname;
    const projectMatch = path.match(/^\/app\/projects\/(\d+)/);
    if (projectMatch) {
      return [
        { label: 'Kundenprojekte', path: '/app/projects' },
        { label: projectName || `Projekt #${projectMatch[1]}` },
      ];
    }
    const leadMatch = path.match(/^\/app\/leads\/(\d+)/);
    if (leadMatch) {
      return [
        { label: 'Unternehmen', path: '/app/companies' },
        { label: leadName || `Lead #${leadMatch[1]}` },
      ];
    }
    if (path.startsWith('/app/settings/')) {
      const sub = PAGE_NAMES[path] || 'Einstellungen';
      return [
        { label: 'Einstellungen', path: '/app/settings' },
        { label: sub },
      ];
    }
    if (path.startsWith('/app/academy/') || path.startsWith('/app/akademie/')) {
      return [
        { label: 'Akademie', path: '/app/academy' },
        { label: PAGE_NAMES[path] || 'Kurs' },
      ];
    }
    const label = PAGE_NAMES[path]
      || Object.entries(PAGE_NAMES).find(([p]) => path.startsWith(p + '/'))?.[1]
      || 'KOMPAGNON';
    return [{ label }];
  })();

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
        minWidth: 0,
        marginLeft: !isMobile && user ? 'var(--sidebar-width)' : 0,
        display: 'flex', flexDirection: 'column',
        height: '100vh', overflow: 'hidden',
      }}>
        {/* Topbar — desktop only */}
        {!isMobile && (
          <Topbar
            breadcrumbs={breadcrumbs}
            ctaLabel={cta?.label}
            ctaAction={cta?.action}
          />
        )}

        {/* Mobile header */}
        {isMobile && (
          <header style={{
            padding: '10px 16px', background: 'var(--bg-surface)',
            borderBottom: '1px solid var(--border-light)',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100, flexShrink: 0,
          }}>
            <div>
              <KompagnonLogo height={36} variant={theme === 'dark' ? 'white' : 'color'} />
            </div>
            <span style={{ fontSize: 14, fontWeight: 500, color: 'var(--text-primary)' }}>
              {pageName}
            </span>
            {/* User avatar + dropdown */}
            <div style={{ position: 'relative' }}>
              <button
                onClick={() => setMobileMenuOpen(o => !o)}
                style={{
                  width: 32, height: 32, borderRadius: '50%',
                  background: 'var(--brand-primary-light)', color: 'var(--brand-primary)',
                  border: 'none', cursor: 'pointer', fontSize: 13, fontWeight: 600,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontFamily: 'var(--font-sans)',
                }}
              >
                {(user?.first_name?.[0] || 'U').toUpperCase()}
              </button>
              {mobileMenuOpen && (
                <>
                  <div
                    style={{ position: 'fixed', inset: 0, zIndex: 50 }}
                    onClick={() => setMobileMenuOpen(false)}
                  />
                  <div style={{
                    position: 'absolute', top: 'calc(100% + 8px)', right: 0,
                    background: 'var(--bg-elevated)', border: '1px solid var(--border-light)',
                    borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-lg)',
                    padding: 4, zIndex: 51, minWidth: 160,
                  }}>
                    <div style={{ padding: '8px 12px 6px', borderBottom: '1px solid var(--border-light)', marginBottom: 4 }}>
                      <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>
                        {user?.first_name} {user?.last_name}
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--text-tertiary)', textTransform: 'capitalize' }}>
                        {user?.role}
                      </div>
                    </div>
                    <div
                      onClick={toggleTheme}
                      style={{
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                        padding: '10px 10px', cursor: 'pointer', fontSize: 13,
                        color: 'var(--text-primary)', borderBottom: '1px solid var(--border-light)',
                        marginBottom: 4,
                      }}
                    >
                      <span>{theme === 'dark' ? '☀️ Hell' : '🌙 Dunkel'}</span>
                      <div style={{
                        width: 36, height: 20, borderRadius: 10,
                        background: theme === 'dark' ? 'var(--brand-primary)' : 'var(--border-light)',
                        position: 'relative', transition: 'background 0.2s',
                      }}>
                        <div style={{
                          position: 'absolute', top: 2, left: theme === 'dark' ? 18 : 2,
                          width: 16, height: 16, borderRadius: '50%',
                          background: '#fff', transition: 'left 0.2s',
                        }} />
                      </div>
                    </div>
                    <button
                      onClick={() => { navigate('/app/profile'); setMobileMenuOpen(false); }}
                      style={{
                        width: '100%', display: 'flex', alignItems: 'center', gap: 8,
                        padding: '7px 10px', border: 'none', borderRadius: 'var(--radius-sm)',
                        background: 'transparent', cursor: 'pointer', fontSize: 13,
                        color: 'var(--text-secondary)', fontFamily: 'var(--font-sans)', textAlign: 'left',
                      }}
                    >
                      Profil
                    </button>
                    <button
                      onClick={() => { logout(); navigate('/'); setMobileMenuOpen(false); }}
                      style={{
                        width: '100%', display: 'flex', alignItems: 'center', gap: 8,
                        padding: '7px 10px', border: 'none', borderRadius: 'var(--radius-sm)',
                        background: 'transparent', cursor: 'pointer', fontSize: 13,
                        color: 'var(--status-danger-text)', fontFamily: 'var(--font-sans)', textAlign: 'left',
                      }}
                    >
                      {icons.logout}
                      <span>Abmelden</span>
                    </button>
                  </div>
                </>
              )}
            </div>
          </header>
        )}

        {/* Content */}
        <main
          ref={mainRef}
          style={{
            flex: 1, overflowY: 'auto', overflowX: 'hidden',
            minWidth: 0, position: 'relative',
            padding: isMobile ? 16 : '20px 28px',
            paddingTop: isMobile ? 72 : undefined,
            paddingBottom: isMobile ? 80 : 20,
          }}
        >
          {isMobile && <PullIndicator />}
          <div key={location.pathname} className="page-enter" style={{ maxWidth: '100%', overflowX: 'hidden' }}>
            <Outlet />
          </div>
        </main>
      </div>

      {/* Bottom nav — mobile only */}
      {isMobile && user && <BottomNav />}

      {/* Global Overlays */}
      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} />
      <ShortcutHelp open={shortcutHelpOpen} onClose={() => setShortcutHelpOpen(false)} />
    </div>
  );
}
