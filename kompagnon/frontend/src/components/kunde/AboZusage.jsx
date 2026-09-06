import { useEffect, useState } from 'react';
import API_BASE_URL from '../../config';

/**
 * Was an dieser Stelle im Pflege-Abo zugesagt ist (L-160, Rang 3).
 *
 * **Der Befund vom 04.09.2026.** Zwölf Positionen, für die der Betrieb 79 €
 * bzw. 149 € netto **monatlich** zahlt — und keine einzige war im Konto
 * abrufbar. Am schärfsten bei der Reaktionszeit: „Antwort innerhalb von 4
 * Stunden" steht im Datenblatt, der Kunde tippt sein Ticket und weiß nicht,
 * wann er mit uns rechnen darf. Eine Leistung, die nirgends benannt ist, wird
 * nicht wahrgenommen und trotzdem bezahlt.
 *
 * **Warum eine Komponente und nicht ein Satz je Seite.** Der Katalog führt zu
 * jeder Position einen `ort` — Support, Änderungen, Bericht, Rücksicherung.
 * Diese Komponente zeigt genau die Positionen dieses Ortes; wer eine Zusage
 * ändert, ändert sie im Datenblatt und im Katalog, nicht an vier Bildschirmen.
 *
 * **Ohne laufendes Abo steht hier nichts.** Kein Basic-Umfang als Vorgabe:
 * Wer keinen Pflegevertrag hat, sähe sonst Zusagen, die niemand gegeben hat.
 */
export default function AboZusage({ token, ort, zeigeGrenzen = false }) {
  const [daten, setDaten] = useState(null);

  useEffect(() => {
    if (!token) return;
    let abgebrochen = false;
    fetch(`${API_BASE_URL}/api/portal/leistungen`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (!abgebrochen) setDaten(d); })
      /* Ein Fehler beim Laden lässt den Block weg — er ergänzt die Seite,
         er trägt sie nicht. Ein Fehlerkasten über dem Ticketformular sähe
         aus, als sei der Support gestört. */
      .catch(() => {});
    return () => { abgebrochen = true; };
  }, [token]);

  const positionen = (daten?.positionen || []).filter(p => p.ort === ort);
  if (!daten?.produkt || positionen.length === 0) return null;

  return (
    <aside style={S.rahmen}>
      <p style={S.kopf}>In Ihrem {daten.produkt === 'ABO-PRO' ? 'Pflege Pro' : 'Pflege Basic'} enthalten</p>
      <ul style={S.liste}>
        {positionen.map(p => (
          <li key={p.nummer} style={S.zeile}>
            <b style={S.titel}>{p.titel}</b>
            <span style={S.warum}>{p.warum}</span>
            {/* Der Wortlaut aus dem Vertrag daneben — die Stelle, an der ein
                Kunde nachschlagen kann, was genau zugesagt ist. */}
            <span style={S.vertrag}>{p.vertragstext} · {p.frequenz}</span>
          </li>
        ))}
      </ul>

      {/* **Was nicht enthalten ist, gehört daneben** — und zwar dort, wo der
          Kunde etwas anfordert. „90 Minuten Änderungen" liest sich für
          manchen als „ihr macht alles"; die Zeile darunter verhindert das
          Gespräch, das mit „das dachte ich wäre dabei" beginnt. Beide Sätze
          stehen ohnehin im Vertrag. Ob sie erscheinen, entscheidet die Seite:
          Am Support wären sie ein Vorwurf, an den Änderungen sind sie eine
          Auskunft. */}
      {zeigeGrenzen && daten.verfall_hinweis && (
        <p style={S.grenze}>{daten.verfall_hinweis}</p>
      )}
      {zeigeGrenzen && daten.nicht_enthalten?.length > 0 && (
        <p style={S.grenze}>
          <b>Nicht enthalten:</b> {daten.nicht_enthalten.join(', ')}. Sagen Sie uns
          trotzdem Bescheid — wir machen Ihnen dafür ein Angebot.
        </p>
      )}
    </aside>
  );
}

const S = {
  rahmen: { background: 'var(--bg-app)', border: '1px solid var(--border-subtle, var(--border-light))', borderLeft: '3px solid var(--brand-primary)', borderRadius: 8, padding: '16px 20px', marginBottom: 16 },
  kopf: { fontSize: 12, fontWeight: 900, letterSpacing: '.04em', textTransform: 'uppercase', color: 'var(--text-tertiary)', margin: '0 0 10px' },
  liste: { listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 12 },
  zeile: { display: 'flex', flexDirection: 'column', gap: 2 },
  titel: { fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' },
  warum: { fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5, maxWidth: '58ch' },
  vertrag: { fontSize: 12, color: 'var(--text-tertiary)', marginTop: 2 },
  grenze: { fontSize: 12, color: 'var(--text-tertiary)', lineHeight: 1.6, margin: '12px 0 0', maxWidth: '62ch' },
};
