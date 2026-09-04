/**
 * Die Seitenleiste des Werkzeugs (L-25).
 *
 * Am 2026-08-30 aus `AppLayout.jsx` herausgeloest — 391 der damals 1.183
 * Zeilen. Sie war dort schon eine eigene Funktion; der Schnitt verschiebt
 * sie nur dorthin, wo man sie sucht.
 */
import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { useEscapeKey } from '../../hooks/useKeyboardShortcuts';
import { MENUE_GRUPPEN, offeneGruppen } from '../../utils/menue';
import { aufTaste } from '../../utils/tastaturBedienung';
import KompagnonLogo from '../KompagnonLogo';
import Logo from '../Logo';
import { icons, VersandHinweis } from './navigationsdaten';

// **Die gedaempfte Schrift der Seitenleiste — mit Deckkraft, aber ueber AA.**
//
// Gemessen am 01.09.2026 am laufenden Werkzeug: Weiss auf `--kc-dark`
// (`rgb(0,79,89)`) erreicht AA erst ab **0,62** Deckkraft. Vorher standen hier
// 0,55 (3,97), 0,45 (3,16), 0,30 (2,20) und 0,28 (2,08) — **561 von 3.203
// Zeichen** auf jeder Seite unter der Schwelle, also die komplette
// Gruppenbeschriftung der Navigation.
//
// **Warum es niemand gesehen hat:** Die Kontrastmessung gab bei einer
// halbdurchsichtigen Schriftfarbe auf — sie zaehlte diese Zeichen als
// „unentscheidbar" statt als gefallen. Erst als sie die Farbe ueber ihren
// Grund legte, wie der Browser es tut, wurde aus 0 % gefallen 21,3 %.
//
// Die Abstufung bleibt erhalten, sie beginnt nur hoeher: gedaempft 0,70
// (5,40), sehr gedaempft 0,62 (4,60). Wer sie senkt, senkt sie unter AA.
const GEDAEMPFT = 'rgba(255,255,255,0.70)';      // 5,40 auf --kc-dark
const SEHR_GEDAEMPFT = 'rgba(255,255,255,0.62)'; // 4,60 auf --kc-dark


export default function SidebarNav({ badges }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, hasRole } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [menuOpen, setMenuOpen] = useState(false);

  // **Escape schliesst das Menue — WCAG 2.1.1 (30.08.2026, L-17).** Die
  // Ueberlagerung darunter nimmt einen Klick; mit der Tastatur fuehrte aus
  // dem geoeffneten Menue kein Weg zurueck.
  useEscapeKey(() => setMenuOpen(false), menuOpen);

  /* Welche Gruppe offen steht, folgt der Adresse — abgeleitet aus den
     Menueeintraegen selbst. Vorher stand die Pfadliste hier ein zweites Mal;
     wer einen Eintrag verschob und diese Liste vergass, bekam eine
     Seitenleiste, die nicht mehr zeigt, wo man ist. Siehe utils/menue.js. */
  const getDefaultOpen = () => offeneGruppen(location.pathname);

  const [openSections, setOpenSections] = useState(getDefaultOpen);
  const toggleSection = (key) => setOpenSections(prev => ({ ...prev, [key]: !prev[key] }));

  /* Die offene Gruppe folgt der Adresse — auch wenn sie sich nach dem Aufbau
     noch aendert.
     `getDefaultOpen` lief nur einmal, beim ersten Rendern. Wer ueber eine
     Weiterleitung ankam, brachte die ALTE Adresse mit, und die passte in keine
     Gruppe: Die Seitenleiste blieb komplett zugeklappt, ohne Hinweis darauf,
     wo man ist. Sichtbar geworden ist das am 16.08. mit /app/leads →
     /app/projektpipeline; /app/sales → /app/deals hatte es schon vorher.
     Hier wird nur GEOEFFNET, nie geschlossen — wer eine andere Gruppe von Hand
     aufklappt, behaelt sie. */
  useEffect(() => {
    setOpenSections(prev => {
      const soll = getDefaultOpen();
      const naechste = { ...prev };
      let geaendert = false;
      Object.entries(soll).forEach(([key, offen]) => {
        if (offen && !prev[key]) { naechste[key] = true; geaendert = true; }
      });
      return geaendert ? naechste : prev;
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname]);

  const isActive = (path) => {
    if (path === '/app/projects') return location.pathname === '/app/projects' || location.pathname.startsWith('/app/projects/');
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  const navItemStyle = (active) => ({
    width: '100%', display: 'flex', alignItems: 'center', gap: 9,
    padding: '7px 14px',
    paddingLeft: active ? 17 : 14,
    border: 'none',
    borderLeft: active ? '3px solid var(--kc-yellow)' : '3px solid transparent',
    cursor: 'pointer', fontSize: 13, textAlign: 'left', fontFamily: 'var(--font-sans)',
    background: active ? 'var(--kc-mid-a-30)' : 'transparent',
    color: active ? '#ffffff' : GEDAEMPFT,
    fontWeight: active ? 600 : 400,
    borderRadius: 0,
    transition: 'background 150ms, color 150ms',
  });

  const subItemStyle = (active) => ({
    width: '100%', display: 'flex', alignItems: 'center', gap: 8,
    paddingTop: 6, paddingBottom: 6, paddingRight: 14,
    paddingLeft: active ? 25 : 22,
    border: 'none',
    borderLeft: active ? '3px solid var(--kc-yellow)' : '3px solid transparent',
    cursor: 'pointer', fontSize: 12, textAlign: 'left', fontFamily: 'var(--font-sans)',
    background: active ? 'var(--kc-mid-a-20)' : 'transparent',
    color: active ? 'var(--kc-yellow)' : GEDAEMPFT,
    fontWeight: active ? 600 : 400,
    borderRadius: 0,
    transition: 'background 150ms, color 150ms',
  });

  const sectionLabelStyle = {
    fontSize: 12, letterSpacing: '.18em', color: SEHR_GEDAEMPFT,
    textTransform: 'uppercase', padding: '14px 14px 4px', fontWeight: 700,
    fontFamily: 'var(--font-sans)', display: 'block',
  };

  const initials = [user?.first_name?.[0], user?.last_name?.[0]].filter(Boolean).join('').toUpperCase() || 'U';

  return (
    <aside style={{
      position: 'fixed', left: 0, top: 0, bottom: 0,
      width: 'var(--sidebar-width)', background: 'var(--kc-dark)',
      display: 'flex', flexDirection: 'column',
      zIndex: 40, overflowY: 'auto',
    }}>
      {/* Logo */}
      <div role="button" tabIndex={0} onKeyDown={aufTaste(() => navigate('/app/dashboard'))} style={{
        padding: '18px 14px 16px', borderBottom: '1px solid rgba(255,255,255,0.08)',
        cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 10,
      }} onClick={() => navigate('/app/dashboard')}>
        <KompagnonLogo variant="white" height={28} style={{ flexShrink: 0 }} />
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1, overflowY: 'auto' }}>
        {user?.role === 'kunde' ? (
          /* ── Kunde view ── */
          <div style={{ marginTop: 8 }}>
            {[
              // **Direkt auf die eigene Karte (04.09.2026).** Der Punkt zeigte
              // auf `/app/dashboard`; `DashboardRoute` wirft einen Kunden von
              // dort sofort auf `/app/usercards/:lead_id`. Der Klick landete
              // also richtig — aber `isActive('/app/dashboard')` verglich mit
              // der Adresse **nach** der Umleitung und war nie wahr. Der Punkt
              // sprang weg und leuchtete nie: von aussen „lässt sich nicht
              // aktivieren".
              //
              // Es ist derselbe Fehler wie eine Zeile darunter, dort am
              // 26.08.2026 behoben. Ein Menuepunkt soll benennen, wohin er
              // wirklich fuehrt — nicht auf eine Weiche zeigen.
              { label: 'Dashboard',     path: user?.lead_id ? `/app/usercards/${user.lead_id}` : '/app/dashboard' },
              { label: 'Meine Daten',   path: '/app/meine-daten' },
              { label: 'Mein Briefing', path: '/app/mein-briefing' },
              { label: 'Freigaben',     path: '/app/freigaben' },
              { label: 'Support',       path: '/app/support' },
              { label: 'Rechnungen',    path: '/app/rechnungen' },
              { label: 'Akademie',      path: '/app/academy' },
              { label: 'Einstellungen', path: '/app/settings' },
            ].map((item) => {
              const active = isActive(item.path);
              return (
                <button key={item.path} onClick={() => navigate(item.path)} style={navItemStyle(active)}>
                  {item.label}
                </button>
              );
            })}
          </div>
        ) : (
          /* ── All other roles: collapsible sections ── */
          <>
            <VersandHinweis onClick={() => navigate('/app/settings/notifications')} />

            {/* Dashboard */}
            <button onClick={() => navigate('/app/dashboard')} style={{ ...navItemStyle(isActive('/app/dashboard')), marginTop: 8, display: 'flex', alignItems: 'center', gap: 9 }}>
              {icons.grid}
              <span>Dashboard</span>
            </button>

            {/* ARBEIT */}
            <span style={sectionLabelStyle}>Arbeit</span>

            {/* Die Gruppen kommen aus utils/menue.js — dieselbe Quelle, aus
                der sich auch ergibt, welche Gruppe zur Adresse offen steht.
                Vorher standen beide Listen getrennt nebeneinander.
                „Einstellungen" und „Verwaltung" werden unten eigens
                gerendert, unterhalb des Trenners. */}
            {MENUE_GRUPPEN
              .filter((g) => !['einstellungen', 'verwaltung'].includes(g.key))
              .map((g) => ({ key: g.key, label: g.label, items: g.eintraege }))
              .map((section) => {
              const visibleItems = section.items.filter((i) => !i.adminOnly || hasRole('admin'));
              if (visibleItems.length === 0) return null;
              const isOpen = openSections[section.key];
              return (
                <React.Fragment key={section.key}>
                  <button onClick={() => toggleSection(section.key)} style={{
                    width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '7px 14px', border: 'none', borderLeft: '3px solid transparent',
                    background: 'transparent', cursor: 'pointer', fontSize: 13, textAlign: 'left',
                    fontFamily: 'var(--font-sans)',
                    color: isOpen ? '#fff' : GEDAEMPFT,
                    fontWeight: isOpen ? 600 : 400,
                  }}>
                    <span>{section.label}</span>
                    <span style={{ fontSize: 14, color: SEHR_GEDAEMPFT, transform: isOpen ? 'rotate(90deg)' : 'none', display: 'inline-block', transition: 'transform 0.15s', lineHeight: 1 }}>›</span>
                  </button>
                  {isOpen && visibleItems.map((item) => (
                    <button key={item.path} onClick={() => navigate(item.path)} style={subItemStyle(isActive(item.path))}>
                      {item.label}
                      {item.badgeKey && badges[item.badgeKey] > 0 && (
                        <span style={{ marginLeft: 'auto', fontSize: 12, padding: '1px 6px', borderRadius: 10, background: 'var(--kc-yellow)', color: 'var(--kc-dark)', fontWeight: 700 }}>
                          {badges[item.badgeKey]}
                        </span>
                      )}
                    </button>
                  ))}
                </React.Fragment>
              );
            })}

            {/* Separator */}
            <div style={{ height: 1, background: 'rgba(255,255,255,0.08)', margin: '8px 14px' }} />

            {/* ── EINSTELLUNGEN ── */}
            <button onClick={() => toggleSection('einstellungen')} style={{
              width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '7px 14px', border: 'none', borderLeft: '3px solid transparent',
              background: 'transparent', cursor: 'pointer', fontSize: 13, textAlign: 'left',
              fontFamily: 'var(--font-sans)',
              color: openSections.einstellungen ? '#fff' : GEDAEMPFT,
              fontWeight: openSections.einstellungen ? 600 : 400,
            }}>
              <span>Einstellungen</span>
              <span style={{ fontSize: 14, color: SEHR_GEDAEMPFT, transform: openSections.einstellungen ? 'rotate(90deg)' : 'none', display: 'inline-block', transition: 'transform 0.15s', lineHeight: 1 }}>›</span>
            </button>
            {openSections.einstellungen
              && MENUE_GRUPPEN.find(g => g.key === 'einstellungen').eintraege
              .filter(i => !i.adminOnly || hasRole('admin')).map(item => (
              <button key={item.path} onClick={() => navigate(item.path)} style={subItemStyle(isActive(item.path))}>
                {item.label}
              </button>
            ))}

            {/* ── VERWALTUNG ──
              * Was für alle gilt, nicht was eine Person für sich einstellt.
              * Stand vorher mit unter „Einstellungen"; acht Einträge dort
              * waren wieder ein Sammelbecken, nur mit besserem Namen. */}
            {(() => {
              const gruppe = MENUE_GRUPPEN.find(g => g.key === 'verwaltung');
              const sichtbar = gruppe.eintraege.filter(i => !i.adminOnly || hasRole('admin'));
              if (sichtbar.length === 0) return null;
              return (
                <>
                  <button onClick={() => toggleSection('verwaltung')} style={{
                    width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '7px 14px', border: 'none', borderLeft: '3px solid transparent',
                    background: 'transparent', cursor: 'pointer', fontSize: 13, textAlign: 'left',
                    fontFamily: 'var(--font-sans)',
                    color: openSections.verwaltung ? '#fff' : GEDAEMPFT,
                    fontWeight: openSections.verwaltung ? 600 : 400,
                  }}>
                    <span>{gruppe.label}</span>
                    <span style={{ fontSize: 14, color: SEHR_GEDAEMPFT, transform: openSections.verwaltung ? 'rotate(90deg)' : 'none', display: 'inline-block', transition: 'transform 0.15s', lineHeight: 1 }}>›</span>
                  </button>
                  {openSections.verwaltung && sichtbar.map(item => (
                    <button key={item.path} onClick={() => navigate(item.path)} style={subItemStyle(isActive(item.path))}>
                      {item.label}
                    </button>
                  ))}
                </>
              );
            })()}
          </>
        )}
      </nav>

      {/* ── Theme Toggle ─────────────────────────────────────────── */}
      <div role="button" tabIndex={0} onKeyDown={aufTaste(toggleTheme)}
        onClick={toggleTheme}
        aria-label={theme === 'dark' ? 'Helles Design' : 'Dunkles Design'}
        title={theme === 'dark' ? 'Helles Design' : 'Dunkles Design'}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '10px 20px',
          cursor: 'pointer',
          borderTop: '0.5px solid rgba(255,255,255,0.08)',
        }}
        onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.06)'}
        onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
      >
        <span style={{
          fontSize: 12,
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '.1em',
          color: GEDAEMPFT,
          fontFamily: 'var(--font-sans)',
          userSelect: 'none',
        }}>
          {theme === 'dark' ? 'Hell' : 'Dunkel'}
        </span>
        <div style={{
          width: 40,
          height: 22,
          borderRadius: 11,
          background: theme === 'dark' ? 'var(--kc-yellow)' : 'rgba(255,255,255,0.20)',
          position: 'relative',
          transition: 'background 0.2s',
          flexShrink: 0,
        }}>
          <div style={{
            position: 'absolute',
            top: 3,
            left: theme === 'dark' ? 21 : 3,
            width: 16,
            height: 16,
            borderRadius: '50%',
            background: theme === 'dark' ? 'var(--brand-primary)' : '#fff',
            transition: 'left 0.2s',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 12,
          }}>
            {theme === 'dark' ? '☀' : '☾'}
          </div>
        </div>
      </div>

      {/* Footer */}
      {user && (
        <div style={{
          borderTop: '1px solid rgba(255,255,255,0.08)',
          padding: '12px 14px', position: 'relative',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 34, height: 34, borderRadius: '50%',
              background: 'var(--brand-primary)', color: 'var(--text-on-brand)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 13, fontWeight: 700, flexShrink: 0, letterSpacing: '0.02em',
              fontFamily: 'var(--font-sans)',
            }}>
              {initials}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 12, fontWeight: 900, color: '#ffffff', textTransform: 'uppercase', letterSpacing: '0.04em', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontFamily: 'var(--font-sans)' }}>
                {user.first_name} {user.last_name}
              </div>
              <div style={{ fontSize: 12, color: 'var(--kc-yellow)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 700, fontFamily: 'var(--font-sans)' }}>
                {user.role}
              </div>
            </div>
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              style={{
                background: 'none', border: 'none', padding: 4,
                color: GEDAEMPFT, cursor: 'pointer',
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
                position: 'absolute', bottom: '100%', left: 10, right: 10,
                background: 'var(--bg-elevated)', border: '1px solid var(--border-light)',
                borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-lg)',
                padding: 4, zIndex: 51, marginBottom: 4,
              }}>
                <div role="button" tabIndex={0} onKeyDown={aufTaste(toggleTheme)}
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

