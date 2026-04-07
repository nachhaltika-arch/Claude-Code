import { useState, useRef } from 'react';
import API_BASE_URL from '../config';

const LABEL_STYLE = {
  display: 'block', fontSize: 11, fontWeight: 600,
  color: '#64748b', textTransform: 'uppercase',
  letterSpacing: '0.06em', marginBottom: 6, marginTop: 16,
};

const INPUT_STYLE = {
  width: '100%', padding: '11px 14px',
  border: '1px solid #e2e8f0', borderRadius: 8,
  fontSize: 16,
  color: '#1a2332', background: 'white',
  boxSizing: 'border-box', marginBottom: 16,
  outline: 'none', fontFamily: 'inherit',
};

const SCHRITTE = [
  { nr: 1, titel: 'Willkommen',  icon: '👋' },
  { nr: 2, titel: 'Ihr Betrieb', icon: '🏢' },
  { nr: 3, titel: 'Unterlagen',  icon: '📁' },
];

export default function OnboardingWizard({ user, onComplete }) {
  const [step, setStep]       = useState(1);
  const [loading, setLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState({
    logo: null,
    foto: null,
  });
  const logoInputRef = useRef(null);
  const fotoInputRef = useRef(null);

  const [formData, setFormData] = useState({
    website_url:   '',
    gewerk:        '',
    leistungen:    '',
    einzugsgebiet: '',
    anmerkungen:   '',
  });

  const updateForm = (field, value) =>
    setFormData(prev => ({ ...prev, [field]: value }));

  const saveOnboarding = async () => {
    setLoading(true);
    try {
      await fetch(
        `${API_BASE_URL}/api/leads/portal-auth/complete-onboarding`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${localStorage.getItem('kompagnon_token')}`,
          },
          body: JSON.stringify({ ...formData, lead_id: user.lead_id }),
        }
      );
      onComplete();
    } catch (e) {
      console.error(e);
      onComplete();
    } finally {
      setLoading(false);
    }
  };

  const uploadFile = async (file, fileType) => {
    if (!user.lead_id || !file) return;
    setUploadStatus(prev => ({ ...prev, [fileType]: 'uploading' }));
    try {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('file_type', fileType);
      fd.append('note', `Onboarding-Upload: ${fileType}`);
      const res = await fetch(
        `${API_BASE_URL}/api/files/${user.lead_id}`,
        {
          method: 'POST',
          headers: { Authorization: `Bearer ${localStorage.getItem('kompagnon_token')}` },
          body: fd,
        }
      );
      setUploadStatus(prev => ({ ...prev, [fileType]: res.ok ? 'done' : 'error' }));
    } catch {
      setUploadStatus(prev => ({ ...prev, [fileType]: 'error' }));
    }
  };

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 9999,
      background: 'rgba(0,0,0,0.55)',
      display: 'flex', alignItems: 'center',
      justifyContent: 'center', padding: 20,
    }}>
      <div style={{
        background: 'white', borderRadius: 20,
        width: '100%', maxWidth: 520,
        maxHeight: '90vh', overflowY: 'auto',
        boxShadow: '0 20px 60px rgba(0,0,0,0.25)',
      }}>

        {/* Farbiger Header */}
        <div style={{
          background: '#008eaa', borderRadius: '20px 20px 0 0',
          padding: '24px 28px 20px',
        }}>
          <div style={{
            fontSize: 11, color: 'rgba(255,255,255,0.7)',
            fontWeight: 600, textTransform: 'uppercase',
            letterSpacing: '0.08em', marginBottom: 6,
          }}>
            KOMPAGNON · Erste Schritte
          </div>
          <div style={{ fontSize: 20, fontWeight: 700, color: 'white' }}>
            {SCHRITTE[step - 1].icon} {SCHRITTE[step - 1].titel}
          </div>

          {/* Fortschritts-Balken */}
          <div style={{ display: 'flex', gap: 6, marginTop: 16 }}>
            {SCHRITTE.map(s => (
              <div key={s.nr} style={{
                flex: 1, height: 4, borderRadius: 2,
                background: s.nr <= step ? 'white' : 'rgba(255,255,255,0.3)',
                transition: 'background 0.3s',
              }} />
            ))}
          </div>
          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.6)', marginTop: 6 }}>
            Schritt {step} von {SCHRITTE.length}
          </div>
        </div>

        {/* Inhalt */}
        <div style={{ padding: '28px 28px 24px' }}>

          {/* ── Schritt 1 ── */}
          {step === 1 && (
            <>
              <p style={{ fontSize: 15, color: '#1a2332', marginTop: 0, marginBottom: 6, fontWeight: 500 }}>
                Hallo{user.first_name ? ` ${user.first_name}` : ''}! 🎉
              </p>
              <p style={{ fontSize: 13, color: '#64748b', marginBottom: 24, lineHeight: 1.6 }}>
                Schön dass Sie da sind. Wir führen Sie in 3 kurzen
                Schritten durch die wichtigsten Infos — das dauert nur 2 Minuten.
              </p>
              <label style={LABEL_STYLE}>Ihre aktuelle Website-URL</label>
              <input
                type="url"
                value={formData.website_url}
                onChange={e => updateForm('website_url', e.target.value)}
                placeholder="https://ihre-website.de"
                style={INPUT_STYLE}
              />
              <p style={{ fontSize: 11, color: '#94a3b8', marginTop: -8, marginBottom: 0 }}>
                Falls Sie noch keine Website haben, lassen Sie das Feld leer.
              </p>
            </>
          )}

          {/* ── Schritt 2 ── */}
          {step === 2 && (
            <>
              <p style={{ fontSize: 13, color: '#64748b', marginTop: 0, marginBottom: 20, lineHeight: 1.6 }}>
                Diese Angaben helfen uns Ihre Website perfekt auf Ihren Betrieb zuzuschneiden.
              </p>
              <label style={LABEL_STYLE}>Gewerk / Branche</label>
              <input
                type="text"
                value={formData.gewerk}
                onChange={e => updateForm('gewerk', e.target.value)}
                placeholder="z.B. Sanitär, Elektriker, Maler, Schreiner..."
                style={INPUT_STYLE}
              />
              <label style={LABEL_STYLE}>Ihre Leistungen</label>
              <textarea
                rows={3}
                value={formData.leistungen}
                onChange={e => updateForm('leistungen', e.target.value)}
                placeholder="Was bieten Sie an? z.B. Badezimmerinstallation, Heizungswartung, Notdienst..."
                style={{ ...INPUT_STYLE, resize: 'vertical' }}
              />
              <label style={LABEL_STYLE}>Einzugsgebiet / Region</label>
              <input
                type="text"
                value={formData.einzugsgebiet}
                onChange={e => updateForm('einzugsgebiet', e.target.value)}
                placeholder="z.B. Koblenz und Umgebung, Rhein-Mosel-Kreis"
                style={INPUT_STYLE}
              />
            </>
          )}

          {/* ── Schritt 3 ── */}
          {step === 3 && (
            <>
              <p style={{ fontSize: 13, color: '#64748b', marginTop: 0, marginBottom: 20, lineHeight: 1.6 }}>
                Falls Sie bereits Unterlagen haben, können Sie diese direkt hier hochladen.
                Sie können das auch später jederzeit nachholen.
              </p>

              {/* Logo-Upload */}
              <div
                onClick={() => logoInputRef.current?.click()}
                style={{
                  border: uploadStatus.logo === 'done' ? '2px solid #1D9E75' : '2px dashed #e2e8f0',
                  borderRadius: 10, padding: '16px 20px', marginBottom: 12,
                  cursor: 'pointer',
                  background: uploadStatus.logo === 'done' ? '#F0FDF4' : '#fafafa',
                  display: 'flex', alignItems: 'center', gap: 14,
                  transition: 'all 0.2s',
                }}
              >
                <div style={{ fontSize: 28 }}>🎨</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: uploadStatus.logo === 'done' ? '#166534' : '#1a2332' }}>
                    {uploadStatus.logo === 'done' ? '✓ Logo hochgeladen'
                      : uploadStatus.logo === 'uploading' ? 'Wird hochgeladen...'
                      : 'Logo hochladen'}
                  </div>
                  <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2 }}>PNG, JPG, SVG · max. 20 MB</div>
                </div>
                {uploadStatus.logo !== 'done' && (
                  <div style={{ fontSize: 11, color: '#008eaa', fontWeight: 600, flexShrink: 0 }}>Auswählen</div>
                )}
              </div>
              <input ref={logoInputRef} type="file" accept=".png,.jpg,.jpeg,.svg,.pdf,.ai,.eps"
                style={{ display: 'none' }}
                onChange={e => { const f = e.target.files[0]; if (f) uploadFile(f, 'logo'); e.target.value = ''; }}
              />

              {/* Fotos-Upload */}
              <div
                onClick={() => fotoInputRef.current?.click()}
                style={{
                  border: uploadStatus.foto === 'done' ? '2px solid #1D9E75' : '2px dashed #e2e8f0',
                  borderRadius: 10, padding: '16px 20px', marginBottom: 20,
                  cursor: 'pointer',
                  background: uploadStatus.foto === 'done' ? '#F0FDF4' : '#fafafa',
                  display: 'flex', alignItems: 'center', gap: 14,
                  transition: 'all 0.2s',
                }}
              >
                <div style={{ fontSize: 28 }}>📷</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: uploadStatus.foto === 'done' ? '#166534' : '#1a2332' }}>
                    {uploadStatus.foto === 'done' ? '✓ Fotos hochgeladen'
                      : uploadStatus.foto === 'uploading' ? 'Wird hochgeladen...'
                      : 'Fotos hochladen'}
                  </div>
                  <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2 }}>Betriebsfotos, Team, Referenzen · max. 20 MB</div>
                </div>
                {uploadStatus.foto !== 'done' && (
                  <div style={{ fontSize: 11, color: '#008eaa', fontWeight: 600, flexShrink: 0 }}>Auswählen</div>
                )}
              </div>
              <input ref={fotoInputRef} type="file" accept=".jpg,.jpeg,.png,.webp" multiple
                style={{ display: 'none' }}
                onChange={e => { const f = e.target.files[0]; if (f) uploadFile(f, 'foto'); e.target.value = ''; }}
              />

              <label style={LABEL_STYLE}>Sonstige Hinweise (optional)</label>
              <textarea
                rows={2}
                value={formData.anmerkungen}
                onChange={e => updateForm('anmerkungen', e.target.value)}
                placeholder="Gibt es noch etwas das wir wissen sollten?"
                style={{ ...INPUT_STYLE, resize: 'none' }}
              />

              {/* Info-Box */}
              <div style={{
                background: '#E6F1FB', borderRadius: 8,
                padding: '12px 14px', fontSize: 12,
                color: '#0C447C', lineHeight: 1.6,
              }}>
                <div style={{ fontWeight: 600, marginBottom: 4 }}>Was jetzt passiert:</div>
                <div>• Wir melden uns innerhalb von 24 Stunden</div>
                <div>• Strategy Workshop vereinbaren (ca. 60 Min.)</div>
                <div>• Ihre neue Website in 14 Werktagen</div>
              </div>
            </>
          )}
        </div>

        {/* Footer mit Buttons */}
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
                border: '1px solid #e2e8f0', background: 'transparent',
                color: '#64748b', fontSize: 14, cursor: 'pointer',
              }}>
              ← Zurück
            </button>
          )}

          {step < SCHRITTE.length ? (
            <button
              onClick={() => setStep(s => s + 1)}
              style={{
                padding: '11px 24px', borderRadius: 8, border: 'none',
                background: '#008eaa', color: 'white',
                fontSize: 14, fontWeight: 600, cursor: 'pointer',
              }}>
              Weiter →
            </button>
          ) : (
            <button
              onClick={saveOnboarding}
              disabled={loading}
              style={{
                padding: '11px 24px', borderRadius: 8, border: 'none',
                background: loading ? '#94a3b8' : '#1D9E75',
                color: 'white', fontSize: 14, fontWeight: 600,
                cursor: loading ? 'not-allowed' : 'pointer',
              }}>
              {loading ? 'Wird gespeichert...' : 'Jetzt starten! 🚀'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
