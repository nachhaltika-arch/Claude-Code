import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import toast from 'react-hot-toast';
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip as ReTooltip, CartesianGrid,
} from 'recharts';
import AuditReport from '../components/AuditReport';
import API_BASE_URL from '../config';
import { useScreenSize } from '../utils/responsive';

const LEVEL_COLORS = {
  'Homepage Standard Platin': '#7bb8e8',
  'Homepage Standard Gold': '#f0c040',
  'Homepage Standard Silber': '#c8c8c8',
  'Homepage Standard Bronze': '#d4915a',
  'Nicht konform': '#e04040',
};

const STATUS_LABELS = {
  new: { label: 'Neu', color: '#4a5a7a' },
  contacted: { label: 'Kontaktiert', color: '#2a7a9a' },
  qualified: { label: 'Qualifiziert', color: '#2a9a5a' },
  proposal_sent: { label: 'Angebot gesendet', color: '#c07820' },
  won: { label: 'Gewonnen', color: '#2a7a3a' },
  lost: { label: 'Verloren', color: '#c03030' },
};

const NAVY = '#0F1E3A';

const CAT_DEFS = [
  { label: 'Rechtliche Compliance', scoreKey: 'rc_score', max: 30 },
  { label: 'Technische Performance', scoreKey: 'tp_score', max: 20 },
  { label: 'Barrierefreiheit', scoreKey: 'bf_score', max: 20 },
  { label: 'Sicherheit & Datenschutz', scoreKey: 'si_score', max: 15 },
  { label: 'SEO & Sichtbarkeit', scoreKey: 'se_score', max: 10 },
  { label: 'Inhalt & Nutzererfahrung', scoreKey: 'ux_score', max: 5 },
];

export default function LeadProfile() {
  const { leadId } = useParams();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [openAudit, setOpenAudit] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [editData, setEditData] = useState({});
  const [downloadingId, setDownloadingId] = useState(null);
  const [enriching, setEnriching] = useState(false);
  const [auditRunning, setAuditRunning] = useState(false);
  const [auditProgress, setAuditProgress] = useState('');
  const [auditError, setAuditError] = useState('');
  const { isMobile } = useScreenSize();

  useEffect(() => {
    loadProfile();
  }, [leadId]); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchLatestScreenshot = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/api/leads/${leadId}/latest-screenshot`);
      if (res.data.screenshot_url) {
        setProfile((prev) => prev ? { ...prev, lead: { ...prev.lead, website_screenshot: res.data.screenshot_url } } : prev);
      }
    } catch { /* silent */ }
  };

  const refreshScreenshot = async () => {
    if (!profile?.lead?.website_url) return;
    await fetchLatestScreenshot();
    if (!profile?.lead?.website_screenshot) {
      try {
        await axios.post(`${API_BASE_URL}/api/leads/${leadId}/screenshot`);
        toast.success('Screenshot wird erstellt...');
        setTimeout(() => loadProfile(), 10000);
      } catch { /* silent */ }
    }
  };

  const loadProfile = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE_URL}/api/leads/${leadId}/profile`);
      setProfile(res.data);
      setEditData(res.data.lead);
      if (!res.data.lead.website_screenshot) fetchLatestScreenshot();
    } catch (e) {
      toast.error('Profil konnte nicht geladen werden.');
    } finally {
      setLoading(false);
    }
  };

  const saveEdit = async () => {
    try {
      await axios.patch(`${API_BASE_URL}/api/leads/${leadId}`, {
        notes: editData.notes,
      });
      toast.success('Gespeichert');
      setEditMode(false);
      loadProfile();
    } catch (e) {
      toast.error('Speichern fehlgeschlagen');
    }
  };

  const downloadPDF = async (auditId, companyName) => {
    setDownloadingId(auditId);
    try {
      const response = await fetch(`${API_BASE_URL}/api/audit/${auditId}/pdf`);
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'PDF Fehler');
      }
      const blob = await response.blob();
      if (blob.size === 0) throw new Error('PDF ist leer');
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Audit-${(companyName || 'Report').replace(/\s+/g, '-')}-${auditId}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      toast.error(e.message);
    } finally {
      setDownloadingId(null);
    }
  };

  const enrichLead = async () => {
    setEnriching(true);
    try {
      const res = await axios.post(`${API_BASE_URL}/api/leads/${leadId}/enrich`);
      if (res.data.status === 'success') {
        toast.success(`Angereichert: ${res.data.enriched_fields.length} Felder aktualisiert`);
        loadProfile();
      } else {
        toast.error(res.data.reason || 'Anreicherung fehlgeschlagen');
      }
    } catch (e) { toast.error('Fehler bei Anreicherung'); }
    finally { setEnriching(false); }
  };

  const startAuditFromProfile = async () => {
    if (!profile?.lead?.website_url) { setAuditError('Keine Website-URL hinterlegt'); return; }
    setAuditRunning(true);
    setAuditProgress('Audit wird gestartet...');
    setAuditError('');
    try {
      const res = await axios.post(`${API_BASE_URL}/api/audit/start`, {
        website_url: profile.lead.website_url,
        lead_id: parseInt(leadId),
        company_name: profile.lead.company_name,
        city: profile.lead.city,
        trade: profile.lead.trade,
      });
      if (!res.data.id) throw new Error('Audit konnte nicht gestartet werden');
      pollAuditInProfile(res.data.id);
    } catch (e) {
      setAuditError(e.response?.data?.detail || e.message || 'Fehler');
      setAuditRunning(false);
    }
  };

  const pollAuditInProfile = (auditId) => {
    const msgs = ['Website wird analysiert...', 'Performance wird gemessen...', 'Rechtliche Anforderungen pruefen...', 'Screenshot wird erstellt...', 'KI-Analyse laeuft...'];
    let i = 0;
    const interval = setInterval(async () => {
      i = (i + 1) % msgs.length;
      setAuditProgress(msgs[i]);
      try {
        const res = await axios.get(`${API_BASE_URL}/api/audit/${auditId}`);
        if (res.data.status === 'completed') {
          clearInterval(interval);
          setAuditProgress('Audit abgeschlossen!');
          toast.success('Audit abgeschlossen');
          setTimeout(() => { setAuditRunning(false); setAuditProgress(''); loadProfile(); }, 1500);
        } else if (res.data.status === 'failed') {
          clearInterval(interval);
          setAuditError(res.data.error_message || 'Audit fehlgeschlagen');
          setAuditRunning(false); setAuditProgress('');
        }
      } catch { /* keep polling */ }
    }, 4000);
    setTimeout(() => { clearInterval(interval); setAuditRunning(false); }, 180000);
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--kc-space-4)', padding: 'var(--kc-space-6)' }}>
        <div className="kc-skeleton" style={{ height: 120 }} />
        <div className="kc-skeleton" style={{ height: 200 }} />
      </div>
    );
  }

  if (!profile) return null;

  const { lead, current_score, current_level, score_history, audits, projects } = profile;
  const levelColor = LEVEL_COLORS[current_level] || '#4a5a7a';
  const statusInfo = STATUS_LABELS[lead.status] || { label: lead.status, color: '#4a5a7a' };
  const latestAudit = audits[0] || null;

  const scoreImprovement = score_history.length >= 2
    ? score_history[score_history.length - 1].score - score_history[0].score
    : null;

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', fontFamily: 'system-ui, sans-serif' }}>
      {/* Back */}
      <button
        onClick={() => navigate('/app/leads')}
        style={{
          background: 'none', border: 'none', color: NAVY, fontSize: 14,
          cursor: 'pointer', marginBottom: 16, padding: 0, display: 'flex', alignItems: 'center', gap: 6,
        }}
      >
        ← Zurück zur Pipeline
      </button>

      {/* ── Website Screenshot ── */}
      {lead.website_screenshot ? (
        <div style={{ marginBottom: 16, borderRadius: 12, overflow: 'hidden', border: '1px solid #e2e8f0', boxShadow: '0 2px 12px rgba(0,0,0,0.08)' }}>
          <div style={{ background: '#f1f5f9', padding: '8px 12px', display: 'flex', alignItems: 'center', gap: 6, borderBottom: '1px solid #e2e8f0' }}>
            {['#ef4444', '#f59e0b', '#22c55e'].map((c) => (
              <div key={c} style={{ width: 10, height: 10, borderRadius: '50%', background: c }} />
            ))}
            <div style={{ flex: 1, background: '#fff', borderRadius: 6, padding: '3px 10px', fontSize: 11, color: '#64748b', marginLeft: 6, border: '1px solid #e2e8f0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {lead.website_url}
            </div>
            <a href={lead.website_url?.startsWith('http') ? lead.website_url : `https://${lead.website_url}`} target="_blank" rel="noopener noreferrer" style={{ color: '#64748b', fontSize: 12, textDecoration: 'none', flexShrink: 0 }} title="Website oeffnen">↗</a>
            <button onClick={refreshScreenshot} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b', fontSize: 14, padding: '2px 6px', borderRadius: 4, flexShrink: 0 }} title="Screenshot aktualisieren">🔄</button>
          </div>
          <div style={{ position: 'relative' }}>
            <img src={lead.website_screenshot} alt={`Website von ${lead.company_name}`} style={{ width: '100%', height: 'auto', display: 'block', maxHeight: 280, objectFit: 'cover', objectPosition: 'top' }} />
            {current_score != null && (
              <div style={{ position: 'absolute', bottom: 12, right: 12, background: 'rgba(15,30,58,0.9)', borderRadius: 20, padding: '6px 14px', display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ color: '#D4A017', fontSize: 13, fontWeight: 800 }}>{current_score}/100</span>
                <span style={{ color: 'rgba(255,255,255,0.85)', fontSize: 11 }}>{current_level?.replace('Homepage Standard ', '')}</span>
              </div>
            )}
          </div>
        </div>
      ) : lead.website_url ? (
        <div onClick={() => !auditRunning && startAuditFromProfile()} style={{ background: '#f8fafc', border: '2px dashed #cbd5e1', borderRadius: 12, padding: 32, textAlign: 'center', marginBottom: 16, color: '#64748b', fontSize: 14, cursor: auditRunning ? 'default' : 'pointer', transition: 'border-color 0.2s' }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>🖥️</div>
          <div style={{ fontWeight: 600, color: '#475569', marginBottom: 6 }}>Kein Screenshot vorhanden</div>
          <div style={{ fontSize: 12 }}>{auditRunning ? 'Audit laeuft...' : 'Klicken um Audit zu starten'}</div>
        </div>
      ) : null}

      {/* ── Header Card ── */}
      <div style={{
        background: NAVY, borderRadius: '12px 12px 0 0', padding: isMobile ? '16px' : '24px 28px', color: '#fff',
        display: 'flex', flexDirection: isMobile ? 'column' : 'row', justifyContent: 'space-between', alignItems: isMobile ? 'center' : 'flex-start',
      }}>
        <div>
          <div style={{ fontSize: 11, color: '#D4A017', textTransform: 'uppercase', letterSpacing: '0.15em', marginBottom: 6 }}>
            Kundenkartei
          </div>
          <div style={{ fontSize: 26, fontWeight: 800, marginBottom: 8 }}>{lead.company_name}</div>
          <div style={{ fontSize: 14, color: 'rgba(255,255,255,0.85)', display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            <span>{lead.trade}</span>
            {lead.city && <span>📍 {lead.city}</span>}
            <span style={{
              background: statusInfo.color + '30', color: statusInfo.color,
              padding: '2px 10px', borderRadius: 20, fontSize: 12, fontWeight: 700,
            }}>
              {statusInfo.label}
            </span>
          </div>
        </div>
        {current_score !== null && (
          <div style={{ textAlign: 'center', flexShrink: 0 }}>
            <div style={{ fontSize: 42, fontWeight: 900, color: levelColor, lineHeight: 1 }}>{current_score}</div>
            <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.75)' }}>/ 100</div>
            <div style={{ fontSize: 11, color: levelColor, fontWeight: 700, marginTop: 4 }}>{current_level}</div>
          </div>
        )}
      </div>

      {/* ── Two-column: Contact + Categories ── */}
      <div style={{
        display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', background: '#fff',
        border: '1px solid #eef0f8', borderTop: 'none',
      }}>
        {/* Contact */}
        <div style={{ padding: isMobile ? '16px' : '24px 28px', borderRight: isMobile ? 'none' : '1px solid #eef0f8' }}>
          <SectionLabel>Kontaktdaten</SectionLabel>
          {editMode ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {[['Ansprechpartner', 'contact_name'], ['Telefon', 'phone'], ['E-Mail', 'email'], ['Website', 'website_url'], ['Stadt', 'city'], ['Notiz', 'notes']].map(([label, field]) => (
                <div key={field}>
                  <div style={{ fontSize: 11, color: '#5a6878', marginBottom: 3 }}>{label}</div>
                  {field === 'notes' ? (
                    <textarea
                      value={editData[field] || ''}
                      onChange={(e) => setEditData((p) => ({ ...p, [field]: e.target.value }))}
                      rows={3}
                      style={{ width: '100%', padding: '7px 10px', border: '1.5px solid #d4d8e8', borderRadius: 6, fontSize: 13, boxSizing: 'border-box', fontFamily: 'inherit', resize: 'vertical' }}
                    />
                  ) : (
                    <input
                      value={editData[field] || ''}
                      onChange={(e) => setEditData((p) => ({ ...p, [field]: e.target.value }))}
                      style={{ width: '100%', padding: '7px 10px', border: '1.5px solid #d4d8e8', borderRadius: 6, fontSize: 13, boxSizing: 'border-box' }}
                    />
                  )}
                </div>
              ))}
              <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                <button onClick={saveEdit} style={{ background: NAVY, color: '#fff', border: 'none', borderRadius: 6, padding: '8px 16px', fontSize: 13, fontWeight: 700, cursor: 'pointer', flex: 1 }}>
                  Speichern
                </button>
                <button onClick={() => setEditMode(false)} style={{ background: '#f0f2f8', color: NAVY, border: 'none', borderRadius: 6, padding: '8px 16px', fontSize: 13, cursor: 'pointer' }}>
                  Abbrechen
                </button>
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {[['👤', lead.contact_name], ['📞', lead.phone], ['✉️', lead.email], ['🌐', lead.website_url], ['📍', lead.city], ['🔧', lead.trade], ['📅', lead.created_at ? `Seit ${lead.created_at}` : '']].filter(([, v]) => v).map(([icon, value], i) => (
                <div key={i} style={{ display: 'flex', gap: 10, alignItems: 'center', fontSize: 14, color: NAVY }}>
                  <span style={{ fontSize: 16 }}>{icon}</span>
                  <span>{value}</span>
                </div>
              ))}
              {lead.notes && (
                <div style={{ background: '#f8f9fc', borderRadius: 8, padding: '10px 12px', fontSize: 13, color: '#4a5a74', marginTop: 8, fontStyle: 'italic' }}>
                  {lead.notes}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Category Overview */}
        <div style={{ padding: isMobile ? '16px' : '24px 28px' }}>
          <SectionLabel>Kategorie-Übersicht</SectionLabel>
          {latestAudit ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {CAT_DEFS.map(({ label, scoreKey, max }) => {
                const score = latestAudit[scoreKey] || 0;
                const pct = max > 0 ? (score / max) * 100 : 0;
                const color = pct >= 80 ? '#2a9a5a' : pct >= 50 ? '#c07820' : '#c03030';
                return (
                  <div key={scoreKey}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
                      <span style={{ fontSize: 12, color: '#4a5a74' }}>{label}</span>
                      <span style={{ fontSize: 12, fontFamily: 'monospace', fontWeight: 700, color }}>{score}/{max}</span>
                    </div>
                    <div style={{ height: 5, background: '#eef0f8', borderRadius: 3, overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: 3, transition: 'width 0.6s ease' }} />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div style={{ fontSize: 13, color: '#5a6878' }}>Noch kein Audit durchgeführt.</div>
          )}
        </div>
      </div>

      {/* ── Score History Chart ── */}
      {score_history.length >= 2 && (
        <div style={{ background: '#fff', border: '1px solid #eef0f8', borderTop: 'none', padding: isMobile ? '16px' : '24px 28px' }}>
          <SectionLabel>Score-Verlauf</SectionLabel>
          {scoreImprovement !== null && (
            <div style={{
              fontSize: 13, fontWeight: 700, marginBottom: 12,
              color: scoreImprovement > 0 ? '#2a9a5a' : scoreImprovement < 0 ? '#c03030' : '#4a5a7a',
            }}>
              {score_history[0].score} → {score_history[score_history.length - 1].score} Punkte
              ({scoreImprovement > 0 ? '+' : ''}{scoreImprovement})
              {scoreImprovement > 0 ? ' ↑ Verbesserung!' : scoreImprovement < 0 ? ' ↓' : ''}
            </div>
          )}
          <ResponsiveContainer width="100%" height={160}>
            <LineChart data={score_history} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eef0f8" />
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#5a6878' }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#5a6878' }} width={30} />
              <ReTooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} formatter={(v) => [`${v}/100`, 'Score']} />
              <Line type="monotone" dataKey="score" stroke={NAVY} strokeWidth={2} dot={{ r: 4, fill: NAVY }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* ── Audit Progress ── */}
      {auditRunning && (
        <div style={{ background: '#f0f7ff', border: '2px solid #008EAA', borderRadius: 0, padding: '20px 24px', display: 'flex', alignItems: 'center', gap: 16, borderLeft: '1px solid #eef0f8', borderRight: '1px solid #eef0f8' }}>
          <div style={{ width: 36, height: 36, borderRadius: '50%', border: '3px solid #e0f0f5', borderTopColor: '#008EAA', flexShrink: 0, animation: 'spin 1s linear infinite' }} />
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: NAVY, marginBottom: 2 }}>Audit laeuft...</div>
            <div style={{ fontSize: 13, color: '#4a5a7a' }}>{auditProgress}</div>
            <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>Ca. 30-60 Sekunden. Seite geoeffnet lassen.</div>
          </div>
        </div>
      )}
      {auditError && (
        <div style={{ background: '#fee2e2', border: '1px solid #fca5a5', padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 10, fontSize: 13, color: '#c0392b', borderLeft: '1px solid #eef0f8', borderRight: '1px solid #eef0f8' }}>
          <span>{auditError}</span>
          <button onClick={() => setAuditError('')} style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer', color: '#c0392b', fontSize: 16 }}>✕</button>
        </div>
      )}

      {/* ── Audit History ── */}
      <div style={{ background: '#fff', border: '1px solid #eef0f8', borderTop: 'none', padding: isMobile ? '16px' : '24px 28px' }}>
        <SectionLabel>Audit-Historie ({audits.length})</SectionLabel>
        {audits.length === 0 ? (
          <div style={{ fontSize: 13, color: '#5a6878' }}>Keine Audits vorhanden.</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {audits.map((audit) => {
              const lc = LEVEL_COLORS[audit.level] || '#4a5a7a';
              return (
                <div key={audit.id} style={{
                  display: 'flex', flexDirection: isMobile ? 'column' : 'row', alignItems: isMobile ? 'flex-start' : 'center', gap: 12, padding: '10px 14px',
                  background: '#f8f9fc', borderRadius: 8, flexWrap: 'wrap',
                }}>
                  <span style={{ fontSize: 12, color: '#5a6878', fontFamily: 'monospace', minWidth: 100 }}>
                    {audit.created_at}
                  </span>
                  <span style={{ fontSize: 12, fontWeight: 700, color: lc }}>
                    {audit.level?.replace('Homepage Standard ', '')}
                  </span>
                  <span style={{ fontSize: 14, fontWeight: 800, color: NAVY, fontFamily: 'monospace' }}>
                    {audit.total_score}/100
                  </span>
                  <div style={{ marginLeft: isMobile ? 0 : 'auto', display: 'flex', gap: 6, flexShrink: 0, width: isMobile ? '100%' : 'auto' }}>
                    <button
                      onClick={() => setOpenAudit(audit)}
                      style={{ background: NAVY, color: '#fff', border: 'none', borderRadius: 6, padding: '5px 12px', fontSize: 12, fontWeight: 700, cursor: 'pointer' }}
                    >
                      Details
                    </button>
                    <button
                      onClick={() => downloadPDF(audit.id, lead.company_name)}
                      disabled={downloadingId === audit.id}
                      style={{
                        background: downloadingId === audit.id ? '#ccc' : '#f0f2f8',
                        color: NAVY, border: 'none', borderRadius: 6, padding: '5px 12px',
                        fontSize: 12, fontWeight: 700, cursor: downloadingId === audit.id ? 'not-allowed' : 'pointer',
                      }}
                    >
                      {downloadingId === audit.id ? '...' : '📄 PDF'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* ── Actions ── */}
      <div style={{
        background: '#fff', border: '1px solid #eef0f8', borderTop: 'none',
        borderRadius: '0 0 12px 12px', padding: isMobile ? '16px' : '20px 28px',
        display: 'flex', flexDirection: isMobile ? 'column' : 'row', gap: 10, flexWrap: 'wrap',
      }}>
        <button
          onClick={startAuditFromProfile}
          disabled={auditRunning}
          style={{ background: auditRunning ? '#64748b' : NAVY, color: '#fff', border: 'none', borderRadius: 8, padding: '10px 20px', fontSize: 13, fontWeight: 700, cursor: auditRunning ? 'not-allowed' : 'pointer', width: isMobile ? '100%' : 'auto', opacity: auditRunning ? 0.7 : 1, display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'center' }}
        >
          {auditRunning ? 'Audit laeuft...' : 'Neuen Audit starten'}
        </button>
        <button
          onClick={() => setEditMode(true)}
          style={{ background: '#f0f2f8', color: NAVY, border: 'none', borderRadius: 8, padding: '10px 20px', fontSize: 13, fontWeight: 700, cursor: 'pointer', width: isMobile ? '100%' : 'auto' }}
        >
          ✏️ Lead bearbeiten
        </button>
        <button
          onClick={enrichLead}
          disabled={enriching}
          style={{ background: '#f0f2f8', color: '#0F1E3A', border: 'none', borderRadius: 8, padding: '10px 20px', fontSize: 13, fontWeight: 700, cursor: 'pointer', opacity: enriching ? 0.6 : 1, width: isMobile ? '100%' : 'auto' }}
        >
          {enriching ? 'Wird analysiert...' : 'Daten aktualisieren'}
        </button>
      </div>

      {/* ── Audit Detail Modal ── */}
      {openAudit && (
        <div
          style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.7)', zIndex: 1000,
            overflowY: 'auto', padding: 20,
          }}
          onClick={(e) => { if (e.target === e.currentTarget) setOpenAudit(null); }}
        >
          <div style={{ maxWidth: 900, margin: '0 auto', borderRadius: 12, overflow: 'hidden', background: '#fff' }}>
            <AuditReport auditData={openAudit} onClose={() => setOpenAudit(null)} />
          </div>
        </div>
      )}
    </div>
  );
}

function SectionLabel({ children }) {
  return (
    <div style={{
      fontSize: 11, fontWeight: 700, textTransform: 'uppercase',
      letterSpacing: '0.1em', color: '#5a6878', marginBottom: 16,
    }}>
      {children}
    </div>
  );
}
