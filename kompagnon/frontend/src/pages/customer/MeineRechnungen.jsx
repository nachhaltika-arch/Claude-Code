import { useAuth } from '../../context/AuthContext';
import Zahlungen from '../../components/Zahlungen';

/**
 * „Rechnungen & Zahlung" — Verträge, Zahlungsart und Belege an einer Stelle.
 *
 * **Diese Seite hieß bis zum 04.09.2026 „Meine Rechnungen" und listete nur
 * Belege** — aus `GET /api/invoices/my`, mit eigenem Abruf und eigener
 * Darstellung. Gleichzeitig zeigte der Block „Zahlungen" auf der Startseite
 * dieselben Rechnungen noch einmal, unter der Überschrift „Ihre Rechnungen",
 * aus `GET /api/portal/zahlungen`. Zwei Überschriften, zwei Abrufe, dieselben
 * Zeilen — und ein Kunde, der sich fragt, welche der beiden Listen die
 * vollständige ist.
 *
 * **Aufgelöst zugunsten der einen Komponente, die mehr kann.** `Zahlungen`
 * zeigt außerdem, was monatlich läuft und womit gezahlt wird — genau die zwei
 * Fragen, die neben „was habe ich bezahlt" stehen. Der Kunde denkt sie als
 * eines; deshalb stehen sie jetzt auch auf einer Seite.
 *
 * **Der Satz „`/api/invoices/my` bleibt bestehen — er hat andere Aufrufer"
 * stand hier bis zum 07.09.2026 und war falsch.** Er war eine Annahme, keine
 * Messung: Mit dem Umbau am 04.09. verlor die Route ihren letzten Aufrufer,
 * und `tools/unaufgerufene-routen.py` führt sie seither unter „ruft niemand".
 * Sie tut dasselbe wie die Rechnungshälfte von `GET /api/portal/zahlungen` —
 * nur mit `SELECT *` und ohne Grenze, während der Portalweg benannte Spalten
 * mit `LIMIT 24` liest. Zwei Wege zu denselben Zeilen, schon auseinander-
 * gelaufen.
 *
 * Ob die Route weg soll, ist eine Entscheidung über eine öffentliche
 * Schnittstelle und steht als solche im Lagebild unter L-105. Verschwunden
 * ist hier nur die **zweite Darstellung** derselben Zeilen.
 */
export default function MeineRechnungen() {
  const { token } = useAuth();

  return (
    <div style={{ maxWidth: 860, margin: '0 auto', padding: '0 0 40px' }}>
      <h1 style={{ fontSize: 22, fontWeight: 900, letterSpacing: '-.02em',
                   color: 'var(--text-primary)', margin: '0 0 16px' }}>
        Rechnungen und Zahlung
      </h1>
      <Zahlungen token={token} ohneTitel />
    </div>
  );
}
