/**
 * Der Nachrichtenverlauf zwischen Kunde und Innendienst.
 *
 * **Der Auftrag (26.08.2026, David).** Im Kundenportal soll der Chat
 * eingebaut werden.
 *
 * **Was schon da war:** Beide Richtungen. Der Innendienst hat den Reiter
 * „Nachrichten" am Betrieb, und `GET`/`POST /api/messages/{id}/kunde` gab es
 * ebenfalls — nur für das **Token-Portal**, das man über den QR-Code ohne
 * Anmeldung betritt. Im angemeldeten Portal fehlte der Verlauf ganz; der
 * einzige Weg zum Team war ein `mailto:`-Link.
 *
 * Seit heute nehmen dieselben zwei Routen auch eine Anmeldung an. Kein
 * zweiter Endpunkt: Zwei Wege zum selben Ziel sind zwei Wege, die falsch
 * sein können.
 *
 * **Was dieses Bauteil bewusst nicht tut:** von selbst nachladen. Ein
 * Dauerpolling für einen Verlauf, in dem ein paar Nachrichten am Tag stehen,
 * kostet Anfragen ohne Gegenwert. Nach dem eigenen Senden wird geladen, sonst
 * über den Knopf „Aktualisieren".
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import API_BASE_URL from '../../config';

/** Wie viele Zeichen eine Nachricht tragen darf. */
const HOECHSTLAENGE = 4000;

function zeitpunkt(roh) {
  if (!roh) return '';
  const d = new Date(roh);
  if (Number.isNaN(d.getTime())) return '';
  return d.toLocaleString('de-DE', {
    day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit',
  });
}

export default function KundenChat({ leadId, token }) {
  const [verlauf, setVerlauf] = useState(null);
  const [text, setText] = useState('');
  const [fehler, setFehler] = useState('');
  const [sendet, setSendet] = useState(false);
  const ende = useRef(null);

  const kopf = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const laden = useCallback(async () => {
    setFehler('');
    try {
      const antwort = await fetch(`${API_BASE_URL}/api/messages/${leadId}/kunde`, { headers: kopf });
      if (!antwort.ok) throw new Error(`Status ${antwort.status}`);
      const daten = await antwort.json();
      setVerlauf(Array.isArray(daten) ? daten : []);
    } catch (e) {
      setVerlauf([]);
      setFehler(`Der Verlauf konnte nicht geladen werden (${e.message}).`);
    }
  }, [leadId, token]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { laden(); }, [laden]);

  // Ans Ende springen, wenn etwas dazugekommen ist — der neueste Beitrag ist
  // der, den man lesen will.
  useEffect(() => {
    if (verlauf && verlauf.length) ende.current?.scrollIntoView({ block: 'nearest' });
  }, [verlauf]);

  async function senden(e) {
    e.preventDefault();
    const inhalt = text.trim();
    if (!inhalt) return;

    setSendet(true); setFehler('');
    try {
      const antwort = await fetch(`${API_BASE_URL}/api/messages/${leadId}/kunde`, {
        method: 'POST', headers: kopf, body: JSON.stringify({ content: inhalt }),
      });
      const daten = await antwort.json().catch(() => ({}));
      if (!antwort.ok) throw new Error(daten.detail || `Status ${antwort.status}`);
      setText('');
      await laden();
    } catch (e2) {
      // Der Text bleibt im Feld stehen. Ihn zu verwerfen, weil der Server
      // gerade nicht mochte, waere der zweite Schaden nach dem ersten.
      setFehler(`Die Nachricht ging nicht raus (${e2.message}). `
        + `Ihr Text steht noch im Feld.`);
    } finally {
      setSendet(false);
    }
  }

  const vomKunden = (m) => m.sender_role === 'kunde';

  return (
    <div style={{
      background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
      borderRadius: 'var(--radius-xl)', padding: '18px 20px',
      display: 'flex', flexDirection: 'column', gap: 12,
    }}>
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 12 }}>
        <h2 style={{ margin: 0, fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>
          Nachrichten
        </h2>
        <button type="button" onClick={laden} style={knopfLeise}>
          Aktualisieren
        </button>
      </div>

      <div style={{
        display: 'flex', flexDirection: 'column', gap: 8,
        maxHeight: 320, overflowY: 'auto', paddingRight: 4,
      }}>
        {verlauf === null && (
          <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>Wird geladen …</div>
        )}
        {verlauf?.length === 0 && (
          <div style={{ fontSize: 12, color: 'var(--text-tertiary)', lineHeight: 1.6 }}>
            Noch keine Nachrichten. Schreiben Sie uns — Ihr Betreuer sieht es
            direkt im Betrieb und bekommt eine Benachrichtigung.
          </div>
        )}
        {verlauf?.map((m) => (
          <div
            key={m.id}
            style={{
              alignSelf: vomKunden(m) ? 'flex-end' : 'flex-start',
              maxWidth: '82%',
              background: vomKunden(m) ? 'var(--brand-primary)' : 'var(--bg-subtle, var(--bg-surface))',
              color: vomKunden(m) ? 'var(--text-on-brand)' : 'var(--text-primary)',
              border: vomKunden(m) ? 'none' : '1px solid var(--border-light)',
              borderRadius: 'var(--radius-md)',
              padding: '8px 12px', fontSize: 13, lineHeight: 1.5,
              whiteSpace: 'pre-wrap', wordBreak: 'break-word',
            }}
          >
            {!vomKunden(m) && (
              <div style={{ fontSize: 12, fontWeight: 700, opacity: 0.7, marginBottom: 3 }}>
                {m.sender_name || 'KOMPAGNON'}
              </div>
            )}
            {m.content}
            <div style={{ fontSize: 12, opacity: 0.65, marginTop: 4, textAlign: 'right' }}>
              {zeitpunkt(m.created_at)}
            </div>
          </div>
        ))}
        <div ref={ende} />
      </div>

      <form onSubmit={senden} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value.slice(0, HOECHSTLAENGE))}
          placeholder="Ihre Nachricht an das Team …"
          aria-label="Ihre Nachricht an das Team"
          rows={3}
          style={{
            width: '100%', resize: 'vertical',
            padding: '10px 12px', fontSize: 13, lineHeight: 1.5,
            borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)',
            background: 'var(--bg-surface)', color: 'var(--text-primary)',
            fontFamily: 'var(--font-sans)',
          }}
        />
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button type="submit" disabled={sendet || !text.trim()} style={{
            padding: '8px 18px', border: 'none', borderRadius: 'var(--radius-md)',
            background: 'var(--brand-primary)', color: 'var(--text-on-brand)',
            fontSize: 13, fontWeight: 600, fontFamily: 'var(--font-sans)',
            cursor: sendet || !text.trim() ? 'default' : 'pointer',
            opacity: sendet || !text.trim() ? 0.6 : 1,
          }}>
            {sendet ? 'Wird gesendet …' : 'Senden'}
          </button>
          <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
            {text.length}/{HOECHSTLAENGE}
          </span>
        </div>
      </form>

      {fehler && (
        <div role="alert" style={{
          fontSize: 12, lineHeight: 1.5, padding: '8px 12px',
          borderRadius: 'var(--radius-md)',
          background: 'var(--status-error-bg)', color: 'var(--status-error-text)',
        }}>
          {fehler}
        </div>
      )}
    </div>
  );
}

const knopfLeise = {
  background: 'none', border: '1px solid var(--border-light)',
  borderRadius: 'var(--radius-md)', padding: '4px 10px',
  fontSize: 12, color: 'var(--text-tertiary)', cursor: 'pointer',
  fontFamily: 'var(--font-sans)',
};
