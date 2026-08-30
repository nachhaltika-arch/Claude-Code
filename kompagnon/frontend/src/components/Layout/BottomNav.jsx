/**
 * Die Navigationsleiste am unteren Rand der Mobilansicht (L-25).
 *
 * Am 2026-08-30 aus `AppLayout.jsx` herausgeloest — 183 der damals 1.183
 * Zeilen.
 */
import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

import { useAuth } from '../../context/AuthContext';
import { useEscapeKey } from '../../hooks/useKeyboardShortcuts';
import { aufTaste } from '../../utils/tastaturBedienung';
import { MOBILE_NAV_H } from './masse';
import { getMobileTabs, icons, MORE_ITEMS, MORE_ITEMS_ADMIN } from './navigationsdaten';

export default function BottomNav() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [moreOpen, setMoreOpen] = useState(false);

  // **Escape schliesst das Menue — WCAG 2.1.1 (30.08.2026, L-17).** Die
  // Ueberlagerung darunter nimmt einen Klick; mit der Tastatur fuehrte aus
  // dem geoeffneten Menue kein Weg zurueck.
  useEscapeKey(() => setMoreOpen(false), moreOpen);

  const role = user?.role || 'mitarbeiter';
  const tabs = getMobileTabs(role, user?.lead_id);
  const moreItems = (role === 'admin' || role === 'superadmin') ? MORE_ITEMS_ADMIN : MORE_ITEMS;

  const isActive = (path) => {
    if (path === '__more__') return moreOpen;
    if (path === '/app/vertrieb') {
      return ['/app/vertrieb', '/app/deals', '/app/campaigns', '/app/audit',
              '/app/newsletter', '/app/import', '/app/retainer', '/app/scraper']
        .some(p => location.pathname === p || location.pathname.startsWith(p + '/'));
    }
    if (path === '/app/projects') {
      return ['/app/projects', '/app/tickets', '/app/checklists', '/app/settings/templates']
        .some(p => location.pathname === p || location.pathname.startsWith(p + '/'));
    }
    if (path === '/app/settings') {
      return location.pathname.startsWith('/app/settings');
    }
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  const handleTab = (path) => {
    if (path === '__more__') {
      setMoreOpen(o => !o);
    } else {
      setMoreOpen(false);
      navigate(path);
    }
  };

  return (
    <>
      {/* Mehr-Overlay */}
      {moreOpen && (
        <>
          <div role="button" tabIndex={0} onKeyDown={aufTaste(() => setMoreOpen(false))}
            onClick={() => setMoreOpen(false)}
            style={{
              position: 'fixed', inset: 0,
              background: 'rgba(0,79,89,0.6)',
              backdropFilter: 'blur(2px)',
              zIndex: 98,
            }}
          />
          <div style={{
            position: 'fixed',
            bottom: `calc(${MOBILE_NAV_H}px + env(safe-area-inset-bottom, 0px))`,
            left: 0, right: 0,
            background: '#fff',
            borderRadius: '16px 16px 0 0',
            padding: '16px 14px',
            zIndex: 99,
            boxShadow: '0 -8px 32px rgba(0,79,89,.2)',
            animation: 'bwSlideUp .2s ease',
          }}>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: 8,
            }}>
              {moreItems.map(item => {
                const active = isActive(item.path);
                return (
                  <button
                    key={item.path}
                    onClick={() => { navigate(item.path); setMoreOpen(false); }}
                    style={{
                      background: active ? '#E0F4F8' : '#F0F4F5',
                      border: active ? '1.5px solid var(--kc-mid)' : '0.5px solid #D5E0E2',
                      borderRadius: 10,
                      padding: '14px 8px',
                      cursor: 'pointer',
                      display: 'flex', flexDirection: 'column',
                      alignItems: 'center', gap: 6,
                      minHeight: 72,
                    }}
                  >
                    <span style={{ fontSize: 22 }}>{item.icon}</span>
                    <span style={{
                      fontSize: 10, fontWeight: 700,
                      color: active ? 'var(--brand-primary)' : '#4A5A5C',
                      textTransform: 'uppercase',
                      letterSpacing: '.04em',
                      textAlign: 'center', lineHeight: 1.3,
                      fontFamily: 'var(--font-sans)',
                    }}>
                      {item.label}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        </>
      )}

      {/* Bottom Bar */}
      <nav style={{
        position: 'fixed',
        bottom: 0, left: 0, right: 0,
        zIndex: 100,
        background: 'var(--brand-primary)',
        borderTop: '0.5px solid rgba(255,255,255,.1)',
        display: 'flex',
        justifyContent: 'space-around',
        alignItems: 'flex-start',
        height: `calc(${MOBILE_NAV_H}px + env(safe-area-inset-bottom, 0px))`,
        paddingTop: 8,
        paddingBottom: 'env(safe-area-inset-bottom, 0px)',
      }}>
        {tabs.map((tab) => {
          const active = isActive(tab.path);
          return (
            <button
              key={tab.path}
              onClick={() => handleTab(tab.path)}
              style={{
                background: 'none', border: 'none',
                display: 'flex', flexDirection: 'column',
                alignItems: 'center', gap: 3,
                padding: '2px 4px',
                cursor: 'pointer', flex: 1,
                minHeight: 44,
                position: 'relative',
                fontFamily: 'var(--font-sans)',
              }}
            >
              {/* Gelber Strich oben beim aktiven Tab */}
              <span style={{
                position: 'absolute', top: -8,
                left: '50%', transform: 'translateX(-50%)',
                width: 24, height: 3,
                background: active ? 'var(--kc-yellow)' : 'transparent',
                borderRadius: 2, transition: 'background .12s',
              }} />

              {/* Icon */}
              <span style={{ display: 'flex', position: 'relative',
                color: active ? 'var(--kc-yellow)' : 'rgba(255,255,255,.45)',
                transition: 'color .12s',
              }}>
                {icons[tab.icon]}
                {tab.badge && !active && (
                  <span style={{
                    position: 'absolute', top: -2, right: -4,
                    width: 7, height: 7, borderRadius: '50%',
                    background: 'var(--kc-yellow)',
                    border: '1.5px solid var(--brand-primary)',
                  }} />
                )}
              </span>

              {/* Label */}
              <span style={{
                fontSize: 10, fontWeight: active ? 700 : 400,
                color: active ? 'var(--kc-yellow)' : 'rgba(255,255,255,.4)',
                textTransform: 'uppercase', letterSpacing: '.04em',
                fontFamily: 'var(--font-sans)',
                transition: 'color .12s',
              }}>
                {tab.label}
              </span>
            </button>
          );
        })}
      </nav>
    </>
  );
}

// ── Main Layout ────────────────────────────────────────────────

