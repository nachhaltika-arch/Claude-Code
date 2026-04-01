import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import API_BASE_URL from '../config';

export default function AuditHook() {
  const navigate = useNavigate();
  const [url, setUrl] = useState('');
  const [email, setEmail] = useState('');
  const [step, setStep] = useState('input');
  const [auditData, setAuditData] = useState(null);
  const [error, setError] = useState('');
  const [progress, setProgress] = useState('');

  const MSGS = [
    '🔍 Website wird analysiert...',
    '⚡ Performance wird gemessen...',
    '⚖️ Rechtliches wird geprüft...',
    '🔒 Sicherheit wird untersucht...',
    '📈 SEO wird bewertet...',
    '🤖 KI-Analyse läuft...',
  ];

  const normalizeUrl = (raw) => {
    raw = raw.trim();
    if (!raw.startsWith('http')) raw = 'https://' + raw;
    return raw;
  };

  const startAudit = async (e) => {
    e.preventDefault();
    if (!url || !email) return;
    setStep('loading');
    setError('');

    let msgIdx = 0;
    setProgress(MSGS[0]);
    const iv = setInterval(() => { msgIdx = (msgIdx + 1) % MSGS.length; setProgress(MSGS[msgIdx]); }, 4000);

    try {
      const cleanUrl = normalizeUrl(url);
      const leadRes = await fetch(`${API_BASE_URL}/api/leads/public`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ website_url: cleanUrl, email, lead_source: 'landing_audit', status: 'new' }),
      });
      const leadData = await leadRes.json();
      const leadId = leadData.id;

      const auditRes = await fetch(`${API_BASE_URL}/api/audit/start`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ website_url: cleanUrl, lead_id: leadId }),
      });
      const auditStart = await auditRes.json();
      const auditId = auditStart.audit_id || auditStart.id;
      if (!auditId) throw new Error('Audit konnte nicht gestartet werden');

      let attempts = 0;
      const poll = setInterval(async () => {
        attempts++;
        if (attempts > 45) { clearInterval(poll); clearInterval(iv); setStep('error'); setError('Zeitüberschreitung — bitte versuche es erneut.'); return; }
        try {
          const r = await fetch(`${API_BASE_URL}/api/audit/${auditId}`);
          const d = await r.json();
          if (d.status === 'completed') { clearInterval(poll); clearInterval(iv); setAuditData(d); setStep('result'); }
          else if (d.status === 'failed') { clearInterval(poll); clearInterval(iv); setStep('error'); setError('Audit fehlgeschlagen — bitte URL prüfen.'); }
        } catch {}
      }, 4000);
    } catch (err) {
      clearInterval(iv);
      setStep('error');
      setError(err.message || 'Verbindungsfehler');
    }
  };

  const scoreColor = (s) => s >= 70 ? '#1a7a3a' : s >= 50 ? '#a06800' : '#b02020';
  const scoreBg = (s) => s >= 70 ? '#eaf5ee' : s >= 50 ? '#fff8e6' : '#fef0f0';
  const levelLabel = (s) => s >= 85 ? 'Homepage Standard Platin 💎' : s >= 70 ? 'Homepage Standard Gold 🥇' : s >= 50 ? 'Homepage Standard Silber 🥈' : s >= 30 ? 'Homepage Standard Bronze 🥉' : 'Nicht konform ⚠️';

  return (
    <section id="gratis-audit" style={{
      background: 'linear-gradient(135deg, #0f1e3a 0%, #1a3a5c 100%)',
      padding: '80px 20px', fontFamily: "'DM Sans', system-ui, sans-serif",
      position: 'relative', overflow: 'hidden',
    }}>
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes fadeUp { from { opacity:0; transform:translateY(16px); } to { opacity:1; transform:translateY(0); } }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.6} }
        .audit-input:focus { border-color: #008eaa !important; box-shadow: 0 0 0 3px rgba(0,142,170,0.15) !important; outline: none !important; }
        .audit-cta:hover { background: #006880 !important; transform: translateY(-1px); }
        .audit-cta { transition: all 0.2s !important; }
        .cat-bar { transition: width 0.8s ease; }
        .result-card { animation: fadeUp 0.4s ease both; }
      `}</style>

      <div style={{ position: 'absolute', inset: 0, backgroundImage: 'radial-gradient(circle at 20% 50%, rgba(0,142,170,0.12) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(0,142,170,0.08) 0%, transparent 40%)', pointerEvents: 'none' }} />

      <div style={{ maxWidth: 700, margin: '0 auto', position: 'relative' }}>

        {/* INPUT */}
        {step === 'input' && (
          <div style={{ textAlign: 'center' }}>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 10, marginBottom: 24 }}>
              <div style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.15)', borderRadius: 20, padding: '5px 14px', fontSize: 13, color: 'rgba(255,255,255,0.5)', textDecoration: 'line-through' }}>49,00 €</div>
              <div style={{ background: 'rgba(0,142,170,0.25)', border: '1px solid rgba(0,142,170,0.5)', borderRadius: 20, padding: '5px 14px', fontSize: 13, fontWeight: 700, color: '#67d4e8', letterSpacing: '0.06em' }}>JETZT KOSTENLOS</div>
            </div>
            <h2 style={{ fontSize: 'clamp(26px, 5vw, 42px)', fontWeight: 700, color: 'white', margin: '0 0 14px', lineHeight: 1.2, letterSpacing: '-0.02em' }}>
              Wie gut ist Ihre Website wirklich?
            </h2>
            <p style={{ fontSize: 16, color: 'rgba(255,255,255,0.65)', maxWidth: 520, margin: '0 auto 36px', lineHeight: 1.65 }}>
              Unser KI-Audit prüft Ihre Website in Sekunden auf Rechtssicherheit, Performance, SEO und mehr — normalerweise <strong style={{ color: 'rgba(255,255,255,0.85)', textDecoration: 'line-through' }}>49 €</strong>, heute für Sie <strong style={{ color: '#67d4e8' }}>kostenlos</strong>.
            </p>
            <form onSubmit={startAudit} style={{ background: 'rgba(255,255,255,0.06)', backdropFilter: 'blur(12px)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 20, padding: '32px 28px', maxWidth: 520, margin: '0 auto' }}>
              <div style={{ marginBottom: 12 }}>
                <input type="text" value={url} onChange={e => setUrl(e.target.value)} placeholder="www.ihrbetrieb.de" required className="audit-input"
                  style={{ width: '100%', padding: '14px 16px', background: 'rgba(255,255,255,0.08)', border: '1.5px solid rgba(255,255,255,0.15)', borderRadius: 12, fontSize: 16, color: 'white', fontFamily: 'inherit', boxSizing: 'border-box', transition: 'all 0.15s' }} />
              </div>
              <div style={{ marginBottom: 16 }}>
                <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="Ihre E-Mail für den Bericht" required className="audit-input"
                  style={{ width: '100%', padding: '14px 16px', background: 'rgba(255,255,255,0.08)', border: '1.5px solid rgba(255,255,255,0.15)', borderRadius: 12, fontSize: 16, color: 'white', fontFamily: 'inherit', boxSizing: 'border-box', transition: 'all 0.15s' }} />
              </div>
              <button type="submit" className="audit-cta" style={{ width: '100%', padding: 16, background: '#008eaa', color: 'white', border: 'none', borderRadius: 12, fontSize: 16, fontWeight: 700, cursor: 'pointer', fontFamily: 'inherit', letterSpacing: '-0.01em' }}>
                🔍 Kostenlosen Audit starten →
              </button>
              <div style={{ marginTop: 14, fontSize: 11, color: 'rgba(255,255,255,0.35)', lineHeight: 1.5 }}>Kein Passwort · Keine Kreditkarte · Ergebnis in ~60 Sekunden</div>
            </form>
            <div style={{ display: 'flex', justifyContent: 'center', gap: 28, marginTop: 32, flexWrap: 'wrap' }}>
              {[{ num: '6', label: 'Prüfkategorien' }, { num: '22', label: 'Prüfpunkte' }, { num: '100', label: 'Punkte möglich' }].map(s => (
                <div key={s.label} style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 28, fontWeight: 700, color: '#67d4e8', letterSpacing: '-0.02em' }}>{s.num}</div>
                  <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.45)', marginTop: 2 }}>{s.label}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* LOADING */}
        {step === 'loading' && (
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <div style={{ width: 64, height: 64, borderRadius: '50%', border: '3px solid rgba(255,255,255,0.1)', borderTopColor: '#008eaa', animation: 'spin 0.9s linear infinite', margin: '0 auto 28px' }} />
            <h3 style={{ fontSize: 22, fontWeight: 600, color: 'white', marginBottom: 12 }}>Audit läuft...</h3>
            <p style={{ fontSize: 15, color: 'rgba(255,255,255,0.55)', animation: 'pulse 2s infinite' }}>{progress}</p>
            <div style={{ marginTop: 32, background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12, padding: '14px 20px', maxWidth: 360, margin: '32px auto 0', fontSize: 13, color: 'rgba(255,255,255,0.4)' }}>
              🌐 {normalizeUrl(url).replace('https://', '')}
            </div>
          </div>
        )}

        {/* ERROR */}
        {step === 'error' && (
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>😔</div>
            <h3 style={{ fontSize: 20, fontWeight: 600, color: 'white', marginBottom: 8 }}>Etwas ist schiefgelaufen</h3>
            <p style={{ fontSize: 14, color: 'rgba(255,255,255,0.55)', marginBottom: 24 }}>{error}</p>
            <button onClick={() => { setStep('input'); setError(''); }} style={{ padding: '12px 28px', background: '#008eaa', color: 'white', border: 'none', borderRadius: 10, fontSize: 14, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit' }}>
              ← Erneut versuchen
            </button>
          </div>
        )}

        {/* RESULT */}
        {step === 'result' && auditData && (
          <div className="result-card">
            <div style={{ textAlign: 'center', marginBottom: 28 }}>
              <div style={{ fontSize: 14, color: 'rgba(255,255,255,0.5)', marginBottom: 8 }}>Audit-Ergebnis für {url.replace(/^https?:\/\//, '')}</div>
              <div style={{ display: 'flex', flexDirection: window.innerWidth < 400 ? 'column' : 'row', alignItems: 'center', justifyContent: 'center', gap: 16 }}>
                <div style={{ width: 'clamp(70px, 20vw, 100px)', height: 'clamp(70px, 20vw, 100px)', borderRadius: '50%', background: scoreBg(auditData.total_score), display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', border: `3px solid ${scoreColor(auditData.total_score)}` }}>
                  <div style={{ fontSize: 32, fontWeight: 700, color: scoreColor(auditData.total_score), lineHeight: 1 }}>{auditData.total_score}</div>
                  <div style={{ fontSize: 11, color: scoreColor(auditData.total_score), opacity: 0.7 }}>/100</div>
                </div>
                <div style={{ textAlign: 'left' }}>
                  <div style={{ fontSize: 18, fontWeight: 700, color: 'white', marginBottom: 4 }}>{levelLabel(auditData.total_score)}</div>
                  <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.5)' }}>Homepage Standard 2026</div>
                </div>
              </div>
            </div>

            <div style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 16, padding: '20px 24px', marginBottom: 20 }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 16 }}>Kategorien</div>
              {[
                ['Rechtl. Compliance', auditData.rc_score, 30],
                ['Performance', auditData.tp_score, 20],
                ['Barrierefreiheit', auditData.bf_score, 20],
                ['Sicherheit', auditData.si_score, 15],
                ['SEO', auditData.se_score, 10],
                ['UX', auditData.ux_score, 5],
              ].map(([label, score, max]) => {
                const pct = Math.min(100, ((score || 0) / max) * 100);
                const col = pct >= 70 ? '#22c55e' : pct >= 50 ? '#f59e0b' : '#ef4444';
                return (
                  <div key={label} style={{ marginBottom: 10 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.7)' }}>{label}</span>
                      <span style={{ fontSize: 12, fontWeight: 600, color: col }}>{score || 0}/{max}</span>
                    </div>
                    <div style={{ height: 5, background: 'rgba(255,255,255,0.08)', borderRadius: 3, overflow: 'hidden' }}>
                      <div className="cat-bar" style={{ width: `${pct}%`, height: '100%', background: col, borderRadius: 3 }} />
                    </div>
                  </div>
                );
              })}
            </div>

            {auditData.ai_summary && (
              <div style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12, padding: '16px 20px', marginBottom: 20, fontSize: 13, color: 'rgba(255,255,255,0.65)', lineHeight: 1.6 }}>
                {auditData.ai_summary.substring(0, 220)}{auditData.ai_summary.length > 220 ? '...' : ''}
              </div>
            )}

            <div style={{ background: 'rgba(0,142,170,0.15)', border: '1px solid rgba(0,142,170,0.3)', borderRadius: 16, padding: 24, textAlign: 'center' }}>
              <div style={{ fontSize: 18, fontWeight: 700, color: 'white', marginBottom: 8 }}>Ihre Website kann besser werden</div>
              <p style={{ fontSize: 13, color: 'rgba(255,255,255,0.6)', marginBottom: 18, lineHeight: 1.6 }}>
                KOMPAGNON bringt Ihre Homepage auf Gold oder Platin — in 14 Werktagen, zum Festpreis. Der vollständige PDF-Bericht geht an {email}.
              </p>
              <div className="cta-stack" style={{ display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap' }}>
                <button onClick={() => navigate('/paket/kompagnon')} style={{ padding: '12px 24px', background: '#d4a017', color: 'white', border: 'none', borderRadius: 10, fontSize: 14, fontWeight: 700, cursor: 'pointer', fontFamily: 'inherit' }}>
                  ⭐ Jetzt optimieren →
                </button>
                <a href="#pakete" style={{ padding: '12px 24px', background: 'rgba(255,255,255,0.1)', color: 'white', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 10, fontSize: 14, cursor: 'pointer', fontFamily: 'inherit', textDecoration: 'none', display: 'inline-block' }}>
                  Alle Pakete ansehen
                </a>
              </div>
            </div>
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <button onClick={() => { setStep('input'); setUrl(''); setEmail(''); setAuditData(null); }} style={{ background: 'none', border: 'none', color: 'rgba(255,255,255,0.35)', fontSize: 12, cursor: 'pointer', fontFamily: 'inherit', textDecoration: 'underline' }}>
                Weitere Website prüfen
              </button>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
