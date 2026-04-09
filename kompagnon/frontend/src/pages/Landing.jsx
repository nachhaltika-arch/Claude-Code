import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useScreenSize } from '../utils/responsive';
import PricingSection from '../components/PricingSection';
import AuditHook from '../components/AuditHook';

// ── Markenfarben kompagnon.eu ─────────────────────────────────
const C = {
  primary:   '#004f59',
  primaryDk: '#003840',
  accent:    '#cf549e',
  highlight: '#ffb347',
  bg:        '#f5f5f0',
  text:      '#222222',
  textMid:   '#555555',
  border:    '#dde0d8',
};

// ── SVG-Schrägkante wie kompagnon.eu ─────────────────────────
const DiagDown = ({ from = C.primary, to = C.bg }) => (
  <svg viewBox="0 0 1065 70" preserveAspectRatio="none"
    style={{ display: 'block', width: '100%', background: to, flexShrink: 0 }}>
    <polygon points="0,55 0,70 1065,70 1065,55 1065,0 0,55" fill={from} />
  </svg>
);

const DiagUp = ({ from = C.bg, to = C.primary }) => (
  <svg viewBox="0 0 1065 70" preserveAspectRatio="none"
    style={{ display: 'block', width: '100%', background: to, flexShrink: 0 }}>
    <polygon points="1065,15 1065,0 0,0 0,15 0,70 1065,15" fill={from} />
  </svg>
);

// ── KC Logo SVG (wie kompagnon.eu) ────────────────────────────
const KCLogo = ({ color = '#fff', size = 28 }) => (
  <svg width={size * 3.2} height={size} viewBox="0 0 102 32" fill="none">
    <rect width="34" height="32" rx="2" fill={color === '#fff' ? '#fff' : C.primary}/>
    <text x="17" y="22" textAnchor="middle" fill={color === '#fff' ? C.primary : '#fff'}
      fontSize="14" fontWeight="800" fontFamily="system-ui">KC</text>
    <text x="42" y="22" fill={color} fontSize="13" fontWeight="700"
      fontFamily="system-ui" letterSpacing="-0.3">KOMPAGNON</text>
  </svg>
);

// ── Check-Icon ────────────────────────────────────────────────
const Check = ({ color = C.accent }) => (
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none" style={{ flexShrink: 0 }}>
    <circle cx="9" cy="9" r="9" fill={color + '22'} />
    <path d="M5 9L7.5 11.5L13 6.5" stroke={color} strokeWidth="1.5"
      strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

// ── Haupt-Komponente ──────────────────────────────────────────
export default function Landing() {
  const nav = useNavigate();
  const { isMobile } = useScreenSize();
  const px = isMobile ? '20px' : '60px';
  const go  = (pkg) => nav(`/checkout/${pkg}`);

  const LEISTUNGEN = [
    { icon: '✏️', title: 'Konzeption & Texte',
      desc: 'Individuelle KI-Texte für Ihren Betrieb, Ihre Region und Ihre Zielgruppe.' },
    { icon: '🎨', title: 'Design & Corporate Identity',
      desc: 'Modernes, markengerechtes Design — mobil, schnell und überzeugend.' },
    { icon: '⚡', title: 'Technik & SEO',
      desc: 'SEO-Volloptimierung, PageSpeed, Google Search Console, DSGVO-konform.' },
  ];

  const PROZESS = [
    ['Auftrag', 'Grünes Licht — wir starten sofort.'],
    ['Analyse', 'Wettbewerb, Sichtbarkeit, Zielgruppe.'],
    ['Texte', 'KI-Texte individuell für Ihren Betrieb.'],
    ['Umsetzung', 'Technisch, mobil, suchmaschinenoptimiert.'],
    ['Präsentation', 'Ihre Website — vor dem Go-live.'],
    ['Go-live', 'Live-Schaltung & Einweisung.'],
    ['Betreuung', 'Wir lassen Sie nicht allein.'],
  ];

  const TRUST = [
    'Trustpilot 4.9/5',
    'Trusted Shops',
    'DSGVO-konform',
    'Festpreis 3.500 €',
    '14 Tage Lieferzeit',
  ];

  return (
    <div style={{ fontFamily: 'system-ui, -apple-system, sans-serif',
                  color: C.text, overflowX: 'hidden', background: '#fff' }}>

      {/* ═══════════════════════════════════════════════
          HEADER — wie kompagnon.eu
      ═══════════════════════════════════════════════ */}
      <header style={{
        position: 'sticky', top: 0, zIndex: 100,
        background: '#fff',
        borderBottom: `1px solid ${C.border}`,
        boxShadow: '0 1px 8px rgba(0,0,0,.06)',
      }}>
        <div style={{
          maxWidth: 1140, margin: '0 auto',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: `12px ${px}`,
        }}>
          {/* Logo */}
          <button onClick={() => nav('/')}
            style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0,
                     display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ background: C.primary, borderRadius: 4, padding: '4px 8px',
                          fontWeight: 800, fontSize: 14, color: '#fff', letterSpacing: '-.3px' }}>
              KC
            </div>
            <span style={{ fontWeight: 700, fontSize: 15, color: C.primary,
                           letterSpacing: '-.3px' }}>KOMPAGNON</span>
          </button>

          {/* Desktop Nav */}
          {!isMobile && (
            <nav style={{ display: 'flex', gap: 28, alignItems: 'center' }}>
              {[['Leistungen','#leistungen'],['Preise','#pakete'],['Analyse','#gratis-audit']].map(([l,h]) => (
                <a key={l} href={h} style={{ fontSize: 14, color: C.textMid,
                  textDecoration: 'none', fontWeight: 500,
                  transition: 'color .15s' }}
                  onMouseEnter={e => e.target.style.color = C.primary}
                  onMouseLeave={e => e.target.style.color = C.textMid}>
                  {l}
                </a>
              ))}
              <button onClick={() => nav('/login')}
                style={{ background: 'transparent', color: C.primary,
                  border: `1.5px solid ${C.primary}`, borderRadius: 6,
                  padding: '8px 18px', fontSize: 14, fontWeight: 600,
                  cursor: 'pointer', transition: 'all .15s' }}
                onMouseEnter={e => { e.target.style.background = C.primary; e.target.style.color = '#fff'; }}
                onMouseLeave={e => { e.target.style.background = 'transparent'; e.target.style.color = C.primary; }}>
                Anmelden
              </button>
              <button onClick={() => nav('/checkout/kompagnon')}
                style={{ background: C.accent, color: '#fff', border: 'none',
                  borderRadius: 6, padding: '8px 20px', fontSize: 14,
                  fontWeight: 700, cursor: 'pointer', transition: 'filter .15s' }}
                onMouseEnter={e => e.target.style.filter = 'brightness(1.1)'}
                onMouseLeave={e => e.target.style.filter = 'none'}>
                Website anfragen
              </button>
            </nav>
          )}

          {/* Mobile: kompakter Button */}
          {isMobile && (
            <button onClick={() => nav('/checkout/kompagnon')}
              style={{ background: C.accent, color: '#fff', border: 'none',
                borderRadius: 6, padding: '8px 14px', fontSize: 13,
                fontWeight: 700, cursor: 'pointer' }}>
              Anfragen
            </button>
          )}
        </div>
      </header>

      {/* ═══════════════════════════════════════════════
          HERO — dunkles Teal, Schrägkante unten
      ═══════════════════════════════════════════════ */}
      <section style={{ background: C.primary, paddingTop: isMobile ? 48 : 72 }}>
        <div style={{ maxWidth: 1140, margin: '0 auto', padding: `0 ${px}`,
                      display: isMobile ? 'block' : 'grid',
                      gridTemplateColumns: '1fr 1fr', gap: 48,
                      alignItems: 'center', paddingBottom: isMobile ? 40 : 64 }}>

          {/* Left: Text */}
          <div>
            <div style={{ display: 'inline-block', background: 'rgba(255,255,255,.1)',
              border: '1px solid rgba(255,255,255,.2)', borderRadius: 20,
              padding: '4px 14px', fontSize: 12, color: 'rgba(255,255,255,.8)',
              fontWeight: 600, letterSpacing: '.06em', textTransform: 'uppercase',
              marginBottom: 20 }}>
              Webdesign für Handwerksbetriebe
            </div>
            <h1 style={{ fontSize: 'clamp(28px, 5vw, 52px)', fontWeight: 900,
              color: '#fff', lineHeight: 1.1, margin: '0 0 16px',
              letterSpacing: '-.02em' }}>
              Ihre neue Website.<br/>
              <span style={{ color: C.highlight }}>Fertig in 14 Tagen.</span>
            </h1>
            <p style={{ fontSize: isMobile ? 15 : 18, color: 'rgba(255,255,255,.75)',
              lineHeight: 1.65, margin: '0 0 28px', maxWidth: 480 }}>
              Individuell für Ihren Handwerksbetrieb. KI-optimiert.
              Festpreis ohne versteckte Kosten.
            </p>

            {/* Trust-Badges */}
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 28 }}>
              {TRUST.map(t => (
                <span key={t} style={{ padding: '4px 12px',
                  background: 'rgba(255,255,255,.1)',
                  border: '1px solid rgba(255,255,255,.15)',
                  borderRadius: 20, fontSize: 12,
                  color: 'rgba(255,255,255,.8)', fontWeight: 500 }}>
                  {t}
                </span>
              ))}
            </div>

            {/* CTAs */}
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              <button onClick={() => go('kompagnon')} style={{
                background: C.accent, color: '#fff', border: 'none',
                borderRadius: 8, padding: '14px 28px', fontSize: 15,
                fontWeight: 700, cursor: 'pointer', transition: 'filter .15s',
              }}
                onMouseEnter={e => e.target.style.filter = 'brightness(1.1)'}
                onMouseLeave={e => e.target.style.filter = 'none'}>
                Jetzt anfragen →
              </button>
              <a href="#gratis-audit" style={{
                display: 'inline-flex', alignItems: 'center',
                background: 'rgba(255,255,255,.08)',
                border: '1.5px solid rgba(255,255,255,.3)',
                borderRadius: 8, padding: '14px 24px', fontSize: 15,
                color: '#fff', textDecoration: 'none', fontWeight: 600,
                transition: 'background .15s',
              }}
                onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,.15)'}
                onMouseLeave={e => e.currentTarget.style.background = 'rgba(255,255,255,.08)'}>
                Kostenlose Analyse
              </a>
            </div>
          </div>

          {/* Right: Stat-Karten wie kompagnon.eu */}
          {!isMobile && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
              {[
                ['14', 'Werktage bis Go-live'],
                ['3.500 €', 'Festpreis garantiert'],
                ['340+', 'Handwerksbetriebe'],
                ['4.9 ★', 'Trustpilot'],
              ].map(([num, label]) => (
                <div key={label} style={{
                  background: 'rgba(255,255,255,.07)',
                  border: '1px solid rgba(255,255,255,.12)',
                  borderRadius: 12, padding: '20px 16px', textAlign: 'center',
                }}>
                  <div style={{ fontSize: 28, fontWeight: 800, color: C.highlight,
                                lineHeight: 1, marginBottom: 6 }}>{num}</div>
                  <div style={{ fontSize: 12, color: 'rgba(255,255,255,.65)',
                                fontWeight: 500 }}>{label}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Schrägkante nach unten */}
        <DiagDown from={C.primary} to={C.bg} />
      </section>

      {/* ═══════════════════════════════════════════════
          LEISTUNGEN — 3 Spalten wie kompagnon.eu
      ═══════════════════════════════════════════════ */}
      <section id="leistungen" style={{ background: C.bg,
        padding: isMobile ? '48px 20px' : '72px 60px' }}>
        <div style={{ maxWidth: 1140, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 48 }}>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '.1em',
              textTransform: 'uppercase', color: C.accent, marginBottom: 10 }}>
              Mit Verstand, Emotion und Expertise
            </div>
            <h2 style={{ fontSize: 'clamp(22px, 4vw, 36px)', fontWeight: 800,
              color: C.primary, margin: '0 0 12px' }}>
              Das leisten wir für Sie
            </h2>
            <p style={{ fontSize: 16, color: C.textMid, maxWidth: 520,
              margin: '0 auto', lineHeight: 1.65 }}>
              Von der Konzeption bis zum Go-live — alles aus einer Hand.
              Festpreis. Keine Überraschungen.
            </p>
          </div>

          <div style={{ display: 'grid',
            gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)',
            gap: 20 }}>
            {LEISTUNGEN.map(({ icon, title, desc }) => (
              <div key={title} style={{
                background: '#fff', borderRadius: 12, padding: '28px 24px',
                border: `1px solid ${C.border}`,
                boxShadow: '0 2px 12px rgba(0,79,89,.06)',
                transition: 'transform .2s, box-shadow .2s',
              }}
                onMouseEnter={e => {
                  e.currentTarget.style.transform = 'translateY(-4px)';
                  e.currentTarget.style.boxShadow = '0 8px 28px rgba(0,79,89,.12)';
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.transform = 'none';
                  e.currentTarget.style.boxShadow = '0 2px 12px rgba(0,79,89,.06)';
                }}>
                <div style={{ fontSize: 36, marginBottom: 14 }}>{icon}</div>
                <div style={{ fontSize: 17, fontWeight: 700, color: C.primary,
                              marginBottom: 8 }}>{title}</div>
                <div style={{ fontSize: 14, color: C.textMid, lineHeight: 1.65 }}>
                  {desc}
                </div>
              </div>
            ))}
          </div>

          {/* 6-Feature-Grid darunter */}
          <div style={{ display: 'grid',
            gridTemplateColumns: isMobile ? '1fr 1fr' : 'repeat(6, 1fr)',
            gap: 12, marginTop: 20 }}>
            {[
              ['🎯', 'Individuelle Texte'],
              ['📱', 'Mobile First'],
              ['⚖️', 'Rechtssicher'],
              ['🔍', 'KI-SEO'],
              ['⚡', '14 Tage'],
              ['🏆', 'Festpreis'],
            ].map(([icon, label]) => (
              <div key={label} style={{
                background: '#fff', border: `1px solid ${C.border}`,
                borderRadius: 8, padding: '12px 8px', textAlign: 'center',
              }}>
                <div style={{ fontSize: 20, marginBottom: 4 }}>{icon}</div>
                <div style={{ fontSize: 11, fontWeight: 600, color: C.primary }}>
                  {label}
                </div>
              </div>
            ))}
          </div>
        </div>

        <DiagUp from={C.bg} to={C.primary} />
      </section>

      {/* ═══════════════════════════════════════════════
          GRATIS AUDIT — bestehende Komponente
      ═══════════════════════════════════════════════ */}
      <AuditHook />

      {/* ═══════════════════════════════════════════════
          PREISPAKETE — bestehende Komponente
      ═══════════════════════════════════════════════ */}
      <PricingSection />

      {/* ═══════════════════════════════════════════════
          PROZESS — 7 Schritte wie kompagnon.eu
      ═══════════════════════════════════════════════ */}
      <section style={{ background: C.bg, padding: isMobile ? '48px 20px' : '72px 60px' }}>
        <DiagDown from={'#fff'} to={C.bg} />
        <div style={{ maxWidth: 1140, margin: '0 auto', paddingTop: 40 }}>
          <div style={{ textAlign: 'center', marginBottom: 48 }}>
            <h2 style={{ fontSize: 'clamp(22px, 4vw, 36px)', fontWeight: 800,
              color: C.primary, margin: '0 0 10px' }}>
              Ihr Weg zur neuen Website
            </h2>
            <p style={{ fontSize: 16, color: C.textMid }}>
              In 7 Schritten. Maximal 14 Werktage.
            </p>
          </div>

          <div style={{
            display: isMobile ? 'flex' : 'grid',
            flexDirection: isMobile ? 'column' : undefined,
            gridTemplateColumns: isMobile ? undefined : `repeat(${PROZESS.length}, 1fr)`,
            gap: isMobile ? 12 : 0,
            position: 'relative',
          }}>
            {/* Verbindungslinie Desktop */}
            {!isMobile && (
              <div style={{ position: 'absolute', top: 22, left: '7%', right: '7%',
                height: 2, background: C.border, zIndex: 0 }} />
            )}

            {PROZESS.map(([title, desc], i) => (
              <div key={i} style={{
                textAlign: isMobile ? 'left' : 'center',
                position: 'relative', zIndex: 1,
                display: isMobile ? 'flex' : 'block',
                alignItems: isMobile ? 'flex-start' : undefined,
                gap: isMobile ? 14 : 0,
              }}>
                <div style={{
                  width: 44, height: 44, borderRadius: '50%',
                  background: i < 3 ? C.primary : '#fff',
                  border: `2px solid ${C.primary}`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  margin: isMobile ? '0' : '0 auto 12px',
                  flexShrink: 0,
                  fontSize: 15, fontWeight: 700,
                  color: i < 3 ? '#fff' : C.primary,
                }}>
                  {i + 1}
                </div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: C.primary,
                                marginBottom: 3 }}>{title}</div>
                  <div style={{ fontSize: 11, color: C.textMid, lineHeight: 1.5 }}>
                    {desc}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════
          KONTAKT-SEKTION — wie kompagnon.eu Kontaktformular
      ═══════════════════════════════════════════════ */}
      <section style={{ background: C.primary }}>
        <DiagUp from={C.bg} to={C.primary} />
        <div style={{ maxWidth: 900, margin: '0 auto',
          padding: isMobile ? '40px 20px 60px' : '60px 60px 80px',
          display: isMobile ? 'block' : 'grid',
          gridTemplateColumns: '1fr 1fr', gap: 60,
          alignItems: 'start' }}>

          {/* Left: Kontaktdaten wie kompagnon.eu */}
          <div>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '.1em',
              textTransform: 'uppercase', color: C.highlight, marginBottom: 10 }}>
              Sprechen Sie mit uns
            </div>
            <h2 style={{ fontSize: 'clamp(22px, 4vw, 34px)', fontWeight: 800,
              color: '#fff', margin: '0 0 16px', lineHeight: 1.2 }}>
              Jetzt Ihre Webseite anfragen
            </h2>
            <p style={{ fontSize: 15, color: 'rgba(255,255,255,.7)',
              lineHeight: 1.65, marginBottom: 28 }}>
              Wir melden uns innerhalb von 24 Stunden bei Ihnen —
              kostenlos und unverbindlich.
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {[
                ['📞', '+49 (0) 261 884470'],
                ['✉️', 'info@kompagnon.eu'],
                ['📍', 'Marienfelder Straße 52, 56070 Koblenz'],
              ].map(([icon, text]) => (
                <div key={text} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                  <span style={{ fontSize: 16 }}>{icon}</span>
                  <span style={{ fontSize: 14, color: 'rgba(255,255,255,.8)' }}>{text}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Right: schnelles Kontakt-CTA */}
          <div style={{ background: 'rgba(255,255,255,.06)',
            border: '1px solid rgba(255,255,255,.12)',
            borderRadius: 14, padding: 28 }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: '#fff',
              marginBottom: 16 }}>
              Gratis Erstgespräch buchen
            </div>
            {['Ihr Name', 'Ihre E-Mail', 'Telefonnummer', 'Ihre Website (optional)'].map(ph => (
              <input key={ph} placeholder={ph} disabled style={{
                width: '100%', marginBottom: 10, padding: '11px 14px',
                background: 'rgba(255,255,255,.08)',
                border: '1px solid rgba(255,255,255,.2)',
                borderRadius: 8, fontSize: 14,
                color: 'rgba(255,255,255,.5)',
                fontFamily: 'inherit',
              }} />
            ))}
            <button onClick={() => window.location.href='mailto:info@kompagnon.eu'}
              style={{
                width: '100%', padding: '13px 0',
                background: C.accent, color: '#fff', border: 'none',
                borderRadius: 8, fontSize: 15, fontWeight: 700,
                cursor: 'pointer', transition: 'filter .15s',
              }}
              onMouseEnter={e => e.target.style.filter = 'brightness(1.1)'}
              onMouseLeave={e => e.target.style.filter = 'none'}>
              Jetzt anfragen →
            </button>
            <p style={{ fontSize: 11, color: 'rgba(255,255,255,.4)',
              textAlign: 'center', marginTop: 10 }}>
              DSGVO-konform · Keine Weitergabe an Dritte
            </p>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════
          FOOTER — wie kompagnon.eu
      ═══════════════════════════════════════════════ */}
      <footer style={{ background: C.primaryDk, padding: isMobile ? '32px 20px' : '48px 60px' }}>
        <div style={{ maxWidth: 1140, margin: '0 auto',
          display: isMobile ? 'block' : 'grid',
          gridTemplateColumns: '2fr 1fr 1fr 1fr', gap: 40 }}>

          {/* Logo + Beschreibung */}
          <div style={{ marginBottom: isMobile ? 28 : 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
              <div style={{ background: '#fff', borderRadius: 4, padding: '3px 7px',
                fontWeight: 800, fontSize: 13, color: C.primary }}>KC</div>
              <span style={{ fontWeight: 700, fontSize: 14, color: '#fff' }}>KOMPAGNON</span>
            </div>
            <p style={{ fontSize: 13, color: 'rgba(255,255,255,.55)', lineHeight: 1.65,
              maxWidth: 280, margin: '0 0 16px' }}>
              Webdesign für Handwerksbetriebe — KI-optimiert, rechtssicher,
              fertig in 14 Tagen.
            </p>
            <div style={{ display: 'flex', gap: 10 }}>
              {['Facebook','Instagram','LinkedIn','XING'].map(s => (
                <div key={s} style={{
                  width: 32, height: 32, borderRadius: '50%',
                  background: 'rgba(255,255,255,.08)',
                  border: '1px solid rgba(255,255,255,.12)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 11, color: 'rgba(255,255,255,.5)', cursor: 'pointer',
                }}>
                  {s[0]}
                </div>
              ))}
            </div>
          </div>

          {/* Links */}
          {[
            ['Leistungen', ['Webdesign','KI-Texte','SEO','Rechtssicher','Portal']],
            ['Pakete', ['Starter 1.500€','Kompagnon 3.500€','Premium','Förderung']],
            ['Rechtliches', ['Impressum','Datenschutz','Barrierefreiheit']],
          ].map(([title, links]) => (
            <div key={title} style={{ marginBottom: isMobile ? 20 : 0 }}>
              <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '.08em',
                textTransform: 'uppercase', color: 'rgba(255,255,255,.4)',
                marginBottom: 12 }}>
                {title}
              </div>
              {links.map(l => (
                <div key={l} style={{ marginBottom: 8 }}>
                  <a href="#" style={{ fontSize: 13, color: 'rgba(255,255,255,.6)',
                    textDecoration: 'none', transition: 'color .15s' }}
                    onMouseEnter={e => e.target.style.color = '#fff'}
                    onMouseLeave={e => e.target.style.color = 'rgba(255,255,255,.6)'}>
                    {l}
                  </a>
                </div>
              ))}
            </div>
          ))}
        </div>

        <div style={{ maxWidth: 1140, margin: '28px auto 0',
          borderTop: '1px solid rgba(255,255,255,.08)',
          paddingTop: 20, display: 'flex',
          justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
          <span style={{ fontSize: 12, color: 'rgba(255,255,255,.35)' }}>
            © 2026 KOMPAGNON Communications BP GmbH · Koblenz
          </span>
          <span style={{ fontSize: 12, color: 'rgba(255,255,255,.25)' }}>
            50° 23' N 7° 35' E
          </span>
        </div>
      </footer>
    </div>
  );
}
