/**
 * Allgemeine Geschäftsbedingungen (ORDERS_05).
 *
 * Der Inhalt steht in `inhalte/rechtstexte.js` — dort wird gepflegt, hier
 * nicht. Siehe `pages/Rechtstext.jsx` für die Darstellung.
 */
import React from 'react';
import Rechtstext from './Rechtstext';
import { AGB as ABSCHNITTE, FASSUNG } from '../inhalte/rechtstexte';

export default function AGB() {
  return (
    <Rechtstext
      titel="Allgemeine Geschäftsbedingungen"
      unterzeile="Für den Kauf digitaler Produkte"
      abschnitte={ABSCHNITTE}
      fassung={FASSUNG}
    />
  );
}
