import { useEffect, useState } from 'react';
import API_BASE_URL from '../../config';
import { datumKurz } from '../../utils/datum';

/**
 * Die Fünf-Werktage-Frist — dort, wo der Kunde freigibt (L-160, Rang 3).
 *
 * **Der Befund.** Der Angebotsfuß sagt zu: „Freigabe des Bauplans innerhalb
 * von 5 Werktagen nach Vorlage" — und wenn sie sich verzögert, ruht die
 * Bauzeit. Auf dem Bildschirm, auf dem der Kunde tatsächlich freigibt, stand
 * die Frist **nirgends**. Er entschied, ohne zu wissen, dass an seiner
 * Entscheidung ein Termin hängt.
 *
 * **Gerechnet wird nichts hier.** Vorlagedatum, Frist und Ruhezeit kommen
 * fertig aus `/api/portal/mitwirkung` (`services/bauzeit.py`, L-166). Eine
 * zweite Rechnung in JavaScript wäre der zweite Ort, an dem die Auslegung des
 * Angebotstexts gepflegt werden müsste — und der Bildschirm sagte eines Tages
 * etwas anderes als die Akte.
 *
 * **Was hier bewusst *nicht* steht:** eine Zuordnung der beiden
 * Mitwirkungspunkte M7 und M8 zu den elf Projektfreigaben. „Seitenstruktur &
 * Sitemap" ist dem Bauplan nahe, aber nicht dasselbe — der Bauplan ist ein
 * eigenes Freigabedokument. Eine erfundene Zuordnung wäre schlechter als
 * keine: Sie hängte eine Vertragsfrist an einen Haken, der sie nicht meint.
 * Der Block nennt die Fristen deshalb als eigene Einheit über der Liste. Die
 * saubere Verbindung gehört zu K4/L-168 — dort, wo der Ablauf ohnehin aus
 * dem Produkt abgeleitet werden muss.
 */
export default function Freigabefrist({ token }) {
  const [frist, setFrist] = useState(null);

  useEffect(() => {
    if (!token) return;
    let abgebrochen = false;
    fetch(`${API_BASE_URL}/api/portal/mitwirkung`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (!abgebrochen) setFrist(d?.frist || null); })
      /* Der Block ergänzt die Seite, er trägt sie nicht — ein Ladefehler
         lässt ihn weg, statt einen Fehlerkasten über die Freigaben zu setzen. */
      .catch(() => {});
    return () => { abgebrochen = true; };
  }, [token]);

  const vorgelegt = (frist?.freigaben || []).filter(f => f.vorgelegt_am);
  if (!frist) return null;

  return (
    <aside style={S.rahmen}>
      <p style={S.kopf}>Ihre Fristen aus dem Vertrag</p>
      <p style={S.satz}>
        Für den Bauplan und für die Texte haben Sie je{' '}
        <b>{frist.freigabefrist_werktage} Werktage</b> nach Vorlage. Was darüber
        hinausgeht, lässt die Bauzeit ruhen — der zugesagte Fertigstellungstag
        verschiebt sich dann um dieselbe Zahl.
      </p>

      {vorgelegt.length === 0 ? (
        <p style={S.leise}>Zurzeit liegt Ihnen nichts zur Freigabe vor.</p>
      ) : (
        <ul style={S.liste}>
          {vorgelegt.map(f => (
            <li key={f.kennung} style={f.werktage > 0 && f.laeuft_noch ? S.warn : S.ruhig}>
              <b>{f.titel}</b> — vorgelegt am {datumKurz(f.vorgelegt_am)},{' '}
              {f.freigegeben_am
                ? `freigegeben am ${datumKurz(f.freigegeben_am)}${
                    f.werktage > 0
                      ? ` · ${f.werktage} ${f.werktage === 1 ? 'Werktag' : 'Werktage'} über der Frist`
                      : ' · innerhalb der Frist'}`
                : `bitte bis ${datumKurz(f.frist_bis)} freigeben${
                    f.werktage > 0
                      ? ` · überschritten, die Bauzeit ruht seit ${f.werktage} ${f.werktage === 1 ? 'Werktag' : 'Werktagen'}`
                      : ''}`}
            </li>
          ))}
        </ul>
      )}

      {frist.ende && (
        <p style={S.ende}>
          Zugesagt fertig: <b>{datumKurz(frist.ende)}</b>
          {frist.pause_werktage > 0 && ` — ursprünglich ${datumKurz(frist.ende_ohne_pause)}.`}
        </p>
      )}
    </aside>
  );
}

/* Status ist immer Farbe UND Text — eine überschrittene Frist steht
   ausgeschrieben da und nicht nur in Warnfarbe. */
const S = {
  rahmen: { background: 'var(--bg-app)', border: '1px solid var(--border-light)', borderLeft: '3px solid var(--brand-primary)', borderRadius: 8, padding: '16px 20px', marginBottom: 16 },
  kopf: { fontSize: 12, fontWeight: 900, letterSpacing: '.04em', textTransform: 'uppercase', color: 'var(--text-tertiary)', margin: '0 0 10px' },
  satz: { fontSize: 13, lineHeight: 1.6, color: 'var(--text-secondary)', margin: '0 0 12px', maxWidth: '62ch' },
  liste: { margin: '0 0 12px', paddingLeft: 20, fontSize: 13, display: 'flex', flexDirection: 'column', gap: 8 },
  ruhig: { color: 'var(--text-secondary)', lineHeight: 1.6 },
  warn: { color: 'var(--status-warning-text)', fontWeight: 700, lineHeight: 1.6 },
  ende: { fontSize: 13, color: 'var(--text-primary)', margin: 0 },
  leise: { fontSize: 13, color: 'var(--text-tertiary)', margin: '0 0 12px' },
};
