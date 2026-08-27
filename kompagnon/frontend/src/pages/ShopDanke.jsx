import React from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import SeitenTitel from '../components/ui/SeitenTitel';

/**
 * Wo der Käufer nach der Zahlung landet (L-100, ORDERS_03).
 *
 * **Sie verspricht nichts, was noch nicht passiert ist.** Die Bestellung
 * steht nach diesem Schritt auf `created`, nicht auf `paid` — die
 * Zahlungsrückmeldung kommt erst mit ORDERS_04. Ein „Vielen Dank für Ihre
 * Zahlung" wäre hier eine Behauptung über etwas, das das System noch gar
 * nicht weiß.
 */
export default function ShopDanke() {
  const nav = useNavigate();
  const [suchParameter] = useSearchParams();
  const nummer = suchParameter.get('order') || '';

  return (
    <div style={{
      minHeight: '100vh', background: 'var(--bg-app)',
      fontFamily: 'var(--font-sans)', display: 'flex',
      alignItems: 'center', justifyContent: 'center', padding: 20,
    }}>
      <SeitenTitel>Bestellung eingegangen</SeitenTitel>
      <div style={{
        width: '100%', maxWidth: 520, background: 'var(--bg-surface)',
        border: '1px solid var(--border-light)', borderRadius: 12, padding: 32,
      }}>
        <div style={{ fontSize: 40, marginBottom: 12 }} aria-hidden="true">📦</div>
        <h1 style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)', margin: '0 0 10px' }}>
          Ihre Bestellung ist eingegangen
        </h1>

        {nummer && (
          <p style={{ fontSize: 14, color: 'var(--text-secondary)', margin: '0 0 14px' }}>
            Bestellnummer:{' '}
            <strong style={{ fontVariantNumeric: 'tabular-nums', color: 'var(--text-primary)' }}>
              {nummer}
            </strong>
            {' '}— bitte bei Rückfragen angeben.
          </p>
        )}

        <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.75, margin: 0 }}>
          Sobald die Zahlung bei uns bestätigt ist, erhalten Sie die
          Bestätigung per E-Mail. Das dauert in der Regel wenige Minuten.
        </p>

        <button
          onClick={() => nav('/shop')}
          style={{
            marginTop: 24, width: '100%', background: 'var(--kc-dark)',
            color: 'var(--text-inverse)', border: 'none', borderRadius: 8,
            padding: '12px 20px', fontSize: 15, fontWeight: 700,
            cursor: 'pointer', minHeight: 48,
          }}
        >
          Zurück zu den Produkten
        </button>
      </div>
    </div>
  );
}
