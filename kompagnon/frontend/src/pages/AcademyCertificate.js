import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import API_BASE_URL from '../config';

export default function AcademyCertificate() {
  const { code } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/academy/certificates/${code}/verify`)
      .then(r => {
        if (!r.ok) throw new Error('Zertifikat nicht gefunden');
        return r.json();
      })
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [code]);

  if (loading) return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#f8fafc' }}>
      <div style={{ width: 32, height: 32, borderRadius: '50%', border: '3px solid #e2e8f0', borderTopColor: '#1e40af', animation: 'spin 0.8s linear infinite' }} />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );

  if (error) return (
    <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#f8fafc', gap: 16 }}>
      <div style={{ fontSize: 56 }}>❌</div>
      <div style={{ fontSize: 20, fontWeight: 700, color: '#dc2626' }}>Zertifikat nicht gefunden</div>
      <div style={{ fontSize: 14, color: '#64748b' }}>Der Code <strong>{code}</strong> ist ungültig oder wurde widerrufen.</div>
    </div>
  );

  return (
    <div style={{ minHeight: '100vh', background: 'linear-gradient(135deg, #f0f4ff 0%, #e8f5e9 100%)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px 16px' }}>
      <style>{`@media print { body { margin: 0; } .no-print { display: none !important; } }`}</style>

      {/* Certificate card */}
      <div style={{
        background: 'white', maxWidth: 720, width: '100%',
        borderRadius: 20, boxShadow: '0 20px 60px rgba(0,0,0,0.12)',
        overflow: 'hidden', position: 'relative',
      }}>
        {/* Top accent bar */}
        <div style={{ height: 8, background: 'linear-gradient(90deg, #1e40af 0%, #3b82f6 50%, #0891b2 100%)' }} />

        {/* Decorative corner */}
        <div style={{ position: 'absolute', top: 30, right: 30, width: 100, height: 100, borderRadius: '50%', border: '2px solid #e8eef8', opacity: 0.5 }} />
        <div style={{ position: 'absolute', top: 50, right: 50, width: 60, height: 60, borderRadius: '50%', border: '2px solid #e8eef8', opacity: 0.5 }} />

        <div style={{ padding: '48px 56px 40px', position: 'relative' }}>
          {/* Logo / Issuer */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 40 }}>
            <div style={{ width: 44, height: 44, borderRadius: 12, background: '#1e40af', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span style={{ color: 'white', fontWeight: 900, fontSize: 14 }}>K</span>
            </div>
            <div>
              <div style={{ fontSize: 16, fontWeight: 800, color: '#1e293b', letterSpacing: '0.04em' }}>KOMPAGNON</div>
              <div style={{ fontSize: 11, color: '#64748b', letterSpacing: '0.08em', textTransform: 'uppercase' }}>Akademy</div>
            </div>
          </div>

          {/* Certificate title */}
          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.14em', textTransform: 'uppercase', color: '#3b82f6', marginBottom: 12 }}>
            Zertifikat über den Abschluss
          </div>

          {/* Trophy */}
          <div style={{ fontSize: 56, marginBottom: 16 }}>🏆</div>

          {/* Recipient */}
          <div style={{ fontSize: 13, color: '#64748b', marginBottom: 6 }}>Hiermit bestätigen wir, dass</div>
          <div style={{ fontSize: 32, fontWeight: 800, color: '#1e293b', letterSpacing: '-0.02em', marginBottom: 6, lineHeight: 1.2 }}>
            {data.user_name}
          </div>
          <div style={{ fontSize: 13, color: '#64748b', marginBottom: 6 }}>den Kurs erfolgreich abgeschlossen hat:</div>

          {/* Course title */}
          <div style={{
            display: 'inline-block', background: '#eff6ff', color: '#1e40af',
            borderRadius: 10, padding: '10px 20px', fontSize: 16, fontWeight: 700, margin: '8px 0 32px',
          }}>
            {data.course_title}
          </div>

          {/* Meta row */}
          <div style={{ display: 'flex', gap: 32, borderTop: '1px solid #f1f5f9', paddingTop: 24, marginTop: 8 }}>
            <div>
              <div style={{ fontSize: 10, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 4 }}>Ausstellungsdatum</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: '#1e293b' }}>
                {data.issued_at ? new Date(data.issued_at).toLocaleDateString('de-DE', { day: '2-digit', month: 'long', year: 'numeric' }) : '—'}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 10, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 4 }}>Zertifikat-Code</div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#1e293b', fontFamily: 'monospace', letterSpacing: '0.12em' }}>
                {data.certificate_code}
              </div>
            </div>
            <div style={{ marginLeft: 'auto', display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
              <div style={{ fontSize: 10, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 4 }}>Status</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#16a34a', fontWeight: 700, fontSize: 13 }}>
                <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#16a34a' }} />
                Verifiziert
              </div>
            </div>
          </div>
        </div>

        {/* Bottom strip */}
        <div style={{ background: '#f8fafc', borderTop: '1px solid #f1f5f9', padding: '14px 56px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ fontSize: 11, color: '#94a3b8' }}>
            Verifiziert unter: <span style={{ color: '#3b82f6' }}>kompagnon.app/academy/certificate/{data.certificate_code}</span>
          </div>
          <div style={{ fontSize: 11, color: '#94a3b8' }}>KOMPAGNON Akademy © {new Date().getFullYear()}</div>
        </div>
      </div>

      {/* Print button */}
      <button
        className="no-print"
        onClick={() => window.print()}
        style={{
          marginTop: 24, padding: '11px 24px', background: '#1e40af', color: 'white',
          border: 'none', borderRadius: 10, fontSize: 13, fontWeight: 700,
          cursor: 'pointer', fontFamily: 'var(--font-sans, sans-serif)',
        }}
      >
        🖨️ Als PDF herunterladen
      </button>
    </div>
  );
}
