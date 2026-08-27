import React, { useEffect, useState } from 'react';
import API_BASE_URL from '../config';
import SeitenTitel from '../components/ui/SeitenTitel';

/**
 * Die öffentliche Verkaufsseite für die digitalen Produkte (L-100, ORDERS_02).
 *
 * **Kein `useAuth()` hier.** Wer kaufen will, hat noch kein Konto — ein
 * Anmelde-Token würde den Zugriff verhindern, statt ihn zu schützen.
 *
 * **Sie liest `/api/products/public`, nicht eine eigene Shop-Schnittstelle.**
 * ORDERS_02 verlangte `/api/shop/products`; die gab es der Sache nach schon
 * zweimal (`/api/products/public` für die Liste, `/api/products/{slug}` für
 * das einzelne, samt 404). Ein dritter Weg auf dieselbe Tabelle wäre die
 * Bauart, die in diesem Baum schon drei Scraper, zwei Briefing-Router und
 * zwei Template-Router hervorgebracht hat.
 *
 * **Der Preis, der groß dasteht, ist der Endpreis.** Entscheidung David vom
 * 21.08.2026 (L-61): `price_brutto` ist, was abgebucht wird. Davor stand auf
 * den Paketseiten „netto" und darunter „zzgl. MwSt.", während die Kasse den
 * Bruttowert belastete — der Kunde las 1.500 € und zahlte 1.500 €, erwartete
 * aber 1.785 €. Der Nettowert steht klein daneben, für Geschäftskunden.
 */

// **Keine Hexwerte als Konstanten** — `utils/markenfarben.test.js` verbietet
// es, und der Grund steht dort: `--kc-dark` und `--kc-mid` haben im
// Dunkelmodus **andere** Werte. Eine Konstante friert den Hellwert ein, und
// `#008EAA` auf dunklem Grund ist genau das Kontrastproblem, fuer das der
// Dunkelmodus den Ton aufhellt (L-32). ORDERS_02 nannte die Hexwerte; das
// Tokensystem sticht den Prompt.
const DARK = 'var(--kc-dark)';
const MID = 'var(--kc-mid)';

const euro = (wert) =>
  Number(wert || 0).toLocaleString('de-DE', {
    style: 'currency', currency: 'EUR', minimumFractionDigits: 2,
  });

export default function Shop() {
  const [produkte, setProdukte] = useState(null);
  const [fehler, setFehler] = useState('');

  useEffect(() => {
    let abgemeldet = false;
    (async () => {
      try {
        const antwort = await fetch(`${API_BASE_URL}/api/products/public`);
        if (!antwort.ok) throw new Error(String(antwort.status));
        const daten = await antwort.json();
        // **Nur die digitalen Produkte.** Dieselbe Liste speist `Checkout.jsx`
        // und traegt die zwei Websprints — die gehoeren hier nicht her: Diese
        // Seite verspricht „zum Mitnehmen", ein Websprint ist ein Projekt.
        //
        // Unterschieden wird an `delivery_type` (`download` / `appointment`
        // gegen `none`) und nicht am Preis oder am Namen: Das ist ein Feld
        // mit einer Bedeutung, kein Merkmal, das zufaellig heute passt.
        const digital = (Array.isArray(daten) ? daten : [])
          .filter((p) => p.delivery_type && p.delivery_type !== 'none');
        if (!abgemeldet) setProdukte(digital);
      } catch {
        // Verständlich statt technisch — und **kein leerer Bildschirm**: Wer
        // hier nichts sieht, hält das Angebot für nicht vorhanden.
        if (!abgemeldet) setFehler('Die Produkte konnten gerade nicht geladen werden. Bitte laden Sie die Seite neu.');
      }
    })();
    return () => { abgemeldet = true; };
  }, []);

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-app)', fontFamily: 'var(--font-sans)' }}>
      <SeitenTitel>Produkte</SeitenTitel>

      <header style={{ background: DARK, color: 'var(--text-inverse)', padding: '48px 24px 40px' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <h1 style={{
            fontWeight: 900, fontSize: 'clamp(26px, 3.4vw, 38px)', letterSpacing: '-.022em',
            textTransform: 'uppercase', margin: 0, textWrap: 'balance',
          }}>
            Produkte
          </h1>
          <p style={{ color: 'var(--text-on-brand-muted, #9DC2C9)', fontSize: 15, maxWidth: '62ch', marginTop: 12, lineHeight: 1.65 }}>
            Der Homepage-Standard zum Mitnehmen — als Arbeitsbuch oder als
            geprüfter Befund über Ihre Website.
          </p>
        </div>
      </header>

      <main style={{ maxWidth: 1100, margin: '0 auto', padding: '32px 24px 64px' }}>
        {fehler && (
          <div role="alert" style={{
            background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)',
            borderRadius: 8, padding: '12px 14px', fontSize: 14,
          }}>
            {fehler}
          </div>
        )}

        {!fehler && produkte === null && (
          <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>Produkte werden geladen…</p>
        )}

        {/* Eine leere Liste ist etwas anderes als ein Fehler — und etwas
            anderes als „noch am Laden". Alle drei Zustände sagen, was los
            ist; ein stiller leerer Bereich wäre der vierte, den niemand
            deuten kann. */}
        {!fehler && Array.isArray(produkte) && produkte.length === 0 && (
          <p style={{ color: 'var(--text-secondary)', fontSize: 14, lineHeight: 1.7 }}>
            Zurzeit ist kein Produkt verfügbar. Workbook und Check&nbsp;PLUS sind
            angelegt, aber noch nicht freigeschaltet.
          </p>
        )}

        <div style={{
          display: 'grid', gap: 20,
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        }}>
          {(produkte || []).map((p) => (
            <article key={p.slug} style={{
              background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
              borderRadius: 12, padding: 24, display: 'flex', flexDirection: 'column', gap: 12,
            }}>
              <h2 style={{ fontSize: 19, fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
                {p.name}
              </h2>
              {p.short_desc && (
                <p style={{ fontSize: 14, color: 'var(--text-secondary)', margin: 0, lineHeight: 1.65 }}>
                  {p.short_desc}
                </p>
              )}

              <div style={{ marginTop: 4, fontVariantNumeric: 'tabular-nums' }}>
                <div style={{ fontSize: 28, fontWeight: 900, color: DARK, letterSpacing: '-.02em' }}>
                  {euro(p.price_brutto)}
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 2 }}>
                  Endpreis · enthält {Number(p.tax_rate)} % MwSt.
                  {p.price_netto ? ` · netto ${euro(p.price_netto)}` : ''}
                </div>
              </div>

              {Array.isArray(p.features) && p.features.length > 0 && (
                <ul style={{ margin: '4px 0 0', paddingLeft: 18, fontSize: 13.5,
                             color: 'var(--text-secondary)', lineHeight: 1.75 }}>
                  {p.features.map((f, i) => <li key={i}>{f}</li>)}
                </ul>
              )}

              {p.is_creditable && p.credit_months > 0 && (
                <p style={{
                  fontSize: 13, color: MID, fontWeight: 700, margin: '4px 0 0', lineHeight: 1.6,
                }}>
                  Wird innerhalb von {p.credit_months} Monaten auf einen Websprint angerechnet.
                </p>
              )}

              {/* **Deaktiviert, und der Grund steht daneben.** Ein Knopf, der
                  nichts tut, ohne zu sagen warum, liest sich als Fehler. Er
                  wird in ORDERS_03 aktiviert — und erst nach ORDERS_05, weil
                  ein Verkauf an Verbraucher ohne Widerrufsbelehrung ein
                  Rechtsverstoß ist und die Widerrufsfrist dann nicht abläuft. */}
              <div style={{ marginTop: 'auto', paddingTop: 12 }}>
                <button
                  type="button"
                  disabled
                  aria-disabled="true"
                  style={{
                    width: '100%', border: 'none', borderRadius: 8, padding: '12px 20px',
                    fontSize: 15, fontWeight: 700, minHeight: 48,
                    background: 'var(--bg-app)', color: 'var(--text-tertiary)',
                    cursor: 'not-allowed',
                  }}
                >
                  Kaufen
                </button>
                <p style={{ fontSize: 12, color: 'var(--text-tertiary)', margin: '8px 0 0', textAlign: 'center' }}>
                  In Kürze verfügbar
                </p>
              </div>
            </article>
          ))}
        </div>
      </main>
    </div>
  );
}
