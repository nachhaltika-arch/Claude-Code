import { useAuth } from '../../context/AuthContext';
import Inhaltsguthaben from '../../components/Inhaltsguthaben';

/**
 * „Inhaltsänderungen" — Guthaben und Wünsche als eigene Seite (L-161).
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
        Inhaltsänderungen
      </h1>
      <Inhaltsguthaben token={token} ohneTitel />
    </div>
  );
}
