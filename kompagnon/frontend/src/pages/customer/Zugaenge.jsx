import { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import API_BASE_URL from '../../config';
import { datumKurz } from '../../utils/datum';
import SeitenTitel from '../../components/ui/SeitenTitel';

/**
 * „Zugänge für Kollegen" — ein Betrieb ist keine Person (L-160 Rang 4, K7).
 *
 * **Der Befund.** Ein Betrieb hatte genau ein Konto. Wer einem Kollegen
 * Zugang geben wollte, gab sein Kennwort weiter — und damit den Blick auf
 * Rechnungen und Zahlungsart. Die Routen zum Anlegen von Konten gibt es
 * längst, aber sie verlangen `manage_users`, also Innendienst: Jeder Zugang
 * musste bei uns beantragt werden.
 *
 * **Zwei Rechtestufen, und bewusst nur zwei.** Drei wären genauer und würden
 * seltener stimmen; die Frage, die ein Betrieb wirklich stellt, ist „darf der
 * ans Geld?". Was sie bedeuten, steht neben der Auswahl und kommt aus dem
 * Katalog (`services/kundenzugang.py`) — eine zweite Fassung auf dem
 * Bildschirm wäre eine, die vom Vertrag abweicht.
 *
 * **Wer nur ansehen darf, sieht diese Seite trotzdem.** Wer hereinkommt, soll
 * sehen, wer sonst hereinkommt; nur die Knöpfe fehlen. Eine Liste, die man
 * nicht sieht, macht das Gefühl nicht besser, sondern schlechter.
 */
export default function Zugaenge() {
  const { token } = useAuth();
  const [daten, setDaten] = useState(null);
  const [fehler, setFehler] = useState('');
  const [mail, setMail] = useState('');
  const [recht, setRecht] = useState('ansehen');
  const [laeuft, setLaeuft] = useState(false);
  const [hinweis, setHinweis] = useState('');

  const laden = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/portal/zugaenge`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`Konnte nicht geladen werden (${res.status})`);
      setDaten(await res.json());
      setFehler('');
    } catch (e) {
      setFehler(e.message);
    }
  }, [token]);

  useEffect(() => { if (token) laden(); }, [token, laden]);

  const einladen = async () => {
    setLaeuft(true); setHinweis(''); setFehler('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/portal/zugaenge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ email: mail.trim(), recht }),
      });
      const d = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(d.detail || 'Einladung nicht möglich.');
      setMail('');
      /* **Was wirklich geschehen ist, nicht was geplant war.** Das Konto
         entsteht auch dann, wenn die Mail scheitert — dann muss der Betrieb
         wissen, dass er selbst Bescheid geben muss. */
      setHinweis(d.mail_versandt
        ? `Einladung an ${d.email} verschickt.`
        : `Zugang für ${d.email} angelegt — die Einladungsmail ging nicht `
          + 'hinaus. Bitte sagen Sie Ihrem Kollegen, dass er sich über '
          + '„Kennwort vergessen" anmelden kann.');
      await laden();
    } catch (e) {
      setFehler(e.message);
    } finally {
      setLaeuft(false);
    }
  };

  const entfernen = async (id, name) => {
    /* Unwiderruflich, deshalb die Rückfrage — und sie nennt den Zugang beim
       Namen, statt nur „Sind Sie sicher?" zu fragen. */
    // eslint-disable-next-line no-alert
    if (!window.confirm(`Zugang für ${name} entfernen? Er kann sich danach nicht mehr anmelden.`)) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/portal/zugaenge/${id}`, {
        method: 'DELETE', headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Zugang nicht entfernt.');
      await laden();
    } catch (e) {
      setFehler(e.message);
    }
  };

  if (!daten) {
    return (
      <div style={S.seite}>
        <SeitenTitel>Zugänge für Kollegen</SeitenTitel>
        <h1 style={S.h1}>Zugänge für Kollegen</h1>
        <p style={S.leise}>{fehler || 'Wird geladen …'}</p>
      </div>
    );
  }

  const stufeText = (wert) => daten.stufen.find(s => s.wert === wert)?.text || '';

  return (
    <div style={S.seite}>
      <SeitenTitel>Zugänge für Kollegen</SeitenTitel>
      <h1 style={S.h1}>Zugänge für Kollegen</h1>
      <p style={S.unter}>
        Ein Betrieb ist keine Person. Geben Sie Ihren Leuten eigene Zugänge,
        statt Ihr Kennwort weiterzugeben.
      </p>

      {fehler && <p style={S.fehler}>{fehler}</p>}
      {hinweis && <p style={S.hinweis}>{hinweis}</p>}

      <ul style={S.liste}>
        {daten.zugaenge.map(z => (
          <li key={z.id} style={S.zeile}>
            <span style={S.kuerzel}>{kuerzel(z)}</span>
            <span style={S.mitte}>
              <span style={S.name}>{z.name || z.email}{z.selbst && ' (Sie)'}</span>
              <span style={S.dazu}>
                {z.email}
                {' · '}
                {z.eingeladen
                  ? 'Einladung offen'
                  : z.zuletzt ? `zuletzt ${datumKurz(z.zuletzt)}` : 'noch nicht angemeldet'}
              </span>
            </span>
            <span style={S.marke} title={stufeText(z.recht)}>
              {z.recht === 'alles' ? 'darf alles' : 'darf ansehen'}
            </span>
            {daten.darf_verwalten && !z.selbst && (
              <button style={S.weg} onClick={() => entfernen(z.id, z.name || z.email)}>
                entfernen
              </button>
            )}
          </li>
        ))}
      </ul>

      {daten.darf_verwalten ? (
        <section style={S.kasten}>
          <h2 style={S.h2}>Kollegen einladen</h2>
          <div style={S.formular}>
            <label style={S.feld}>
              <span style={S.beschriftung}>E-Mail-Adresse</span>
              <input style={S.eingabe} type="email" value={mail}
                     onChange={e => setMail(e.target.value)}
                     placeholder="name@ihr-betrieb.de" />
            </label>
            <label style={S.feld}>
              <span style={S.beschriftung}>Darf</span>
              <select style={S.eingabe} value={recht}
                      onChange={e => setRecht(e.target.value)}>
                {daten.stufen.map(s => (
                  <option key={s.wert} value={s.wert}>
                    {s.wert === 'alles' ? 'alles' : 'ansehen'}
                  </option>
                ))}
              </select>
            </label>
            <button style={S.knopf} onClick={einladen}
                    disabled={laeuft || !mail.includes('@')}>
              {laeuft ? 'Wird angelegt …' : 'Einladen'}
            </button>
          </div>
          {/* Die Erklärung kommt aus dem Katalog, nicht von hier — sonst
              stünde auf dem Bildschirm etwas anderes als im Vertrag. */}
          <p style={S.erklaerung}>{stufeText(recht)}</p>
        </section>
      ) : (
        <p style={S.leise}>
          Neue Zugänge richtet ein Kollege ein, der alles darf.
        </p>
      )}
    </div>
  );
}

function kuerzel(z) {
  const teile = (z.name || z.email || '?').split(/[\s@.]+/).filter(Boolean);
  return (teile[0]?.[0] || '?').toUpperCase() + (teile[1]?.[0] || '').toUpperCase();
}

const S = {
  seite: { maxWidth: 760, margin: '0 auto', padding: '0 0 40px' },
  h1: { fontSize: 22, fontWeight: 900, letterSpacing: '-.02em', color: 'var(--text-primary)', margin: '0 0 6px' },
  unter: { fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.6, margin: '0 0 22px', maxWidth: '62ch' },
  liste: { listStyle: 'none', margin: '0 0 28px', padding: 0, display: 'flex', flexDirection: 'column', gap: 10 },
  zeile: { display: 'flex', alignItems: 'center', gap: 14, background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 8, padding: '14px 18px' },
  kuerzel: { flex: 'none', width: 36, height: 36, borderRadius: '50%', background: 'var(--bg-app)', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 900, fontSize: 13 },
  mitte: { flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: 2 },
  name: { fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' },
  dazu: { fontSize: 13, color: 'var(--text-tertiary)' },
  marke: { flex: 'none', fontSize: 12, fontWeight: 700, padding: '4px 10px', borderRadius: 999, background: 'var(--bg-app)', color: 'var(--text-secondary)', boxShadow: 'inset 0 0 0 1px var(--border-subtle, var(--border-light))' },
  weg: { flex: 'none', background: 'none', border: 'none', color: 'var(--status-danger-text)', fontSize: 13, cursor: 'pointer', fontFamily: 'inherit' },
  kasten: { background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 8, padding: 22 },
  h2: { fontSize: 13, fontWeight: 900, textTransform: 'uppercase', letterSpacing: '.06em', color: 'var(--text-tertiary)', margin: '0 0 14px' },
  formular: { display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'flex-end' },
  feld: { display: 'flex', flexDirection: 'column', gap: 6, flex: '1 1 200px' },
  beschriftung: { fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)' },
  eingabe: { padding: '10px 12px', borderRadius: 6, border: '1px solid var(--border-light)', background: 'var(--bg-app)', color: 'var(--text-primary)', fontSize: 14, fontFamily: 'inherit' },
  knopf: { fontWeight: 900, fontSize: 14, padding: '11px 22px', borderRadius: 6, border: 'none', cursor: 'pointer', background: 'var(--brand-primary)', color: 'var(--text-on-brand)' },
  erklaerung: { fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6, margin: '14px 0 0', maxWidth: '62ch' },
  hinweis: { fontSize: 13, color: 'var(--status-success-text)', margin: '0 0 16px', lineHeight: 1.6 },
  fehler: { fontSize: 13, color: 'var(--status-danger-text)', margin: '0 0 16px' },
  leise: { fontSize: 13, color: 'var(--text-tertiary)' },
};
