/**
 * Der Trichter als Zusammenfassung — welche Stufe leckt (L-192).
 *
 * Die Liste darunter zeigt einzelne Anfragen. Diese Ansicht zeigt die
 * **Stufen**: Ohne sie steht nach zwei Wochen Budget nicht fest, wo der
 * Verkehr verlorengeht.
 *
 * **Drei Klassen, und die Trennung ist der eigentliche Inhalt** (E17 des
 * Vertriebsplans: Kennzeichnung GEMESSEN / ERFAHREN / ANGENOMMEN, überall):
 *
 *   gemessen       aus widget_requests, Zeitstempel je Zeile
 *   angenommen     aus dem Vertriebsplan, auf die gemessene Basis gerechnet
 *   nicht erhoben  Anzeigenklicks (Meta) und Termine (Google-Kalender)
 *
 * Neben sechs gemessenen Balken sieht eine angenommene Zahl aus wie eine
 * gemessene. Deshalb tragen die Annahmen einen blassen Balken, das Wort
 * „angenommen" und ihre Quelle — und die nicht erhobenen Stufen erscheinen
 * gar nicht als Balken: Ein Balken der Länge null hieße „niemand hat
 * gebucht", und das ist eine Aussage, die hier niemand treffen kann.
 *
 * Die Form — Beschriftung links, Balken rechts mit der Zahl darin — stammt
 * aus dem Vertriebsplan-Artefakt vom 15.09.2026.
 */
import React from 'react';

const ZEITRAEUME = [7, 30, 90];

function Prozent({ wert }) {
  // Kein Rückfall auf „0 %": Ohne Grundgesamtheit ist nichts gemessen.
  if (wert === null || wert === undefined) return <span>–</span>;
  return <span>{wert.toLocaleString('de-DE')} %</span>;
}

const zeile = { display: 'grid', gridTemplateColumns: 'minmax(110px,170px) 1fr',
                gap: 12, alignItems: 'center', marginBottom: 8 };
const beschriftung = { fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)' };
// Mindestens 12 px — L-17. Der Zusatz ist die Stelle, an der man aus
// Platzgründen am ehesten darunter rutscht, und er trägt die Herkunft der
// Zahl: gerade das muss lesbar sein.
const zusatz = { display: 'block', fontWeight: 400, fontSize: 12,
                 color: 'var(--text-tertiary)', lineHeight: 1.4 };

function Balken({ breite, blass, kinder }) {
  return (
    <div style={{ height: 26, borderRadius: 4, display: 'flex', alignItems: 'center',
                  paddingInline: 9, fontSize: 12, fontWeight: 600, whiteSpace: 'nowrap',
                  minWidth: 'fit-content', width: `${Math.max(breite, 3)}%`,
                  background: blass ? 'var(--border-light)' : 'var(--brand-primary)',
                  color: blass ? 'var(--text-secondary)' : '#fff' }}>
      {kinder}
    </div>
  );
}

function GemesseneStufe({ stufe, basis, erste }) {
  // Der Abbruch gegenüber der Vorstufe ist die eigentliche Auskunft: Er sagt,
  // welcher Schritt kostet — nicht, wie weit der Trichter insgesamt trägt.
  const abbruch = erste || stufe.anteil_vorstufe === null
    ? null
    : Math.round((100 - stufe.anteil_vorstufe) * 10) / 10;
  const spanne = stufe.erwartet_von !== null && stufe.erwartet_von !== undefined;

  return (
    <div style={zeile}>
      <div style={beschriftung}>
        {stufe.name}
        {spanne && (
          <span style={zusatz}>
            Plan: {stufe.erwartet_von}–{stufe.erwartet_bis} % der Vorstufe
          </span>
        )}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <Balken breite={basis ? (stufe.anzahl / basis) * 100 : 3}
                kinder={stufe.anzahl} />
        <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
          <Prozent wert={stufe.anteil_gesamt} />
          {abbruch !== null && abbruch > 0 && (
            <span style={{ color: 'var(--error)', marginLeft: 8 }}>
              −{abbruch.toLocaleString('de-DE')} %
            </span>
          )}
          {stufe.unter_erwartung && (
            <strong style={{ color: 'var(--error)', marginLeft: 8 }}>
              unter Plan
            </strong>
          )}
        </span>
      </div>
    </div>
  );
}

function AngenommeneStufe({ eintrag, basis }) {
  return (
    <div style={zeile}>
      <div style={beschriftung}>
        {eintrag.name}
        <span style={zusatz}>{eintrag.hinweis}</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <Balken blass breite={basis && eintrag.erwartet ? (eintrag.erwartet / basis) * 100 : 3}
                kinder={eintrag.erwartet === null ? '–' : eintrag.erwartet.toLocaleString('de-DE')} />
        <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>angenommen</span>
      </div>
    </div>
  );
}

function Gruppe({ titel, hinweis, children }) {
  return (
    <div style={{ marginTop: 14 }}>
      <div style={{ fontSize: 12, fontWeight: 700, letterSpacing: '.08em',
                    textTransform: 'uppercase', color: 'var(--text-tertiary)',
                    marginBottom: 8 }}>
        {titel}
      </div>
      {hinweis && (
        <p style={{ fontSize: 12, color: 'var(--text-tertiary)', margin: '0 0 10px',
                    lineHeight: 1.5 }}>{hinweis}</p>
      )}
      {children}
    </div>
  );
}

export default function TrichterAuswertung({ daten, tage, nurAnzeige, onZeitraum, onHerkunft }) {
  if (!daten) return null;

  const basis = daten.stufen.length ? daten.stufen[0].anzahl : 0;
  const quelle = daten.angenommen && daten.angenommen.length
    ? daten.angenommen[0].herkunft : '';

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
        <Gruppe titel="Gemessen">
          {daten.zu_wenig_daten && (
            <p style={{ fontSize: 12, color: 'var(--text-tertiary)',
                        margin: '0 0 10px', lineHeight: 1.5 }}>
              <strong>{daten.grundgesamtheit} Anfragen</strong> — unter{' '}
              {daten.mindestzahl} sagt eine Quote wenig. Die Zahlen stehen hier,
              die Entscheidung sollte an den absoluten Werten hängen.
            </p>
          )}
          {daten.stufen.map((stufe, i) => (
            <GemesseneStufe key={stufe.schluessel} stufe={stufe} basis={basis}
                            erste={i === 0} />
          ))}
        </Gruppe>
      )}

      {daten.angenommen && daten.angenommen.length > 0 && (
        <Gruppe
          titel="Angenommen"
          hinweis={`Keine dieser Zahlen ist erhoben. Sie zeigen, was der ${quelle}
                    bei den oben gemessenen Werten erwarten ließe — nicht, was
                    geschehen ist.`}
        >
          {daten.angenommen.map((eintrag) => (
            <AngenommeneStufe key={eintrag.schluessel} eintrag={eintrag} basis={basis} />
          ))}
        </Gruppe>
      )}

      <Gruppe titel="Nicht erhoben">
        {daten.nicht_erhoben.map((eintrag) => (
          <p key={eintrag.schluessel}
             style={{ fontSize: 12, color: 'var(--text-tertiary)',
                      margin: '0 0 6px', lineHeight: 1.5 }}>
            <strong>{eintrag.name}:</strong> {eintrag.grund}
          </p>
        ))}
      </Gruppe>
    </div>
  );
}
