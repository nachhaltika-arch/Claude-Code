/**
 * Was vom Kunden hereinkommt — Ticket, Chat, später E-Mail (L-18).
 *
 * **Der Anlass (26.08.2026, David):** „ich brauche eine notification für
 * tickets, chat oder email die wir vom kunden erhalten."
 *
 * Vorher: Ein Ticket löste **gar nichts** aus, eine Chatnachricht eine Mail
 * an eine feste Adresse aus der Umgebung. Wer im Werkzeug arbeitete, erfuhr
 * nichts, bis er von sich aus nachsah.
 *
 * **Warum sie sich nicht von selbst aktualisiert.** Ein Dauerpolling im Kopf
 * jeder Seite ist eine Anfrage alle paar Sekunden, den ganzen Arbeitstag
 * lang, für ein Postfach mit ein paar Einträgen am Tag. Sie holt die Zahl
 * beim Seitenwechsel und beim Öffnen — das ist der Rhythmus, in dem im
 * Innendienst ohnehin gearbeitet wird.
 *
 * **Warum sie beim Klick als gelesen gilt und nicht beim Aufklappen.**
 * Aufklappen heißt „ich schaue kurz", nicht „ich habe es bearbeitet". Wer
 * eine Meldung öffnet, hat sie gesehen; die übrigen bleiben fett stehen.
 */
import { useCallback, useEffect, useState } from 'react';
import { useEscapeKey } from '../../hooks/useKeyboardShortcuts';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import API_BASE_URL from '../../config';
import { aufTaste } from '../../utils/tastaturBedienung';

/** Symbol je Quelle — damit man die Art vor dem Lesen erkennt. */
// `faellig` kam am 01.09.2026 dazu (L-101): keine Meldung eines Kunden,
// sondern eine Aufgabe mit Termin — das Quartals-Re-Audit der Pflege-Abos.
// Ohne eigenes Zeichen faellt sie auf den Punkt zurueck und sieht aus wie
// etwas, das jemand vergessen hat einzutragen.
const SINNBILD = { ticket: '🎫', chat: '💬', mail: '✉️', faellig: '📅' };

function wieLange(roh) {
  if (!roh) return '';
  const dann = new Date(roh);
  if (Number.isNaN(dann.getTime())) return '';
  const minuten = Math.round((Date.now() - dann.getTime()) / 60000);
  if (minuten < 1) return 'gerade eben';
  if (minuten < 60) return `vor ${minuten} min`;
  if (minuten < 60 * 24) return `vor ${Math.round(minuten / 60)} h`;
  return dann.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' });
}

export default function Glocke() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [offen, setOffen] = useState(false);

  // **Escape schliesst — WCAG 2.1.1 (30.08.2026, L-17).** Der Hintergrund
  // reagiert auf einen Klick; mit der Tastatur gab es keinen Weg heraus.
  // `role="button"` waere hier falsch: Eine Ueberlagerung ist keine
  // Schaltflaeche, sie ist der Weg zurueck.
  // **Steht hier und nicht unter der Signatur.** Der Aufruf liest eine
  // `const`-Bindung von oben; weiter oben eingesetzt waere das ein
  // ReferenceError beim Rendern — und keiner der 558 Tests rendert
  // diese Seite, haette ihn also gemeldet.
  useEscapeKey(() => setOffen(false), offen);
  const [anzahl, setAnzahl] = useState(0);
  const [liste, setListe] = useState(null);

  const kopf = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const zahlHolen = useCallback(async () => {
    try {
      const antwort = await fetch(`${API_BASE_URL}/api/benachrichtigungen/anzahl`, { headers: kopf });
      if (!antwort.ok) return;               // Kein Recht, kein Rauschen.
      const daten = await antwort.json();
      setAnzahl(daten.ungelesen || 0);
    } catch { /* Eine Glocke, die nicht laedt, schweigt — sie stoert nicht. */ }
  }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  // Beim Seitenwechsel neu fragen: Wer gerade ein Ticket bearbeitet hat,
  // soll die Zahl sinken sehen, ohne die Seite neu zu laden.
  useEffect(() => { zahlHolen(); }, [zahlHolen, location.pathname]);

  async function aufklappen() {
    const neuerZustand = !offen;
    setOffen(neuerZustand);
    if (!neuerZustand) return;

    setListe(null);
    try {
      const antwort = await fetch(`${API_BASE_URL}/api/benachrichtigungen`, { headers: kopf });
      setListe(antwort.ok ? await antwort.json() : []);
    } catch {
      setListe([]);
    }
  }

  async function oeffnen(eintrag) {
    setOffen(false);
    try {
      await fetch(`${API_BASE_URL}/api/benachrichtigungen/${eintrag.id}/gelesen`,
        { method: 'POST', headers: kopf });
    } catch { /* Der Weg zum Vorgang ist wichtiger als der Haken. */ }
    zahlHolen();
    if (eintrag.ziel) navigate(eintrag.ziel);
  }

  async function alleGelesen() {
    try {
      await fetch(`${API_BASE_URL}/api/benachrichtigungen/alle-gelesen`,
        { method: 'POST', headers: kopf });
    } catch { /* still */ }
    setAnzahl(0);
    setListe((v) => (v || []).map((e) => ({ ...e, gelesen: true })));
  }

  return (
    <div style={{ position: 'relative', flexShrink: 0 }}>
      <button
        type="button"
        onClick={aufklappen}
        aria-expanded={offen}
        aria-label={anzahl
          ? `Posteingang, ${anzahl} ungelesen`
          : 'Posteingang, nichts Neues'}
        style={{
          position: 'relative', background: 'none', border: 'none',
          cursor: 'pointer', padding: '6px 8px', fontSize: 17, lineHeight: 1,
          color: 'var(--text-secondary, var(--text-primary))',
        }}
      >
        🔔
        {anzahl > 0 && (
          <span style={{
            position: 'absolute', top: 0, right: 0,
            minWidth: 16, height: 16, padding: '0 4px',
            borderRadius: 8, background: 'var(--status-error-text)',
            color: '#fff', fontSize: 12, fontWeight: 700,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontFamily: 'var(--font-sans)',
          }}>
            {anzahl > 99 ? '99+' : anzahl}
          </span>
        )}
      </button>

      {offen && (
        <>
          {/* Ein Klick daneben schliesst — sonst verdeckt das Feld, was man
            * als Naechstes anklicken will. */}
          <div role="button" tabIndex={0}
            onKeyDown={aufTaste(() => setOffen(false))}
            onClick={() => setOffen(false)}
            style={{ position: 'fixed', inset: 0, zIndex: 119 }}
          />
          <div style={{
            position: 'absolute', top: 'calc(100% + 8px)', right: 0, zIndex: 120,
            width: 340, maxHeight: 420, overflowY: 'auto',
            background: 'var(--bg-elevated, var(--bg-surface))',
            border: '1px solid var(--border-light)',
            borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-lg)',
            padding: 4,
          }}>
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '8px 10px 6px', borderBottom: '1px solid var(--border-light)',
            }}>
              <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)' }}>
                Vom Kunden
              </span>
              {anzahl > 0 && (
                <button type="button" onClick={alleGelesen} style={{
                  background: 'none', border: 'none', cursor: 'pointer',
                  fontSize: 12, color: 'var(--text-tertiary)',
                  fontFamily: 'var(--font-sans)',
                }}>
                  Alle gelesen
                </button>
              )}
            </div>

            {liste === null && (
              <div style={{ padding: '12px 10px', fontSize: 12, color: 'var(--text-tertiary)' }}>
                Wird geladen …
              </div>
            )}
            {liste?.length === 0 && (
              <div style={{ padding: '12px 10px', fontSize: 12, color: 'var(--text-tertiary)', lineHeight: 1.55 }}>
                Nichts Neues. Hier erscheinen Tickets und Nachrichten, die
                Kunden schicken.
              </div>
            )}
            {liste?.map((eintrag) => (
              <button
                key={eintrag.id}
                type="button"
                onClick={() => oeffnen(eintrag)}
                style={{
                  display: 'flex', gap: 8, width: '100%', textAlign: 'left',
                  background: 'none', border: 'none', cursor: 'pointer',
                  padding: '9px 10px', borderRadius: 'var(--radius-md)',
                  fontFamily: 'var(--font-sans)', color: 'var(--text-primary)',
                }}
              >
                <span style={{ fontSize: 14, flexShrink: 0 }} aria-hidden="true">
                  {SINNBILD[eintrag.art] || '•'}
                </span>
                <span style={{ minWidth: 0, flex: 1 }}>
                  <span style={{
                    display: 'block', fontSize: 12,
                    fontWeight: eintrag.gelesen ? 400 : 700,
                    color: eintrag.gelesen ? 'var(--text-tertiary)' : 'var(--text-primary)',
                  }}>
                    {eintrag.titel}
                  </span>
                  {eintrag.hinweis && (
                    <span style={{
                      display: 'block', fontSize: 12, color: 'var(--text-tertiary)',
                      overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                    }}>
                      {eintrag.hinweis}
                    </span>
                  )}
                  <span style={{ display: 'block', fontSize: 12, color: 'var(--text-tertiary)', marginTop: 2 }}>
                    {wieLange(eintrag.erstellt_am)}
                  </span>
                </span>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
