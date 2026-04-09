import React, { useState, useEffect, useCallback, useRef } from 'react';
import { createPortal } from 'react-dom';
import { QRCodeCanvas } from 'qrcode.react';
import toast from 'react-hot-toast';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

export const SOURCES = [
  { key: 'facebook',   label: 'Facebook',   icon: '📘', color: '#1877F2' },
  { key: 'linkedin',   label: 'LinkedIn',   icon: '💼', color: '#0A66C2' },
  { key: 'google_ads', label: 'Google Ads', icon: '🔍', color: '#EA4335' },
  { key: 'briefkarte', label: 'Briefkarte', icon: '📬', color: '#854F0B' },
  { key: 'instagram',  label: 'Instagram',  icon: '📸', color: '#E1306C' },
  { key: 'email',      label: 'E-Mail',     icon: '✉️', color: '#008EAA' },
  { key: 'sonstige',   label: 'Sonstige',   icon: '📌', color: '#64748B' },
];

export const SOURCE_ICONS = Object.fromEntries(SOURCES.map(s => [s.key, s.icon]));
export const SOURCE_LABELS = Object.fromEntries(SOURCES.map(s => [s.key, s.label]));
export const SOURCE_COLORS = Object.fromEntries(SOURCES.map(s => [s.key, s.color]));

export default function CampaignManager() {
  const { token } = useAuth();
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showNew, setShowNew] = useState(false);
  const [openQr, setOpenQr] = useState(null);
  const h = { Authorization: `Bearer ${token}` };

  const loadCampaigns = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/campaigns/`, { headers: h });
      if (res.ok) setCampaigns(await res.json());
    } catch (e) { console.error(e); }
    setLoading(false);
  }, [token]); // eslint-disable-line

  useEffect(() => { loadCampaigns(); }, [loadCampaigns]);

  const deleteCampaign = async (id, name) => {
    if (!window.confirm(`Kampagne "${name}" archivieren?`)) return;
    try {
      await fetch(`${API_BASE_URL}/api/campaigns/${id}`, { method: 'DELETE', headers: h });
      toast.success('Kampagne archiviert');
      loadCampaigns();
    } catch { toast.error('Fehler'); }
  };

  return (
    <div style={{ padding: '24px 32px', maxWidth: 1400, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)' }}>🎯 Kampagnen</div>
          <div style={{ fontSize: 13, color: 'var(--text-tertiary)', marginTop: 4 }}>
            {campaigns.length} aktive Kampagnen — UTM-Tracking + QR-Codes
          </div>
        </div>
        <button onClick={() => setShowNew(true)} style={{
          padding: '10px 20px', background: 'var(--brand-primary)', color: '#fff',
          border: 'none', borderRadius: 'var(--radius-md)', fontSize: 14, fontWeight: 600,
          cursor: 'pointer', fontFamily: 'var(--font-sans)',
        }}>
          + Neue Kampagne
        </button>
      </div>

      {loading && <div style={{ color: 'var(--text-tertiary)', padding: 40, textAlign: 'center' }}>Wird geladen…</div>}

      {!loading && campaigns.length === 0 && (
        <div style={{
          textAlign: 'center', padding: 64,
          background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
          borderRadius: 'var(--radius-lg)', color: 'var(--text-tertiary)',
        }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>🎯</div>
          <div style={{ fontSize: 14, marginBottom: 4 }}>Noch keine Kampagnen vorhanden</div>
          <div style={{ fontSize: 12 }}>Lege deine erste Kampagne an, um UTM-Tracking und QR-Codes zu generieren.</div>
        </div>
      )}

      {/* Campaign Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: 16 }}>
        {campaigns.map(c => {
          const color = SOURCE_COLORS[c.source] || 'var(--brand-primary)';
          return (
            <div key={c.id} style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-light)',
              borderRadius: 'var(--radius-lg)',
              overflow: 'hidden',
              display: 'flex', flexDirection: 'column',
              borderLeft: `4px solid ${color}`,
            }}>
              <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-light)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                  <span style={{ fontSize: 22 }}>{c.source_icon}</span>
                  <span style={{ fontSize: 11, fontWeight: 700, color, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    {c.source_label}
                  </span>
                </div>
                <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 3 }}>
                  {c.name}
                </div>
                {c.description && (
                  <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>{c.description}</div>
                )}
              </div>

              <div style={{ padding: '14px 20px', flex: 1, display: 'flex', flexDirection: 'column', gap: 10 }}>
                {/* Tracking-URL */}
                <div>
                  <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>
                    Tracking-URL
                  </div>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <input
                      readOnly
                      value={c.tracking_url}
                      onClick={e => e.target.select()}
                      style={{
                        flex: 1, padding: '7px 10px',
                        background: 'var(--bg-app)', border: '1px solid var(--border-light)',
                        borderRadius: 'var(--radius-md)', fontSize: 11,
                        color: 'var(--text-primary)', fontFamily: 'monospace',
                        outline: 'none',
                      }}
                    />
                    <button onClick={() => { navigator.clipboard.writeText(c.tracking_url); toast.success('Kopiert'); }}
                      style={{
                        padding: '7px 12px', background: 'var(--bg-app)',
                        border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)',
                        fontSize: 11, cursor: 'pointer', color: 'var(--text-secondary)',
                        fontFamily: 'var(--font-sans)', whiteSpace: 'nowrap',
                      }}>
                      📋
                    </button>
                  </div>
                </div>

                {/* Stats */}
                <div style={{ display: 'flex', gap: 14, padding: '8px 0' }}>
                  <div>
                    <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)' }}>{c.lead_count || 0}</div>
                    <div style={{ fontSize: 10, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Leads</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--status-success-text)' }}>{c.won_count || 0}</div>
                    <div style={{ fontSize: 10, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Gewonnen</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--brand-primary)' }}>
                      {c.lead_count ? Math.round(((c.won_count || 0) / c.lead_count) * 100) : 0}%
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Rate</div>
                  </div>
                </div>

                {/* QR + Archive */}
                <div style={{ display: 'flex', gap: 8, marginTop: 'auto' }}>
                  <button onClick={() => setOpenQr(openQr === c.id ? null : c.id)}
                    style={{
                      flex: 1, padding: '8px 12px',
                      background: openQr === c.id ? color : 'var(--bg-app)',
                      color: openQr === c.id ? '#fff' : 'var(--text-primary)',
                      border: '1px solid var(--border-light)',
                      borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 500,
                      cursor: 'pointer', fontFamily: 'var(--font-sans)',
                    }}>
                    {openQr === c.id ? '◄ QR ausblenden' : '🔳 QR anzeigen'}
                  </button>
                  <button onClick={() => deleteCampaign(c.id, c.name)}
                    title="Archivieren"
                    style={{
                      padding: '8px 12px',
                      background: 'none', border: '1px solid var(--border-light)',
                      borderRadius: 'var(--radius-md)', fontSize: 13,
                      cursor: 'pointer', color: 'var(--text-tertiary)',
                    }}>
                    ×
                  </button>
                </div>

                {openQr === c.id && (
                  <QrCodePanel campaign={c} color={color} />
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* New Campaign Modal */}
      {showNew && (
        <NewCampaignModal
          onClose={() => setShowNew(false)}
          onCreated={() => { setShowNew(false); loadCampaigns(); }}
          token={token}
        />
      )}
    </div>
  );
}


function QrCodePanel({ campaign, color }) {
  const ref = useRef(null);

  const download = () => {
    const canvas = ref.current?.querySelector('canvas');
    if (!canvas) return;
    const url = canvas.toDataURL('image/png');
    const a = document.createElement('a');
    a.href = url;
    a.download = `qr-${campaign.slug}.png`;
    a.click();
  };

  return (
    <div style={{
      marginTop: 10, padding: 14,
      background: 'var(--bg-app)', borderRadius: 'var(--radius-md)',
      border: '1px solid var(--border-light)',
      display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10,
    }}>
      <div ref={ref} style={{ background: '#fff', padding: 12, borderRadius: 8 }}>
        <QRCodeCanvas
          value={campaign.tracking_url}
          size={180}
          fgColor={color}
          bgColor="#ffffff"
          level="M"
        />
      </div>
      <button onClick={download} style={{
        padding: '8px 18px', background: color, color: '#fff',
        border: 'none', borderRadius: 'var(--radius-md)', fontSize: 12,
        fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)',
      }}>
        ↓ PNG herunterladen
      </button>
    </div>
  );
}


function NewCampaignModal({ onClose, onCreated, token }) {
  const [name, setName] = useState('');
  const [source, setSource] = useState('facebook');
  const [description, setDescription] = useState('');
  const [targetUrl, setTargetUrl] = useState('https://kompagnon.eu');
  const [saving, setSaving] = useState(false);

  const save = async () => {
    if (!name.trim()) { toast.error('Name ist erforderlich'); return; }
    setSaving(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/campaigns/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ name, source, description, target_url: targetUrl }),
      });
      if (res.ok) {
        toast.success('Kampagne angelegt');
        onCreated();
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || 'Fehler');
      }
    } catch { toast.error('Verbindungsfehler'); }
    setSaving(false);
  };

  const inputStyle = {
    width: '100%', boxSizing: 'border-box', padding: '10px 12px',
    border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)',
    background: 'var(--bg-app)', color: 'var(--text-primary)',
    fontSize: 13, fontFamily: 'var(--font-sans)', outline: 'none',
  };
  const labelStyle = { fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6, display: 'block' };

  return createPortal(
    <div
      onClick={e => e.target === e.currentTarget && onClose()}
      style={{
        position: 'fixed', top: 0, right: 0, bottom: 0, left: 0, zIndex: 2000,
        background: 'rgba(0,0,0,0.55)', backdropFilter: 'blur(4px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16,
      }}
    >
      <div style={{
        background: 'var(--bg-surface)', borderRadius: 16,
        width: '100%', maxWidth: 560, maxHeight: '90vh',
        display: 'flex', flexDirection: 'column', overflow: 'hidden',
        boxShadow: '0 32px 80px rgba(0,0,0,0.28)',
      }}>
        <div style={{ padding: '20px 28px', borderBottom: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--brand-primary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 3 }}>
              Neue Kampagne
            </div>
            <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)' }}>
              Quelle wählen + Details
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'var(--bg-app)', border: '1px solid var(--border-light)', width: 32, height: 32, borderRadius: 8, cursor: 'pointer', fontSize: 18, color: 'var(--text-secondary)' }}>×</button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: 24 }}>
          <div style={{ marginBottom: 18 }}>
            <label style={labelStyle}>Kanal *</label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 8 }}>
              {SOURCES.map(s => (
                <button
                  key={s.key}
                  type="button"
                  onClick={() => setSource(s.key)}
                  style={{
                    padding: '12px 8px',
                    background: source === s.key ? s.color : 'var(--bg-app)',
                    color: source === s.key ? '#fff' : 'var(--text-primary)',
                    border: `2px solid ${source === s.key ? s.color : 'var(--border-light)'}`,
                    borderRadius: 'var(--radius-md)',
                    cursor: 'pointer', fontFamily: 'var(--font-sans)',
                    fontSize: 12, fontWeight: 600,
                    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4,
                    transition: 'all 0.15s',
                  }}
                >
                  <span style={{ fontSize: 22 }}>{s.icon}</span>
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          <div style={{ marginBottom: 14 }}>
            <label style={labelStyle}>Kampagnen-Name *</label>
            <input style={inputStyle} value={name} onChange={e => setName(e.target.value)} placeholder="z.B. Facebook April 2026 Koblenz" />
          </div>

          <div style={{ marginBottom: 14 }}>
            <label style={labelStyle}>Ziel-URL</label>
            <input style={inputStyle} value={targetUrl} onChange={e => setTargetUrl(e.target.value)} placeholder="https://kompagnon.eu" />
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>
              Wohin der Kunde nach Klick weitergeleitet wird. Bei Briefkarten wird automatisch die Landing-Page verwendet.
            </div>
          </div>

          <div style={{ marginBottom: 14 }}>
            <label style={labelStyle}>Beschreibung (optional)</label>
            <textarea
              style={{ ...inputStyle, minHeight: 70, resize: 'vertical' }}
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="Interne Notizen zur Kampagne…"
            />
          </div>
        </div>

        <div style={{ padding: '16px 28px', borderTop: '1px solid var(--border-light)', display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
          <button onClick={onClose} style={{
            padding: '9px 18px', background: 'var(--bg-app)',
            border: '1px solid var(--border-light)', color: 'var(--text-secondary)',
            borderRadius: 'var(--radius-md)', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)',
          }}>
            Abbrechen
          </button>
          <button onClick={save} disabled={saving} style={{
            padding: '9px 22px', background: saving ? 'var(--text-tertiary)' : 'var(--brand-primary)',
            color: '#fff', border: 'none', borderRadius: 'var(--radius-md)',
            fontSize: 13, fontWeight: 600, cursor: saving ? 'wait' : 'pointer', fontFamily: 'var(--font-sans)',
          }}>
            {saving ? 'Speichern…' : 'Kampagne anlegen'}
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
