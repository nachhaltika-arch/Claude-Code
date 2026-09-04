/**
 * Drei Website-Entwürfe erzeugen und auswählen (L-105, Phase 3).
 *
 * **Warum es diesen Schritt gibt.** Die Erzeugung stand seit Langem im
 * Backend — 248 Zeilen in `routers/projects_versionen.py` —, und das
 * Kundenportal ist darauf fertig eingerichtet: „🎨 Ihre 3 Website-Entwürfe
 * sind bereit! — Wählen Sie Ihren Favoriten", mit Vorschau je Entwurf.
 *
 * **Nur konnte kein einziger Entwurf entstehen.** `POST /generate-versions`
 * ist der einzige Schreiber von `website_versions`, und im ganzen Bestand
 * kam die Adresse nur in ihrer eigenen Definition vor. Gefunden am
 * 01.09.2026 beim Durchgehen der Endpunkte ohne Aufrufer.
 *
 * **Warum es niemandem auffiel:** Das Portal hat den ehrlichen Riegel
 * `if (versions.length === 0) return null` — der Abschnitt versteckt sich,
 * wenn nichts da ist. Der Kunde sah nie ein leeres Versprechen, und genau
 * deshalb merkte niemand, dass er es nie sehen würde. Ein gut versteckter
 * Mangel ist schwerer zu finden als ein sichtbarer.
 *
 * **Der Knopf sagt, was er kostet.** Die Erzeugung ruft das Modell; das
 * Guthaben ist knapp und in L-58 benannt. Ein Knopf, der ungefragt Geld
 * ausgibt, wird einmal aus Versehen gedrückt und danach gemieden.
 *
 * **Auswählen darf auch der Innendienst.** Normalerweise wählt der Kunde im
 * Portal — aber am Telefon fällt die Entscheidung oft mündlich, und dann
 * soll sie hier eingetragen werden können, statt den Kunden zu bitten, sich
 * einzuloggen.
 */
import { useCallback, useEffect, useState } from 'react';
import API_BASE_URL from '../../config';

export function EntwuerfeEmbed({ project, headers }) {
  const [versionen, setVersionen] = useState(null);
  const [laeuft, setLaeuft] = useState(false);
  const [fehler, setFehler] = useState('');

  const projektId = project?.id;

  const laden = useCallback(async () => {
    if (!projektId) return;
    try {
      const antwort = await fetch(
        `${API_BASE_URL}/api/projects/${projektId}/versions`, { headers });
      if (!antwort.ok) throw new Error(`Status ${antwort.status}`);
      setVersionen(await antwort.json());
      setFehler('');
    } catch (e) {
      // Kein Rückfall auf „keine Entwürfe": Das wäre eine Aussage über den
      // Bestand, wo gar nicht gelesen werden konnte — und der Knopf darunter
      // hiesse dann „erzeugen", obwohl vielleicht längst drei da sind.
      setVersionen(null);
      setFehler(`Die Entwürfe konnten nicht geladen werden (${e.message}).`);
    }
  }, [projektId]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { laden(); }, [laden]);

  async function erzeugen() {
    setLaeuft(true); setFehler('');
    try {
      const antwort = await fetch(
        `${API_BASE_URL}/api/projects/${projektId}/generate-versions`,
        { method: 'POST', headers });
      const d = await antwort.json().catch(() => ({}));
      if (!antwort.ok) throw new Error(d.detail || `Status ${antwort.status}`);
      await laden();
    } catch (e) {
      setFehler(`Die Erzeugung ist fehlgeschlagen (${e.message}). `
                + 'Es wurde nichts gespeichert.');
    } finally {
      setLaeuft(false);
    }
  }

  async function auswaehlen(versionId) {
    setLaeuft(true); setFehler('');
    try {
      const antwort = await fetch(
        `${API_BASE_URL}/api/projects/${projektId}/versions/${versionId}/select`,
        { method: 'POST', headers });
      if (!antwort.ok) throw new Error(`Status ${antwort.status}`);
      await laden();
    } catch (e) {
      setFehler(`Die Auswahl wurde nicht gespeichert (${e.message}).`);
    } finally {
      setLaeuft(false);
    }
  }

  if (!projektId) return null;

  const liste = Array.isArray(versionen) ? versionen : [];
  const gewaehlt = liste.find((v) => v.selected);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div>
        <h3 style={{ margin: 0, fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>
          Drei Entwürfe für die Startseite
        </h3>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: '4px 0 0', lineHeight: 1.5 }}>
          Der Kunde wählt seinen Favoriten im Portal. Bis dahin sieht er den
          Abschnitt gar nicht — ohne Entwürfe bleibt er ausgeblendet.
        </p>
      </div>

      {fehler && (
        <div role="alert" style={alarm}>{fehler}</div>
      )}

      {versionen !== null && liste.length === 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'flex-start' }}>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
            Es gibt noch keine Entwürfe. Die Erzeugung liest Briefing,
            Inspirationsadressen und Vorlagen und ruft dafür das Modell —
            <b> sie kostet Guthaben</b> und dauert etwa eine Minute.
          </p>
          <button type="button" onClick={erzeugen} disabled={laeuft} style={hauptknopf(laeuft)}>
            {laeuft ? 'Entwürfe entstehen …' : 'Drei Entwürfe erzeugen'}
          </button>
        </div>
      )}

      {gewaehlt && (
        <div style={{
          fontSize: 13, padding: '9px 12px', borderRadius: 'var(--radius-md)',
          background: 'var(--status-success-bg)', color: 'var(--status-success-text)',
        }}>
          Version {gewaehlt.version_label} ist ausgewählt — die Umsetzung baut darauf auf.
        </div>
      )}

      {liste.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 12 }}>
          {liste.map((v) => {
            let grund = {};
            try { grund = JSON.parse(v.ki_reasoning || '{}'); } catch { grund = {}; }
            return (
              <div key={v.id} style={{
                border: v.selected ? '2px solid var(--brand-primary)' : '1px solid var(--border-light)',
                borderRadius: 'var(--radius-md)', overflow: 'hidden',
                background: 'var(--bg-surface)',
              }}>
                <div style={{ height: 170, overflow: 'hidden', position: 'relative', background: 'var(--bg-app)' }}>
                  <iframe
                    title={`Entwurf ${v.version_label}`}
                    src={`${API_BASE_URL}/api/projects/${projektId}/versions/${v.id}/preview`}
                    style={{
                      width: '250%', height: '425px', transform: 'scale(0.4)',
                      transformOrigin: 'top left', border: 'none', pointerEvents: 'none',
                    }}
                  />
                </div>
                <div style={{ padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: 6 }}>
                  <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--brand-primary)', textTransform: 'uppercase', letterSpacing: '.06em' }}>
                    Version {v.version_label}
                  </div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                    {grund.titel || v.template_name || `Entwurf ${v.version_label}`}
                  </div>
                  {grund.beschreibung && (
                    <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.45 }}>
                      {grund.beschreibung}
                    </div>
                  )}
                  {!v.selected && (
                    <button type="button" onClick={() => auswaehlen(v.id)}
                      disabled={laeuft} style={nebenknopf}>
                      Als gewählt eintragen
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {liste.length > 0 && (
        <button type="button" onClick={erzeugen} disabled={laeuft}
          style={{ ...nebenknopf, alignSelf: 'flex-start' }}
          title="Ersetzt die vorhandenen Entwürfe und kostet erneut Guthaben">
          {laeuft ? 'Entwürfe entstehen …' : 'Neu erzeugen (ersetzt die bisherigen)'}
        </button>
      )}
    </div>
  );
}

const alarm = {
  fontSize: 13, padding: '9px 12px', borderRadius: 'var(--radius-md)',
  background: 'var(--status-error-bg)', color: 'var(--status-error-text)',
};

const hauptknopf = (laeuft) => ({
  padding: '9px 16px', fontSize: 13, fontWeight: 700,
  borderRadius: 'var(--radius-md)', border: 'none',
  background: 'var(--brand-primary)', color: 'var(--text-on-brand)',
  fontFamily: 'var(--font-sans)', cursor: laeuft ? 'default' : 'pointer',
  opacity: laeuft ? 0.6 : 1,
});

const nebenknopf = {
  padding: '6px 12px', fontSize: 12, fontWeight: 600,
  borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)',
  background: 'var(--bg-surface)', color: 'var(--text-primary)',
  fontFamily: 'var(--font-sans)', cursor: 'pointer',
};
