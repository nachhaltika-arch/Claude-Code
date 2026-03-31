import React from 'react';

const COURSES = [
  { title: 'Homepage Standard 2025', description: 'Erfahren Sie, wie eine professionelle Handwerker-Website aufgebaut sein muss.', icon: 'fa-globe', color: 'primary', lessons: 12, minutes: 45, status: 'Aktiv', badge: 'success' },
  { title: 'Google Optimierung', description: 'Lokale SEO für Handwerksbetriebe — Google Maps, My Business und Rankings.', icon: 'fa-magnifying-glass', color: 'success', lessons: 8, minutes: 30, status: 'Aktiv', badge: 'success' },
  { title: 'Social Media Basics', description: 'Instagram, Facebook und Co. effektiv nutzen — ohne großen Zeitaufwand.', icon: 'fa-share-nodes', color: 'info', lessons: 6, minutes: 20, status: 'Intern', badge: 'warning' },
  { title: 'Kundenbewertungen', description: 'Strategien für mehr Google-Bewertungen und den Umgang mit Feedback.', icon: 'fa-star', color: 'warning', lessons: 5, minutes: 15, status: 'Bald', badge: 'info' },
  { title: 'Datenschutz für KMU', description: 'DSGVO-konforme Website, Cookie-Banner und Datenschutzerklärung.', icon: 'fa-shield-halved', color: 'danger', lessons: 4, minutes: 12, status: 'Entwurf', badge: 'secondary' },
];

export default function Akademie() {
  return (
    <div>
      <h2 className="mb-4"><i className="fas fa-graduation-cap me-2"></i>Akademie</h2>
      <div className="row g-3">
        {COURSES.map((c, i) => (
          <div className="col-sm-6 col-lg-4" key={i}>
            <div className="card shadow-sm h-100">
              <div className="card-body">
                <div className={`bg-${c.color} bg-opacity-10 text-${c.color} rounded d-inline-flex align-items-center justify-content-center mb-3`} style={{ width: 40, height: 40 }}>
                  <i className={`fas ${c.icon}`}></i>
                </div>
                <h6 className="card-title">{c.title}</h6>
                <p className="card-text small text-muted" style={{ display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>{c.description}</p>
              </div>
              <div className="card-footer bg-transparent d-flex justify-content-between align-items-center">
                <small className="text-muted">{c.lessons} Lektionen · {c.minutes} Min.</small>
                <span className={`badge bg-${c.badge}`}>{c.status}</span>
              </div>
            </div>
          </div>
        ))}
        <div className="col-sm-6 col-lg-4">
          <div className="card border-2 border-dashed h-100 d-flex align-items-center justify-content-center text-muted" style={{ minHeight: 180, cursor: 'pointer' }}>
            <div className="text-center">
              <i className="fas fa-plus-circle fs-3 mb-2"></i>
              <div>Neuen Kurs erstellen</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
