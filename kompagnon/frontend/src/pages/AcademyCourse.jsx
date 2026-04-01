import React, { useState, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import Badge from '../components/ui/Badge';
import academyCourses from '../data/academyCourses';

const BADGE_MAP = {
  primary: 'info', warning: 'warning', success: 'success', danger: 'danger', info: 'info', secondary: 'neutral',
};

const CHECKLIST_ITEMS = {
  'akquise-prozess': ['Lead-Quellen identifizieren', 'Erstkontakt vorbereiten', 'Audit als Türöffner nutzen', 'Angebot erstellen und nachfassen', 'Auftrag abschließen'],
  'audit-durchfuehren': ['Audit-Tool öffnen und URL eingeben', 'Ergebnisse interpretieren', 'Schwachstellen priorisieren', 'Kundenpräsentation vorbereiten', 'Handlungsempfehlungen ableiten'],
  '7-projektphasen': ['Phase 1: Akquisition verstehen', 'Phase 2-3: Briefing & Content planen', 'Phase 4-5: Technik & QA durchführen', 'Phase 6: Go-Live vorbereiten', 'Phase 7: Post-Launch betreuen'],
  'system-bedienen': ['Dashboard und KPIs verstehen', 'Vertriebspipeline bedienen', 'Domain-Import durchführen', 'Kundenkartei pflegen', 'Audit-Tool nutzen'],
  'kaltakquise': ['Zielgruppe definieren', 'Anschreiben-Vorlage erstellen', 'Telefonleitfaden vorbereiten', 'Follow-up Strategie planen', 'Erfolgsmessung einrichten'],
  'qualitaetsstandards': ['QA-Checkliste durchgehen', 'Cross-Browser Testing', 'Mobile Responsiveness prüfen', 'Rechtliche Inhalte verifizieren', 'Kundenübergabe dokumentieren'],
  'projekt-ablauf': ['Beauftragung und Zahlung', 'Briefing-Gespräch führen', 'Zwischenpräsentation prüfen', 'Feedback und Korrekturen', 'Go-Live und Einweisung'],
  'vorbereitung': ['Logo in Vektorformat bereitstellen', 'Texte und Inhalte liefern', 'Fotos in hoher Auflösung', 'Zugangsdaten sammeln', 'Ansprechpartner benennen'],
  'audit-verstehen': ['Gesamtscore einordnen', 'Kategorien verstehen', 'Kritische Punkte identifizieren', 'Verbesserungspotenzial erkennen', 'Nächste Schritte planen'],
  'website-pflegen': ['WordPress-Login finden', 'Texte bearbeiten', 'Bilder austauschen', 'Neue Seite erstellen', 'Backup-Routine verstehen'],
  'seo-google': ['Google Business Profil einrichten', 'Bewertungen sammeln', 'Keywords verstehen', 'Meta-Daten prüfen', 'Lokale Sichtbarkeit messen'],
};

export default function AcademyCourse() {
  const { kursId } = useParams();
  const navigate = useNavigate();

  const course = useMemo(() => academyCourses.find(c => c.id === kursId), [kursId]);
  const [checked, setChecked] = useState({});

  const formats = course?.formats || [];
  const firstTab = formats[0] || 'text';
  const [activeTab, setActiveTab] = useState(firstTab);

  const items = CHECKLIST_ITEMS[kursId] || ['Punkt 1', 'Punkt 2', 'Punkt 3', 'Punkt 4', 'Punkt 5'];
  const checkedCount = Object.values(checked).filter(Boolean).length;

  if (!course) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 20px' }}>
        <div style={{ fontSize: 48, marginBottom: 16, opacity: 0.4 }}>📚</div>
        <h2 style={{ fontSize: 18, color: 'var(--text-primary)', marginBottom: 8 }}>Kurs nicht gefunden</h2>
        <p style={{ fontSize: 13, color: 'var(--text-tertiary)', marginBottom: 20 }}>Der angeforderte Kurs existiert nicht.</p>
        <button onClick={() => navigate('/app/akademie')} style={{
          padding: '9px 20px', background: 'var(--brand-primary)', color: 'white', border: 'none',
          borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)',
        }}>← Zurück zur Akademie</button>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, maxWidth: 900, margin: '0 auto', width: '100%' }}>

      {/* Breadcrumb */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text-tertiary)' }}>
        <Link to="/app/akademie" style={{ color: 'var(--brand-primary)', textDecoration: 'none' }}>Akademie</Link>
        <span>›</span>
        <span style={{ color: 'var(--text-secondary)' }}>{course.title}</span>
      </div>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, flexWrap: 'wrap' }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6, flexWrap: 'wrap' }}>
            <h2 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>{course.title}</h2>
            <Badge variant={BADGE_MAP[course.categoryColor] || 'neutral'}>{course.category}</Badge>
          </div>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>{course.description}</p>
        </div>
      </div>

      {/* Tabs */}
      <div style={{
        display: 'flex', gap: 4, background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
        borderRadius: 'var(--radius-lg)', padding: 4,
      }}>
        {formats.includes('text') && (
          <button onClick={() => setActiveTab('text')} style={{
            flex: 1, padding: '8px 12px', borderRadius: 'var(--radius-md)', border: 'none',
            background: activeTab === 'text' ? 'var(--bg-active)' : 'transparent',
            color: activeTab === 'text' ? 'var(--brand-primary)' : 'var(--text-tertiary)',
            fontSize: 12, fontWeight: activeTab === 'text' ? 500 : 400, cursor: 'pointer',
            fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
          }}>📄 Anleitung</button>
        )}
        {formats.includes('video') && (
          <button onClick={() => setActiveTab('video')} style={{
            flex: 1, padding: '8px 12px', borderRadius: 'var(--radius-md)', border: 'none',
            background: activeTab === 'video' ? 'var(--bg-active)' : 'transparent',
            color: activeTab === 'video' ? 'var(--brand-primary)' : 'var(--text-tertiary)',
            fontSize: 12, fontWeight: activeTab === 'video' ? 500 : 400, cursor: 'pointer',
            fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
          }}>🎬 Video</button>
        )}
        {formats.includes('checklist') && (
          <button onClick={() => setActiveTab('checklist')} style={{
            flex: 1, padding: '8px 12px', borderRadius: 'var(--radius-md)', border: 'none',
            background: activeTab === 'checklist' ? 'var(--bg-active)' : 'transparent',
            color: activeTab === 'checklist' ? 'var(--brand-primary)' : 'var(--text-tertiary)',
            fontSize: 12, fontWeight: activeTab === 'checklist' ? 500 : 400, cursor: 'pointer',
            fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
          }}>✅ Checkliste</button>
        )}
      </div>

      {/* Tab Content */}
      <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>

        {/* Anleitung */}
        {activeTab === 'text' && (
          <div style={{ padding: '48px 24px', textAlign: 'center', maxWidth: 600, margin: '0 auto' }}>
            <div style={{ fontSize: 48, marginBottom: 16, opacity: 0.3 }}>🔨</div>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>Dieser Inhalt wird gerade erstellt</h3>
            <p style={{ fontSize: 13, color: 'var(--text-tertiary)', lineHeight: 1.6 }}>
              Die Anleitung für „{course.title}" wird aktuell vorbereitet und in Kürze hier verfügbar sein.
            </p>
          </div>
        )}

        {/* Video */}
        {activeTab === 'video' && (
          <div style={{ padding: 16 }}>
            <div style={{
              position: 'relative', paddingBottom: '56.25%', height: 0,
              background: 'var(--bg-app)', borderRadius: 'var(--radius-md)', overflow: 'hidden',
            }}>
              <div style={{
                position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
                alignItems: 'center', justifyContent: 'center', gap: 12,
              }}>
                <div style={{ fontSize: 48, opacity: 0.3 }}>🎬</div>
                <div style={{ fontSize: 14, color: 'var(--text-tertiary)' }}>Video folgt in Kürze</div>
              </div>
            </div>
          </div>
        )}

        {/* Checkliste */}
        {activeTab === 'checklist' && (
          <div style={{ padding: 16 }}>
            {/* Progress */}
            <div style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>{checkedCount} von {items.length} erledigt</span>
                <span style={{ fontSize: 12, color: checkedCount === items.length ? 'var(--status-success-text)' : 'var(--text-tertiary)' }}>
                  {Math.round((checkedCount / items.length) * 100)}%
                </span>
              </div>
              <div style={{ height: 6, background: 'var(--border-light)', borderRadius: 3, overflow: 'hidden' }}>
                <div style={{
                  width: `${(checkedCount / items.length) * 100}%`, height: '100%',
                  background: checkedCount === items.length ? 'var(--status-success-text)' : 'var(--brand-primary)',
                  borderRadius: 3, transition: 'width 0.3s ease',
                }} />
              </div>
            </div>

            {/* Items */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {items.map((item, i) => {
                const isDone = checked[i];
                return (
                  <label key={i} style={{
                    display: 'flex', alignItems: 'center', gap: 12, padding: '10px 12px',
                    borderRadius: 'var(--radius-md)', cursor: 'pointer',
                    background: isDone ? 'var(--status-success-bg)' : 'transparent',
                    transition: 'background 0.15s',
                  }}>
                    <input type="checkbox" checked={!!isDone}
                      onChange={() => setChecked(prev => ({ ...prev, [i]: !prev[i] }))}
                      style={{ width: 18, height: 18, accentColor: 'var(--brand-primary)', cursor: 'pointer', flexShrink: 0 }} />
                    <span style={{
                      fontSize: 13, color: isDone ? 'var(--text-tertiary)' : 'var(--text-primary)',
                      textDecoration: isDone ? 'line-through' : 'none', transition: 'all 0.15s',
                    }}>
                      {item}
                    </span>
                  </label>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Back button */}
      <div>
        <button onClick={() => navigate('/app/akademie')} style={{
          padding: '9px 20px', background: 'transparent', color: 'var(--brand-primary)',
          border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
          fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)',
        }}>
          ← Zurück zur Übersicht
        </button>
      </div>
    </div>
  );
}
