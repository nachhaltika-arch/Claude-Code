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
    id: 'briefing-unternehmen', nr: 1, icon: '🏢',
    label: 'Briefing: Betrieb',
    desc: 'Gewerk, Leistungen und USP eintragen',
    auto: false,
    component: 'BriefingUnternehmen',
    istFertig: (d) => !!(d.briefing?.gewerk && d.briefing?.leistungen?.trim()),
    fertigText: (d) => d.briefing?.gewerk || 'Ausgefüllt',
  },
  {
    id: 'audit', nr: 2, icon: '🔍',
    label: 'Website analysieren',
    desc: 'Technische Analyse der bestehenden Website',
    auto: true,
    component: 'Audit',
    istFertig: (d) => !!(d.latestAudit?.total_score > 0),
    fertigText: (d) => `Score: ${d.latestAudit?.total_score}/100`,
  },
  {
    id: 'analyse-zentrale', nr: 3, icon: '🔬',
    label: 'Vollanalyse starten',
    desc: 'Crawler, Brand-Farben, PageSpeed — alles auf einmal',
    auto: false,
    component: 'AnalyseZentrale',
    istFertig: (d) => (d.crawlPages || 0) >= 3 && !!(d.brandPrimaryColor),
    fertigText: (d) => `${d.crawlPages} Seiten · Brand erkannt`,
  },
  {
    id: 'briefing-website', nr: 4, icon: '📋',
    label: 'Briefing: Website',
    desc: 'Ziele, gewünschte Seiten, Design-Wünsche',
    auto: false,
    component: 'BriefingWebsite',
    istFertig: (d) => !!((d.briefing?.hauptziel && d.briefing?.aktionen) || d.briefing?.seiten),
    fertigText: () => 'Ausgefüllt',
  },
  {
    id: 'zugangsdaten', nr: 5, icon: '🔑',
    label: 'Zugangsdaten',
    desc: 'Hosting, FTP, CMS-Zugänge',
    auto: false,
    optional: true,
    component: 'Zugangsdaten',
    istFertig: (d) => (d.credsCount || 0) >= 1,
    fertigText: (d) => `${d.credsCount} Einträge`,
  },
  {
    id: 'sitemap', nr: 6, icon: '🗺️',
    label: 'Sitemap generieren',
    desc: 'KI legt alle Seiten aus dem Briefing an — 1 Klick',
    auto: false,
    component: 'Sitemap',
    istFertig: (d) => (d.sitemapCount || 0) >= 3,
    fertigText: (d) => `${d.sitemapCount} Seiten`,
  },
  {
    id: 'content-generieren', nr: 7, icon: '🤖',
    label: 'Alle Texte generieren',
    desc: 'KI schreibt alle Seiten auf einmal — ~60 Sekunden',
    auto: false,
    component: 'ContentWerkstatt',
    istFertig: (d) => (d.sitemapCount || 0) > 0 && (d.contentCount || 0) >= (d.sitemapCount || 1),
    fertigText: (d) => `${d.contentCount}/${d.sitemapCount} Seiten befüllt`,
  },
  {
    id: 'design-generieren', nr: 8, icon: '🎨',
    label: 'Design auswählen',
    desc: 'Aus KI-Entwürfen eine Variante wählen',
    auto: false,
    component: 'DesignStudio',
    istFertig: (d) => (d.designVersions || 0) >= 1,
    fertigText: (d) => `${d.designVersions} Version(en)`,
  },
  {
    id: 'editor', nr: 9, icon: '🖊️',
    label: 'Feinschliff im Editor',
    desc: 'Fotos einsetzen, Texte prüfen, Mobile testen',
    auto: false,
    optional: true,
    component: 'Editor',
    istFertig: (d) => !!(d.editorSaved),
    fertigText: () => 'Gespeichert',
  },
  {
    id: 'netlify', nr: 10, icon: '🚀',
    label: 'Website veröffentlichen',
    desc: 'Ein Klick — live auf Netlify',
    auto: false,
    component: 'Netlify',
    istFertig: (d) => !!(d.netlifyUrl && d.netlifyReady),
    fertigText: (d) => d.netlifyUrl || 'Deployed',
  },
  {
    id: 'dns', nr: 11, icon: '🌍',
    label: 'Domain verbinden',
    desc: 'Anleitung geht automatisch an den Kunden',
    auto: true,
    component: 'DNS',
    istFertig: (d) => !!(d.domainReachable && d.domainStatusCode === 200),
    fertigText: () => 'Domain erreichbar',
  },
  {
    id: 'qa', nr: 12, icon: '✓',
    label: 'QA-Check',
    desc: 'Links, Mobile, Impressum — automatisch geprüft',
    auto: true,
    component: 'QA',
    istFertig: (d) => !!(d.qaResult),
    fertigText: () => 'QA abgeschlossen',
  },
  {
    id: 'abnahme', nr: 13, icon: '🏁',
    label: 'Fertig!',
    desc: 'Kundenfreigabe und Go-Live',
    auto: false,
    component: 'Abnahme',
    istFertig: (d) => !!(d.goLiveConfirmed || d.projectStatus === 'fertig'),
    fertigText: () => '🎉 Live!',
  },
];

export default function ProzessFlowV2({
  project, lead, token, briefing, latestAudit, onAuditUpdate,
  onSitemapReload, onBrandUpdate, onCrawlUpdate,
  crawlPages, sitemapPages, sitemapLoading,
  websiteContent, brandData, netlify, qaResult,
  onProjectRefresh,
}) {
  const nav = useNavigate();
  const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };
  const leadId = project?.lead_id || lead?.id;

  const [localBriefing, setLocalBriefing]       = useState(briefing);
  const [localLatestAudit, setLocalLatestAudit] = useState(latestAudit);
  const [localCrawlPages, setLocalCrawlPages]   = useState(crawlPages);
  const [localBrandColor, setLocalBrandColor]   = useState(brandData?.primary_color || null);

  useEffect(() => { setLocalBriefing(briefing); }, [briefing]); // eslint-disable-line
  useEffect(() => { setLocalLatestAudit(latestAudit); }, [latestAudit]); // eslint-disable-line
  useEffect(() => { setLocalCrawlPages(crawlPages); }, [crawlPages]); // eslint-disable-line
  useEffect(() => { if (brandData?.primary_color) setLocalBrandColor(brandData.primary_color); }, [brandData]); // eslint-disable-line

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
    briefing: localBriefing,
    latestAudit: localLatestAudit,
    crawlPages:        localCrawlPages || 0,
    brandPrimaryColor: brandData?.primary_color || localBrandColor || null,
    sitemapCount:      sitemapPages?.length || 0,
    contentCount:      (websiteContent || []).filter(p => p.ki_content || p.content_generated).length,
    credsCount:        0,
    designVersions:    0,
    editorSaved:       !!(project?.editor_saved || (sitemapPages || []).some(p => p.gjs_html?.trim())),
    netlifyUrl:        netlify?.netlify_site_url || netlify?.url || project?.netlify_site_url || null,
    netlifyReady:      !!(netlify?.state === 'ready' || netlify?.connected === true || project?.netlify_last_deploy || netlify?.netlify_last_deploy),
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

  const fertigCount = SCHRITTE.filter(s => s.istFertig(prozessDaten)).length;
  const gesamtPct   = Math.round((fertigCount / SCHRITTE.length) * 100);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden', fontFamily: 'var(--font-sans)', background: 'var(--bg-app)' }}>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>

      {/* Breadcrumb */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '10px 20px', borderBottom: '1px solid var(--border-light)', background: 'var(--bg-surface)', fontSize: 12, color: 'var(--text-secondary)', flexShrink: 0 }}>
        <button onClick={() => nav('/app/dashboard')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', fontSize: 12, fontFamily: 'var(--font-sans)', padding: 0 }}>Dashboard</button>
        <span>›</span>
        <button onClick={() => nav('/app/projects')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', fontSize: 12, fontFamily: 'var(--font-sans)', padding: 0 }}>Projekte</button>
        <span>›</span>
        <span
          onClick={() => leadId && nav(`/app/leads/${leadId}`)}
          style={{ cursor: leadId ? 'pointer' : 'default', color: leadId ? 'var(--brand-primary)' : 'var(--text-primary)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 5 }}
        >
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--brand-primary)', display: 'inline-block', flexShrink: 0 }} />
          {lead?.company_name || project?.company_name || `Projekt #${project?.id}`}
        </span>
      </div>

      {/* Scrollbarer Inhalt */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px' }}>

        {/* Fortschrittsbalken */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
          <div style={{ flex: 1, height: 6, background: 'var(--border-light)', borderRadius: 3, overflow: 'hidden' }}>
            <div style={{ height: '100%', width: `${gesamtPct}%`, background: '#534AB7', borderRadius: 3, transition: 'width .5s' }} />
          </div>
          <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)', flexShrink: 0 }}>
            {fertigCount} von {SCHRITTE.length}
          </span>
        </div>

        {/* Schritt-Liste */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {SCHRITTE.map((schritt, idx) => {
            const fertig     = schritt.istFertig(prozessDaten);
            const istAktiv   = schritt.id === aktiverId;
            const istOffen   = schritt.id === offenerSchritt;
            const istFutur   = !fertig && !istAktiv;
            const istNaechster = idx === aktiverIdx + 1;

            const cardBorder = istAktiv
              ? '2px solid #534AB7'
              : '1px solid var(--border-light)';

            const numBg    = fertig ? '#E1F5EE' : istAktiv ? '#534AB7' : 'var(--bg-elevated)';
            const numColor = fertig ? '#085041' : istAktiv ? '#fff' : 'var(--text-tertiary)';

            return (
              <div key={schritt.id} style={{
                background: 'var(--bg-surface)',
                border: cardBorder,
                borderRadius: 12,
                overflow: 'hidden',
                opacity: istFutur && !istNaechster && !schritt.optional ? 0.45 : 1,
                transition: 'all .2s',
              }}>
                {/* Header */}
                <div
                  onClick={() => !istFutur && setOffenerSchritt(istOffen && !istAktiv ? null : schritt.id)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 12,
                    padding: '14px 18px',
                    cursor: istFutur ? 'default' : 'pointer',
                    background: istAktiv ? '#534AB710' : 'transparent',
                  }}
                >
                  <div style={{ width: 32, height: 32, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, fontWeight: 600, flexShrink: 0, background: numBg, color: numColor }}>
                    {fertig ? '✓' : schritt.nr}
                  </div>

                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2, flexWrap: 'wrap' }}>
                      <span style={{ fontSize: 14, fontWeight: 500, color: fertig ? 'var(--text-secondary)' : 'var(--text-primary)' }}>
                        {schritt.icon} {schritt.label}
                      </span>
                      {istAktiv && (
                        <span style={{ fontSize: 10, fontWeight: 700, padding: '2px 8px', background: '#534AB7', color: '#fff', borderRadius: 10, letterSpacing: '.04em' }}>JETZT DU</span>
                      )}
                      {schritt.optional && (
                        <span style={{ fontSize: 10, color: 'var(--text-tertiary)', padding: '2px 6px', background: 'var(--bg-elevated)', borderRadius: 4 }}>Optional</span>
                      )}
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 4 }}>
                      {schritt.auto && !fertig && <span style={{ color: '#534AB7' }}>🤖</span>}
                      {fertig ? schritt.fertigText(prozessDaten) : schritt.desc}
                    </div>
                  </div>

                  <div style={{ flexShrink: 0 }}>
                    {fertig ? (
                      <span style={{ fontSize: 11, padding: '3px 10px', background: '#E1F5EE', color: '#085041', borderRadius: 20, fontWeight: 500 }}>
                        Erledigt ✓
                      </span>
                    ) : istAktiv && schritt.auto ? (
                      <span style={{ fontSize: 11, padding: '3px 10px', background: '#EEEDFE', color: '#534AB7', borderRadius: 20, fontWeight: 500 }}>
                        Automatisch
                      </span>
                    ) : !istFutur ? (
                      <span style={{ fontSize: 18, color: 'var(--text-tertiary)', transform: istOffen ? 'rotate(90deg)' : 'none', display: 'inline-block', transition: 'transform .2s' }}>›</span>
                    ) : null}
                  </div>
                </div>

                {/* Inhalt — nur wenn offen und nicht fertig */}
                {istOffen && !fertig && (
                  <div style={{ borderTop: '1px solid var(--border-light)' }}>
                    <SchrittContent
                      schritt={schritt}
                      project={project}
                      lead={lead}
                      leadId={leadId}
                      token={token}
                      headers={headers}
                      localBriefing={localBriefing}
                      reloadBriefing={reloadBriefing}
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
                      onProjectRefresh={onProjectRefresh}
                      prozessDaten={prozessDaten}
                    />

                    {schritt.istFertig(prozessDaten) && idx < SCHRITTE.length - 1 && (
                      <div style={{ padding: '12px 18px', borderTop: '1px solid var(--border-light)', display: 'flex', justifyContent: 'flex-end' }}>
                        <button
                          onClick={() => setOffenerSchritt(SCHRITTE[idx + 1].id)}
                          style={{ padding: '10px 24px', background: '#534AB7', color: '#fff', border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}
                        >
                          Weiter →
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function SchrittContent({
  schritt, project, lead, leadId, token, headers,
  localBriefing, reloadBriefing, latestAudit, onAuditComplete,
  onAnalyseUpdate, onSitemapReload, sitemapPages, sitemapLoading,
  websiteContent, brandData, netlify, qaResult, onProjectRefresh,
}) {
  const pad = { padding: '20px 24px' };

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
          projectId={project.id}
          leadId={leadId}
          websiteUrl={lead?.website_url || project.website_url}
          token={token}
          onDataUpdate={onAnalyseUpdate}
        />
      );

    case 'Audit':
      return (
        <AuditEmbed
          project={project}
          lead={lead}
          headers={headers}
          latestAudit={latestAudit}
          onAuditComplete={onAuditComplete}
        />
      );

    case 'Zugangsdaten':
      return <ZugangsdatenEmbed project={project} headers={headers} />;

    case 'Sitemap':
      return (
        <div>
          <SitemapKiVorschlag
            project={project}
            leadId={leadId}
            headers={headers}
            onGenerated={onSitemapReload}
            hasExistingPages={sitemapPages.length > 0}
            existingCount={sitemapPages.filter(p => !p.ist_pflichtseite).length}
          />
          {sitemapLoading ? <Spinner /> : (
            <SitemapEditorEmbed
              pages={sitemapPages}
              leadId={leadId}
              headers={headers}
              onReload={onSitemapReload}
            />
          )}
        </div>
      );

    case 'ContentWerkstatt':
      return (
        <ContentWerkstatt
          project={project}
          sitemapPages={sitemapPages}
          sitemapLoading={sitemapLoading}
          token={token}
          leadId={leadId}
          websiteContent={websiteContent}
          onProjectRefresh={onProjectRefresh}
        />
      );

    case 'DesignStudio':
      return (
        <DesignStudioEmbed
          project={project}
          leadId={leadId}
          token={token}
          headers={headers}
          brandData={brandData}
          sitemapPages={sitemapPages}
        />
      );

    case 'Editor':
      return (
        <DesignStudio
          project={project}
          leadId={leadId}
          token={token}
          brandData={brandData}
          sitemapPages={sitemapPages}
        />
      );

    case 'Netlify':
      return <NetlifyEmbed project={project} headers={headers} />;

    case 'DNS':
      return <DNSEmbed project={project} lead={lead} headers={headers} />;

    case 'QA':
      return <QAEmbed project={project} headers={headers} qaResult={qaResult} />;

    case 'Abnahme':
      return <AbnahmeEmbed project={project} lead={lead} headers={headers} netlify={netlify} />;

    default:
      return (
        <div style={{ padding: '20px 24px', color: 'var(--text-secondary)', fontSize: 13 }}>
          Dieser Schritt wird vorbereitet …
        </div>
      );
  }
}
