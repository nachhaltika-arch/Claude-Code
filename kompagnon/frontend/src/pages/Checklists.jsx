import React, { useCallback, useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import API_BASE_URL from '../config';
import { useAuth } from '../context/AuthContext';
import SeitenTitel from '../components/ui/SeitenTitel';
import { aufTaste } from '../utils/tastaturBedienung';

/**
 * Die Projektchecklisten — 67 Punkte über sieben Phasen (L-105).
 *
 * **Was hier vorher stand.** Eine Attrappe: ein Symbol, die Zeile
 * „54 Items across 7 Phasen — In Entwicklung", und kein einziger Aufruf.
 * Dabei war alles andere längst da:
 *
 *   - `seed_checklists.create_project_checklists` legt die Punkte an — und
 *     der Zahlungspfad ruft sie bei **jedem Kauf** auf. In der Datenbank
 *     stehen also für jedes verkaufte Projekt 67 Zeilen.
 *   - `GET /api/projects/{id}/checklist` gibt sie heraus.
 *   - `PATCH /api/projects/{id}/checklist/{item_key}` hakt einen ab.
 *
 * Drei von vier Teilen gebaut, das vierte eine Attrappe. Und die Attrappe
 * behauptete **54**, während die Vorlage **67** Punkte führt — eine Zahl,
 * die niemand nachgerechnet hat.
 *
 * **Die Punkte werden nicht hier definiert.** Sie kommen aus der Antwort des
 * Servers, samt `is_critical` und `responsible`. Eine zweite Liste im
 * Frontend wäre die nächste Zahl, die auseinanderläuft.
 */

//: Die Phasennamen stehen hier, weil die Schnittstelle nur Nummern liefert.
//: Abgeleitet aus den tatsächlichen Punkten je Phase — nicht erfunden:
//: Phase 3 heisst „Inhalte", weil dort „Hero-Headline KI-generiert" steht.
const PHASEN = {
  1: 'Akquise und Analyse',
  2: 'Auftrag und Briefing',
  3: 'Inhalte',
  4: 'Aufbau',
  5: 'Prüfung',
  6: 'Umstellung und Go-live',
  7: 'Nachbetreuung',
};

export default function Checklists() {
  const { projectId } = useParams();
  const nav = useNavigate();
  const { token } = useAuth();
  const [punkte, setPunkte] = useState(null);
  const [fehler, setFehler] = useState('');
  const [laeuftGerade, setLaeuftGerade] = useState('');

  const kopf = { Authorization: `Bearer ${token}` };

  const laden = useCallback(async () => {
    if (!projectId) return;
    try {
      const antwort = await fetch(
        `${API_BASE_URL}/api/projects/${projectId}/checklist`, { headers: kopf });
      if (antwort.status === 404) {
        setFehler('Dieses Projekt gibt es nicht.');
        return;
      }
      if (!antwort.ok) throw new Error(String(antwort.status));
      setPunkte(await antwort.json());
    } catch {
      setFehler('Die Checkliste konnte nicht geladen werden. Bitte neu laden.');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, token]);

  useEffect(() => { laden(); }, [laden]);

  const abhaken = async (punkt) => {
    setLaeuftGerade(punkt.item_key);
    // **Erst der Server, dann die Anzeige.** Ein Haken, der sofort umspringt
    // und beim nächsten Laden zurückfällt, ist schlimmer als einer, der kurz
    // wartet: Der Mensch glaubt, es sei erledigt.
    try {
      const antwort = await fetch(
        `${API_BASE_URL}/api/projects/${projectId}/checklist/${encodeURIComponent(punkt.item_key)}`,
        {
          method: 'PATCH',
          headers: { ...kopf, 'Content-Type': 'application/json' },
          body: JSON.stringify({ is_completed: !punkt.is_completed }),
        });
      if (!antwort.ok) throw new Error(String(antwort.status));
      const neu = await antwort.json();
      setPunkte((alte) => alte.map((p) => (
        p.item_key === punkt.item_key
          ? { ...p, is_completed: neu.is_completed,
              completed_at: neu.completed_at, completed_by: neu.completed_by }
          : p
      )));
      setFehler('');
    } catch {
      setFehler('Der Haken konnte nicht gespeichert werden — er steht noch wie vorher.');
    } finally {
      setLaeuftGerade('');
    }
  };

  // ── Ohne Projekt: sagen, was fehlt ──────────────────────────────────
  if (!projectId) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        <SeitenTitel>Checklisten</SeitenTitel>
        <div>
          <span style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: '.07em',
                         color: 'var(--text-tertiary)', fontWeight: 700 }}>
            Qualitätssicherung
          </span>
          <h1 style={{ fontSize: 24, fontWeight: 800, color: 'var(--text-primary)', margin: '4px 0 0' }}>
            Checklisten
          </h1>
        </div>
        <div className="kc-card" style={{ padding: 24 }}>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14, lineHeight: 1.75, margin: 0 }}>
            Checklisten gehören zu einem Projekt. Öffnen Sie ein Projekt in der
            Projektpipeline — die Checkliste liegt dort unter
            <strong> Projekt → Checkliste</strong>.
          </p>
          <button
            onClick={() => nav('/app/projektpipeline')}
            style={{
              marginTop: 16, background: 'var(--kc-dark)', color: 'var(--text-inverse)',
              border: 'none', borderRadius: 8, padding: '10px 18px',
              fontSize: 14, fontWeight: 700, cursor: 'pointer', minHeight: 44,
            }}
          >
            Zur Projektpipeline
          </button>
        </div>
      </div>
    );
  }

  const nachPhase = (punkte || []).reduce((sammlung, p) => {
    (sammlung[p.phase] = sammlung[p.phase] || []).push(p);
    return sammlung;
  }, {});
  const erledigt = (punkte || []).filter((p) => p.is_completed).length;
  const gesamt = (punkte || []).length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <SeitenTitel>Checkliste</SeitenTitel>

      <div>
        <span style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: '.07em',
                       color: 'var(--text-tertiary)', fontWeight: 700 }}>
          Qualitätssicherung · Projekt {projectId}
        </span>
        <h1 style={{ fontSize: 24, fontWeight: 800, color: 'var(--text-primary)', margin: '4px 0 0' }}>
          Checkliste
        </h1>
        {gesamt > 0 && (
          <p style={{ fontSize: 14, color: 'var(--text-secondary)', margin: '6px 0 0',
                      fontVariantNumeric: 'tabular-nums' }}>
            {erledigt} von {gesamt} Punkten erledigt
          </p>
        )}
      </div>

      {fehler && (
        <div role="alert" style={{
          background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)',
          borderRadius: 8, padding: '10px 14px', fontSize: 14,
        }}>
          {fehler}
        </div>
      )}

      {!fehler && punkte === null && (
        <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>Checkliste wird geladen…</p>
      )}

      {/* Eine leere Checkliste ist etwas anderes als ein Fehler: Projekte von
          vor der Einführung haben keine Punkte. Das zu sagen ist ehrlicher,
          als einen leeren Bereich zu zeigen. */}
      {!fehler && Array.isArray(punkte) && punkte.length === 0 && (
        <div className="kc-card" style={{ padding: 24 }}>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14, lineHeight: 1.75, margin: 0 }}>
            Für dieses Projekt sind keine Checklistenpunkte angelegt. Sie
            entstehen beim Anlegen eines Projekts; ältere Projekte haben keine.
          </p>
        </div>
      )}

      {Object.keys(nachPhase).sort((a, b) => a - b).map((phase) => {
        const eintraege = nachPhase[phase];
        const fertig = eintraege.filter((p) => p.is_completed).length;
        return (
          <section key={phase} className="kc-card" style={{ padding: 20 }}>
            <header style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between',
                             gap: 12, marginBottom: 12, flexWrap: 'wrap' }}>
              <h2 style={{ fontSize: 16, fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
                Phase {phase} · {PHASEN[phase] || 'Weitere Schritte'}
              </h2>
              <span style={{ fontSize: 13, color: 'var(--text-tertiary)',
                             fontVariantNumeric: 'tabular-nums' }}>
                {fertig}/{eintraege.length}
              </span>
            </header>

            <ul style={{ listStyle: 'none', margin: 0, padding: 0,
                         display: 'flex', flexDirection: 'column', gap: 2 }}>
              {eintraege.map((p) => (
                <li key={p.item_key}>
                  <div
                    role="checkbox"
                    tabIndex={0}
                    aria-checked={p.is_completed}
                    onClick={() => abhaken(p)}
                    onKeyDown={aufTaste(() => abhaken(p))}
                    style={{
                      display: 'flex', gap: 12, alignItems: 'flex-start',
                      padding: '10px 12px', borderRadius: 8, cursor: 'pointer',
                      opacity: laeuftGerade === p.item_key ? 0.5 : 1,
                      background: p.is_completed ? 'var(--bg-app)' : 'transparent',
                    }}
                  >
                    {/* **Kein `<input>`.** Die Bedienung liegt am `role="checkbox"`
                        darum herum; ein echtes Eingabefeld darin waere ein
                        zweiter Bedienpunkt, den ein Screenreader ansagt und
                        niemand braucht. `utils/feldName.test.js` hat es
                        gefunden — es hatte keinen vorlesbaren Namen, und den
                        haette es auch nicht haben duerfen. */}
                    <span aria-hidden="true" style={{
                      marginTop: 2, width: 18, height: 18, flexShrink: 0,
                      borderRadius: 4, display: 'inline-flex',
                      alignItems: 'center', justifyContent: 'center',
                      border: p.is_completed ? 'none' : '2px solid var(--border-medium)',
                      background: p.is_completed ? 'var(--kc-dark)' : 'transparent',
                      color: 'var(--text-inverse)', fontSize: 12, fontWeight: 900,
                    }}>
                      {p.is_completed ? '✓' : ''}
                    </span>
                    <span style={{ flex: 1, fontSize: 14, lineHeight: 1.6,
                                   color: p.is_completed ? 'var(--text-tertiary)' : 'var(--text-primary)',
                                   textDecoration: p.is_completed ? 'line-through' : 'none' }}>
                      {p.item_label}
                      {/* PFLICHT-Punkte sind hervorgehoben, weil sie im
                          Abnahmeprotokoll zählen — nicht als Farbe allein:
                          Wer Farben nicht unterscheidet, liest das Wort. */}
                      {p.is_critical && (
                        <strong style={{ marginLeft: 8, fontSize: 12, color: 'var(--status-danger-text)',
                                         textTransform: 'uppercase', letterSpacing: '.06em' }}>
                          Pflicht
                        </strong>
                      )}
                    </span>
                    {p.is_completed && p.completed_by && (
                      <span style={{ fontSize: 12, color: 'var(--text-tertiary)', whiteSpace: 'nowrap' }}>
                        {p.completed_by}
                      </span>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </section>
        );
      })}
    </div>
  );
}
