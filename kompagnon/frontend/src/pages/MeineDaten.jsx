/**
 * Die Stammdaten des eigenen Betriebs — vom Kunden gepflegt.
 *
 * **Der Auftrag (26.08.2026, David).** Im Kundenportal sollen Stammdaten
 * bearbeitbar sein.
 *
 * **Was der Menüpunkt „Meine Kartei" vorher tat:** Er zeigte auf
 * `/app/betriebe/{id}` — den Innendienst-Bildschirm, dessen Route
 * `roles={['admin','auditor']}` trägt. `PrivateRoute` wirft einen Kunden von
 * dort auf sein Dashboard zurück. Der Punkt sah aus wie eine zweite Seite und
 * war eine Schleife auf dieselbe.
 *
 * **Warum ausgerechnet diese Felder:** Rechtsform, Registernummer,
 * Registergericht und Geschäftsführer kennt der Betrieb — wir nicht. Sie
 * müssen ins Impressum, und bisher wurden sie im Briefing per Hand abgefragt
 * und vom Innendienst eingetragen. Was **wir** über den Betrieb führen —
 * Status, Herkunft, interne Notizen — steht hier bewusst nicht; der Server
 * nimmt es auch nicht an (Erlaubnisliste in `leads_portal.py`).
 */
import { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';
import SeitenTitel from '../components/ui/SeitenTitel';
import KundenChat from '../components/kunde/KundenChat';

/**
 * Die Felder in der Reihenfolge, in der ein Mensch sie im Kopf hat: erst der
 * Betrieb, dann die Erreichbarkeit, dann die Anschrift, zuletzt das, was ins
 * Impressum muss.
 */
const GRUPPEN = [
  {
    titel: 'Betrieb',
    felder: [
      { name: 'company_name', label: 'Firmenname' },
      { name: 'display_name', label: 'Anzeigename', hinweis: 'Wie der Betrieb auf der Website heißen soll, falls abweichend.' },
      { name: 'website_url', label: 'Website', typ: 'url' },
    ],
  },
  {
    titel: 'Erreichbarkeit',
    felder: [
      { name: 'contact_name', label: 'Ansprechpartner' },
      { name: 'phone', label: 'Telefon', typ: 'tel' },
      { name: 'email', label: 'E-Mail des Betriebs', typ: 'email', hinweis: 'Die geschäftliche Adresse. Ihre Anmeldeadresse ändert sich dadurch nicht.' },
    ],
  },
  {
    titel: 'Anschrift',
    felder: [
      { name: 'street', label: 'Straße' },
      { name: 'house_number', label: 'Hausnummer' },
      { name: 'postal_code', label: 'PLZ' },
      { name: 'city', label: 'Ort' },
    ],
  },
  {
    titel: 'Angaben fürs Impressum',
    hinweis: 'Diese Angaben müssen im Impressum Ihrer Website stehen. '
      + 'Sie kennen sie — wir tragen sie nur ein.',
    felder: [
      { name: 'legal_form', label: 'Rechtsform', hinweis: 'z. B. GmbH, GbR, Einzelunternehmen' },
      { name: 'register_number', label: 'Registernummer', hinweis: 'z. B. HRB 12345' },
      { name: 'register_court', label: 'Registergericht', hinweis: 'z. B. Amtsgericht Koblenz' },
      { name: 'vat_id', label: 'Umsatzsteuer-ID' },
      { name: 'ceo_first_name', label: 'Geschäftsführer — Vorname' },
      { name: 'ceo_last_name', label: 'Geschäftsführer — Nachname' },
    ],
  },
];

const ALLE_FELDER = GRUPPEN.flatMap((g) => g.felder.map((f) => f.name));

export default function MeineDaten() {
  const { token, user } = useAuth();
  const leadId = user?.lead_id;

  const [werte, setWerte] = useState(null);
  const [gespeichert, setGespeichert] = useState(null);
  const [fehler, setFehler] = useState('');
  const [hinweis, setHinweis] = useState('');
  const [speichert, setSpeichert] = useState(false);

  const kopf = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const laden = useCallback(async () => {
    if (!leadId) return;
    setFehler('');
    try {
      const antwort = await fetch(`${API_BASE_URL}/api/leads/${leadId}`, { headers: kopf });
      if (!antwort.ok) throw new Error(`Status ${antwort.status}`);
      const daten = await antwort.json();
      const nur = Object.fromEntries(ALLE_FELDER.map((f) => [f, daten[f] ?? '']));
      setWerte(nur);
      setGespeichert(nur);
    } catch (e) {
      setFehler(`Ihre Daten konnten nicht geladen werden (${e.message}).`);
    }
  }, [leadId, token]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { laden(); }, [laden]);

  /** Nur das Geänderte senden — sonst schreibt jedes Speichern jedes Feld. */
  const geaendert = werte && gespeichert
    ? Object.fromEntries(ALLE_FELDER
      .filter((f) => (werte[f] ?? '') !== (gespeichert[f] ?? ''))
      .map((f) => [f, werte[f]]))
    : {};
  const anzahlGeaendert = Object.keys(geaendert).length;

  async function speichern(e) {
    e.preventDefault();
    if (!anzahlGeaendert) return;

    setSpeichert(true); setFehler(''); setHinweis('');
    try {
      const antwort = await fetch(`${API_BASE_URL}/api/leads/${leadId}/stammdaten`, {
        method: 'PATCH', headers: kopf, body: JSON.stringify(geaendert),
      });
      const daten = await antwort.json().catch(() => ({}));
      if (!antwort.ok) throw new Error(daten.detail || `Status ${antwort.status}`);

      // Angezeigt wird, was der Server **gespeichert** hat, nicht was wir
      // gesendet haben. Ein stillschweigend verworfenes Feld sähe sonst aus
      // wie ein übernommenes.
      const nur = Object.fromEntries(ALLE_FELDER.map((f) => [f, daten.stammdaten?.[f] ?? '']));
      setWerte(nur);
      setGespeichert(nur);
      setHinweis(daten.nicht_uebernommen?.length
        ? `Gespeichert. Nicht übernommen: ${daten.nicht_uebernommen.join(', ')}.`
        : 'Gespeichert.');
    } catch (e2) {
      setFehler(`Speichern fehlgeschlagen (${e2.message}). Ihre Eingaben stehen noch da.`);
    } finally {
      setSpeichert(false);
    }
  }

  if (!leadId) {
    return (
      <div style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>
        <SeitenTitel>Meine Daten</SeitenTitel>
        Ihr Konto ist noch keinem Betrieb zugeordnet. Bitte wenden Sie sich an
        Ihren Betreuer.
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 880 }}>
      <SeitenTitel>Meine Daten</SeitenTitel>

      <form onSubmit={speichern} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
        {GRUPPEN.map((gruppe) => (
          <section key={gruppe.titel} style={{
            background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
            borderRadius: 'var(--radius-xl)', padding: '18px 20px',
          }}>
            <h2 style={{ margin: 0, fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
              {gruppe.titel}
            </h2>
            {gruppe.hinweis && (
              <p style={{ margin: '6px 0 0', fontSize: 12, lineHeight: 1.55, color: 'var(--text-tertiary)' }}>
                {gruppe.hinweis}
              </p>
            )}
            <div style={{
              display: 'grid', gap: 12, marginTop: 14,
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            }}>
              {gruppe.felder.map((feld) => (
                <label key={feld.name} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-secondary, var(--text-primary))' }}>
                    {feld.label}
                  </span>
                  <input
                    type={feld.typ || 'text'}
                    value={werte?.[feld.name] ?? ''}
                    disabled={!werte}
                    onChange={(e) => setWerte({ ...werte, [feld.name]: e.target.value })}
                    style={{
                      padding: '8px 10px', fontSize: 13,
                      borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)',
                      background: 'var(--bg-surface)', color: 'var(--text-primary)',
                      fontFamily: 'var(--font-sans)',
                    }}
                  />
                  {feld.hinweis && (
                    <span style={{ fontSize: 10, color: 'var(--text-tertiary)', lineHeight: 1.4 }}>
                      {feld.hinweis}
                    </span>
                  )}
                </label>
              ))}
            </div>
          </section>
        ))}

        <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
          <button type="submit" disabled={speichert || !anzahlGeaendert} style={{
            padding: '10px 22px', border: 'none', borderRadius: 'var(--radius-md)',
            background: 'var(--brand-primary)', color: 'var(--text-on-brand)',
            fontSize: 13, fontWeight: 700, fontFamily: 'var(--font-sans)',
            cursor: speichert || !anzahlGeaendert ? 'default' : 'pointer',
            opacity: speichert || !anzahlGeaendert ? 0.6 : 1,
          }}>
            {speichert ? 'Wird gespeichert …' : 'Änderungen speichern'}
          </button>
          <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
            {anzahlGeaendert === 0
              ? 'Keine Änderungen'
              : `${anzahlGeaendert} geändert${anzahlGeaendert === 1 ? '' : 'e'} Angabe${anzahlGeaendert === 1 ? '' : 'n'}`}
          </span>
        </div>
      </form>

      {fehler && (
        <div role="alert" style={meldung('error')}>{fehler}</div>
      )}
      {hinweis && (
        <div style={meldung('success')}>{hinweis}</div>
      )}

      <KundenChat leadId={leadId} token={token} />
    </div>
  );
}

const meldung = (art) => ({
  fontSize: 12, lineHeight: 1.5, padding: '10px 14px',
  borderRadius: 'var(--radius-md)',
  background: `var(--status-${art}-bg)`,
  color: `var(--status-${art}-text)`,
});
