import { useEffect, useState } from 'react';
import API_BASE_URL from '../config';

/**
 * Wie viele Betriebe schon analysiert wurden — belegbar (L-65).
 *
 * **Der Befund.** Das eingebettete Widget sagte „Über 340 Handwerksbetriebe
 * analysiert", und die Zahl stand fest im Quelltext — auf **fremden Seiten**.
 * Sie kann zutreffen; nachsehen konnte es niemand, und mit jedem Tag altert
 * sie. Die Anzahl liegt in `audit_results` und laesst sich abfragen.
 *
 * Der Server rundet auf Zehner **ab**: Die Aussage behauptet damit nie mehr,
 * als geschehen ist. Kommt `0` zurueck — zu wenige Analysen oder die
 * Zaehlung faellt aus —, faellt der Satz weg. Ein Werbetext, der nichts
 * behauptet, ist besser als einer, der etwas Falsches behauptet.
 */
export default function useAnalysenZahl() {
  const [anzeige, setAnzeige] = useState(0);

  useEffect(() => {
    let abgemeldet = false;

    (async () => {
      try {
        const antwort = await fetch(`${API_BASE_URL}/api/audit/analysen/anzahl`);
        if (!antwort.ok) return;
        const daten = await antwort.json();
        if (!abgemeldet) setAnzeige(Number(daten?.anzeige) || 0);
      } catch {
        // **Absichtlich still.** Das Widget haengt auf einer fremden Seite;
        // faellt die Zahl aus, faellt der Satz weg und nicht das Widget.
      }
    })();

    return () => { abgemeldet = true; };
  }, []);

  return anzeige;
}

/**
 * Der Satz zur Zahl — oder `null`, wenn es nichts zu sagen gibt.
 *
 * Reine Funktion, damit die Regel „unter zehn wird nichts behauptet" an
 * einer Stelle steht und pruefbar ist.
 */
export function analysenSatz(anzeige) {
  const zahl = Number(anzeige) || 0;
  if (zahl < 10) return null;
  return `Über ${zahl.toLocaleString('de-DE')} Handwerksbetriebe analysiert`;
}
