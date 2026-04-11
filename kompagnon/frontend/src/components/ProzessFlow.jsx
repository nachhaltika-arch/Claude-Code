import { useState, useEffect, useCallback } from 'react';
import AnalyseCentrale from './AnalyseCentrale';
import ContentWerkstatt from './ContentWerkstatt';
import DesignStudio from './DesignStudio';
import BriefingTab from './BriefingTab';
import BriefingWizard from './BriefingWizard';

const PHASEN = [
  {
    id: 'analyse', label: 'Analyse', icon: '🔍', color: '#008EAA',
    schritte: [
      { id: 'briefing-unternehmen', nr: 1, label: 'Briefing Unternehmen', desc: 'Stammdaten, Leistungen, USP erfassen', icon: '🏢', component: 'BriefingUnternehmen',
        istFertig: (d) => !!(d.briefing?.gewerk && d.briefing?.leistungen),
        fertigText: (d) => `${d.briefing?.gewerk}` },
      { id: 'audit', nr: 2, label: 'Website-Audit', desc: 'Technische Analyse der bestehenden Website', icon: '🔍', component: 'Audit',
        istFertig: (d) => !!(d.latestAudit?.total_score),
        fertigText: (d) => `Score: ${d.latestAudit?.total_score}/100` },
      { id: 'analyse-zentrale', nr: 3, label: 'Analyse-Zentrale', desc: 'Crawler starten — Seiten, Content, Brand, PageSpeed', icon: '🔬', component: 'AnalyseZentrale',
        istFertig: (d) => (d.crawlPages || 0) > 0,
        fertigText: (d) => `${d.crawlPages} Seiten gecrawlt` },
      { id: 'briefing-website', nr: 4, label: 'Briefing Website', desc: 'Ziele, Design-Wuensche, Seiten dokumentieren', icon: '📋', component: 'BriefingWebsite',
        istFertig: (d) => !!(d.briefing?.hauptziel || d.briefing?.seiten),
        fertigText: () => 'Ausgefuellt' },
      { id: 'zugangsdaten', nr: 5, label: 'Zugangsdaten', desc: 'Hosting, FTP, CMS-Zugaenge speichern', icon: '🔑', component: 'Zugangsdaten', optional: true,
        istFertig: (d) => (d.credsCount || 0) > 0,
        fertigText: (d) => `${d.credsCount} Eintraege` },
    ],
  },
  {
    id: 'content', label: 'Content', icon: '📝', color: '#7c3aed',
    schritte: [
      { id: 'sitemap', nr: 6, label: 'Sitemap anlegen', desc: 'Seitenstruktur der neuen Website definieren', icon: '🗺️', component: 'Sitemap',
        istFertig: (d) => (d.sitemapCount || 0) >= 3,
        fertigText: (d) => `${d.sitemapCount} Seiten` },
      { id: 'content-generieren', nr: 7, label: 'Content generieren', desc: 'KI erstellt Texte je Seite aus altem Content', icon: '🤖', component: 'ContentWerkstatt',
        istFertig: (d) => (d.contentCount || 0) > 0,
        fertigText: (d) => `${d.contentCount}/${d.sitemapCount} Seiten` },
      { id: 'bilder', nr: 8, label: 'Bilder & Assets', desc: 'Bilder den Seiten zuordnen', icon: '🖼️', component: 'Assets', optional: true,
        istFertig: (d) => !!(d.hasAssets),
        fertigText: () => 'Assets zugeordnet' },
    ],
  },
  {
    id: 'design', label: 'Design', icon: '🎨', color: '#d97706',
    schritte: [
      { id: 'template', nr: 9, label: 'Template waehlen', desc: 'Stil-Vorlage auswaehlen', icon: '🎭', component: 'DesignStudio',
        istFertig: (d) => !!(d.designVersions > 0),
        fertigText: (d) => `${d.designVersions} Version(en)` },
      { id: 'editor', nr: 10, label: 'Im Editor nachbearbeiten', desc: 'Feinschliff im GrapesJS-Editor', icon: '🖊️', component: 'Editor', optional: true,
        istFertig: (d) => !!(d.editorSaved),
        fertigText: () => 'Gespeichert' },
    ],
  },
  {
    id: 'golive', label: 'Go Live', icon: '🚀', color: '#059669',
    schritte: [
      { id: 'netlify', nr: 11, label: 'Auf Netlify deployen', desc: 'Website veroeffentlichen', icon: '🚀', component: 'Netlify',
        istFertig: (d) => !!(d.netlifyUrl),
        fertigText: (d) => d.netlifyUrl },
      { id: 'dns', nr: 12, label: 'DNS umstellen', desc: 'CNAME beim Domain-Anbieter setzen', icon: '🌍', component: 'DNS',
        istFertig: (d) => !!(d.dnsConfigured),
        fertigText: () => 'DNS konfiguriert' },
      { id: 'qa', nr: 13, label: 'QA-Check', desc: 'Links, Formulare, Mobile, Impressum pruefen', icon: '✓', component: 'QA',
        istFertig: (d) => !!(d.qaResult),
        fertigText: () => 'QA abgeschlossen' },
      { id: 'abnahme', nr: 14, label: 'Abnahme & Go Live', desc: 'Kundenfreigabe — Website ist live', icon: '🏁', component: 'Abnahme',
        istFertig: (d) => !!(d.goLiveConfirmed),
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

  const prozessDaten = {
    briefing,
    latestAudit,
    crawlPages:      crawlPages || 0,
    sitemapCount:    sitemapPages?.length || 0,
    contentCount:    (websiteContent || []).filter(p => p.ki_content).length,
    credsCount:      0,
    hasAssets:       (websiteContent || []).some(p => p.images?.length > 0),
    designVersions:  0,
    editorSaved:     false,
    netlifyUrl:      netlify?.url || null,
    dnsConfigured:   false,
    qaResult,
    goLiveConfirmed: false,
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
  const headers     = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };

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
                    <button key={s.id} onClick={() => waehleSchritt(s)} title={`${s.nr}. ${s.label}`}
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

          {/* Inhalt */}
          <SchrittInhalt
            schritt={aktivObj} project={project} lead={lead}
            token={token} headers={headers}
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

function SchrittInhalt({ schritt, project, lead, token, headers,
  briefing, latestAudit, sitemapPages, sitemapLoading,
  websiteContent, brandData, netlify, qaResult }) {

  const pad = { padding: '20px 24px' };

  switch (schritt.component) {

    case 'BriefingUnternehmen':
      return lead ? (
        <div style={pad}>
          <BriefingWizard
            leadId={lead.id}
            leadData={briefing}
            onClose={() => {}}
            onComplete={() => {}}
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
      return (
        <div style={pad}>
          {latestAudit ? (
            <div style={{ background: 'var(--status-success-bg)', border: '1px solid var(--status-success-text)', borderRadius: 8, padding: '14px 18px' }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--status-success-text)' }}>
                Audit vorhanden — Score: {latestAudit.total_score}/100
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>{latestAudit.level}</div>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '32px 20px', color: 'var(--text-tertiary)' }}>
              <div style={{ fontSize: 32, marginBottom: 10 }}>🔍</div>
              <div style={{ fontSize: 13 }}>Noch kein Audit — bitte Audit starten.</div>
            </div>
          )}
        </div>
      );

    case 'Zugangsdaten':
      return (
        <div style={pad}>
          <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
            Hosting-, FTP- und CMS-Zugaenge sicher speichern.
          </div>
        </div>
      );

    case 'Sitemap':
      return sitemapLoading
        ? <Spinner />
        : (
          <div style={pad}>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 12 }}>
              {sitemapPages.length > 0
                ? `${sitemapPages.length} Seiten definiert.`
                : 'Noch keine Sitemap — bitte Seitenstruktur anlegen.'}
            </div>
            {sitemapPages.map(p => (
              <div key={p.id} style={{ padding: '8px 12px', borderBottom: '1px solid var(--border-light)', display: 'flex', gap: 10 }}>
                <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-primary)' }}>{p.page_name}</span>
                <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{p.page_type}</span>
              </div>
            ))}
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

    case 'Assets':
      return (
        <div style={pad}>
          <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
            {(websiteContent || []).length} gecrawlte Seiten · {sitemapPages.length} Sitemap-Seiten
          </div>
        </div>
      );

    case 'DesignStudio':
    case 'Editor':
      return (
        <DesignStudio
          project={project}
          leadId={project.lead_id}
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
