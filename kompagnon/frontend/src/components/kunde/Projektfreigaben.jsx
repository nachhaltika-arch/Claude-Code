/**
 * Die elf Freigaben des Projekts — vom Kunden erteilt, nicht von uns.
 *
 * **Der Befund (26.08.2026, L-105).** Diese elf Punkte — von
 * „Auftragserteilung & Anzahlung" über „Impressum & Datenschutz geprüft" bis
 * „Finale Abnahme & Go-Live Freigabe" — hakte bisher der **Innendienst** ab.
 * `BriefingTab.toggleFreigabe` schreibt sie über die Innendienst-Route und
 * trägt fest `durch: "KOMPAGNON"` ein.
 *
 * Der Endpunkt für den Kunden war genau dafür gebaut — seine Adresse als
 * Urheber, Datum und Uhrzeit, **unwiderruflich** — und wurde von nirgendwo
 * aufgerufen.
 *
 * **Eine Abnahme, die der Auftragnehmer selbst abhakt, ist keine Abnahme.**
 * Bei „Finale Abnahme" und „Impressum & Datenschutz" ist das im Streitfall
 * der Unterschied zwischen einem Nachweis und einer Behauptung.
 *
 * **Der Innendienst behält seinen Weg** — für den Fall, dass eine Freigabe
 * telefonisch oder per Mail kommt. Am Eintrag steht dann „KOMPAGNON", und
 * dieser Bildschirm zeigt das auch so an: Wer freigegeben hat, ist sichtbar.
 *
 * **Warum eine Rückfrage vor dem Klick.** Unwiderruflich heißt
 * unwiderruflich; ein versehentlicher Klick auf „Finale Abnahme" lässt sich
 * nicht zurücknehmen. Die Rückfrage nennt den Punkt beim Namen, statt nur
 * „Sind Sie sicher?" zu fragen.
 */
import { useCallback, useEffect, useState } from 'react';
import API_BASE_URL from '../../config';

/**
 * Die elf Punkte in der Reihenfolge des Ablaufs.
 *
 * **Dieselbe Liste steht in `BriefingTab.jsx`** — bewusst, denn sie ist die
 * Sprache gegenüber dem Kunden und nicht die Wahrheit über einen Datensatz.
 * Der `key` ist die Verbindung; wer einen Punkt umbenennt, muss beide
 * Stellen anfassen, und ein Test hält fest, dass die Schlüssel gleich sind.
 */
export const FREIGABEN = [
  { key: 'auftragserteilung', label: 'Auftragserteilung & Anzahlung', phase: '1.0' },
  { key: 'assets_geliefert', label: 'Logo, Fotos & Texte eingegangen', phase: '1.2' },
  { key: 'sitemap_freigabe', label: 'Seitenstruktur & Sitemap freigegeben', phase: '2.0' },
  { key: 'design_entwurf', label: 'Design-Entwurf Startseite freigegeben', phase: '3.0' },
  { key: 'design_final', label: 'Finales Design aller Seiten freigegeben', phase: '3.2' },
  { key: 'content_freigabe', label: 'Alle Inhalte geprüft & freigegeben', phase: '4.0' },
  { key: 'testphase', label: 'Testversion auf Staging geprüft', phase: '5.0' },
  { key: 'rechtliches', label: 'Impressum & Datenschutz geprüft', phase: '5.1' },
  { key: 'google_business', label: 'Google Business Profil aktualisiert', phase: '6.0' },
  { key: 'abnahme_go_live', label: 'Finale Abnahme & Go-Live Freigabe', phase: '6.2' },
  { key: 'einweisung', label: 'Einweisung CMS / Website-Pflege', phase: '7.0' },
];

export default function Projektfreigaben({ leadId, token }) {
  const [stand, setStand] = useState(null);
  const [fehler, setFehler] = useState('');
  const [frage, setFrage] = useState(null);   // der Punkt, der bestätigt wird
  const [laeuft, setLaeuft] = useState(false);

  const kopf = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const laden = useCallback(async () => {
    if (!leadId) return;
    setFehler('');
    try {
      const antwort = await fetch(`${API_BASE_URL}/api/briefings/mein/${leadId}`, { headers: kopf });
      if (!antwort.ok) throw new Error(`Status ${antwort.status}`);
      const daten = await antwort.json();
      setStand(daten.freigaben || {});
    } catch (e) {
      // Kein leerer Stand als Rückfall: „nichts freigegeben" wäre eine
      // Aussage, und geladen werden konnte gar nichts.
      setStand(null);
      setFehler(`Der Stand konnte nicht geladen werden (${e.message}).`);
    }
  }, [leadId, token]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { laden(); }, [laden]);

  async function erteilen(eintrag) {
    setLaeuft(true); setFehler('');
    try {
      const antwort = await fetch(`${API_BASE_URL}/api/briefings/${leadId}/freigabe`, {
        method: 'PATCH', headers: kopf, body: JSON.stringify({ key: eintrag.key }),
      });
      const daten = await antwort.json().catch(() => ({}));
      if (!antwort.ok) throw new Error(daten.detail || `Status ${antwort.status}`);
      setFrage(null);
      await laden();
    } catch (e) {
      setFehler(`Die Freigabe wurde nicht gespeichert (${e.message}).`);
    } finally {
      setLaeuft(false);
    }
  }

  if (!leadId) return null;

  return (
    <section style={{
      background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
      borderRadius: 'var(--radius-xl)', padding: '18px 20px',
      display: 'flex', flexDirection: 'column', gap: 14, marginTop: 20,
    }}>
      <div>
        <h2 style={{ margin: 0, fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
          Freigaben zum Projektablauf
        </h2>
        <p style={{ margin: '6px 0 0', fontSize: 12, lineHeight: 1.55, color: 'var(--text-tertiary)' }}>
          Diese Punkte begleiten Ihr Projekt von der Beauftragung bis zur
          Übergabe. <strong>Eine erteilte Freigabe lässt sich nicht
          zurücknehmen</strong> — deshalb fragen wir vor jedem Klick noch
          einmal nach.
        </p>
      </div>

      {stand === null && !fehler && (
        <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>Wird geladen …</div>
      )}

      {stand !== null && (
        <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 6 }}>
          {FREIGABEN.map((eintrag) => {
            const erteilt = stand[eintrag.key]?.datum;
            const durch = stand[eintrag.key]?.durch;
            const vonUns = erteilt && durch === 'KOMPAGNON';

            return (
              <li key={eintrag.key} style={{
                display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap',
                padding: '10px 12px', borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-light)',
                background: erteilt ? 'var(--status-success-bg)' : 'transparent',
              }}>
                <span style={{ fontSize: 12, color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', flexShrink: 0 }}>
                  {eintrag.phase}
                </span>
                <span style={{
                  flex: 1, minWidth: 180, fontSize: 13,
                  color: erteilt ? 'var(--status-success-text)' : 'var(--text-primary)',
                  fontWeight: erteilt ? 600 : 400,
                }}>
                  {eintrag.label}
                </span>

                {erteilt ? (
                  <span style={{ fontSize: 12, color: 'var(--text-tertiary)', textAlign: 'right' }}>
                    {stand[eintrag.key].datum}
                    {stand[eintrag.key].uhrzeit ? ` · ${stand[eintrag.key].uhrzeit}` : ''}
                    <br />
                    {/* Wer freigegeben hat, steht da — auch wenn wir es
                      * waren. Sonst sähe eine telefonisch übermittelte
                      * Freigabe aus wie eine, die der Kunde selbst geklickt
                      * hat. */}
                    {vonUns ? 'durch KOMPAGNON erfasst' : `durch ${durch || 'Sie'}`}
                  </span>
                ) : (
                  <button type="button" onClick={() => setFrage(eintrag)} style={{
                    padding: '6px 14px', border: '1px solid var(--brand-primary)',
                    borderRadius: 'var(--radius-md)', background: 'transparent',
                    color: 'var(--brand-primary-mid, var(--brand-primary))',
                    fontSize: 12, fontWeight: 600, cursor: 'pointer',
                    fontFamily: 'var(--font-sans)', flexShrink: 0,
                  }}>
                    Freigeben
                  </button>
                )}
              </li>
            );
          })}
        </ul>
      )}

      {/* Die Rueckfrage nennt den Punkt beim Namen. „Sind Sie sicher?" ohne
        * Gegenstand ist eine Frage, die niemand liest. */}
      {frage && (
        <div role="alertdialog" aria-label="Freigabe bestätigen" style={{
          padding: '14px 16px', borderRadius: 'var(--radius-md)',
          background: 'var(--status-warning-bg)', color: 'var(--status-warning-text)',
          fontSize: 13, lineHeight: 1.55,
        }}>
          <div style={{ marginBottom: 10 }}>
            Möchten Sie <strong>„{frage.label}"</strong> freigeben? Das lässt
            sich nicht zurücknehmen; Ihr Name und der Zeitpunkt werden
            festgehalten.
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button type="button" disabled={laeuft} onClick={() => erteilen(frage)} style={{
              padding: '7px 16px', border: 'none', borderRadius: 'var(--radius-md)',
              background: 'var(--brand-primary)', color: 'var(--text-on-brand)',
              fontSize: 12, fontWeight: 700, cursor: laeuft ? 'default' : 'pointer',
              opacity: laeuft ? 0.6 : 1, fontFamily: 'var(--font-sans)',
            }}>
              {laeuft ? 'Wird gespeichert …' : 'Ja, freigeben'}
            </button>
            <button type="button" onClick={() => setFrage(null)} style={{
              padding: '7px 16px', border: '1px solid currentColor',
              borderRadius: 'var(--radius-md)', background: 'transparent',
              color: 'inherit', fontSize: 12, cursor: 'pointer',
              fontFamily: 'var(--font-sans)',
            }}>
              Abbrechen
            </button>
          </div>
        </div>
      )}

      {fehler && (
        <div role="alert" style={{
          fontSize: 12, padding: '8px 12px', borderRadius: 'var(--radius-md)',
          background: 'var(--status-error-bg)', color: 'var(--status-error-text)',
        }}>
          {fehler}
        </div>
      )}
    </section>
  );
}
