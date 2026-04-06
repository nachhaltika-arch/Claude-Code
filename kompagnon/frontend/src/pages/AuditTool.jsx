import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { useSearchParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';
import AuditReport from '../components/AuditReport';
import { useScreenSize } from '../utils/responsive';

const TRADE_OPTIONS = [
  'Elektriker', 'Klempner', 'Maler', 'Schreiner',
  'Dachdecker', 'Heizung', 'Sanitär', 'Fliesenleger', 'Sonstiges',
];

const LOADING_STEPS = [
  'Website wird geprüft...',
  'Performance wird analysiert...',
  'Rechtliche Anforderungen werden geprüft...',
  'KI-Analyse läuft...',
];

export default function AuditTool() {
  const [searchParams] = useSearchParams();
  const [step, setStep] = useState('form'); // form | loading | result
  const [result, setResult] = useState(null);
  const [auditId, setAuditId] = useState(null);
  const [loadingStep, setLoadingStep] = useState(0);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [showLeadModal, setShowLeadModal] = useState(false);
  const [savedLeadId, setSavedLeadId] = useState(null);
  const [scrapedData, setScrapedData] = useState(null);
  const [scrapingBlocked, setScrapingBlocked] = useState(false);
  const [url, setUrl] = useState(searchParams.get('url') || '');
  const { isMobile } = useScreenSize();
  const pollRef = useRef(null);
  const stepRef = useRef(null);
  const navigate = useNavigate();

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
      if (stepRef.current) clearInterval(stepRef.current);
    };
  }, []);

  const startAudit = async () => {
    if (!url.trim()) {
      toast.error('Bitte eine Website-URL eingeben.');
      return;
    }

    setStep('loading');
    setLoadingStep(0);
    setResult(null);
    setAuditId(null);
    setScrapedData(null);

    // Animate loading steps (cycle through every 3s)
    stepRef.current = setInterval(() => {
      setLoadingStep((s) => (s + 1) % LOADING_STEPS.length);
    }, 3000);

    try {
      const res = await axios.post(`${API_BASE_URL}/api/audit/start`, {
        website_url: url,
      });
      const id = res.data.id;
      setAuditId(id);

      // Store scraped data for display
      if (res.data.scraped) {
        setScrapedData(res.data.scraped);
        if (res.data.scraped.scraping_blocked) setScrapingBlocked(true);
      }

      // Start polling every 4 seconds
      pollRef.current = setInterval(async () => {
        try {
          const poll = await axios.get(`${API_BASE_URL}/api/audit/${id}`);
          const data = poll.data;

          if (data.status === 'completed') {
            clearInterval(pollRef.current);
            clearInterval(stepRef.current);
            pollRef.current = null;
            stepRef.current = null;
            setResult(data);
            setStep('result');
          } else if (data.status === 'failed') {
            clearInterval(pollRef.current);
            clearInterval(stepRef.current);
            pollRef.current = null;
            stepRef.current = null;
            toast.error(data.error_message || data.message || 'Audit fehlgeschlagen');
            setStep('form');
          }
        } catch (err) {
          // Network blip — keep polling
        }
      }, 4000);
    } catch (error) {
      clearInterval(stepRef.current);
      stepRef.current = null;
      const msg = error.response?.data?.detail || 'Audit konnte nicht gestartet werden';
      toast.error(msg);
      setStep('form');
    }
  };

  const downloadPDF = async () => {
    if (!auditId) return;
    setPdfLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/audit/${auditId}/pdf`);
      if (!response.ok) {
        let detail = 'Unbekannter Fehler';
        try {
          const err = await response.json();
          detail = err.detail || detail;
        } catch (_) {}
        throw new Error(detail);
      }
      const blob = await response.blob();
      if (blob.size === 0) throw new Error('PDF ist leer');
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Homepage-Standard-Audit-${(result?.company_name || 'Audit').replace(/\s+/g, '-')}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('PDF Fehler:', err);
      toast.error(`PDF Fehler: ${err.message}`);
    } finally {
      setPdfLoading(false);
    }
  };

  // ═════════════════════════════════════════════════════════
  // STEP 1: Form (simplified — URL only)
  // ═════════════════════════════════════════════════════════
  if (step === 'form') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', width: '100%', minWidth: 0, overflowX: 'hidden' }}>
        <div >
          <span >Homepage Standard</span>
          <h1>Website-Audit</h1>
        </div>

        <div className="kc-card" style={{ maxWidth: isMobile ? '100%' : '600px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px', margin: 0 }}>
            Geben Sie die Domain ein — wir ermitteln alle weiteren Informationen automatisch.
          </p>
          <div>
            <Label required>Website / Domain</Label>
            <div style={{ display: 'flex', gap: '12px' }}>
              <Input
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && startAudit()}
                placeholder="z.B. elektro-mustermann.de"
                style={{ ...inputStyle, flex: 1 }}
                required
              />
              <button
                onClick={startAudit}
                disabled={!url.trim()}
                className="kc-btn-primary"
                style={{ fontSize: '14px', whiteSpace: 'nowrap', opacity: url.trim() ? 1 : 0.6 }}
              >
                Audit starten
              </button>
            </div>
            <p style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginTop: '8px', marginBottom: 0 }}>
              Wir analysieren automatisch: Firmenname, Kontaktdaten, Performance, Rechtliches &amp; SEO
            </p>
          </div>
        </div>
      </div>
    );
  }

  // ═════════════════════════════════════════════════════════
  // STEP 2: Loading (polls backend every 4s)
  // ═════════════════════════════════════════════════════════
  if (step === 'loading') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', width: '100%', minWidth: 0, overflowX: 'hidden' }}>
        <div >
          <span >Audit läuft</span>
          <h1>Analyse von {scrapedData?.company_name || url}</h1>
        </div>
        <div className="kc-card" style={{ maxWidth: isMobile ? '100%' : '500px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {LOADING_STEPS.map((text, i) => (
            <div
              key={i}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                opacity: i <= loadingStep ? 1 : 0.3,
                transition: 'opacity 0.5s ease',
              }}
            >
              <span style={{
                width: '24px', height: '24px', borderRadius: 'var(--radius-full)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '11px', fontWeight: 700,
                background: i < loadingStep ? 'var(--status-success-text)' : i === loadingStep ? 'var(--brand-primary)' : 'var(--border-light)',
                color: i <= loadingStep ? 'var(--bg-surface)' : 'var(--text-tertiary)',
              }}>
                {i < loadingStep ? '✓' : i + 1}
              </span>
              <span style={{ fontSize: '13px', fontWeight: i === loadingStep ? 700 : 400, color: 'var(--text-primary)' }}>
                {text}
              </span>
            </div>
          ))}
          <div className="skeleton" style={{ height: '4px', marginTop: '16px' }} />
          <p style={{ fontSize: '11px', color: 'var(--text-tertiary)', textAlign: 'center' }}>
            Die Analyse kann bis zu 30 Sekunden dauern.
          </p>
        </div>

        {/* Scraped data preview */}
        {scrapedData && (
          <div style={{
            maxWidth: '500px',
            background: '#f0f7ff', borderRadius: 'var(--radius-lg)',
            padding: '16px 20px',
            border: '1px solid #c0d8f0',
          }}>
            <div style={{
              fontSize: '11px', fontWeight: 700, color: '#2a5aa0',
              marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.05em',
            }}>
              ✓ Automatisch erkannt
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: '8px', fontSize: '13px', minWidth: 0, width: '100%' }}>
              {scrapedData.company_name && (
                <div><span style={{ color: 'var(--text-tertiary)' }}>Firma:</span> <strong>{scrapedData.company_name}</strong></div>
              )}
              {scrapedData.city && (
                <div><span style={{ color: 'var(--text-tertiary)' }}>Stadt:</span> <strong>{scrapedData.city}</strong></div>
              )}
              {scrapedData.phone && (
                <div><span style={{ color: 'var(--text-tertiary)' }}>Telefon:</span> <strong>{scrapedData.phone}</strong></div>
              )}
              {scrapedData.email && (
                <div><span style={{ color: 'var(--text-tertiary)' }}>E-Mail:</span> <strong>{scrapedData.email}</strong></div>
              )}
              {scrapedData.trade && scrapedData.trade !== 'Sonstiges' && (
                <div><span style={{ color: 'var(--text-tertiary)' }}>Gewerk:</span> <strong>{scrapedData.trade}</strong></div>
              )}
            </div>
          </div>
        )}
      </div>
    );
  }

  // ═════════════════════════════════════════════════════════
  // STEP 3: Result
  // ═════════════════════════════════════════════════════════
  const r = result;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', width: '100%', minWidth: 0, overflowX: 'hidden' }}>
      {/* Header */}
      <div >
        <span >Audit-Ergebnis</span>
        <h1>{r.company_name}</h1>
      </div>

      {/* Scraping-blocked warning */}
      {scrapingBlocked && (
        <div style={{
          background: '#FFFBEB', border: '1px solid #F59E0B', borderRadius: 8,
          padding: '10px 16px', fontSize: 13, color: '#92400E',
          display: 'flex', alignItems: 'flex-start', gap: 10,
        }}>
          <span style={{ fontSize: 16, flexShrink: 0 }}>⚠️</span>
          <span>
            Die Website hat automatisches Scraping blockiert. Einige Felder wurden nicht automatisch befüllt.
          </span>
        </div>
      )}

      {/* Full Report */}
      <AuditReport auditData={r} />

      {/* Actions */}
      <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', flexDirection: isMobile ? 'column' : 'row', alignItems: isMobile ? 'stretch' : 'center', paddingTop: '8px' }}>
        <button className="kc-btn-primary" style={isMobile ? { width: '100%' } : undefined} onClick={() => { setStep('form'); setResult(null); setAuditId(null); setSavedLeadId(null); setScrapedData(null); }}>
          Neues Audit starten
        </button>
        <button
          className="kc-btn-secondary"
          onClick={downloadPDF}
          disabled={pdfLoading}
          style={{ opacity: pdfLoading ? 0.6 : 1, ...(isMobile ? { width: '100%' } : {}) }}
        >
          {pdfLoading ? 'PDF wird erstellt...' : '✓ PDF herunterladen'}
        </button>
        {savedLeadId ? (
          <button className="kc-btn-ghost" onClick={() => navigate('/app/leads')} style={{ color: 'var(--status-success-text)', ...(isMobile ? { width: '100%' } : {}) }}>
            → Lead ansehen
          </button>
        ) : (
          <button className="kc-btn-secondary" style={isMobile ? { width: '100%' } : undefined} onClick={() => setShowLeadModal(true)}>
            Als Lead speichern
          </button>
        )}
      </div>

      {/* Lead Modal */}
      {showLeadModal && (
        <SaveLeadModal
          audit={r}
          auditId={auditId}
          onClose={() => setShowLeadModal(false)}
          onSaved={(id) => { setSavedLeadId(id); setShowLeadModal(false); }}
        />
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// Save Lead Modal
// ═══════════════════════════════════════════════════════════

const LEVEL_STYLES = {
  'Homepage Standard Platin': { bg: '#e8eaf6', color: '#283593', icon: '\uD83C\uDFC6' },
  'Homepage Standard Gold':   { bg: '#fff8e1', color: '#f57f17', icon: '\uD83E\uDD47' },
  'Homepage Standard Silber': { bg: '#f5f5f5', color: '#616161', icon: '\uD83E\uDD48' },
  'Homepage Standard Bronze': { bg: '#efebe9', color: '#4e342e', icon: '\uD83E\uDD49' },
  'Nicht konform':            { bg: '#fdecea', color: '#C8102E', icon: '⛔' },
};

function SaveLeadModal({ audit, auditId, onClose, onSaved }) {
  const { isMobile } = useScreenSize();
  const [saving, setSaving] = useState(false);
  const [leadForm, setLeadForm] = useState({
    company_name: audit.company_name || '',
    contact_name: '',
    phone: '',
    email: '',
    website_url: audit.website_url || '',
    city: audit.city || '',
    trade: audit.trade || '',
    notes: `Audit-Ergebnis: ${audit.total_score}/100 Punkte - ${audit.level}`,
    lead_source: 'Audit',
  });

  const setField = (field) => (e) => setLeadForm((f) => ({ ...f, [field]: e.target.value }));

  const handleSave = async (e) => {
    e.preventDefault();
    if (!leadForm.company_name.trim()) {
      toast.error('Firmenname ist Pflichtfeld.');
      return;
    }
    setSaving(true);
    try {
      const res = await axios.post(`${API_BASE_URL}/api/leads/`, leadForm);
      const newLeadId = res.data.id;

      // Link audit to the new lead
      if (auditId) {
        try {
          await axios.patch(`${API_BASE_URL}/api/audit/${auditId}/link-lead`, { lead_id: newLeadId });
        } catch (_) {
          // non-critical — lead is saved even if linking fails
        }
      }

      toast.success(`✓ ${leadForm.company_name} wurde als Lead angelegt!`);
      onSaved(newLeadId);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Lead konnte nicht angelegt werden.');
    } finally {
      setSaving(false);
    }
  };

  const ls = LEVEL_STYLES[audit.level] || LEVEL_STYLES['Nicht konform'];

  return createPortal(
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, zIndex: 1000,
        background: 'rgba(0,0,0,0.5)',
        display: 'flex', alignItems: isMobile ? 'flex-end' : 'center', justifyContent: 'center',
        padding: isMobile ? 0 : '16px',
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'var(--bg-surface)',
          borderRadius: isMobile ? '16px 16px 0 0' : 'var(--radius-lg)',
          boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
          width: '100%', maxWidth: '560px',
          maxHeight: isMobile ? '94vh' : '90vh', overflow: 'auto',
        }}
      >
        {/* Modal Header */}
        <div style={{
          background: 'var(--brand-primary)', color: 'var(--bg-surface)',
          padding: '16px 24px',
          borderRadius: 'var(--radius-lg) var(--radius-lg) 0 0',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '16px', fontFamily: 'var(--font-sans)' }}>
              Lead anlegen
            </h3>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none', border: 'none', color: 'var(--bg-surface)',
              fontSize: '18px', cursor: 'pointer', padding: '4px',
              lineHeight: 1,
            }}
            aria-label="Schließen"
          >
            ✕
          </button>
        </div>

        {/* Audit Score Badge */}
        <div style={{
          padding: '16px 24px',
          borderBottom: '1px solid var(--border-light)',
          display: 'flex', alignItems: 'center', gap: '12px',
        }}>
          <span style={{
            display: 'inline-flex', alignItems: 'center', gap: '8px',
            padding: '4px 16px',
            borderRadius: 'var(--radius-md)',
            background: ls.bg, border: `1.5px solid ${ls.color}`,
            fontWeight: 700, fontSize: '13px', color: ls.color,
          }}>
            {ls.icon} {audit.total_score}/100 — {audit.level}
          </span>
          <span style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>
            {audit.website_url}
          </span>
        </div>

        {/* Form */}
        <form onSubmit={handleSave} style={{
          padding: '24px',
          display: 'flex', flexDirection: 'column', gap: '16px',
        }}>
          <div>
            <Label required>Firmenname</Label>
            <Input value={leadForm.company_name} onChange={setField('company_name')} required />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
            <div>
              <Label>Ansprechpartner</Label>
              <Input value={leadForm.contact_name} onChange={setField('contact_name')} placeholder="Vor- und Nachname" />
            </div>
            <div>
              <Label>Telefon</Label>
              <Input type="tel" value={leadForm.phone} onChange={setField('phone')} placeholder="+49 ..." />
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
            <div>
              <Label>E-Mail</Label>
              <Input type="email" value={leadForm.email} onChange={setField('email')} placeholder="info@firma.de" />
            </div>
            <div>
              <Label>Website URL</Label>
              <Input value={leadForm.website_url} onChange={setField('website_url')} />
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
            <div>
              <Label>Stadt</Label>
              <Input value={leadForm.city} onChange={setField('city')} />
            </div>
            <div>
              <Label>Gewerk</Label>
              <select value={leadForm.trade} onChange={setField('trade')} style={inputStyle}>
                <option value="">Bitte wählen...</option>
                {TRADE_OPTIONS.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          </div>
          <div>
            <Label>Notiz</Label>
            <textarea
              value={leadForm.notes}
              onChange={setField('notes')}
              rows={2}
              style={{ ...inputStyle, resize: 'vertical', fontFamily: 'var(--font-sans)' }}
            />
          </div>

          <div style={{ display: 'flex', gap: '12px', paddingTop: '8px' }}>
            <button
              type="submit"
              className="kc-btn-primary"
              disabled={saving}
              style={{ opacity: saving ? 0.6 : 1 }}
            >
              {saving ? 'Wird angelegt...' : 'Lead anlegen'}
            </button>
            <button type="button" className="kc-btn-ghost" onClick={onClose}>
              Abbrechen
            </button>
          </div>
        </form>
      </div>
    </div>,
    document.body
  );
}

// ═══════════════════════════════════════════════════════════
// Shared form helpers
// ═══════════════════════════════════════════════════════════

const inputStyle = {
  width: '100%',
  padding: '10px 14px',
  border: '1px solid var(--border-light)',
  borderRadius: 'var(--radius-md)',
  fontSize: 13,
  fontFamily: 'var(--font-sans)',
  background: 'var(--bg-surface)',
  color: 'var(--text-primary)',
  outline: 'none',
};

function Label({ children, required }) {
  return (
    <label style={{
      display: 'block', fontSize: 13, fontWeight: 500,
      color: 'var(--text-secondary)', marginBottom: 4,
    }}>
      {children}{required && <span style={{ color: 'var(--brand-primary)' }}> *</span>}
    </label>
  );
}

function Input(props) {
  return <input {...props} style={{ ...inputStyle, ...props.style }} />;
}
