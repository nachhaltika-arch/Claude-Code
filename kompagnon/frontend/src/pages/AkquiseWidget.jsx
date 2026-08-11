/**
 * Akquise → Widget: Einbindung, Datenschutz-Link und E-Mail-Versand.
 *
 * Hier wird gepflegt, was das Widget auf fremden Landingpages anzeigt und
 * über welchen Zugang die Berichts-E-Mails rausgehen. Ohne diese Seite müsste
 * beides im Render-Dashboard gesetzt werden.
 */
import React, { useCallback, useEffect, useState } from 'react';
import toast from 'react-hot-toast';

import { apiCall } from '../context/AuthContext';
import { parseApiError, parseResponseJson } from '../utils/apiError';

const LEERE_SMTP = {
  host: '', port: 587, user: '', password: '',
  sender_name: 'KOMPAGNON', sender_email: '',
};

async function anfrage(url, options = {}) {
  const response = await apiCall(url, options);
  const data = await parseResponseJson(response);
  if (!response.ok) {
    throw new Error(parseApiError(data, response.status));
  }
  return data;
}

function Abschnitt({ titel, hinweis, children }) {
  return (
    <section className="kc-card" style={{ marginBottom: 20 }}>
      <h3 style={{ margin: '0 0 4px', fontSize: 15 }}>{titel}</h3>
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

export default function AkquiseWidget() {
  const [widget, setWidget] = useState(null);
  const [smtp, setSmtp] = useState(null);
  const [smtpForm, setSmtpForm] = useState(LEERE_SMTP);
  const [testEmpfaenger, setTestEmpfaenger] = useState('');
  const [laedt, setLaedt] = useState(true);
  const [speichert, setSpeichert] = useState('');

  const laden = useCallback(async () => {
    setLaedt(true);
    try {
      const [w, s] = await Promise.all([
        anfrage('/api/acquisition/widget'),
        anfrage('/api/acquisition/smtp'),
      ]);
      setWidget(w);
      setSmtp(s);
      setSmtpForm({
        host: s.host || '', port: s.port || 587, user: s.user || '', password: '',
        sender_name: s.sender_name || 'KOMPAGNON', sender_email: s.sender_email || '',
      });
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

  async function smtpSpeichern(event) {
    event.preventDefault();
    setSpeichert('smtp');
    try {
      const aktualisiert = await anfrage('/api/acquisition/smtp', {
        method: 'PUT',
        body: JSON.stringify({ ...smtpForm, port: Number(smtpForm.port) || 587 }),
      });
      setSmtp(aktualisiert);
      setSmtpForm((alt) => ({ ...alt, password: '' }));
      toast.success('E-Mail-Zugang gespeichert');
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
      const ergebnis = await anfrage('/api/acquisition/smtp/test', {
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
    const code = `<iframe src="${widget.embed_url}" style="width:100%;max-width:680px;height:760px;border:0;display:block;margin:0 auto;" title="KOMPAGNON Website-Analyse" loading="lazy"></iframe>`;
    navigator.clipboard.writeText(code)
      .then(() => toast.success('Einbaucode kopiert'))
      .catch(() => toast.error('Kopieren nicht möglich — bitte manuell markieren.'));
  }

  if (laedt) return <div style={{ padding: 24 }}>Einstellungen werden geladen…</div>;
  if (!widget || !smtp) {
    return (
      <div style={{ padding: 24 }}>
        <p>Die Einstellungen konnten nicht geladen werden.</p>
        <button className="kc-btn" onClick={laden}>Erneut versuchen</button>
      </div>
    );
  }

  return (
    <div style={{ padding: 24, maxWidth: 1180 }}>
      <div style={{ marginBottom: 20 }}>
        <span style={{ fontSize: 11, letterSpacing: '.1em', textTransform: 'uppercase',
                       color: 'var(--text-tertiary)' }}>Akquise</span>
        <h2 style={{ margin: '4px 0 0' }}>Analyse-Widget</h2>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: '6px 0 0' }}>
          {widget.requests_total} Anfragen insgesamt · {widget.requests_confirmed} bestätigte
          Einwilligungen zur Kontaktaufnahme.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) 420px', gap: 20 }}>
        <div>
          <Abschnitt
            titel="Einbindung"
            hinweis="Diesen Code auf der fremden Landingpage einfügen. Änderungen an den
                     Einstellungen unten wirken sofort — der Code muss dafür nicht getauscht werden."
          >
            <pre style={{
              background: 'var(--bg-app)', border: '1px solid var(--border-light)',
              borderRadius: 6, padding: 12, fontSize: 11, overflowX: 'auto', margin: 0,
            }}>
{`<iframe src="${widget.embed_url}"
  style="width:100%;max-width:680px;height:760px;border:0;
         display:block;margin:0 auto;"
  title="KOMPAGNON Website-Analyse" loading="lazy"></iframe>`}
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

          <Abschnitt
            titel="E-Mail-Versand (SMTP)"
            hinweis="Über diesen Zugang gehen die Berichts-E-Mails raus. Das Passwort wird
                     verschlüsselt gespeichert und nie wieder angezeigt."
          >
            {!smtp.encryption_available && (
              <p style={{ background: '#FDECEA', borderLeft: '3px solid var(--brand-primary)',
                          padding: '10px 12px', fontSize: 12, borderRadius: 5, marginBottom: 14 }}>
                CREDENTIALS_KEY fehlt auf dem Server — solange kann kein Passwort
                gespeichert werden.
              </p>
            )}
            <form onSubmit={smtpSpeichern}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 110px', gap: 12 }}>
                <Feld
                  label="Server" value={smtpForm.host} required
                  onChange={(e) => setSmtpForm({ ...smtpForm, host: e.target.value })}
                  placeholder="smtp.strato.de"
                />
                <Feld
                  label="Port" type="number" value={smtpForm.port}
                  onChange={(e) => setSmtpForm({ ...smtpForm, port: e.target.value })}
                />
              </div>
              <Feld
                label="Benutzer" value={smtpForm.user} required
                onChange={(e) => setSmtpForm({ ...smtpForm, user: e.target.value })}
                placeholder="versand@kompagnon.de"
              />
              <Feld
                label="Passwort" type="password" value={smtpForm.password}
                onChange={(e) => setSmtpForm({ ...smtpForm, password: e.target.value })}
                placeholder={smtp.password_set ? '•••••••• (hinterlegt)' : 'Passwort eingeben'}
                hinweis={smtp.password_set
                  ? `Hinterlegt (Quelle: ${smtp.password_source}). Leer lassen, um es zu behalten.`
                  : 'Noch kein Passwort hinterlegt.'}
              />
              <Feld
                label="Absendername" value={smtpForm.sender_name}
                onChange={(e) => setSmtpForm({ ...smtpForm, sender_name: e.target.value })}
              />
              <Feld
                label="Absenderadresse" type="email" value={smtpForm.sender_email}
                onChange={(e) => setSmtpForm({ ...smtpForm, sender_email: e.target.value })}
                placeholder="analyse@kompagnon.de"
              />
              <button className="kc-btn" type="submit" disabled={speichert === 'smtp'}>
                {speichert === 'smtp' ? 'Speichert…' : 'Zugang speichern'}
              </button>
            </form>

            <div style={{ marginTop: 18, paddingTop: 16, borderTop: '1px solid var(--border-light)' }}>
              <Feld
                label="Test-E-Mail senden an" type="email" value={testEmpfaenger}
                onChange={(e) => setTestEmpfaenger(e.target.value)}
                placeholder="ich@kompagnon.de"
              />
              <button className="kc-btn" type="button" onClick={testSenden}
                      disabled={speichert === 'test' || !smtp.configured}>
                {speichert === 'test' ? 'Sendet…' : 'Test senden'}
              </button>
              {!smtp.configured && (
                <span style={{ fontSize: 11, color: 'var(--text-tertiary)', marginLeft: 10 }}>
                  Erst Server und Benutzer speichern.
                </span>
              )}
            </div>
          </Abschnitt>
        </div>

        <div>
          <Abschnitt titel="Vorschau" hinweis="So sehen Interessenten das Widget.">
            <iframe
              src={widget.embed_url}
              title="Widget-Vorschau"
              style={{ width: '100%', height: 760, border: '1px solid var(--border-light)',
                       borderRadius: 8, background: '#fff' }}
            />
          </Abschnitt>
        </div>
      </div>
    </div>
  );
}
