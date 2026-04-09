import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import API_BASE_URL from '../config';

const TEAL    = '#008eaa';
const DARK1   = '#04293a';
const DARK2   = '#004f59';
const DARK3   = '#006880';

const MSGS = [
  '🔍 Website wird analysiert...',
  '⚡ Performance wird gemessen...',
  '⚖️ Rechtliches wird geprüft...',
  '🔒 Sicherheit wird untersucht...',
  '📈 SEO wird bewertet...',
  '🤖 KI-Analyse läuft...',
];

const LEVEL = (s) =>
  s >= 85 ? 'Homepage Standard Platin 💎'
  : s >= 70 ? 'Homepage Standard Gold 🥇'
  : s >= 50 ? 'Homepage Standard Silber 🥈'
  : s >= 30 ? 'Homepage Standard Bronze 🥉'
  : 'Nicht konform ⚠️';

const scoreColor = (s) =>
  s >= 70 ? '#1d9e75' : s >= 50 ? '#e67e22' : '#c0392b';

export default function AuditHook() {
  const navigate = useNavigate();
  const [url,      setUrl]      = useState('');
  const [email,    setEmail]    = useState('');
  const [step,     setStep]     = useState('input');
  const [auditData,setAuditData]= useState(null);
  const [error,    setError]    = useState('');
  const [progress, setProgress] = useState('');

  const normalizeUrl = (raw) => {
    raw = raw.trim();
    if (!raw.startsWith('http')) raw = 'https://' + raw;
    return raw;
  };

  /* Auto-fill URL aus E-Mail (bestehende Logik) */
  const handleEmailChange = (val) => {
    setEmail(val);
    const at = val.indexOf('@');
    if (at !== -1) {
      const host = val.slice(at + 1).toLowerCase().trim();
      const FREE = ['gmail.com','gmx.de','gmx.net','web.de','yahoo.de','yahoo.com',
                    'hotmail.com','outlook.com','icloud.com','t-online.de','freenet.de'];
      if (host && !FREE.includes(host) && !url) setUrl(host);
    }
  };

  const startAudit = async (e) => {
    e.preventDefault();
    if (!url || !email) return;
    setStep('loading');
    setError('');

    let idx = 0;
    setProgress(MSGS[0]);
    const iv = setInterval(() => { idx = (idx + 1) % MSGS.length; setProgress(MSGS[idx]); }, 4000);

    try {
      const cleanUrl = normalizeUrl(url);
      const leadRes  = await fetch(`${API_BASE_URL}/api/leads/public`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ website_url: cleanUrl, email, lead_source: 'landing_audit', status: 'new' }),
      });
      const leadData = await leadRes.json();
      const leadId   = leadData.id;

      const auditRes = await fetch(`${API_BASE_URL}/api/audit/start`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ website_url: cleanUrl, lead_id: leadId }),
      });
      const auditStart = await auditRes.json();
      const auditId    = auditStart.audit_id || auditStart.id;
      if (!auditId) throw new Error('Audit konnte nicht gestartet werden');

      let attempts = 0;
      const poll = setInterval(async () => {
        attempts++;
        if (attempts > 45) {
          clearInterval(poll); clearInterval(iv);
          setStep('error'); setError('Zeitüberschreitung — bitte erneut versuchen.');
          return;
        }
        try {
          const r = await fetch(`${API_BASE_URL}/api/audit/${auditId}`);
          const d = await r.json();
          if (d.status === 'completed') {
            clearInterval(poll); clearInterval(iv);
            setAuditData(d); setStep('result');
          } else if (d.status === 'failed') {
            clearInterval(poll); clearInterval(iv);
            setStep('error'); setError('Audit fehlgeschlagen — bitte URL prüfen.');
          }
        } catch {}
      }, 4000);
    } catch (err) {
      clearInterval(iv);
      setStep('error'); setError(err.message || 'Verbindungsfehler');
    }
  };

  /* ── Styles ── */
  const S = {
    section: {
      background: DARK1,
      fontFamily: "'Segoe UI', system-ui, sans-serif",
      position: 'relative',
      overflow: 'hidden',
    },
    heroBand: {
      background: DARK2,
      padding: 'clamp(24px, 5vw, 48px) clamp(16px, 5vw, 40px) 0',
    },
    inner: {
      maxWidth: 960,
      margin: '0 auto',
      display: 'grid',
      gridTemplateColumns: 'minmax(0,1fr) minmax(0,1fr)',
      gap: 'clamp(20px, 4vw, 48px)',
      alignItems: 'start',
    },
    innerMobile: {
      maxWidth: 960,
      margin: '0 auto',
      display: 'grid',
      gridTemplateColumns: '1fr',
      gap: 0,
    },
  };

  const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;

  /* ── Trust-Signale ── */
  const TrustItem = ({ label }) => (
    <div style={{ display:'flex', alignItems:'center', gap: 6,
                  fontSize: 12, color: 'rgba(255,255,255,.6)' }}>
      <div style={{
        width: 16, height: 16, borderRadius: '50%', background: TEAL,
        display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
      }}>
        <svg width="8" height="6" viewBox="0 0 8 6" fill="none">
          <path d="M1 3L3 5L7 1" stroke="white" strokeWidth="1.5"
                strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </div>
      {label}
    </div>
  );

  /* ── 3-Schritt-Prozess ── */
  const Steps = () => (
    <div style={{ display:'flex', gap: 0, marginTop: 20 }}>
      {['E-Mail eingeben', 'Analyse läuft', 'Ergebnis sehen'].map((txt, i) => (
        <div key={i} style={{ flex:1, textAlign:'center', position:'relative' }}>
          {i < 2 && (
            <div style={{
              position:'absolute', top: 14, right: 0, width:'50%',
              height: 1, background: 'rgba(255,255,255,.15)',
            }}/>
          )}
          <div style={{
            width: 28, height: 28, borderRadius: '50%', background: TEAL,
            color: '#fff', fontSize: 11, fontWeight: 700,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 6px',
          }}>{i + 1}</div>
          <div style={{ fontSize: 10, color: 'rgba(255,255,255,.5)', lineHeight: 1.4 }}>
            {txt.split(' ').map((w, j) => <span key={j}>{w}<br/></span>)}
          </div>
        </div>
      ))}
    </div>
  );

  /* ── Formular-Karte ── */
  const FormCard = () => (
    <div style={{
      background: '#fff',
      borderRadius: isMobile ? '12px 12px 0 0' : 12,
      padding: 'clamp(16px, 3vw, 24px)',
      boxShadow: isMobile ? '0 -4px 24px rgba(0,0,0,.3)' : '0 8px 32px rgba(0,0,0,.25)',
    }}>
      <div style={{ fontSize: 10, fontWeight: 700, letterSpacing:'.1em',
                    textTransform:'uppercase', color: TEAL, marginBottom: 6 }}>
        Gratis Website-Audit
      </div>
      <div style={{ fontSize: 15, fontWeight: 700, color: DARK1, marginBottom: 16 }}>
        Ihre Website in 7 Kategorien analysieren
      </div>

      <form onSubmit={startAudit}>
        {/* E-Mail */}
        <div style={{ marginBottom: 12 }}>
          <label style={{ display:'block', fontSize: 10, fontWeight: 600,
                          color: '#5a7a80', textTransform:'uppercase',
                          letterSpacing:'.06em', marginBottom: 4 }}>
            Geschäftliche E-Mail
          </label>
          <input
            type="email" required value={email}
            onChange={e => handleEmailChange(e.target.value)}
            placeholder="max@klempner-mueller.de"
            style={{
              width:'100%', padding:'10px 12px',
              border: '1.5px solid #dde8ea', borderRadius: 8,
              fontSize: 13, color: DARK1, background:'#f8fbfc',
              outline:'none', fontFamily:'inherit',
            }}
            onFocus={e => e.target.style.borderColor = TEAL}
            onBlur={e  => e.target.style.borderColor = '#dde8ea'}
          />
          <div style={{ fontSize: 10, color:'#94adb2', marginTop: 3 }}>
            Wir erkennen Ihre Website automatisch
          </div>
        </div>

        {/* Website */}
        <div style={{ marginBottom: 12 }}>
          <label style={{ display:'block', fontSize: 10, fontWeight: 600,
                          color:'#5a7a80', textTransform:'uppercase',
                          letterSpacing:'.06em', marginBottom: 4 }}>
            {url ? 'Website erkannt' : 'Ihre Website-URL'}
          </label>
          <div style={{ position:'relative', display:'flex', alignItems:'center' }}>
            {url && (
              <div style={{
                position:'absolute', left: 10, width: 8, height: 8,
                borderRadius:'50%', background: TEAL,
              }}/>
            )}
            <input
              type="text" required value={url}
              onChange={e => setUrl(e.target.value)}
              placeholder="www.ihr-betrieb.de"
              style={{
                width:'100%', padding:`10px 12px 10px ${url ? '26px' : '12px'}`,
                border: `1.5px solid ${url ? TEAL : '#dde8ea'}`,
                borderRadius: 8, fontSize: 13,
                color: url ? TEAL : DARK1,
                background: url ? '#f0fafb' : '#f8fbfc',
                outline:'none', fontFamily:'inherit',
                transition: 'all .2s',
              }}
              onFocus={e => e.target.style.borderColor = TEAL}
              onBlur={e  => { if (!url) e.target.style.borderColor = '#dde8ea'; }}
            />
            {url && (
              <span style={{
                position:'absolute', right: 10, fontSize: 9,
                color:'#94adb2', fontWeight: 600,
              }}>auto</span>
            )}
          </div>
        </div>

        {/* CTA */}
        <button
          type="submit"
          style={{
            width:'100%', padding: 13,
            background: TEAL, color:'#fff', border:'none',
            borderRadius: 8, fontSize: 14, fontWeight: 700,
            cursor:'pointer', display:'flex', alignItems:'center',
            justifyContent:'center', gap: 8, marginTop: 4,
            fontFamily:'inherit', letterSpacing:'.01em',
            transition:'background .2s',
          }}
          onMouseEnter={e => e.target.style.background = DARK3}
          onMouseLeave={e => e.target.style.background = TEAL}
        >
          Website jetzt analysieren →
        </button>
        <div style={{ fontSize: 10, color:'#94adb2', textAlign:'center', marginTop: 6 }}>
          Ergebnis erscheint sofort · Kein Login nötig
        </div>
      </form>
    </div>
  );

  /* ── Ergebnis-Kacheln ── */
  const ResultGrid = ({ categories }) => {
    const cats = categories
      ? Object.entries(categories).slice(0, 4).map(([k, v]) => ({
          label: k.replace(/_/g,' ').replace(/\b\w/g, c => c.toUpperCase()),
          score: typeof v === 'object' ? v.score : v,
        }))
      : [
          { label:'Ladezeit Mobile', score: null },
          { label:'Rechtliches',     score: null },
          { label:'SEO-Grundlagen',  score: null },
          { label:'Sicherheit',      score: null },
        ];

    return (
      <div style={{
        display:'grid',
        gridTemplateColumns: isMobile ? '1fr 1fr' : 'repeat(4,1fr)',
        gap: 8, marginBottom: 10,
      }}>
        {cats.map((c, i) => (
          <div key={i} style={{
            background:'#fff', border:'1px solid #dde8ea',
            borderRadius: 8, padding:'10px 8px', textAlign:'center',
          }}>
            <div style={{
              fontSize: 22, fontWeight: 800, marginBottom: 2,
              color: c.score !== null ? scoreColor(c.score) : '#94adb2',
            }}>
              {c.score !== null ? c.score : '—'}
            </div>
            <div style={{ fontSize: 10, color:'#5a7a80', lineHeight: 1.3 }}>
              {c.label}
            </div>
          </div>
        ))}
      </div>
    );
  };

  /* ── RENDER ── */
  return (
    <section id="gratis-audit" style={S.section}>
      <style>{`
        @keyframes spin    { to { transform: rotate(360deg); } }
        @keyframes fadeUp  { from { opacity:0; transform:translateY(16px); } to { opacity:1; transform:none; } }
        @keyframes pulse   { 0%,100%{opacity:1} 50%{opacity:.55} }
        @media(max-width:767px){
          .audit-inner { grid-template-columns: 1fr !important; }
          .audit-left  { padding-bottom: 0 !important; }
        }
      `}</style>

      {/* ═══ HERO BAND ═══ */}
      {(step === 'input' || step === 'loading' || step === 'error') && (
        <div style={S.heroBand}>
          <div className="audit-inner" style={S.inner}>

            {/* LEFT — Value Prop */}
            <div className="audit-left" style={{ paddingBottom: 32 }}>
              {/* Badges */}
              <div style={{ display:'flex', gap: 8, marginBottom: 14, flexWrap:'wrap' }}>
                <span style={{
                  fontSize: 11, fontWeight: 700, letterSpacing:'.06em',
                  textTransform:'uppercase', padding:'3px 10px', borderRadius: 20,
                  background:'rgba(255,255,255,.07)', color:'rgba(255,255,255,.35)',
                  border:'1px solid rgba(255,255,255,.1)', textDecoration:'line-through',
                }}>49,00 €</span>
                <span style={{
                  fontSize: 11, fontWeight: 700, letterSpacing:'.06em',
                  textTransform:'uppercase', padding:'3px 10px', borderRadius: 20,
                  background:'rgba(0,142,170,.25)', color:'#67d4e8',
                  border:`1px solid rgba(0,142,170,.5)`,
                }}>Jetzt kostenlos</span>
              </div>

              {/* Headline */}
              <h2 style={{
                fontSize:'clamp(22px, 4vw, 36px)', fontWeight: 800,
                color:'#fff', lineHeight: 1.15, marginBottom: 12,
                letterSpacing:'-.02em',
              }}>
                Wie gut ist Ihre Website{' '}
                <span style={{ color:'#00d4f5' }}>wirklich?</span>
              </h2>
              <p style={{
                fontSize: 13, color:'rgba(255,255,255,.6)',
                lineHeight: 1.65, marginBottom: 16, maxWidth: 380,
              }}>
                In 60 Sekunden sehen Sie, warum Ihre Website keine Kunden gewinnt — und was Sie dagegen tun können.
              </p>

              {/* Trust */}
              <div style={{ display:'flex', flexWrap:'wrap', gap:'8px 16px', marginBottom: 4 }}>
                <TrustItem label="Kostenlos & unverbindlich" />
                <TrustItem label="DSGVO-konform" />
                <TrustItem label="Sofortergebnis" />
                <TrustItem label="Kein Login nötig" />
              </div>

              <Steps />
            </div>

            {/* RIGHT — Formular-Karte */}
            <div>
              {step === 'input' && <FormCard />}

              {step === 'loading' && (
                <div style={{
                  background:'#fff', borderRadius: 12, padding: 28,
                  textAlign:'center',
                  boxShadow:'0 8px 32px rgba(0,0,0,.25)',
                }}>
                  <div style={{
                    width: 56, height: 56, borderRadius:'50%',
                    border:`3px solid rgba(0,142,170,.15)`,
                    borderTopColor: TEAL,
                    animation:'spin .9s linear infinite',
                    margin:'0 auto 20px',
                  }}/>
                  <div style={{ fontSize: 15, fontWeight: 600, color: DARK1, marginBottom: 8 }}>
                    Audit läuft…
                  </div>
                  <div style={{ fontSize: 13, color:'#94adb2', animation:'pulse 2s infinite' }}>
                    {progress}
                  </div>
                  <div style={{
                    marginTop: 20, padding:'10px 14px',
                    background:'#f0fafb', border:`1px solid ${TEAL}30`,
                    borderRadius: 8, fontSize: 12, color: TEAL,
                    fontWeight: 600,
                  }}>
                    {normalizeUrl(url).replace('https://','').replace('www.','')}
                  </div>
                </div>
              )}

              {step === 'error' && (
                <div style={{
                  background:'#fff', borderRadius: 12, padding: 28,
                  textAlign:'center', boxShadow:'0 8px 32px rgba(0,0,0,.25)',
                }}>
                  <div style={{ fontSize: 40, marginBottom: 12 }}>😔</div>
                  <div style={{ fontSize: 15, fontWeight: 600, color: DARK1, marginBottom: 8 }}>
                    Etwas ist schiefgelaufen
                  </div>
                  <div style={{ fontSize: 13, color:'#94adb2', marginBottom: 20 }}>{error}</div>
                  <button
                    onClick={() => { setStep('input'); setError(''); }}
                    style={{
                      padding:'10px 24px', background: TEAL, color:'#fff',
                      border:'none', borderRadius: 8, fontSize: 13,
                      fontWeight: 600, cursor:'pointer', fontFamily:'inherit',
                    }}
                  >
                    ← Erneut versuchen
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ═══ DIAGONALE KANTE ═══ */}
      <svg
        viewBox="0 0 1200 28"
        preserveAspectRatio="none"
        style={{ display:'block', width:'100%', background:'#f0fafb' }}
      >
        <polygon points="0,0 1200,0 0,28" fill={DARK2}/>
      </svg>

      {/* ═══ ERGEBNIS-SEKTION ═══ */}
      {step === 'result' && auditData ? (
        <div style={{ background:'#f0fafb', padding:'clamp(20px,4vw,40px) clamp(16px,5vw,40px)' }}>
          <div style={{ maxWidth: 960, margin:'0 auto', animation:'fadeUp .4s ease' }}>

            {/* Verdict */}
            <div style={{
              display:'flex', alignItems:'center', flexWrap:'wrap',
              gap: 12, marginBottom: 20,
            }}>
              <div style={{
                fontSize: 48, fontWeight: 800, lineHeight: 1,
                color: scoreColor(auditData.score || 0),
              }}>
                {auditData.score || 0}
              </div>
              <div>
                <div style={{ fontSize: 11, color:'#5a7a80', marginBottom: 3 }}>
                  Gesamtpunkte von 100
                </div>
                <div style={{
                  display:'inline-flex', alignItems:'center', gap: 6,
                  padding:'4px 12px',
                  background: scoreColor(auditData.score||0) + '18',
                  border:`1px solid ${scoreColor(auditData.score||0)}40`,
                  borderRadius: 20, fontSize: 12, fontWeight: 700,
                  color: scoreColor(auditData.score||0),
                }}>
                  {LEVEL(auditData.score || 0)}
                </div>
              </div>
            </div>

            {/* Kategorie-Kacheln */}
            <div style={{
              fontSize: 12, fontWeight: 600, color: DARK1,
              marginBottom: 10, display:'flex', alignItems:'center', gap: 6,
            }}>
              <div style={{ width: 3, height: 14, background: TEAL, borderRadius: 2 }}/>
              Ergebnis nach Kategorie
            </div>
            <ResultGrid categories={auditData.categories} />

            {/* Zusammenfassung */}
            {auditData.ai_summary && (
              <div style={{
                padding:'12px 14px', background:'#fff',
                border:'1px solid #dde8ea', borderRadius: 8,
                fontSize: 12, color:'#5a7a80', lineHeight: 1.6,
                marginBottom: 20,
              }}>
                {auditData.ai_summary}
              </div>
            )}

            {/* Buttons */}
            <div style={{ display:'flex', gap: 10, flexWrap:'wrap' }}>
              <button
                onClick={() => navigate('/checkout/kompagnon')}
                style={{
                  padding:'12px 24px', background: TEAL, color:'#fff',
                  border:'none', borderRadius: 8, fontSize: 13,
                  fontWeight: 700, cursor:'pointer', fontFamily:'inherit',
                }}
              >
                Jetzt Webseite anfragen →
              </button>
              <button
                onClick={() => { setStep('input'); setUrl(''); setEmail(''); setAuditData(null); }}
                style={{
                  padding:'12px 24px', background:'transparent',
                  color: TEAL, border:`1.5px solid ${TEAL}`,
                  borderRadius: 8, fontSize: 13, fontWeight: 600,
                  cursor:'pointer', fontFamily:'inherit',
                }}
              >
                Neue Analyse starten
              </button>
            </div>
          </div>
        </div>
      ) : (
        /* Ergebnis-PREVIEW (wenn noch kein Audit gelaufen) */
        <div style={{ background:'#f0fafb', padding:'clamp(16px,3vw,28px) clamp(16px,5vw,40px)' }}>
          <div style={{ maxWidth: 960, margin:'0 auto' }}>
            <div style={{
              fontSize: 12, fontWeight: 600, color: DARK1,
              marginBottom: 10, display:'flex', alignItems:'center', gap: 6,
            }}>
              <div style={{ width: 3, height: 14, background: TEAL, borderRadius: 2 }}/>
              So sieht Ihr Ergebnis aus — live, sofort nach der Analyse
            </div>
            <ResultGrid categories={null} />
            <div style={{
              padding:'10px 12px', background:'#fff',
              border:'1px solid #dde8ea', borderRadius: 8,
              fontSize: 11, color:'#5a7a80', lineHeight: 1.5,
            }}>
              <strong style={{ color: DARK1 }}>Beispiel: 31/100 · Nicht konform ⚠️</strong>
              {' '}· 3 kritische Probleme gefunden · Sofortige Überarbeitung empfohlen
            </div>
          </div>
        </div>
      )}

      {/* ═══ BOTTOM CTA BAND ═══ */}
      <div style={{
        background: TEAL,
        padding:'clamp(14px,3vw,20px) clamp(16px,5vw,40px)',
      }}>
        <div style={{
          maxWidth: 960, margin:'0 auto',
          display:'flex', alignItems:'center',
          justifyContent:'space-between', gap: 16, flexWrap:'wrap',
        }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color:'#fff', marginBottom: 2 }}>
              Jetzt Ihre kostenlose Analyse starten
            </div>
            <div style={{ fontSize: 11, color:'rgba(255,255,255,.7)' }}>
              Über 340 Handwerksbetriebe analysiert · Festpreis 3.500 €
            </div>
          </div>
          <button
            onClick={() => {
              const el = document.getElementById('gratis-audit');
              if (el) el.scrollIntoView({ behavior:'smooth' });
            }}
            style={{
              padding:'10px 20px', background:'#fff', color: TEAL,
              border:'none', borderRadius: 8, fontSize: 13,
              fontWeight: 700, cursor:'pointer', whiteSpace:'nowrap',
              fontFamily:'inherit',
            }}
          >
            Direkt anfragen →
          </button>
        </div>
      </div>
    </section>
  );
}
