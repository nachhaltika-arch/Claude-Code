import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useEscapeKey } from '../../hooks/useKeyboardShortcuts';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useVersand } from '../../context/VersandContext';
import { useScreenSize } from '../../utils/responsive';
import { MENUE_GRUPPEN, offeneGruppen } from '../../utils/menue';
import { loadJson } from '../../utils/apiRequest';
import { useTheme } from '../../context/ThemeContext';
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts';
import { usePullToRefresh } from '../../hooks/useTouch';
import PullIndicator from '../ui/PullIndicator';
import CommandPalette from '../CommandPalette';
import ShortcutHelp from '../ShortcutHelp';
import API_BASE_URL from '../../config';
import Logo from '../Logo';
import KompagnonLogo from '../KompagnonLogo';
import { aufTaste } from '../../utils/tastaturBedienung';
import Glocke from './Glocke';
// Am 30.08.2026 herausgeloest (L-25): Die Datei trug 1.183 Zeilen und darin
// vier Komponenten. Seitenleiste und Mobilnavigation waren schon eigene
// Funktionen — der Schnitt verschiebt sie nur dorthin, wo man sie sucht.
import BottomNav from './BottomNav';
import SidebarNav from './SidebarNav';
import { MOBILE_HEADER_H, MOBILE_NAV_H } from './masse';
import { icons } from './navigationsdaten';


// ── SVG Icons (16x16) ──────────────────────────────────────────

const PAGE_NAMES = {
  '/app/dashboard': 'Dashboard',
  '/app/portal': 'Mein Projekt',
  '/app/deals': 'Deals',
  '/app/campaigns': 'Kampagnen',
  '/app/sales': 'Vertriebspipeline',
  '/app/projektpipeline': 'Projektpipeline',
  '/app/audit': 'Website Audit',
  '/app/akademie': 'Akademie',
  '/app/academy': 'Akademie',
  '/app/akademie/admin': 'Kurse verwalten',
  '/app/academy/admin': 'Kurse verwalten',
  '/app/settings': 'Einstellungen',
  '/app/projects': 'Kundenprojekte',
  '/app/betriebe': 'Betriebe',
  '/app/import': 'Domain Import',
  '/app/export': 'Export',
  '/app/tickets': 'Support Tickets',
  '/app/profile': 'Profil',
  '/app/checklists': 'Checklisten',
  '/app/product':         'Produktentwicklung',
  '/app/product-editor':  'Produkteditor',
  '/app/pages':           'Seiten-Manager',
  '/app/settings/component-library': 'Komponenten-Bibliothek',
};

function Topbar({ breadcrumbs = [], ctaLabel, ctaAction }) {
  const navigate = useNavigate();
  const { hasRole } = useAuth();
  // Die Glocke traegt Betriebsnamen und Betreffzeilen anderer Kunden —
  // sie gehoert dem Innendienst. Der Server weist einen Kunden ohnehin ab
  // (403); hier faellt der Knopf weg, statt zuverlaessig zu scheitern.
  const istInnendienst = hasRole('admin', 'superadmin', 'mitarbeiter');
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
      {/* Brotkrume — nur, wenn sie einen Weg zeigt.
        * Auf obersten Seiten bestand sie aus einem einzigen Element: dem
        * Seitennamen, der zwei Zeilen tiefer nochmal als Überschrift steht.
        * Eine Brotkrume mit einem Element zeigt keine Hierarchie, sie
        * wiederholt nur (UX-20). */}
      <nav style={{ display: 'flex', alignItems: 'center', gap: 6, minWidth: 0 }}>
        {(breadcrumbs.length > 1 ? breadcrumbs : []).map((crumb, i) => {
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
      {/* Der Posteingang (L-18, 26.08.2026). Nur fuer den Innendienst — die
        * Meldungen tragen Betriebsnamen und Betreffzeilen anderer Kunden.
        * Rechts neben der Handlungstaste, weil dort der Blick ohnehin
        * hingeht. */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
        {istInnendienst && <Glocke />}
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
      </div>
    </header>
  );
}

// ── Bottom Nav (Mobile) ────────────────────────────────────────

export default function AppLayout() {
  const { isMobile } = useScreenSize();
  const { user, logout, token } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();
  const navigate = useNavigate();
  const [badges] = useState({ pipeline: 0, audits: 0 });
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // **Escape schliesst das Menue — WCAG 2.1.1 (30.08.2026, L-17).** Die
  // Ueberlagerung darunter nimmt einen Klick; mit der Tastatur fuehrte aus
  // dem geoeffneten Menue kein Weg zurueck.
  useEscapeKey(() => setMobileMenuOpen(false), mobileMenuOpen);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [shortcutHelpOpen, setShortcutHelpOpen] = useState(false);

  const togglePalette = useCallback(() => setPaletteOpen(p => !p), []);
  const goSettings = useCallback(() => navigate('/app/settings'), [navigate]);
  const goDashboard = useCallback(() => navigate('/app/dashboard'), [navigate]);
  const toggleHelp = useCallback(() => setShortcutHelpOpen(p => !p), []);

  // Keepalive: Backend alle 12 Minuten pingen (verhindert Render.com Kaltstart)
  const [slowApi, setSlowApi] = useState(false);
  const slowApiTimer = useRef(null);
  useEffect(() => {
    if (!user) return;
    const ping = async () => {
      slowApiTimer.current = setTimeout(() => setSlowApi(true), 5000);
      // quiet: Der Ping haelt nur den Render-Dienst wach. Ein Ausfall zeigt
      // sich ohnehin an der naechsten echten Anfrage — hier waere eine Meldung
      // alle 12 Minuten nur Laerm.
      await loadJson(`${API_BASE_URL}/api/health`, {}, { quiet: true });
      clearTimeout(slowApiTimer.current);
      setSlowApi(false);
    };
    ping();
    const interval = setInterval(ping, 12 * 60 * 1000);
    return () => { clearInterval(interval); clearTimeout(slowApiTimer.current); };
  }, [user]); // eslint-disable-line

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
  const [projectLeadId, setProjectLeadId] = useState(null);
  const [leadName, setLeadName] = useState(null);

  useEffect(() => {
    const projectMatch = location.pathname.match(/^\/app\/projects\/(\d+)/);
    // Hiess `/app/leads/(\d+)` und traf damit seit der Umbenennung am 16.08.
    // nichts mehr: Die Einzelansicht liegt unter `/app/betriebe/:id`, die alte
    // Adresse leitet nur noch weiter. Folge war kein Fehler, sondern eine
    // Auslassung — in der Brotkrumenleiste stand „Betriebe" ohne den Namen
    // des Betriebs, auf dessen Seite man gerade war.
    const leadMatch = location.pathname.match(/^\/app\/betriebe\/(\d+)/);
    if (projectMatch) {
      setProjectName(null);
      setProjectLeadId(null);
      // quiet: nur der Name in der Brotkrumenleiste. Scheitert die Anfrage,
      // meldet die Seite selbst den Fehler — zweimal waere zu viel.
      loadJson(
        `${API_BASE_URL}/api/projects/${projectMatch[1]}`,
        { headers: token ? { Authorization: `Bearer ${token}` } : {} },
        { quiet: true },
      ).then(d => {
        if (d?.company_name) setProjectName(d.company_name);
        if (d?.lead_id) setProjectLeadId(d.lead_id);
      });
    } else if (leadMatch) {
      setLeadName(null);
      loadJson(
        `${API_BASE_URL}/api/leads/${leadMatch[1]}`,
        { headers: token ? { Authorization: `Bearer ${token}` } : {} },
        { quiet: true },
      ).then(d => { if (d?.company_name || d?.display_name) setLeadName(d.display_name || d.company_name); });
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
        { label: 'Dashboard', path: '/app/dashboard' },
        { label: 'Projekte', path: '/app/projects' },
        { label: projectName || `Projekt #${projectMatch[1]}`, path: projectLeadId ? `/app/betriebe/${projectLeadId}` : null },
      ];
    }
    const leadMatch = path.match(/^\/app\/betriebe\/(\d+)/);
    if (leadMatch) {
      return [
        { label: 'Betriebe', path: '/app/betriebe' },
        { label: leadName || `Betrieb #${leadMatch[1]}` },
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
    // Hiess „+ Neuer Lead" und fuehrte zum Domain-Import — auf der
    // Projektpipeline. Der sichtbarste Teil der alten Verwechslung.
    '/app/projektpipeline': null,
    // Stand „+ Neues Audit" auf dem Bildschirm, der selbst das neue Audit
    // ist — mit `action: () => {}`, also ohne jede Wirkung. Ein Knopf, der
    // nichts tut, ist schlimmer als keiner: Man drückt ihn und sucht den
    // Fehler bei sich (UX-23). Nach einem fertigen Bericht steht der richtige
    // Knopf ohnehin unter dem Ergebnis.
    '/app/audit': null,
  };
  const cta = ctaMap[location.pathname];

  const hideSidebar = /^\/app\/projects\/\d+/.test(location.pathname);

  return (
    <div style={{ height: '100vh', overflow: 'hidden', display: 'flex' }}>
      {/* Sprunglink — WCAG 2.4.1 „Bypass Blocks", Stufe A.
          Gemessen am 30.08.2026 (L-17, `tools/bedienbarkeit_messen.py`): Auf
          /app/betriebe liegen **38 Tabstopps** vor dem Inhalt, fast alle in
          der Seitenleiste, und sie stehen auf jeder Seite wieder da. Wer mit
          der Tastatur arbeitet, tabbt sich durch die Navigation, bevor er
          etwas tun kann.
          Er ist unsichtbar, bis er den Fokus bekommt — dann steht er oben
          links. Er muss das **erste** Element im Baum sein, sonst führt er
          hinter das, was er überspringen soll. */}
      <a href="#inhalt" className="kc-sprunglink">Zum Inhalt springen</a>

      {/* Sidebar — desktop only, hidden on project process route */}
      {!isMobile && user && !hideSidebar && <SidebarNav badges={badges} />}

      {/* Main area */}
      <div style={{
        flex: 1,
        minWidth: 0,
        marginLeft: !isMobile && user && !hideSidebar ? 'var(--sidebar-width)' : 0,
        display: 'flex', flexDirection: 'column',
        height: '100vh', overflow: 'hidden',
      }}>
        {/* Topbar — desktop only, hidden on project process route (breadcrumb is inside ProzessFlowV3) */}
        {!isMobile && !hideSidebar && (
          <Topbar
            breadcrumbs={breadcrumbs}
            ctaLabel={cta?.label}
            ctaAction={cta?.action}
          />
        )}

        {/* Mobile header */}
        {isMobile && (
          <header style={{
            height: 52, background: 'var(--brand-primary)',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            position: 'fixed', top: 0, left: 0, right: 0, zIndex: 110, flexShrink: 0,
            padding: '0 18px',
          }}>
            <KompagnonLogo variant="icon" height={28} style={{ flexShrink: 0 }} />
            <span style={{
              fontSize: 16, fontWeight: 700, color: '#fff',
              textTransform: 'uppercase', letterSpacing: '.04em',
              fontFamily: 'var(--font-sans)',
            }}>
              {breadcrumbs[breadcrumbs.length - 1]?.label || 'KOMPAGNON'}
            </span>
            {/* User avatar + dropdown */}
            <div style={{ position: 'relative' }}>
              <button
                onClick={() => setMobileMenuOpen(o => !o)}
                style={{
                  width: 30, height: 30, borderRadius: '50%',
                  background: 'var(--brand-primary)',
                  border: 'none', cursor: 'pointer', fontSize: 12, fontWeight: 900,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontFamily: 'var(--font-sans)', color: 'var(--text-on-brand)',
                }}
              >
                {((user?.first_name?.[0] || '') + (user?.last_name?.[0] || '')).toUpperCase() || 'U'}
              </button>
              {mobileMenuOpen && (
                <>
                  <div role="button" tabIndex={0} onKeyDown={aufTaste(() => setMobileMenuOpen(false))}
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
                      <div style={{ fontSize: 12, color: 'var(--text-tertiary)', textTransform: 'capitalize' }}>
                        {user?.role}
                      </div>
                    </div>
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
          id="inhalt"
          // **`tabIndex={-1}` gehoert zum Sprunglink.** Ohne ihn scrollt der
          // Browser zwar zum Ziel, setzt den Fokus aber nicht hinein: Der
          // naechste Tabulator fuehrt zurueck an den Anfang, und der Link
          // haette nichts bewirkt. `-1` heisst „per Programm fokussierbar,
          // nicht in der Tabulatorreihenfolge" — `<main>` selbst soll kein
          // Tabstopp werden.
          tabIndex={-1}
          ref={mainRef}
          style={isMobile ? {
            position: 'fixed',
            top: MOBILE_HEADER_H,
            left: 0, right: 0,
            bottom: `calc(${MOBILE_NAV_H}px + env(safe-area-inset-bottom, 0px))`,
            overflowY: 'auto',
            overflowX: 'hidden',
            WebkitOverflowScrolling: 'touch',
            background: '#F0F4F5',
            padding: '12px 0 0',
          } : {
            flex: 1,
            overflowY: location.pathname.match(/^\/app\/projects\/\d+/) ? 'hidden' : 'auto',
            overflowX: 'hidden',
            minWidth: 0, position: 'relative',
            padding: location.pathname.match(/^\/app\/projects\/\d+/) ? 0 : '20px 28px',
            display: location.pathname.match(/^\/app\/projects\/\d+/) ? 'flex' : 'block',
            flexDirection: 'column',
          }}
        >
          {/* Kaltstart-Banner */}
          {slowApi && (
            <div style={{
              position: 'fixed', zIndex: 200,
              ...(isMobile
                ? { top: 64, left: 16, right: 16 }
                : { bottom: 24, right: 24, maxWidth: 320 }),
              background: 'var(--status-warning-bg)',
              border: '1px solid var(--status-warning-text)',
              borderRadius: 'var(--radius-md)',
              padding: '10px 14px',
              display: 'flex', alignItems: 'center', gap: 10,
              fontSize: 12, color: 'var(--status-warning-text)', fontWeight: 500,
              boxShadow: 'var(--shadow-md)',
              animation: 'bwFadeIn 0.3s ease',
            }}>
              <div style={{ width: 14, height: 14, borderRadius: '50%', border: '2px solid var(--status-warning-text)', borderTopColor: 'transparent', animation: 'spin 0.8s linear infinite', flexShrink: 0 }} />
              Server startet — bitte 30–60 Sekunden warten
            </div>
          )}
          {isMobile && <PullIndicator />}
          <div key={location.pathname} className="page-enter" style={{
            maxWidth: '100%',
            overflowX: 'hidden',
            ...(location.pathname.match(/^\/app\/projects\/\d+/) ? { flex: 1, minHeight: 0, overflow: 'hidden' } : {}),
          }}>
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
