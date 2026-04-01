import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import academyCourses from '../data/academyCourses';

export default function Akademie() {
  const { user } = useAuth();
  const isInternal = user?.role === 'admin' || user?.role === 'auditor';
  const [viewMode, setViewMode] = useState(isInternal ? 'employee' : 'customer');

  const courses = academyCourses.filter(c => c.audience === viewMode);
  const heading = viewMode === 'employee' ? 'Interne Schulungen' : 'Ihr Projekt verstehen';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* Hero Banner */}
      <div style={{
        background: 'var(--brand-primary)', borderRadius: 'var(--radius-xl)',
        padding: '40px 24px', textAlign: 'center', color: 'white',
      }}>
        <div style={{ fontSize: 40, marginBottom: 12 }}>🎓</div>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: 'white', margin: '0 0 8px', letterSpacing: '-0.01em' }}>
          KOMPAGNON Akademie
        </h1>
        <p style={{ fontSize: 15, color: 'rgba(255,255,255,0.75)', margin: 0 }}>
          Ihr Wissenshub für digitale Sichtbarkeit
        </p>

        {/* Admin Toggle */}
        {isInternal && (
          <div style={{ marginTop: 20, display: 'flex', gap: 6, justifyContent: 'center' }}>
            {[
              { id: 'employee', label: 'Interne Schulungen' },
              { id: 'customer', label: 'Kundenansicht' },
            ].map(v => (
              <button key={v.id} onClick={() => setViewMode(v.id)} style={{
                padding: '7px 16px', borderRadius: 'var(--radius-full)', border: 'none',
                background: viewMode === v.id ? 'rgba(255,255,255,0.25)' : 'rgba(255,255,255,0.08)',
                color: 'white', fontSize: 12, fontWeight: viewMode === v.id ? 600 : 400,
                cursor: 'pointer', fontFamily: 'var(--font-sans)', transition: 'all 0.15s',
              }}>
                {v.label}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Section Heading */}
      <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)' }}>
        {heading}
      </div>

      {/* Course Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
        gap: 14,
      }}>
        {courses.map(course => (
          <Card key={course.id} padding="md" style={{
            display: 'flex', flexDirection: 'column', gap: 10,
            cursor: 'pointer', transition: 'all 0.15s',
          }}
          onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--border-medium)'; e.currentTarget.style.boxShadow = 'var(--shadow-elevated)'; }}
          onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border-light)'; e.currentTarget.style.boxShadow = 'var(--shadow-card)'; }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Badge variant={
                course.categoryColor === 'primary' ? 'info'
                : course.categoryColor === 'warning' ? 'warning'
                : course.categoryColor === 'success' ? 'success'
                : course.categoryColor === 'danger' ? 'danger'
                : 'neutral'
              }>
                {course.category}
              </Badge>
              <div style={{ display: 'flex', gap: 4 }}>
                {course.formats.includes('video') && <span title="Video" style={{ fontSize: 12 }}>🎬</span>}
                {course.formats.includes('text') && <span title="Text" style={{ fontSize: 12 }}>📄</span>}
                {course.formats.includes('checklist') && <span title="Checkliste" style={{ fontSize: 12 }}>✅</span>}
              </div>
            </div>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
              {course.title}
            </div>
            <div style={{
              fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5,
              display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden',
            }}>
              {course.description}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
