import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { apiCall } from '../context/AuthContext';

const NAVY = '#0F1E3A';

export default function TwoFactorSetup() {
  const navigate = useNavigate();
  const [step, setStep] = useState('start'); // start | scan | backup
  const [secret, setSecret] = useState('');
  const [qrCode, setQrCode] = useState('');
  const [code, setCode] = useState('');
  const [backupCodes, setBackupCodes] = useState([]);
  const [loading, setLoading] = useState(false);

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
    if (code.length !== 6) { toast.error('Bitte 6-stelligen Code eingeben'); return; }
    setLoading(true);
    try {
      const res = await apiCall('/api/auth/2fa/verify-setup', { method: 'POST', body: JSON.stringify({ totp_code: code }) });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);
      setBackupCodes(data.backup_codes);
      setStep('backup');
      toast.success('2FA erfolgreich aktiviert!');
    } catch (e) { toast.error(e.message); }
    finally { setLoading(false); }
  };

  const copyBackupCodes = () => {
    navigator.clipboard.writeText(backupCodes.join('\n'));
    toast.success('Backup-Codes kopiert');
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

  const cardStyle = { background: '#fff', borderRadius: 16, padding: '36px 32px', maxWidth: 480, width: '100%', margin: '40px auto', boxShadow: '0 4px 24px rgba(0,0,0,0.06)' };
  const btnStyle = { width: '100%', padding: '12px', background: NAVY, color: '#fff', border: 'none', borderRadius: 8, fontSize: 15, fontWeight: 700, cursor: 'pointer', minHeight: 48 };

  return (
    <div style={cardStyle}>
      {step === 'start' && (
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>🔐</div>
          <h2 style={{ fontSize: 20, color: NAVY, marginBottom: 12 }}>Zwei-Faktor-Authentifizierung einrichten</h2>
          <p style={{ fontSize: 14, color: '#4a5a7a', marginBottom: 24 }}>
            Schuetzen Sie Ihr Konto mit einem zweiten Faktor. Sie benoetigen eine Authenticator-App wie Google Authenticator oder Authy.
          </p>
          <button onClick={startSetup} disabled={loading} style={btnStyle}>
            {loading ? 'Wird vorbereitet...' : '2FA einrichten'}
          </button>
          <button onClick={() => navigate('/app/profile')} style={{ background: 'none', border: 'none', color: '#4a5a7a', marginTop: 16, cursor: 'pointer', fontSize: 13 }}>
            Zurueck zum Profil
          </button>
        </div>
      )}

      {step === 'scan' && (
        <div style={{ textAlign: 'center' }}>
          <h2 style={{ fontSize: 18, color: NAVY, marginBottom: 16 }}>QR-Code scannen</h2>
          <p style={{ fontSize: 13, color: '#4a5a7a', marginBottom: 16 }}>
            Scannen Sie diesen QR-Code mit Ihrer Authenticator-App:
          </p>
          {qrCode && (
            <div style={{ display: 'inline-block', padding: 12, background: '#fff', border: '1px solid #eef0f8', borderRadius: 12, marginBottom: 16 }}>
              <img src={`data:image/png;base64,${qrCode}`} alt="2FA QR Code" style={{ width: 200, height: 200 }} />
            </div>
          )}
          <div style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 12, color: '#5a6878', marginBottom: 4 }}>Oder manuell eingeben:</div>
            <div style={{ fontFamily: 'monospace', fontSize: 14, fontWeight: 700, color: NAVY, background: '#f0f2f8', padding: '8px 16px', borderRadius: 8, display: 'inline-block', wordBreak: 'break-all' }}>
              {secret}
            </div>
          </div>
          <div style={{ marginBottom: 16 }}>
            <label style={{ fontSize: 13, fontWeight: 600, color: '#4a5a74', display: 'block', marginBottom: 6 }}>6-stelliger Code</label>
            <input
              value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
              style={{ width: '100%', padding: '12px', border: '2px solid #d4d8e8', borderRadius: 8, fontSize: 22, textAlign: 'center', fontFamily: 'monospace', fontWeight: 700, letterSpacing: '0.3em', boxSizing: 'border-box' }}
              placeholder="000000" inputMode="numeric" maxLength={6}
            />
          </div>
          <button onClick={verifySetup} disabled={loading || code.length !== 6} style={{ ...btnStyle, opacity: code.length === 6 ? 1 : 0.5 }}>
            {loading ? 'Wird geprueft...' : '2FA aktivieren'}
          </button>
        </div>
      )}

      {step === 'backup' && (
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>✅</div>
          <h2 style={{ fontSize: 18, color: NAVY, marginBottom: 8 }}>2FA erfolgreich aktiviert!</h2>
          <p style={{ fontSize: 13, color: '#4a5a7a', marginBottom: 16 }}>
            Bewahren Sie diese Backup-Codes sicher auf. Jeder Code ist einmalig nutzbar.
          </p>
          <div style={{ background: '#f8f9fc', borderRadius: 10, padding: '16px 20px', marginBottom: 16, textAlign: 'left' }}>
            {backupCodes.map((code, i) => (
              <div key={i} style={{ fontFamily: 'monospace', fontSize: 15, fontWeight: 700, color: NAVY, padding: '4px 0' }}>
                {code}
              </div>
            ))}
          </div>
          <div style={{ color: '#c07820', fontSize: 13, fontWeight: 600, marginBottom: 16 }}>
            Diese Codes werden nur einmal angezeigt!
          </div>
          <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
            <button onClick={copyBackupCodes} style={{ flex: 1, background: '#f0f2f8', color: NAVY, border: 'none', borderRadius: 8, padding: '10px', fontSize: 13, fontWeight: 700, cursor: 'pointer', minHeight: 44 }}>
              Kopieren
            </button>
            <button onClick={downloadBackupCodes} style={{ flex: 1, background: '#f0f2f8', color: NAVY, border: 'none', borderRadius: 8, padding: '10px', fontSize: 13, fontWeight: 700, cursor: 'pointer', minHeight: 44 }}>
              Download
            </button>
          </div>
          <button onClick={() => navigate('/app/profile')} style={btnStyle}>Fertig</button>
        </div>
      )}
    </div>
  );
}
