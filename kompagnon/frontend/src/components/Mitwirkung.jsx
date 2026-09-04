import { useState, useEffect } from 'react';
import API_BASE_URL from '../config';
import { datumKurz } from '../utils/datum';
import MitwirkungAktion from './kunde/MitwirkungAktion';

/**
 * Was wir vom Kunden brauchen — als Liste, die er abarbeiten kann (L-159).
 *
 * **Warum eine eigene Datei.** `KundenPortal.jsx` hat 657 Zeilen; dieser Block
 * hätte es über die eigene 800-Zeilen-Grenze gehoben.
 *
 * **Drei Entscheidungen aus dem Entwurf, die hier tragen:**
 *
 * 1. **Oben steht ein Datum, keine Klausel.** „Die Bauzeit beginnt an dem
 *    Werktag, an dem sämtliche Mitwirkungsleistungen vorliegen" ist die
 *    Vertragssprache. Der Kunde will wissen, wann gebaut wird.
 * 2. **Erledigtes wandert nach unten, verschwindet aber nicht.** Dort steht,
 *    was wir wann verbucht haben — die Stelle, an der er widersprechen kann.
 * 3. **„Offen" ist neutral, nicht orange.** Orange heißt „Achtung"; ein noch
 *    nicht erledigter Punkt ist kein Fehler. Warm ist genau ein Zeichen auf
 *    dem Bildschirm: der nächste Schritt.
 */
/*
 * `ohneTitel` laesst die eigene Ueberschrift weg (L-161, 04.09.2026).
 *
 * Seit dem Umbau steht dieser Block **allein** auf einer Seite statt als
 * einer von dreien auf der Uebersicht. Dann traegt die Seite den Titel, und
 * dieser hier waere der zweite — ein Screenreader laese
 * „Inhaltsaenderungen. Inhaltsaenderungen".
 *
 * **Warum die Seite ihn traegt und nicht dieser Block.** Der erste Entwurf
 * machte es umgekehrt: Der Block befoerderte seine Ueberschrift zum `h1`.
 * Das lief, sah richtig aus — und liess `seitenTitel.test.js` auflaufen, den
 * Waechter aus L-17: Er liest die **Seitendatei** und kann nicht durch eine
 * Komponente hindurchsehen. Der Waechter hat recht; ein Titel gehoert dorthin,
 * wo die Seite steht.
 */
export default function Mitwirkung({ token, ohneTitel = false }) {
  const [daten, setDaten] = useState(null);
  const [fehler, setFehler] = useState('');
  const [laeuft, setLaeuft] = useState('');
  const [offenerPunkt, setOffenerPunkt] = useState(null);

  const laden = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/portal/mitwirkung`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`Konnte nicht geladen werden (${res.status})`);
      setDaten(await res.json());
      setFehler('');
    } catch (e) {
      setFehler(e.message);
    }
  };

  useEffect(() => { if (token) laden(); }, [token]);   // eslint-disable-line

  const eintragen = async (kennung, angaben = {}) => {
    setLaeuft(kennung);
    try {
      const res = await fetch(`${API_BASE_URL}/api/portal/mitwirkung/${kennung}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ angaben }),
      });
      if (!res.ok) throw new Error('Eintrag nicht gespeichert — bitte noch einmal.');
      await laden();
      setOffenerPunkt(null);
    } catch (e) {
      setFehler(e.message);
    } finally {
      setLaeuft('');
    }
  };

  if (fehler) return <p style={S.fehler}>{fehler}</p>;
  if (!daten) return <p style={S.leise}>Wird geladen …</p>;
  if (!daten.punkte.length) return null;

  const offene = daten.punkte.filter(p => !p.erledigt);
  const fertige = daten.punkte.filter(p => p.erledigt);
  const naechster = offene[0]?.kennung;

  return (
    <section style={S.rahmen}>
      <header style={S.kopf}>
        {!ohneTitel && <h2 style={S.h1}>Was wir von Ihnen brauchen</h2>}
        <p style={S.termin}>{satz(daten)}</p>
        <p style={S.zaehler}>{daten.erledigt} von {daten.gesamt} erledigt</p>
      </header>

      {offene.length > 0 && (
        <>
          <h3 style={S.h2}>Damit wir starten können</h3>
          {offene.map(p => (
            <Karte key={p.kennung} punkt={p} naechst={p.kennung === naechster}
                   auf={offenerPunkt === p.kennung}
                   umschalten={() => setOffenerPunkt(offenerPunkt === p.kennung ? null : p.kennung)}
                   eintragen={eintragen} laeuft={laeuft === p.kennung}
                   token={token} leadId={daten.lead_id} terminLink={daten.termin_link}
                   neuLaden={laden} />
          ))}
        </>
      )}

      {fertige.length > 0 && (
        <>
          <h3 style={S.h2}>Schon erledigt</h3>
          {fertige.map(p => (
            <Karte key={p.kennung} punkt={p}
                   auf={offenerPunkt === p.kennung}
                   umschalten={() => setOffenerPunkt(offenerPunkt === p.kennung ? null : p.kennung)} />
          ))}
        </>
      )}

      {daten.spaeter?.length > 0 && (
        <div style={S.spaeter}>
          <h4 style={S.h3}>Später kommen zwei Freigaben auf Sie zu</h4>
          <p style={S.spaeterText}>
            Nichts zu tun, solange wir nichts vorgelegt haben. Sie bekommen eine
            Nachricht, und dann haben Sie fünf Werktage.
          </p>
          <ul style={S.liste}>
            {daten.spaeter.map(p => (
              <li key={p.kennung}><b>{p.titel}</b> — {p.warum}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

function satz({ offen, start_moeglich }) {
  if (start_moeglich) return 'Alles da. Wir starten am nächsten Werktag — die Bauzeit läuft ab dann.';
  if (offen === 1) return 'Es fehlt noch eine Angabe. Kommt sie heute, starten wir morgen.';
  return `Es fehlen noch ${WORTE[offen] || offen} Angaben. Sobald sie da sind, starten wir am nächsten Werktag.`;
}

const WORTE = ['keine', 'eine', 'zwei', 'drei', 'vier', 'fünf', 'sechs', 'sieben', 'acht'];

function Karte({ punkt, naechst, auf, umschalten, eintragen, laeuft,
                 token, leadId, terminLink, neuLaden }) {
  const fertig = punkt.erledigt;
  return (
    <article style={{ ...S.karte, borderTopColor: fertig ? 'var(--status-success)' : 'var(--brand-primary)' }}>
      {/* **Kein `disabled` (04.09.2026).** Erledigte Karten waren gesperrt und
          sahen trotzdem aus wie die offenen — gleiche Form, gleicher
          Zeigefinger, keine Reaktion. Beim ersten Test von aussen wurde genau
          die erste, erledigte Karte angeklickt, und nichts geschah.
          Aufklappen dürfen sie ohnehin: Dort steht, was wir wann verbucht
          haben — die Stelle, an der ein Kunde widersprechen kann. Nur der
          Eintragen-Knopf fehlt. */}
      <button style={S.zeile} onClick={umschalten} aria-expanded={!!auf}>
        <span style={S.nr}>{punkt.kennung}</span>
        <span style={S.mitte}>
          <span style={S.titel}>{punkt.titel}</span>
          <span style={S.warum}>
            {fertig && punkt.erledigt_am
              ? `Eingegangen am ${datumKurz(punkt.erledigt_am)}${punkt.bestaetigt_von ? ` · ${punkt.bestaetigt_von}` : ''}`
              : punkt.warum}
          </span>
        </span>
        <span style={fertig ? S.markeFertig : naechst ? S.markeNaechst : S.markeOffen}>
          {fertig ? 'erledigt' : naechst ? 'als Nächstes' : 'offen'}
        </span>
      </button>

      {auf && (
        <div style={S.klapp}>
          <p style={S.klappText}>{punkt.vertragstext}</p>
          {fertig ? (
            <>
              {punkt.notiz && (
                /* Was wir verbucht haben, im Wortlaut. Die Stelle, an der ein
                   Kunde widersprechen kann — und aus der der Fristbeginn
                   abgeleitet wird. */
                <p style={S.notiz}>{punkt.notiz}</p>
              )}
              <p style={S.leise}>
                Sollte das nicht stimmen, schreiben Sie uns — wir tragen es zurück.
              </p>
            </>
          ) : punkt.aktion && punkt.aktion !== 'abhaken' ? (
            /* **Die Handlung selbst, nicht nur ein Haken** (04.09.2026).
               Welche es ist, sagt der Katalog — siehe `MitwirkungAktion`. */
            <MitwirkungAktion punkt={punkt} token={token} leadId={leadId}
                              terminLink={terminLink} eintragen={eintragen}
                              laeuft={laeuft} neuLaden={neuLaden} />
          ) : (
            <button style={S.knopf} onClick={() => eintragen(punkt.kennung)} disabled={laeuft}>
              {laeuft ? 'Wird gespeichert …' : 'Das habe ich erledigt'}
            </button>
          )}
        </div>
      )}
    </article>
  );
}

/* Tool-CI: Dark Teal dominiert, Gelb genau einmal, Status immer Farbe UND Text. */
const marke = {
  flex: 'none', display: 'inline-flex', alignItems: 'center', fontSize: 12,
  fontWeight: 700, padding: '4px 10px', borderRadius: 999, whiteSpace: 'nowrap',
};
const S = {
  rahmen: { marginTop: 32 },
  kopf: { background: 'var(--brand-primary)', color: '#fff', borderRadius: 12, padding: 32, marginBottom: 24 },
  h1: { fontWeight: 900, letterSpacing: '-0.025em', fontSize: 24, margin: '0 0 8px' },
  termin: { fontSize: 17, lineHeight: 1.5, margin: 0, maxWidth: '52ch' },
  zaehler: { marginTop: 20, fontFamily: 'var(--font-mono, monospace)', fontSize: 14, opacity: 0.85, margin: '20px 0 0' },
  h2: { fontWeight: 900, letterSpacing: '-0.025em', fontSize: 14, textTransform: 'uppercase', margin: '32px 0 12px', color: 'var(--text-secondary)' },
  h3: { fontWeight: 900, fontSize: 15, margin: '0 0 6px' },
  karte: { background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderTop: '3px solid', borderRadius: 8, marginBottom: 12, overflow: 'hidden' },
  zeile: { display: 'flex', gap: 16, alignItems: 'flex-start', padding: '20px 24px', width: '100%', background: 'none', border: 'none', textAlign: 'left', font: 'inherit', color: 'inherit', cursor: 'pointer' },
  nr: { fontFamily: 'var(--font-mono, monospace)', fontSize: 13, color: 'var(--text-tertiary)', flex: 'none', width: 32 },
  mitte: { flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: 2 },
  titel: { fontWeight: 700, fontSize: 16, color: 'var(--text-primary)' },
  warum: { fontSize: 14, color: 'var(--text-tertiary)', lineHeight: 1.5, maxWidth: '56ch' },
  markeOffen: { ...marke, background: 'var(--bg-app)', color: 'var(--text-secondary)', boxShadow: 'inset 0 0 0 1px var(--border-subtle)' },
  markeNaechst: { ...marke, background: 'var(--brand-accent, #FAE600)', color: '#000' },
  markeFertig: { ...marke, background: 'var(--status-success-bg)', color: 'var(--status-success)' },
  klapp: { padding: '0 24px 24px 72px', borderTop: '1px solid var(--border-subtle)' },
  klappText: { fontSize: 14, color: 'var(--text-secondary)', margin: '16px 0 12px', maxWidth: '62ch' },
  knopf: { fontWeight: 900, fontSize: 14, padding: '12px 20px', borderRadius: 6, border: 'none', cursor: 'pointer', background: 'var(--brand-primary)', color: '#fff' },
  spaeter: { background: 'var(--bg-app)', borderRadius: 8, padding: 24, marginTop: 16 },
  spaeterText: { fontSize: 14, color: 'var(--text-secondary)', margin: '0 0 16px', maxWidth: '60ch' },
  liste: { margin: 0, paddingLeft: 20, fontSize: 14, color: 'var(--text-secondary)' },
  fehler: { color: 'var(--status-danger-text)', fontSize: 14 },
  leise: { color: 'var(--text-tertiary)', fontSize: 14 },
  notiz: { fontSize: 14, color: 'var(--text-primary)', background: 'var(--bg-app)',
           padding: '10px 14px', borderRadius: 6, margin: '0 0 10px', lineHeight: 1.5 },
};
