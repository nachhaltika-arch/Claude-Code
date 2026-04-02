import { useState } from 'react';
import { useAuth } from '../context/AuthContext';

// ── Dummy data ────────────────────────────────────────────────────────────────

const DUMMY_COURSES = [
  {
    id: 1,
    title: 'Gratis Mitgliedschaft',
    description: 'Einführung in das KOMPAGNON-System und erste Schritte für neue Mitglieder.',
    category: 'intern',
    chapters: 0,
    participants: 14,
    duration: '0:18:00',
    color: '#3b82f6',
    initials: 'GM',
  },
  {
    id: 2,
    title: 'Website-Pflege für Kunden',
    description: 'Wie Kunden ihre Website eigenständig pflegen, Inhalte aktualisieren und häufige Fehler vermeiden.',
    category: 'kunde',
    chapters: 4,
    participants: 38,
    duration: '1:24:45',
    color: '#16a34a',
    initials: 'WP',
  },
  {
    id: 3,
    title: 'Homepage Standard 2025 — Das Produkt',
    description: 'Vollständige Produktschulung: Anforderungen, Audit-Kriterien, Zertifizierungsstufen und Umsetzungsprozess.',
    category: 'produkt',
    chapters: 6,
    participants: 9,
    duration: '3:03:19',
    color: '#7c3aed',
    initials: 'HS',
  },
];

const CATEGORIES = [
  { value: 'all',     label: 'Alle' },
  { value: 'intern',  label: 'Intern' },
  { value: 'kunde',   label: 'Kunden' },
  { value: 'produkt', label: 'Produkt' },
];

const BADGE = {
  intern:  { label: 'Intern',   bg: '#eff6ff', color: '#1d4ed8' },
  kunde:   { label: 'Kunde',    bg: '#f0fdf4', color: '#15803d' },
  produkt: { label: 'Produkt',  bg: '#faf5ff', color: '#6d28d9' },
};

// ── Main Component ────────────────────────────────────────────────────────────

export default function Courses() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [activeTab, setActiveTab]     = useState('all');
  const [search, setSearch]           = useState('');
  const [categoryFilter, setCategory] = useState('all');
  const [openMenu, setOpenMenu]       = useState(null);

  const filtered = DUMMY_COURSES.filter(c => {
    if (activeTab === 'mine') return false; // placeholder — no enrollment yet
    if (categoryFilter !== 'all' && c.category !== categoryFilter) return false;
    if (search && !c.title.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 900, margin: '0 auto', width: '100%' }}
      onClick={() => openMenu && setOpenMenu(null)}
    >
      {/* ── Header ── */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>Kurse</h1>
          <p style={{ fontSize: 13, color: 'var(--text-tertiary)', marginTop: 4 }}>Lernmaterialien &amp; Schulungen</p>
        </div>
        {isAdmin && (
          <button
            style={{
              background: 'var(--brand-primary)', color: 'white',
              border: 'none', borderRadius: 'var(--radius-md)',
              padding: '9px 16px', fontSize: 13, fontWeight: 600,
              cursor: 'pointer', fontFamily: 'var(--font-sans)',
              display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0,
            }}
          >
            + Kurs erstellen
          </button>
        )}
      </div>

      {/* ── Tabs ── */}
      <div style={{ display: 'flex', gap: 0, borderBottom: '1px solid var(--border-light)' }}>
        {[{ id: 'all', label: 'Alle Kurse' }, { id: 'mine', label: 'Meine Kurse' }].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '8px 16px', border: 'none', background: 'transparent',
              fontFamily: 'var(--font-sans)', fontSize: 13, cursor: 'pointer',
              color: activeTab === tab.id ? 'var(--brand-primary)' : 'var(--text-tertiary)',
              fontWeight: activeTab === tab.id ? 600 : 400,
              borderBottom: activeTab === tab.id ? '2px solid var(--brand-primary)' : '2px solid transparent',
              marginBottom: -1,
              transition: 'color 0.15s',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── Filters ── */}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Kurse suchen…"
          style={{
            flex: '1 1 200px', padding: '8px 12px', fontSize: 13,
            border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)',
            background: 'var(--bg-surface)', color: 'var(--text-primary)',
            fontFamily: 'var(--font-sans)', outline: 'none',
          }}
        />
        <select
          value={categoryFilter}
          onChange={e => setCategory(e.target.value)}
          style={{
            padding: '8px 12px', fontSize: 13,
            border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)',
            background: 'var(--bg-surface)', color: 'var(--text-primary)',
            fontFamily: 'var(--font-sans)', cursor: 'pointer', outline: 'none',
            flexShrink: 0,
          }}
        >
          {CATEGORIES.map(c => (
            <option key={c.value} value={c.value}>{c.label}</option>
          ))}
        </select>
      </div>

      {/* ── Course list ── */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {activeTab === 'mine' ? (
          <EmptyState
            icon="📚"
            title="Noch keine Kurse belegt"
            sub="Stöbere in allen Kursen und starte dein erstes Training."
          />
        ) : filtered.length === 0 ? (
          <EmptyState
            icon="🔍"
            title="Keine Kurse gefunden"
            sub="Passe die Suche oder den Filter an."
          />
        ) : (
          filtered.map(course => (
            <CourseCard
              key={course.id}
              course={course}
              menuOpen={openMenu === course.id}
              onMenuToggle={(e) => { e.stopPropagation(); setOpenMenu(openMenu === course.id ? null : course.id); }}
              onMenuClose={() => setOpenMenu(null)}
              isAdmin={isAdmin}
            />
          ))
        )}
      </div>
    </div>
  );
}

// ── Course Card ───────────────────────────────────────────────────────────────

function CourseCard({ course, menuOpen, onMenuToggle, onMenuClose, isAdmin }) {
  const badge = BADGE[course.category];

  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border-light)',
      borderRadius: 'var(--radius-lg)',
      padding: '14px 16px',
      display: 'flex', alignItems: 'center', gap: 14,
      transition: 'border-color 0.15s',
    }}
      onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--border-medium)'}
      onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border-light)'}
    >
      {/* Thumbnail */}
      <div style={{
        width: 80, height: 80, borderRadius: 'var(--radius-md)', flexShrink: 0,
        background: course.color, display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 22, fontWeight: 700, color: 'white', letterSpacing: '0.02em',
        userSelect: 'none',
      }}>
        {course.initials}
      </div>

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 4 }}>
          <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {course.title}
          </span>
          {badge && (
            <span style={{
              fontSize: 10, fontWeight: 600, padding: '2px 8px',
              borderRadius: 'var(--radius-full)', background: badge.bg, color: badge.color,
              border: `1px solid ${badge.color}30`, flexShrink: 0,
            }}>
              {badge.label}
            </span>
          )}
        </div>
        <p style={{ fontSize: 12, color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
          {course.description}
        </p>

        {/* Stats */}
        <div style={{ display: 'flex', gap: 16, marginTop: 8 }}>
          <Stat icon="📖" value={`${course.chapters} Kapitel`} />
          <Stat icon="👤" value={`${course.participants} Teilnehmer`} />
          <Stat icon="⏱" value={course.duration} />
        </div>
      </div>

      {/* Menu */}
      <div style={{ position: 'relative', flexShrink: 0 }} onClick={e => e.stopPropagation()}>
        <button
          onClick={onMenuToggle}
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--text-tertiary)', fontSize: 18, padding: '4px 6px',
            borderRadius: 'var(--radius-sm)', lineHeight: 1,
            transition: 'background 0.1s, color 0.1s',
          }}
          onMouseEnter={e => { e.currentTarget.style.background = 'var(--bg-hover)'; e.currentTarget.style.color = 'var(--text-primary)'; }}
          onMouseLeave={e => { e.currentTarget.style.background = 'none'; e.currentTarget.style.color = 'var(--text-tertiary)'; }}
          title="Optionen"
        >
          ⋮
        </button>

        {menuOpen && (
          <div style={{
            position: 'absolute', top: 'calc(100% + 4px)', right: 0,
            background: 'var(--bg-elevated)', border: '1px solid var(--border-light)',
            borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-lg)',
            padding: 4, zIndex: 100, minWidth: 150,
          }}>
            <MenuItem onClick={onMenuClose}>Kurs öffnen</MenuItem>
            {isAdmin && (
              <>
                <MenuItem onClick={onMenuClose}>Bearbeiten</MenuItem>
                <div style={{ height: 1, background: 'var(--border-light)', margin: '4px 0' }} />
                <MenuItem onClick={onMenuClose} danger>Löschen</MenuItem>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function Stat({ icon, value }) {
  return (
    <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: 'var(--text-tertiary)' }}>
      <span>{icon}</span>
      <span>{value}</span>
    </span>
  );
}

function MenuItem({ children, onClick, danger }) {
  return (
    <button
      onClick={onClick}
      style={{
        width: '100%', display: 'block', padding: '7px 10px',
        background: 'transparent', border: 'none', borderRadius: 'var(--radius-sm)',
        fontFamily: 'var(--font-sans)', fontSize: 13, cursor: 'pointer',
        color: danger ? 'var(--status-danger-text)' : 'var(--text-secondary)',
        textAlign: 'left', transition: 'background 0.1s',
      }}
      onMouseEnter={e => e.currentTarget.style.background = danger ? 'var(--status-danger-bg)' : 'var(--bg-hover)'}
      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
    >
      {children}
    </button>
  );
}

function EmptyState({ icon, title, sub }) {
  return (
    <div style={{
      textAlign: 'center', padding: '48px 24px',
      border: '1.5px dashed var(--border-medium)', borderRadius: 'var(--radius-lg)',
      color: 'var(--text-tertiary)',
    }}>
      <div style={{ fontSize: 32, marginBottom: 12 }}>{icon}</div>
      <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>{title}</div>
      <div style={{ fontSize: 13 }}>{sub}</div>
    </div>
  );
}
