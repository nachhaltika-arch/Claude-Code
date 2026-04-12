import { useState, useRef } from 'react';
import API_BASE_URL from '../config';

const SCHRITTE = [
  { nr: 1, titel: 'Willkommen',       icon: '👋' },
  { nr: 2, titel: 'Ihr Betrieb',      icon: '🏢' },
  { nr: 3, titel: 'Unterlagen',       icon: '📁' },
  { nr: 4, titel: 'Nächste Schritte', icon: '🚀' },
];

const INP = {
  width: '100%', padding: '12px 14px',
  border: '1.5px solid #e2e8f0', borderRadius: 10,
  fontSize: 16, fontFamily: 'inherit',
  color: '#1a2332', background: 'white',
  boxSizing: 'border-box', marginBottom: 14, outline: 'none',
};

const LBL = {
  display: 'block', fontSize: 11, fontWeight: 600,
  color: '#64748b', textTransform: 'uppercase',
  letterSpacing: '0.06em', marginBottom: 6, marginTop: 16,
};

export default function OnboardingWizard({ user, onComplete }) {
  const [step, setStep]         = useState(1);
  const [saving, setSaving]     = useState(false);
  const [uploadStatus, setUploadStatus] = useState({ logo: null, foto: null });
  const logoRef = useRef(null);
  const fotoRef = useRef(null);
  const [form, setForm] = useState({
    website_url:   '',
    gewerk:        '',
    leistungen:    '',
    einzugsgebiet: '',
    anmerkungen:   '',
  });
  const upd = (f) => (e) =>
    setForm(p => ({ ...p, [f]: e.target.value }));

  const uploadFile = async (file, fileType) => {
    if (!user?.lead_id || !file) return;
    setUploadStatus(p => ({ ...p, [fileType]: 'uploading' }));
    const fd = new FormData();
    fd.append('file', file);
    fd.append('file_type', fileType);
    fd.append('note', `Onboarding: ${fileType}`);
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/files/${user.lead_id}`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${sessionStorage.getItem('kompagnon_token')}`,
          },
          body: fd,
        }
      );
      setUploadStatus(p => ({
        ...p, [fileType]: res.ok ? 'done' : 'error',
      }));
    } catch {
      setUploadStatus(p => ({ ...p, [fileType]: 'error' }));
    }
  };

  const saveAndFinish = async () => {
    setSaving(true);
    try {
      await fetch(
        `${API_BASE_URL}/api/leads/portal-auth/complete-onboarding`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${sessionStorage.getItem('kompagnon_token')}`,
          },
          body: JSON.stringify({
            lead_id: user.lead_id,
            ...form,
          }),
        }
      );
    } catch (e) {
      console.error('Onboarding save error:', e);
    } finally {
      setSaving(false);
    }
    // Schritt 4 (Abschluss) anzeigen — NICHT direkt schließen
    setStep(4);
  };

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 9999,
      background: 'rgba(15,25,40,0.6)',
      display: 'flex', alignItems: 'center',
      justifyContent: 'center', padding: 20,
    }}>
      <div style={{
        background: 'white', borderRadius: 20, width: '100%',
        maxWidth: 520, maxHeight: '92vh', overflowY: 'auto',
        boxShadow: '0 24px 80px rgba(0,0,0,0.3)',
      }}>

        {/* ── Farbiger Header ── */}
        <div style={{
          background: '#008eaa',
          borderRadius: '20px 20px 0 0',
          padding: '22px 28px 18px',
        }}>
          <div style={{
            fontSize: 10, color: 'rgba(255,255,255,0.65)',
            fontWeight: 700, textTransform: 'uppercase',
            letterSpacing: '0.1em', marginBottom: 4,
          }}>
            KOMPAGNON · Erste Schritte
          </div>
          <div style={{ fontSize: 19, fontWeight: 700, color: 'white' }}>
            {SCHRITTE[step - 1].icon} {SCHRITTE[step - 1].titel}
          </div>

          {/* Fortschrittsbalken */}
          <div style={{ display: 'flex', gap: 5, marginTop: 14 }}>
            {SCHRITTE.map(s => (
              <div key={s.nr} style={{
                flex: 1, height: 3, borderRadius: 2,
                background: s.nr <= step
                  ? 'white' : 'rgba(255,255,255,0.28)',
                transition: 'background 0.3s',
              }} />
            ))}
          </div>
          <div style={{
            fontSize: 11, color: 'rgba(255,255,255,0.55)',
            marginTop: 5,
          }}>
            {step < 4
              ? `Schritt ${step} von 3`
              : 'Abgeschlossen ✓'}
          </div>
        </div>

        {/* ── Inhalt ── */}
        <div style={{ padding: '26px 28px 22px' }}>

          {/* SCHRITT 1 — Willkommen & Website */}
          {step === 1 && (
            <>
              <p style={{
                fontSize: 14, color: '#1a2332',
                fontWeight: 500, marginTop: 0,
              }}>
                Hallo{user?.first_name ? ` ${user.first_name}` : ''}! 🎉
              </p>
              <p style={{
                fontSize: 13, color: '#64748b',
                lineHeight: 1.65, marginBottom: 20,
              }}>
                Ihr Kauf war erfolgreich. Wir brauchen noch
                3 kurze Angaben — das dauert etwa 2 Minuten.
              </p>

              <label style={LBL}>Ihre aktuelle Website-URL</label>
              <input
                type="url"
                value={form.website_url}
                onChange={upd('website_url')}
                placeholder="https://ihre-website.de"
                style={INP}
              />
              <p style={{
                fontSize: 11, color: '#94a3b8',
                marginTop: -10, marginBottom: 0,
              }}>
                Haben Sie noch keine Website? Lassen Sie das Feld leer.
              </p>
            </>
          )}

          {/* SCHRITT 2 — Betrieb */}
          {step === 2 && (
            <>
              <p style={{
                fontSize: 13, color: '#64748b',
                marginTop: 0, marginBottom: 4, lineHeight: 1.65,
              }}>
                Diese Infos helfen uns Ihre Website perfekt
                auf Ihr Gewerk zuzuschneiden.
              </p>

              <label style={LBL}>Gewerk / Branche *</label>
              <input
                type="text"
                value={form.gewerk}
                onChange={upd('gewerk')}
                placeholder="z.B. Sanitär, Elektriker, Maler, Schreiner..."
                style={INP}
              />

              <label style={LBL}>Ihre Leistungen</label>
              <textarea
                rows={3}
                value={form.leistungen}
                onChange={upd('leistungen')}
                placeholder="Was bieten Sie an? z.B. Badezimmer, Heizung, Notdienst, Wartung..."
                style={{ ...INP, resize: 'vertical' }}
              />

              <label style={LBL}>Einzugsgebiet / Region</label>
              <input
                type="text"
                value={form.einzugsgebiet}
                onChange={upd('einzugsgebiet')}
                placeholder="z.B. Koblenz und Umgebung, Rhein-Mosel-Kreis"
                style={INP}
              />
            </>
          )}

          {/* SCHRITT 3 — Unterlagen */}
          {step === 3 && (
            <>
              <p style={{
                fontSize: 13, color: '#64748b',
                marginTop: 0, marginBottom: 16, lineHeight: 1.65,
              }}>
                Haben Sie bereits Unterlagen? Laden Sie diese
                direkt hoch — oder später jederzeit nach.
              </p>

              {['logo', 'foto'].map((type) => {
                const st    = uploadStatus[type];
                const ref   = type === 'logo' ? logoRef : fotoRef;
                const label = type === 'logo'
                  ? { icon: '🎨', title: 'Firmenlogo hochladen',
                      hint: 'PNG, JPG, SVG, PDF · max. 20 MB' }
                  : { icon: '📷', title: 'Betriebsfotos hochladen',
                      hint: 'JPG, PNG, WebP · max. 20 MB · mehrere möglich' };
                return (
                  <div key={type}>
                    <div
                      onClick={() => st !== 'done' && ref.current?.click()}
                      style={{
                        border: st === 'done'
                          ? '2px solid #1D9E75'
                          : '2px dashed #e2e8f0',
                        borderRadius: 10, padding: '14px 18px',
                        marginBottom: 10, cursor: st === 'done'
                          ? 'default' : 'pointer',
                        background: st === 'done' ? '#F0FDF4' : '#fafafa',
                        display: 'flex', alignItems: 'center', gap: 14,
                        transition: 'all 0.2s',
                      }}
                    >
                      <div style={{ fontSize: 26 }}>{label.icon}</div>
                      <div style={{ flex: 1 }}>
                        <div style={{
                          fontSize: 13, fontWeight: 600,
                          color: st === 'done' ? '#166534' : '#1a2332',
                        }}>
                          {st === 'done'
                            ? `✓ ${type === 'logo' ? 'Logo' : 'Fotos'} hochgeladen`
                            : st === 'uploading' ? 'Wird hochgeladen...'
                            : label.title}
                        </div>
                        <div style={{
                          fontSize: 11, color: '#94a3b8', marginTop: 2,
                        }}>
                          {label.hint}
                        </div>
                      </div>
                      {st !== 'done' && (
                        <div style={{
                          fontSize: 11, color: '#008eaa',
                          fontWeight: 600, flexShrink: 0,
                        }}>
                          Auswählen
                        </div>
                      )}
                    </div>
                    <input
                      ref={ref}
                      type="file"
                      accept={type === 'logo'
                        ? '.png,.jpg,.jpeg,.svg,.pdf,.ai,.eps'
                        : '.jpg,.jpeg,.png,.webp'}
                      multiple={type === 'foto'}
                      style={{ display: 'none' }}
                      onChange={(e) => {
                        const f = e.target.files[0];
                        if (f) uploadFile(f, type);
                        e.target.value = '';
                      }}
                    />
                  </div>
                );
              })}

              <label style={LBL}>Sonstige Hinweise (optional)</label>
              <textarea
                rows={2}
                value={form.anmerkungen}
                onChange={upd('anmerkungen')}
                placeholder="Besondere Wünsche oder Hinweise für uns..."
                style={{ ...INP, resize: 'none' }}
              />
            </>
          )}

          {/* SCHRITT 4 — Strategy Workshop / Abschluss */}
          {step === 4 && (
            <>
              <div style={{ textAlign: 'center', marginBottom: 24 }}>
                <div style={{ fontSize: 52, marginBottom: 8 }}>🎉</div>
                <h3 style={{
                  color: '#1a2332', fontSize: 18,
                  fontWeight: 700, margin: '0 0 8px',
                }}>
                  Alles erledigt!
                </h3>
                <p style={{
                  color: '#64748b', fontSize: 13,
                  lineHeight: 1.65, margin: 0,
                }}>
                  Ihre Angaben wurden gespeichert. Wir melden uns
                  innerhalb von 24 Stunden für Ihren
                  Strategy Workshop.
                </p>
              </div>

              {/* Workshop-Info-Box */}
              <div style={{
                background: '#E1F5EE',
                border: '1.5px solid #1D9E75',
                borderRadius: 12, padding: '18px 20px',
                marginBottom: 20,
              }}>
                <div style={{
                  fontSize: 13, fontWeight: 700,
                  color: '#085041', marginBottom: 10,
                }}>
                  📅 Strategy Workshop — was Sie erwartet:
                </div>
                {[
                  'Ca. 60 Minuten · online per Video oder telefonisch',
                  'Wir analysieren gemeinsam Ihre bisherige Online-Präsenz',
                  'Sie erhalten konkrete Empfehlungen für Ihre neue Website',
                  'Wir definieren Texte, Struktur und Design gemeinsam',
                ].map((punkt, i) => (
                  <div key={i} style={{
                    display: 'flex', gap: 8, marginBottom: 6,
                    fontSize: 12, color: '#0F6E56',
                  }}>
                    <span>✓</span>
                    <span>{punkt}</span>
                  </div>
                ))}
              </div>

              {/* Termin-Anfrage */}
              <div style={{
                background: '#E6F1FB', borderRadius: 10,
                padding: '14px 18px', marginBottom: 20,
                textAlign: 'center',
              }}>
                <div style={{
                  fontSize: 12, color: '#0C447C',
                  marginBottom: 10, lineHeight: 1.5,
                }}>
                  Möchten Sie direkt einen Termin buchen?
                </div>
                <a
                  href="mailto:info@kompagnon.eu?subject=Strategy Workshop Termin"
                  style={{
                    display: 'inline-block',
                    background: '#008eaa', color: 'white',
                    padding: '10px 22px', borderRadius: 8,
                    textDecoration: 'none', fontSize: 13,
                    fontWeight: 600,
                  }}
                >
                  Termin anfragen →
                </a>
                <div style={{
                  fontSize: 11, color: '#378ADD', marginTop: 8,
                }}>
                  info@kompagnon.eu · wir antworten innerhalb 24h
                </div>
              </div>

              {/* Abschluss-Button */}
              <button
                onClick={onComplete}
                style={{
                  width: '100%', padding: '14px', border: 'none',
                  borderRadius: 10, background: '#1D9E75',
                  color: 'white', fontSize: 15, fontWeight: 700,
                  cursor: 'pointer', fontFamily: 'inherit',
                }}
              >
                Zum Kundenportal →
              </button>
            </>
          )}
        </div>

        {/* ── Footer mit Buttons ── */}
        {step < 4 && (
          <div style={{
            padding: '0 28px 24px',
            display: 'flex', gap: 10,
            justifyContent: step > 1 ? 'space-between' : 'flex-end',
          }}>
            {step > 1 && (
              <button
                onClick={() => setStep(s => s - 1)}
                style={{
                  padding: '11px 20px', borderRadius: 8,
                  border: '1px solid #e2e8f0',
                  background: 'transparent', color: '#64748b',
                  fontSize: 14, cursor: 'pointer',
                }}>
                ← Zurück
              </button>
            )}

            {step < 3 ? (
              <button
                onClick={() => setStep(s => s + 1)}
                style={{
                  padding: '11px 24px', borderRadius: 8,
                  border: 'none', background: '#008eaa',
                  color: 'white', fontSize: 14,
                  fontWeight: 600, cursor: 'pointer',
                }}>
                Weiter →
              </button>
            ) : (
              <button
                onClick={saveAndFinish}
                disabled={saving}
                style={{
                  padding: '11px 24px', borderRadius: 8,
                  border: 'none',
                  background: saving ? '#94a3b8' : '#008eaa',
                  color: 'white', fontSize: 14, fontWeight: 600,
                  cursor: saving ? 'not-allowed' : 'pointer',
                }}>
                {saving ? 'Speichert...' : 'Fertig & Absenden ✓'}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
