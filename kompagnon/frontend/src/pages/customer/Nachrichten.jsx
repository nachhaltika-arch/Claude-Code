import { useAuth } from '../../context/AuthContext';
import KundenChat from '../../components/kunde/KundenChat';
import SeitenTitel from '../../components/ui/SeitenTitel';

/**
 * „Nachrichten" — der Verlauf mit dem Betreuer, an einem Ort.
 *
 * **Der Befund (06.09.2026, Entwurf `kundenkonto-neu`).** Der Verlauf stand an
 * **zwei** Stellen: auf der Übersicht und unter „Meine Daten".
 *
 * Auf der Übersicht war er falsch, weil diese Seite zwei Fragen beantwortet
 * und sonst keine — *Wo stehen wir?* und *Was liegt bei mir?* Ein
 * Nachrichtenverlauf beantwortet keine davon; er macht die Seite lang, und
 * genau so steht es im Entwurf.
 *
 * Unter „Meine Daten" war er sachlich falsch: Das ist die Seite für
 * Stammdaten, kein Postfach.
 *
 * **Zwei Orte für denselben Verlauf sind zwei, an denen jemand nachsieht — und
 * einer, an dem er das Ungelesene übersieht.**
 *
 * Die Seite selbst ist dünn, und das ist richtig: `KundenChat` bringt alles
 * mit, was er braucht. Was hier steht, ist der Ort und die Überschrift — die
 * gehört in die Seitendatei, weil `seitenTitel.test.js` die Seite liest und
 * nicht durch eine Komponente hindurchsehen kann.
 */
export default function Nachrichten() {
  const { token, user } = useAuth();

  return (
    <div style={S.seite}>
      <SeitenTitel>Nachrichten</SeitenTitel>
      <h1 style={S.h1}>Nachrichten</h1>
      <p style={S.unter}>
        Ihr Verlauf mit uns. Schreiben Sie hier, was Sie brauchen — wir
        antworten an derselben Stelle.
      </p>

      {user?.lead_id ? (
        <KundenChat leadId={user.lead_id} token={token} />
      ) : (
        /* **Kein leerer Kasten.** Ein Konto ohne Betrieb hat keinen
           Betreuer — der Satz sagt das, statt ein Eingabefeld anzubieten,
           dessen Nachricht nirgends ankäme. */
        <p style={S.leise}>
          Sobald Ihr Auftrag angelegt ist, steht hier Ihr Verlauf mit uns.
        </p>
      )}
    </div>
  );
}

const S = {
  seite: { maxWidth: 760, margin: '0 auto', padding: '0 0 40px' },
  h1: { fontSize: 22, fontWeight: 900, letterSpacing: '-.02em', color: 'var(--text-primary)', margin: '0 0 6px' },
  unter: { fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.6, margin: '0 0 22px', maxWidth: '62ch' },
  leise: { fontSize: 13, color: 'var(--text-tertiary)' },
};
