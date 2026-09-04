import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';
import KundenChat from '../components/kunde/KundenChat';
import { aufgabeBestimmen, kachelnBauen, lageBestimmen, verlaufBauen }
  from '../utils/kundenuebersicht';

/**
 * Die Übersicht des Kunden — eine Lage, eine Aufgabe, drei Zahlen (L-161).
 *
 * **Der Anlass.** Am 04.09.2026 meldete David: „unübersichtlich und
 * unaufgeräumt". Nachgemessen am laufenden Werkzeug waren es **3.156 px** und
 * **zehn Überschriften**, davon vier auf derselben Ebene ohne Rangfolge — und
 * der größte Teil davon war an diesem Tag von mir selbst dazugekommen: drei
 * Arbeitsflächen (Mitwirkung, Inhaltsänderungen, Zahlungen), jede für sich
 * richtig, alle zusammen ein Stapel.
 *
 * **Die Regel dieser Seite, aus dem abgenommenen Entwurf:** Sie beantwortet
 * zwei Fragen und sonst keine — *Wo stehen wir?* und *Was liegt bei mir?*
 * Alles, woran man arbeitet, hat einen Menüpunkt. Was hier steht, ist die
 * Lage in einem Satz, **eine** Aufgabe, drei Kacheln und der jüngste Verlauf.
 *
 * **Ein warmes Zeichen je Bildschirm.** „Offen" ist kein Fehler, sondern ein
 * Zustand; farbig ausgezeichnet wird nur, was der Kunde jetzt tun soll.
 * Alles gleichzeitig hervorzuheben heißt, nichts hervorzuheben.
 *
 * **Die Werte kommen aus vier Endpunkten, die es schon gibt.** Kein
 * Sammel-Endpunkt: Er wäre eine zweite Wahrheit über dieselben Zahlen, und
 * die vier Abrufe laufen nebeneinander.
 */

const LEER = { profil: null, mitwirkung: null, inhalt: null, zahlungen: null,
               portal: null, projekt: null };

export default function CustomerDashboard() {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [daten, setDaten] = useState(LEER);
  const [laedt, setLaedt] = useState(true);
  const [fehler, setFehler] = useState(null);

  useEffect(() => {
    if (!user?.lead_id) { setLaedt(false); setFehler('keine_kartei'); return; }
    const kopf = { Authorization: `Bearer ${token}` };
    const hol = (pfad) => fetch(`${API_BASE_URL}${pfad}`, { headers: kopf })
      .then((r) => (r.ok ? r.json() : null))
      .catch(() => null);

    Promise.all([
      hol(`/api/usercards/${user.lead_id}/profile`),
      hol('/api/portal/mitwirkung'),
      hol('/api/portal/inhalt'),
      hol('/api/portal/zahlungen'),
      hol('/api/portal/me'),
    ]).then(async ([profil, mitwirkung, inhalt, zahlungen, portal]) => {
      // **Nur das Profil ist unverzichtbar.** Die anderen dürfen fehlen — ein
      // Betrieb ohne Abo hat keine Zahlungen, und eine leere Kachel ist
      // besser als eine Seite, die wegen einer Nebensache nicht erscheint.
      if (!profil) { setFehler('Ihre Daten konnten gerade nicht geladen werden.'); setLaedt(false); return; }

      // **Zweiter Zug, weil er von der ersten Antwort abhängt.** Die offenen
      // Freigaben stehen in `content_freigaben` am Projekt, und das Profil
      // liefert diese Spalte nicht mit — es führt fünf Projektfelder, die
      // Spalte ist keines davon. Ohne sie könnte die Übersicht den nächsten
      // Schritt in der Bauphase nicht benennen, und genau darum geht es hier.
      const projektId = portal?.project_id || (profil.projects || [])[0]?.id;
      const projekt = projektId ? await hol(`/api/projects/${projektId}`) : null;

      setDaten({ profil, mitwirkung, inhalt, zahlungen, portal, projekt });
      setLaedt(false);
    });
  }, [user?.lead_id, token]);

  if (laedt) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '50vh', flexDirection: 'column', gap: 12 }}>
      <div style={{ width: 36, height: 36, borderRadius: '50%', border: '3px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
      <span style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>Wird geladen…</span>
    </div>
  );

  if (fehler === 'keine_kartei') return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '50vh', gap: 16, textAlign: 'center', padding: 24 }}>
      <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>Kartei noch nicht verknüpft</h2>
      <p style={{ fontSize: 14, color: 'var(--text-secondary)', maxWidth: 400, margin: 0 }}>
        Ihre Kundenkartei wurde noch nicht verknüpft. Bitte kontaktieren Sie KOMPAGNON.
      </p>
      <a href="mailto:info@kompagnon.eu" style={{ background: 'var(--brand-primary)', color: 'var(--text-on-brand)', padding: '10px 24px', borderRadius: 'var(--radius-md)', textDecoration: 'none', fontSize: 14, fontWeight: 600 }}>
        Kontakt aufnehmen
      </a>
    </div>
  );

  if (fehler) return <p style={{ textAlign: 'center', padding: 60, color: 'var(--text-tertiary)' }}>{fehler}</p>;

  const { profil, mitwirkung, inhalt, zahlungen, portal, projekt } = daten;
  const lage = lageBestimmen({ profil, mitwirkung });
  const kacheln = kachelnBauen({ profil, mitwirkung, inhalt, zahlungen, lage });
  const aufgabe = aufgabeBestimmen({ lage, mitwirkung, inhalt, projekt, portal });
  const verlauf = verlaufBauen({ inhalt, zahlungen, profil });
  const betrieb = profil.lead?.display_name || profil.lead?.company_name || '';

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', width: '100%', paddingBottom: 40 }}>

      <h1 style={{ fontSize: 26, fontWeight: 900, letterSpacing: '-.025em', color: 'var(--text-primary)', margin: '0 0 6px' }}>
        {betrieb}
      </h1>
      <p style={{ fontSize: 19, lineHeight: 1.5, color: 'var(--text-primary)', margin: '0 0 4px', maxWidth: '56ch' }}>
        {lage.satz}
      </p>
      <p style={{ fontSize: 14, color: 'var(--text-tertiary)', margin: '0 0 28px' }}>{lage.dazu}</p>

      {/* **Das einzige warme Zeichen auf dem Bildschirm.** Es benennt den
          nächsten Schritt — bei ihm, wenn etwas bei ihm liegt, sonst bei
          uns. Alles gleichzeitig hervorzuheben heißt, nichts hervorzuheben;
          deshalb ist dies die einzige farbige Fläche der Seite. */}
      {aufgabe && (
        <div style={{
          background: 'var(--kc-dark)', color: '#fff', borderRadius: 'var(--radius-lg)',
          padding: '22px 26px', marginBottom: 28, display: 'flex', gap: 20,
          alignItems: 'center', flexWrap: 'wrap',
        }}>
          <div style={{ flex: 1, minWidth: 240 }}>
            {/* Der hervorgehobene Teil kommt als eigenes Feld aus
                `kundenuebersicht.js` — dort steht *was* dasteht, hier *wie*. */}
            <p style={{ margin: 0, fontSize: 16, lineHeight: 1.5 }}>
              {aufgabe.vorspann}
              <b style={{ color: 'var(--kc-yellow)', fontWeight: 900 }}>{aufgabe.hervor}</b>
              {aufgabe.nachspann || ''}
            </p>
            {aufgabe.dazu && (
              <p style={{ margin: '4px 0 0', fontSize: 14, lineHeight: 1.45, color: 'rgba(255,255,255,.78)' }}>
                {aufgabe.dazu}
              </p>
            )}
          </div>
          {/* **Kein Knopf, wenn es nichts zu tun gibt.** Ein Streifen, der
              berichtet, braucht keinen — und eine Schaltfläche ohne Aufgabe
              dahinter ist die Sorte Knopf, die man einmal drückt und danach
              nicht mehr ernst nimmt. */}
          {aufgabe.knopf && (
            <button
              onClick={() => navigate(aufgabe.ziel)}
              style={{
                font: 'inherit', fontWeight: 900, fontSize: 14, padding: '12px 22px',
                borderRadius: 'var(--radius-md)', border: 'none',
                background: 'var(--kc-yellow)', color: '#000', cursor: 'pointer', flex: 'none',
              }}
            >
              {aufgabe.knopf}
            </button>
          )}
        </div>
      )}

      <div style={{ display: 'grid', gap: 12, gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', marginBottom: 8 }}>
        {kacheln.map((k) => (
          <Kachel key={k.was} {...k} onClick={k.ziel ? () => navigate(k.ziel) : undefined} />
        ))}
      </div>

      <h2 style={{ fontSize: 14, fontWeight: 900, textTransform: 'uppercase', letterSpacing: '-.02em', color: 'var(--text-tertiary)', margin: '32px 0 10px' }}>
        Zuletzt passiert
      </h2>
      <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)' }}>
        {verlauf.length === 0 ? (
          <p style={{ padding: '14px 18px', margin: 0, fontSize: 14, color: 'var(--text-tertiary)' }}>
            Hier steht, was zuletzt an Ihrem Auftrag geschehen ist.
          </p>
        ) : verlauf.map((z, i) => (
          <div key={i} style={{
            display: 'flex', gap: 14, alignItems: 'baseline', padding: '12px 18px',
            borderTop: i === 0 ? 'none' : '1px solid var(--border-light)', fontSize: 15,
            color: 'var(--text-primary)',
          }}>
            <span>{z.was}</span>
            <span style={{ marginLeft: 'auto', flex: 'none', fontSize: 13, color: 'var(--text-tertiary)', fontVariantNumeric: 'tabular-nums' }}>
              {z.wann}
            </span>
          </div>
        ))}
      </div>

      {user?.lead_id && (
        <div style={{ marginTop: 32 }}>
          <KundenChat leadId={user.lead_id} token={token} />
        </div>
      )}
    </div>
  );
}

function Kachel({ was, zahl, klein, sagt, hin, betont, gut, onClick }) {
  const rand = betont ? 'var(--kc-dark)' : gut ? 'var(--success)' : 'var(--border-medium)';
  return (
    <div
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onClick={onClick}
      onKeyDown={onClick ? (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick(); } } : undefined}
      style={{
        background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
        borderTop: `3px solid ${rand}`, borderRadius: 'var(--radius-lg)', padding: 20,
        textAlign: 'left', cursor: onClick ? 'pointer' : 'default',
      }}
    >
      <p style={{ fontSize: 13, color: 'var(--text-tertiary)', margin: '0 0 8px', textTransform: 'uppercase', letterSpacing: '.04em', fontWeight: 700 }}>
        {was}
      </p>
      <span style={{ fontSize: 30, fontWeight: 700, lineHeight: 1, color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums' }}>
        {zahl}
        {klein && <small style={{ fontSize: 15, fontWeight: 400, color: 'var(--text-tertiary)', marginLeft: 6 }}>{klein}</small>}
      </span>
      <p style={{ fontSize: 14, color: 'var(--text-secondary)', margin: '8px 0 0', lineHeight: 1.45 }}>{sagt}</p>
      {hin && onClick && (
        <p style={{ fontSize: 13, color: 'var(--kc-mid)', margin: '10px 0 0', fontWeight: 700 }}>{hin}</p>
      )}
    </div>
  );
}
