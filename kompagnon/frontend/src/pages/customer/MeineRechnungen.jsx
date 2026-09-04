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
 * Der Abruf `/api/invoices/my` bleibt bestehen — er hat andere Aufrufer.
 * Verschwunden ist nur die **zweite Darstellung** derselben Zeilen.
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
