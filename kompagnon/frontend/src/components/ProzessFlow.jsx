import { useState, useEffect, useCallback } from 'react';
import AnalyseCentrale from './AnalyseCentrale';
import ContentWerkstatt from './ContentWerkstatt';
import DesignStudio from './DesignStudio';
import BriefingTab from './BriefingTab';
import BriefingWizard from './BriefingWizard';
import API_BASE_URL from '../config';

const PHASEN = [
  {
    id: 'analyse', label: 'Analyse', icon: '🔍', color: '#008EAA',
    schritte: [
      { id: 'briefing-unternehmen', nr: 1, label: 'Briefing Unternehmen', desc: 'Stammdaten, Leistungen, USP erfassen', icon: '🏢', component: 'BriefingUnternehmen',
        istFertig: (d) => !!(d.briefing?.gewerk && d.briefing?.leistungen?.trim()),
        wasFehlts: (d) => { if (!d.briefing?.gewerk && !d.briefing?.leistungen) return []; const f = []; if (!d.briefing?.gewerk) f.push('Gewerk / Branche'); if (!d.briefing?.leistungen?.trim()) f.push('Leistungen'); return f; },
        fertigText: (d) => d.briefing?.gewerk || 'Ausgefuellt' },
      { id: 'audit', nr: 2, label: 'Website-Audit', desc: 'Technische Analyse der bestehenden Website', icon: '🔍', component: 'Audit',
        istFertig: (d) => !!(d.latestAudit?.total_score > 0),
        wasFehlts: (d) => d.latestAudit ? [] : ['Audit noch nicht gestartet'],
        fertigText: (d) => `Score: ${d.latestAudit?.total_score}/100` },
      { id: 'analyse-zentrale', nr: 3, label: 'Analyse-Zentrale', desc: 'Crawler, Brand Design, PageSpeed, GA', icon: '🔬', component: 'AnalyseZentrale',
        istFertig: (d) => (d.crawlPages || 0) >= 3 && !!(d.brandPrimaryColor),
        wasFehlts: (d) => { const f = []; if ((d.crawlPages||0) < 3) f.push(`Crawler: ${d.crawlPages||0} Seiten (mind. 3)`); if (!d.brandPrimaryColor) f.push('Brand-Scan fehlt'); return f; },
        fertigText: (d) => `${d.crawlPages} Seiten · Brand` },
      { id: 'briefing-website', nr: 4, label: 'Briefing Website', desc: 'Ziele, Design, Seiten dokumentieren', icon: '📋', component: 'BriefingWebsite',
        istFertig: (d) => !!((d.briefing?.hauptziel && d.briefing?.aktionen) || d.briefing?.seiten),
        wasFehlts: (d) => { const f = []; if (!d.briefing?.hauptziel) f.push('Hauptziel'); if (!d.briefing?.aktionen) f.push('CTA-Aktion'); if (!d.briefing?.seiten) f.push('Gewuenschte Seiten'); return f; },
        fertigText: () => 'Ausgefuellt' },
      { id: 'zugangsdaten', nr: 5, label: 'Zugangsdaten', desc: 'Hosting, FTP, CMS-Zugaenge', icon: '🔑', component: 'Zugangsdaten', optional: true,
        istFertig: (d) => (d.credsCount || 0) >= 1,
        wasFehlts: (d) => d.credsCount ? [] : ['Keine Zugaenge gespeichert'],
        fertigText: (d) => `${d.credsCount} Eintraege` },
    ],
  },
  {
    id: 'content', label: 'Content', icon: '📝', color: '#7c3aed',
    schritte: [
      { id: 'sitemap', nr: 6, label: 'Sitemap anlegen', desc: 'Seitenstruktur definieren', icon: '🗺️', component: 'Sitemap',
        istFertig: (d) => (d.sitemapCount || 0) >= 3,
        wasFehlts: (d) => { const f = 3-(d.sitemapCount||0); return f > 0 ? [`Noch ${f} Seite(n) (mind. 3)`] : []; },
        fertigText: (d) => `${d.sitemapCount} Seiten` },
      { id: 'content-generieren', nr: 7, label: 'Content & Bilder', desc: 'KI-Texte + Bilder je Seite', icon: '🤖', component: 'ContentWerkstatt',
        istFertig: (d) => (d.sitemapCount||0) > 0 && (d.contentCount||0) >= (d.sitemapCount||1),
        wasFehlts: (d) => { if (!d.sitemapCount) return ['Zuerst Sitemap anlegen']; const o = (d.sitemapCount||0)-(d.contentCount||0); return o > 0 ? [`${o}/${d.sitemapCount} Seiten ohne Content`] : []; },
        fertigText: (d) => `${d.contentCount}/${d.sitemapCount} Seiten` },
    ],
  },
  {
    id: 'design', label: 'Design', icon: '🎨', color: '#d97706',
    schritte: [
      { id: 'design-generieren', nr: 8, label: 'Design generieren', desc: 'Template + KI-Entwurf', icon: '✨', component: 'DesignStudio',
        istFertig: (d) => (d.designVersions || 0) >= 1,
        wasFehlts: (d) => (d.designVersions||0) === 0 ? ['Noch kein Design generiert'] : [],
        fertigText: (d) => `${d.designVersions} Version(en)` },
      { id: 'editor', nr: 9, label: 'Editor nachbearbeiten', desc: 'Feinschliff im GrapesJS', icon: '🖊️', component: 'Editor', optional: true,
        istFertig: (d) => !!(d.editorSaved),
        wasFehlts: () => ['Editor nicht geoeffnet'],
        fertigText: () => 'Gespeichert' },
    ],
  },
  {
    id: 'golive', label: 'Go Live', icon: '🚀', color: '#059669',
    schritte: [
      { id: 'netlify', nr: 10, label: 'Netlify deployen', desc: 'Website veroeffentlichen', icon: '🚀', component: 'Netlify',
        istFertig: (d) => !!(d.netlifyUrl && d.netlifyReady),
        wasFehlts: (d) => { if (!d.netlifyUrl) return ['Netlify nicht angelegt']; if (!d.netlifyReady) return ['Deploy nicht abgeschlossen']; return []; },
        fertigText: (d) => d.netlifyUrl || 'Deployed' },
      { id: 'dns', nr: 11, label: 'DNS umstellen', desc: 'CNAME beim Domain-Anbieter', icon: '🌍', component: 'DNS',
        istFertig: (d) => !!(d.domainReachable && d.domainStatusCode === 200),
        wasFehlts: (d) => { if (!d.netlifyUrl) return ['Zuerst Netlify deployen']; if (!d.domainReachable) return ['Domain nicht erreichbar']; return []; },
        fertigText: () => 'Domain erreichbar' },
      { id: 'qa', nr: 12, label: 'QA-Check', desc: 'Links, Mobile, Impressum', icon: '✓', component: 'QA',
        istFertig: (d) => !!(d.qaResult),
        wasFehlts: () => ['QA-Scan nicht durchgefuehrt'],
        fertigText: () => 'QA abgeschlossen' },
      { id: 'abnahme', nr: 13, label: 'Abnahme & Go Live', desc: 'Kundenfreigabe', icon: '🏁', component: 'Abnahme',
        istFertig: (d) => !!(d.goLiveConfirmed || d.projectStatus === 'fertig'),
        wasFehlts: (d) => { const f = []; if (!d.qaResult) f.push('QA-Check fehlt'); if (!d.domainReachable) f.push('DNS nicht umgestellt'); if (!d.goLiveConfirmed) f.push('Abnahme nicht erteilt'); return f; },
        fertigText: () => 'Live!' },
    ],
  },
];

export const ALLE_SCHRITTE = PHASEN.flatMap(p =>
  p.schritte.map(s => ({ ...s, phase: p }))
);

export { PHASEN };
export default function ProzessFlow({
  project, lead, token, briefing, latestAudit,
  crawlPages, sitemapPages, sitemapLoading,
  websiteContent, brandData, netlify, qaResult,
}) {
  const [aktiverSchritt, setAktiverSchritt] = useState(null);
  const [warnung, setWarnung]               = useState(null);
  const [localBriefing, setLocalBriefing]   = useState(briefing);

  useEffect(() => { setLocalBriefing(briefing); }, [briefing]); // eslint-disable-line

  const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };

  const reloadBriefing = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/briefings/${lead?.id || project?.lead_id}`, { headers });
      if (res.ok) setLocalBriefing(await res.json());
    } catch { /* silent */ }
  };

  const leadId = project?.lead_id || lead?.id;

  const prozessDaten = {
    briefing: localBriefing,
    latestAudit,
    crawlPages:       crawlPages || 0,
    brandPrimaryColor: brandData?.primary_color || null,
    sitemapCount:     sitemapPages?.length || 0,
    contentCount:     (websiteContent || []).filter(p => p.ki_content).length,
    credsCount:       0,
    hasAssets:        (websiteContent || []).some(p => p.images?.length > 0),
    designVersions:   0,
    editorSaved:      false,
    netlifyUrl:       netlify?.url || null,
    netlifyReady:     netlify?.state === 'ready' || netlify?.published_deploy?.state === 'ready',
    domainReachable:  project?.domain_reachable || false,
    domainStatusCode: project?.domain_status_code || null,
    qaResult,
    projectStatus:    project?.status || '',
    goLiveConfirmed:  false,
  };

  // Auto-Vorschlag: erster nicht-fertiger Schritt
  useEffect(() => {
    if (aktiverSchritt) return;
    const erster = ALLE_SCHRITTE.find(s => !s.istFertig(prozessDaten));
    setAktiverSchritt(erster?.id || ALLE_SCHRITTE[ALLE_SCHRITTE.length - 1].id);
  }, [JSON.stringify(prozessDaten)]); // eslint-disable-line

  const waehleSchritt = useCallback((schritt) => {
    const idx    = ALLE_SCHRITTE.findIndex(s => s.id === schritt.id);
    const voriger = idx > 0 ? ALLE_SCHRITTE[idx - 1] : null;
    if (voriger && !voriger.optional && !voriger.istFertig(prozessDaten)) {
      setWarnung({ ziel: schritt, fehlt: voriger,
        text: `Schritt ${voriger.nr} "${voriger.label}" ist noch nicht abgeschlossen.` });
    } else {
      setWarnung(null);
      setAktiverSchritt(schritt.id);
    }
  }, [JSON.stringify(prozessDaten)]); // eslint-disable-line

  const aktivObj    = ALLE_SCHRITTE.find(s => s.id === aktiverSchritt);
  const fertigCount = ALLE_SCHRITTE.filter(s => s.istFertig(prozessDaten)).length;
  const gesamtPct   = Math.round((fertigCount / ALLE_SCHRITTE.length) * 100);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

      {/* Gesamtfortschritt */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{ flex: 1, height: 6, background: 'var(--border-light)', borderRadius: 3, overflow: 'hidden' }}>
          <div style={{ height: '100%', width: `${gesamtPct}%`, background: 'linear-gradient(90deg,#008EAA,#059669)', borderRadius: 3, transition: 'width .5s' }} />
        </div>
        <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', flexShrink: 0 }}>
          {fertigCount}/{ALLE_SCHRITTE.length} · {gesamtPct}%
        </span>
      </div>

      {/* Phasen-Fortschrittsleiste */}
      <div style={{ display: 'flex', background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
        {PHASEN.map((phase, pi) => {
          const phaseFertig = phase.schritte.filter(s => s.istFertig(prozessDaten)).length;
          const phaseAktiv  = phase.schritte.some(s => s.id === aktiverSchritt);
          return (
            <div key={phase.id} style={{
              flex: 1, borderRight: pi < PHASEN.length - 1 ? '1px solid var(--border-light)' : 'none',
              padding: '10px 0 8px',
              background: phaseAktiv ? `${phase.color}12` : 'transparent',
              borderBottom: phaseAktiv ? `3px solid ${phase.color}` : '3px solid transparent',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 5, marginBottom: 8 }}>
                <span style={{ fontSize: 13 }}>{phase.icon}</span>
                <span style={{ fontSize: 11, fontWeight: 700, color: phaseAktiv ? phase.color : 'var(--text-secondary)' }}>{phase.label}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'center', gap: 4 }}>
                {phase.schritte.map(s => {
                  const fertig = s.istFertig(prozessDaten);
                  const aktiv  = s.id === aktiverSchritt;
                  return (
                    <button key={s.id} onClick={() => waehleSchritt(s)}
                      title={(() => { const f = s.wasFehlts?.(prozessDaten) || []; if (s.istFertig(prozessDaten)) return `${s.nr}. ${s.label} \u2713`; return f.length > 0 ? `${s.nr}. ${s.label}\n${f.join('\n')}` : `${s.nr}. ${s.label}`; })()}
                      style={{
                        width: aktiv ? 28 : 20, height: 20,
                        borderRadius: aktiv ? 10 : '50%', border: 'none', cursor: 'pointer',
                        background: fertig ? '#059669' : aktiv ? phase.color : s.optional ? 'var(--border-light)' : 'var(--bg-elevated)',
                        color: fertig || aktiv ? '#fff' : 'var(--text-tertiary)',
                        fontSize: 9, fontWeight: 700, transition: 'all .2s', padding: 0,
                        display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'var(--font-sans)',
                      }}>
                      {fertig ? '\u2713' : s.nr}
                    </button>
                  );
                })}
              </div>
              <div style={{ textAlign: 'center', marginTop: 5, fontSize: 9, color: 'var(--text-tertiary)' }}>
                {phaseFertig}/{phase.schritte.length}
              </div>
            </div>
          );
        })}
      </div>

      {/* Reihenfolge-Warnung */}
      {warnung && (
        <div style={{ padding: '12px 16px', background: 'var(--status-warning-bg)', border: '1px solid var(--status-warning-text)', borderRadius: 'var(--radius-lg)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 16 }}>⚠️</span>
            <div>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--status-warning-text)' }}>Empfohlene Reihenfolge</div>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{warnung.text}</div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={() => { setWarnung(null); setAktiverSchritt(warnung.fehlt.id); }}
              style={{ padding: '6px 12px', borderRadius: 6, border: 'none', background: 'var(--status-warning-text)', color: '#fff', fontSize: 11, fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
              Schritt {warnung.fehlt.nr} zuerst
            </button>
            <button onClick={() => { setWarnung(null); setAktiverSchritt(warnung.ziel.id); }}
              style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid var(--status-warning-text)', background: 'transparent', color: 'var(--status-warning-text)', fontSize: 11, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
              Trotzdem weiter
            </button>
          </div>
        </div>
      )}

      {/* Aktiver Schritt */}
      {aktivObj && (
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
          <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', gap: 14, background: `${aktivObj.phase.color}08` }}>
            <div style={{ width: 36, height: 36, borderRadius: '50%', flexShrink: 0, background: aktivObj.istFertig(prozessDaten) ? '#059669' : aktivObj.phase.color, color: '#fff', fontSize: 14, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {aktivObj.istFertig(prozessDaten) ? '\u2713' : aktivObj.nr}
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: aktivObj.phase.color, textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 2 }}>
                {aktivObj.phase.label} · Schritt {aktivObj.nr}/{ALLE_SCHRITTE.length}
                {aktivObj.optional && <span style={{ marginLeft: 8, opacity: .6 }}>Optional</span>}
                {aktivObj.istFertig(prozessDaten) && <span style={{ marginLeft: 8, background: '#dcfce7', color: '#059669', padding: '1px 6px', borderRadius: 99 }}>Fertig</span>}
              </div>
              <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>{aktivObj.icon} {aktivObj.label}</div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>
                {aktivObj.istFertig(prozessDaten) ? aktivObj.fertigText(prozessDaten) : aktivObj.desc}
              </div>
            </div>
            <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
              {aktivObj.nr > 1 && (
                <button onClick={() => { setWarnung(null); setAktiverSchritt(ALLE_SCHRITTE[aktivObj.nr - 2].id); }}
                  style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid var(--border-light)', background: 'var(--bg-surface)', color: 'var(--text-secondary)', fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                  Zurueck
                </button>
              )}
              {aktivObj.nr < ALLE_SCHRITTE.length && (
                <button onClick={() => waehleSchritt(ALLE_SCHRITTE[aktivObj.nr])}
                  style={{ padding: '6px 14px', borderRadius: 6, border: 'none', background: aktivObj.istFertig(prozessDaten) ? '#059669' : aktivObj.phase.color, color: '#fff', fontSize: 12, fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                  Weiter
                </button>
              )}
            </div>
          </div>

          {/* Fehlende Felder — nicht fuer Schritte mit eingebettetem Formular */}
          {!aktivObj.istFertig(prozessDaten) && !['BriefingUnternehmen','BriefingWebsite','ContentWerkstatt','DesignStudio','AnalyseZentrale'].includes(aktivObj.component) && aktivObj.wasFehlts && (() => {
            const fehlende = aktivObj.wasFehlts(prozessDaten);
            if (!fehlende || fehlende.length === 0) return null;
            return (
              <div style={{ margin: '0 20px 0', padding: '10px 14px', background: 'rgba(220,38,38,.06)', border: '1px solid rgba(220,38,38,.2)', borderRadius: 8, display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                <span style={{ fontSize: 14, flexShrink: 0, marginTop: 1 }}>⚠️</span>
                <div>
                  <div style={{ fontSize: 11, fontWeight: 700, color: '#C0392B', marginBottom: 4 }}>Noch nicht abgeschlossen:</div>
                  {fehlende.map((f, i) => <div key={i} style={{ fontSize: 12, color: '#C0392B', lineHeight: 1.6 }}>{f}</div>)}
                </div>
              </div>
            );
          })()}

          {/* Inhalt */}
          <SchrittInhalt
            schritt={aktivObj} project={project} lead={lead}
            leadId={leadId} token={token} headers={headers}
            briefing={briefing} latestAudit={latestAudit}
            sitemapPages={sitemapPages} sitemapLoading={sitemapLoading}
            websiteContent={websiteContent} brandData={brandData}
            netlify={netlify} qaResult={qaResult}
          />
        </div>
      )}
    </div>
  );
}

function SchrittInhalt({ schritt, project, lead, leadId, token, headers,
  briefing, latestAudit, sitemapPages, sitemapLoading,
  websiteContent, brandData, netlify, qaResult }) {

  const pad = { padding: '20px 24px' };

  switch (schritt.component) {

    case 'BriefingUnternehmen':
      return lead ? (
        <div style={pad}>
          <BriefingWizard
            leadId={lead.id}
            leadData={localBriefing}
            onClose={() => {}}
            onComplete={reloadBriefing}
            embedded
          />
        </div>
      ) : <Spinner />;

    case 'BriefingWebsite':
      return lead
        ? <div style={pad}><BriefingTab lead={lead} token={token} /></div>
        : <Spinner />;

    case 'AnalyseZentrale':
      return (
        <AnalyseCentrale
          projectId={project.id}
          leadId={project.lead_id}
          websiteUrl={lead?.website_url || project.website_url}
          token={token}
        />
      );

    case 'Audit':
      return <AuditEmbed project={project} lead={lead} headers={headers} latestAudit={latestAudit} />;

    case 'Zugangsdaten':
      return <ZugangsdatenEmbed project={project} headers={headers} />;

    case 'Sitemap':
      return (
        <div>
          {sitemapPages.length === 0 && (
            <SitemapKiVorschlag project={project} leadId={leadId} headers={headers} />
          )}
          {sitemapLoading ? <Spinner /> : (
            <div style={pad}>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 12 }}>
                {sitemapPages.length > 0 ? `${sitemapPages.length} Seiten definiert.` : 'KI-Vorschlag nutzen oder manuell anlegen.'}
              </div>
              {sitemapPages.map(p => (
                <div key={p.id} style={{ padding: '8px 12px', borderBottom: '1px solid var(--border-light)', display: 'flex', gap: 10, alignItems: 'center' }}>
                  <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-primary)', flex: 1 }}>{p.page_name}</span>
                  <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{p.page_type}</span>
                  {p.ziel_keyword && <span style={{ fontSize: 10, color: 'var(--text-tertiary)', fontStyle: 'italic' }}>{p.ziel_keyword}</span>}
                </div>
              ))}
            </div>
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
          leadId={project.lead_id}
          websiteContent={websiteContent}
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
      return (
        <div style={pad}>
          {netlify ? (
            <div style={{ background: 'var(--status-success-bg)', border: '1px solid var(--status-success-text)', borderRadius: 8, padding: 14 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--status-success-text)' }}>{netlify.url}</div>
            </div>
          ) : (
            <div style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>Netlify noch nicht eingerichtet.</div>
          )}
        </div>
      );

    case 'DNS':
      return (
        <div style={pad}>
          <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
            CNAME beim Domain-Anbieter von {lead?.company_name || 'Kunde'} setzen.
          </div>
        </div>
      );

    case 'QA':
      return (
        <div style={pad}>
          {qaResult
            ? <div style={{ fontSize: 13, color: 'var(--status-success-text)' }}>QA abgeschlossen</div>
            : <div style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>QA noch nicht durchgefuehrt.</div>}
        </div>
      );

    case 'Abnahme':
      return (
        <div style={{ ...pad, textAlign: 'center' }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>🏁</div>
          <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>
            Bereit fuer Go Live!
          </div>
          {netlify?.url && (
            <a href={netlify.url} target="_blank" rel="noreferrer"
              style={{ fontSize: 13, color: 'var(--brand-primary)' }}>
              {netlify.url}
            </a>
          )}
        </div>
      );

    default:
      return (
        <div style={{ ...pad, textAlign: 'center', color: 'var(--text-tertiary)' }}>
          <div style={{ fontSize: 32 }}>{schritt.icon}</div>
          <div style={{ fontSize: 13, marginTop: 8 }}>{schritt.desc}</div>
        </div>
      );
  }
}

function Spinner() {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: 32 }}>
      <div style={{ width: 24, height: 24, borderRadius: '50%', border: '2px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin .8s linear infinite' }} />
    </div>
  );
}

function SitemapKiVorschlag({ project, leadId, headers }) {
  const [loading, setLoading] = useState(false);
  const [done, setDone]       = useState(false);
  const [error, setError]     = useState(null);

  const generate = async () => {
    if (!leadId) { setError('Keine Lead-ID verfuegbar.'); return; }
    setLoading(true); setError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/sitemap/${leadId}/generate`, { method: 'POST', headers });
      if (!res.ok) throw new Error((await res.json().catch(()=>({}))).detail || `HTTP ${res.status}`);
      setDone(true);
      setTimeout(() => window.location.reload(), 800);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  if (done) return (
    <div style={{ padding: '12px 18px', background: 'var(--status-success-bg)', borderRadius: 8, fontSize: 13, color: 'var(--status-success-text)', marginBottom: 12 }}>
      Sitemap wurde generiert — wird geladen...
    </div>
  );

  return (
    <div style={{ margin: '0 20px 16px', padding: '14px 18px', background: 'rgba(0,142,170,.06)', border: '1px solid rgba(0,142,170,.25)', borderRadius: 10, display: 'flex', alignItems: 'center', gap: 14 }}>
      <span style={{ fontSize: 28, flexShrink: 0 }}>🤖</span>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 3 }}>Noch keine Sitemap — KI-Vorschlag erstellen?</div>
        <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Claude analysiert Briefing und gecrawlte Seiten und erstellt eine passende Seitenstruktur.</div>
        {error && <div style={{ fontSize: 11, color: 'var(--status-danger-text)', marginTop: 6 }}>{error}</div>}
      </div>
      <button onClick={generate} disabled={loading}
        style={{ padding: '9px 18px', borderRadius: 8, border: 'none', background: loading ? 'var(--border-medium)' : 'var(--brand-primary)', color: '#fff', fontSize: 12, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)', flexShrink: 0, display: 'flex', alignItems: 'center', gap: 6 }}>
        {loading ? (<><span style={{ width: 12, height: 12, border: '2px solid rgba(255,255,255,.3)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin .8s linear infinite', display: 'inline-block' }} />Wird erstellt...</>) : 'KI-Sitemap erstellen'}
      </button>
    </div>
  );
}

function AuditEmbed({ project, lead, headers, latestAudit }) {
  const [running, setRunning]   = useState(false);
  const [progress, setProgress] = useState('');
  const [error, setError]       = useState('');
  const [result, setResult]     = useState(latestAudit || null);

  const websiteUrl = lead?.website_url || project?.website_url;

  const scoreColor = (s) =>
    s >= 85 ? { bg: '#EAF3DE', text: '#27500A' } :
    s >= 70 ? { bg: '#FEF9C3', text: '#854D0E' } :
    s >= 50 ? { bg: '#FEF3DC', text: '#8A5C00' } :
              { bg: '#FDEAEA', text: '#C0392B' };

  const startAudit = async () => {
    if (!websiteUrl) { setError('Keine Website-URL hinterlegt.'); return; }
    setRunning(true); setError(''); setProgress('Audit wird gestartet...');
    try {
      const res = await fetch(`${API_BASE_URL}/api/audit/start`, {
        method: 'POST', headers,
        body: JSON.stringify({
          website_url: websiteUrl, lead_id: project?.lead_id,
          company_name: lead?.company_name || project?.company_name || '',
          city: lead?.city || '', trade: lead?.trade || '',
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Start fehlgeschlagen');
      const auditId = data.audit_id || data.id;
      if (!auditId) throw new Error('Keine Audit-ID erhalten');

      const msgs = ['Website wird analysiert...', 'Performance wird gemessen...', 'Rechtliches wird geprueft...', 'Screenshot wird erstellt...', 'KI-Analyse laeuft...'];
      let i = 0;
      const iv = setInterval(() => { i = (i + 1) % msgs.length; setProgress(msgs[i]); }, 4000);

      const deadline = Date.now() + 180000;
      while (Date.now() < deadline) {
        await new Promise(r => setTimeout(r, 4000));
        const poll = await fetch(`${API_BASE_URL}/api/audit/${auditId}`, { headers }).then(r => r.json()).catch(() => ({}));
        if (poll.status === 'completed') { clearInterval(iv); setResult(poll); setProgress(''); setRunning(false); break; }
        if (poll.status === 'failed') { clearInterval(iv); throw new Error('Audit fehlgeschlagen'); }
      }
    } catch (e) { setError(e.message); setRunning(false); setProgress(''); }
  };

  return (
    <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 16 }}>
      {websiteUrl && (
        <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
          <span style={{ color: 'var(--text-tertiary)' }}>URL: </span>
          <a href={websiteUrl} target="_blank" rel="noreferrer" style={{ color: 'var(--brand-primary)', textDecoration: 'none' }}>{websiteUrl}</a>
        </div>
      )}

      <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        <button onClick={startAudit} disabled={running || !websiteUrl}
          style={{ padding: '10px 22px', borderRadius: 8, border: 'none', background: running || !websiteUrl ? 'var(--border-medium)' : 'var(--brand-primary)', color: '#fff', fontSize: 13, fontWeight: 700, cursor: running || !websiteUrl ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', gap: 8 }}>
          {running ? (<><span style={{ width: 14, height: 14, border: '2px solid rgba(255,255,255,.3)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin .8s linear infinite', display: 'inline-block' }} />Laeuft...</>) : result ? 'Neuen Audit starten' : 'Audit starten'}
        </button>
        {running && <span style={{ fontSize: 12, color: 'var(--text-secondary)', fontStyle: 'italic' }}>{progress}</span>}
        {!websiteUrl && <span style={{ fontSize: 12, color: 'var(--status-warning-text)' }}>Keine Website-URL hinterlegt</span>}
      </div>

      {error && <div style={{ fontSize: 12, color: 'var(--status-danger-text)', background: 'var(--status-danger-bg)', padding: '8px 12px', borderRadius: 6 }}>{error}</div>}

      {result && !running && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <div style={{ ...scoreColor(result.total_score), padding: '12px 20px', borderRadius: 10, textAlign: 'center' }}>
              <div style={{ fontSize: 36, fontWeight: 900, lineHeight: 1, color: scoreColor(result.total_score).text }}>{result.total_score ?? '\u2014'}</div>
              <div style={{ fontSize: 10, fontWeight: 600, color: scoreColor(result.total_score).text, opacity: .7, marginTop: 2 }}>/ 100</div>
            </div>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>{result.level || '\u2014'}</div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 3 }}>
                {result.created_at ? new Date(result.created_at).toLocaleDateString('de-DE', { day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit' }) : ''}
              </div>
            </div>
          </div>
          {result.ai_summary && (
            <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.7, background: 'var(--bg-app)', borderRadius: 8, padding: '12px 14px', borderLeft: '3px solid var(--brand-primary)' }}>
              {result.ai_summary}
            </div>
          )}
          {result.top_problems?.length > 0 && (
            <div>
              <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.07em', marginBottom: 8 }}>Wichtigste Probleme</div>
              {result.top_problems.slice(0, 5).map((p, i) => (
                <div key={i} style={{ fontSize: 12, color: 'var(--text-secondary)', padding: '4px 0', borderBottom: '1px solid var(--border-light)', display: 'flex', gap: 8 }}>
                  <span style={{ color: 'var(--status-danger-text)', flexShrink: 0 }}>{'\u2717'}</span>
                  {typeof p === 'string' ? p : p.label || p.text || JSON.stringify(p)}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {!result && !running && (
        <div style={{ textAlign: 'center', padding: '32px 20px', color: 'var(--text-tertiary)' }}>
          <div style={{ fontSize: 36, marginBottom: 10 }}>🔍</div>
          <div style={{ fontSize: 13 }}>Noch kein Audit vorhanden. Klicke auf Audit starten.</div>
        </div>
      )}
    </div>
  );
}

function ZugangsdatenEmbed({ project, headers }) {
  const [creds, setCreds]       = useState([]);
  const [loading, setLoading]   = useState(true);
  const [saving, setSaving]     = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm]         = useState({ label: '', typ: 'hosting', username: '', password: '', url: '', notes: '' });

  const TYP_OPTIONS = [
    { value: 'hosting',   label: 'Hosting / cPanel' },
    { value: 'ftp',       label: 'FTP / SFTP' },
    { value: 'cms',       label: 'CMS / WordPress' },
    { value: 'domain',    label: 'Domain-Registrar' },
    { value: 'netlify',   label: 'Netlify' },
    { value: 'email',     label: 'E-Mail / SMTP' },
    { value: 'sonstiges', label: 'Sonstiges' },
  ];

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/projects/${project.id}/credentials`, { headers })
      .then(r => r.ok ? r.json() : [])
      .then(d => setCreds(Array.isArray(d) ? d : []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []); // eslint-disable-line

  const save = async () => {
    if (!form.label.trim()) return;
    setSaving(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/projects/${project.id}/credentials`, { method: 'POST', headers, body: JSON.stringify(form) });
      if (res.ok) { const neu = await res.json(); setCreds(prev => [...prev, neu]); setForm({ label: '', typ: 'hosting', username: '', password: '', url: '', notes: '' }); setShowForm(false); }
    } catch {} finally { setSaving(false); }
  };

  const del = async (id) => {
    await fetch(`${API_BASE_URL}/api/projects/${project.id}/credentials/${id}`, { method: 'DELETE', headers });
    setCreds(prev => prev.filter(c => c.id !== id));
  };

  if (loading) return <Spinner />;

  return (
    <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ fontSize: 12, color: 'var(--text-secondary)', background: 'var(--bg-app)', borderRadius: 8, padding: '10px 14px', borderLeft: '3px solid var(--brand-primary)' }}>
        Zugangsdaten werden verschluesselt gespeichert.
      </div>

      {creds.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {creds.map(c => (
            <div key={c.id} style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 8, padding: '12px 14px', display: 'flex', alignItems: 'flex-start', gap: 12 }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>{c.label}</span>
                  <span style={{ fontSize: 10, padding: '1px 7px', borderRadius: 99, background: 'var(--bg-elevated)', color: 'var(--text-tertiary)', fontWeight: 600 }}>
                    {TYP_OPTIONS.find(t => t.value === c.typ)?.label || c.typ || 'Sonstiges'}
                  </span>
                </div>
                {c.username && <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{c.username}</div>}
                {c.url && <a href={c.url} target="_blank" rel="noreferrer" style={{ fontSize: 12, color: 'var(--brand-primary)', textDecoration: 'none', display: 'block' }}>{c.url}</a>}
                {c.notes && <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>{c.notes}</div>}
              </div>
              <button onClick={() => del(c.id)} style={{ fontSize: 14, background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)', padding: 4 }}>X</button>
            </div>
          ))}
        </div>
      )}

      {showForm ? (
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 10, padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>Neuen Zugang hinzufuegen</div>
          {[
            { key: 'label', label: 'Bezeichnung *', placeholder: 'z.B. IONOS cPanel' },
            { key: 'username', label: 'Benutzername', placeholder: 'user@domain.de' },
            { key: 'password', label: 'Passwort', placeholder: '', type: 'password' },
            { key: 'url', label: 'URL / Panel', placeholder: 'https://login.ionos.de' },
            { key: 'notes', label: 'Notizen', placeholder: 'Weitere Infos' },
          ].map(f => (
            <div key={f.key}>
              <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.07em', marginBottom: 4 }}>{f.label}</div>
              <input type={f.type || 'text'} value={form[f.key]} onChange={e => setForm(p => ({ ...p, [f.key]: e.target.value }))} placeholder={f.placeholder}
                style={{ width: '100%', padding: '8px 10px', fontSize: 13, border: '1px solid var(--border-light)', borderRadius: 6, background: 'var(--bg-app)', color: 'var(--text-primary)', fontFamily: 'var(--font-sans)', boxSizing: 'border-box' }} />
            </div>
          ))}
          <div>
            <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.07em', marginBottom: 4 }}>Typ</div>
            <select value={form.typ} onChange={e => setForm(p => ({ ...p, typ: e.target.value }))}
              style={{ width: '100%', padding: '8px 10px', fontSize: 13, border: '1px solid var(--border-light)', borderRadius: 6, background: 'var(--bg-app)', color: 'var(--text-primary)', fontFamily: 'var(--font-sans)' }}>
              {TYP_OPTIONS.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
            <button onClick={() => setShowForm(false)} style={{ flex: 1, padding: 8, borderRadius: 6, border: '1px solid var(--border-light)', background: 'transparent', color: 'var(--text-secondary)', fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>Abbrechen</button>
            <button onClick={save} disabled={saving || !form.label.trim()}
              style={{ flex: 2, padding: 8, borderRadius: 6, border: 'none', background: form.label.trim() ? 'var(--brand-primary)' : 'var(--border-medium)', color: '#fff', fontSize: 12, fontWeight: 700, cursor: form.label.trim() ? 'pointer' : 'not-allowed', fontFamily: 'var(--font-sans)' }}>
              {saving ? 'Speichert...' : 'Speichern'}
            </button>
          </div>
        </div>
      ) : (
        <button onClick={() => setShowForm(true)}
          style={{ padding: '10px 20px', borderRadius: 8, border: '1.5px dashed var(--border-medium)', background: 'transparent', color: 'var(--brand-primary)', fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', gap: 8 }}>
          + Zugang hinzufuegen
        </button>
      )}

      {creds.length === 0 && !showForm && (
        <div style={{ textAlign: 'center', padding: '24px 0', color: 'var(--text-tertiary)', fontSize: 13 }}>Noch keine Zugangsdaten gespeichert.</div>
      )}
    </div>
  );
}

function DesignStudioEmbed({ project, leadId, token, headers, brandData, sitemapPages }) {
  const [selectedPage, setSelectedPage] = useState(null);
  const [generating, setGenerating]     = useState(false);
  const [generatedHtml, setGeneratedHtml] = useState(null);
  const [error, setError]               = useState('');
  const [dbTemplates, setDbTemplates]   = useState([]);
  const [selectedTpl, setSelectedTpl]   = useState(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/templates/`, { headers })
      .then(r => r.ok ? r.json() : [])
      .then(d => setDbTemplates(Array.isArray(d) ? d : []))
      .catch(() => {});
  }, []); // eslint-disable-line

  const PRESETS = [
    { id: 'modern', label: 'Modern Clean', color: '#008EAA', desc: 'Minimalistisch, viel Weissraum' },
    { id: 'bold', label: 'Handwerk Bold', color: '#C0392B', desc: 'Kraftvoll, markant' },
    { id: 'trust', label: 'Service & Trust', color: '#2C3E50', desc: 'Serioes, vertrauenswuerdig' },
    { id: 'friendly', label: 'Local Friendly', color: '#27AE60', desc: 'Warm, freundlich, lokal' },
    { id: 'premium', label: 'Premium Dark', color: '#1A1A2E', desc: 'Hochwertig, dunkel' },
  ];

  const colors = brandData ? [
    { role: 'Primaer', hex: brandData.primary_color || '#008EAA' },
    { role: 'Sekundaer', hex: brandData.secondary_color || '#004F59' },
  ].filter(c => c.hex) : [];

  const fonts = brandData?.all_fonts || [];

  const generate = async () => {
    if (!selectedPage) { setError('Bitte Seite auswaehlen'); return; }
    setGenerating(true); setError('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/projects/${project.id}/design-json/${selectedPage.id}`, { method: 'POST', headers });
      if (!res.ok) throw new Error((await res.json().catch(()=>({}))).detail || 'Fehler');
      const { blocks, brand } = await res.json();
      const { renderPage } = await import('../grapesjs/handwerk-blocks');
      setGeneratedHtml(renderPage(blocks, brand));
    } catch (e) { setError(e.message); }
    finally { setGenerating(false); }
  };

  return (
    <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 24 }}>
      {colors.length > 0 && (
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 10 }}>Brand-Farben</div>
          <div style={{ display: 'flex', gap: 10 }}>
            {colors.map(c => (
              <div key={c.role} style={{ textAlign: 'center' }}>
                <div style={{ width: 52, height: 52, borderRadius: 10, background: c.hex, border: '1px solid var(--border-light)', marginBottom: 4 }} />
                <div style={{ fontSize: 10, color: 'var(--text-tertiary)', fontWeight: 600 }}>{c.role}</div>
                <div style={{ fontSize: 9, color: 'var(--text-tertiary)', fontFamily: 'monospace' }}>{c.hex}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {fonts.length > 0 && (
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 10 }}>Schriftarten</div>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            {fonts.slice(0,4).map((f, i) => (
              <div key={i} style={{ padding: '10px 16px', background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 8 }}>
                <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 2 }}>Aa</div>
                <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{f}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div>
        <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 10 }}>Stil-Vorlage waehlen</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(160px,1fr))', gap: 10 }}>
          {PRESETS.map(p => (
            <div key={p.id} onClick={() => setSelectedTpl(p.id)}
              style={{ padding: '12px 14px', borderRadius: 10, cursor: 'pointer',
                border: `2px solid ${selectedTpl === p.id ? p.color : 'var(--border-light)'}`,
                background: selectedTpl === p.id ? `${p.color}12` : 'var(--bg-surface)', transition: 'all .15s' }}>
              <div style={{ width: '100%', height: 6, borderRadius: 3, background: p.color, marginBottom: 8 }} />
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 3 }}>{p.label}</div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{p.desc}</div>
            </div>
          ))}
          {dbTemplates.map(t => (
            <div key={`db-${t.id}`} onClick={() => setSelectedTpl(`db-${t.id}`)}
              style={{ padding: '12px 14px', borderRadius: 10, cursor: 'pointer',
                border: `2px solid ${selectedTpl === `db-${t.id}` ? 'var(--brand-primary)' : 'var(--border-light)'}`,
                background: selectedTpl === `db-${t.id}` ? 'var(--bg-active)' : 'var(--bg-surface)' }}>
              <div style={{ fontSize: 11, color: 'var(--brand-primary)', fontWeight: 700, marginBottom: 4 }}>Gespeichert</div>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)' }}>{t.name}</div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ borderTop: '1px solid var(--border-light)', paddingTop: 20 }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 10 }}>KI-Design generieren</div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
          <select value={selectedPage?.id || ''} onChange={e => { const p = sitemapPages.find(s => String(s.id) === e.target.value); setSelectedPage(p || null); }}
            style={{ flex: 1, minWidth: 180, padding: '9px 12px', fontSize: 13, border: '1px solid var(--border-light)', borderRadius: 8, background: 'var(--bg-app)', color: 'var(--text-primary)', fontFamily: 'var(--font-sans)' }}>
            <option value="">Seite waehlen...</option>
            {sitemapPages.map(p => <option key={p.id} value={p.id}>{p.page_name}</option>)}
          </select>
          <button onClick={generate} disabled={generating || !selectedPage || !selectedTpl}
            style={{ padding: '9px 20px', borderRadius: 8, border: 'none', background: (generating || !selectedPage || !selectedTpl) ? 'var(--border-medium)' : 'var(--brand-primary)', color: '#fff', fontSize: 13, fontWeight: 700, cursor: (generating || !selectedPage || !selectedTpl) ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', gap: 8 }}>
            {generating ? (<><span style={{ width:14, height:14, border:'2px solid rgba(255,255,255,.3)', borderTopColor:'#fff', borderRadius:'50%', animation:'spin .8s linear infinite', display:'inline-block' }} />Generiert...</>) : 'Design generieren'}
          </button>
        </div>
        {!selectedTpl && <div style={{ fontSize: 11, color: 'var(--status-warning-text)', marginTop: 6 }}>Bitte zuerst eine Stil-Vorlage waehlen</div>}
        {error && <div style={{ fontSize: 12, color: 'var(--status-danger-text)', marginTop: 8 }}>{error}</div>}
      </div>

      {generatedHtml && (
        <div style={{ borderTop: '1px solid var(--border-light)', paddingTop: 20 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 10 }}>Vorschau</div>
          <iframe srcDoc={generatedHtml} style={{ width: '100%', height: 500, border: '1px solid var(--border-light)', borderRadius: 8 }} title="Design-Vorschau" />
          <button onClick={() => window.dispatchEvent(new CustomEvent('kompagnon:open-editor', { detail: { html: generatedHtml } }))}
            style={{ marginTop: 10, padding: '10px 20px', borderRadius: 8, border: 'none', background: 'var(--brand-primary)', color: '#fff', fontSize: 13, fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
            Im Editor oeffnen
          </button>
        </div>
      )}
    </div>
  );
}
