import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

const FEATURES = [
  { icon: '🤖', text: 'Monatliches KI-Sichtbarkeits-Monitoring' },
  { icon: '📄', text: 'llms.txt + schema.org dauerhaft aktuell' },
  { icon: '📊', text: 'Monats-Report per E-Mail mit Score-Verlauf' },
  { icon: '🔔', text: 'Alarm bei Score-Verschlechterung' },
  { icon: '⚙️', text: 'Automatische Optimierung der KI-Signale' },
];

function scoreColor(score) {
  if (score == null) return 'var(--text-tertiary)';
  if (score >= 80) return 'var(--status-success-text)';
  if (score >= 50) return 'var(--status-warning-text)';
  return 'var(--status-danger-text)';
}

export default function GeoAddonCard({ projectId }) {
  const { token } = useAuth();
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [checkingOut, setCheckingOut] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!projectId || !token) {
      setLoading(false);
      return;
    }
    const load = async () => {
      try {
        const res = await fetch(
          `${API_BASE_URL}/api/geo-payments/${projectId}/status`,
          { headers: { Authorization: `Bearer ${token}` } },
        );
        if (res.ok) setStatus(await res.json());
      } catch (e) {
        // fail quietly — addon is optional
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [projectId, token]);

  const startCheckout = async () => {
    if (!projectId || checkingOut) return;
    setCheckingOut(true);
    setError(null);
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/geo-payments/${projectId}/create-subscription`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
        },
      );
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.detail || 'Stripe-Sitzung konnte nicht gestartet werden.');
      }
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      } else {
        throw new Error('Keine Checkout-URL erhalten.');
      }
    } catch (e) {
      setError(e.message);
      setCheckingOut(false);
    }
  };

  if (loading || !projectId) return null;

  // Backend hat keine Analyse → kein Add-on verfuegbar
  if (!status) return null;

  const subStatus = status.subscription_status;
  const price = status.upsell_price;
  const score = status.geo_score_total;
  const periodEnd = status.subscription_current_period_end;

  // ── Aktiv ───────────────────────────────────────────────────────
  if (subStatus === 'active' || subStatus === 'cancel_at_period_end') {
    const isCanceled = subStatus === 'cancel_at_period_end';
    return (
      <div
        style={{
          background: 'var(--status-success-bg)',
          border: '1px solid var(--status-success-text)',
          borderRadius: 'var(--radius-lg)',
          padding: '18px 20px',
          marginTop: 24,
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: 10,
            flexWrap: 'wrap',
            marginBottom: 8,
          }}
        >
          <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--status-success-text)' }}>
            ✓ KI-Sichtbarkeit Add-on aktiv
          </div>
          {score != null && (
            <span
              style={{
                fontSize: 12,
                fontWeight: 700,
                color: scoreColor(score),
                background: 'var(--bg-surface)',
                padding: '3px 10px',
                borderRadius: 99,
                border: `1px solid ${scoreColor(score)}`,
              }}
            >
              GEO-Score: {score}/100
            </span>
          )}
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
          {isCanceled ? (
            <>
              Ihr Abo läuft am{' '}
              <strong>{periodEnd ? new Date(periodEnd).toLocaleDateString('de-DE') : 'Periodenende'}</strong>{' '}
              aus. Bis dahin bleibt das Monitoring aktiv.
            </>
          ) : (
            <>
              Ihre Website wird monatlich auf KI-Sichtbarkeit überprüft. Den nächsten Report
              erhalten Sie automatisch per E-Mail.
            </>
          )}
        </div>
      </div>
    );
  }

  // ── Buchbar ─────────────────────────────────────────────────────
  if (!price || price <= 0) return null;

  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '2px solid var(--brand-primary)',
        borderRadius: 'var(--radius-lg)',
        padding: '20px 22px',
        marginTop: 24,
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 10,
          flexWrap: 'wrap',
          marginBottom: 6,
        }}
      >
        <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--brand-primary)' }}>
          🤖 KI-Sichtbarkeit Add-on
        </div>
        {score != null && (
          <span
            style={{
              fontSize: 11,
              fontWeight: 700,
              color: scoreColor(score),
              background: 'var(--bg-app)',
              padding: '3px 10px',
              borderRadius: 99,
              border: `1px solid ${scoreColor(score)}`,
            }}
          >
            Aktueller GEO-Score: {score}/100
          </span>
        )}
      </div>

      <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5, margin: '0 0 14px 0' }}>
        Damit ChatGPT, Claude, Perplexity & Google AI Ihre Website auch in Zukunft empfehlen,
        muss sie regelmäßig für KI-Suchmaschinen optimiert werden.
      </p>

      <div
        style={{
          background: 'var(--bg-app)',
          borderRadius: 'var(--radius-md)',
          padding: '12px 14px',
          marginBottom: 14,
        }}
      >
        {FEATURES.map((f, i) => (
          <div
            key={i}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              fontSize: 12,
              color: 'var(--text-primary)',
              padding: '5px 0',
            }}
          >
            <span style={{ fontSize: 14, flexShrink: 0 }}>{f.icon}</span>
            <span>{f.text}</span>
          </div>
        ))}
      </div>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 12,
          flexWrap: 'wrap',
          marginBottom: 12,
        }}
      >
        <div>
          <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)' }}>
            {price.toFixed(2).replace('.', ',')} €
            <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-tertiary)' }}>
              {' '}
              / Monat
            </span>
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
            Monatlich kündbar · zzgl. MwSt.
          </div>
        </div>
        <button
          onClick={startCheckout}
          disabled={checkingOut}
          style={{
            padding: '11px 20px',
            background: 'var(--brand-primary)',
            color: '#fff',
            border: 'none',
            borderRadius: 'var(--radius-md)',
            fontSize: 13,
            fontWeight: 600,
            cursor: checkingOut ? 'wait' : 'pointer',
            fontFamily: 'var(--font-sans)',
          }}
        >
          {checkingOut ? 'Wird vorbereitet…' : 'Add-on jetzt buchen →'}
        </button>
      </div>

      {error && (
        <div
          style={{
            fontSize: 12,
            color: 'var(--status-danger-text)',
            background: 'var(--status-danger-bg)',
            borderRadius: 'var(--radius-md)',
            padding: '8px 10px',
          }}
        >
          ❌ {error}
        </div>
      )}
    </div>
  );
}
