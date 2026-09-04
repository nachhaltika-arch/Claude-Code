import { useAuth } from '../../context/AuthContext';
import Mitwirkung from '../../components/Mitwirkung';

/**
 * „Was wir brauchen" — die Mitwirkungsleistungen als eigene Seite (L-161).
 *
 * **Warum sie hier steht und nicht mehr auf der Übersicht.** Der Block ist
 * 1.083 px hoch; auf der Startseite verdrängte er alles, was ein Kunde beim
 * Hinsehen zuerst wissen will. Gemessen am 04.09.2026: zehn Überschriften auf
 * 3.156 px, davon vier auf derselben Ebene — David nannte es „unübersichtlich
 * und unaufgeräumt", und das war es.
 *
 * **Der Name ist die Arbeit, nicht das Wort aus dem Vertrag.** „Mitwirkungs-
 * pflichten" ist der Rechtsbegriff; ein Kunde liest „Was wir brauchen". Der
 * Vertragstext steht in jedem Punkt darunter, wo er hingehört.
 */
export default function WasWirBrauchen() {
  const { token } = useAuth();

  return (
    <div style={{ maxWidth: 860, margin: '0 auto', padding: '0 0 40px' }}>
      <h1 style={{ fontSize: 22, fontWeight: 900, letterSpacing: '-.02em',
                   color: 'var(--text-primary)', margin: '0 0 16px' }}>
        Was wir brauchen
      </h1>
      <Mitwirkung token={token} ohneTitel />
    </div>
  );
}
