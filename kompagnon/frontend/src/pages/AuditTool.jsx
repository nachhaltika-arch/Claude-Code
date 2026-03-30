import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';
import AuditReport from '../components/AuditReport';

const TRADE_OPTIONS = [
  'Elektriker', 'Klempner', 'Maler', 'Schreiner',
  'Dachdecker', 'Heizung', 'Sanit\u00E4r', 'Fliesenleger', 'Sonstiges',
];

const LOADING_STEPS = [
  'Website wird gepr\u00FCft...',
  'Performance wird analysiert...',
  'Rechtliche Anforderungen werden gepr\u00FCft...',
  'KI-Analyse l\u00E4uft...',
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
  const pollRef = useRef(null);
  const stepRef = useRef(null);
  const navigate = useNavigate();

  const [form, setForm] = useState({
    website_url: searchParams.get('url') || '',
    company_name: searchParams.get('company') || '',
    contact_name: searchParams.get('contact') || '',
    city: searchParams.get('city') || '',
    trade: searchParams.get('trade') || '',
    lead_id: searchParams.get('lead_id') || '',
  });

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
      if (stepRef.current) clearInterval(stepRef.current);
    };
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.website_url.trim() || !form.company_name.trim()) {
      toast.error('Website URL und Firmenname sind Pflichtfelder.');
      return;
    }

    setStep('loading');
    setLoadingStep(0);
    setResult(null);
    setAuditId(null);

    // Animate loading steps (cycle through every 3s)
    stepRef.current = setInterval(() => {
      setLoadingStep((s) => (s + 1) % LOADING_STEPS.length);
    }, 3000);

    try {
      const payload = {
        ...form,
        lead_id: form.lead_id ? parseInt(form.lead_id, 10) : null,
      };
      const res = await axios.post(`${API_BASE_URL}/api/audit/start`, payload);
      const id = res.data.id;
      setAuditId(id);

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
          // pending / running -> keep polling
        } catch (err) {
          // Network blip — keep polling, don't abort
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
  // STEP 1: Form
  // ═════════════════════════════════════════════════════════
  if (step === 'form') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--kc-space-6)' }}>
        <div className="kc-section-header">
          <span className="kc-eyebrow">Homepage Standard</span>
          <h1>Website-Audit</h1>
        </div>

        <form
          onSubmit={handleSubmit}
          className="kc-card"
          style={{ maxWidth: '680px', display: 'flex', flexDirection: 'column', gap: 'var(--kc-space-4)' }}
        >
          <div>
            <Label required>Website URL</Label>
            <Input value={form.website_url} onChange={set('website_url')} placeholder="https://www.firma.de" required />
          </div>
          <div>
            <Label required>Firmenname</Label>
            <Input value={form.company_name} onChange={set('company_name')} placeholder="z.B. M\u00FCller Sanit\u00E4r GmbH" required />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--kc-space-4)' }}>
            <div>
              <Label>Ansprechpartner</Label>
              <Input value={form.contact_name} onChange={set('contact_name')} placeholder="Vor- und Nachname" />
            </div>
            <div>
              <Label>Stadt</Label>
              <Input value={form.city} onChange={set('city')} placeholder="z.B. Koblenz" />
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--kc-space-4)' }}>
            <div>
              <Label>Gewerk</Label>
              <select value={form.trade} onChange={set('trade')} style={inputStyle}>
                <option value="">Bitte w\u00E4hlen...</option>
                {TRADE_OPTIONS.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            {form.lead_id && (
              <div>
                <Label>Verkn\u00FCpfter Lead</Label>
                <Input value={form.lead_id} disabled style={{ opacity: 0.6 }} />
              </div>
            )}
          </div>
          <div style={{ paddingTop: 'var(--kc-space-2)' }}>
            <button type="submit" className="kc-btn-primary" style={{ fontSize: 'var(--kc-text-base)' }}>
              Audit starten
            </button>
          </div>
        </form>
      </div>
    );
  }

  // ═════════════════════════════════════════════════════════
  // STEP 2: Loading (polls backend every 4s)
  // ═════════════════════════════════════════════════════════
  if (step === 'loading') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--kc-space-6)' }}>
        <div className="kc-section-header">
          <span className="kc-eyebrow">Audit l\u00E4uft</span>
          <h1>Analyse von {form.company_name}</h1>
        </div>
        <div className="kc-card" style={{ maxWidth: '500px', display: 'flex', flexDirection: 'column', gap: 'var(--kc-space-4)' }}>
          {LOADING_STEPS.map((text, i) => (
            <div
              key={i}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--kc-space-3)',
                opacity: i <= loadingStep ? 1 : 0.3,
                transition: 'opacity 0.5s ease',
              }}
            >
              <span style={{
                width: '24px', height: '24px', borderRadius: 'var(--kc-radius-full)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 'var(--kc-text-xs)', fontWeight: 700,
                background: i < loadingStep ? 'var(--kc-success)' : i === loadingStep ? 'var(--kc-rot)' : 'var(--kc-rand)',
                color: i <= loadingStep ? 'var(--kc-weiss)' : 'var(--kc-mittel)',
              }}>
                {i < loadingStep ? '\u2713' : i + 1}
              </span>
              <span style={{ fontSize: 'var(--kc-text-sm)', fontWeight: i === loadingStep ? 700 : 400, color: 'var(--kc-text-primaer)' }}>
                {text}
              </span>
            </div>
          ))}
          <div className="kc-skeleton" style={{ height: '4px', marginTop: 'var(--kc-space-4)' }} />
          <p style={{ fontSize: 'var(--kc-text-xs)', color: 'var(--kc-mittel)', textAlign: 'center' }}>
            Die Analyse kann bis zu 30 Sekunden dauern.
          </p>
        </div>
      </div>
    );
  }

  // ═════════════════════════════════════════════════════════
  // STEP 3: Result
  // ═════════════════════════════════════════════════════════
  const r = result;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--kc-space-6)' }}>
      {/* Header */}
      <div className="kc-section-header">
        <span className="kc-eyebrow">Audit-Ergebnis</span>
        <h1>{r.company_name}</h1>
      </div>

      {/* Full Report */}
      <AuditReport auditData={r} />

      {/* Actions */}
      <div style={{ display: 'flex', gap: 'var(--kc-space-4)', flexWrap: 'wrap', alignItems: 'center', paddingTop: 'var(--kc-space-2)' }}>
        <button className="kc-btn-primary" onClick={() => { setStep('form'); setResult(null); setAuditId(null); setSavedLeadId(null); }}>
          Neues Audit starten
        </button>
        <button
          className="kc-btn-secondary"
          onClick={downloadPDF}
          disabled={pdfLoading}
          style={{ opacity: pdfLoading ? 0.6 : 1 }}
        >
          {pdfLoading ? 'PDF wird erstellt...' : '\u2713 PDF herunterladen'}
        </button>
        {savedLeadId ? (
          <button className="kc-btn-ghost" onClick={() => navigate('/leads')} style={{ color: 'var(--kc-success)' }}>
            \u2192 Lead ansehen
          </button>
        ) : (
          <button className="kc-btn-secondary" onClick={() => setShowLeadModal(true)}>
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
  'Nicht konform':            { bg: '#fdecea', color: '#C8102E', icon: '\u26D4' },
};

function SaveLeadModal({ audit, auditId, onClose, onSaved }) {
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

      toast.success(`\u2713 ${leadForm.company_name} wurde als Lead angelegt!`);
      onSaved(newLeadId);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Lead konnte nicht angelegt werden.');
    } finally {
      setSaving(false);
    }
  };

  const ls = LEVEL_STYLES[audit.level] || LEVEL_STYLES['Nicht konform'];

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, zIndex: 100,
        background: 'rgba(0,0,0,0.5)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 'var(--kc-space-4)',
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'var(--kc-weiss)',
          borderRadius: 'var(--kc-radius-lg)',
          boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
          width: '100%', maxWidth: '560px',
          maxHeight: '90vh', overflow: 'auto',
        }}
      >
        {/* Modal Header */}
        <div style={{
          background: 'var(--kc-rot)', color: 'var(--kc-weiss)',
          padding: 'var(--kc-space-4) var(--kc-space-6)',
          borderRadius: 'var(--kc-radius-lg) var(--kc-radius-lg) 0 0',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <div>
            <h3 style={{ margin: 0, fontSize: 'var(--kc-text-lg)', fontFamily: 'var(--kc-font-display)' }}>
              Lead anlegen
            </h3>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none', border: 'none', color: 'var(--kc-weiss)',
              fontSize: 'var(--kc-text-xl)', cursor: 'pointer', padding: 'var(--kc-space-1)',
              lineHeight: 1,
            }}
            aria-label="Schlie\u00DFen"
          >
            \u2715
          </button>
        </div>

        {/* Audit Score Badge */}
        <div style={{
          padding: 'var(--kc-space-4) var(--kc-space-6)',
          borderBottom: '1px solid var(--kc-rand)',
          display: 'flex', alignItems: 'center', gap: 'var(--kc-space-3)',
        }}>
          <span style={{
            display: 'inline-flex', alignItems: 'center', gap: 'var(--kc-space-2)',
            padding: 'var(--kc-space-1) var(--kc-space-4)',
            borderRadius: 'var(--kc-radius-md)',
            background: ls.bg, border: `1.5px solid ${ls.color}`,
            fontWeight: 700, fontSize: 'var(--kc-text-sm)', color: ls.color,
          }}>
            {ls.icon} {audit.total_score}/100 \u2014 {audit.level}
          </span>
          <span style={{ fontSize: 'var(--kc-text-xs)', color: 'var(--kc-mittel)' }}>
            {audit.website_url}
          </span>
        </div>

        {/* Form */}
        <form onSubmit={handleSave} style={{
          padding: 'var(--kc-space-6)',
          display: 'flex', flexDirection: 'column', gap: 'var(--kc-space-4)',
        }}>
          <div>
            <Label required>Firmenname</Label>
            <Input value={leadForm.company_name} onChange={setField('company_name')} required />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--kc-space-4)' }}>
            <div>
              <Label>Ansprechpartner</Label>
              <Input value={leadForm.contact_name} onChange={setField('contact_name')} placeholder="Vor- und Nachname" />
            </div>
            <div>
              <Label>Telefon</Label>
              <Input type="tel" value={leadForm.phone} onChange={setField('phone')} placeholder="+49 ..." />
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--kc-space-4)' }}>
            <div>
              <Label>E-Mail</Label>
              <Input type="email" value={leadForm.email} onChange={setField('email')} placeholder="info@firma.de" />
            </div>
            <div>
              <Label>Website URL</Label>
              <Input value={leadForm.website_url} onChange={setField('website_url')} />
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--kc-space-4)' }}>
            <div>
              <Label>Stadt</Label>
              <Input value={leadForm.city} onChange={setField('city')} />
            </div>
            <div>
              <Label>Gewerk</Label>
              <select value={leadForm.trade} onChange={setField('trade')} style={inputStyle}>
                <option value="">Bitte w\u00E4hlen...</option>
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
              style={{ ...inputStyle, resize: 'vertical', fontFamily: 'var(--kc-font-body)' }}
            />
          </div>

          <div style={{ display: 'flex', gap: 'var(--kc-space-3)', paddingTop: 'var(--kc-space-2)' }}>
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
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// Shared form helpers
// ═══════════════════════════════════════════════════════════

const inputStyle = {
  width: '100%',
  padding: 'var(--kc-space-3) var(--kc-space-4)',
  border: '1.5px solid var(--kc-rand)',
  borderRadius: 'var(--kc-radius-md)',
  fontSize: 'var(--kc-text-base)',
  fontFamily: 'var(--kc-font-body)',
  background: 'var(--kc-weiss)',
  outline: 'none',
};

function Label({ children, required }) {
  return (
    <label style={{
      display: 'block', fontSize: 'var(--kc-text-sm)', fontWeight: 600,
      color: 'var(--kc-text-sekundaer)', marginBottom: 'var(--kc-space-1)',
    }}>
      {children}{required && <span style={{ color: 'var(--kc-rot)' }}> *</span>}
    </label>
  );
}

function Input(props) {
  return <input {...props} style={{ ...inputStyle, ...props.style }} />;
}
