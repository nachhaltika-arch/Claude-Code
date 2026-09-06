import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import API_BASE_URL from '../../config';
import Zahlungen from '../../components/Zahlungen';
import { datumKurz } from '../../utils/datum';

/**
 * Die Kontoverwaltung des Kunden — sechs Bereiche an einer Stelle (06.09.2026).
 *
 * **Der Wunsch (David):** Profil, Abo und Zahlung, Rechnungen, Geräte,
 * Sicherheit, Benachrichtigungen und Downloads.
 *
 * **Warum eine Seite mit Abschnitten und nicht sechs Menüpunkte.** Das sind
 * Dinge, die man selten und dann meist zusammen erledigt: Man kommt hierher,
 * weil sich etwas geändert hat — neue Telefonnummer, neue Karte, ein fremdes
 * Gerät in der Liste. Sechs Punkte im Menü hätten die täglichen Wege
 * verdrängt („Was wir brauchen", „Inhaltsänderungen"), die den Kunden
 * wirklich beschäftigen.
 *
 * **Was hier bewusst nicht neu gebaut ist.** Abo, Zahlungsart und Rechnungen
 * zeigt `Zahlungen` — dieselbe Komponente wie unter „Rechnungen und Zahlung".
 * Zwei Darstellungen derselben Zeilen würden auseinanderlaufen; das war
 * schon einmal so, siehe die Doppelung „Ihre/Meine Rechnungen" (L-161).
 */

const ABSCHNITTE = [
  { id: 'profil', titel: 'Profil' },
  { id: 'zahlung', titel: 'Abo, Zahlung und Rechnungen' },
  { id: 'geraete', titel: 'Geräte' },
  { id: 'sicherheit', titel: 'Sicherheit' },
  { id: 'post', titel: 'Benachrichtigungen' },
  { id: 'downloads', titel: 'Downloads' },
];

export default function MeinKonto() {
  const { token, user } = useAuth();
  const [offen, setOffen] = useState('profil');

  return (
    <div style={{ maxWidth: 880, margin: '0 auto', padding: '0 0 48px' }}>
      <h1 style={S.h1}>Mein Konto</h1>
      <p style={S.unter}>
        Ihre Daten, Ihre Zahlungen und Ihre Zugänge — alles, was zu Ihrem
        Konto gehört und nicht zu einem Auftrag.
      </p>

      {/* Ein Reiter je Bereich. Sie stehen alle sichtbar da, statt in einem
          Ausklappmenü zu verschwinden: Wer hierherkommt, sucht oft nicht das,
          was er beim Öffnen sieht. */}
      <div style={S.reiter}>
        {ABSCHNITTE.map((a) => (
          <button key={a.id} onClick={() => setOffen(a.id)}
                  aria-pressed={offen === a.id}
                  style={{ ...S.reiterKnopf, ...(offen === a.id ? S.reiterAn : {}) }}>
            {a.titel}
          </button>
        ))}
      </div>

      {offen === 'profil' && <Profil token={token} user={user} />}
      {offen === 'zahlung' && <Zahlungen token={token} ohneTitel />}
      {offen === 'geraete' && <Geraete token={token} />}
      {offen === 'sicherheit' && <Sicherheit token={token} />}
      {offen === 'post' && <Post token={token} />}
      {offen === 'downloads' && <Downloads token={token} />}
    </div>
  );
}

/* ── Profil ──────────────────────────────────────────────────────── */

function Profil({ token }) {
  const [daten, setDaten] = useState(null);
  const [entwurf, setEntwurf] = useState({});
  const [stand, setStand] = useState('');

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => { if (d) { setDaten(d); setEntwurf(d); } })
      .catch(() => setStand('Ihre Daten konnten nicht geladen werden.'));
  }, [token]);

  const speichern = async () => {
    setStand('speichert');
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/me`, {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          first_name: entwurf.first_name || '',
          last_name: entwurf.last_name || '',
          phone: entwurf.phone || '',
        }),
      });
      if (!res.ok) throw new Error('Nicht gespeichert — bitte noch einmal.');
      setDaten(await res.json());
      setStand('gespeichert');
    } catch (e) { setStand(e.message); }
  };

  if (!daten) return <p style={S.leise}>{stand || 'Wird geladen …'}</p>;

  return (
    <section style={S.karte}>
      <Feld beschriftung="Vorname" wert={entwurf.first_name || ''}
            aendern={(v) => setEntwurf({ ...entwurf, first_name: v })} />
      <Feld beschriftung="Nachname" wert={entwurf.last_name || ''}
            aendern={(v) => setEntwurf({ ...entwurf, last_name: v })} />
      <Feld beschriftung="Telefon" wert={entwurf.phone || ''}
            aendern={(v) => setEntwurf({ ...entwurf, phone: v })} />

      {/* **Die Adresse ist nicht änderbar, und das steht dabei.** An ihr
          hängt die Anmeldung; sie zu tauschen ist ein Vorgang mit
          Bestätigungsmail, kein Formularfeld. Ein Feld, das aussieht wie
          änderbar und dann nicht speichert, ist schlimmer als eine Zeile. */}
      <p style={S.zeile}>
        <span style={S.beschriftung}>E-Mail</span>
        <span>{daten.email} <span style={S.leise}>— Änderung bitte über Support,
          daran hängt Ihre Anmeldung.</span></span>
      </p>

      <button style={S.knopf} onClick={speichern} disabled={stand === 'speichert'}>
        {stand === 'speichert' ? 'Wird gespeichert …' : 'Änderungen speichern'}
      </button>
      {stand === 'gespeichert' && <p style={S.gut}>Gespeichert.</p>}
      {stand && !['speichert', 'gespeichert'].includes(stand) && <p style={S.fehler}>{stand}</p>}
    </section>
  );
}

/* ── Geräte ──────────────────────────────────────────────────────── */

function Geraete({ token }) {
  const [liste, setListe] = useState(null);
  const [laeuft, setLaeuft] = useState(0);
  const [fehler, setFehler] = useState('');

  const laden = () => fetch(`${API_BASE_URL}/api/portal/geraete`, {
    headers: { Authorization: `Bearer ${token}` },
  }).then((r) => (r.ok ? r.json() : { geraete: [] })).then((d) => setListe(d.geraete || []));

  useEffect(() => { laden(); }, [token]);   // eslint-disable-line

  const abmelden = async (id) => {
    setLaeuft(id);
    try {
      const res = await fetch(`${API_BASE_URL}/api/portal/geraete/${id}/abmelden`, {
        method: 'POST', headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Konnte nicht abgemeldet werden.');
      await laden();
    } catch (e) { setFehler(e.message); } finally { setLaeuft(0); }
  };

  if (!liste) return <p style={S.leise}>Wird geladen …</p>;
  if (!liste.length) {
    return (
      <section style={S.karte}>
        <p style={S.leise}>
          Hier erscheinen Ihre Anmeldungen, sobald Sie sich das nächste Mal
          anmelden.
        </p>
      </section>
    );
  }

  return (
    <section style={S.karte}>
      <p style={S.hinweis}>
        Wo Ihr Konto angemeldet ist. Kommt Ihnen ein Gerät fremd vor, melden
        Sie es ab — <b>und ändern Sie danach Ihr Passwort.</b>
      </p>
      {liste.map((g) => (
        <div key={g.id} style={S.reihe}>
          <span style={{ flex: 1 }}>
            <b>{g.geraet}</b>
            {g.dieses_geraet && <>{' '}<span style={S.marke}>dieses Gerät</span></>}
            <span style={S.leise}>
              {' '}{g.netz && `${g.netz} · `}
              seit {datumKurz(g.angemeldet_am)}
              {g.abgemeldet ? ' · abgemeldet' : g.abgelaufen ? ' · abgelaufen' : ''}
            </span>
          </span>
          {!g.abgemeldet && !g.abgelaufen && (
            <button style={S.knopfKlein} onClick={() => abmelden(g.id)} disabled={laeuft === g.id}>
              {laeuft === g.id ? '…' : 'Abmelden'}
            </button>
          )}
        </div>
      ))}
      {fehler && <p style={S.fehler}>{fehler}</p>}
    </section>
  );
}

/* ── Sicherheit ──────────────────────────────────────────────────── */

function Sicherheit({ token }) {
  const [alt, setAlt] = useState('');
  const [neu, setNeu] = useState('');
  const [stand, setStand] = useState('');

  const wechseln = async () => {
    if (neu.length < 8) { setStand('Das neue Passwort braucht mindestens acht Zeichen.'); return; }
    setStand('speichert');
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/change-password`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ current_password: alt, new_password: neu }),
      });
      const d = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(d.detail || 'Das hat nicht geklappt.');
      setAlt(''); setNeu(''); setStand('gewechselt');
    } catch (e) { setStand(e.message); }
  };

  return (
    <section style={S.karte}>
      <h2 style={S.h2}>Passwort ändern</h2>
      {/* `autoComplete` sagt dem Passwortspeicher, worum es geht — ohne die
          Angabe bietet er beim Ändern die falsche Zeile an. */}
      <Feld beschriftung="Aktuelles Passwort" wert={alt} aendern={setAlt}
            typ="password" autoComplete="current-password" />
      <Feld beschriftung="Neues Passwort" wert={neu} aendern={setNeu}
            typ="password" autoComplete="new-password" />
      <button style={S.knopf} onClick={wechseln} disabled={stand === 'speichert'}>
        {stand === 'speichert' ? 'Wird geändert …' : 'Passwort ändern'}
      </button>
      {stand === 'gewechselt' && <p style={S.gut}>Passwort geändert.</p>}
      {stand && !['speichert', 'gewechselt'].includes(stand) && <p style={S.fehler}>{stand}</p>}

      <h2 style={{ ...S.h2, marginTop: 28 }}>Zwei-Faktor-Anmeldung</h2>
      <p style={S.hinweis}>
        Zusätzlich zum Passwort ein Code aus einer App auf Ihrem Telefon.
        Wir richten das mit Ihnen zusammen ein — <b>schreiben Sie uns kurz</b>,
        dann führen wir Sie durch die Einrichtung und hinterlegen die
        Ersatzcodes an einem sicheren Ort.
      </p>
      {/* **Kein Selbstbedienungsknopf, und das ist Absicht.** Wer die
          Einrichtung allein abbricht, hat einen halb aktivierten zweiten
          Faktor und kommt nicht mehr hinein — bei einem Handwerksbetrieb ohne
          zweiten Zugang ist das ein Ausfall, kein Ärgernis. */}
    </section>
  );
}

/* ── Benachrichtigungen ──────────────────────────────────────────── */

function Post({ token }) {
  const [arten, setArten] = useState(null);
  const [fehler, setFehler] = useState('');

  const laden = () => fetch(`${API_BASE_URL}/api/portal/benachrichtigungen`, {
    headers: { Authorization: `Bearer ${token}` },
  }).then((r) => (r.ok ? r.json() : { arten: [] })).then((d) => setArten(d.arten || []));

  useEffect(() => { laden(); }, [token]);   // eslint-disable-line

  const umschalten = async (art) => {
    setFehler('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/portal/benachrichtigungen/${art.schluessel}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ an: !art.an }),
      });
      const d = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(d.detail || 'Nicht gespeichert.');
      await laden();
    } catch (e) { setFehler(e.message); }
  };

  if (!arten) return <p style={S.leise}>Wird geladen …</p>;

  const waehlbar = arten.filter((a) => a.abwaehlbar);
  const pflicht = arten.filter((a) => !a.abwaehlbar);

  return (
    <section style={S.karte}>
      <h2 style={S.h2}>Was Sie bekommen möchten</h2>
      {waehlbar.map((a) => (
        <label key={a.schluessel} style={S.wahlzeile}>
          <input type="checkbox" checked={a.an} onChange={() => umschalten(a)} />
          <span>
            <b>{a.titel}</b>
            <span style={S.leise}> — {a.beschreibung}</span>
          </span>
        </label>
      ))}

      <h2 style={{ ...S.h2, marginTop: 28 }}>Was zum Vertrag gehört</h2>
      {/* **Und warum es nicht abwählbar ist, steht dabei.** Eine gesperrte
          Auswahl ohne Begründung liest sich als Gängelung; mit Begründung als
          Schutz — und sie ist es auch: An der Freigabe hängt eine Frist. */}
      {pflicht.map((a) => (
        <p key={a.schluessel} style={S.zeile}>
          <span><b>{a.titel}</b><span style={S.leise}> — {a.beschreibung}</span></span>
          <span style={S.leise}>{a.warum_pflicht}</span>
        </p>
      ))}
      {fehler && <p style={S.fehler}>{fehler}</p>}
    </section>
  );
}

/* ── Downloads ───────────────────────────────────────────────────── */

function Downloads({ token }) {
  const [daten, setDaten] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/portal/downloads`, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => (r.ok ? r.json() : { dateien: [], kaeufe: [] }))
      .then(setDaten)
      .catch(() => setDaten({ dateien: [], kaeufe: [] }));
  }, [token]);

  if (!daten) return <p style={S.leise}>Wird geladen …</p>;
  const leer = !daten.dateien.length && !daten.kaeufe.length;

  return (
    <section style={S.karte}>
      {leer && <p style={S.leise}>Hier liegt noch nichts zum Herunterladen.</p>}

      {daten.kaeufe.length > 0 && (
        <>
          <h2 style={S.h2}>Ihre Käufe</h2>
          {daten.kaeufe.map((k) => (
            <div key={k.nummer} style={S.reihe}>
              <span style={{ flex: 1 }}>
                <b>{k.produkt}</b>
                <span style={S.leise}> — {k.nummer}, {datumKurz(k.gekauft_am)}</span>
              </span>
              {k.adresse && (
                <a style={S.knopfKlein} href={`${API_BASE_URL}${k.adresse}`}>Herunterladen</a>
              )}
            </div>
          ))}
        </>
      )}

      {daten.dateien.length > 0 && (
        <>
          <h2 style={{ ...S.h2, marginTop: daten.kaeufe.length ? 28 : 0 }}>Dateien zu Ihrem Betrieb</h2>
          {daten.dateien.map((d) => (
            <div key={d.id} style={S.reihe}>
              <span style={{ flex: 1 }}>
                <b>{d.name}</b>
                <span style={S.leise}>
                  {' '}— {groesse(d.groesse)}, von {d.von}, {datumKurz(d.hochgeladen_am)}
                </span>
              </span>
            </div>
          ))}
          {/* Kein Download-Knopf an den Betriebsdateien: Der bestehende Weg
              verlangt eine Kennung je Datei, und ein Knopf, der ins Leere
              führt, ist schlimmer als keiner. Die Liste sagt, was da ist —
              holen kann es der Kunde über den Support, bis der Weg steht. */}
        </>
      )}
    </section>
  );
}

function groesse(bytes) {
  const n = Number(bytes || 0);
  if (n > 1024 * 1024) return `${(n / 1024 / 1024).toFixed(1)} MB`;
  if (n > 1024) return `${Math.round(n / 1024)} KB`;
  return `${n} B`;
}

/* ── Bausteine ───────────────────────────────────────────────────── */

function Feld({ beschriftung, wert, aendern, typ = 'text', autoComplete = 'off' }) {
  return (
    <label style={S.feld}>
      <span style={S.beschriftung}>{beschriftung}</span>
      <input type={typ} value={wert} autoComplete={autoComplete}
             onChange={(e) => aendern(e.target.value)} style={S.eingabe} />
    </label>
  );
}

const S = {
  h1: { fontSize: 22, fontWeight: 900, letterSpacing: '-.02em', color: 'var(--text-primary)', margin: '0 0 6px' },
  unter: { fontSize: 15, color: 'var(--text-secondary)', margin: '0 0 22px', maxWidth: '60ch', lineHeight: 1.55 },
  reiter: { display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 20 },
  reiterKnopf: {
    font: 'inherit', fontSize: 13.5, fontWeight: 700, padding: '8px 15px',
    borderRadius: 999, border: '1px solid var(--border-medium)',
    background: 'var(--bg-surface)', color: 'var(--text-secondary)', cursor: 'pointer',
  },
  reiterAn: { background: 'var(--brand-primary)', borderColor: 'var(--brand-primary)', color: 'var(--text-on-brand)' },
  karte: { background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 12, padding: 24 },
  h2: { fontSize: 13, fontWeight: 900, textTransform: 'uppercase', letterSpacing: '.06em', color: 'var(--text-tertiary)', margin: '0 0 14px' },
  hinweis: { fontSize: 14, color: 'var(--text-secondary)', margin: '0 0 16px', lineHeight: 1.55, maxWidth: '62ch' },
  feld: { display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 14, maxWidth: 420 },
  beschriftung: { fontSize: 13, fontWeight: 700, color: 'var(--text-secondary)' },
  eingabe: {
    font: 'inherit', fontSize: 14, padding: '9px 11px', borderRadius: 6,
    border: '1px solid var(--border-medium)', background: 'var(--bg-app)',
    color: 'var(--text-primary)', width: '100%',
  },
  zeile: { display: 'flex', flexDirection: 'column', gap: 3, fontSize: 14, color: 'var(--text-primary)', margin: '0 0 14px', lineHeight: 1.5 },
  reihe: { display: 'flex', gap: 12, alignItems: 'baseline', padding: '11px 0', borderTop: '1px solid var(--border-light)', fontSize: 14 },
  wahlzeile: { display: 'flex', gap: 10, alignItems: 'flex-start', padding: '9px 0', fontSize: 14, cursor: 'pointer', lineHeight: 1.5 },
  marke: {
    fontSize: 12, fontWeight: 900, padding: '2px 8px', borderRadius: 999, marginLeft: 8,
    background: 'var(--status-success-bg)', color: 'var(--status-success)',
  },
  knopf: {
    fontWeight: 900, fontSize: 14, padding: '11px 20px', borderRadius: 6, border: 'none',
    cursor: 'pointer', background: 'var(--brand-primary)', color: 'var(--text-on-brand)', marginTop: 6,
  },
  knopfKlein: {
    font: 'inherit', fontSize: 13, fontWeight: 700, padding: '6px 13px', borderRadius: 6,
    border: '1px solid var(--border-medium)', background: 'var(--bg-app)',
    color: 'var(--text-primary)', cursor: 'pointer', textDecoration: 'none', flex: 'none',
  },
  leise: { color: 'var(--text-tertiary)', fontSize: 13.5 },
  gut: { color: 'var(--success)', fontSize: 14, margin: '10px 0 0' },
  fehler: { color: 'var(--error)', fontSize: 14, margin: '10px 0 0' },
};
