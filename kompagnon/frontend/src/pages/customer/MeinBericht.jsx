import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import API_BASE_URL from '../../config';
import GeoReport from '../../components/GeoReport';

/**
 * „Mein Bericht" — der Prüfstand der eigenen Website (L-161).
 *
 * **Warum die Kategoriebalken von der Startseite hierher gewandert sind.**
 * Sie beantworten eine Frage, die ein Kunde einmal im Monat stellt, nicht
 * beim Anmelden. Auf der Übersicht standen sie neben vier Kennzahlen und drei
 * Arbeitsflächen und machten aus einer Lagemeldung eine Materialsammlung.
 * Die Übersicht nennt jetzt den Punktwert und verweist hierher.
 */
const KATEGORIEN = [
  { key: 'rc_score', label: 'Recht und Pflichtangaben', max: 30 },
  { key: 'tp_score', label: 'Technik und Ladezeit',     max: 20 },
  { key: 'bf_score', label: 'Barrierefreiheit',         max: 20 },
  { key: 'si_score', label: 'Sicherheit',               max: 15 },
  { key: 'se_score', label: 'Auffindbarkeit',           max: 10 },
  { key: 'ux_score', label: 'Inhalt und Bedienung',     max:  5 },
];

// Zwei Farben fuer denselben Wert, und das ist kein Versehen (L-17): Ein
// Balken ist eine Flaeche und darf kraeftig sein; die Ziffern daneben sind
// Text und muessen den Kontrast halten.
const balkenFarbe = (a) => (a >= 0.7 ? '#16a34a' : a >= 0.45 ? '#f59e0b' : '#dc2626');
const zifferFarbe = (a) => (a >= 0.7 ? 'var(--success)' : a >= 0.45 ? 'var(--warn)' : 'var(--error)');

export default function MeinBericht() {
  const { user, token } = useAuth();
  const [profil, setProfil] = useState(null);
  const [fehler, setFehler] = useState('');

  useEffect(() => {
    if (!user?.lead_id) return;
    fetch(`${API_BASE_URL}/api/usercards/${user.lead_id}/profile`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then(setProfil)
      .catch(() => setFehler('Der Bericht konnte gerade nicht geladen werden.'));
  }, [user?.lead_id, token]);

  if (fehler) return <p style={{ color: 'var(--error)', fontSize: 14 }}>{fehler}</p>;
  if (!profil) return null;

  const audit = (profil.audits || [])[0] || null;
  const projekt = (profil.projects || [])[0] || null;

  let empfehlungen = audit?.recommendations || [];
  let maengel = audit?.top_issues || [];
  try { if (typeof empfehlungen === 'string') empfehlungen = JSON.parse(empfehlungen); } catch { empfehlungen = []; }
  try { if (typeof maengel === 'string') maengel = JSON.parse(maengel); } catch { maengel = []; }
  const text = (e) => (typeof e === 'string' ? e : e?.title || e?.text || e?.issue || '');

  const karte = {
    background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
    borderRadius: 'var(--radius-lg)', padding: 20, marginBottom: 16,
  };
  const ueberschrift = {
    fontSize: 13, fontWeight: 800, color: 'var(--text-tertiary)',
    textTransform: 'uppercase', letterSpacing: '.06em', margin: '0 0 16px',
  };

  return (
    <div style={{ maxWidth: 860, margin: '0 auto', padding: '0 0 40px' }}>
      {/* **Sichtbar, nicht nur fuer Hilfsmittel.** Hier stand ein
          `SeitenTitel` — der ist mit Absicht unsichtbar und gehoert auf
          Seiten, die schon eine sichtbare Ueberschrift haben. Diese hat
          keine: Ohne Pruefung blieb die Seite bis auf einen grauen Kasten
          leer und sah aus, als sei sie kaputt. Am 04.09.2026 im Browser
          gesehen, nicht im Quelltext. */}
      <h1 style={{ fontSize: 22, fontWeight: 900, letterSpacing: '-.02em',
                   color: 'var(--text-primary)', margin: '0 0 16px' }}>
        Mein Bericht
      </h1>

      {!audit ? (
        <div style={{ ...karte, color: 'var(--text-tertiary)', fontSize: 14 }}>
          Für Ihre Website liegt noch keine Prüfung vor. Sobald wir sie geprüft
          haben, steht der Bericht hier.
        </div>
      ) : (
        <>
          <div style={karte}>
            <h2 style={ueberschrift}>Gesamtergebnis</h2>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, flexWrap: 'wrap' }}>
              <span style={{ fontSize: 34, fontWeight: 900, color: 'var(--text-primary)',
                             fontVariantNumeric: 'tabular-nums', lineHeight: 1 }}>
                {profil.current_score ?? audit.total_score}
              </span>
              <span style={{ fontSize: 15, color: 'var(--text-secondary)' }}>von 100 Punkten</span>
              <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>
                · {(profil.current_level || '').replace('Homepage Standard ', '') || '—'}
              </span>
            </div>
            <p style={{ fontSize: 13, color: 'var(--text-tertiary)', margin: '10px 0 0' }}>
              Geprüft am {audit.created_at ? new Date(audit.created_at).toLocaleDateString('de-DE') : '—'}
            </p>
          </div>

          <div style={karte}>
            <h2 style={ueberschrift}>Die acht Bereiche</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {KATEGORIEN.map((k) => {
                const punkte = audit[k.key] ?? 0;
                const anteil = k.max > 0 ? punkte / k.max : 0;
                return (
                  <div key={k.key}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontSize: 13 }}>
                      <span style={{ color: 'var(--text-secondary)' }}>{k.label}</span>
                      <span style={{ fontWeight: 700, color: zifferFarbe(anteil),
                                     fontVariantNumeric: 'tabular-nums' }}>{punkte}/{k.max}</span>
                    </div>
                    <div style={{ height: 6, background: 'var(--border-light)', borderRadius: 3, overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${anteil * 100}%`,
                                    background: balkenFarbe(anteil), borderRadius: 3 }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {(maengel.length > 0 || empfehlungen.length > 0) && (
            <div style={karte}>
              <h2 style={ueberschrift}>Was wir Ihnen empfehlen</h2>
              <ol style={{ margin: 0, paddingLeft: 20, display: 'flex', flexDirection: 'column', gap: 8 }}>
                {[...maengel, ...empfehlungen].slice(0, 7).map((e, i) => (
                  <li key={i} style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.55 }}>
                    {text(e)}
                  </li>
                ))}
              </ol>
            </div>
          )}
        </>
      )}

      {projekt?.id && <GeoReport projectId={projekt.id} token={token} />}
    </div>
  );
}
