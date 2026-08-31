/**
 * Bilder und Dokumente des eigenen Betriebs.
 *
 * **Warum das zum Briefing gehört (26.08.2026).** Ein Briefing ohne Logo und
 * Fotos ist eine Beschreibung von Bildern, die niemand hat. Den Weg gab es
 * für den Innendienst und für das QR-Portal (per Token) — nur nicht für den
 * Kunden, der sich anmeldet.
 *
 * **Was hier bewusst sichtbar ist:** wer die Datei beigesteuert hat. Der
 * Kunde sieht auch, was wir hochgeladen haben — sonst wirkte die Liste
 * lückenhaft, und er lüde ein zweites Mal hoch, was längst da ist.
 *
 * **Was hier bewusst fehlt: Löschen.** Eine Datei, die im Projekt schon
 * verwendet wird, verschwände damit unter der Hand. Wer etwas zurückziehen
 * will, schreibt es in den Chat daneben — ein Satz an den Betreuer ist der
 * kürzere Weg als ein Knopf, dessen Folgen niemand übersieht.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import API_BASE_URL from '../../config';

/** Wie der Server sie einsortiert — dieselben Werte wie in `files.py`. */
const ARTEN = [
  { wert: 'logo', label: 'Logo' },
  { wert: 'foto', label: 'Foto' },
  { wert: 'text', label: 'Text' },
  { wert: 'sonstiges', label: 'Sonstiges' },
];

const HOECHSTGROESSE = 20 * 1024 * 1024;

/** Erlaubt laut `ALLOWED_EXTENSIONS` — ohne `zugangsdaten`. */
const ERLAUBT = 'jpg,jpeg,png,gif,pdf,doc,docx,txt,zip,svg,ai,eps';

function groesse(bytes) {
  if (!bytes && bytes !== 0) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function MeineDateien({ leadId, token }) {
  const [dateien, setDateien] = useState(null);
  const [art, setArt] = useState('logo');
  const [fehler, setFehler] = useState('');
  const [hinweis, setHinweis] = useState('');
  const [laeuft, setLaeuft] = useState(false);
  const eingabe = useRef(null);

  const authKopf = token ? { Authorization: `Bearer ${token}` } : {};

  const laden = useCallback(async () => {
    setFehler('');
    try {
      const antwort = await fetch(`${API_BASE_URL}/api/files/mein/${leadId}`, { headers: authKopf });
      if (!antwort.ok) throw new Error(`Status ${antwort.status}`);
      const daten = await antwort.json();
      setDateien(Array.isArray(daten) ? daten : []);
    } catch (e) {
      setDateien([]);
      setFehler(`Die Liste konnte nicht geladen werden (${e.message}).`);
    }
  }, [leadId, token]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { laden(); }, [laden]);

  async function hochladen(datei) {
    if (!datei) return;

    // Vor dem Senden prüfen, nicht danach: 20 MB durch die Leitung zu
    // schicken, um „zu groß" zu hören, ist auf dem Telefon eine Zumutung.
    // Der Server prüft trotzdem — er ist die Stelle, die es verbindlich weiß.
    if (datei.size > HOECHSTGROESSE) {
      setFehler(`„${datei.name}" ist ${groesse(datei.size)} groß. Erlaubt sind 20 MB.`);
      return;
    }

    setLaeuft(true); setFehler(''); setHinweis('');
    const paket = new FormData();
    paket.append('file', datei);
    paket.append('file_type', art);
    paket.append('note', '');

    try {
      const antwort = await fetch(`${API_BASE_URL}/api/files/mein/${leadId}/upload`, {
        method: 'POST', headers: authKopf, body: paket,
      });
      const daten = await antwort.json().catch(() => ({}));
      if (!antwort.ok) throw new Error(daten.detail || `Status ${antwort.status}`);
      setHinweis(`„${daten.original_filename}" ist angekommen.`);
      await laden();
    } catch (e) {
      setFehler(`Hochladen fehlgeschlagen (${e.message}).`);
    } finally {
      setLaeuft(false);
      if (eingabe.current) eingabe.current.value = '';
    }
  }

  return (
    <section style={{
      background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
      borderRadius: 'var(--radius-xl)', padding: '18px 20px',
      display: 'flex', flexDirection: 'column', gap: 14,
    }}>
      <div>
        <h2 style={{ margin: 0, fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
          Bilder und Dokumente
        </h2>
        <p style={{ margin: '6px 0 0', fontSize: 12, lineHeight: 1.55, color: 'var(--text-tertiary)' }}>
          Logo, Fotos vom Betrieb, Referenzen, Unterlagen. Bis 20 MB je Datei;
          Bilder, PDF, Word, Text und ZIP.
        </p>
      </div>

      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span style={{ fontSize: 12, fontWeight: 600 }}>Wofür ist die Datei?</span>
          <select value={art} onChange={(e) => setArt(e.target.value)} style={feld}>
            {ARTEN.map((a) => <option key={a.wert} value={a.wert}>{a.label}</option>)}
          </select>
        </label>

        <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span style={{ fontSize: 12, fontWeight: 600 }}>Datei wählen</span>
          <input
            ref={eingabe}
            type="file"
            accept={ERLAUBT.split(',').map((e) => `.${e}`).join(',')}
            aria-label="Datei zum Hochladen wählen"
            disabled={laeuft}
            onChange={(e) => hochladen(e.target.files?.[0])}
            style={{ ...feld, padding: '6px 8px' }}
          />
        </label>

        {laeuft && (
          <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>Wird hochgeladen …</span>
        )}
      </div>

      {dateien === null && (
        <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>Wird geladen …</div>
      )}
      {dateien?.length === 0 && (
        <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
          Noch nichts hochgeladen.
        </div>
      )}
      {dateien?.length > 0 && (
        <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 6 }}>
          {dateien.map((d) => (
            <li key={d.id} style={{
              display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap',
              padding: '8px 12px', borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-light)', fontSize: 12,
            }}>
              <a
                href={`${API_BASE_URL}/api/files/mein/download/${d.id}`}
                target="_blank" rel="noopener noreferrer"
                style={{ fontWeight: 600, color: 'var(--brand-primary-mid, var(--brand-primary))' }}
              >
                {d.original_filename}
              </a>
              <span style={{ color: 'var(--text-tertiary)' }}>
                {d.file_type} · {groesse(d.file_size)}
              </span>
              <span style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--text-tertiary)' }}>
                {d.uploaded_by_role === 'kunde' ? 'von Ihnen' : 'von KOMPAGNON'}
              </span>
            </li>
          ))}
        </ul>
      )}

      {fehler && <div role="alert" style={meldung('error')}>{fehler}</div>}
      {hinweis && <div style={meldung('success')}>{hinweis}</div>}
    </section>
  );
}

const feld = {
  padding: '8px 10px', fontSize: 13,
  borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)',
  background: 'var(--bg-surface)', color: 'var(--text-primary)',
  fontFamily: 'var(--font-sans)',
};

const meldung = (art) => ({
  fontSize: 12, lineHeight: 1.5, padding: '8px 12px',
  borderRadius: 'var(--radius-md)',
  background: `var(--status-${art}-bg)`,
  color: `var(--status-${art}-text)`,
});
