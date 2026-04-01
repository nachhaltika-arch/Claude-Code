import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useScreenSize } from '../utils/responsive';
import PricingSection from '../components/PricingSection';
import AuditHook from '../components/AuditHook';


const A = '#D4A017';
const G = '#4a5a7a';

export default function Landing() {
  const nav = useNavigate();
  const { isMobile } = useScreenSize();
  const go = (pkg) => nav(`/checkout/${pkg}`);

  return (
    <div className="landing-page" style={{ fontFamily: 'system-ui, -apple-system, sans-serif', color: '#0f1c20', overflowX: 'hidden' }}>
      {/* ── HERO ── */}
      <section style={{ background: 'linear-gradient(135deg, #008eaa 0%, #1a3050 100%)', minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <nav style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: isMobile ? '12px 16px' : '20px 60px', gap: 8 }}>
          <div style={{ color: '#fff', fontWeight: 900, fontSize: isMobile ? 18 : 24, letterSpacing: '-0.5px', flexShrink: 0 }}>KOMPAGNON</div>
          <div className="pkg-switcher" style={{ alignItems: 'center' }}>
            <a href="#pakete" style={{ fontSize: 13, color: 'rgba(255,255,255,0.75)', textDecoration: 'none', fontWeight: 500, whiteSpace: 'nowrap' }}>Preise</a>
            <button onClick={() => nav('/login')} style={{ background: 'transparent', color: '#fff', border: '1.5px solid rgba(255,255,255,0.4)', borderRadius: 8, padding: '8px 16px', fontWeight: 600, fontSize: 13, cursor: 'pointer', whiteSpace: 'nowrap' }}>
              Anmelden
            </button>
            {!isMobile && (
              <button onClick={() => nav('/register')} style={{ background: A, color: '#0f1c20', border: 'none', borderRadius: 8, padding: '8px 16px', fontWeight: 700, fontSize: 13, cursor: 'pointer', whiteSpace: 'nowrap' }}>
                Kostenlos starten
              </button>
            )}
          </div>
        </nav>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', padding: isMobile ? '32px 20px' : '60px', textAlign: 'center' }}>
          <h1 className="hero-title" style={{ color: '#fff', fontWeight: 900, marginBottom: 20, maxWidth: 700 }}>
            Ihre neue Webseite.<br />Fertig in 14 Tagen.
          </h1>
          <p className="hero-subtitle" style={{ color: 'rgba(255,255,255,0.8)', maxWidth: 540, marginBottom: 24, lineHeight: 1.5 }}>
            Individuell fuer Handwerksbetriebe. KI-optimiert. Festpreis 2.000 Euro.
          </p>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'center', marginBottom: 28, fontSize: 12, color: 'rgba(255,255,255,0.75)' }}>
            {['Trustpilot 4.9/5', 'Trusted Shops', 'DSGVO-konform', 'Festpreis'].map((t, i) => (
              <span key={i} style={{ padding: '4px 12px', background: 'rgba(255,255,255,0.08)', borderRadius: 20 }}>{t}</span>
            ))}
          </div>
          <div className="cta-stack" style={{ display: 'flex', gap: 10, flexDirection: isMobile ? 'column' : 'row', width: isMobile ? '100%' : 'auto', maxWidth: 400 }}>
            <a href="#gratis-audit" className="landing-btn" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, padding: '14px 24px', background: '#008eaa', color: 'white', borderRadius: 10, fontSize: 15, fontWeight: 700, textDecoration: 'none', width: '100%', textAlign: 'center' }}>
              🔍 Gratis Audit starten
            </a>
            <a href="#pakete" className="landing-btn" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, padding: '12px 24px', background: 'transparent', color: 'white', border: '1.5px solid rgba(255,255,255,0.4)', borderRadius: 10, fontSize: 14, fontWeight: 600, textDecoration: 'none', width: '100%', textAlign: 'center' }}>
              Pakete & Preise ↓
            </a>
          </div>
        </div>
        <div style={{ textAlign: 'center', paddingBottom: 24, color: 'rgba(255,255,255,0.3)', fontSize: 24, animation: 'bounce 2s infinite' }}>v</div>
      </section>

      {/* ── SOCIAL PROOF ── */}
      <section style={{ background: '#fff', padding: isMobile ? '40px 20px' : '48px 60px' }}>
        <div style={{ display: 'flex', justifyContent: 'center', gap: isMobile ? 20 : 60, flexWrap: 'wrap', alignItems: 'center' }}>
          <TrustBadge title="Trustpilot" rating="4.9/5" sub="127 Bewertungen" />
          {!isMobile && <div style={{ width: 1, height: 50, background: '#eee' }} />}
          <TrustBadge title="Trusted Shops" rating="4.8/5" sub="Zertifizierter Shop" />
        </div>
      </section>

      {/* ── LEISTUNGEN ── */}
      <section style={{ background: '#f8f9fc', padding: isMobile ? '48px 20px' : '72px 60px' }}>
        <SectionHead title="Was Sie bekommen" sub="Alles inklusive. Einmaliger Festpreis." />
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)', gap: 16, maxWidth: 900, margin: '0 auto' }}>
          {[
            ['🎯', 'Individuelle Texte', 'Jeder Text wird speziell fuer Ihren Betrieb, Ihre Region und Ihre Zielgruppe geschrieben.'],
            ['⚡', 'Fertig in 14 Tagen', 'Von der Beauftragung bis zur Live-Schaltung in maximal 14 Werktagen.'],
            ['🔍', 'KI-Suchmaschinen-Optimierung', 'Ihre Webseite wird auch von ChatGPT, Perplexity und Google AI empfohlen.'],
            ['📱', 'Mobile First', 'Perfekt auf Smartphone, Tablet und Desktop. Getestet auf allen Geraeten.'],
            ['⚖️', 'Rechtssicher', 'Impressum, Datenschutz, Cookie-Banner — DSGVO-konform und abmahnsicher.'],
            ['📊', 'SEO-Volloptimierung', 'Keywords, Meta-Daten, Google Search Console, Sitemap — alles eingerichtet.'],
          ].map(([icon, title, desc], i) => (
            <div key={i} style={{ background: '#fff', borderRadius: 12, padding: 24, border: '1px solid #eef0f8' }}>
              <div style={{ fontSize: 32, marginBottom: 12 }}>{icon}</div>
              <div style={{ fontWeight: 700, fontSize: 16, color: 'var(--text-primary)', marginBottom: 8 }}>{title}</div>
              <div style={{ fontSize: 14, color: G, lineHeight: 1.5 }}>{desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── PREISE ── */}
      {/* ── GRATIS AUDIT ── */}
      <AuditHook />

      {/* ── PREISE ── */}
      <PricingSection />

      {/* ── PROZESS ── */}
      <section style={{ background: '#f8f9fc', padding: isMobile ? '48px 20px' : '72px 60px' }}>
        <SectionHead title="Ihr Weg zur neuen Webseite" sub="In 7 Schritten. Maximal 14 Werktage." />
        <div style={{ display: 'flex', flexDirection: isMobile ? 'column' : 'row', gap: isMobile ? 20 : 0, justifyContent: 'center', maxWidth: 900, margin: '0 auto', position: 'relative' }}>
          {!isMobile && <div style={{ position: 'absolute', top: 20, left: '8%', right: '8%', height: 2, background: '#d4d8e8', zIndex: 0 }} />}
          {[
            ['Auftrag & Zahlung', 'Gruenes Licht — wir starten sofort.'],
            ['Analyse & Strategie', 'Wettbewerb, Sichtbarkeit, Workshop.'],
            ['Inhalte & Texte', 'Individuell fuer Ihren Betrieb.'],
            ['Technische Umsetzung', 'WordPress, SEO, GEO, Mobile.'],
            ['Praesentation', 'Ihre Webseite — vor dem Go-live.'],
            ['Go-live', 'Live-Schaltung & Einweisung.'],
            ['Nachbetreuung', 'Wir lassen Sie nicht allein.'],
          ].map(([title, desc], i) => (
            <div key={i} style={{ flex: 1, textAlign: 'center', position: 'relative', zIndex: 1, display: 'flex', flexDirection: isMobile ? 'row' : 'column', alignItems: 'center', gap: isMobile ? 12 : 8 }}>
              <div style={{ width: 40, height: 40, borderRadius: '50%', background: 'var(--brand-primary)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: 16, flexShrink: 0 }}>{i + 1}</div>
              <div style={{ textAlign: isMobile ? 'left' : 'center' }}>
                <div style={{ fontWeight: 700, fontSize: 13, color: 'var(--text-primary)' }}>{title}</div>
                <div style={{ fontSize: 12, color: G, marginTop: 2 }}>{desc}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── BEWERTUNGEN ── */}
      <section style={{ background: '#fff', padding: isMobile ? '48px 20px' : '72px 60px' }}>
        <SectionHead title="Was unsere Kunden sagen" />
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)', gap: 20, maxWidth: 900, margin: '0 auto' }}>
          {[
            ['"Innerhalb von 12 Tagen hatten wir unsere neue Webseite. Seitdem kommen deutlich mehr Anfragen aus unserer Region."', 'Thomas M., Elektroinstallateur, Muenchen'],
            ['"Endlich eine Webseite, die auch bei Google gefunden wird. Der Strategie-Workshop hat mir die Augen geoeffnet."', 'Klaus B., Sanitaer & Heizung, Hamburg'],
            ['"Professionell, schnell und das fuer einen Festpreis. Kein Vergleich zu der Agentur, die mir 8.000 Euro wollte."', 'Andrea S., Malerbetrieb, Berlin'],
          ].map(([text, author], i) => (
            <div key={i} style={{ background: '#f8f9fc', borderRadius: 12, padding: 24, border: '1px solid #eef0f8' }}>
              <div style={{ color: A, fontSize: 16, marginBottom: 12 }}>★★★★★</div>
              <p style={{ fontSize: 14, color: 'var(--text-primary)', lineHeight: 1.6, fontStyle: 'italic', marginBottom: 16 }}>{text}</p>
              <div style={{ fontSize: 13, color: G }}>— {author}</div>
              <div style={{ fontSize: 11, color: '#2a9a5a', marginTop: 6, fontWeight: 600 }}>Verifizierter Kunde</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── FAQ ── */}
      <section style={{ background: '#f8f9fc', padding: isMobile ? '48px 20px' : '72px 60px' }}>
        <SectionHead title="Haeufige Fragen" />
        <div style={{ maxWidth: 700, margin: '0 auto' }}>
          {[
            ['Wie lange dauert die Erstellung?', 'Von der Beauftragung bis zur Live-Schaltung maximal 14 Werktage. In der Regel sind wir noch schneller.'],
            ['Was ist im Festpreis enthalten?', 'Alle Leistungen: Texte, Design, SEO, GEO-Optimierung, rechtssichere Pflichtseiten, Einweisung und Nachbetreuung.'],
            ['Was passiert nach dem Go-live?', 'Sie erhalten eine persoenliche Einweisung in WordPress, ein Uebergabedokument und einen Ansprechpartner fuer die ersten Wochen.'],
            ['Brauche ich technische Kenntnisse?', 'Nein. Wir kuemmern uns um alles Technische. Nach der Uebergabe koennen Sie einfache Aenderungen selbst vornehmen.'],
            ['Kann ich meine bestehende Domain behalten?', 'Ja, wir uebertragen Ihre bestehende Domain oder registrieren eine neue auf Wunsch.'],
            ['Was ist GEO-Optimierung?', 'GEO steht fuer Generative Engine Optimization. Wir bereiten Ihre Website so auf, dass sie auch von KI-Suchmaschinen wie ChatGPT und Google AI empfohlen wird.'],
          ].map(([q, a], i) => (
            <FAQItem key={i} question={q} answer={a} />
          ))}
        </div>
      </section>

      {/* ── FINALER CTA ── */}
      <section style={{ background: `linear-gradient(135deg, #008eaa 0%, #1a3050 100%)`, padding: isMobile ? '60px 20px' : '80px 60px', textAlign: 'center' }}>
        <h2 style={{ color: '#fff', fontSize: isMobile ? 28 : 40, fontWeight: 900, marginBottom: 16 }}>
          Bereit fuer Ihren neuen Webauftritt?
        </h2>
        <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: 16, marginBottom: 32, maxWidth: 480, margin: '0 auto 32px' }}>
          Keine Verpflichtung. Kein Risiko. Nur ein gutes Gespraech.
        </p>
        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexDirection: isMobile ? 'column' : 'row', alignItems: 'center' }}>
          <Btn onClick={() => go('kompagnon')} primary>Jetzt Webseite anfragen</Btn>
          <Btn onClick={() => nav('/audit')} ghost>Kostenlose Website-Analyse</Btn>
        </div>
        <div style={{ display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap', marginTop: 32, fontSize: 12, color: 'rgba(255,255,255,0.4)' }}>
          {['SSL-gesichert', 'DSGVO-konform', 'Antwort in 24h', 'Made in Germany'].map((t, i) => (
            <span key={i}>{t}</span>
          ))}
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer style={{ background: '#111827', padding: isMobile ? '40px 20px' : '48px 60px', color: 'rgba(255,255,255,0.75)', fontSize: 13 }}>
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(4, 1fr)', gap: 32, maxWidth: 900, margin: '0 auto' }}>
          <div>
            <div style={{ color: '#fff', fontWeight: 900, fontSize: 18, marginBottom: 12 }}>KOMPAGNON</div>
            <p style={{ lineHeight: 1.6 }}>Professionelle Webseiten fuer Handwerksbetriebe. KI-optimiert. Festpreis.</p>
          </div>
          <div>
            <div style={{ color: '#fff', fontWeight: 700, marginBottom: 12 }}>Leistungen</div>
            {['Website-Erstellung', 'SEO-Optimierung', 'GEO-Optimierung', 'Strategie-Workshop'].map((t, i) => (
              <div key={i} style={{ marginBottom: 6 }}>{t}</div>
            ))}
          </div>
          <div>
            <div style={{ color: '#fff', fontWeight: 700, marginBottom: 12 }}>Unternehmen</div>
            {['Ueber uns', 'Referenzen', 'Blog', 'Karriere'].map((t, i) => (
              <div key={i} style={{ marginBottom: 6 }}>{t}</div>
            ))}
          </div>
          <div>
            <div style={{ color: '#fff', fontWeight: 700, marginBottom: 12 }}>Kontakt</div>
            <div style={{ marginBottom: 6 }}>info@kompagnon.de</div>
            <div style={{ marginBottom: 6 }}>+49 261 12345</div>
            <div>Koblenz, Deutschland</div>
          </div>
        </div>
        <div style={{ borderTop: '1px solid rgba(255,255,255,0.1)', marginTop: 32, paddingTop: 20, textAlign: 'center', fontSize: 12 }}>
          2026 KOMPAGNON Communications · <Link to="/impressum" style={{ color: 'inherit' }}>Impressum</Link> · <Link to="/datenschutz" style={{ color: 'inherit' }}>Datenschutz</Link> · AGB
        </div>
      </footer>

      {/* ── MOBILE STICKY CTA ── */}
      {isMobile && (
        <div style={{
          position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 100,
          background: 'var(--brand-primary)', padding: '12px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          boxShadow: '0 -4px 20px rgba(0,0,0,0.3)',
        }}>
          <div style={{ color: '#fff', fontSize: 14, fontWeight: 700 }}>Jetzt anfragen — 2.000 Euro</div>
          <button onClick={() => go('kompagnon')} style={{ background: A, color: 'var(--text-primary)', border: 'none', borderRadius: 8, padding: '10px 20px', fontWeight: 700, fontSize: 14, cursor: 'pointer' }}>
            Zum Angebot
          </button>
        </div>
      )}

      <style>{`
        @keyframes bounce { 0%,100% { transform: translateY(0); } 50% { transform: translateY(8px); } }
      `}</style>
    </div>
  );
}

// ── Sub-components ──

function Btn({ children, onClick, primary, ghost }) {
  return (
    <button onClick={onClick} style={{
      padding: '14px 32px', borderRadius: 8, fontSize: 16, fontWeight: 700, cursor: 'pointer', minHeight: 48, border: 'none', width: '100%', maxWidth: 280,
      ...(primary ? { background: '#D4A017', color: 'var(--text-primary)' } : {}),
      ...(ghost ? { background: 'transparent', color: '#fff', border: '2px solid rgba(255,255,255,0.3)' } : {}),
    }}>
      {children}
    </button>
  );
}

function SectionHead({ title, sub }) {
  return (
    <div style={{ textAlign: 'center', marginBottom: 40 }}>
      <h2 style={{ fontSize: 32, fontWeight: 900, color: 'var(--text-primary)', marginBottom: sub ? 8 : 0 }}>{title}</h2>
      {sub && <p style={{ fontSize: 16, color: '#4a5a7a' }}>{sub}</p>}
    </div>
  );
}

function TrustBadge({ title, rating, sub }) {
  return (
    <div style={{ textAlign: 'center' }}>
      <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-primary)', marginBottom: 4 }}>{title}</div>
      <div style={{ color: '#D4A017', fontSize: 18, marginBottom: 4 }}>★★★★★ {rating}</div>
      <div style={{ fontSize: 12, color: '#4a5a7a' }}>{sub}</div>
    </div>
  );
}

function PriceCard({ name, price, features = [], missing = [], recommended, onClick }) {
  const bg = recommended ? 'var(--text-primary)' : '#fff';
  const fg = recommended ? '#fff' : 'var(--text-primary)';
  const sub = recommended ? 'rgba(255,255,255,0.8)' : '#4a5a7a';
  return (
    <div style={{
      background: bg, borderRadius: 16, padding: 28, border: recommended ? 'none' : '1px solid #eef0f8',
      width: '100%', maxWidth: 280, transform: recommended ? 'scale(1.05)' : 'none', position: 'relative',
    }}>
      {recommended && <div style={{ position: 'absolute', top: -12, left: '50%', transform: 'translateX(-50%)', background: '#D4A017', color: 'var(--text-primary)', fontSize: 11, fontWeight: 800, padding: '4px 16px', borderRadius: 20 }}>EMPFOHLEN</div>}
      <div style={{ fontSize: 18, fontWeight: 800, color: fg, marginBottom: 4 }}>{name}</div>
      <div style={{ fontSize: 36, fontWeight: 900, color: fg, marginBottom: 16 }}>{price} <span style={{ fontSize: 16, fontWeight: 400, color: sub }}>Euro</span></div>
      {features.map((f, i) => <div key={i} style={{ fontSize: 14, color: fg, marginBottom: 6, display: 'flex', gap: 8 }}><span style={{ color: '#27AE60' }}>✓</span> {f}</div>)}
      {missing.map((f, i) => <div key={i} style={{ fontSize: 14, color: sub, marginBottom: 6, display: 'flex', gap: 8 }}><span>—</span> {f}</div>)}
      <button onClick={onClick} style={{
        width: '100%', marginTop: 16, padding: '12px', borderRadius: 8, fontSize: 15, fontWeight: 700, cursor: 'pointer', minHeight: 48,
        background: recommended ? '#D4A017' : 'transparent', color: recommended ? 'var(--text-primary)' : 'var(--text-primary)',
        border: recommended ? 'none' : '2px solid var(--text-primary)',
      }}>
        {recommended ? 'Jetzt starten' : 'Anfragen'}
      </button>
    </div>
  );
}

function FAQItem({ question, answer }) {
  const [open, setOpen] = useState(false);
  return (
    <div style={{ borderBottom: '1px solid #eef0f8', padding: '16px 0' }}>
      <button onClick={() => setOpen(!open)} style={{
        width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left', padding: 0,
      }}>
        <span style={{ fontWeight: 700, fontSize: 15, color: 'var(--text-primary)' }}>{question}</span>
        <span style={{ fontSize: 20, color: '#4a5a7a', flexShrink: 0, marginLeft: 12 }}>{open ? '−' : '+'}</span>
      </button>
      {open && <p style={{ fontSize: 14, color: '#4a5a7a', lineHeight: 1.6, marginTop: 10, marginBottom: 0 }}>{answer}</p>}
    </div>
  );
}
