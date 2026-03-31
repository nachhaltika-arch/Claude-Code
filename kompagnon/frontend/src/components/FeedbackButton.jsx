import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import API_BASE_URL from '../config';

const TYPES = [
  { id: 'bug', label: 'Fehler melden', color: '#dc2626' },
  { id: 'feature', label: 'Idee vorschlagen', color: '#7c3aed' },
  { id: 'feedback', label: 'Feedback geben', color: '#008EAA' },
  { id: 'question', label: 'Frage stellen', color: '#d97706' },
];

export default function FeedbackButton() {
  const { user, token } = useAuth();
  const { isMobile } = useScreenSize();
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

  const inp = { width: '100%', padding: '10px 12px', border: '1.5px solid #e2e8f0', borderRadius: 8, fontSize: 14, boxSizing: 'border-box', outline: 'none' };

  return (
    <>
      <button onClick={() => setOpen(true)} style={{
        position: 'fixed', bottom: isMobile ? 80 : 24, right: 24, width: 52, height: 52, borderRadius: '50%',
        background: '#0F1E3A', color: '#fff', border: 'none', cursor: 'pointer', fontSize: 22,
        boxShadow: '0 4px 20px rgba(15,30,58,0.3)', zIndex: 90, display: 'flex', alignItems: 'center', justifyContent: 'center',
      }} title="Feedback & Support">💬</button>

      {open && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', zIndex: 200, display: 'flex', alignItems: 'flex-end', justifyContent: 'flex-end', padding: isMobile ? 0 : 24 }}
          onClick={(e) => { if (e.target === e.currentTarget) reset(); }}>
          <div style={{ background: '#fff', borderRadius: isMobile ? '16px 16px 0 0' : 16, width: '100%', maxWidth: 420, boxShadow: '0 20px 60px rgba(0,0,0,0.2)', overflow: 'hidden', maxHeight: isMobile ? '90vh' : 'auto', overflowY: 'auto' }}>
            {step === 'form' ? (
              <>
                <div style={{ background: '#0F1E3A', padding: '16px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ color: '#fff', fontWeight: 800, fontSize: 15 }}>Feedback & Support</div>
                    <div style={{ color: 'rgba(255,255,255,0.75)', fontSize: 12, marginTop: 2 }}>Antwort innerhalb von 24 Stunden</div>
                  </div>
                  <button onClick={reset} style={{ background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: '50%', width: 32, height: 32, color: '#fff', cursor: 'pointer', fontSize: 16, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>✕</button>
                </div>
                <div style={{ padding: 20 }}>
                  <Lbl>Art der Anfrage</Lbl>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, marginBottom: 16 }}>
                    {TYPES.map((t) => (
                      <button key={t.id} onClick={() => setForm((p) => ({ ...p, type: t.id }))} style={{
                        padding: '8px 10px', borderRadius: 8, border: `1.5px solid ${form.type === t.id ? t.color : '#e2e8f0'}`,
                        background: form.type === t.id ? t.color + '15' : '#fff', color: form.type === t.id ? t.color : '#475569',
                        fontSize: 12, fontWeight: 600, cursor: 'pointer', textAlign: 'left', minHeight: 36,
                      }}>{t.label}</button>
                    ))}
                  </div>
                  <Lbl>Betreff *</Lbl>
                  <input value={form.title} onChange={(e) => setForm((p) => ({ ...p, title: e.target.value }))} placeholder="Kurze Beschreibung..." maxLength={100} style={{ ...inp, marginBottom: 12 }} />
                  <Lbl>Beschreibung *</Lbl>
                  <textarea value={form.description} onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))} placeholder="Details..." rows={4} style={{ ...inp, resize: 'vertical', minHeight: 100, marginBottom: 16 }} />
                  <div style={{ fontSize: 11, color: '#64748b', marginBottom: 16 }}>ℹ️ Seite und Browser-Info werden automatisch mitgesendet</div>
                  <button onClick={submit} disabled={loading || !form.title || !form.description} style={{
                    width: '100%', padding: 12, background: loading || !form.title || !form.description ? '#64748b' : '#0F1E3A',
                    color: '#fff', border: 'none', borderRadius: 8, fontSize: 14, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', minHeight: 44,
                  }}>{loading ? 'Wird gesendet...' : 'Absenden'}</button>
                </div>
              </>
            ) : (
              <div style={{ padding: '40px 24px', textAlign: 'center' }}>
                <div style={{ fontSize: 52, marginBottom: 16 }}>✅</div>
                <h3 style={{ fontSize: 18, fontWeight: 800, color: '#0F1E3A', marginBottom: 8 }}>Danke!</h3>
                <p style={{ fontSize: 14, color: '#64748b', marginBottom: 16 }}>Ihr Ticket wurde erstellt.</p>
                <div style={{ background: '#f0fafa', border: '1px solid #008EAA40', borderRadius: 10, padding: '12px 16px', marginBottom: 20 }}>
                  <div style={{ fontSize: 11, color: '#64748b', marginBottom: 4 }}>Ticket-Nummer</div>
                  <div style={{ fontSize: 20, fontWeight: 900, color: '#008EAA', letterSpacing: '0.05em' }}>{ticketNr}</div>
                </div>
                <button onClick={reset} style={{ background: '#0F1E3A', color: '#fff', border: 'none', borderRadius: 8, padding: '10px 24px', fontSize: 14, fontWeight: 700, cursor: 'pointer', minHeight: 44 }}>Schliessen</button>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}

function Lbl({ children }) {
  return <div style={{ fontSize: 11, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>{children}</div>;
}
