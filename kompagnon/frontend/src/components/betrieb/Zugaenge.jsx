/**
 * Wer sich an diesem Betrieb anmelden kann.
 *
 * **Der Anlass (25.08.2026).** Ein Kundenzugang entstand bisher nur beim
 * Stripe-Kauf — ein Konto je Betrieb. In einem Handwerksbetrieb arbeiten
 * aber Inhaber und Büroleitung am selben Vorgang; ohne zweiten Zugang
 * teilen sich zwei Menschen ein Passwort, und jede Spur im Protokoll zeigt
 * auf denselben Namen.
 *
 * **Der Innendienst lädt ein, nicht der Kunde.** Das war Davids Entscheidung
 * an diesem Tag: Es soll keinen Weg geben, auf dem sich jemand selbst
 * Zugriff auf einen Betrieb verschafft.
 *
 * Der Bildschirm zeigt **kein Passwort** und **keinen Einladungslink**. Der
 * Link ist der Schlüssel zu diesem Konto; wer ihn sieht, kann sich als
 * dieser Mensch anmelden. Er geht ausschließlich in die Mail an ihn.
 */
import { useCallback, useEffect, useState } from 'react';
import Card from '../ui/Card';

const LEER = { email: '', first_name: '', last_name: '' };

export default function Zugaenge({ leadId, token }) {
  const [zugaenge, setZugaenge] = useState(null);
  const [fehler, setFehler] = useState('');
  const [hinweis, setHinweis] = useState('');
  const [formular, setFormular] = useState(LEER);
  const [laeuft, setLaeuft] = useState(false);

  const kopf = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };

  const laden = useCallback(async () => {
    setFehler('');
    try {
      const antwort = await fetch(`/api/leads/${leadId}/zugaenge`, { headers: kopf });
      if (!antwort.ok) throw new Error(`Status ${antwort.status}`);
      const daten = await antwort.json();
      setZugaenge(daten.zugaenge || []);
    } catch (e) {
      setZugaenge([]);
      setFehler(`Zugänge konnten nicht geladen werden (${e.message}).`);
    }
  }, [leadId, token]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { laden(); }, [laden]);

  async function einladen(e) {
    e.preventDefault();
    setLaeuft(true); setFehler(''); setHinweis('');
    try {
      const antwort = await fetch(`/api/leads/${leadId}/zugaenge`, {
        method: 'POST', headers: kopf, body: JSON.stringify(formular),
      });
      const daten = await antwort.json().catch(() => ({}));
      if (!antwort.ok) throw new Error(daten.detail || `Status ${antwort.status}`);
      setFormular(LEER);
      setHinweis(daten.mail_versandt
        ? `Einladung an ${daten.email} versandt.`
        : `Zugang für ${daten.email} angelegt — die Einladungsmail ging `
          + `nicht raus. Über „Einladung erneut senden“ noch einmal versuchen.`);
      await laden();
    } catch (e2) {
      setFehler(e2.message);
    } finally {
      setLaeuft(false);
    }
  }

  async function erneuern(id) {
    setFehler(''); setHinweis('');
    try {
      const antwort = await fetch(`/api/leads/${leadId}/zugaenge/${id}/einladung`,
        { method: 'POST', headers: kopf });
      const daten = await antwort.json().catch(() => ({}));
      if (!antwort.ok) throw new Error(daten.detail || `Status ${antwort.status}`);
      setHinweis(daten.mail_versandt
        ? `Einladung an ${daten.email} erneut versandt.`
        : 'Die Mail ging nicht raus — bitte den Mailversand prüfen.');
      await laden();
    } catch (e) { setFehler(e.message); }
  }

  async function entziehen(id, email) {
    // Kein `confirm()`: Ein Browser-Dialog blockiert, und das Entziehen ist
    // umkehrbar — das Konto wird deaktiviert, nicht gelöscht.
    setFehler(''); setHinweis('');
    try {
      const antwort = await fetch(`/api/leads/${leadId}/zugaenge/${id}`,
        { method: 'DELETE', headers: kopf });
      if (!antwort.ok) throw new Error(`Status ${antwort.status}`);
      setHinweis(`Zugang von ${email} geschlossen. Das Konto bleibt bestehen.`);
      await laden();
    } catch (e) { setFehler(e.message); }
  }

  return (
    <Card padding="md">
      <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 4 }}>
        Zugänge dieses Betriebs
      </div>
      <div style={{ fontSize: 11, color: 'var(--text-tertiary)', lineHeight: 1.5, marginBottom: 16 }}>
        Jeder Mensch im Betrieb bekommt ein eigenes Konto — kein geteiltes
        Passwort. Freigeschaltete Kurse gelten dem Betrieb und gelten damit
        für jeden Zugang, auch für später hinzugekommene.
      </div>

      {zugaenge === null ? (
        <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Wird geladen …</div>
      ) : zugaenge.length === 0 ? (
        <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 16 }}>
          Noch kein Zugang. Der erste entsteht beim Kauf — oder hier.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 16 }}>
          {zugaenge.map(z => (
            <div key={z.id} style={{
              display: 'flex', alignItems: 'center', gap: 12, padding: '10px 12px',
              background: 'var(--bg-app)', borderRadius: 'var(--radius-md)',
              opacity: z.aktiv ? 1 : 0.55,
            }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {z.name || z.email}
                </div>
                <div style={{ fontSize: 10, color: 'var(--text-tertiary)', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {z.name ? z.email : ''}
                  {z.zuletzt_angemeldet
                    ? ` · zuletzt angemeldet ${z.zuletzt_angemeldet.slice(0, 10)}`
                    : ' · noch nie angemeldet'}
                </div>
              </div>
              <span style={{
                fontSize: 9, fontWeight: 700, letterSpacing: '0.06em',
                textTransform: 'uppercase', padding: '3px 8px',
                borderRadius: 'var(--radius-sm)',
                background: !z.aktiv ? 'var(--bg-active)'
                  : z.eingeladen ? 'var(--status-warning-bg)' : 'var(--status-success-bg)',
                color: !z.aktiv ? 'var(--text-tertiary)'
                  : z.eingeladen ? 'var(--status-warning-text)' : 'var(--status-success-text)',
              }}>
                {!z.aktiv ? 'geschlossen' : z.eingeladen ? 'eingeladen' : 'aktiv'}
              </span>
              {z.aktiv && z.eingeladen && (
                <button onClick={() => erneuern(z.id)} style={knopfLeise}>
                  Einladung erneut senden
                </button>
              )}
              {z.aktiv && (
                <button onClick={() => entziehen(z.id, z.email)} style={knopfLeise}>
                  Zugang schließen
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      <form onSubmit={einladen} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-primary)' }}>
          Weiteren Zugang einladen
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <input required type="email" placeholder="E-Mail-Adresse" value={formular.email}
            onChange={e => setFormular({ ...formular, email: e.target.value })}
            style={{ ...feld, flex: '2 1 200px' }} />
          <input placeholder="Vorname" value={formular.first_name}
            onChange={e => setFormular({ ...formular, first_name: e.target.value })}
            style={{ ...feld, flex: '1 1 110px' }} />
          <input placeholder="Nachname" value={formular.last_name}
            onChange={e => setFormular({ ...formular, last_name: e.target.value })}
            style={{ ...feld, flex: '1 1 110px' }} />
        </div>
        <button type="submit" disabled={laeuft} style={{
          alignSelf: 'flex-start', padding: '8px 16px', border: 'none',
          borderRadius: 'var(--radius-md)', background: 'var(--brand-primary)',
          color: 'var(--text-on-brand)', fontSize: 12, fontWeight: 500,
          cursor: laeuft ? 'default' : 'pointer', opacity: laeuft ? 0.6 : 1,
          fontFamily: 'var(--font-sans)',
        }}>
          {laeuft ? 'Wird eingeladen …' : 'Einladung senden'}
        </button>
        <div style={{ fontSize: 10, color: 'var(--text-tertiary)', lineHeight: 1.5 }}>
          Der Eingeladene setzt sein Passwort über einen Link, der sieben Tage
          gilt. Ein Passwort wird nie verschickt und nirgends angezeigt.
        </div>
      </form>

      {fehler && <div style={{ ...meldung, background: 'var(--status-error-bg)', color: 'var(--status-error-text)' }}>{fehler}</div>}
      {hinweis && <div style={{ ...meldung, background: 'var(--status-success-bg)', color: 'var(--status-success-text)' }}>{hinweis}</div>}
    </Card>
  );
}

const feld = {
  padding: '8px 10px', border: '1px solid var(--border-light)',
  borderRadius: 'var(--radius-md)', fontSize: 12, fontFamily: 'var(--font-sans)',
  background: 'var(--bg-surface)', color: 'var(--text-primary)', minWidth: 0,
};

const knopfLeise = {
  padding: '5px 10px', border: '1px solid var(--border-light)',
  borderRadius: 'var(--radius-md)', background: 'transparent',
  color: 'var(--text-tertiary)', fontSize: 10, cursor: 'pointer',
  whiteSpace: 'nowrap', fontFamily: 'var(--font-sans)',
};

const meldung = {
  marginTop: 12, padding: '8px 10px', borderRadius: 'var(--radius-md)',
  fontSize: 11, lineHeight: 1.5,
};
