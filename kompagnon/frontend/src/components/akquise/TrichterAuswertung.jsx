/**
 * Der Trichter als Zusammenfassung — welche Stufe leckt (L-192).
 *
 * Die Liste darunter zeigt einzelne Anfragen. Diese Ansicht zeigt die
 * **Stufen**: Ohne sie steht nach zwei Wochen Budget nicht fest, wo der
 * Verkehr verlorengeht.
 *
 * **Was hier bewusst nicht als Balken erscheint.** Klicks auf die Anzeige und
 * gebuchte Termine misst dieses System nicht — sie stehen bei Meta und im
 * Google-Kalender. Ein Balken der Länge null hieße „niemand hat geklickt";
 * deshalb stehen sie als benannte Leerstellen darunter, mit Grund. Dieselbe
 * Regel wie im Audit: 0 heißt „geprüft und nicht erfüllt", fehlend heißt
 * „nicht erhoben".
 */
import React from 'react';

const ZEITRAEUME = [7, 30, 90];

function Prozent({ wert }) {
  // Kein Rückfall auf „0 %": Ohne Grundgesamtheit ist nichts gemessen.
  if (wert === null || wert === undefined) return <span>–</span>;
  return <span>{wert.toLocaleString('de-DE')} %</span>;
}

function Stufe({ stufe, breiteBasis, erste }) {
  const breite = breiteBasis ? Math.max(2, (stufe.anzahl / breiteBasis) * 100) : 2;
  // Der Abbruch gegenüber der Vorstufe ist die eigentliche Auskunft: Er sagt,
  // welcher Schritt kostet — nicht, wie weit der Trichter insgesamt trägt.
  const abbruch = erste || stufe.anteil_vorstufe === null
    ? null
    : Math.round((100 - stufe.anteil_vorstufe) * 10) / 10;

  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between',
                    fontSize: 12, marginBottom: 3 }}>
        <span style={{ color: 'var(--text-secondary)' }}>{stufe.name}</span>
        <span style={{ color: 'var(--text-tertiary)' }}>
          <strong style={{ color: 'var(--text-primary)' }}>{stufe.anzahl}</strong>
          {'  '}<Prozent wert={stufe.anteil_gesamt} />
          {abbruch !== null && abbruch > 0 && (
            <span style={{ color: 'var(--error)', marginLeft: 8 }}>
              −{abbruch.toLocaleString('de-DE')} %
            </span>
          )}
        </span>
      </div>
      <div style={{ height: 8, borderRadius: 4, background: 'var(--border-light)' }}>
        <div style={{ height: 8, borderRadius: 4, width: `${breite}%`,
                      background: 'var(--brand-primary)' }} />
      </div>
    </div>
  );
}

export default function TrichterAuswertung({ daten, tage, nurAnzeige, onZeitraum, onHerkunft }) {
  if (!daten) return null;

  const basis = daten.stufen.length ? daten.stufen[0].anzahl : 0;

  return (
    <div>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
        {ZEITRAEUME.map((wert) => (
          <button
            key={wert}
            type="button"
            onClick={() => onZeitraum(wert)}
            style={{
              padding: '4px 10px', fontSize: 12, borderRadius: 6, cursor: 'pointer',
              border: '1px solid var(--border-light)',
              background: wert === tage ? 'var(--brand-primary)' : 'transparent',
              color: wert === tage ? '#fff' : 'var(--text-secondary)',
            }}
          >
            {wert} Tage
          </button>
        ))}
        <label style={{ fontSize: 12, color: 'var(--text-secondary)',
                        display: 'flex', alignItems: 'center', gap: 6 }}>
          <input type="checkbox" checked={nurAnzeige}
                 onChange={(e) => onHerkunft(e.target.checked)} />
          nur aus der Anzeige ({daten.aus_anzeige})
        </label>
      </div>

      {daten.grundgesamtheit === 0 ? (
        <p style={{ fontSize: 13, color: 'var(--text-tertiary)', margin: 0 }}>
          In diesem Zeitraum ist keine Anfrage eingegangen. Die Quoten bleiben
          leer — nicht null: Es ist nichts gemessen worden.
        </p>
      ) : (
        <>
          {daten.zu_wenig_daten && (
            <p style={{ fontSize: 12, color: 'var(--text-tertiary)',
                        margin: '0 0 10px', lineHeight: 1.5 }}>
              <strong>{daten.grundgesamtheit} Anfragen</strong> — unter{' '}
              {daten.mindestzahl} sagt eine Quote wenig. Die Zahlen stehen hier,
              die Entscheidung sollte an den absoluten Werten hängen.
            </p>
          )}
          {daten.stufen.map((stufe, i) => (
            <Stufe key={stufe.schluessel} stufe={stufe} breiteBasis={basis}
                   erste={i === 0} />
          ))}
        </>
      )}

      <div style={{ marginTop: 14, paddingTop: 10,
                    borderTop: '1px solid var(--border-light)' }}>
        <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 6,
                      color: 'var(--text-secondary)' }}>
          Nicht erhoben
        </div>
        {daten.nicht_erhoben.map((eintrag) => (
          <p key={eintrag.schluessel}
             style={{ fontSize: 12, color: 'var(--text-tertiary)',
                      margin: '0 0 6px', lineHeight: 1.5 }}>
            <strong>{eintrag.name}:</strong> {eintrag.grund}
          </p>
        ))}
      </div>
    </div>
  );
}
