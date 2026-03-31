import React from 'react';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';

const COURSES = [
  {
    title: 'Homepage Standard 2025',
    description: 'Erfahren Sie, wie eine professionelle Handwerker-Website aufgebaut sein muss — inkl. rechtlicher Anforderungen, SEO und Performance.',
    icon: '🌐', iconBg: '#e0f4f8', iconColor: '#008eaa',
    lessons: 12, minutes: 45,
    status: 'Aktiv', variant: 'success',
  },
  {
    title: 'Google Optimierung',
    description: 'Lokale Suchmaschinenoptimierung für Handwerksbetriebe — Google Maps, My Business und organische Rankings.',
    icon: '🔍', iconBg: '#eaf5ee', iconColor: '#1a7a3a',
    lessons: 8, minutes: 30,
    status: 'Aktiv', variant: 'success',
  },
  {
    title: 'Social Media Basics',
    description: 'Praxistipps für Handwerker: Instagram, Facebook und Co. effektiv nutzen — ohne großen Zeitaufwand.',
    icon: '📱', iconBg: '#f3e8ff', iconColor: '#7c3aed',
    lessons: 6, minutes: 20,
    status: 'Intern', variant: 'warning',
  },
  {
    title: 'Kundenbewertungen',
    description: 'Strategien für mehr Google-Bewertungen und den professionellen Umgang mit negativem Feedback.',
    icon: '⭐', iconBg: '#fff8e6', iconColor: '#a06800',
    lessons: 5, minutes: 15,
    status: 'Bald', variant: 'info',
  },
  {
    title: 'Datenschutz für KMU',
    description: 'DSGVO-konforme Website, Cookie-Banner, Datenschutzerklärung und Impressum richtig umsetzen.',
    icon: '🔒', iconBg: '#fef0f0', iconColor: '#b02020',
    lessons: 4, minutes: 12,
    status: 'Entwurf', variant: 'neutral',
  },
  {
    title: 'Vertrieb & Akquise',
    description: 'Effektive Methoden zur Neukundengewinnung — von der Erstansprache bis zum Vertragsabschluss.',
    icon: '🤝', iconBg: '#e0f4f8', iconColor: '#006880',
    lessons: 10, minutes: 35,
    status: 'Entwurf', variant: 'neutral',
  },
];

export default function Akademie() {
  return (
    <div style={{ animation: 'fadeIn 0.3s ease' }}>
      {/* Course Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
        gap: 14,
      }}>
        {COURSES.map((course, i) => (
          <Card key={i} padding="md" style={{ display: 'flex', flexDirection: 'column', gap: 10, cursor: 'pointer', transition: 'all 0.15s' }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--border-medium)'; e.currentTarget.style.boxShadow = 'var(--shadow-elevated)'; }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border-light)'; e.currentTarget.style.boxShadow = 'var(--shadow-card)'; }}
          >
            {/* Icon */}
            <div style={{
              width: 36, height: 36, borderRadius: 'var(--radius-md)',
              background: course.iconBg, display: 'flex', alignItems: 'center',
              justifyContent: 'center', fontSize: 18,
            }}>
              {course.icon}
            </div>

            {/* Title */}
            <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>
              {course.title}
            </div>

            {/* Description */}
            <div style={{
              fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.5,
              display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}>
              {course.description}
            </div>

            {/* Footer */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 'auto', paddingTop: 6 }}>
              <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                {course.lessons} Lektionen · {course.minutes} Min.
              </span>
              <Badge variant={course.variant}>{course.status}</Badge>
            </div>
          </Card>
        ))}

        {/* Add course placeholder */}
        <div style={{
          border: '1.5px dashed var(--border-medium)',
          borderRadius: 'var(--radius-lg)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          padding: 24, minHeight: 160, cursor: 'pointer',
          color: 'var(--text-tertiary)', fontSize: 13,
          transition: 'all 0.15s',
        }}
        onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--brand-primary)'; e.currentTarget.style.color = 'var(--brand-primary)'; }}
        onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border-medium)'; e.currentTarget.style.color = 'var(--text-tertiary)'; }}
        >
          + Neuen Kurs erstellen
        </div>
      </div>
    </div>
  );
}
