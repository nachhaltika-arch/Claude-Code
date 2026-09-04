import { useState } from 'react';
import { Link } from 'react-router-dom';
import API_BASE_URL from '../../config';

/**
 * Was der Kunde an einem Mitwirkungspunkt tatsächlich tun kann (L-160/L-161).
 *
 * **Der Anlass, 04.09.2026.** „Was wir brauchen" war eine Liste zum Abhaken:
 * Der Kunde las, was fehlt, erledigte es woanders — per Mail, per Telefon —
 * und bestätigte hier, dass er es getan habe. Die Seite wusste vom eigentlichen
 * Vorgang nichts, und der Betrieb hatte zwei Wege für dieselbe Sache. David
 * beim Ansehen: „hier kann der Kunde nicht wirklich was machen".
 *
 * **Welche Handlung zu einem Punkt gehört, sagt der Katalog**, nicht diese
 * Datei: `services/mitwirkung.py` gibt je Punkt eine `aktion` und die Felder
 * dazu aus. Hier steht nur, wie eine Aktion aussieht. Eine Verzweigung nach
 * `M1`, `M3`, `M5` wäre der zweite Ort, an dem der Katalog gepflegt werden
 * müsste — und der erste, der beim nächsten Produkt vergessen wird.
 *
 * **Was hier bewusst fehlt: ein Feld für Zugangsdaten.** M1 und M9 handeln von
 * Zugängen zur Domainverwaltung und zum alten Redaktionssystem. Ein Feld dafür
 * wäre bequem und falsch — es lieferte uns fremde Passwörter im Klartext, mit
 * allem, was daran hängt: Sicherung, Protokoll, Löschfrist, Haftung. Der Kunde
 * entscheidet stattdessen, **wer einträgt**. Braucht es Zugang, melden wir uns
 * und zeigen ihm, wie er ihn delegiert, statt ihn zu verwahren.
 */
export default function MitwirkungAktion({ punkt, token, leadId, terminLink,
                                           eintragen, laeuft, neuLaden }) {
  const [werte, setWerte] = useState({});
  const [wahl, setWahl] = useState(punkt.wahlen?.[0]?.wert || '');
  const setzen = (name) => (e) => setWerte((w) => ({ ...w, [name]: e.target.value }));

  const absenden = () => eintragen(punkt.kennung, { ...werte, wahl });

  if (punkt.aktion === 'dateien') {
    return <Dateien punkt={punkt} token={token} leadId={leadId}
                    eintragen={eintragen} laeuft={laeuft} neuLaden={neuLaden} />;
  }

  if (punkt.aktion === 'termin') {
    return (
      <div style={S.block}>
        {terminLink ? (
          <>
            <p style={S.hinweis}>
              Suchen Sie sich einen Termin aus, der Ihnen passt — 90 Minuten,
              per Video oder Telefon.
            </p>
            {/* Ein Kalender bei einem Dritten: neues Fenster, und `noopener`,
                weil die fremde Seite sonst auf dieses hier zugreifen kann. */}
            <a href={terminLink} target="_blank" rel="noopener noreferrer"
               style={S.knopf}>Termin aussuchen</a>
            <button style={S.zweit} onClick={absenden} disabled={laeuft}>
              {laeuft ? 'Wird gespeichert …' : 'Termin steht schon'}
            </button>
          </>
        ) : (
          /* **Kein toter Knopf.** Ist kein Kalender hinterlegt, führte er ins
             Leere — und ein Link, der nichts tut, liest sich als Fehler des
             Nutzers. Dann sagt die Karte, dass wir uns melden. */
          <>
            <p style={S.hinweis}>
              Wir melden uns bei Ihnen und stimmen einen Termin ab.
            </p>
            <button style={S.knopf} onClick={absenden} disabled={laeuft}>
              {laeuft ? 'Wird gespeichert …' : 'Termin steht schon'}
            </button>
          </>
        )}
      </div>
    );
  }

  if (punkt.aktion === 'freigabe') {
    return (
      <div style={S.block}>
        <p style={S.hinweis}>
          Sobald wir Ihnen etwas vorgelegt haben, steht es unter „Freigaben" —
          eine Zeile je Seite, ein Klick zum Freigeben.
        </p>
        <Link to="/app/freigaben" style={S.knopf}>Zu den Freigaben</Link>
      </div>
    );
  }

  // Felder, Wahl, oder beides — die Reihenfolge kommt vom Server.
  return (
    <div style={S.block}>
      {punkt.wahlen?.length > 0 && (
        <fieldset style={S.gruppe}>
          <legend style={S.legende}>Wie möchten Sie es halten?</legend>
          {punkt.wahlen.map((w) => (
            <label key={w.wert} style={S.wahl}>
              <input type="radio" name={`wahl-${punkt.kennung}`} value={w.wert}
                     checked={wahl === w.wert} onChange={() => setWahl(w.wert)} />
              <span>{w.text}</span>
            </label>
          ))}
        </fieldset>
      )}

      {punkt.felder?.map((f) => (
        <label key={f.name} style={S.feld}>
          <span style={S.beschriftung}>{f.beschriftung}</span>
          <input value={werte[f.name] || ''} onChange={setzen(f.name)}
                 style={S.eingabe} autoComplete="off" />
        </label>
      ))}

      {punkt.aktion === 'domain' && wahl === 'selbst' && (
        <p style={S.hinweis}>
          Wir schicken Ihnen die einzutragenden Werte, sobald die Seite steht.
          <b> Ihre Zugangsdaten brauchen wir dafür nicht</b> — geben Sie sie
          uns bitte auch nicht über dieses Formular.
        </p>
      )}

      <label style={S.feld}>
        <span style={S.beschriftung}>Möchten Sie uns etwas dazu sagen? (freiwillig)</span>
        <textarea value={werte.hinweis || ''} onChange={setzen('hinweis')}
                  rows={2} style={{ ...S.eingabe, resize: 'vertical' }} />
      </label>

      <button style={S.knopf} onClick={absenden} disabled={laeuft}>
        {laeuft ? 'Wird gespeichert …' : 'Speichern und erledigen'}
      </button>
    </div>
  );
}

/**
 * Der echte Datei-Upload.
 *
 * **Er geht über `POST /api/files/mein/{lead_id}/upload`** — den Weg, den es
 * seit dem 26.08.2026 gibt und der den eigenen Betrieb prüft. Ein zweiter
 * Upload-Weg wäre eine zweite Stelle mit Größen- und Typprüfung, und eine
 * Grenze, die nur an einer von zwei Türen hängt, ist keine.
 */
function Dateien({ punkt, token, leadId, eintragen, laeuft, neuLaden }) {
  const [dateien, setDateien] = useState([]);
  const [laedt, setLaedt] = useState(false);
  const [fehler, setFehler] = useState('');

  const hochladen = async (auswahl) => {
    if (!auswahl?.length || !leadId) return;
    setLaedt(true);
    setFehler('');
    const angekommen = [];
    // Nacheinander statt alle auf einmal: Bei zehn Bildern über eine
    // Baustellenverbindung sagt ein Fehler dann, **welche** Datei es war.
    for (const datei of Array.from(auswahl)) {
      const paket = new FormData();
      paket.append('file', datei);
      paket.append('file_type', punkt.dateiart || 'sonstiges');
      paket.append('note', `${punkt.kennung} — ${punkt.titel}`);
      try {
        const res = await fetch(`${API_BASE_URL}/api/files/mein/${leadId}/upload`, {
          method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: paket,
        });
        const d = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(d.detail || `${datei.name} ließ sich nicht hochladen.`);
        angekommen.push(datei.name);
      } catch (e) {
        setFehler(e.message);
      }
    }
    setDateien((v) => [...v, ...angekommen]);
    setLaedt(false);
    if (neuLaden) neuLaden();
  };

  return (
    <div style={S.block}>
      <p style={S.hinweis}>
        Legen Sie ab, was Sie haben — Bilder, Logo, Dokumente. Bis 20 MB je
        Datei. Wir sagen Ihnen, wenn etwas nicht reicht.
      </p>

      <label style={S.ablage}>
        <input type="file" multiple style={{ display: 'none' }}
               onChange={(e) => { hochladen(e.target.files); e.target.value = ''; }} />
        <span style={S.ablageText}>
          {laedt ? 'Wird hochgeladen …' : 'Dateien auswählen'}
        </span>
      </label>

      {dateien.length > 0 && (
        <ul style={S.liste}>
          {dateien.map((n, i) => <li key={i}>{n} — angekommen</li>)}
        </ul>
      )}
      {fehler && <p style={S.fehler}>{fehler}</p>}

      {/* **Hochgeladen heißt nicht vollständig.** Nur der Kunde weiß, ob er
          alles hat; deshalb bleibt das Erledigt ein eigener Schritt. Aus ihm
          entsteht der Fristbeginn, und den darf keine Datei auslösen. */}
      <button style={S.knopf} onClick={() => eintragen(punkt.kennung, {
        hinweis: dateien.length ? `${dateien.length} Datei(en) hochgeladen` : '',
      })} disabled={laeuft || laedt}>
        {laeuft ? 'Wird gespeichert …' : 'Das war alles'}
      </button>
    </div>
  );
}

const S = {
  block: { display: 'flex', flexDirection: 'column', gap: 12, alignItems: 'flex-start' },
  hinweis: { fontSize: 14, color: 'var(--text-secondary)', margin: 0, lineHeight: 1.55, maxWidth: '58ch' },
  gruppe: { border: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 8 },
  legende: { fontSize: 13, fontWeight: 700, color: 'var(--text-secondary)', padding: 0, marginBottom: 4 },
  wahl: { display: 'flex', gap: 9, alignItems: 'flex-start', fontSize: 14, cursor: 'pointer', maxWidth: '54ch', lineHeight: 1.5 },
  feld: { display: 'flex', flexDirection: 'column', gap: 4, width: '100%', maxWidth: 420 },
  beschriftung: { fontSize: 13, fontWeight: 700, color: 'var(--text-secondary)' },
  eingabe: {
    font: 'inherit', fontSize: 14, padding: '9px 11px', borderRadius: 6,
    border: '1px solid var(--border-medium)', background: 'var(--bg-surface)',
    color: 'var(--text-primary)', width: '100%',
  },
  ablage: {
    display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
    padding: '18px 28px', borderRadius: 8, cursor: 'pointer',
    border: '2px dashed var(--border-medium)', background: 'var(--bg-app)',
  },
  ablageText: { fontSize: 14, fontWeight: 700, color: 'var(--text-secondary)' },
  liste: { margin: 0, paddingLeft: 20, fontSize: 13.5, color: 'var(--text-secondary)' },
  knopf: {
    fontWeight: 900, fontSize: 14, padding: '12px 20px', borderRadius: 6,
    border: 'none', cursor: 'pointer', background: 'var(--brand-primary)',
    color: '#fff', textDecoration: 'none', display: 'inline-block',
  },
  zweit: {
    font: 'inherit', fontSize: 13.5, fontWeight: 700, padding: '9px 16px',
    borderRadius: 6, cursor: 'pointer', background: 'transparent',
    color: 'var(--text-secondary)', border: '1px solid var(--border-medium)',
  },
  fehler: { color: 'var(--status-danger-text)', fontSize: 14, margin: 0 },
};
