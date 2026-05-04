import { useState, useRef } from 'react';
import { QRCodeCanvas } from 'qrcode.react';

const PRIMARY = '#008eaa';
const BASE_URL = 'https://kompagnon-frontend.onrender.com/kampagne';

export default function QRGenerator() {
  const [slug, setSlug] = useState('');
  const qrRef = useRef(null);

  const url = slug.trim() ? `${BASE_URL}/${slug.trim()}` : '';

  const handleDownload = () => {
    const canvas = qrRef.current?.querySelector('canvas');
    if (!canvas) return;
    const link = document.createElement('a');
    link.download = `qr-${slug.trim() || 'kampagne'}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
  };

  return (
    <div style={{ maxWidth: 560, margin: '0 auto', padding: '32px 16px' }}>
      <h1 style={{
        fontFamily: 'var(--font-sans)', fontWeight: 700, fontSize: 22,
        color: 'var(--text-primary)', margin: '0 0 6px',
      }}>
        QR-Code Generator
      </h1>
      <p style={{ margin: '0 0 28px', fontSize: 14, color: 'var(--text-secondary)' }}>
        Erstelle einen QR-Code für eine Kampagnen-Landing-Page.
      </p>

      {/* Slug input */}
      <div style={{ marginBottom: 20 }}>
        <label style={{
          display: 'block', marginBottom: 6, fontSize: 13,
          fontWeight: 600, color: 'var(--text-primary)',
        }}>
          Kampagnen-Slug
        </label>
        <input
          type="text"
          value={slug}
          onChange={(e) => setSlug(e.target.value.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, ''))}
          placeholder="postkarte-koblenz-mai-2025"
          style={{
            width: '100%', boxSizing: 'border-box',
            padding: '12px 14px', fontSize: 15,
            border: '1.5px solid var(--border-light)',
            borderRadius: 8, background: 'var(--bg-surface)',
            color: 'var(--text-primary)', outline: 'none',
            fontFamily: 'var(--font-mono)',
          }}
        />
        <p style={{ margin: '6px 0 0', fontSize: 12, color: 'var(--text-tertiary)' }}>
          Nur Kleinbuchstaben, Zahlen und Bindestriche.
        </p>
      </div>

      {/* URL preview */}
      {url && (
        <div style={{
          marginBottom: 24, padding: '12px 14px',
          background: 'var(--bg-app)', border: '1px solid var(--border-light)',
          borderRadius: 8, wordBreak: 'break-all',
          fontSize: 13, fontFamily: 'var(--font-mono)', color: PRIMARY,
        }}>
          {url}
        </div>
      )}

      {/* QR preview */}
      {url && (
        <div style={{ marginBottom: 24 }}>
          <div
            ref={qrRef}
            style={{
              display: 'inline-flex', padding: 20,
              background: '#fff', borderRadius: 12,
              boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
              border: '1px solid var(--border-light)',
            }}
          >
            <QRCodeCanvas
              value={url}
              size={256}
              fgColor={PRIMARY}
              bgColor="#ffffff"
              level="M"
              includeMargin={false}
            />
          </div>
        </div>
      )}

      {/* Download button */}
      {url && (
        <button
          onClick={handleDownload}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            padding: '12px 24px', background: PRIMARY, color: '#fff',
            border: 'none', borderRadius: 8, fontSize: 14, fontWeight: 600,
            cursor: 'pointer', fontFamily: 'var(--font-sans)',
          }}
        >
          ↓ Als PNG herunterladen (qr-{slug.trim()}.png)
        </button>
      )}

      {/* Tip */}
      <div style={{
        marginTop: 32, padding: '14px 16px',
        background: '#f0f9ff', border: '1px solid #bae6fd',
        borderRadius: 8, fontSize: 13, color: '#0369a1', lineHeight: 1.6,
      }}>
        <strong>Tipp:</strong> Jeden Slug nur einmal nutzen – so erkennst du,
        welche Kampagne (Stadt, Monat) den Lead gebracht hat.
      </div>
    </div>
  );
}
