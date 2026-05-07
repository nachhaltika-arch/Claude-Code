/**
 * KASSidebar — Sidebar fuer den ProzessFlowV3-Editor (Schritt F).
 *
 * Zwei Ebenen:
 *   1. View-Switcher (oben): 4 Buttons fuer Sitemap / Wireframe / Style Guide / Design
 *   2. Phasen-Navigator (Mitte): 17 Schritte gruppiert in 6 Phasen, mit Status-Dots
 *
 * Plus Fortschrittsleiste unten.
 *
 * Diese Komponente ist die Source-of-Truth fuer die SCHRITTE-Konstante.
 * Step G (ProzessFlowV3-Refactor) importiert sie von hier und verbindet
 * die Schritte mit dem tatsaechlichen Workflow-State.
 *
 * Props:
 *   activeView           — 'sitemap' | 'wireframe' | 'styleguide' | 'design'
 *   onViewChange(view)
 *   activeStep           — id eines Schritts aus SCHRITTE
 *   onStepClick(stepId)
 *   stepStatus           — { [stepId]: 'completed'|'active'|'pending' }
 *   isOpen               — Mobile collapse state
 *   onClose              — Mobile close callback
 *
 * Brand-Farben:
 *   #004F59 KC_DARK     - Sidebar-Hintergrund
 *   #008EAA KC_MID      - aktive View-Tab + Logo-Mark
 *   #FAE600 KC_YELLOW   - aktiver Schritt-Dot + Fortschrittsleiste
 *   #1D9E75 GREEN       - 'completed' Dot
 */
import { useEffect, useMemo, useState } from 'react';

// Phase D: localStorage-Key fuer den Collapse-State, damit das Setting
// ueber Reloads erhalten bleibt.
const COLLAPSE_KEY = 'kas:sidebar:collapsed';

const KC_DARK = '#004F59';
const KC_MID = '#008EAA';
const KC_YELLOW = '#FAE600';
const GREEN = '#1D9E75';

// ── 17 Schritte in 6 Phasen — aus dem Online-Fertig-Spec ────────────────────
//
// view       — schaltet die rechte Spalte auf eine der 4 neuen Views
//              (SitemapView/WireframeView/StyleGuideView/DesignView)
// component  — fuer Steps OHNE view: rendert SchrittInhalt aus
//              ProzessFlow.jsx mit dem entsprechenden case-Branch
//              (BriefingUnternehmenEmbed, AuditEmbed, etc.)
// gate       — Gate-Schritt mit Lock-Icon (Customer-Approval)
// optional   — kein Pflichtschritt fuer Fortschritt
export const SCHRITTE = [
  // Phase 1 — Analyse (5)
  { id: 'briefing-unternehmen', nr: 1,  phase: 'Analyse',     name: 'Briefing: Unternehmen', view: null,         component: 'BriefingUnternehmen' },
  { id: 'audit',                nr: 2,  phase: 'Analyse',     name: 'Website-Audit',          view: null,         component: 'Audit' },
  { id: 'content-vollanalyse',  nr: 3,  phase: 'Analyse',     name: 'Content-Vollanalyse',    view: null,         component: 'AnalyseZentrale' },
  { id: 'briefing-website',     nr: 4,  phase: 'Analyse',     name: 'Briefing: Website',      view: null,         component: 'BriefingWebsite' },
  { id: 'zugangsdaten',         nr: 5,  phase: 'Analyse',     name: 'Zugangsdaten',           view: null,         component: 'Zugangsdaten', optional: true },

  // Phase 2 — Sitemap + Wireframe (2)
  { id: 'sitemap-ki',           nr: 6,  phase: 'Sitemap',     name: 'KI-Sitemap',             view: 'sitemap',    component: null },
  { id: 'wireframe-ki',         nr: 7,  phase: 'Sitemap',     name: 'KI-Wireframe',           view: 'wireframe',  component: null },

  // Phase 3 — Style Guide + Design (2, mit Gate)
  { id: 'style-guide',          nr: 8,  phase: 'Design',      name: 'Style Guide',            view: 'styleguide', component: null, gate: true },
  { id: 'finales-design',       nr: 9,  phase: 'Design',      name: 'Finales Design',         view: 'design',     component: null },

  // Phase 4 — Produktion (2)
  { id: 'ki-content',           nr: 10, phase: 'Produktion',  name: 'KI-Content',             view: null,         component: 'ContentWerkstatt' },
  { id: 'netlify-deploy',       nr: 11, phase: 'Produktion',  name: 'Netlify Deploy',         view: null,         component: 'Netlify' },

  // Phase 5 — Go Live (3, mit Gate)
  { id: 'dns',                  nr: 12, phase: 'GoLive',      name: 'DNS',                    view: null,         component: 'DNS' },
  { id: 'qa',                   nr: 13, phase: 'GoLive',      name: 'QA-Check',               view: null,         component: 'QA' },
  { id: 'abnahme',              nr: 14, phase: 'GoLive',      name: 'Abnahme',                view: null,         component: 'Abnahme', gate: true },

  // Phase 6 — Post-Launch (3) — noch keine Legacy-Components, nur Placeholder
  { id: 'umami',                nr: 15, phase: 'PostLaunch',  name: 'Umami einrichten',       view: null,         component: null },
  { id: 'heatmap',              nr: 16, phase: 'PostLaunch',  name: 'Heatmap einrichten',     view: null,         component: null },
  { id: 'monats-report',        nr: 17, phase: 'PostLaunch',  name: 'Monats-Report',          view: null,         component: null },
];

const PHASE_META = {
  Analyse:    { label: 'Analyse',     icon: '🔍' },
  Sitemap:    { label: 'Sitemap',     icon: '🗺' },
  Design:     { label: 'Design',      icon: '🎨' },
  Produktion: { label: 'Produktion',  icon: '⚙️' },
  GoLive:     { label: 'Go Live',     icon: '🚀' },
  PostLaunch: { label: 'Post-Launch', icon: '📊' },
};

const VIEW_TABS = [
  { id: 'sitemap',    label: 'Sitemap',     icon: SitemapIcon },
  { id: 'wireframe',  label: 'Wireframe',   icon: WireframeIcon },
  { id: 'styleguide', label: 'Style Guide', icon: StyleGuideIcon },
  { id: 'design',     label: 'Design',      icon: DesignIcon },
];

// Schritte nach Phase gruppiert (Source-of-Truth aus SCHRITTE)
function groupByPhase(schritte) {
  const map = new Map();
  for (const s of schritte) {
    if (!map.has(s.phase)) map.set(s.phase, []);
    map.get(s.phase).push(s);
  }
  return [...map.entries()].map(([phase, steps]) => ({
    phase,
    label: PHASE_META[phase]?.label || phase,
    icon:  PHASE_META[phase]?.icon || '•',
    steps,
  }));
}

export default function KASSidebar({
  activeView,
  onViewChange,
  activeStep,
  onStepClick,
  stepStatus = {},
  isOpen = true,
  onClose,
}) {
  const phaseGroups = useMemo(() => groupByPhase(SCHRITTE), []);

  // Phase auf, in der sich der active Step befindet — sonst Default die erste
  const initialOpenPhase = useMemo(() => {
    const found = SCHRITTE.find((s) => s.id === activeStep);
    return found?.phase || phaseGroups[0]?.phase;
  }, [activeStep, phaseGroups]);

  const [openPhase, setOpenPhase] = useState(initialOpenPhase);

  // Phase D: Collapsed-State persistent. Default = expanded.
  const [collapsed, setCollapsed] = useState(() => {
    try { return localStorage.getItem(COLLAPSE_KEY) === '1'; } catch { return false; }
  });
  const toggleCollapsed = () => {
    setCollapsed((c) => {
      const next = !c;
      try { localStorage.setItem(COLLAPSE_KEY, next ? '1' : '0'); } catch {}
      return next;
    });
  };

  const completedCount = SCHRITTE.filter((s) => stepStatus[s.id] === 'completed').length;
  const progressPct = Math.round((completedCount / SCHRITTE.length) * 100);

  if (!isOpen) return null;

  return (
    <aside
      style={{
        width: collapsed ? 56 : 220,
        flexShrink: 0,
        height: '100vh',
        background: KC_DARK,
        color: '#fff',
        display: 'flex',
        flexDirection: 'column',
        fontFamily: 'var(--font-sans, "Noto Sans", sans-serif)',
        transition: 'width 0.2s ease-out',
      }}
      aria-label="Prozess-Sidebar"
    >
      {/* Logo-Header */}
      <div style={{
        padding: collapsed ? '14px 0' : '18px 16px',
        borderBottom: '1px solid rgba(255,255,255,0.08)',
        display: 'flex', alignItems: 'center', justifyContent: collapsed ? 'center' : 'flex-start', gap: 10,
      }}>
        <div
          aria-hidden
          title={collapsed ? 'KOMPAGNON · ProzessFlow v3' : undefined}
          style={{
            width: 28, height: 28, background: KC_MID, borderRadius: 6,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', fontWeight: 900, fontSize: 13, letterSpacing: '-0.05em',
            flexShrink: 0,
          }}
        >
          KA
        </div>
        {!collapsed && (
          <>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 13, fontWeight: 800, letterSpacing: '-0.01em', textTransform: 'uppercase' }}>
                ONLINE-FERTIG
              </div>
              <div style={{ fontSize: 9, opacity: 0.55, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                ProzessFlow v3
              </div>
            </div>
            {onClose && (
              <button
                type="button"
                onClick={onClose}
                aria-label="Sidebar schließen"
                style={{ background: 'none', border: 'none', color: 'rgba(255,255,255,0.5)', fontSize: 18, cursor: 'pointer' }}
              >
                ✕
              </button>
            )}
          </>
        )}
      </div>

      {/* Ebene 1: View-Switcher */}
      <div style={{
        padding: collapsed ? '8px 6px' : '14px 12px 10px',
        borderBottom: '1px solid rgba(255,255,255,0.08)',
      }}>
        {!collapsed && (
          <div style={{ fontSize: 9, fontWeight: 700, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: 8, paddingLeft: 4 }}>
            Ansicht
          </div>
        )}
        <div style={{
          display: 'grid',
          gridTemplateColumns: collapsed ? '1fr' : '1fr 1fr',
          gap: 4,
        }}>
          {VIEW_TABS.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeView === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => onViewChange?.(tab.id)}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: collapsed ? 0 : 4,
                  padding: collapsed ? '10px 4px' : '10px 4px',
                  background: isActive ? 'rgba(255,255,255,0.12)' : 'transparent',
                  color: isActive ? '#fff' : 'rgba(255,255,255,0.55)',
                  border: isActive ? `1px solid ${KC_MID}` : '1px solid transparent',
                  borderRadius: 6,
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                  fontSize: 9,
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                }}
                aria-pressed={isActive}
                title={tab.label}
              >
                <Icon active={isActive} />
                {!collapsed && <span>{tab.label}</span>}
              </button>
            );
          })}
        </div>
      </div>

      {/* Phase D: Im Collapsed-Mode Phasen-Navigator komplett ausblenden, nur
          schmaler Scroll-Spacer + aktive Phase als Icon-Marker */}
      {collapsed ? (
        <nav style={{ flex: 1, overflowY: 'auto', padding: '8px 6px' }} aria-label="Phasen kompakt">
          {phaseGroups.map((group) => {
            const stepsCompleted = group.steps.filter((s) => stepStatus[s.id] === 'completed').length;
            const allCompleted = stepsCompleted === group.steps.length;
            const containsActive = group.steps.some((s) => s.id === activeStep);
            return (
              <button
                key={group.phase} type="button"
                onClick={() => {
                  // Klick im Collapsed-Mode: zur ersten un-locked-Step der Phase springen
                  const firstNonLocked = group.steps.find((s) => stepStatus[s.id] !== 'locked');
                  if (firstNonLocked) onStepClick?.(firstNonLocked.id);
                }}
                title={`${group.label} (${stepsCompleted}/${group.steps.length})`}
                style={{
                  width: '100%', padding: '10px 0', marginBottom: 2,
                  background: containsActive ? 'rgba(255,255,255,0.10)' : 'transparent',
                  border: containsActive ? `1px solid ${KC_MID}` : '1px solid transparent',
                  borderRadius: 6, cursor: 'pointer', color: '#fff',
                  fontFamily: 'inherit',
                  display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2,
                }}
              >
                <span aria-hidden style={{ fontSize: 16, opacity: allCompleted ? 1 : 0.7 }}>
                  {group.icon}
                </span>
                <span style={{
                  fontSize: 8, fontVariantNumeric: 'tabular-nums',
                  color: allCompleted ? GREEN : 'rgba(255,255,255,0.55)',
                  fontWeight: 700,
                }}>
                  {stepsCompleted}/{group.steps.length}
                </span>
              </button>
            );
          })}
        </nav>
      ) : (
      <nav
        style={{ flex: 1, overflowY: 'auto', padding: '12px 8px' }}
        aria-label="Phasen und Schritte"
      >
        {phaseGroups.map((group) => {
          const stepsCompleted = group.steps.filter((s) => stepStatus[s.id] === 'completed').length;
          const isOpenPhase = openPhase === group.phase;

          return (
            <div key={group.phase} style={{ marginBottom: 4 }}>
              {/* Phase-Header — klickbar zum Toggle */}
              <button
                type="button"
                onClick={() => setOpenPhase(isOpenPhase ? null : group.phase)}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '8px 10px',
                  background: 'transparent',
                  border: 'none',
                  color: '#fff',
                  cursor: 'pointer',
                  borderRadius: 4,
                  textAlign: 'left',
                }}
                aria-expanded={isOpenPhase}
              >
                <span aria-hidden style={{ fontSize: 14 }}>{group.icon}</span>
                <span style={{ flex: 1, fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  {group.label}
                </span>
                <span style={{ fontSize: 10, opacity: 0.55, fontVariantNumeric: 'tabular-nums' }}>
                  {stepsCompleted}/{group.steps.length}
                </span>
                <span style={{ fontSize: 9, opacity: 0.5, marginLeft: 4, transition: 'transform 0.2s', display: 'inline-block', transform: isOpenPhase ? 'rotate(180deg)' : 'rotate(0)' }}>
                  ▼
                </span>
              </button>

              {/* Schritte der Phase (collapsible) */}
              {isOpenPhase && (
                <ul style={{ listStyle: 'none', padding: '2px 0 4px 0', margin: 0 }}>
                  {group.steps.map((step) => {
                    const status = stepStatus[step.id] || 'pending';
                    const isActive = step.id === activeStep;
                    const isLocked = status === 'locked';
                    const dotColor =
                      status === 'completed' ? GREEN :
                      isActive ? KC_YELLOW :
                      status === 'ready' ? 'rgba(255,255,255,0.5)' :
                      'rgba(255,255,255,0.15)';
                    return (
                      <li key={step.id}>
                        <button
                          type="button"
                          onClick={() => onStepClick?.(step.id)}
                          aria-disabled={isLocked}
                          title={isLocked ? 'Gesperrt — vorherigen Schritt zuerst abschließen' : step.name}
                          style={{
                            width: '100%',
                            display: 'flex',
                            alignItems: 'center',
                            gap: 10,
                            padding: '6px 10px 6px 18px',
                            background: isActive ? 'rgba(255,255,255,0.06)' : 'transparent',
                            border: 'none',
                            borderLeft: isActive ? `2px solid ${KC_YELLOW}` : '2px solid transparent',
                            color: isActive ? '#fff' : isLocked ? 'rgba(255,255,255,0.25)' : 'rgba(255,255,255,0.55)',
                            cursor: isLocked ? 'not-allowed' : 'pointer',
                            opacity: isLocked ? 0.55 : 1,
                            textAlign: 'left',
                            fontSize: 10,
                            fontWeight: isActive ? 700 : 500,
                            transition: 'all 0.12s',
                          }}
                        >
                          <span
                            aria-hidden
                            style={{
                              width: 8,
                              height: 8,
                              borderRadius: '50%',
                              background: dotColor,
                              flexShrink: 0,
                              boxShadow: isActive ? `0 0 0 2px rgba(250,230,0,0.25)` : 'none',
                            }}
                          />
                          <span style={{ flex: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {step.nr}. {step.name}
                          </span>
                          {status === 'completed' && (
                            <span aria-label="Abgeschlossen" style={{ fontSize: 9, color: GREEN, fontWeight: 700 }}>✓</span>
                          )}
                          {isLocked && (
                            <span aria-label="Gesperrt" style={{ fontSize: 9, opacity: 0.65 }}>🔒</span>
                          )}
                          {step.optional && !isLocked && status !== 'completed' && (
                            <span style={{ fontSize: 8, opacity: 0.5, fontStyle: 'italic' }}>opt.</span>
                          )}
                          {step.gate && !isLocked && status !== 'completed' && (
                            <span aria-label="Gate" title="Gate-Schritt" style={{ fontSize: 9, opacity: 0.55 }}>⚑</span>
                          )}
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          );
        })}
      </nav>

      )}

      {/* Fortschrittsleiste */}
      <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)' }}>
        {!collapsed && (
          <div style={{ padding: '8px 16px 4px', display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'rgba(255,255,255,0.55)' }}>
            <span style={{ fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Fortschritt</span>
            <span style={{ fontVariantNumeric: 'tabular-nums', fontWeight: 700, color: '#fff' }}>
              {completedCount}/{SCHRITTE.length}
            </span>
          </div>
        )}
        <div
          title={collapsed ? `Fortschritt: ${completedCount}/${SCHRITTE.length}` : undefined}
          style={{ height: 3, background: 'rgba(255,255,255,0.08)', overflow: 'hidden' }}
        >
          <div
            style={{
              height: '100%',
              width: `${progressPct}%`,
              background: KC_YELLOW,
              transition: 'width 0.3s',
            }}
          />
        </div>
        {/* Phase D: Collapse-Toggle ganz unten */}
        <button
          type="button"
          onClick={toggleCollapsed}
          aria-label={collapsed ? 'Sidebar einblenden' : 'Sidebar einklappen'}
          title={collapsed ? 'Sidebar einblenden' : 'Sidebar einklappen'}
          style={{
            width: '100%', padding: '8px 0',
            background: 'transparent', border: 'none',
            color: 'rgba(255,255,255,0.55)',
            cursor: 'pointer', fontSize: 14,
            fontFamily: 'inherit',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
          }}
          onMouseEnter={(e) => { e.currentTarget.style.color = '#fff'; }}
          onMouseLeave={(e) => { e.currentTarget.style.color = 'rgba(255,255,255,0.55)'; }}
        >
          <span aria-hidden style={{ fontSize: 14, lineHeight: 1 }}>
            {collapsed ? '»' : '«'}
          </span>
          {!collapsed && (
            <span style={{ fontSize: 9, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Einklappen
            </span>
          )}
        </button>
      </div>
    </aside>
  );
}

// ── View-Tab-Icons (inline SVG, kein Icon-Library-Dependency) ──────────────

function SitemapIcon({ active }) {
  const stroke = active ? '#fff' : 'rgba(255,255,255,0.55)';
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <rect x="3"  y="3"  width="6" height="6" />
      <rect x="15" y="3"  width="6" height="6" />
      <rect x="3"  y="15" width="6" height="6" />
      <rect x="15" y="15" width="6" height="6" />
      <line x1="9" y1="6"  x2="15" y2="6" />
      <line x1="9" y1="18" x2="15" y2="18" />
      <line x1="6" y1="9"  x2="6"  y2="15" />
      <line x1="18" y1="9" x2="18" y2="15" />
    </svg>
  );
}

function WireframeIcon({ active }) {
  const stroke = active ? '#fff' : 'rgba(255,255,255,0.55)';
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <rect x="3" y="3"  width="18" height="4" />
      <rect x="3" y="9"  width="18" height="6" />
      <rect x="3" y="17" width="8"  height="4" />
      <rect x="13" y="17" width="8" height="4" />
    </svg>
  );
}

function StyleGuideIcon({ active }) {
  const stroke = active ? '#fff' : 'rgba(255,255,255,0.55)';
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M12 2 L22 12 L12 22 L2 12 Z" />
    </svg>
  );
}

function DesignIcon({ active }) {
  const stroke = active ? '#fff' : 'rgba(255,255,255,0.55)';
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M12 2 A10 10 0 0 1 22 12 L12 12 Z" fill={active ? KC_MID : 'rgba(255,255,255,0.15)'} />
      <circle cx="12" cy="12" r="10" />
    </svg>
  );
}
