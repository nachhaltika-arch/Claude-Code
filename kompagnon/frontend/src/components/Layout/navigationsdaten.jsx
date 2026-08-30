/**
 * Was die Navigation zeigt — Symbole, Tabs und der Versandhinweis (L-25).
 *
 * Am 2026-08-30 aus `AppLayout.jsx` herausgeloest; die Datei trug 1.183 Zeilen
 * und darin vier Komponenten plus ihre Daten.
 *
 * **Hier steht, was angezeigt wird, nicht wie.** Die Symbole, die Tabs der
 * Mobilansicht und ihre Ueberlaufliste. Wer einen Menuepunkt hinzufuegt,
 * aendert nur diese Datei — die Komponenten daneben lesen sie.
 */
import { useVersand } from '../../context/VersandContext';

export const icons = {
  grid: (
    <svg aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="1.5" y="1.5" width="5" height="5" rx="1"/><rect x="9.5" y="1.5" width="5" height="5" rx="1"/>
      <rect x="1.5" y="9.5" width="5" height="5" rx="1"/><rect x="9.5" y="9.5" width="5" height="5" rx="1"/>
    </svg>
  ),
  chart: (
    <svg aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="8" width="3" height="6" rx="0.5"/><rect x="6.5" y="4" width="3" height="10" rx="0.5"/>
      <rect x="11" y="2" width="3" height="12" rx="0.5"/>
    </svg>
  ),
  users: (
    <svg aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="6" cy="5" r="2.5"/><path d="M1.5 14c0-2.5 2-4.5 4.5-4.5s4.5 2 4.5 4.5"/>
      <circle cx="11" cy="5.5" r="1.8"/><path d="M11 9.5c1.8 0 3.5 1.3 3.5 3.5"/>
    </svg>
  ),
  docCheck: (
    <svg aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 1.5H4a1.5 1.5 0 00-1.5 1.5v10A1.5 1.5 0 004 14.5h8a1.5 1.5 0 001.5-1.5V6L9 1.5z"/>
      <path d="M6 10l1.5 1.5L10 8"/>
    </svg>
  ),
  gradCap: (
    <svg aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M8 2L1.5 6 8 10l6.5-4L8 2z"/><path d="M4 8v3.5c0 1 1.8 2 4 2s4-1 4-2V8"/>
      <path d="M14.5 6v4.5"/>
    </svg>
  ),
  gear: (
    <svg aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="8" cy="8" r="2"/><path d="M13.4 10a1.2 1.2 0 00.2 1.3l.04.04a1.44 1.44 0 11-2.04 2.04l-.04-.04a1.2 1.2 0 00-1.3-.2 1.2 1.2 0 00-.72 1.1v.12a1.44 1.44 0 01-2.88 0v-.06a1.2 1.2 0 00-.78-1.1 1.2 1.2 0 00-1.3.2l-.04.04a1.44 1.44 0 11-2.04-2.04l.04-.04a1.2 1.2 0 00.2-1.3 1.2 1.2 0 00-1.1-.72h-.12a1.44 1.44 0 010-2.88h.06a1.2 1.2 0 001.1-.78 1.2 1.2 0 00-.2-1.3l-.04-.04A1.44 1.44 0 114.3 2.24l.04.04a1.2 1.2 0 001.3.2h.06a1.2 1.2 0 00.72-1.1V1.26a1.44 1.44 0 012.88 0v.06a1.2 1.2 0 00.72 1.1 1.2 1.2 0 001.3-.2l.04-.04a1.44 1.44 0 112.04 2.04l-.04.04a1.2 1.2 0 00-.2 1.3v.06a1.2 1.2 0 001.1.72h.12a1.44 1.44 0 010 2.88h-.06a1.2 1.2 0 00-1.1.72z"/>
    </svg>
  ),
  key: (
    <svg aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="10.5" cy="5.5" r="3"/><path d="M2 14l5.3-5.3"/><path d="M5.8 10.2l1.5 1.5"/>
    </svg>
  ),
  book: (
    <svg aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 2.5A1.5 1.5 0 013.5 1h9A1.5 1.5 0 0114 2.5v11a1.5 1.5 0 01-1.5 1.5h-9A1.5 1.5 0 012 13.5V2.5z"/>
      <path d="M5 1v14M5 5h6M5 8h6M5 11h4"/>
    </svg>
  ),
  newspaper: (
    <svg aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="1.5" y="2.5" width="13" height="11" rx="1.5"/>
      <path d="M4.5 6h7M4.5 8.5h7M4.5 11h4"/>
    </svg>
  ),
  dots: (
    <svg aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
      <circle cx="4" cy="8" r="1.2"/><circle cx="8" cy="8" r="1.2"/><circle cx="12" cy="8" r="1.2"/>
    </svg>
  ),
  logout: (
    <svg aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 14H3a1 1 0 01-1-1V3a1 1 0 011-1h3"/><path d="M10.5 11.5L14 8l-3.5-3.5"/><path d="M14 8H6"/>
    </svg>
  ),
  menu: (
    <svg aria-hidden="true" width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <line x1="3" y1="5" x2="15" y2="5"/><line x1="3" y1="9" x2="15" y2="9"/><line x1="3" y1="13" x2="15" y2="13"/>
    </svg>
  ),
  folder: (
    <svg aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1.5 3.5A1 1 0 012.5 2.5h3.6l1.4 1.5H13.5A1 1 0 0114.5 5v7a1 1 0 01-1 1h-11a1 1 0 01-1-1V3.5z"/>
    </svg>
  ),
  gear: (
    <svg aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="8" cy="8" r="2.5"/><path d="M8 1.5v1.5M8 13v1.5M1.5 8H3M13 8h1.5M3.05 3.05l1.06 1.06M11.89 11.89l1.06 1.06M3.05 12.95l1.06-1.06M11.89 4.11l1.06-1.06"/>
    </svg>
  ),
};

// ── Nav structure ──────────────────────────────────────────────
//
// Hier stand bis 2026-08-17 ein `NAV_SECTIONS` mit sieben Gruppen — nie
// importiert, nie gerendert. Die gerenderte Navigation steht weiter unten
// in `SidebarNav` und wich inhaltlich ab. Entfernt zusammen mit
// `components/Sidebar.jsx`, der dritten toten Definition: Wer beim
// Aufraeumen die falsche findet, aendert die falsche Datei.

export function getMobileTabs(role, leadId) {
  if (role === 'kunde') {
    return [
      { label: 'Start',         path: '/app/dashboard',                                        icon: 'grid'  },
      { label: 'Mein Projekt',  path: leadId ? `/app/usercards/${leadId}` : '/app/dashboard',  icon: 'users' },
      { label: 'Einstellungen', path: '/app/settings',                                         icon: 'gear'  },
    ];
  }
  return [
    { label: 'Dashboard', path: '/app/dashboard', icon: 'grid'  },
    { label: 'Vertrieb',  path: '/app/vertrieb',  icon: 'chart' },
    { label: 'Betriebe',  path: '/app/betriebe',            icon: 'users', badge: true },
    { label: 'Projekte',  path: '/app/projects',  icon: 'users' },
    { label: 'Mehr',      path: '__more__',        icon: 'menu'  },
  ];
}

export const MORE_ITEMS = [
  { label: 'Betriebe', path: '/app/betriebe', icon: '🏢' },
  { label: 'Newsletter', path: '/app/newsletter', icon: '📧' },
  { label: 'Tickets', path: '/app/tickets', icon: '🎫' },
  { label: 'Akademie', path: '/app/academy', icon: '🎓' },
  { label: 'Einstellungen', path: '/app/settings', icon: '⚙️' },
  { label: 'Profil', path: '/app/profile', icon: '👤' },
];

export const MORE_ITEMS_ADMIN = [
  ...MORE_ITEMS,
  { label: 'Produkteditor', path: '/app/product-editor', icon: '🛒' },
  { label: 'Domain Import', path: '/app/import', icon: '⬆️' },
];

// ── Hinweis: automatischer Versand ist aus ─────────────────────
//
// Ein Not-Aus, den man nur in den Einstellungen sieht, ist ein Not-Aus, den
// man vergisst. Nach dem Vorfall vom 17.08.2026 gilt: Der abgeschaltete
// Zustand steht dort, wo man ohnehin hinsieht.
//
// Gezeigt wird nur, was von der Normallage abweicht — ist der Versand an,
// steht hier nichts. Ein Dauerhinweis wird nach drei Tagen unsichtbar.
export function VersandHinweis({ onClick }) {
  const { erlaubt, laedt } = useVersand();

  if (laedt || erlaubt === true) return null;

  const unbekannt = erlaubt === null;

  return (
    <button
      type="button" onClick={onClick}
      title={unbekannt
        ? 'Der Zustand des automatischen Versands konnte nicht geladen werden.'
        : 'Kein Job verschickt derzeit von sich aus E-Mails. Zum Umschalten klicken.'}
      style={{
        display: 'flex', alignItems: 'center', gap: 8, width: '100%',
        margin: '8px 0 0', padding: '8px 10px',
        borderRadius: 'var(--radius-md)', cursor: 'pointer', textAlign: 'left',
        border: `1px solid ${unbekannt ? 'var(--border-medium)' : 'var(--status-warning-text)'}`,
        background: unbekannt ? 'transparent' : 'var(--status-warning-bg)',
        color: unbekannt ? 'var(--text-tertiary)' : 'var(--status-warning-text)',
        fontFamily: 'var(--font-sans)', fontSize: 11, fontWeight: 600,
        lineHeight: 1.35,
      }}
    >
      <span aria-hidden="true" style={{ fontSize: 13 }}>{unbekannt ? '?' : '🛑'}</span>
      <span>
        {unbekannt ? 'Versand-Zustand unbekannt' : 'Automatischer Versand aus'}
      </span>
    </button>
  );
}

// ── Sidebar ────────────────────────────────────────────────────

