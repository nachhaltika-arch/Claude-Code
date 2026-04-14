import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import API_BASE_URL from '../config';

/**
 * Oeffentliche Bestaetigungsseite fuer den tokenisierten Content-Approval-Link
 * aus der Admin-E-Mail. Ruft einmal GET /api/projects/approve-content/{token}
 * auf und zeigt je nach Response einen Erfolgs- oder Fehler-Screen.
 *
 * Token ist single-use — ein zweiter Aufruf mit demselben Token liefert 404
 * ("ungueltig oder bereits verwendet") und zeigt einen klaren Hinweis.
 */
export default function ApproveContent() {
  const { token } = useParams();
  const navigate = useNavigate();

  const [state, setState] = useState('loading'); // 'loading' | 'ok' | 'error'
  const [companyName, setCompanyName] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    if (!token) {
      setState('error');
      setErrorMsg('Kein Token in der URL gefunden.');
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(
          `${API_BASE_URL}/api/projects/approve-content/${encodeURIComponent(token)}`,
          { method: 'GET' },
        );
        const data = await res.json().catch(() => ({}));
        if (cancelled) return;
        if (res.ok && data?.approved) {
          setCompanyName(data.company_name || '');
          setState('ok');
        } else {
          setErrorMsg(data?.detail || 'Dieser Link ist ungültig oder wurde bereits verwendet.');
          setState('error');
        }
      } catch (e) {
        if (cancelled) return;
        setErrorMsg('Verbindungsfehler — bitte später erneut versuchen.');
        setState('error');
      }
    })();
    return () => { cancelled = true; };
  }, [token]);

  const pageStyle = {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    background: 'linear-gradient(180deg, #F6F8FA 0%, #EDF1F5 100%)',
    fontFamily: 'var(--font-sans, system-ui)',
  };

  const cardStyle = {
    maxWidth: 520,
    width: '100%',
    background: '#fff',
    borderRadius: 16,
    padding: '40px 32px',
    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
    textAlign: 'center',
  };

  if (state === 'loading') {
    return (
      <div style={pageStyle}>
        <div style={cardStyle}>
          <div style={{ fontSize: 36, marginBottom: 16 }}>⏳</div>
          <div style={{ fontSize: 18, fontWeight: 600, color: '#1A2C32', marginBottom: 6 }}>
            Freigabe wird verarbeitet …
          </div>
          <div style={{ fontSize: 13, color: '#64748B' }}>
            Einen kleinen Moment bitte.
          </div>
        </div>
      </div>
    );
  }

  if (state === 'error') {
    return (
      <div style={pageStyle}>
        <div style={cardStyle}>
          <div style={{ fontSize: 44, marginBottom: 16 }}>⚠️</div>
          <div style={{ fontSize: 20, fontWeight: 700, color: '#B02A2A', marginBottom: 10 }}>
            Freigabe nicht möglich
          </div>
          <div style={{ fontSize: 14, color: '#1A2C32', lineHeight: 1.6, marginBottom: 18 }}>
            {errorMsg || 'Dieser Link ist leider ungültig oder abgelaufen.'}
          </div>
          <div style={{ fontSize: 12, color: '#64748B', lineHeight: 1.6 }}>
            Bitte wenden Sie sich an{' '}
            <a
              href="mailto:info@kompagnon.de"
              style={{ color: '#008EAA', textDecoration: 'none', fontWeight: 600 }}
            >
              info@kompagnon.de
            </a>{' '}
            wenn Sie Hilfe brauchen.
          </div>
        </div>
      </div>
    );
  }

  // state === 'ok'
  return (
    <div style={pageStyle}>
      <div style={cardStyle}>
        <div style={{
          fontSize: 52,
          marginBottom: 18,
          color: '#1D9E75',
          lineHeight: 1,
        }}>✓</div>
        <div style={{ fontSize: 22, fontWeight: 700, color: '#0F5C43', marginBottom: 10 }}>
          Vielen Dank!
        </div>
        <div style={{ fontSize: 15, color: '#1A2C32', lineHeight: 1.6, marginBottom: 8 }}>
          Ihre Freigabe wurde registriert
          {companyName ? <> für <strong>{companyName}</strong></> : ''}.
        </div>
        <div style={{ fontSize: 14, color: '#27500A', lineHeight: 1.6, marginBottom: 28 }}>
          Ihr Design wird jetzt erstellt. Wir melden uns bei Ihnen, sobald die
          ersten Entwürfe zum Anschauen bereit sind.
        </div>
        <button
          onClick={() => navigate('/portal/login')}
          style={{
            padding: '12px 28px',
            borderRadius: 10,
            border: 'none',
            background: '#008EAA',
            color: '#fff',
            fontSize: 14,
            fontWeight: 700,
            cursor: 'pointer',
            fontFamily: 'inherit',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.12)',
          }}
        >
          Zum Kundenportal
        </button>
        <div style={{ fontSize: 11, color: '#94A3B8', marginTop: 20 }}>
          Sie können dieses Fenster jetzt schließen.
        </div>
      </div>
    </div>
  );
}
