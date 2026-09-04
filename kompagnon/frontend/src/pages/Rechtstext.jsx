/**
 * Die Darstellung eines Rechtstextes — AGB wie Widerrufsbelehrung (ORDERS_05).
 *
 * **Eine Hülle statt zweier Seiten.** Dieselbe Überlegung wie bei `Feld.jsx`
 * und `OeffentlicheSeite.jsx`: Zwei Kopien derselben Darstellung driften
 * auseinander, und die dritte Rechtsseite vergisst das Warnband. Der Inhalt
 * kommt aus `inhalte/rechtstexte.js`, hier steht nur, wie er aussieht.
 *
 * **Das Warnband ist der eigentliche Zweck.** Solange ein Abschnitt
 * `ausstehend` trägt, muss das unübersehbar sein — für David, der die Texte
 * einsetzt, und für jeden, der die Seite vorher zu Gesicht bekommt. Ein
 * Platzhalter, der aussieht wie ein Text, ist gefährlicher als eine leere
 * Seite: Ohne korrekte Belehrung läuft die Widerrufsfrist nicht ab.
 */
import React from 'react';
import { aufTaste } from '../utils/tastaturBedienung';
import { AUSSTEHEND, textIstVollstaendig } from '../inhalte/rechtstexte';

function Abschnitt({ eintrag }) {
  return (
    <section className="space-y-2">
      <h2 className="font-semibold kc-legal__text">{eintrag.titel}</h2>

      {eintrag.ausstehend ? (
        <div
          data-testid="abschnitt-ausstehend"
          className="kc-legal__karte border-l-4 p-3 text-sm"
          style={{ borderLeftColor: '#b45309' }}
        >
          {/* Die Markierung im Klartext, nicht als Symbol: Sie soll in einer
              Volltextsuche über den Quellbaum **und** im ausgelieferten
              Bündel auffindbar sein. */}
          <p className="font-mono font-semibold">{AUSSTEHEND}</p>
          <p className="mt-1">{eintrag.hinweis}</p>
        </div>
      ) : (
        eintrag.absaetze.map((absatz, i) => (
          // eslint-disable-next-line react/no-array-index-key
          <p key={i}>{absatz}</p>
        ))
      )}
    </section>
  );
}

export default function Rechtstext({ titel, unterzeile, abschnitte, fassung }) {
  const vollstaendig = textIstVollstaendig(abschnitte);

  return (
    <div className="min-h-screen kc-legal">
      <div className="kc-legal__band py-12">
        <div className="max-w-3xl mx-auto px-6">
          <div
            role="button"
            tabIndex={0}
            onKeyDown={aufTaste(() => window.history.back())}
            onClick={() => window.history.back()}
            className="kc-legal__band-leise text-sm cursor-pointer hover:opacity-100 mb-4 flex items-center gap-2"
          >
            ← Zurück
          </div>
          <h1 className="text-3xl font-extrabold">{titel}</h1>
          <p className="kc-legal__band-leise mt-2 text-sm">
            {unterzeile}
            {fassung ? ` · Fassung ${fassung}` : ' · noch keine gültige Fassung'}
          </p>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-6 py-12">
        {!vollstaendig && (
          <div
            data-testid="rechtstext-warnband"
            role="alert"
            className="kc-legal__karte border-l-4 p-4 mb-6"
            style={{ borderLeftColor: '#b45309' }}
          >
            <p className="font-semibold kc-legal__text">
              Dieser Text ist noch nicht rechtsverbindlich.
            </p>
            <p className="text-sm mt-1">
              Die Abschnitte unten sind eine Gliederung für die anwaltliche
              Fassung, kein geprüfter Text. Solange das hier steht, ist der
              Verkauf gesperrt — im Backend fehlt dann auch{' '}
              <code>AGB_FASSUNG</code>, und ohne sie entsteht keine Bestellung.
            </p>
          </div>
        )}

        <div className="kc-legal__karte p-6 space-y-8">
          {abschnitte.map((eintrag) => (
            <Abschnitt key={eintrag.titel} eintrag={eintrag} />
          ))}
        </div>
      </div>
    </div>
  );
}
