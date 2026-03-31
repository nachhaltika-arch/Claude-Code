import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

const TYPES = [
  { id: 'bug', label: 'Fehler melden', icon: 'fa-bug' },
  { id: 'feature', label: 'Idee vorschlagen', icon: 'fa-lightbulb' },
  { id: 'feedback', label: 'Feedback geben', icon: 'fa-comment' },
  { id: 'question', label: 'Frage stellen', icon: 'fa-circle-question' },
];

export default function FeedbackButton() {
  const { user, token } = useAuth();
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState('form');
  const [form, setForm] = useState({ type: 'feedback', priority: 'medium', title: '', description: '' });
  const [loading, setLoading] = useState(false);
  const [ticketNr, setTicketNr] = useState('');

  const submit = async () => {
    if (!form.title || !form.description) return;
    setLoading(true);
    try {
      const h = { 'Content-Type': 'application/json' };
      if (token) h.Authorization = `Bearer ${token}`;
      const res = await fetch(`${API_BASE_URL}/api/tickets/`, {
        method: 'POST', headers: h,
        body: JSON.stringify({ ...form, page_url: window.location.href, browser_info: navigator.userAgent, user_email: user?.email || '', user_name: user ? `${user.first_name} ${user.last_name}` : '' }),
      });
      const data = await res.json();
      setTicketNr(data.ticket_number || '');
      setStep('success');
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const reset = () => { setOpen(false); setStep('form'); setForm({ type: 'feedback', priority: 'medium', title: '', description: '' }); setTicketNr(''); };

  if (!open) return (
    <button className="btn btn-primary rounded-circle shadow-lg position-fixed" style={{ bottom: 24, right: 24, width: 52, height: 52, zIndex: 1050, minHeight: 'auto' }} onClick={() => setOpen(true)} title="Feedback">
      <i className="fas fa-comment-dots fs-5"></i>
    </button>
  );

  return (
    <div className="modal show d-block" style={{ background: 'rgba(0,0,0,0.4)', zIndex: 1060 }} onClick={e => { if (e.target === e.currentTarget) reset(); }}>
      <div className="modal-dialog modal-dialog-centered" style={{ maxWidth: 420 }}>
        <div className="modal-content">
          {step === 'form' ? (
            <>
              <div className="modal-header bg-dark text-white">
                <h6 className="modal-title"><i className="fas fa-headset me-2"></i>Feedback & Support</h6>
                <button className="btn-close btn-close-white" onClick={reset}></button>
              </div>
              <div className="modal-body">
                <label className="form-label small fw-semibold text-uppercase text-muted">Art der Anfrage</label>
                <div className="row g-2 mb-3">
                  {TYPES.map(t => (
                    <div className="col-6" key={t.id}>
                      <button className={`btn w-100 btn-sm ${form.type === t.id ? 'btn-primary' : 'btn-outline-secondary'}`} onClick={() => setForm(p => ({ ...p, type: t.id }))}>
                        <i className={`fas ${t.icon} me-1`}></i> {t.label}
                      </button>
                    </div>
                  ))}
                </div>
                <div className="mb-3">
                  <label className="form-label small fw-semibold text-uppercase text-muted">Betreff *</label>
                  <input className="form-control" value={form.title} onChange={e => setForm(p => ({ ...p, title: e.target.value }))} placeholder="Kurze Beschreibung..." maxLength={100} />
                </div>
                <div className="mb-3">
                  <label className="form-label small fw-semibold text-uppercase text-muted">Beschreibung *</label>
                  <textarea className="form-control" rows={4} value={form.description} onChange={e => setForm(p => ({ ...p, description: e.target.value }))} placeholder="Details..." />
                </div>
                <small className="text-muted"><i className="fas fa-info-circle me-1"></i>Seite und Browser-Info werden automatisch mitgesendet</small>
              </div>
              <div className="modal-footer">
                <button className="btn btn-primary w-100" onClick={submit} disabled={loading || !form.title || !form.description}>
                  {loading ? <><span className="spinner-border spinner-border-sm me-1"></span>Wird gesendet...</> : <><i className="fas fa-paper-plane me-1"></i>Absenden</>}
                </button>
              </div>
            </>
          ) : (
            <div className="modal-body text-center py-5">
              <i className="fas fa-circle-check text-success fs-1 mb-3"></i>
              <h5>Danke!</h5>
              <p className="text-muted">Ihr Ticket wurde erstellt.</p>
              {ticketNr && <div className="alert alert-info py-2"><small>Ticket-Nummer:</small> <strong>{ticketNr}</strong></div>}
              <button className="btn btn-dark" onClick={reset}>Schließen</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
