/**
 * Punktfarbe, Punktbeschriftung und der Balken der GEO-Ansicht (L-25).
 *
 * Am 2026-08-31 aus `GeoOptimizerStep.jsx` herausgeloest — **zuerst**, weil
 * Ansicht und beide ausgezogenen Reiter sie brauchen.
 */
export const SCORE_COLOR = (score) => {
  if (score >= 75) return '#27ae60';
  if (score >= 50) return '#f39c12';
  return '#e74c3c';
};

export const SCORE_LABEL = (score) => {
  if (score >= 75) return 'Gut';
  if (score >= 50) return 'Ausbaufaehig';
  return 'Handlungsbedarf';
};

export const ScoreBar = ({ label, score }) => (
  <div style={{ marginBottom: 10 }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontSize: 13 }}>
      <span>{label}</span>
      <span style={{ fontWeight: 600, color: SCORE_COLOR(score) }}>{score}/100</span>
    </div>
    <div style={{ height: 8, background: '#E5E7EB', borderRadius: 4, overflow: 'hidden' }}>
      <div
        style={{
          height: '100%',
          width: `${Math.min(score, 100)}%`,
          background: SCORE_COLOR(score),
          borderRadius: 4,
          transition: 'width 0.6s ease',
        }}
      />
    </div>
  </div>
);

