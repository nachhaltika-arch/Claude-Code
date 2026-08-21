/**
 * Akquise → Analyse-Widget: Einbindung, Anzeige-Einstellungen, Anfragen.
 *
 * Das Widget läuft auf einer fremden Landingpage. Diese Seite liefert deshalb
 * alles, was für den Einbau dort nötig ist — Code zum Kopieren, eine Vorschau,
 * die sich genauso verhält wie die Einbettung beim Kunden, und den Nachweis,
 * dass die Berichte tatsächlich rausgehen.
 *
 * Der E-Mail-Zugang wird hier nur noch angezeigt: seit dem Wechsel auf die
 * Brevo-Transaktions-API kommt er aus der Umgebung und ist nichts, was hier
 * einzustellen wäre.
 */
import React, { useCallback, useEffect, useRef, useState } from 'react';
import toast from 'react-hot-toast';

import { apiCall } from '../context/AuthContext';
import { parseApiError, parseResponseJson } from '../utils/apiError';
import { useScreenSize } from '../utils/responsive';
import { buildEmbedCode, embedOrigin, START_HEIGHT_PX } from '../utils/widgetEmbed';
import { datumUndZeit } from '../utils/datum';

async function anfrage(url, options = {}) {
  const response = await apiCall(url, options);
  const data = await parseResponseJson(response);
  if (!response.ok) {
    throw new Error(parseApiError(data, response.status));
  }
  return data;
}

/* Frischemarker für die Vorschau. Browser halten eine einmal geladene
   Widget-Fassung fest; wer die Adresse aufrief, als sie noch von der
   React-App verschluckt wurde, sah im Rahmen dauerhaft das Dashboard.
   Einmal pro Seitenaufruf berechnet — als Wert im Rendern erzeugt, würde
   das iframe bei jedem Rendern neu laden. Der Einbaucode für Kunden bleibt
   bewusst ohne Marker: dort sorgt der no-cache-Header des Servers dafür. */
const VORSCHAU_MARKER = Date.now();

function zeitpunkt(iso) {
  if (!iso) return '—';
  return datumUndZeit(iso);
}

// ── Bausteine ────────────────────────────────────────────────────────

function Abschnitt({ titel, hinweis, kopfzeile, children }) {
  return (
    <section className="kc-card" style={{ marginBottom: 20 }}>
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between',
                    gap: 12, flexWrap: 'wrap' }}>
        <h2 style={{ margin: '0 0 4px', fontSize: 15 }}>{titel}</h2>
        {kopfzeile}
      </div>
      {hinweis && (
        <p style={{ margin: '0 0 16px', fontSize: 12, color: 'var(--text-tertiary)', lineHeight: 1.5 }}>
          {hinweis}
        </p>
      )}
      {children}
    </section>
  );
}

function Feld({ label, hinweis, ...props }) {
  return (
    <label style={{ display: 'block', marginBottom: 14 }}>
      <span style={{ display: 'block', fontSize: 12, fontWeight: 600, marginBottom: 5 }}>
        {label}
      </span>
      <input
        {...props}
        style={{
          width: '100%', padding: '9px 11px', fontSize: 13,
          border: '1px solid var(--border-light)', borderRadius: 6,
          background: 'var(--bg-app)', color: 'var(--text-primary)',
        }}
      />
      {hinweis && (
        <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{hinweis}</span>
      )}
    </label>
  );
}

/** Ampel für einen Zustand — grün wenn in Ordnung, sonst gedämpftes Rot. */
function Zustand({ ok, children, title }) {
  return (
    <span
      title={title}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12,
        fontWeight: 600, color: ok ? 'var(--kc-success, #1D9E75)' : '#C0392B',
      }}
    >
      <span aria-hidden="true" style={{
        width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
        background: 'currentColor',
      }} />
      {children}
    </span>
  );
}

function Kennzahl({ wert, label }) {
  return (
    <div>
      <div style={{ fontSize: 22, fontWeight: 700, lineHeight: 1.1 }}>{wert}</div>
      <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{label}</div>
    </div>
  );
}

// ── Vorschau ─────────────────────────────────────────────────────────

/**
 * Hält die Vorschauhöhe an der Höhenmeldung des Widgets.
 *
 * Bewusst dieselbe Prüfung wie im Einbaucode für den Kunden: Herkunft und
 * Absenderrahmen werden kontrolliert. Was hier funktioniert, funktioniert
 * damit auch auf der fremden Landingpage.
 */
function useVorschauHoehe(embedUrl) {
  const [hoehe, setHoehe] = useState(START_HEIGHT_PX);
  const rahmen = useRef(null);

  useEffect(() => {
    const herkunft = embedOrigin(embedUrl);

    function beiNachricht(ereignis) {
      if (ereignis.origin !== herkunft) return;
      if (!ereignis.data || ereignis.data.type !== 'kpg-audit-height') return;
      if (rahmen.current && rahmen.current.contentWindow !== ereignis.source) return;
      const gemeldet = parseInt(ereignis.data.height, 10);
      if (gemeldet > 0) setHoehe(gemeldet);
    }

    window.addEventListener('message', beiNachricht);
    return () => window.removeEventListener('message', beiNachricht);
  }, [embedUrl]);

  return [hoehe, rahmen];
}

function Vorschau({ embedUrl }) {
  const [hoehe, rahmen] = useVorschauHoehe(embedUrl);

  return (
    <Abschnitt
      titel="Vorschau"
      hinweis="So sehen Interessenten das Widget. Der Rahmen wächst mit dem Inhalt —
               genau wie mit dem Einbaucode auf der Kundenseite."
      kopfzeile={
        <a href={embedUrl} target="_blank" rel="noopener noreferrer"
           style={{ fontSize: 12, fontWeight: 600, color: 'var(--brand-primary)' }}>
          In neuem Tab öffnen ↗
        </a>
      }
    >
      <iframe
        ref={rahmen}
        src={`${embedUrl}?v=${VORSCHAU_MARKER}`}
        title="Widget-Vorschau"
        style={{ width: '100%', height: hoehe, border: '1px solid var(--border-light)',
                 borderRadius: 8, background: '#fff', transition: 'height .2s' }}
      />
    </Abschnitt>
  );
}

// ── Versandweg ───────────────────────────────────────────────────────

function Versand({ kanal, aktion, laeuft, empfaenger, setEmpfaenger }) {
  return (
    <Abschnitt
      titel="E-Mail-Versand"
      hinweis="Über diesen Weg gehen die Berichte an die Interessenten. Der Zugang
               kommt aus der Server-Umgebung und wird hier nicht eingestellt."
      kopfzeile={<Zustand ok={kanal.ready} title={kanal.detail}>{kanal.label}</Zustand>}
    >
      <dl style={{ margin: '0 0 16px', fontSize: 12, display: 'grid',
                   gridTemplateColumns: 'auto 1fr', gap: '6px 14px' }}>
        <dt style={{ color: 'var(--text-tertiary)' }}>Absender</dt>
        <dd style={{ margin: 0 }}>
          {kanal.sender_name} &lt;{kanal.sender_email || 'Vorgabe'}&gt;
        </dd>
        <dt style={{ color: 'var(--text-tertiary)' }}>Zugang</dt>
        <dd style={{ margin: 0 }}>{kanal.detail}</dd>
      </dl>

      {!kanal.ready && (
        <p style={{ background: '#FDECEA', borderLeft: '3px solid #C0392B',
                    padding: '10px 12px', fontSize: 12, borderRadius: 5, marginBottom: 14 }}>
          Solange kein Versandweg eingerichtet ist, läuft die Analyse zwar durch,
          der Bericht erreicht den Interessenten aber nicht. BREVO_API_KEY in der
          Server-Umgebung setzen.
        </p>
      )}

      <Feld
        label="Test-E-Mail senden an" type="email" value={empfaenger}
        onChange={(e) => setEmpfaenger(e.target.value)}
        placeholder="ich@kompagnon.de"
      />
      <button className="kc-btn" type="button" onClick={aktion}
              disabled={laeuft || !kanal.ready}>
        {laeuft ? 'Sendet…' : 'Test senden'}
      </button>
    </Abschnitt>
  );
}

// ── Anfragen ─────────────────────────────────────────────────────────

function Anfragen({ eintraege, limit }) {
  if (!eintraege.length) {
    return (
      <Abschnitt titel="Letzte Anfragen">
        <p style={{ fontSize: 13, color: 'var(--text-tertiary)', margin: 0 }}>
          Noch keine Anfragen eingegangen.
        </p>
      </Abschnitt>
    );
  }

  const kopf = { textAlign: 'left', padding: '6px 8px', fontSize: 11, fontWeight: 600,
                 color: 'var(--text-tertiary)', borderBottom: '1px solid var(--border-light)' };
  const zelle = { padding: '8px', borderBottom: '1px solid var(--border-light)',
                  verticalAlign: 'top' };

  return (
    <Abschnitt
      titel="Letzte Anfragen"
      hinweis={`Die jüngsten ${limit} Anfragen aus dem Widget. „Bericht" zeigt, ob die
                E-Mail mit der Analyse tatsächlich rausgegangen ist.`}
    >
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
          <thead>
            <tr>
              <th style={kopf}>Eingegangen</th>
              <th style={kopf}>E-Mail</th>
              <th style={kopf}>Website</th>
              <th style={kopf}>Bericht</th>
              <th style={kopf}>Einwilligung</th>
            </tr>
          </thead>
          <tbody>
            {eintraege.map((eintrag) => (
              <tr key={eintrag.id}>
                <td style={{ ...zelle, whiteSpace: 'nowrap' }}>{zeitpunkt(eintrag.created_at)}</td>
                <td style={zelle}>{eintrag.email}</td>
                <td style={{ ...zelle, maxWidth: 220, overflowWrap: 'anywhere' }}>
                  {eintrag.website_url}
                </td>
                {/* Vier Stufen, von hinten gelesen: abgerufen schlägt
                    versendet, versendet setzt die bestätigte Adresse voraus.
                    Ohne Bestätigung geht kein Berichtslink raus. */}
                <td style={zelle}>
                  <Zustand ok={eintrag.report_opened || eintrag.report_sent}>
                    {eintrag.report_opened ? 'abgerufen'
                      : eintrag.report_sent ? 'versendet'
                      : eintrag.verified ? 'bestätigt'
                      : eintrag.verify_sent ? 'wartet auf Bestätigung'
                      : 'offen'}
                  </Zustand>
                </td>
                <td style={{ ...zelle, color: 'var(--text-secondary)' }}>
                  {!eintrag.consent_marketing && 'nicht erteilt'}
                  {eintrag.consent_marketing && (eintrag.consent_confirmed
                    ? 'bestätigt' : 'unbestätigt')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Abschnitt>
  );
}

// ── Seite ────────────────────────────────────────────────────────────

export default function AkquiseWidget() {
  const [widget, setWidget] = useState(null);
  const [kanal, setKanal] = useState(null);
  const [anfragen, setAnfragen] = useState({ requests: [], limit: 0 });
  const [testEmpfaenger, setTestEmpfaenger] = useState('');
  const [laedt, setLaedt] = useState(true);
  const [speichert, setSpeichert] = useState('');
  const { isDesktop } = useScreenSize();

  const laden = useCallback(async () => {
    setLaedt(true);
    try {
      const [w, m, a] = await Promise.all([
        anfrage('/api/acquisition/widget'),
        anfrage('/api/acquisition/mail'),
        anfrage('/api/acquisition/widget/requests'),
      ]);
      setWidget(w);
      setKanal(m);
      setAnfragen(a);
    } catch (error) {
      toast.error(error.message || 'Einstellungen konnten nicht geladen werden.');
    } finally {
      setLaedt(false);
    }
  }, []);

  useEffect(() => { laden(); }, [laden]);

  async function widgetSpeichern(event) {
    event.preventDefault();
    setSpeichert('widget');
    try {
      await anfrage('/api/acquisition/widget', {
        method: 'PUT',
        body: JSON.stringify({
          privacy_url: widget.privacy_url || '',
          checkout_url: widget.checkout_url || '',
          headline: widget.headline || '',
        }),
      });
      toast.success('Widget-Einstellungen gespeichert');
    } catch (error) {
      toast.error(error.message || 'Speichern fehlgeschlagen.');
    } finally {
      setSpeichert('');
    }
  }

  async function testSenden() {
    if (!testEmpfaenger.trim()) {
      toast.error('Bitte eine Empfängeradresse angeben.');
      return;
    }
    setSpeichert('test');
    try {
      const ergebnis = await anfrage('/api/acquisition/mail/test', {
        method: 'POST',
        body: JSON.stringify({ to: testEmpfaenger.trim() }),
      });
      toast.success(ergebnis.message || 'Test-E-Mail versendet');
    } catch (error) {
      toast.error(error.message || 'Test-E-Mail fehlgeschlagen.');
    } finally {
      setSpeichert('');
    }
  }

  function einbaucodeKopieren() {
    navigator.clipboard.writeText(buildEmbedCode(widget.embed_url))
      .then(() => toast.success('Einbaucode kopiert'))
      .catch(() => toast.error('Kopieren nicht möglich — bitte manuell markieren.'));
  }

  if (laedt) return <div style={{ padding: 24 }}>Einstellungen werden geladen…</div>;
  if (!widget || !kanal) {
    return (
      <div style={{ padding: 24 }}>
        <p>Die Einstellungen konnten nicht geladen werden.</p>
        <button className="kc-btn" onClick={laden}>Erneut versuchen</button>
      </div>
    );
  }

  const versendet = anfragen.requests.filter((r) => r.report_sent).length;

  return (
    <div style={{ padding: 24, maxWidth: 1180 }}>
      <div style={{ marginBottom: 20 }}>
        <span style={{ fontSize: 11, letterSpacing: '.1em', textTransform: 'uppercase',
                       color: 'var(--text-tertiary)' }}>Akquise</span>
        <h1 style={{ margin: '4px 0 14px', fontSize: 20, fontWeight: 700 }}>Analyse-Widget</h1>
        <div style={{ display: 'flex', gap: 32, alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <Kennzahl wert={widget.requests_total} label="Anfragen insgesamt" />
          <Kennzahl wert={versendet} label={`Berichte versendet (letzte ${anfragen.limit})`} />
          <Kennzahl wert={widget.requests_confirmed} label="Bestätigte Einwilligungen" />
          <Zustand ok={kanal.ready} title={kanal.detail}>
            Versand über {kanal.label}
          </Zustand>
        </div>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: isDesktop ? 'minmax(0,1fr) 420px' : 'minmax(0,1fr)',
        gap: 20,
        alignItems: 'start',
      }}>
        <div>
          <Abschnitt
            titel="Einbindung"
            hinweis="Diesen Code auf der fremden Landingpage einfügen — iframe und Skript
                     gehören zusammen. Das Skript führt die Höhe nach, sonst bleibt der
                     Rahmen auf Formularhöhe stehen und das Ergebnis wird abgeschnitten.
                     Änderungen an den Einstellungen unten wirken sofort, der Code muss
                     dafür nicht getauscht werden."
          >
            <pre style={{
              background: 'var(--bg-app)', border: '1px solid var(--border-light)',
              borderRadius: 6, padding: 12, fontSize: 11, lineHeight: 1.5,
              overflowX: 'auto', margin: 0,
            }}>
              {buildEmbedCode(widget.embed_url)}
            </pre>
            <button className="kc-btn" style={{ marginTop: 12 }} onClick={einbaucodeKopieren}>
              Einbaucode kopieren
            </button>
          </Abschnitt>

          <Abschnitt
            titel="Anzeige und Links"
            hinweis="Der Datenschutz-Link erscheint unter dem Formular. Ohne hinterlegte
                     Adresse wird er ausgeblendet — für eine Seite, die personenbezogene
                     Daten erhebt, sollte er gesetzt sein."
          >
            <form onSubmit={widgetSpeichern}>
              <Feld
                label="Überschrift im Widget"
                value={widget.headline || ''}
                onChange={(e) => setWidget({ ...widget, headline: e.target.value })}
                placeholder="Ihre Website jetzt analysieren"
              />
              <Feld
                label="Datenschutzerklärung"
                type="url"
                value={widget.privacy_url || ''}
                onChange={(e) => setWidget({ ...widget, privacy_url: e.target.value })}
                placeholder="https://kompagnon.de/datenschutz"
                hinweis="Vollständige Adresse inklusive https://"
              />
              <Feld
                label="Ziel des Aktions-Buttons"
                type="url"
                value={widget.checkout_url || ''}
                onChange={(e) => setWidget({ ...widget, checkout_url: e.target.value })}
                placeholder="https://kompagnon.de/angebot"
              />
              <button className="kc-btn" type="submit" disabled={speichert === 'widget'}>
                {speichert === 'widget' ? 'Speichert…' : 'Speichern'}
              </button>
            </form>
          </Abschnitt>

          <Versand
            kanal={kanal}
            aktion={testSenden}
            laeuft={speichert === 'test'}
            empfaenger={testEmpfaenger}
            setEmpfaenger={setTestEmpfaenger}
          />

          <Anfragen eintraege={anfragen.requests} limit={anfragen.limit} />
        </div>

        <div style={isDesktop ? { position: 'sticky', top: 20 } : undefined}>
          <Vorschau embedUrl={widget.embed_url} />
        </div>
      </div>
    </div>
  );
}
