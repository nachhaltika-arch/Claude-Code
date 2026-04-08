import { useState } from 'react';
import toast from 'react-hot-toast';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

const CHECKLIST = [
  { category: 'Rechtliches', items: [
    { id: 'impressum', label: 'Impressum vorhanden und korrekt (Name, Adresse, USt-ID)' },
    { id: 'datenschutz', label: 'Datenschutzerklaerung DSGVO-konform', link: 'https://datenschutz-generator.de' },
    { id: 'cookie', label: 'Cookie-Banner aktiv (Borlabs / Usercentrics / CookieYes)' },
  ]},
  { category: 'Browser-Test', items: [
    { id: 'chrome_desktop', label: 'Chrome Desktop' },
    { id: 'firefox_desktop', label: 'Firefox Desktop' },
    { id: 'safari_desktop', label: 'Safari Desktop' },
    { id: 'chrome_mobile', label: 'Chrome Mobile (Android)' },
    { id: 'safari_mobile', label: 'Safari Mobile (iPhone)' },
  ]},
  { category: 'Performance', items: [
    { id: 'bilder_webp', label: 'Alle Bilder unter 200KB (WebP-Format)' },
    { id: 'pagespeed_mobile', label: 'PageSpeed Mobile > 70' },
    { id: 'pagespeed_desktop', label: 'PageSpeed Desktop > 85' },
  ]},
  { category: 'Analytics', items: [
    { id: 'google_analytics', label: 'Google Analytics eingerichtet' },
    { id: 'search_console', label: 'Google Search Console verifiziert' },
    { id: 'sitemap_xml', label: 'Sitemap.xml eingereicht' },
  ]},
];

const ALL_ITEMS = CHECKLIST.flatMap(c => c.items);

export default function QAChecklist({ projectId, initialData }) {
  const { token } = useAuth();
  const [checked, setChecked] = useState(() => {
    try { return JSON.parse(initialData?.qa_checklist_json || '{}'); } catch { return {}; }
  });

  const h = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const doneCount = ALL_ITEMS.filter(i => checked[i.id]).length;
  const totalCount = ALL_ITEMS.length;
  const allDone = doneCount === totalCount;
  const pct = totalCount > 0 ? Math.round(doneCount / totalCount * 100) : 0;

  const toggle = async (id) => {
    const next = { ...checked, [id]: !checked[id] };
    setChecked(next);
    try {
      await fetch(`${API_BASE_URL}/api/projects/${projectId}`, {
        method: 'PUT', headers: h,
        body: JSON.stringify({ qa_checklist_json: JSON.stringify(next) }),
      });
    } catch {}
  };

  const advancePhase = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/projects/${projectId}`, {
        method: 'PUT', headers: h,
        body: JSON.stringify({ current_phase: 6 }),
      });
      toast.success('Phase aktualisiert');
    } catch { toast.error('Fehler beim Aktualisieren'); }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Progress */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 16px', background: 'var(--bg-elevated)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)' }}>
        <div style={{ flex: 1, height: 6, background: 'var(--border-light)', borderRadius: 3, overflow: 'hidden' }}>
          <div style={{ width: `${pct}%`, height: '100%', background: allDone ? '#22C55E' : '#008eaa', transition: 'width 0.4s ease', borderRadius: 3 }} />
        </div>
        <span style={{ fontSize: 12, fontWeight: 600, color: allDone ? 'var(--status-success-text)' : 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
          {doneCount} von {totalCount} Punkte erledigt
        </span>
      </div>

      {/* All done banner */}
      {allDone && (
        <div style={{ padding: '10px 16px', borderRadius: 'var(--radius-md)', background: 'var(--status-success-bg)', border: '1px solid #bbf7d0', fontSize: 13, color: 'var(--status-success-text)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
          <span>QA abgeschlossen &#10003; — Projekt bereit fuer Go-Live</span>
          <button onClick={advancePhase} style={{ padding: '6px 14px', border: 'none', borderRadius: 'var(--radius-md)', background: 'var(--brand-primary)', color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>Weiter zu Go-Live</button>
        </div>
      )}

      {/* Categories */}
      {CHECKLIST.map(cat => (
        <div key={cat.category} style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
          <div style={{ padding: '10px 16px', background: 'var(--bg-app)', borderBottom: '1px solid var(--border-light)' }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{cat.category}</span>
          </div>
          {cat.items.map((item, idx) => {
            const done = !!checked[item.id];
            return (
              <div key={item.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 16px', borderBottom: idx < cat.items.length - 1 ? '1px solid var(--border-light)' : 'none', cursor: 'pointer', transition: 'background 0.1s' }}
                onClick={() => toggle(item.id)}
                onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
              >
                <div style={{ width: 18, height: 18, borderRadius: 4, border: done ? 'none' : '2px solid var(--border-light)', background: done ? '#008eaa' : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, transition: 'all 0.15s' }}>
                  {done && <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2.5 6l2.5 2.5 4.5-5"/></svg>}
                </div>
                <span style={{ fontSize: 13, color: done ? 'var(--status-success-text)' : 'var(--text-primary)', textDecoration: done ? 'line-through' : 'none', flex: 1 }}>
                  {item.label}
                </span>
                {item.link && (
                  <a href={item.link} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()} style={{ color: 'var(--brand-primary)', flexShrink: 0, display: 'flex' }} title="Link oeffnen">
                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M6 3H3.5A1.5 1.5 0 002 4.5v8A1.5 1.5 0 003.5 14h8a1.5 1.5 0 001.5-1.5V10M10 2h4v4M7 9l7-7"/></svg>
                  </a>
                )}
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
}
