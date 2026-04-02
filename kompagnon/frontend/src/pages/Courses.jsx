import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

// ── Constants ─────────────────────────────────────────────────────────────────

const CATEGORIES = [
  { value: 'all',     label: 'Alle' },
  { value: 'intern',  label: 'Intern' },
  { value: 'kunde',   label: 'Kunden' },
  { value: 'produkt', label: 'Produkt' },
];

const CATEGORY_OPTIONS = CATEGORIES.slice(1); // without "Alle", for form select

const BADGE = {
  intern:  { label: 'Intern',   bg: '#eff6ff', color: '#1d4ed8' },
  kunde:   { label: 'Kunde',    bg: '#f0fdf4', color: '#15803d' },
  produkt: { label: 'Produkt',  bg: '#faf5ff', color: '#6d28d9' },
};

const COLOR_OPTIONS = ['#008eaa', '#059669', '#7c3aed'];

// Derive initials from title (up to 2 words)
function initials(title = '') {
  return title.trim().split(/\s+/).slice(0, 2).map(w => w[0]?.toUpperCase() || '').join('');
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function Courses() {
  const { user, token } = useAuth();
  const isAdmin = user?.role === 'admin';

  // List state
  const [courses, setCourses]         = useState([]);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState(null);

  // UI state
  const [activeTab, setActiveTab]     = useState('all');
  const [search, setSearch]           = useState('');
  const [categoryFilter, setCategory] = useState('all');
  const [openMenu, setOpenMenu]       = useState(null);

  // Modal state
  const [modalMode, setModalMode]     = useState(null); // null | 'create' | 'edit'
  const [modalCourse, setModalCourse] = useState(null); // course being edited
  const [saving, setSaving]           = useState(false);
  const [form, setForm]               = useState({
    title: '', description: '', category: 'intern', thumbnail_color: '#008eaa',
  });

  // Delete state
  const [deleteId, setDeleteId]       = useState(null);
  const [deleting, setDeleting]       = useState(false);

  // ── API helpers ─────────────────────────────────────────────────────────────

  const headers = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const loadCourses = useCallback(async () => {
    setLoading(true);
    setError(null);
    const url = categoryFilter === 'all'
      ? `${API_BASE_URL}/api/courses/`
      : `${API_BASE_URL}/api/courses/?category=${categoryFilter}`;
    try {
      const res = await fetch(url, { headers });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setCourses(await res.json());
    } catch (e) {
      setError('Kurse konnten nicht geladen werden. Bitte versuche es erneut.');
    } finally {
      setLoading(false);
    }
  }, [categoryFilter, token]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { loadCourses(); }, [loadCourses]);

  // ── Modal helpers ───────────────────────────────────────────────────────────

  const openCreate = () => {
    setForm({ title: '', description: '', category: 'intern', thumbnail_color: '#008eaa' });
    setModalCourse(null);
    setModalMode('create');
  };

  const openEdit = (course) => {
    setForm({
      title:           course.title,
      description:     course.description || '',
      category:        course.category || 'intern',
      thumbnail_color: course.thumbnail_color || '#008eaa',
    });
    setModalCourse(course);
    setModalMode('edit');
  };

  const closeModal = () => { setModalMode(null); setModalCourse(null); setSaving(false); };

  const handleSave = async () => {
    if (!form.title.trim()) return;
    setSaving(true);
    try {
      const url    = modalMode === 'create'
        ? `${API_BASE_URL}/api/courses/`
        : `${API_BASE_URL}/api/courses/${modalCourse.id}`;
      const method = modalMode === 'create' ? 'POST' : 'PUT';
      const res = await fetch(url, { method, headers, body: JSON.stringify(form) });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      closeModal();
      await loadCourses();
    } catch {
      setSaving(false);
    }
  };

  // ── Delete helpers ──────────────────────────────────────────────────────────

  const handleDelete = async () => {
    if (!deleteId) return;
    setDeleting(true);
    try {
      await fetch(`${API_BASE_URL}/api/courses/${deleteId}`, { method: 'DELETE', headers });
      setDeleteId(null);
      await loadCourses();
    } finally {
      setDeleting(false);
    }
  };

  // ── Filtered list (client-side text search only) ────────────────────────────

  const filtered = courses.filter(c => {
    if (activeTab === 'mine') return false;
    if (search && !c.title.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  // ── Render ──────────────────────────────────────────────────────────────────

  return (
    <div
      style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 900, margin: '0 auto', width: '100%' }}
      onClick={() => openMenu && setOpenMenu(null)}
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>Kurse</h1>
          <p style={{ fontSize: 13, color: 'var(--text-tertiary)', marginTop: 4 }}>Lernmaterialien &amp; Schulungen</p>
        </div>
        {isAdmin && (
          <button
            onClick={openCreate}
            style={{
              background: 'var(--brand-primary)', color: 'white', border: 'none',
              borderRadius: 'var(--radius-md)', padding: '9px 16px', fontSize: 13,
              fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)',
              display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0,
            }}
          >
            + Kurs erstellen
          </button>
        )}
      </div>

      {/* Tabs */}
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
              marginBottom: -1, transition: 'color 0.15s',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Filters */}
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
            fontFamily: 'var(--font-sans)', cursor: 'pointer', outline: 'none', flexShrink: 0,
          }}
        >
          {CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
        </select>
      </div>

      {/* Course list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '48px 0' }}>
            <div style={{
              width: 32, height: 32, borderRadius: '50%',
              border: '3px solid var(--border-light)', borderTopColor: 'var(--brand-primary)',
              animation: 'spin 0.8s linear infinite',
            }} />
          </div>
        ) : error ? (
          <div style={{
            textAlign: 'center', padding: '32px 24px',
            border: '1px solid var(--status-danger-bg)', borderRadius: 'var(--radius-lg)',
            background: 'var(--status-danger-bg)',
          }}>
            <div style={{ fontSize: 14, color: 'var(--status-danger-text)' }}>{error}</div>
            <button onClick={loadCourses} style={{
              marginTop: 12, padding: '7px 16px', fontSize: 13,
              background: 'var(--brand-primary)', color: 'white', border: 'none',
              borderRadius: 'var(--radius-md)', cursor: 'pointer', fontFamily: 'var(--font-sans)',
            }}>
              Erneut versuchen
            </button>
          </div>
        ) : activeTab === 'mine' ? (
          <EmptyState icon="📚" title="Noch keine Kurse belegt" sub="Stöbere in allen Kursen und starte dein erstes Training." />
        ) : filtered.length === 0 ? (
          <EmptyState icon="🔍" title="Keine Kurse gefunden" sub="Passe die Suche oder den Filter an." />
        ) : (
          filtered.map(course => (
            <CourseCard
              key={course.id}
              course={course}
              menuOpen={openMenu === course.id}
              onMenuToggle={e => { e.stopPropagation(); setOpenMenu(openMenu === course.id ? null : course.id); }}
              onMenuClose={() => setOpenMenu(null)}
              isAdmin={isAdmin}
              onEdit={() => { setOpenMenu(null); openEdit(course); }}
              onDelete={() => { setOpenMenu(null); setDeleteId(course.id); }}
            />
          ))
        )}
      </div>

      {/* Create / Edit Modal */}
      {modalMode && (
        <Modal onClose={closeModal}>
          <h2 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 20 }}>
            {modalMode === 'create' ? 'Kurs erstellen' : 'Kurs bearbeiten'}
          </h2>

          <label style={labelStyle}>Titel *</label>
          <input
            value={form.title}
            onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
            placeholder="Kurstitel"
            autoFocus
            style={inputStyle}
          />

          <label style={{ ...labelStyle, marginTop: 14 }}>Beschreibung</label>
          <textarea
            value={form.description}
            onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
            placeholder="Kurze Beschreibung des Inhalts…"
            rows={3}
            style={{ ...inputStyle, resize: 'vertical', lineHeight: 1.5 }}
          />

          <label style={{ ...labelStyle, marginTop: 14 }}>Kategorie</label>
          <select
            value={form.category}
            onChange={e => setForm(f => ({ ...f, category: e.target.value }))}
            style={inputStyle}
          >
            {CATEGORY_OPTIONS.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
          </select>

          <label style={{ ...labelStyle, marginTop: 14 }}>Farbe</label>
          <div style={{ display: 'flex', gap: 10, marginTop: 6 }}>
            {COLOR_OPTIONS.map(color => (
              <button
                key={color}
                onClick={() => setForm(f => ({ ...f, thumbnail_color: color }))}
                style={{
                  width: 36, height: 36, borderRadius: 8, background: color, border: 'none',
                  cursor: 'pointer', flexShrink: 0,
                  outline: form.thumbnail_color === color ? `3px solid ${color}` : '3px solid transparent',
                  outlineOffset: 2,
                  transform: form.thumbnail_color === color ? 'scale(1.15)' : 'scale(1)',
                  transition: 'transform 0.15s, outline 0.15s',
                }}
                title={color}
              />
            ))}
          </div>

          <div style={{ display: 'flex', gap: 10, marginTop: 24, justifyContent: 'flex-end' }}>
            <button onClick={closeModal} style={btnSecondary}>Abbrechen</button>
            <button
              onClick={handleSave}
              disabled={!form.title.trim() || saving}
              style={{ ...btnPrimary, opacity: !form.title.trim() || saving ? 0.6 : 1 }}
            >
              {saving ? 'Speichern…' : 'Speichern'}
            </button>
          </div>
        </Modal>
      )}

      {/* Delete confirmation dialog */}
      {deleteId && (
        <Modal onClose={() => !deleting && setDeleteId(null)} maxWidth={380}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 32, marginBottom: 12 }}>🗑️</div>
            <h2 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>
              Kurs löschen?
            </h2>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 24 }}>
              {courses.find(c => c.id === deleteId)?.title} wird dauerhaft gelöscht.
            </p>
            <div style={{ display: 'flex', gap: 10 }}>
              <button onClick={() => setDeleteId(null)} disabled={deleting} style={{ ...btnSecondary, flex: 1 }}>
                Abbrechen
              </button>
              <button onClick={handleDelete} disabled={deleting} style={{ ...btnDanger, flex: 1 }}>
                {deleting ? 'Löschen…' : 'Löschen'}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

// ── Course Card ───────────────────────────────────────────────────────────────

function CourseCard({ course, menuOpen, onMenuToggle, onMenuClose, isAdmin, onEdit, onDelete }) {
  const badge    = BADGE[course.category];
  const color    = course.thumbnail_color || '#008eaa';
  const abbrev   = initials(course.title);

  return (
    <div
      style={{
        background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
        borderRadius: 'var(--radius-lg)', padding: '14px 16px',
        display: 'flex', alignItems: 'center', gap: 14, transition: 'border-color 0.15s',
      }}
      onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--border-medium)'}
      onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border-light)'}
    >
      {/* Thumbnail */}
      <div style={{
        width: 80, height: 80, borderRadius: 'var(--radius-md)', flexShrink: 0,
        background: color, display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 22, fontWeight: 700, color: 'white', letterSpacing: '0.02em', userSelect: 'none',
      }}>
        {abbrev}
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
        <div style={{ display: 'flex', gap: 16, marginTop: 8 }}>
          <Stat icon="📖" value={`${course.chapter_count ?? 0} Kapitel`} />
          <Stat icon="👤" value={`${course.participant_count ?? 0} Teilnehmer`} />
          <Stat icon="⏱" value={course.duration || '0:00:00'} />
        </div>
      </div>

      {/* Three-dot menu */}
      <div style={{ position: 'relative', flexShrink: 0 }} onClick={e => e.stopPropagation()}>
        <button
          onClick={onMenuToggle}
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--text-tertiary)', fontSize: 18, padding: '4px 6px',
            borderRadius: 'var(--radius-sm)', lineHeight: 1, transition: 'background 0.1s, color 0.1s',
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
                <MenuItem onClick={onEdit}>Bearbeiten</MenuItem>
                <div style={{ height: 1, background: 'var(--border-light)', margin: '4px 0' }} />
                <MenuItem onClick={onDelete} danger>Löschen</MenuItem>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Modal wrapper ─────────────────────────────────────────────────────────────

function Modal({ children, onClose, maxWidth = 480 }) {
  return (
    <>
      <div
        style={{ position: 'fixed', inset: 0, background: 'rgba(15,28,32,0.55)', backdropFilter: 'blur(4px)', zIndex: 200 }}
        onClick={onClose}
      />
      <div style={{
        position: 'fixed', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
        background: 'var(--bg-surface)', borderRadius: 'var(--radius-xl)',
        boxShadow: 'var(--shadow-elevated)', padding: '28px 24px',
        width: `min(${maxWidth}px, calc(100vw - 32px))`,
        maxHeight: '90vh', overflowY: 'auto', zIndex: 201,
      }}
        onClick={e => e.stopPropagation()}
      >
        {children}
      </div>
    </>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function Stat({ icon, value }) {
  return (
    <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: 'var(--text-tertiary)' }}>
      <span>{icon}</span><span>{value}</span>
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

// ── Style constants ───────────────────────────────────────────────────────────

const labelStyle = {
  display: 'block', fontSize: 12, fontWeight: 600,
  color: 'var(--text-secondary)', marginBottom: 6,
};

const inputStyle = {
  width: '100%', padding: '9px 12px', fontSize: 13,
  border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)',
  background: 'var(--bg-app)', color: 'var(--text-primary)',
  fontFamily: 'var(--font-sans)', outline: 'none',
  boxSizing: 'border-box',
};

const btnPrimary = {
  padding: '9px 20px', fontSize: 13, fontWeight: 600,
  background: 'var(--brand-primary)', color: 'white',
  border: 'none', borderRadius: 'var(--radius-md)', cursor: 'pointer',
  fontFamily: 'var(--font-sans)',
};

const btnSecondary = {
  padding: '9px 16px', fontSize: 13,
  background: 'var(--bg-hover)', color: 'var(--text-secondary)',
  border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)',
  cursor: 'pointer', fontFamily: 'var(--font-sans)',
};

const btnDanger = {
  padding: '9px 16px', fontSize: 13, fontWeight: 600,
  background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)',
  border: 'none', borderRadius: 'var(--radius-md)', cursor: 'pointer',
  fontFamily: 'var(--font-sans)',
};
