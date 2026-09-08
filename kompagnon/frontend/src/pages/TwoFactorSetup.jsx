/**
 * Einrichten **und** Abschalten der Zwei-Faktor-Anmeldung.
 *
 * **Abschalten kam am 08.09.2026 dazu (L-105).** `DELETE /2fa/disable` stand
 * seit Langem im Backend, und niemand rief es: „2FA verwalten" im Profil
 * führte auf dieselbe Einrichtungsmaske wie „2FA einrichten". Wer eingeschaltet
 * hatte, konnte hier nichts mehr tun.
 *
 * **Das ist kein Aussperrfall.** Die Route verlangt Passwort *und* gültigen
 * Code, hilft also niemandem, der sein Gerät verloren hat. Was fehlte, ist das
 * **freiwillige** Abschalten — und dafür ist diese Seite der Ort, weil das
 * Menü hierher führt.
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { apiCall, useAuth } from '../context/AuthContext';
import SeitenTitel from '../components/ui/SeitenTitel';
import { abschaltenBereit, nurZiffern } from '../utils/zweiFaktor';



export default function TwoFactorSetup() {
  const navigate = useNavigate();
  const { user, refreshUser } = useAuth();
  const [step, setStep] = useState('start'); // start | scan | backup | abschalten | abgeschaltet
  const [secret, setSecret] = useState('');
  const [qrCode, setQrCode] = useState('');
  const [code, setCode] = useState('');
  const [passwort, setPasswort] = useState('');
  const [backupCodes, setBackupCodes] = useState([]);
  const [loading, setLoading] = useState(false);

  // **Abgeleitet statt in einem Effekt gesetzt.** Der Benutzer kommt später
  // als der erste Aufbau; ein Effekt, der `step` nachträgt, schöbe nach dem
  // Abschalten wieder auf „aktiv", solange die Antwort von `/auth/me` noch
  // unterwegs ist — die Seite behauptete das Gegenteil dessen, was gerade
  // geschehen ist. `abgeschaltet` ist deshalb ein eigener Endzustand.
  const zeigt = (step === 'start' && user?.totp_enabled) ? 'aktiv' : step;

  const startSetup = async () => {
    setLoading(true);
    try {
      const res = await apiCall('/api/auth/2fa/setup', { method: 'POST' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);
      setSecret(data.secret);
      setQrCode(data.qr_code_base64);
      setStep('scan');
    } catch (e) { toast.error(e.message); }
    finally { setLoading(false); }
  };

  const verifySetup = async () => {
    if (code.length !== 6) { toast.error('Der Code muss genau 6 Ziffern haben — bitte Authenticator-App prüfen'); return; }
    setLoading(true);
    try {
      const res = await apiCall('/api/auth/2fa/verify-setup', { method: 'POST', body: JSON.stringify({ totp_code: code }) });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);
      setBackupCodes(data.backup_codes);
      setStep('backup');
      toast.success('✓ Zwei-Faktor-Authentifizierung aktiviert — Backup-Codes sicher aufbewahren');
    } catch (e) { toast.error(e.message); }
    finally { setLoading(false); }
  };

  /**
   * Abschalten — Passwort und gültiger Code, wie die Route sie verlangt.
   *
   * **Die Fehlermeldung des Servers wird durchgereicht, nicht ersetzt.** Er
   * unterscheidet „Passwort falsch" von „Ungueltiger 2FA-Code"; wer beides zu
   * „Angaben falsch" zusammenzieht, lässt jemanden am richtigen Passwort
   * zweifeln, während nur die Uhr seines Telefons abweicht.
   */
  const abschalten = async () => {
    if (!abschaltenBereit({ passwort, code })) return;
    setLoading(true);
    try {
      const res = await apiCall('/api/auth/2fa/disable', {
        method: 'DELETE',
        body: JSON.stringify({ password: passwort, totp_code: code }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Abschalten fehlgeschlagen');
      // Erst den Zustand leeren, dann den Benutzer neu holen: Passwort und
      // Code sollen nicht im Speicher stehen bleiben, wenn die Antwort hängt.
      setPasswort('');
      setCode('');
      setStep('abgeschaltet');
      toast.success('Zwei-Faktor-Authentifizierung abgeschaltet');
      if (refreshUser) await refreshUser();
    } catch (e) { toast.error(e.message); }
    finally { setLoading(false); }
  };

  const abschaltenAbbrechen = () => {
    setPasswort('');
    setCode('');
    setStep('start');
  };

  const copyBackupCodes = () => {
    navigator.clipboard.writeText(backupCodes.join('\n'));
    toast.success('Backup-Codes in Zwischenablage kopiert — sicher aufbewahren!');
  };

  const downloadBackupCodes = () => {
    const blob = new Blob([backupCodes.join('\n')], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'KOMPAGNON-Backup-Codes.txt';
    a.click();
    URL.revokeObjectURL(url);
  };

  const cardStyle = { background: 'var(--bg-surface)', borderRadius: 'var(--radius-xl)', padding: '36px 32px', maxWidth: 480, width: '100%', margin: '40px auto', boxShadow: '0 4px 24px rgba(0,0,0,0.06)' };
  const btnStyle = { width: '100%', padding: '12px', background: 'var(--brand-primary)', color: 'var(--text-on-brand)', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 15, fontWeight: 700, cursor: 'pointer', minHeight: 48 };

  return (
    <div style={cardStyle}>
      <SeitenTitel>Zwei-Faktor-Authentifizierung</SeitenTitel>
      {zeigt === 'start' && (
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>🔐</div>
          <h2 style={{ fontSize: 20, color: 'var(--text-primary)', marginBottom: 12 }}>Zwei-Faktor-Authentifizierung einrichten</h2>
          <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 24 }}>
            Schuetzen Sie Ihr Konto mit einem zweiten Faktor. Sie benoetigen eine Authenticator-App wie Google Authenticator oder Authy.
          </p>
          <button onClick={startSetup} disabled={loading} style={btnStyle}>
            {loading ? 'Wird vorbereitet...' : '2FA einrichten'}
          </button>
          <button onClick={() => navigate('/app/profile')} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', marginTop: 16, cursor: 'pointer', fontSize: 13 }}>
            Zurueck zum Profil
          </button>
        </div>
      )}

      {zeigt === 'aktiv' && (
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>🔐</div>
          <h2 style={{ fontSize: 20, color: 'var(--text-primary)', marginBottom: 12 }}>Zwei-Faktor-Authentifizierung ist aktiv</h2>
          <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 24 }}>
            Bei jeder Anmeldung fragen wir zusaetzlich nach dem Code aus Ihrer Authenticator-App.
          </p>
          <button onClick={() => setStep('abschalten')} data-testid="2fa-abschalten" style={{ ...btnStyle, background: 'var(--bg-app)', color: 'var(--text-primary)' }}>
            Zwei-Faktor-Authentifizierung abschalten
          </button>
          <button onClick={() => navigate('/app/profile')} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', marginTop: 16, cursor: 'pointer', fontSize: 13 }}>
            Zurueck zum Profil
          </button>
        </div>
      )}

      {zeigt === 'abschalten' && (
        <div>
          <h2 style={{ fontSize: 18, color: 'var(--text-primary)', marginBottom: 8 }}>Abschalten bestaetigen</h2>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
            Danach genuegt Ihr Passwort allein zur Anmeldung. Zur Bestaetigung
            brauchen wir Ihr Passwort und einen gueltigen Code aus der App.
          </p>
          <div style={{ marginBottom: 12 }}>
            <label htmlFor="2fa-passwort" style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>Passwort</label>
            <input id="2fa-passwort" type="password" autoComplete="current-password"
              value={passwort} onChange={(e) => setPasswort(e.target.value)}
              style={{ width: '100%', padding: '12px', border: '2px solid var(--border-light)', borderRadius: 'var(--radius-md)', fontSize: 15, boxSizing: 'border-box', background: 'var(--bg-surface)', color: 'var(--text-primary)' }}
            />
          </div>
          <div style={{ marginBottom: 16 }}>
            <label htmlFor="2fa-abschaltcode" style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>6-stelliger Code</label>
            <input id="2fa-abschaltcode" value={code}
              onChange={(e) => setCode(nurZiffern(e.target.value))}
              style={{ width: '100%', padding: '12px', border: '2px solid var(--border-light)', borderRadius: 'var(--radius-md)', fontSize: 22, textAlign: 'center', fontFamily: 'monospace', fontWeight: 700, letterSpacing: '0.3em', boxSizing: 'border-box', background: 'var(--bg-surface)', color: 'var(--text-primary)' }}
              placeholder="000000" inputMode="numeric" maxLength={6}
            />
          </div>
          {/* **Kein Aussperrfall, und das steht hier.** Wer sein Geraet
              verloren hat, kommt ueber diesen Weg nicht weiter — er braucht
              den Innendienst. Das jetzt zu sagen ist billiger als drei
              Fehlversuche. */}
          <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 16 }}>
            Kein Zugriff mehr auf die App? Dann hilft dieser Weg nicht weiter —
            bitte wenden Sie sich an uns.
          </p>
          <button onClick={abschalten} disabled={loading || !abschaltenBereit({ passwort, code })}
            style={{ ...btnStyle, opacity: abschaltenBereit({ passwort, code }) ? 1 : 0.5 }}>
            {loading ? 'Wird abgeschaltet...' : 'Jetzt abschalten'}
          </button>
          <button onClick={abschaltenAbbrechen} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', marginTop: 16, cursor: 'pointer', fontSize: 13, width: '100%' }}>
            Abbrechen
          </button>
        </div>
      )}

      {zeigt === 'abgeschaltet' && (
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>🔓</div>
          <h2 style={{ fontSize: 18, color: 'var(--text-primary)', marginBottom: 8 }}>Zwei-Faktor-Authentifizierung ist abgeschaltet</h2>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 20 }}>
            Ihre Backup-Codes sind damit ungueltig. Sie koennen den Schutz
            jederzeit wieder einrichten — dann bekommen Sie neue.
          </p>
          <button onClick={() => navigate('/app/profile')} style={btnStyle}>Fertig</button>
        </div>
      )}

      {zeigt === 'scan' && (
        <div style={{ textAlign: 'center' }}>
          <h2 style={{ fontSize: 18, color: 'var(--text-primary)', marginBottom: 16 }}>QR-Code scannen</h2>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
            Scannen Sie diesen QR-Code mit Ihrer Authenticator-App:
          </p>
          {qrCode && (
            <div style={{ display: 'inline-block', padding: 12, background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', marginBottom: 16 }}>
              <img src={`data:image/png;base64,${qrCode}`} alt="2FA QR Code" style={{ width: 200, height: 200 }} />
            </div>
          )}
          <div style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 4 }}>Oder manuell eingeben:</div>
            <div style={{ fontFamily: 'monospace', fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', background: 'var(--bg-app)', padding: '8px 16px', borderRadius: 'var(--radius-md)', display: 'inline-block', wordBreak: 'break-all' }}>
              {secret}
            </div>
          </div>
          <div style={{ marginBottom: 16 }}>
            <label style={{ fontSize: 13, fontWeight: 600, color: '#4a5a74', display: 'block', marginBottom: 6 }}>6-stelliger Code</label>
            <input aria-label="6-stelliger Code"
              value={code} onChange={(e) => setCode(nurZiffern(e.target.value))}
              style={{ width: '100%', padding: '12px', border: '2px solid #d4d8e8', borderRadius: 'var(--radius-md)', fontSize: 22, textAlign: 'center', fontFamily: 'monospace', fontWeight: 700, letterSpacing: '0.3em', boxSizing: 'border-box' }}
              placeholder="000000" inputMode="numeric" maxLength={6}
            />
          </div>
          <button onClick={verifySetup} disabled={loading || code.length !== 6} style={{ ...btnStyle, opacity: code.length === 6 ? 1 : 0.5 }}>
            {loading ? 'Wird geprueft...' : '2FA aktivieren'}
          </button>
        </div>
      )}

      {zeigt === 'backup' && (
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>✅</div>
          <h2 style={{ fontSize: 18, color: 'var(--text-primary)', marginBottom: 8 }}>2FA erfolgreich aktiviert!</h2>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
            Bewahren Sie diese Backup-Codes sicher auf. Jeder Code ist einmalig nutzbar.
          </p>
          <div style={{ background: '#f8f9fc', borderRadius: 10, padding: '16px 20px', marginBottom: 16, textAlign: 'left' }}>
            {backupCodes.map((code, i) => (
              <div key={i} style={{ fontFamily: 'monospace', fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', padding: '4px 0' }}>
                {code}
              </div>
            ))}
          </div>
          <div style={{ color: '#c07820', fontSize: 13, fontWeight: 600, marginBottom: 16 }}>
            Diese Codes werden nur einmal angezeigt!
          </div>
          <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
            <button onClick={copyBackupCodes} style={{ flex: 1, background: 'var(--bg-app)', color: 'var(--text-primary)', border: 'none', borderRadius: 'var(--radius-md)', padding: '10px', fontSize: 13, fontWeight: 700, cursor: 'pointer', minHeight: 44 }}>
              Kopieren
            </button>
            <button onClick={downloadBackupCodes} style={{ flex: 1, background: 'var(--bg-app)', color: 'var(--text-primary)', border: 'none', borderRadius: 'var(--radius-md)', padding: '10px', fontSize: 13, fontWeight: 700, cursor: 'pointer', minHeight: 44 }}>
              Download
            </button>
          </div>
          <button onClick={() => navigate('/app/profile')} style={btnStyle}>Fertig</button>
        </div>
      )}
    </div>
  );
}
