// ProzessFlowV3 — Wizard-Interface mit Breadcrumb
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import API_BASE_URL from '../config';
import { useScreenSize } from '../utils/responsive';
import AnalyseCentrale from './AnalyseCentrale';
import ContentWerkstatt from './ContentWerkstatt';
import DesignStudio from './DesignStudio';
import BriefingTab from './BriefingTab';
import BrandDesignWerkstatt from './BrandDesignWerkstatt';
import BrandDesignEditor from './BrandDesignEditor';
import BrandGuideline from './BrandGuideline';
import SeoAnalyseStep from './SeoAnalyseStep';
import SitemapVorschlaege from './SitemapVorschlaege';
import ZieleZielgruppe from './briefing/ZieleZielgruppe';
import AssetsKlaeren from './briefing/AssetsKlaeren';
import Funktionen from './briefing/Funktionen';
import SeoZiele from './briefing/SeoZiele';
import {
  BriefingUnternehmenEmbed,
  AuditEmbed,
  SitemapKiVorschlag,
  SitemapEditorEmbed,
  DesignStudioEmbed,
  NetlifyEmbed,
  DNSEmbed,
  QAEmbed,
  AbnahmeEmbed,
  ZugangsdatenEmbed,
} from './EmbedComponents';

// ── Schritt-Definitionen (Logik 1:1 aus ProzessFlow.jsx) ─────────────────────
const SCHRITTE = [
  {
    id: 'briefing-unternehmen', nr: 1, phase: 'Analyse',
    icon: '🏢', label: 'Briefing', auto: false,
    cta: 'Briefing ausfüllen →',
    desc: 'Gewerk, Leistungen und euren USP eintragen — das ist die Basis für alles.',
    component: 'BriefingUnternehmen',
    istFertig: (d) => !!(d.briefing?.gewerk && d.briefing?.leistungen?.trim()),
    fertigText: (d) => d.briefing?.gewerk || 'Ausgefüllt',
  },
  {
    id: 'ziele-zielgruppe', nr: 2, phase: 'Analyse',
    icon: '🎯', label: 'Ziele & Zielgruppe', auto: false,
    cta: 'Bestätigen & weiter →',
    desc: 'KI leitet Ziele und Zielgruppe automatisch ab — bitte prüfen.',
    component: 'ZieleZielgruppe',
    istFertig: (d) => !!(d.briefing?.hauptziel && d.briefing?.aktionen),
    fertigText: () => 'Ausgefüllt',
  },
  {
    id: 'assets', nr: 3, phase: 'Analyse',
    icon: '📦', label: 'Assets klären', auto: false, optional: true,
    cta: 'Assets bestätigen →',
    desc: 'Logo, Fotos und CI-Materialien — werden automatisch erkannt.',
    component: 'AssetsKlaeren',
    istFertig: (d) => d.briefing?.logo_vorhanden !== undefined && d.briefing?.logo_vorhanden !== '',
    fertigText: () => 'Assets geklärt',
  },
  {
    id: 'funktionen', nr: 4, phase: 'Analyse',
    icon: '⚙️', label: 'Funktionen', auto: false, optional: true,
    cta: 'Funktionen bestätigen →',
    desc: 'Terminbuchung, Shop, Sprachen, externe Tools — automatisch erkannt.',
    component: 'Funktionen',
    istFertig: (d) => { try { const f = d.briefing?.funktionen_json; if (!f) return false; const p = typeof f === 'string' ? JSON.parse(f) : f; return !!p?.bestaetigt; } catch { return false; } },
    fertigText: () => 'Funktionen geklärt',
  },
  {
    id: 'seo-ziele', nr: 5, phase: 'Analyse',
    icon: '📈', label: 'SEO-Ziele', auto: false,
    cta: 'SEO-Ziele bestätigen →',
    desc: 'Keywords automatisch generiert — Google Business und Social Media aus Website erkannt.',
    component: 'SeoZiele',
    istFertig: (d) => { try { const s = d.briefing?.seo_json; if (!s) return false; const p = typeof s === 'string' ? JSON.parse(s) : s; return !!(p?.bestaetigt && p?.keywords?.length > 0); } catch { return false; } },
    fertigText: () => 'SEO-Ziele gesetzt',
  },
  {
    id: 'audit', nr: 6, phase: 'Analyse',
    icon: '🔍', label: 'Website-Audit', auto: false,
    cta: 'Audit starten →',
    desc: 'Technische Analyse der alten Website — Score, Probleme und Empfehlungen.',
    component: 'Audit',
    istFertig: (d) => !!(d.latestAudit?.total_score > 0),
    fertigText: (d) => `Score: ${d.latestAudit?.total_score}/100`,
  },
  {
    id: 'analyse-zentrale', nr: 7, phase: 'Analyse',
    icon: '🔬', label: 'Vollanalyse', auto: false,
    cta: 'Vollanalyse starten →',
    desc: 'Crawler, PageSpeed, GA und Hosting werden gleichzeitig gemessen.',
    component: 'AnalyseZentrale',
    istFertig: (d) => (d.crawlPages || 0) >= 3,
    fertigText: (d) => `${d.crawlPages} Seiten gecrawlt`,
  },
  {
    id: 'brand-design', nr: 8, phase: 'Analyse',
    icon: '🎨', label: 'Brand Design', auto: false,
    cta: 'Brand Design speichern →',
    desc: 'Farben, Schriften und Stil fuer die neue Website festlegen.',
    component: 'BrandDesign',
    istFertig: (d) => !!(d.brandPrimaryColor),
    fertigText: (d) => d.brandPrimaryColor || 'Gespeichert',
  },
  {
    id: 'brand-guideline', nr: 9, phase: 'Analyse',
    icon: '📐', label: 'Brand Guideline', auto: false,
    cta: 'Guideline generieren →',
    desc: 'KI erstellt Farb-Tokens, Typografie-Skala und Komponenten-Stile aus den Brand-Daten.',
    component: 'BrandGuideline',
    istFertig: (d) => !!(d.brandGuidelineGenerated),
    fertigText: () => 'Design-System erstellt',
  },
  {
    id: 'seo-analyse', nr: 10, phase: 'Analyse',
    icon: '📊', label: 'SEO-Analyse', auto: false,
    cta: 'SEO-Analyse starten →',
    desc: 'Lokale SEO-Positionierung analysieren — Keywords, On-Page, Wettbewerber.',
    component: 'SeoAnalyse',
    istFertig: (d) => !!(d.seoCompleted),
    fertigText: (d) => d.seoScore ? `Score: ${d.seoScore}` : 'Abgeschlossen',
  },
  {
    id: 'briefing-website', nr: 11, phase: 'Analyse',
    icon: '📋', label: 'Briefing: Website', auto: false,
    cta: 'Website-Briefing ausfüllen →',
    desc: 'Ziele, gewünschte Seiten und Design-Wünsche dokumentieren.',
    component: 'BriefingWebsite',
    istFertig: (d) => !!((d.briefing?.hauptziel && d.briefing?.aktionen) || d.briefing?.seiten),
    fertigText: () => 'Ausgefüllt',
  },
  {
    id: 'zugangsdaten', nr: 12, phase: 'Analyse',
    icon: '🔑', label: 'Zugangsdaten', auto: false, optional: true,
    cta: 'Zugangsdaten speichern →',
    desc: 'Hosting, FTP und CMS-Zugänge sicher speichern.',
    component: 'Zugangsdaten',
    istFertig: (d) => (d.credsCount || 0) >= 1,
    fertigText: (d) => `${d.credsCount} Einträge`,
  },
  {
    id: 'sitemap', nr: 13, phase: 'Content',
    icon: '🗺️', label: 'Sitemap', auto: false,
    cta: 'KI-Sitemap generieren →',
    desc: 'KI legt alle Seiten aus dem Briefing an — 1 Klick.',
    component: 'Sitemap',
    istFertig: (d) => (d.sitemapCount || 0) >= 3,
    fertigText: (d) => `${d.sitemapCount} Seiten`,
  },
  {
    id: 'seiteninhalte', nr: 14, phase: 'Content',
    icon: '📝', label: 'Seiteninhalte', auto: false,
    cta: 'Alle Texte generieren →',
    desc: 'KI schreibt alle Seiten auf einmal — ca. 60 Sekunden.',
    component: 'Seiteninhalte',
    istFertig: (d) => (d.sitemapCount || 0) > 0 && (d.contentCount || 0) >= (d.sitemapCount || 1),
    fertigText: (d) => `${d.contentCount}/${d.sitemapCount} Seiten`,
  },
  {
    id: 'bilder-assets', nr: 15, phase: 'Content',
    icon: '🖼️', label: 'Bilder & Assets', auto: false, optional: true,
    cta: 'Weiter zu Freigaben →',
    desc: 'Fotos, Icons und Medien jeder Seite zuweisen.',
    component: 'BilderAssets',
    istFertig: (d) => !!(d.assetsChecked),
    fertigText: () => 'Geprueft',
  },
  {
    id: 'freigaben', nr: 16, phase: 'Content',
    icon: '✅', label: 'Freigaben', auto: false, optional: true,
    cta: 'Freigabe anfordern →',
    desc: 'Content-Freigabe vom Kunden einholen.',
    component: 'Freigaben',
    istFertig: (d) => !!(d.contentApproved),
    fertigText: () => 'Freigegeben',
  },
  {
    id: 'design-generieren', nr: 17, phase: 'Design',
    icon: '🎨', label: 'Design wählen', auto: false,
    cta: 'Design generieren →',
    desc: 'KI erstellt 3 Entwürfe — du wählst den besten.',
    component: 'DesignStudio',
    istFertig: (d) => (d.designVersions || 0) >= 1,
    fertigText: (d) => `${d.designVersions} Version(en)`,
  },
  {
    id: 'editor', nr: 18, phase: 'Design',
    icon: '🖊️', label: 'Feinschliff', auto: false, optional: true,
    cta: 'Editor öffnen →',
    desc: 'Echte Fotos einsetzen, Texte prüfen, Mobile-Ansicht testen.',
    component: 'Editor',
    istFertig: (d) => !!(d.editorSaved),
    fertigText: () => 'Gespeichert',
  },
  {
    id: 'netlify', nr: 19, phase: 'Go Live',
    icon: '🚀', label: 'Veröffentlichen', auto: false,
    cta: 'Jetzt veröffentlichen →',
    desc: 'Website live schalten — 1 Klick, Netlify deployt automatisch.',
    component: 'Netlify',
    istFertig: (d) => !!(d.netlifyUrl && d.netlifyReady),
    fertigText: (d) => d.netlifyUrl || 'Deployed',
  },
  {
    id: 'dns', nr: 20, phase: 'Go Live',
    icon: '🌍', label: 'Domain verbinden', auto: true,
    autoText: 'DNS-Anleitung wird automatisch per E-Mail an den Kunden gesendet — du musst nichts tun.',
    desc: 'Anleitung geht direkt an den Kunden.',
    component: 'DNS',
    istFertig: (d) => !!(d.domainReachable && d.domainStatusCode === 200),
    fertigText: () => 'Domain erreichbar',
  },
  {
    id: 'qa', nr: 21, phase: 'Go Live',
    icon: '✅', label: 'QM-Audit', auto: false,
    cta: 'QM-Audit starten →',
    desc: 'Qualitaetskontrolle der neuen Website — gleicher Audit, neue Seite.',
    component: 'QA',
    istFertig: (d) => !!(d.qaResult),
    fertigText: () => 'QM abgeschlossen',
  },
  {
    id: 'abnahme', nr: 22, phase: 'Go Live',
    icon: '🏁', label: 'Go Live!', auto: false,
    cta: 'Abnahme erteilen →',
    desc: 'Finale Kundenfreigabe und Go-Live.',
    component: 'Abnahme',
    istFertig: (d) => !!(d.goLiveConfirmed || d.projectStatus === 'fertig'),
    fertigText: () => '🎉 Live!',
  },
];

// ── Haupt-Komponente ──────────────────────────────────────────────────────────

export default function ProzessFlowV3({
  project, lead, token, briefing, latestAudit, onAuditUpdate,
  onSitemapReload, onBrandUpdate, onCrawlUpdate,
  crawlPages, sitemapPages, sitemapLoading,
  websiteContent, brandData, netlify, qaResult,
}) {
  const navigate   = useNavigate();
  const { isMobile } = useScreenSize();
  const headers    = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };
  const leadId     = project?.lead_id || lead?.id;
  const companyName = lead?.display_name || lead?.company_name || project?.company_name || 'Projekt';

  const [localBriefing,    setLocalBriefing]    = useState(briefing);
  const [localLatestAudit, setLocalLatestAudit] = useState(latestAudit);
  const [localCrawlPages,  setLocalCrawlPages]  = useState(crawlPages);
  const [localBrandColor,  setLocalBrandColor]  = useState(brandData?.primary_color || null);

  useEffect(() => { setLocalBriefing(briefing); },     [briefing]);     // eslint-disable-line
  useEffect(() => { setLocalLatestAudit(latestAudit); }, [latestAudit]); // eslint-disable-line
  useEffect(() => { setLocalCrawlPages(crawlPages); },  [crawlPages]);   // eslint-disable-line
  useEffect(() => {
    if (brandData?.primary_color) setLocalBrandColor(brandData.primary_color);
  }, [brandData]); // eslint-disable-line

  const [confirmedSteps, setConfirmedSteps] = useState(project?.steps_confirmed || {});
  useEffect(() => {
    if (!project?.id) return;
    fetch(`${API_BASE_URL}/api/projects/${project.id}/confirmed-steps`, { headers })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setConfirmedSteps(d.confirmed_steps || {}); })
      .catch(() => {});
  }, [project?.id]); // eslint-disable-line

  const reloadConfirmedSteps = async () => {
    if (!project?.id) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/projects/${project.id}/confirmed-steps`, { headers });
      if (res.ok) { const d = await res.json(); setConfirmedSteps(d.confirmed_steps || {}); }
    } catch { /* silent */ }
  };

  const prozessDaten = {
    briefing:         localBriefing,
    latestAudit:      localLatestAudit,
    crawlPages:       localCrawlPages || 0,
    brandPrimaryColor: localBrandColor || null,
    confirmedSteps,
    brandGuidelineGenerated: !!(confirmedSteps['brand-guideline']?.confirmed || lead?.brand_guideline_json || brandData?.guideline_generated),
    seoCompleted: false,
    seoScore: null,
    sitemapCount:     sitemapPages?.length || 0,
    contentCount:     (websiteContent || []).filter(p => p.ki_content || p.content_generated).length,
    assetsChecked:    !!(project?.assets_checked),
    contentApproved:  !!(project?.content_approved_at),
    credsCount:       0,
    designVersions:   0,
    editorSaved:      !!((sitemapPages || []).some(p => p.gjs_html?.trim())),
    netlifyUrl:       netlify?.netlify_site_url || netlify?.url || project?.netlify_site_url || null,
    netlifyReady:     !!(netlify?.state === 'ready' || netlify?.connected === true || project?.netlify_last_deploy || netlify?.netlify_last_deploy),
    domainReachable:  project?.domain_reachable || false,
    domainStatusCode: project?.domain_status_code || null,
    qaResult,
    projectStatus:    project?.status || '',
    goLiveConfirmed:  false,
  };

  const aktiverIdx  = SCHRITTE.findIndex(s => !s.istFertig(prozessDaten));
  const aktiverId   = aktiverIdx >= 0 ? SCHRITTE[aktiverIdx].id : SCHRITTE[SCHRITTE.length - 1].id;
  const [offenerSchritt, setOffenerSchritt] = useState(aktiverId);

  const fertigCount = SCHRITTE.filter(s => s.istFertig(prozessDaten)).length;
  const gesamtPct   = Math.round((fertigCount / SCHRITTE.length) * 100);
  const aktivObj    = SCHRITTE.find(s => s.id === offenerSchritt) || SCHRITTE[0];
  const aktivIdx    = SCHRITTE.findIndex(s => s.id === offenerSchritt);
  const doneSchritte = SCHRITTE.slice(0, aktivIdx).filter(s => s.istFertig(prozessDaten));
  const nextSchritte = SCHRITTE.slice(aktivIdx + 1, aktivIdx + 3);

  const handleAnalyseUpdate = useCallback((data) => {
    if (data.crawlPages != null) setLocalCrawlPages(data.crawlPages);
    if (data.brandPrimaryColor) setLocalBrandColor(data.brandPrimaryColor);
    if (data.brandPrimaryColor && onBrandUpdate) onBrandUpdate(data.brandData);
    if (data.crawlPages != null && onCrawlUpdate) onCrawlUpdate(data.crawlPages);
  }, [onBrandUpdate, onCrawlUpdate]); // eslint-disable-line

  const handleAuditComplete = useCallback((audit) => {
    setLocalLatestAudit(audit);
    if (onAuditUpdate) onAuditUpdate(audit);
  }, [onAuditUpdate]); // eslint-disable-line

  const reloadBriefing = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/briefings/${leadId}`, { headers });
      if (res.ok) setLocalBriefing(await res.json());
    } catch { /* silent */ }
  };

  const goWeiter = () => {
    if (aktivIdx < SCHRITTE.length - 1) setOffenerSchritt(SCHRITTE[aktivIdx + 1].id);
  };
  const goZurueck = () => {
    if (aktivIdx > 0) setOffenerSchritt(SCHRITTE[aktivIdx - 1].id);
  };

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '80px 1fr',
      height: isMobile ? '100%' : '100vh',
      minHeight: 0,
      background: 'var(--surface)',
      overflow: 'hidden',
      fontFamily: 'var(--font-sans)',
    }}>
      {/* ── TIMELINE (links, 80px) ── */}
      <div style={{
        width: 80,
        background: 'linear-gradient(180deg, #004F59 0%, #003840 100%)',
        display: 'flex', flexDirection: 'column',
        alignItems: 'center',
        height: '100%', flexShrink: 0,
        ...(isMobile ? {} : { minHeight: '100vh' }),
        boxShadow: '2px 0 16px rgba(0,0,0,.25)',
      }}>

        {/* SVG Logo */}
        <div style={{
          width: '100%', padding: '14px 0 12px',
          display: 'flex', justifyContent: 'center', alignItems: 'center',
          borderBottom: '0.5px solid rgba(255,255,255,.1)',
          marginBottom: 12, flexShrink: 0,
        }}>
          <svg width="38" height="38" viewBox="0 0 107.7 107.7" xmlns="http://www.w3.org/2000/svg" style={{ display: 'block' }}>
            <path fill="#008EAA" d="M5.7,53.8c0,11.8,4.3,22.7,11.3,31.1,3.4-19.9,14-59.4,20-76.2C18.7,15.5,5.7,33.1,5.7,53.8Z"/>
            <path fill="#008EAA" d="M55.1,5.7c-1.4,5.4-6.4,24.1-10.4,38.4,7.1-8.9,16.2-15,23.5-15.5.8,0,1.4,0,2.3,0,4.5.2,14.6,4.8,15.5,13.5.3,5.4-4.1,15.5-8.2,15.8-5.1.3-9.7-6.1-9.8-7.4-.2-3,2.6-6.7,2.5-7.8,0-.4-.6-.5-1-.4-2.5.2-18.9,17.5-18,33.3.3,5.3,2.2,8.7,9.2,8.3,9.1-.6,18.2-8,28-22.4,1.1-1.6,2.4-2.3,3.5-2.4,2.3-.1,4.5,1.9,4.6,4.6,0,.8,0,1.7-.5,2.5-.7,1.4-5,8.2-10.9,14.5-7.8,8.5-17.6,13.2-26.5,14.5-4.9.7-10.6-.3-15.2-2.7-3.8-1.9-8.1-5.9-9.6-10.7-1.4,5.3-2.7,10.5-3.9,14.2,7,3.9,15,6.1,23.5,6.1,26.6,0,48.2-21.6,48.2-48.2S81.1,6.3,55.1,5.7Z"/>
          </svg>
        </div>

        {/* Nummerierte Schritte */}
        <div style={{
          flex: 1, display: 'flex', flexDirection: 'column',
          alignItems: 'center', gap: 4,
          padding: '4px 0', overflowY: 'auto',
          width: '100%', scrollbarWidth: 'none',
        }}>
          {SCHRITTE.map((s, idx) => {
            const fertig = s.istFertig(prozessDaten);
            const aktiv  = s.id === offenerSchritt;
            const naechster = !fertig && !aktiv && idx === aktivIdx + 1;
            const size = aktiv ? 36 : naechster ? 30 : fertig ? 30 : 26;
            const bg = fertig ? '#00875A'
              : aktiv ? '#FAE600'
              : naechster ? 'rgba(255,255,255,.15)'
              : 'rgba(255,255,255,.06)';
            const color = fertig ? '#fff'
              : aktiv ? '#004F59'
              : naechster ? 'rgba(255,255,255,.7)'
              : 'rgba(255,255,255,.25)';

            return (
              <div
                key={s.id}
                onClick={() => setOffenerSchritt(s.id)}
                title={`${s.nr}. ${s.label}`}
                style={{
                  position: 'relative',
                  width: size, height: size,
                  borderRadius: '50%',
                  background: bg, color,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontFamily: "'Barlow Condensed', var(--font-sans)",
                  fontSize: aktiv ? 15 : size <= 26 ? 11 : 13,
                  fontWeight: 700,
                  cursor: 'pointer', flexShrink: 0,
                  transition: 'all .2s', userSelect: 'none',
                  boxShadow: aktiv
                    ? '0 0 0 3px rgba(250,230,0,.3), 0 3px 12px rgba(250,230,0,.4)'
                    : fertig ? '0 2px 6px rgba(0,135,90,.35)'
                    : naechster ? '0 0 0 1px rgba(255,255,255,.2)'
                    : 'none',
                  animation: aktiv ? 'stepPulse 2s ease-in-out infinite' : 'none',
                }}
              >
                {fertig ? '✓' : s.nr}
              </div>
            );
          })}
        </div>

        {/* Avatar + Fortschritt */}
        <div style={{
          width: '100%', padding: '10px 0 12px',
          borderTop: '0.5px solid rgba(255,255,255,.1)',
          display: 'flex', flexDirection: 'column',
          alignItems: 'center', gap: 4, flexShrink: 0,
        }}>
          <div style={{
            width: 30, height: 30, borderRadius: '50%',
            background: '#008EAA',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 10, fontWeight: 900, color: '#fff',
            fontFamily: 'var(--font-sans)',
          }}>DA</div>
          <div style={{
            fontSize: 9, fontWeight: 900,
            color: 'rgba(255,255,255,.3)',
            textTransform: 'uppercase', letterSpacing: '.06em',
          }}>{gesamtPct}%</div>
        </div>

      </div>

      {/* ── CONTENT (rechts) ── */}
      <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

        {/* BREADCRUMB */}
        <div style={{
          background: '#fff',
          borderBottom: '0.5px solid var(--border)',
          padding: '0 20px', height: 40,
          display: 'flex', alignItems: 'center',
          gap: 0, flexShrink: 0,
        }}>
          <BreadcrumbItem
            onClick={() => navigate('/app/dashboard')}
            icon={
              <svg width="11" height="11" viewBox="0 0 12 12" fill="currentColor" style={{ flexShrink: 0 }}>
                <path d="M1 5.5L6 1.5L11 5.5V10.5H8V7.5H4V10.5H1V5.5Z" opacity=".7"/>
              </svg>
            }
            label="Dashboard"
          />
          <BreadcrumbSep />
          <BreadcrumbItem onClick={() => navigate('/app/projects')} label="Projekte" />
          <BreadcrumbSep />
          <BreadcrumbItem
            onClick={() => leadId && navigate(`/app/leads/${leadId}`)}
            dot
            label={companyName}
          />
          <BreadcrumbSep />
          <div style={{
            fontSize: 10, fontWeight: 900,
            textTransform: 'uppercase', letterSpacing: '.08em',
            color: 'var(--text-60)',
            cursor: 'default', padding: '4px 6px',
            fontFamily: 'var(--font-sans)',
          }}>
            Schritt {aktivObj.nr} · {aktivObj.label}
          </div>
        </div>

        {/* PROJEKT-BAR */}
        <div style={{
          background: '#fff',
          borderBottom: '0.5px solid var(--border)',
          padding: '0 20px', height: 44,
          display: 'flex', alignItems: 'center',
          justifyContent: 'space-between', flexShrink: 0,
        }}>
          <div>
            <div style={{
              fontFamily: 'var(--font-display)',
              fontSize: 15, fontWeight: 700,
              color: 'var(--kc-dark)',
              textTransform: 'uppercase', letterSpacing: '.02em',
            }}>{companyName}</div>
            <div style={{
              fontSize: 10, fontWeight: 700,
              color: 'var(--text-30)',
              textTransform: 'uppercase', letterSpacing: '.06em',
            }}>
              {lead?.city || ''}{lead?.trade ? ` · ${lead.trade}` : ''}
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{
              width: 100, height: 5,
              background: 'var(--border)',
              borderRadius: 3, overflow: 'hidden',
            }}>
              <div style={{
                height: '100%', width: `${gesamtPct}%`,
                background: 'var(--kc-mid)',
                borderRadius: 3, transition: 'width .5s',
              }} />
            </div>
            <div style={{
              fontSize: 10, fontWeight: 900,
              color: 'var(--text-30)',
              textTransform: 'uppercase', letterSpacing: '.06em',
              whiteSpace: 'nowrap',
            }}>{fertigCount} / {SCHRITTE.length}</div>
          </div>
        </div>

        {/* ERLEDIGTE SCHRITTE (kompakt) */}
        {doneSchritte.length > 0 && (
          <div style={{ padding: '10px 20px 0', flexShrink: 0 }}>
            {doneSchritte.slice(-3).map(s => (
              <div key={s.id} style={{
                display: 'flex', alignItems: 'center', gap: 7,
                fontSize: 10, color: 'var(--text-30)',
                fontWeight: 700, textTransform: 'uppercase',
                letterSpacing: '.04em', padding: '2px 0',
                fontFamily: 'var(--font-sans)',
              }}>
                <div style={{
                  width: 14, height: 14, borderRadius: '50%',
                  background: 'var(--success)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 7, fontWeight: 900, color: '#fff', flexShrink: 0,
                }}>✓</div>
                {s.phase} · {s.label}
              </div>
            ))}
            {doneSchritte.length > 3 && (
              <div style={{
                fontSize: 10, color: 'var(--text-30)',
                paddingLeft: 21, fontWeight: 700,
                fontFamily: 'var(--font-sans)',
              }}>
                + {doneSchritte.length - 3} weitere erledigt
              </div>
            )}
          </div>
        )}

        {/* AKTIVER SCHRITT (Hauptbereich) */}
        <div style={{
          flex: 1, display: 'flex', flexDirection: 'column',
          padding: '20px', overflowY: 'auto',
        }}>
          <div style={{
            fontSize: 10, fontWeight: 900,
            textTransform: 'uppercase', letterSpacing: '.12em',
            color: 'var(--text-30)', marginBottom: 6,
            fontFamily: 'var(--font-sans)',
          }}>
            {aktivObj.phase} · Schritt {aktivObj.nr} von {SCHRITTE.length}
            {aktivObj.optional && (
              <span style={{ marginLeft: 8, color: 'var(--text-30)' }}>· Optional</span>
            )}
          </div>

          <div style={{
            fontFamily: 'var(--font-display)',
            fontSize: 28, fontWeight: 700,
            color: 'var(--kc-dark)',
            textTransform: 'uppercase', letterSpacing: '.01em',
            lineHeight: 1, marginBottom: 6,
          }}>
            {aktivObj.icon} {aktivObj.label}
          </div>

          <div style={{
            fontSize: 12, color: 'var(--text-60)',
            lineHeight: 1.6, marginBottom: 16,
            maxWidth: 500, fontFamily: 'var(--font-sans)',
          }}>
            {aktivObj.desc}
          </div>

          {aktivObj.auto ? (
            <div style={{
              background: 'var(--info-bg)',
              border: '0.5px solid rgba(0,142,170,.3)',
              borderRadius: 'var(--r-lg)',
              padding: '16px 20px',
              display: 'flex', alignItems: 'center', gap: 14,
              marginBottom: 16,
            }}>
              <div style={{
                width: 28, height: 28, borderRadius: '50%',
                border: '3px solid rgba(0,142,170,.2)',
                borderTopColor: 'var(--kc-mid)',
                animation: 'spin .8s linear infinite',
                flexShrink: 0,
              }} />
              <div>
                <div style={{
                  fontSize: 12, fontWeight: 900,
                  color: 'var(--kc-dark)',
                  textTransform: 'uppercase', letterSpacing: '.06em',
                  marginBottom: 3, fontFamily: 'var(--font-sans)',
                }}>Läuft automatisch</div>
                <div style={{ fontSize: 12, color: 'var(--text-60)', lineHeight: 1.6 }}>
                  {aktivObj.autoText}
                </div>
              </div>
            </div>
          ) : (
            <SchrittContent
              schritt={aktivObj}
              project={project}
              lead={lead}
              leadId={leadId}
              token={token}
              headers={headers}
              localBriefing={localBriefing}
              reloadBriefing={reloadBriefing}
              goWeiter={goWeiter}
              latestAudit={localLatestAudit}
              onAuditComplete={handleAuditComplete}
              onAnalyseUpdate={handleAnalyseUpdate}
              onSitemapReload={onSitemapReload}
              sitemapPages={sitemapPages}
              sitemapLoading={sitemapLoading}
              websiteContent={websiteContent}
              brandData={brandData}
              netlify={netlify}
              qaResult={qaResult}
              prozessDaten={prozessDaten}
              reloadConfirmedSteps={reloadConfirmedSteps}
            />
          )}

          {/* CTA-ROW */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 10,
            marginTop: 'auto', paddingTop: 16,
            borderTop: '0.5px solid var(--border)',
          }}>
            {aktivIdx > 0 && (
              <button
                onClick={goZurueck}
                style={{
                  background: 'transparent',
                  color: 'var(--text-30)',
                  border: '0.5px solid var(--border)',
                  borderRadius: 'var(--r-md)',
                  padding: '10px 14px',
                  fontSize: 11, fontWeight: 700,
                  cursor: 'pointer',
                  textTransform: 'uppercase', letterSpacing: '.06em',
                  fontFamily: 'var(--font-sans)',
                }}
              >← Zurück</button>
            )}

            {aktivObj.istFertig(prozessDaten) ? (
              aktivIdx < SCHRITTE.length - 1 && (
                <button
                  onClick={goWeiter}
                  style={{
                    background: 'var(--kc-dark)',
                    color: '#fff', border: 'none',
                    borderRadius: 'var(--r-md)',
                    padding: '11px 24px',
                    fontSize: 12, fontWeight: 900,
                    cursor: 'pointer',
                    textTransform: 'uppercase', letterSpacing: '.06em',
                    fontFamily: 'var(--font-sans)',
                    display: 'inline-flex', alignItems: 'center', gap: 7,
                  }}
                >Weiter →</button>
              )
            ) : !aktivObj.auto && (
              <button
                style={{
                  background: 'var(--kc-yellow)',
                  color: '#000', border: 'none',
                  borderRadius: 'var(--r-md)',
                  padding: '11px 24px',
                  fontSize: 12, fontWeight: 900,
                  cursor: 'pointer',
                  textTransform: 'uppercase', letterSpacing: '.06em',
                  fontFamily: 'var(--font-sans)',
                  display: 'inline-flex', alignItems: 'center', gap: 7,
                }}
              >{aktivObj.cta}</button>
            )}

            <div style={{
              marginLeft: 'auto',
              fontSize: 10, fontWeight: 900,
              color: 'var(--text-30)',
              textTransform: 'uppercase', letterSpacing: '.08em',
              fontFamily: 'var(--font-sans)',
            }}>
              Schritt {aktivObj.nr} / {SCHRITTE.length}
            </div>
          </div>
        </div>

        {/* NEXT PREVIEW */}
        {nextSchritte.length > 0 && (
          <div style={{
            padding: '10px 20px',
            borderTop: '0.5px solid var(--border)',
            background: '#fff', flexShrink: 0,
            display: 'flex', alignItems: 'center', gap: 12,
          }}>
            <div style={{
              fontSize: 9, fontWeight: 900,
              color: 'var(--text-30)',
              textTransform: 'uppercase', letterSpacing: '.1em',
              flexShrink: 0, fontFamily: 'var(--font-sans)',
            }}>Danach</div>
            {nextSchritte.map(s => (
              <div key={s.id} style={{
                display: 'flex', alignItems: 'center', gap: 5,
                padding: '4px 9px',
                background: 'var(--surface)',
                borderRadius: 'var(--r-sm)',
                fontSize: 10, color: 'var(--text-30)',
                fontWeight: 700, textTransform: 'uppercase',
                letterSpacing: '.04em', fontFamily: 'var(--font-sans)',
              }}>
                {s.icon} {s.label}
                {s.auto && (
                  <span style={{
                    padding: '1px 5px',
                    background: 'var(--info-bg)',
                    color: 'var(--kc-mid)',
                    borderRadius: 3, fontSize: 8, fontWeight: 700,
                  }}>🤖</span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes stepPulse {
          0%, 100% { box-shadow: 0 0 0 3px rgba(250,230,0,.3), 0 3px 12px rgba(250,230,0,.4); }
          50%       { box-shadow: 0 0 0 6px rgba(250,230,0,.15), 0 3px 16px rgba(250,230,0,.6); }
        }
      `}</style>
    </div>
  );
}

// ── Breadcrumb-Hilfskomponenten ───────────────────────────────────────────────

function BreadcrumbItem({ onClick, icon, label, dot }) {
  return (
    <div
      onClick={onClick}
      style={{
        display: 'flex', alignItems: 'center', gap: 5,
        fontSize: 10, fontWeight: 900,
        textTransform: 'uppercase', letterSpacing: '.08em',
        color: 'var(--text-30)', cursor: 'pointer',
        padding: '4px 6px', borderRadius: 'var(--r-sm)',
        transition: 'all .12s', userSelect: 'none',
        fontFamily: 'var(--font-sans)',
      }}
      onMouseEnter={e => { e.currentTarget.style.color = 'var(--kc-dark)'; e.currentTarget.style.background = 'var(--surface)'; }}
      onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-30)'; e.currentTarget.style.background = 'transparent'; }}
    >
      {icon}
      {dot && (
        <div style={{
          width: 6, height: 6, borderRadius: '50%',
          background: 'var(--kc-mid)', flexShrink: 0,
        }} />
      )}
      {label}
    </div>
  );
}

function BreadcrumbSep() {
  return (
    <span style={{
      color: 'var(--text-30)', fontSize: 12,
      fontWeight: 700, padding: '0 2px',
      userSelect: 'none',
    }}>
      ›
    </span>
  );
}

// ── Schritt-Content (delegiert an bestehende Embed-Komponenten) ───────────────

function SchrittContent({ schritt, ...props }) {
  const pad = { padding: '16px 0' };

  switch (schritt.component) {
    case 'BriefingUnternehmen':
      return props.lead
        ? <BriefingUnternehmenEmbed lead={props.lead} localBriefing={props.localBriefing} reloadBriefing={props.reloadBriefing} />
        : <Spinner />;
    case 'ZieleZielgruppe':
      return (
        <ZieleZielgruppe
          leadId={props.leadId}
          token={props.token}
          briefing={props.localBriefing}
          onSaved={() => { if (props.reloadBriefing) props.reloadBriefing(); if (props.goWeiter) props.goWeiter(); }}
        />
      );
    case 'AssetsKlaeren':
      return (
        <AssetsKlaeren
          leadId={props.leadId}
          token={props.token}
          onSaved={() => { if (props.reloadBriefing) props.reloadBriefing(); if (props.goWeiter) props.goWeiter(); }}
        />
      );
    case 'Funktionen':
      return (
        <Funktionen
          leadId={props.leadId}
          token={props.token}
          onSaved={() => { if (props.reloadBriefing) props.reloadBriefing(); if (props.goWeiter) props.goWeiter(); }}
        />
      );
    case 'SeoZiele':
      return (
        <SeoZiele
          leadId={props.leadId}
          token={props.token}
          projectId={props.project?.id}
          onSaved={() => { if (props.reloadBriefing) props.reloadBriefing(); }}
          onStepConfirmed={() => { if (props.reloadConfirmedSteps) props.reloadConfirmedSteps(); if (props.goWeiter) props.goWeiter(); }}
        />
      );
    case 'BriefingWebsite':
      return props.lead
        ? <div style={pad}><BriefingTab lead={props.lead} token={props.token} /></div>
        : <Spinner />;
    case 'AnalyseZentrale':
      return (
        <AnalyseCentrale
          projectId={props.project?.id}
          leadId={props.leadId}
          websiteUrl={props.lead?.website_url || props.project?.website_url}
          token={props.token}
          onDataUpdate={props.onAnalyseUpdate}
        />
      );
    case 'Audit':
      return <AuditEmbed project={props.project} lead={props.lead} headers={props.headers} latestAudit={props.latestAudit} onAuditComplete={props.onAuditComplete} />;
    case 'Sitemap':
      return (
        <div>
          {(props.sitemapPages?.length === 0) && (
            <SitemapKiVorschlag project={props.project} leadId={props.leadId} headers={props.headers} onGenerated={props.onSitemapReload} hasExistingPages={false} existingCount={0} />
          )}
          {props.sitemapLoading ? <Spinner /> : (
            <SitemapEditorEmbed pages={props.sitemapPages} leadId={props.leadId} headers={props.headers} onReload={props.onSitemapReload} />
          )}
          <div style={{ padding: '0 24px 20px' }}>
            <SitemapVorschlaege leadId={props.leadId} token={props.token} onAdded={props.onSitemapReload} />
          </div>
        </div>
      );
    case 'BrandDesign':
      return (
        <BrandDesignEditor
          leadId={props.leadId}
          token={props.token}
          brandData={props.brandData}
          onSaved={(data) => { if (props.onAnalyseUpdate) props.onAnalyseUpdate({ brandPrimaryColor: data?.primary, brandData: data }); }}
        />
      );
    case 'BrandGuideline':
      return (
        <BrandGuideline project={props.project} lead={props.lead} token={props.token}
          leadId={props.leadId} brandData={props.brandData}
          projectId={props.project?.id}
          onStepConfirmed={() => { if (props.reloadConfirmedSteps) props.reloadConfirmedSteps(); if (props.goWeiter) props.goWeiter(); }} />
      );
    case 'SeoAnalyse':
      return <SeoAnalyseStep projectId={props.project?.id} token={props.token} />;
    case 'ContentWerkstatt':
      return (
        <ContentWerkstatt project={props.project} sitemapPages={props.sitemapPages} sitemapLoading={props.sitemapLoading} token={props.token} leadId={props.leadId} websiteContent={props.websiteContent} />
      );
    case 'Seiteninhalte':
      return (
        <ContentWerkstatt project={props.project} sitemapPages={props.sitemapPages} sitemapLoading={props.sitemapLoading}
          token={props.token} leadId={props.leadId} websiteContent={props.websiteContent}
          defaultTab="inhalte" hideTabs />
      );
    case 'BilderAssets':
      return (
        <ContentWerkstatt project={props.project} sitemapPages={props.sitemapPages} sitemapLoading={props.sitemapLoading}
          token={props.token} leadId={props.leadId} websiteContent={props.websiteContent}
          defaultTab="assets" hideTabs />
      );
    case 'Freigaben':
      return (
        <ContentWerkstatt project={props.project} sitemapPages={props.sitemapPages} sitemapLoading={props.sitemapLoading}
          token={props.token} leadId={props.leadId} websiteContent={props.websiteContent}
          defaultTab="freigaben" hideTabs />
      );
    case 'DesignStudio':
      return <DesignStudioEmbed project={props.project} leadId={props.leadId} token={props.token} headers={props.headers} brandData={props.brandData} sitemapPages={props.sitemapPages} />;
    case 'Editor':
      return <DesignStudio project={props.project} leadId={props.leadId} token={props.token} brandData={props.brandData} sitemapPages={props.sitemapPages} />;
    case 'Netlify':
      return <NetlifyEmbed project={props.project} headers={props.headers} netlify={props.netlify} />;
    case 'DNS':
      return <DNSEmbed project={props.project} lead={props.lead} headers={props.headers} />;
    case 'QA':
      return <QAEmbed project={props.project} headers={props.headers} qaResult={props.qaResult} />;
    case 'Abnahme':
      return <AbnahmeEmbed project={props.project} headers={props.headers} />;
    case 'Zugangsdaten':
      return <ZugangsdatenEmbed project={props.project} headers={props.headers} />;
    default:
      return <div style={{ padding: '16px 0', fontSize: 13, color: 'var(--text-60)' }}>Wird vorbereitet …</div>;
  }
}

function Spinner() {
  return (
    <div style={{ padding: 28, display: 'flex', justifyContent: 'center' }}>
      <div style={{
        width: 24, height: 24, borderRadius: '50%',
        border: '3px solid var(--border)',
        borderTopColor: 'var(--kc-mid)',
        animation: 'spin .8s linear infinite',
      }} />
    </div>
  );
}
