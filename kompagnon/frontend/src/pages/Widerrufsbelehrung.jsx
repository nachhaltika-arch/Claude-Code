/**
 * Widerrufsbelehrung (ORDERS_05).
 *
 * **Ohne korrekte Belehrung beginnt die Widerrufsfrist nicht zu laufen** —
 * sie wird zwölf Monate und vierzehn Tage lang. Deshalb steht hier eine
 * Gliederung und kein selbstgeschriebener Text; das amtliche Muster (Anlage 1
 * zu Art. 246a § 1 Abs. 2 EGBGB) füllt die Kanzlei aus.
 */
import React from 'react';
import Rechtstext from './Rechtstext';
import { WIDERRUF as ABSCHNITTE, FASSUNG } from '../inhalte/rechtstexte';

export default function Widerrufsbelehrung() {
  return (
    <Rechtstext
      titel="Widerrufsbelehrung"
      unterzeile="Für Verbraucher beim Kauf digitaler Produkte"
      abschnitte={ABSCHNITTE}
      fassung={FASSUNG}
    />
  );
}
