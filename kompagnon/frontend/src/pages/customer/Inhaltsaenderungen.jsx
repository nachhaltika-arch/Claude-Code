import { useAuth } from '../../context/AuthContext';
import Inhaltsguthaben from '../../components/Inhaltsguthaben';
import AboZusage from '../../components/kunde/AboZusage';
import AbrufbareLeistungen from '../../components/kunde/AbrufbareLeistungen';

/**
 * „Leistungen und Guthaben" — was im Abo steckt, und was davon übrig ist.
 *
 * Hiess bis zum 06.09.2026 „Inhaltsänderungen" (L-161) und zeigte auch nur
 * die: Kontostand in Minuten, Wunsch anfordern, Verlauf. Seit L-160 Rang 3
 * steht darunter, **wofür der Betrieb monatlich zahlt** — im Wortlaut des
 * Vertrags, mit Verfallhinweis und Ausschlussliste. Der alte Name nannte
 * die Hälfte; der Menüpunkt im Entwurf `kundenkonto-neu` nennt beides.
 *
 * Der Kunde kommt hierher mit einer Absicht („die Öffnungszeiten stimmen
 * nicht mehr"), nicht zum Stöbern. Eine eigene Seite ist für so etwas der
 * kürzere Weg als ein Block, den man auf einer langen Startseite sucht.
 */
export default function Inhaltsaenderungen() {
  const { token } = useAuth();

  return (
    <div style={{ maxWidth: 860, margin: '0 auto', padding: '0 0 40px' }}>
      <h1 style={{ fontSize: 22, fontWeight: 900, letterSpacing: '-.02em',
                   color: 'var(--text-primary)', margin: '0 0 16px' }}>
        Leistungen und Guthaben
      </h1>
      <Inhaltsguthaben token={token} ohneTitel />
      {/* **Was hier im Abo steckt, im Wortlaut des Vertrags** (L-160, Rang 3).
          Der Kontostand allein sagt, wie viel übrig ist — nicht, worauf er
          sich stützt, dass die Minuten am Monatsende verfallen und dass eine
          neue Unterseite pro Jahr enthalten ist. Die Positionen kommen aus dem
          Katalog; welche hierher gehören, entscheidet ihr `ort`. */}
      <AboZusage token={token} ort="aenderungen" zeigeGrenzen />
      {/* **Was er abrufen kann** (L-160 Rang 6). Hier und nicht auf einer
          eigenen Seite: Wer nach „was steht mir zu" sucht, ist genau hier —
          und die Rücksicherung sucht man im Ernstfall nicht in einem Menü,
          sondern dort, wo die Abo-Leistungen stehen. */}
      <AbrufbareLeistungen token={token} />
    </div>
  );
}
