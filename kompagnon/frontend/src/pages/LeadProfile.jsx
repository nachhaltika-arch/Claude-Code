import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import toast from 'react-hot-toast';
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip as ReTooltip, CartesianGrid,
} from 'recharts';
import AuditReport from '../components/AuditReport';
import HomepageChecklist from '../components/HomepageChecklist';
import SecurityChecklist from '../components/SecurityChecklist';
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
  new: { label: 'Neu', color: 'var(--text-secondary)' },
  contacted: { label: 'Kontaktiert', color: '#2a7a9a' },
  qualified: { label: 'Qualifiziert', color: 'var(--status-success-text)' },
  proposal_sent: { label: 'Angebot gesendet', color: '#c07820' },
  won: { label: 'Gewonnen', color: 'var(--status-success-text)' },
  lost: { label: 'Verloren', color: '#c03030' },
};



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
  const [screenshotLoading, setScreenshotLoading] = useState(false);
  const [screenshotError, setScreenshotError] = useState('');
  const [deleteAuditId, setDeleteAuditId] = useState(null);
  const [deletingAudit, setDeletingAudit] = useState(false);
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

  const createScreenshot = async () => {
    if (!profile?.lead?.website_url) { setScreenshotError('Keine Website-URL hinterlegt'); return; }
    setScreenshotLoading(true);
    setScreenshotError('');
    try {
      const res = await axios.post(`${API_BASE_URL}/api/leads/${leadId}/screenshot`);
      if (res.data.success && res.data.screenshot_url) {
        setProfile((prev) => prev ? { ...prev, lead: { ...prev.lead, website_screenshot: res.data.screenshot_url } } : prev);
      } else {
        setScreenshotError(res.data.detail || 'Screenshot konnte nicht erstellt werden');
      }
    } catch (e) {
      setScreenshotError(e.response?.data?.detail || 'Verbindungsfehler');
    } finally {
      setScreenshotLoading(false);
    }
  };

  const refreshScreenshot = async () => {
    if (!profile?.lead?.website_url) return;
    await fetchLatestScreenshot();
    if (!profile?.lead?.website_screenshot) {
      await createScreenshot();
    }
  };

  const loadProfile = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE_URL}/api/leads/${leadId}/profile`);
      setProfile(res.data);
      const ld = res.data.lead;
      setEditData({
        company_name: ld.company_name || '', contact_name: ld.contact_name || '', phone: ld.phone || '',
        email: ld.email || '', website_url: ld.website_url || '', city: ld.city || '', trade: ld.trade || '',
        notes: ld.notes || '', display_name: ld.display_name || '', street: ld.street || '',
        house_number: ld.house_number || '', postal_code: ld.postal_code || '', legal_form: ld.legal_form || '',
        vat_id: ld.vat_id || '', register_number: ld.register_number || '', register_court: ld.register_court || '',
        ceo_first_name: ld.ceo_first_name || '', ceo_last_name: ld.ceo_last_name || '',
      });
      if (!res.data.lead.website_screenshot) fetchLatestScreenshot();
    } catch (e) {
      toast.error('Profil konnte nicht geladen werden.');
    } finally {
      setLoading(false);
    }
  };

  const saveEdit = async () => {
    try {
      await axios.patch(`${API_BASE_URL}/api/leads/${leadId}`, editData);
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

  const deleteAudit = async (auditId) => {
    setDeletingAudit(true);
    try {
      const res = await axios.delete(`${API_BASE_URL}/api/audit/${auditId}`);
      if (res.data.success) { setDeleteAuditId(null); toast.success('Audit geloescht'); await loadProfile(); }
    } catch (e) { toast.error(e.response?.data?.detail || 'Loeschen fehlgeschlagen'); }
    finally { setDeletingAudit(false); }
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
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', padding: '24px' }}>
        <div className="skeleton" style={{ height: 120 }} />
        <div className="skeleton" style={{ height: 200 }} />
      </div>
    );
  }

  if (!profile) return null;

  const { lead, current_score, current_level, score_history, audits, projects } = profile;
  const levelColor = LEVEL_COLORS[current_level] || '#4a5a7a';
  const statusInfo = STATUS_LABELS[lead.status] || { label: lead.status, color: 'var(--text-secondary)' };
  const latestAudit = audits[0] || null;

  const scoreImprovement = score_history.length >= 2
    ? score_history[score_history.length - 1].score - score_history[0].score
    : null;

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', fontFamily: 'var(--font-sans)' }}>
      {/* Back */}
      <button
        onClick={() => navigate('/app/leads')}
        style={{
          background: 'none', border: 'none', color: 'var(--text-primary)', fontSize: 14,
          cursor: 'pointer', marginBottom: 16, padding: 0, display: 'flex', alignItems: 'center', gap: 6,
        }}
      >
        ← Zurück zur Pipeline
      </button>

      {/* ── Website Screenshot ── */}
      {lead.website_screenshot ? (
        <div style={{ marginBottom: 16, borderRadius: 'var(--radius-lg)', overflow: 'hidden', border: '1px solid var(--border-light)', boxShadow: '0 2px 12px rgba(0,0,0,0.08)' }}>
          <div style={{ background: 'var(--bg-app)', padding: '8px 12px', display: 'flex', alignItems: 'center', gap: 6, borderBottom: '1px solid var(--border-light)' }}>
            {['#ef4444', '#f59e0b', '#22c55e'].map((c) => (
              <div key={c} style={{ width: 10, height: 10, borderRadius: '50%', background: c }} />
            ))}
            <div style={{ flex: 1, background: 'var(--bg-surface)', borderRadius: 6, padding: '3px 10px', fontSize: 11, color: 'var(--text-tertiary)', marginLeft: 6, border: '1px solid var(--border-light)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {lead.website_url}
            </div>
            <a href={lead.website_url?.startsWith('http') ? lead.website_url : `https://${lead.website_url}`} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-tertiary)', fontSize: 12, textDecoration: 'none', flexShrink: 0 }} title="Website oeffnen">↗</a>
            <button onClick={refreshScreenshot} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)', fontSize: 14, padding: '2px 6px', borderRadius: 4, flexShrink: 0 }} title="Screenshot aktualisieren">🔄</button>
          </div>
          <div style={{ position: 'relative' }}>
            <img src={lead.website_screenshot} alt={`Website von ${lead.company_name}`} style={{ width: '100%', height: 'auto', display: 'block', maxHeight: 280, objectFit: 'cover', objectPosition: 'top' }} />
            {current_score != null && (
              <div style={{ position: 'absolute', bottom: 12, right: 12, background: 'rgba(15,30,58,0.9)', borderRadius: 20, padding: '6px 14px', display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ color: 'var(--brand-primary-light)', fontSize: 13, fontWeight: 800 }}>{current_score}/100</span>
                <span style={{ color: 'rgba(255,255,255,0.85)', fontSize: 11 }}>{current_level?.replace('Homepage Standard ', '')}</span>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div style={{ marginBottom: 16, borderRadius: 'var(--radius-lg)', overflow: 'hidden', border: '1px solid var(--border-light)' }}>
          {/* Browser chrome for placeholder too */}
          {lead.website_url && (
            <div style={{ background: 'var(--bg-app)', padding: '8px 12px', display: 'flex', alignItems: 'center', gap: 6, borderBottom: '1px solid var(--border-light)' }}>
              {['#ef4444', '#f59e0b', '#22c55e'].map((c) => <div key={c} style={{ width: 10, height: 10, borderRadius: '50%', background: c }} />)}
              <div style={{ flex: 1, background: 'var(--bg-surface)', borderRadius: 6, padding: '3px 10px', fontSize: 11, color: 'var(--text-tertiary)', marginLeft: 6, border: '1px solid var(--border-light)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {lead.website_url || 'Keine Website'}
              </div>
            </div>
          )}
          <div
            onClick={screenshotLoading ? undefined : lead.website_url ? createScreenshot : undefined}
            style={{
              background: screenshotLoading ? '#f0f7ff' : '#f8fafc', padding: '40px 24px', textAlign: 'center',
              cursor: screenshotLoading ? 'default' : lead.website_url ? 'pointer' : 'default',
              minHeight: 180, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 8,
              transition: 'background 0.2s',
            }}
          >
            {screenshotLoading ? (
              <>
                <div style={{ width: 48, height: 48, borderRadius: '50%', border: '3px solid #bae6fd', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.9s linear infinite', marginBottom: 4 }} />
                <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>Screenshot wird erstellt...</div>
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>{lead.website_url}</div>
                <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Dauert ca. 10-15 Sekunden</div>
              </>
            ) : lead.website_url ? (
              <>
                <div style={{ width: 56, height: 56, borderRadius: '50%', background: 'var(--status-info-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 26, marginBottom: 4 }}>📸</div>
                <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>Kein Screenshot vorhanden</div>
                <div style={{ fontSize: 12, color: 'var(--brand-primary)', fontWeight: 600 }}>Klicken um Screenshot zu erstellen</div>
              </>
            ) : (
              <>
                <div style={{ fontSize: 32 }}>🌐</div>
                <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)' }}>Keine Website hinterlegt</div>
              </>
            )}
          </div>
          {screenshotError && (
            <div style={{ background: 'var(--status-danger-bg)', border: '1px solid #fca5a5', padding: '10px 14px', fontSize: 12, color: 'var(--status-danger-text)', display: 'flex', alignItems: 'center', gap: 8 }}>
              <span>{screenshotError}</span>
              <button onClick={() => setScreenshotError('')} style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--status-danger-text)', fontSize: 14, padding: 0 }}>✕</button>
            </div>
          )}
        </div>
      )}

      {/* ── Header Card ── */}
      <div style={{
        background: 'var(--brand-primary)', borderRadius: '12px 12px 0 0', padding: isMobile ? '16px' : '24px 28px', color: '#fff',
        display: 'flex', flexDirection: isMobile ? 'column' : 'row', justifyContent: 'space-between', alignItems: isMobile ? 'center' : 'flex-start',
      }}>
        <div>
          <div style={{ fontSize: 11, color: 'var(--brand-primary-light)', textTransform: 'uppercase', letterSpacing: '0.15em', marginBottom: 6 }}>
            Kundenkartei
          </div>
          <div style={{ fontSize: 26, fontWeight: 800, marginBottom: 4 }}>{lead.display_name || lead.company_name}</div>
          {lead.display_name && lead.display_name !== lead.company_name && <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.6)', marginBottom: 4 }}>{lead.company_name}{lead.legal_form ? ` ${lead.legal_form}` : ''}</div>}
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
        display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', background: 'var(--bg-surface)',
        border: '1px solid var(--border-light)', borderTop: 'none',
      }}>
        {/* Contact */}
        <div style={{ padding: isMobile ? '16px' : '24px 28px', borderRight: isMobile ? 'none' : '1px solid var(--border-light)' }}>
          <SectionLabel>Stammdaten</SectionLabel>
          {editMode ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <SubLbl>Unternehmen</SubLbl>
              <EI l="Firmenname" f="company_name" d={editData} s={setEditData} />
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                <EI l="Gesellschaftsform" f="legal_form" d={editData} s={setEditData} ph="GmbH" />
                <EI l="Karteiname" f="display_name" d={editData} s={setEditData} ph="Anzeigename" />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                <EI l="GF Vorname" f="ceo_first_name" d={editData} s={setEditData} />
                <EI l="GF Nachname" f="ceo_last_name" d={editData} s={setEditData} />
              </div>
              <SubLbl>Adresse</SubLbl>
              <div style={{ display: 'grid', gridTemplateColumns: '3fr 1fr', gap: 8 }}>
                <EI l="Strasse" f="street" d={editData} s={setEditData} />
                <EI l="Nr." f="house_number" d={editData} s={setEditData} />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 8 }}>
                <EI l="PLZ" f="postal_code" d={editData} s={setEditData} />
                <EI l="Ort" f="city" d={editData} s={setEditData} />
              </div>
              <SubLbl>Kontakt</SubLbl>
              {[['Ansprechpartner', 'contact_name'], ['Telefon', 'phone'], ['E-Mail', 'email'], ['Website', 'website_url'], ['Gewerk', 'trade']].map(([l, f]) => <EI key={f} l={l} f={f} d={editData} s={setEditData} />)}
              <SubLbl>Rechtliches</SubLbl>
              {[['USt-IdNr.', 'vat_id', 'DE123456789'], ['Handelsreg.-Nr.', 'register_number', 'HRB 12345'], ['Registergericht', 'register_court', 'AG Koblenz']].map(([l, f, p]) => <EI key={f} l={l} f={f} d={editData} s={setEditData} ph={p} />)}
              <div><div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 3 }}>Notizen</div>
                <textarea value={editData.notes || ''} onChange={(e) => setEditData((p) => ({ ...p, notes: e.target.value }))} rows={3} style={{ width: '100%', padding: '7px 10px', border: '1px solid var(--border-medium)', borderRadius: 6, fontSize: 13, boxSizing: 'border-box', resize: 'vertical' }} />
              </div>
              <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
                <button onClick={saveEdit} style={{ background: 'var(--brand-primary)', color: '#fff', border: 'none', borderRadius: 6, padding: '8px 16px', fontSize: 13, fontWeight: 700, cursor: 'pointer', flex: 2, minHeight: 44 }}>Speichern</button>
                <button onClick={() => setEditMode(false)} style={{ background: 'var(--bg-app)', color: 'var(--text-primary)', border: 'none', borderRadius: 6, padding: '8px 16px', fontSize: 13, cursor: 'pointer', flex: 1, minHeight: 44 }}>Abbrechen</button>
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {[['🏢', [lead.company_name, lead.legal_form].filter(Boolean).join(' ')], ['👔', [lead.ceo_first_name, lead.ceo_last_name].filter(Boolean).join(' ')], ['👤', lead.contact_name], ['📞', lead.phone], ['✉️', lead.email], ['🌐', lead.website_url],
                ['📍', [lead.street, lead.house_number].filter(Boolean).join(' ') + (lead.street ? ', ' : '') + [lead.postal_code, lead.city].filter(Boolean).join(' ')],
                ['🔧', lead.trade], ['📅', lead.created_at ? `Seit ${lead.created_at}` : '']
              ].filter(([, v]) => v && v.trim()).map(([icon, value], i) => (
                <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'center', fontSize: 13, color: 'var(--text-primary)' }}>
                  <span style={{ fontSize: 15, flexShrink: 0 }}>{icon}</span>
                  <span>{value}</span>
                </div>
              ))}
              {(lead.vat_id || lead.register_number) && (
                <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: 6, marginTop: 4 }}>
                  {lead.vat_id && <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>USt-IdNr.: {lead.vat_id}</div>}
                  {lead.register_number && <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>HR: {lead.register_number} {lead.register_court}</div>}
                </div>
              )}
              {lead.notes && <div style={{ background: '#f8f9fc', borderRadius: 'var(--radius-md)', padding: '10px 12px', fontSize: 12, color: '#4a5a74', marginTop: 6, fontStyle: 'italic' }}>{lead.notes}</div>}
              <button onClick={() => setEditMode(true)} style={{ marginTop: 8, width: '100%', padding: 8, background: 'var(--bg-app)', color: 'var(--text-primary)', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600, cursor: 'pointer', minHeight: 44 }}>Daten bearbeiten</button>
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
                    <div style={{ height: 5, background: 'var(--bg-app)', borderRadius: 3, overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: 3, transition: 'width 0.6s ease' }} />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Noch kein Audit durchgeführt.</div>
          )}
        </div>
      </div>

      {/* ── Score History Chart ── */}
      {score_history.length >= 2 && (
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderTop: 'none', padding: isMobile ? '16px' : '24px 28px' }}>
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
              <ReTooltip contentStyle={{ fontSize: 12, borderRadius: 'var(--radius-md)' }} formatter={(v) => [`${v}/100`, 'Score']} />
              <Line type="monotone" dataKey="score" stroke={'var(--brand-primary)'} strokeWidth={2} dot={{ r: 4, fill: 'var(--brand-primary)' }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* ── Homepage Checklist ── */}
      <HomepageChecklist auditData={audits?.[0] || null} />
      <SecurityChecklist auditData={audits?.[0] || null} />

      {/* ── Audit Progress ── */}
      {auditRunning && (
        <div style={{ background: '#f0f7ff', border: '2px solid #008EAA', borderRadius: 0, padding: '20px 24px', display: 'flex', alignItems: 'center', gap: 16, borderLeft: '1px solid var(--border-light)', borderRight: '1px solid var(--border-light)' }}>
          <div style={{ width: 36, height: 36, borderRadius: '50%', border: '3px solid #e0f0f5', borderTopColor: 'var(--brand-primary)', flexShrink: 0, animation: 'spin 1s linear infinite' }} />
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 2 }}>Audit laeuft...</div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{auditProgress}</div>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>Ca. 30-60 Sekunden. Seite geoeffnet lassen.</div>
          </div>
        </div>
      )}
      {auditError && (
        <div style={{ background: 'var(--status-danger-bg)', border: '1px solid #fca5a5', padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 10, fontSize: 13, color: 'var(--status-danger-text)', borderLeft: '1px solid var(--border-light)', borderRight: '1px solid var(--border-light)' }}>
          <span>{auditError}</span>
          <button onClick={() => setAuditError('')} style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--status-danger-text)', fontSize: 16 }}>✕</button>
        </div>
      )}

      {/* ── Audit History ── */}
      <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderTop: 'none', padding: isMobile ? '16px' : '24px 28px' }}>
        <SectionLabel>Audit-Historie ({audits.length})</SectionLabel>
        {audits.length === 0 ? (
          <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Keine Audits vorhanden.</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {audits.map((audit) => {
              const lc = LEVEL_COLORS[audit.level] || '#4a5a7a';
              return (
                <div key={audit.id} style={{
                  display: 'flex', flexDirection: isMobile ? 'column' : 'row', alignItems: isMobile ? 'flex-start' : 'center', gap: 12, padding: '10px 14px',
                  background: '#f8f9fc', borderRadius: 'var(--radius-md)', flexWrap: 'wrap',
                }}>
                  <span style={{ fontSize: 12, color: 'var(--text-secondary)', fontFamily: 'monospace', minWidth: 100 }}>
                    {audit.created_at}
                  </span>
                  <span style={{ fontSize: 12, fontWeight: 700, color: lc }}>
                    {audit.level?.replace('Homepage Standard ', '')}
                  </span>
                  <span style={{ fontSize: 14, fontWeight: 800, color: 'var(--text-primary)', fontFamily: 'monospace' }}>
                    {audit.total_score}/100
                  </span>
                  <div style={{ marginLeft: isMobile ? 0 : 'auto', display: 'flex', gap: 6, flexShrink: 0, width: isMobile ? '100%' : 'auto' }}>
                    <button
                      onClick={() => setOpenAudit(audit)}
                      style={{ background: 'var(--brand-primary)', color: '#fff', border: 'none', borderRadius: 6, padding: '5px 12px', fontSize: 12, fontWeight: 700, cursor: 'pointer' }}
                    >
                      Details
                    </button>
                    <button
                      onClick={() => downloadPDF(audit.id, lead.company_name)}
                      disabled={downloadingId === audit.id}
                      style={{
                        background: downloadingId === audit.id ? '#ccc' : '#f0f2f8',
                        color: 'var(--text-primary)', border: 'none', borderRadius: 6, padding: '5px 12px',
                        fontSize: 12, fontWeight: 700, cursor: downloadingId === audit.id ? 'not-allowed' : 'pointer',
                      }}
                    >
                      {downloadingId === audit.id ? '...' : '📄 PDF'}
                    </button>
                    <button onClick={() => setDeleteAuditId(audit.id)} title="Audit loeschen" style={{
                      background: 'none', border: '1px solid #fca5a5', borderRadius: 6, padding: '5px 8px',
                      fontSize: 14, cursor: 'pointer', color: 'var(--status-danger-text)', minWidth: 32, minHeight: 32,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                      🗑️
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
        background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderTop: 'none',
        borderRadius: '0 0 12px 12px', padding: isMobile ? '16px' : '20px 28px',
        display: 'flex', flexDirection: isMobile ? 'column' : 'row', gap: 10, flexWrap: 'wrap',
      }}>
        <button
          onClick={startAuditFromProfile}
          disabled={auditRunning}
          style={{ background: auditRunning ? '#64748b' : 'var(--brand-primary)', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', padding: '10px 20px', fontSize: 13, fontWeight: 700, cursor: auditRunning ? 'not-allowed' : 'pointer', width: isMobile ? '100%' : 'auto', opacity: auditRunning ? 0.7 : 1, display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'center' }}
        >
          {auditRunning ? 'Audit laeuft...' : 'Neuen Audit starten'}
        </button>
        <button
          onClick={() => setEditMode(true)}
          style={{ background: 'var(--bg-app)', color: 'var(--text-primary)', border: 'none', borderRadius: 'var(--radius-md)', padding: '10px 20px', fontSize: 13, fontWeight: 700, cursor: 'pointer', width: isMobile ? '100%' : 'auto' }}
        >
          ✏️ Lead bearbeiten
        </button>
        <button
          onClick={enrichLead}
          disabled={enriching}
          style={{ background: 'var(--bg-app)', color: 'var(--text-primary)', border: 'none', borderRadius: 'var(--radius-md)', padding: '10px 20px', fontSize: 13, fontWeight: 700, cursor: 'pointer', opacity: enriching ? 0.6 : 1, width: isMobile ? '100%' : 'auto' }}
        >
          {enriching ? 'Wird analysiert...' : 'Daten aktualisieren'}
        </button>
      </div>

      {/* ── Delete Audit Modal ── */}
      {deleteAuditId && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}
          onClick={() => setDeleteAuditId(null)}>
          <div onClick={(e) => e.stopPropagation()} style={{ background: 'var(--bg-surface)', borderRadius: 'var(--radius-xl)', padding: 28, maxWidth: 380, width: '100%', boxShadow: '0 20px 60px rgba(0,0,0,0.2)', textAlign: 'center' }}>
            <div style={{ width: 52, height: 52, borderRadius: '50%', background: 'var(--status-danger-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24, margin: '0 auto 16px' }}>🗑️</div>
            <h3 style={{ fontSize: 18, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 8 }}>Audit loeschen?</h3>
            <p style={{ fontSize: 14, color: 'var(--text-tertiary)', marginBottom: 8, lineHeight: 1.5 }}>Dieser Audit-Eintrag wird dauerhaft geloescht.</p>
            <p style={{ fontSize: 12, color: 'var(--status-danger-text)', marginBottom: 24 }}>Screenshot und alle Ergebnisse gehen verloren.</p>
            <div style={{ display: 'flex', gap: 10 }}>
              <button onClick={() => setDeleteAuditId(null)} disabled={deletingAudit} style={{ flex: 1, padding: 11, background: 'var(--bg-app)', color: 'var(--text-primary)', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 14, fontWeight: 600, cursor: 'pointer', minHeight: 44 }}>Abbrechen</button>
              <button onClick={() => deleteAudit(deleteAuditId)} disabled={deletingAudit} style={{ flex: 1, padding: 11, background: deletingAudit ? '#64748b' : '#ef4444', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 14, fontWeight: 700, cursor: deletingAudit ? 'not-allowed' : 'pointer', minHeight: 44 }}>
                {deletingAudit ? 'Loeschen...' : 'Endgueltig loeschen'}
              </button>
            </div>
          </div>
        </div>
      )}

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
          <div style={{ maxWidth: 900, margin: '0 auto', borderRadius: 'var(--radius-lg)', overflow: 'hidden', background: 'var(--bg-surface)' }}>
            <AuditReport auditData={openAudit} onClose={() => setOpenAudit(null)} />
          </div>
        </div>
      )}
    </div>
  );
}

function SectionLabel({ children }) {
  return (
    <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--text-secondary)', marginBottom: 16 }}>
      {children}
    </div>
  );
}

function SubLbl({ children }) {
  return <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.1em', marginTop: 6 }}>{children}</div>;
}

function EI({ l, f, d, s, ph = '' }) {
  return (
    <div>
      <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 3 }}>{l}</div>
      <input value={d[f] || ''} onChange={(e) => s((p) => ({ ...p, [f]: e.target.value }))} placeholder={ph} style={{ width: '100%', padding: '7px 10px', border: '1px solid var(--border-medium)', borderRadius: 6, fontSize: 13, boxSizing: 'border-box' }} />
    </div>
  );
}
