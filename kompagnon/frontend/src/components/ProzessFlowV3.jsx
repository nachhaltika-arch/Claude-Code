import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import API_BASE_URL from '../config';
import AnalyseCentrale from './AnalyseCentrale';
import ContentWerkstatt from './ContentWerkstatt';
import DesignStudio from './DesignStudio';
import BriefingTab from './BriefingTab';
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
  Spinner,
} from './ProzessFlow';

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
    id: 'audit', nr: 2, phase: 'Analyse',
    icon: '🔍', label: 'Website-Audit', auto: true,
    autoText: 'Bestehende Website wird analysiert — Score, Probleme und Bericht in ~30 Sekunden.',
    desc: 'Technische Analyse der alten Website.',
    component: 'Audit',
    istFertig: (d) => !!(d.latestAudit?.total_score > 0),
    fertigText: (d) => `Score: ${d.latestAudit?.total_score}/100`,
  },
  {
    id: 'analyse-zentrale', nr: 3, phase: 'Analyse',
    icon: '🔬', label: 'Vollanalyse', auto: false,
    cta: 'Vollanalyse starten →',
    desc: 'Crawler, Brand-Farben und PageSpeed werden gleichzeitig gemessen.',
    component: 'AnalyseZentrale',
    istFertig: (d) => !!(d.analyseZentraleConfirmed) || ((d.crawlPages || 0) >= 3 && !!(d.brandPrimaryColor)),
    fertigText: (d) => d.analyseZentraleConfirmed ? 'Analyse abgeschlossen' : `${d.crawlPages} Seiten · Brand erkannt`,
  },
  {
    id: 'briefing-website', nr: 4, phase: 'Analyse',
    icon: '📋', label: 'Briefing: Website', auto: false,
    cta: 'Website-Briefing ausfüllen →',
    desc: 'Ziele, gewünschte Seiten und Design-Wünsche dokumentieren.',
    component: 'BriefingWebsite',
    istFertig: (d) => !!((d.briefing?.hauptziel && d.briefing?.aktionen) || d.briefing?.seiten),
    fertigText: () => 'Ausgefüllt',
  },
  {
    id: 'zugangsdaten', nr: 5, phase: 'Analyse',
    icon: '🔑', label: 'Zugangsdaten', auto: false, optional: true,
    cta: 'Zugangsdaten speichern →',
    desc: 'Hosting, FTP und CMS-Zugänge sicher speichern.',
    component: 'Zugangsdaten',
    istFertig: (d) => (d.credsCount || 0) >= 1,
    fertigText: (d) => `${d.credsCount} Einträge`,
  },
  {
    id: 'sitemap', nr: 6, phase: 'Content',
    icon: '🗺️', label: 'Sitemap', auto: false,
    cta: 'KI-Sitemap generieren →',
    desc: 'KI legt alle Seiten aus dem Briefing an — 1 Klick.',
    component: 'Sitemap',
    istFertig: (d) => (d.sitemapCount || 0) >= 3,
    fertigText: (d) => `${d.sitemapCount} Seiten`,
  },
  {
    id: 'content-generieren', nr: 7, phase: 'Content',
    icon: '✍️', label: 'Texte generieren', auto: false,
    cta: 'Alle Texte generieren →',
    desc: 'KI schreibt alle Seiten auf einmal — ca. 60 Sekunden.',
    component: 'ContentWerkstatt',
    istFertig: (d) => (d.sitemapCount || 0) > 0 && (d.contentCount || 0) >= (d.sitemapCount || 1),
    fertigText: (d) => `${d.contentCount}/${d.sitemapCount} Seiten`,
  },
  {
    id: 'design-generieren', nr: 8, phase: 'Design',
    icon: '🎨', label: 'Design wählen', auto: false,
    cta: 'Design generieren →',
    desc: 'KI erstellt 3 Entwürfe — du wählst den besten.',
    component: 'DesignStudio',
    istFertig: (d) => (d.designVersions || 0) >= 1,
    fertigText: (d) => `${d.designVersions} Version(en)`,
  },
  {
    id: 'editor', nr: 9, phase: 'Design',
    icon: '🖊️', label: 'Feinschliff', auto: false, optional: true,
    cta: 'Editor öffnen →',
    desc: 'Echte Fotos einsetzen, Texte prüfen, Mobile-Ansicht testen.',
    component: 'Editor',
    istFertig: (d) => !!(d.editorSaved),
    fertigText: () => 'Gespeichert',
  },
  {
    id: 'netlify', nr: 10, phase: 'Go Live',
    icon: '🚀', label: 'Veröffentlichen', auto: false,
    cta: 'Jetzt veröffentlichen →',
    desc: 'Website live schalten — 1 Klick, Netlify deployt automatisch.',
    component: 'Netlify',
    istFertig: (d) => !!(d.netlifyUrl && d.netlifyReady),
    fertigText: (d) => d.netlifyUrl || 'Deployed',
  },
  {
    id: 'dns', nr: 11, phase: 'Go Live',
    icon: '🌍', label: 'Domain verbinden', auto: true,
    autoText: 'DNS-Anleitung wird automatisch per E-Mail an den Kunden gesendet — du musst nichts tun.',
    desc: 'Anleitung geht direkt an den Kunden.',
    component: 'DNS',
    istFertig: (d) => !!(d.domainReachable && d.domainStatusCode === 200),
    fertigText: () => 'Domain erreichbar',
  },
  {
    id: 'qa', nr: 12, phase: 'Go Live',
    icon: '✅', label: 'QA-Check', auto: true,
    autoText: 'Website wird automatisch auf Fehler, Mobile-Darstellung und Impressum geprüft.',
    desc: 'Links, Mobile, Impressum — automatisch.',
    component: 'QA',
    istFertig: (d) => !!(d.qaResult),
    fertigText: () => 'QA abgeschlossen',
  },
  {
    id: 'abnahme', nr: 13, phase: 'Go Live',
    icon: '🏁', label: 'Go Live!', auto: false,
    cta: 'Abnahme erteilen →',
    desc: 'Finale Kundenfreigabe und Go-Live.',
    component: 'Abnahme',
    istFertig: (d) => !!(d.goLiveConfirmed || d.projectStatus === 'fertig'),
    fertigText: () => '🎉 Live!',
  },
];

export default function ProzessFlowV3({
  project, lead, token, briefing, latestAudit, onAuditUpdate,
  onSitemapReload, onBrandUpdate, onCrawlUpdate,
  crawlPages, sitemapPages, sitemapLoading,
  websiteContent, brandData, netlify, qaResult,
  onProjectRefresh,
}) {
  const navigate    = useNavigate();
  const headers     = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };
  const leadId      = project?.lead_id || lead?.id;
  const companyName = lead?.display_name || lead?.company_name || project?.company_name || 'Projekt';

  const [localBriefing,    setLocalBriefing]    = useState(briefing);
  const [localLatestAudit, setLocalLatestAudit] = useState(latestAudit);
  const [localCrawlPages,  setLocalCrawlPages]  = useState(crawlPages);
  const [localBrandColor,  setLocalBrandColor]  = useState(brandData?.primary_color || null);
  const [localBrandData,   setLocalBrandData]   = useState(brandData);
  const [confirmedSteps,   setConfirmedSteps]   = useState(() => {
    try { return JSON.parse(project?.steps_confirmed || '{}'); } catch { return {}; }
  });

  useEffect(() => { setLocalBriefing(briefing); }, [briefing]); // eslint-disable-line
  useEffect(() => { setLocalLatestAudit(latestAudit); }, [latestAudit]); // eslint-disable-line
  useEffect(() => { setLocalCrawlPages(crawlPages); }, [crawlPages]); // eslint-disable-line
  useEffect(() => { if (brandData?.primary_color) setLocalBrandColor(brandData.primary_color); }, [brandData]); // eslint-disable-line
  useEffect(() => { setLocalBrandData(brandData); }, [brandData]); // eslint-disable-line

  useEffect(() => {
    if (!project?.id || !token) return;
    fetch(`${API_BASE_URL}/api/projects/${project.id}/confirmed-steps`, {
      headers: { Authorization: `Bearer ${token}` },
    }).then(r => r.ok ? r.json() : {}).then(data => setConfirmedSteps(data || {})).catch(() => {});
  }, [project?.id]); // eslint-disable-line

  const handleStepConfirmed = useCallback((stepId) => {
    setConfirmedSteps(prev => ({
      ...prev,
      [stepId]: { confirmed: true, confirmed_at: new Date().toISOString() },
    }));
  }, []);

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

  const prozessDaten = {
    briefing:          localBriefing,
    latestAudit:       localLatestAudit,
    crawlPages:        localCrawlPages || 0,
    brandPrimaryColor: localBrandData?.primary_color || localBrandColor || null,
    analyseZentraleConfirmed: !!(confirmedSteps['analyse-zentrale']?.confirmed),
    brandGuidelineDone: !!(localBrandData?.guideline_generated || localBrandData?.design_tokens) || !!(confirmedSteps['brand-guideline']?.confirmed),
    seoBestaetigt: !!(confirmedSteps['seo-ziele']?.confirmed) || (() => {
      try {
        const raw = localBriefing?.seo_json;
        if (!raw) return false;
        const p = typeof raw === 'string' ? JSON.parse(raw) : raw;
        return !!(p?.bestaetigt && p?.keywords?.length > 0);
      } catch { return false; }
    })(),
    sitemapCount:      sitemapPages?.length || 0,
    contentCount:      (websiteContent || []).filter(p => p.ki_content || p.content_generated).length,
    credsCount:        0,
    designVersions:    0,
    editorSaved:       !!(project?.editor_saved || (sitemapPages || []).some(p => p.gjs_html?.trim())),
    netlifyUrl:        netlify?.netlify_site_url || netlify?.url || project?.netlify_site_url || null,
    netlifyReady:      !!(netlify?.state === 'ready' || netlify?.connected === true || project?.netlify_last_deploy),
    domainReachable:   project?.domain_reachable || false,
    domainStatusCode:  project?.domain_status_code || null,
    qaResult,
    projectStatus:     project?.status || '',
    goLiveConfirmed:   !!(project?.abnahme_datum),
  };

  const aktiverIdx = SCHRITTE.findIndex(s => !s.istFertig(prozessDaten));
  const aktiverId  = aktiverIdx >= 0 ? SCHRITTE[aktiverIdx].id : SCHRITTE[SCHRITTE.length - 1].id;
  const [offenerSchritt, setOffenerSchritt] = useState(aktiverId);

  useEffect(() => { setOffenerSchritt(prev => prev ?? aktiverId); }, [aktiverId]); // eslint-disable-line

  const fertigCount  = SCHRITTE.filter(s => s.istFertig(prozessDaten)).length;
  const gesamtPct    = Math.round((fertigCount / SCHRITTE.length) * 100);
  const aktivObj     = SCHRITTE.find(s => s.id === offenerSchritt) || SCHRITTE[0];
  const aktivIdx     = SCHRITTE.findIndex(s => s.id === offenerSchritt);
  const doneSchritte = SCHRITTE.slice(0, aktivIdx).filter(s => s.istFertig(prozessDaten));
  const nextSchritte = SCHRITTE.slice(aktivIdx + 1, aktivIdx + 3);

  const goWeiter  = () => { if (aktivIdx < SCHRITTE.length - 1) setOffenerSchritt(SCHRITTE[aktivIdx + 1].id); };
  const goZurueck = () => { if (aktivIdx > 0) setOffenerSchritt(SCHRITTE[aktivIdx - 1].id); };

  return (
    <div style={{
      display: 'grid', gridTemplateColumns: '64px 1fr',
      height: '100vh', background: 'var(--bg-app)',
      overflow: 'hidden', fontFamily: 'var(--font-sans)',
    }}>
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes stepPulse {
          0%,100% { box-shadow: 0 0 0 3px rgba(250,230,0,.3); }
          50%      { box-shadow: 0 0 0 6px rgba(250,230,0,.15); }
        }
      `}</style>

      {/* ── TIMELINE (64px links) ─────────────────────────────────────────── */}
      <div style={{
        background: 'linear-gradient(180deg,#004F59 0%,#003840 100%)',
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        padding: '14px 0', overflowY: 'auto', overflowX: 'hidden',
      }}>
        {/* Logo */}
        <svg width="32" height="32" viewBox="0 0 107.7 107.7" fill="none" style={{ marginBottom: 16, flexShrink: 0 }}>
          <path d="M53.85 0C24.1 0 0 24.1 0 53.85s24.1 53.85 53.85 53.85 53.85-24.1 53.85-53.85S83.6 0 53.85 0zm0 96.9c-23.75 0-43.05-19.3-43.05-43.05S30.1 10.8 53.85 10.8s43.05 19.3 43.05 43.05S77.6 96.9 53.85 96.9z" fill="#008EAA"/>
          <path d="M53.85 21.6c-17.8 0-32.25 14.45-32.25 32.25S36.05 86.1 53.85 86.1 86.1 71.65 86.1 53.85 71.65 21.6 53.85 21.6zm0 53.7c-11.85 0-21.45-9.6-21.45-21.45S42 32.4 53.85 32.4s21.45 9.6 21.45 21.45S65.7 75.3 53.85 75.3z" fill="#008EAA"/>
        </svg>

        {/* Punkte */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 5, position: 'relative', padding: '4px 0', width: '100%' }}>
          <div style={{ position: 'absolute', left: '50%', transform: 'translateX(-50%)', top: 0, bottom: 0, width: 1, background: 'rgba(255,255,255,.08)' }} />
          {SCHRITTE.map((s) => {
            const fertig = s.istFertig(prozessDaten);
            const aktiv  = s.id === offenerSchritt;
            const size   = aktiv ? 14 : fertig ? 11 : 9;
            const bg     = fertig
              ? '#00875A'
              : aktiv
                ? '#FAE600'
                : SCHRITTE[aktivIdx + 1]?.id === s.id
                  ? 'rgba(255,255,255,.25)'
                  : 'rgba(255,255,255,.09)';
            return (
              <div
                key={s.id}
                onClick={() => setOffenerSchritt(s.id)}
                title={`${s.nr}. ${s.label}`}
                style={{
                  position: 'relative', zIndex: 1,
                  width: size, height: size, borderRadius: '50%',
                  background: bg,
                  border: aktiv ? '2px solid rgba(255,255,255,.6)' : 'none',
                  cursor: 'pointer', transition: 'all .2s', flexShrink: 0,
                  animation: aktiv ? 'stepPulse 2s ease-in-out infinite' : 'none',
                }}
              />
            );
          })}
        </div>

        {/* Fortschritt % */}
        <div style={{ marginTop: 12, fontSize: 9, fontWeight: 900, color: 'rgba(255,255,255,.3)', textTransform: 'uppercase', letterSpacing: '.06em' }}>
          {gesamtPct}%
        </div>
      </div>

      {/* ── CONTENT (rechts) ──────────────────────────────────────────────── */}
      <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

        {/* Breadcrumb */}
        <div style={{ background: 'var(--bg-surface)', borderBottom: '1px solid var(--border-light)', padding: '0 20px', height: 40, display: 'flex', alignItems: 'center', gap: 0, flexShrink: 0 }}>
          <BreadcrumbItem onClick={() => navigate('/app/dashboard')} label="Dashboard" icon={
            <svg width="11" height="11" viewBox="0 0 12 12" fill="currentColor" style={{ flexShrink: 0, opacity: .6 }}>
              <path d="M1 5.5L6 1.5L11 5.5V10.5H8V7.5H4V10.5H1V5.5Z"/>
            </svg>
          } />
          <BreadcrumbSep />
          <BreadcrumbItem onClick={() => navigate('/app/projects')} label="Projekte" />
          <BreadcrumbSep />
          <BreadcrumbItem
            onClick={() => leadId && navigate(`/app/leads/${leadId}`)}
            dot label={companyName}
          />
          <BreadcrumbSep />
          <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', padding: '4px 6px' }}>
            Schritt {aktivObj.nr} · {aktivObj.label}
          </span>
        </div>

        {/* Projekt-Bar */}
        <div style={{ background: 'var(--bg-surface)', borderBottom: '1px solid var(--border-light)', padding: '0 20px', height: 44, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0 }}>
          <div>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '.02em' }}>{companyName}</div>
            <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em' }}>
              {lead?.city || ''}{lead?.trade ? ` · ${lead.trade}` : ''}
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 100, height: 5, background: 'var(--border-light)', borderRadius: 3, overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${gesamtPct}%`, background: 'var(--brand-primary)', borderRadius: 3, transition: 'width .5s' }} />
            </div>
            <span style={{ fontSize: 10, fontWeight: 900, color: 'var(--text-tertiary)', whiteSpace: 'nowrap' }}>{fertigCount} / {SCHRITTE.length}</span>
          </div>
        </div>

        {/* Erledigte Schritte (kompakt) */}
        {doneSchritte.length > 0 && (
          <div style={{ padding: '8px 20px 0', flexShrink: 0 }}>
            {doneSchritte.slice(-3).map(s => (
              <div key={s.id} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 10, color: 'var(--text-tertiary)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.04em', padding: '2px 0' }}>
                <div style={{ width: 14, height: 14, borderRadius: '50%', background: '#00875A', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 7, color: '#fff', flexShrink: 0 }}>✓</div>
                {s.phase} · {s.label}
              </div>
            ))}
            {doneSchritte.length > 3 && (
              <div style={{ fontSize: 10, color: 'var(--text-tertiary)', paddingLeft: 20, fontWeight: 700 }}>+ {doneSchritte.length - 3} weitere erledigt</div>
            )}
          </div>
        )}

        {/* Aktiver Schritt */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '20px', overflowY: 'auto' }}>

          {/* Phase + Nr */}
          <div style={{ fontSize: 10, fontWeight: 900, textTransform: 'uppercase', letterSpacing: '.12em', color: 'var(--text-tertiary)', marginBottom: 6 }}>
            {aktivObj.phase} · Schritt {aktivObj.nr} von {SCHRITTE.length}
            {aktivObj.optional && <span style={{ marginLeft: 8 }}>· Optional</span>}
          </div>

          {/* Titel */}
          <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '.01em', lineHeight: 1, marginBottom: 8 }}>
            {aktivObj.icon} {aktivObj.label}
          </div>

          {/* Beschreibung */}
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: 16, maxWidth: 500 }}>
            {aktivObj.desc}
          </div>

          {/* Auto oder Manuell */}
          {aktivObj.auto && !aktivObj.istFertig(prozessDaten) ? (
            <div style={{ background: 'var(--info-bg, #EFF6FF)', border: '1px solid rgba(0,142,170,.25)', borderRadius: 10, padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 14, marginBottom: 16 }}>
              <div style={{ width: 28, height: 28, borderRadius: '50%', border: '3px solid rgba(0,142,170,.2)', borderTopColor: 'var(--brand-primary)', animation: 'spin .8s linear infinite', flexShrink: 0 }} />
              <div>
                <div style={{ fontSize: 12, fontWeight: 900, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 3 }}>Läuft automatisch</div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6 }}>{aktivObj.autoText}</div>
              </div>
            </div>
          ) : (
            <SchrittContent
              schritt={aktivObj}
              project={project} lead={lead} leadId={leadId}
              token={token} headers={headers}
              localBriefing={localBriefing} reloadBriefing={reloadBriefing}
              latestAudit={localLatestAudit} onAuditComplete={handleAuditComplete}
              onAnalyseUpdate={handleAnalyseUpdate} onSitemapReload={onSitemapReload}
              sitemapPages={sitemapPages} sitemapLoading={sitemapLoading}
              websiteContent={websiteContent} brandData={localBrandData}
              netlify={netlify} qaResult={qaResult}
              onProjectRefresh={onProjectRefresh}
              confirmedSteps={confirmedSteps}
              onStepConfirmed={handleStepConfirmed}
            />
          )}

          {/* CTA-Row */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 'auto', paddingTop: 16, borderTop: '1px solid var(--border-light)' }}>
            {aktivIdx > 0 && (
              <button onClick={goZurueck} style={{ background: 'transparent', color: 'var(--text-secondary)', border: '1px solid var(--border-light)', borderRadius: 8, padding: '10px 14px', fontSize: 11, fontWeight: 700, cursor: 'pointer', textTransform: 'uppercase', letterSpacing: '.06em', fontFamily: 'var(--font-sans)' }}>
                ← Zurück
              </button>
            )}
            {aktivObj.istFertig(prozessDaten) ? (
              aktivIdx < SCHRITTE.length - 1 && (
                <button onClick={goWeiter} style={{ flex: 1, background: 'var(--brand-primary)', color: '#fff', border: 'none', borderRadius: 8, padding: '11px 24px', fontSize: 12, fontWeight: 900, cursor: 'pointer', textTransform: 'uppercase', letterSpacing: '.06em', fontFamily: 'var(--font-sans)' }}>
                  Weiter →
                </button>
              )
            ) : confirmedSteps[aktivObj.id]?.confirmed ? (
              aktivIdx < SCHRITTE.length - 1 && (
                <button onClick={goWeiter} style={{ flex: 1, background: '#1D9E75', color: '#fff', border: 'none', borderRadius: 8, padding: '11px 24px', fontSize: 12, fontWeight: 900, cursor: 'pointer', textTransform: 'uppercase', letterSpacing: '.06em', fontFamily: 'var(--font-sans)' }}>
                  ✓ Abgeschlossen — Weiter →
                </button>
              )
            ) : !aktivObj.auto && aktivObj.cta && (
              <button style={{ flex: 1, background: '#FAE600', color: '#000', border: 'none', borderRadius: 8, padding: '11px 24px', fontSize: 12, fontWeight: 900, cursor: 'default', textTransform: 'uppercase', letterSpacing: '.06em', fontFamily: 'var(--font-sans)' }}>
                {aktivObj.cta}
              </button>
            )}
            <div style={{ marginLeft: 'auto', fontSize: 10, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em' }}>
              Schritt {aktivObj.nr} / {SCHRITTE.length}
            </div>
          </div>
        </div>

        {/* Next Preview */}
        {nextSchritte.length > 0 && (
          <div style={{ padding: '10px 20px', borderTop: '1px solid var(--border-light)', background: 'var(--bg-surface)', flexShrink: 0, display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ fontSize: 9, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.1em', flexShrink: 0 }}>Danach</div>
            {nextSchritte.map(s => (
              <div key={s.id} style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '4px 9px', background: 'var(--bg-elevated)', borderRadius: 6, fontSize: 10, color: 'var(--text-secondary)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.04em' }}>
                {s.icon} {s.label}
                {s.auto && <span style={{ padding: '1px 4px', background: '#EFF6FF', color: 'var(--brand-primary)', borderRadius: 3, fontSize: 8 }}>🤖</span>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function BreadcrumbItem({ onClick, icon, label, dot }) {
  const [hover, setHover] = useState(false);
  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        display: 'flex', alignItems: 'center', gap: 5,
        fontSize: 10, fontWeight: 900, textTransform: 'uppercase', letterSpacing: '.08em',
        color: hover ? 'var(--text-primary)' : 'var(--text-tertiary)',
        cursor: 'pointer', padding: '4px 6px', borderRadius: 4,
        background: hover ? 'var(--bg-elevated)' : 'transparent',
        transition: 'all .12s', userSelect: 'none', fontFamily: 'var(--font-sans)',
      }}
    >
      {icon}
      {dot && <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--brand-primary)', flexShrink: 0 }} />}
      {label}
    </div>
  );
}

function BreadcrumbSep() {
  return <span style={{ color: 'var(--text-tertiary)', fontSize: 12, fontWeight: 700, padding: '0 1px', userSelect: 'none' }}>›</span>;
}

function SchrittContent({
  schritt, project, lead, leadId, token, headers,
  localBriefing, reloadBriefing, latestAudit, onAuditComplete,
  onAnalyseUpdate, onSitemapReload, sitemapPages, sitemapLoading,
  websiteContent, brandData, netlify, qaResult, onProjectRefresh,
  confirmedSteps, onStepConfirmed,
}) {
  const pad = { padding: '16px 0' };

  switch (schritt.component) {
    case 'BriefingUnternehmen':
      return lead
        ? <BriefingUnternehmenEmbed lead={lead} localBriefing={localBriefing} reloadBriefing={reloadBriefing} />
        : <Spinner />;

    case 'BriefingWebsite':
      return lead
        ? <div style={pad}><BriefingTab lead={lead} token={token} /></div>
        : <Spinner />;

    case 'AnalyseZentrale':
      return (
        <AnalyseCentrale
          projectId={project?.id} leadId={leadId}
          websiteUrl={lead?.website_url || project?.website_url}
          token={token} onDataUpdate={onAnalyseUpdate}
          stepId="analyse-zentrale"
          confirmedSteps={confirmedSteps}
          onStepConfirmed={onStepConfirmed}
        />
      );

    case 'Audit':
      return <AuditEmbed project={project} lead={lead} headers={headers} latestAudit={latestAudit} onAuditComplete={onAuditComplete} />;

    case 'Zugangsdaten':
      return <ZugangsdatenEmbed project={project} headers={headers} />;

    case 'Sitemap':
      return (
        <div>
          <SitemapKiVorschlag
            project={project} leadId={leadId} headers={headers}
            onGenerated={onSitemapReload}
            hasExistingPages={sitemapPages.length > 0}
            existingCount={sitemapPages.filter(p => !p.ist_pflichtseite).length}
          />
          {sitemapLoading ? <Spinner /> : (
            <SitemapEditorEmbed pages={sitemapPages} leadId={leadId} headers={headers} onReload={onSitemapReload} />
          )}
        </div>
      );

    case 'ContentWerkstatt':
      return (
        <ContentWerkstatt
          project={project} sitemapPages={sitemapPages} sitemapLoading={sitemapLoading}
          token={token} leadId={leadId} websiteContent={websiteContent}
          onProjectRefresh={onProjectRefresh}
        />
      );

    case 'DesignStudio':
      return <DesignStudioEmbed project={project} leadId={leadId} token={token} headers={headers} brandData={brandData} sitemapPages={sitemapPages} />;

    case 'Editor':
      return <DesignStudio project={project} leadId={leadId} token={token} brandData={brandData} sitemapPages={sitemapPages} />;

    case 'Netlify':
      return <NetlifyEmbed project={project} headers={headers} />;

    case 'DNS':
      return <DNSEmbed project={project} lead={lead} headers={headers} />;

    case 'QA':
      return <QAEmbed project={project} headers={headers} qaResult={qaResult} />;

    case 'Abnahme':
      return <AbnahmeEmbed project={project} lead={lead} headers={headers} netlify={netlify} />;

    default:
      return <div style={{ padding: '16px 0', fontSize: 13, color: 'var(--text-secondary)' }}>Wird vorbereitet …</div>;
  }
}
