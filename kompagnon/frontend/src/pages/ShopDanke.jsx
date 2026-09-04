import React, { useEffect, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import SeitenTitel from '../components/ui/SeitenTitel';
import API_BASE_URL from '../config';
import { aussage, weiterFragen } from '../utils/bestellstatus';

/**
 * Wo der Käufer nach der Zahlung landet (L-100, ORDERS_03).
 *
 * **Sie verspricht nichts, was noch nicht passiert ist** — und seit dem
 * 31.08.2026 weiß sie auch, was passiert ist. Bis dahin stand hier in jedem
 * Fall derselbe Satz: „Sobald die Zahlung bei uns bestätigt ist …". Er stammt
 * aus ORDERS_03, als es die Zahlungsrückmeldung noch nicht gab; seit
 * ORDERS_04 gibt es sie, und `GET /api/shop/orders/{nr}/status` beantwortet
 * genau diese Frage. **Gerufen hat ihn niemand** (L-105).
 *
 * **Kein Downloadlink hier.** Der Endpunkt gibt bewusst nur Nummer, Status
 * und Produktschlüssel heraus — die Bestellnummer steht im Browserverlauf und
 * in E-Mails, ein Abruf daraus wäre eine Datenschutzlücke in einer
 * öffentlichen Route. Datei und Rechnung kommen über die E-Mail, so wie
 * ORDERS_06 und ORDERS_07 sie versenden.
 */

/** Abstand zwischen zwei Nachfragen. */
const TAKT_MS = 3000;

/** Nach zwei Minuten wird nicht weiter gefragt — siehe `weiterFragen`. */
const HOECHSTENS = 40;

export default function ShopDanke() {
  const nav = useNavigate();
  const [suchParameter] = useSearchParams();
  const nummer = suchParameter.get('order') || '';

  const [status, setStatus] = useState(null);
  const [abgelaufen, setAbgelaufen] = useState(false);
  const versuche = useRef(0);

  useEffect(() => {
    if (!nummer) return undefined;
    let gestoppt = false;
    let uhr = null;

    const fragen = async () => {
      if (gestoppt) return;
      versuche.current += 1;
      try {
        const antwort = await fetch(
          `${API_BASE_URL}/api/shop/orders/${encodeURIComponent(nummer)}/status`,
        );
        // **Ein 404 beendet die Schleife nicht.** Die Bestellung entsteht in
        // demselben Augenblick, in dem der Käufer hier landet; eine Sekunde
        // Vorsprung des Browsers ist kein Fehler.
        if (antwort.ok) {
          const daten = await antwort.json();
          if (!gestoppt) setStatus(daten.status || null);
          if (!weiterFragen(daten.status, versuche.current, HOECHSTENS)) {
            if (!gestoppt && versuche.current >= HOECHSTENS) setAbgelaufen(true);
            return;
          }
        }
      } catch (_) {
        // Ein Netzfehler ist kein Zustand der Bestellung. Weiterfragen.
      }
      if (gestoppt) return;
      if (versuche.current >= HOECHSTENS) { setAbgelaufen(true); return; }
      uhr = setTimeout(fragen, TAKT_MS);
    };

    fragen();
    return () => { gestoppt = true; if (uhr) clearTimeout(uhr); };
  }, [nummer]);

  const { titel, text, art } = aussage(status, abgelaufen);
  const zeichen = art === 'gut' ? '✅' : (art === 'fehler' ? '⚠️' : '📦');
  const randfarbe = art === 'fehler'
    ? 'var(--status-danger-text)'
    : 'var(--border-light)';

  return (
    <div style={{
      minHeight: '100vh', background: 'var(--bg-app)',
      fontFamily: 'var(--font-sans)', display: 'flex',
      alignItems: 'center', justifyContent: 'center', padding: 20,
    }}>
      <SeitenTitel>{titel}</SeitenTitel>
      <div style={{
        width: '100%', maxWidth: 520, background: 'var(--bg-surface)',
        border: `1px solid ${randfarbe}`, borderRadius: 12, padding: 32,
      }}>
        <div style={{ fontSize: 40, marginBottom: 12 }} aria-hidden="true">{zeichen}</div>
        <h1 style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)', margin: '0 0 10px' }}>
          {titel}
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

        {/* **Der Stand wird angesagt, nicht nur gezeigt.** Wer die Seite mit
            einem Screenreader liest, bekommt die Änderung sonst nicht mit —
            sie passiert ohne sein Zutun. */}
        <p
          aria-live="polite"
          style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.75, margin: 0 }}
        >
          {text}
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
