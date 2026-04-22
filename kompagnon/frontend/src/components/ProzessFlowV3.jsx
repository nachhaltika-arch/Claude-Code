import { useState, useEffect, useCallback } from 'react';
import { PHASEN, ALLE_SCHRITTE, SchrittInhalt } from './ProzessFlow';
import API_BASE_URL from '../config';

export default function ProzessFlowV3({
  project, lead, token, briefing, latestAudit, onAuditUpdate,
  onSitemapReload, onBrandUpdate, onCrawlUpdate,
  crawlPages, sitemapPages, sitemapLoading,
  websiteContent, brandData, netlify, qaResult,
  onProjectRefresh, onNavigateBack, isAdmin, onShowEdit, onShowApproval, navigate,
}) {
  const [aktiverSchritt, setAktiverSchritt] = useState(null);
  const [warnung, setWarnung]               = useState(null);
  const [localBriefing, setLocalBriefing]   = useState(briefing);
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
  }, [onBrandUpdate, onCrawlUpdate]);

  const handleAuditComplete = useCallback((audit) => {
    setLocalLatestAudit(audit);
    if (onAuditUpdate) onAuditUpdate(audit);
  }, [onAuditUpdate]);

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
    latestAudit: localLatestAudit,
    crawlPages:        localCrawlPages || 0,
    brandPrimaryColor:       brandData?.primary_color || localBrandColor || null,
    brandGuidelineGenerated: !!(brandData?.guideline_generated),
    sitemapCount:      sitemapPages?.length || 0,
    contentCount:      (websiteContent || []).filter(p => p.ki_content).length,
    credsCount:        0,
    hasAssets:         (websiteContent || []).some(p => p.images?.length > 0),
    designVersions:    0,
    editorSaved:       false,
    netlifyUrl:        netlify?.url || null,
    netlifyReady:      netlify?.state === 'ready' || netlify?.published_deploy?.state === 'ready',
    domainReachable:   project?.domain_reachable || false,
    domainStatusCode:  project?.domain_status_code || null,
    qaResult,
    projectStatus:     project?.status || '',
    goLiveConfirmed:   !!(project?.abnahme_datum),
    kiReportDone:      false,
    moodboardDone:     false,
    qmDone:            false,
    gbpPlaceId:        project?.gbp_place_id || null,
    screenshotBefore:  project?.screenshot_before || null,
    screenshotAfter:   project?.screenshot_after || null,
  };

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

  const goTo = (delta) => {
    if (!aktivObj) return;
    const next = ALLE_SCHRITTE[aktivObj.nr - 1 + delta];
    if (!next) return;
    if (delta > 0) waehleSchritt(next);
    else { setWarnung(null); setAktiverSchritt(next.id); }
  };

  return (
    <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>

      {/* ── Top progress bar ─────────────────────────────────────────────── */}
      <div style={{ padding: '10px 16px 8px', borderBottom: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{ flex: 1, height: 5, background: 'var(--border-light)', borderRadius: 3, overflow: 'hidden' }}>
          <div style={{ height: '100%', width: `${gesamtPct}%`, background: 'linear-gradient(90deg,#008EAA,#059669)', borderRadius: 3, transition: 'width .5s' }} />
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexShrink: 0 }}>
          {PHASEN.map(phase => {
            const phaseFertig = phase.schritte.filter(s => s.istFertig(prozessDaten)).length;
            const phaseAktiv  = phase.schritte.some(s => s.id === aktiverSchritt);
            return (
              <div key={phase.id} style={{ display: 'flex', alignItems: 'center', gap: 4, opacity: phaseAktiv ? 1 : 0.5 }}>
                <span style={{ fontSize: 11 }}>{phase.icon}</span>
                <span style={{ fontSize: 10, fontWeight: 700, color: phaseAktiv ? phase.color : 'var(--text-tertiary)' }}>
                  {phaseFertig}/{phase.schritte.length}
                </span>
              </div>
            );
          })}
          <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-secondary)', marginLeft: 4 }}>
            {fertigCount}/{ALLE_SCHRITTE.length} · {gesamtPct}%
          </span>
        </div>
      </div>

      {/* ── Main: timeline + content ──────────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '64px 1fr', minHeight: 400 }}>

        {/* Left 64px timeline */}
        <div style={{ borderRight: '1px solid var(--border-light)', background: 'var(--bg-app)', padding: '12px 0', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0 }}>
          {PHASEN.map((phase, pi) => (
            <TimelinePhase
              key={phase.id}
              phase={phase}
              prozessDaten={prozessDaten}
              aktiverSchritt={aktiverSchritt}
              waehleSchritt={waehleSchritt}
              isLast={pi === PHASEN.length - 1}
            />
          ))}
        </div>

        {/* Right content area */}
        <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0 }}>

          {/* Active step header */}
          {aktivObj && (
            <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', gap: 14, background: `${aktivObj.phase.color}08`, flexShrink: 0 }}>
              <div style={{ width: 38, height: 38, borderRadius: '50%', flexShrink: 0, background: aktivObj.istFertig(prozessDaten) ? '#059669' : aktivObj.phase.color, color: '#fff', fontSize: 15, fontWeight: 800, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {aktivObj.istFertig(prozessDaten) ? '✓' : aktivObj.nr}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 10, fontWeight: 700, color: aktivObj.phase.color, textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 2 }}>
                  {aktivObj.phase.label} · Schritt {aktivObj.nr}/{ALLE_SCHRITTE.length}
                  {aktivObj.optional && <span style={{ marginLeft: 8, opacity: .6 }}>Optional</span>}
                  {aktivObj.istFertig(prozessDaten) && <span style={{ marginLeft: 8, background: '#dcfce7', color: '#059669', padding: '1px 6px', borderRadius: 99 }}>Fertig</span>}
                </div>
                <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>{aktivObj.icon} {aktivObj.label}</div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 1 }}>
                  {aktivObj.istFertig(prozessDaten) ? aktivObj.fertigText(prozessDaten) : aktivObj.desc}
                </div>
              </div>
              <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                {aktivObj.nr > 1 && (
                  <button onClick={() => goTo(-1)}
                    style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid var(--border-light)', background: 'var(--bg-surface)', color: 'var(--text-secondary)', fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                    ← Zurück
                  </button>
                )}
                {aktivObj.nr < ALLE_SCHRITTE.length && (
                  <button onClick={() => goTo(1)}
                    style={{ padding: '6px 14px', borderRadius: 6, border: 'none', background: aktivObj.istFertig(prozessDaten) ? '#059669' : aktivObj.phase.color, color: '#fff', fontSize: 12, fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                    Weiter →
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Order warning */}
          {warnung && (
            <div style={{ margin: '12px 16px 0', padding: '12px 16px', background: 'var(--status-warning-bg)', border: '1px solid var(--status-warning-text)', borderRadius: 'var(--radius-lg)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', flexShrink: 0 }}>
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

          {/* Missing fields warning */}
          {aktivObj && !aktivObj.istFertig(prozessDaten) &&
           !['BriefingUnternehmen','BriefingWebsite','ContentWerkstatt','DesignStudio','AnalyseZentrale'].includes(aktivObj.component) &&
           (() => {
             const fehlende = aktivObj.wasFehlts?.(prozessDaten) || [];
             if (!fehlende.length) return null;
             return (
               <div style={{ margin: '12px 20px 0', padding: '10px 14px', background: 'rgba(220,38,38,.06)', border: '1px solid rgba(220,38,38,.2)', borderRadius: 8, display: 'flex', alignItems: 'flex-start', gap: 10, flexShrink: 0 }}>
                 <span style={{ fontSize: 14, flexShrink: 0, marginTop: 1 }}>⚠️</span>
                 <div>
                   <div style={{ fontSize: 11, fontWeight: 700, color: '#C0392B', marginBottom: 4 }}>Noch nicht abgeschlossen:</div>
                   {fehlende.map((f, i) => <div key={i} style={{ fontSize: 12, color: '#C0392B', lineHeight: 1.6 }}>{f}</div>)}
                 </div>
               </div>
             );
           })()}

          {/* Step content */}
          {aktivObj && (
            <SchrittInhalt
              schritt={aktivObj} project={project} lead={lead}
              leadId={leadId} token={token} headers={headers}
              briefing={briefing} latestAudit={localLatestAudit}
              localBriefing={localBriefing} reloadBriefing={reloadBriefing}
              onAuditComplete={handleAuditComplete}
              onSitemapReload={onSitemapReload}
              onAnalyseUpdate={handleAnalyseUpdate}
              sitemapPages={sitemapPages} sitemapLoading={sitemapLoading}
              websiteContent={websiteContent} brandData={brandData}
              netlify={netlify} qaResult={qaResult}
              onProjectRefresh={onProjectRefresh}
              isAdmin={isAdmin} navigate={navigate}
              onShowEdit={onShowEdit} onShowApproval={onShowApproval}
            />
          )}
        </div>
      </div>
    </div>
  );
}

function TimelinePhase({ phase, prozessDaten, aktiverSchritt, waehleSchritt, isLast }) {
  return (
    <div style={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      {/* Phase label */}
      <div style={{ fontSize: 8, fontWeight: 800, color: phase.color, textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 6, opacity: 0.85 }}>
        {phase.label.slice(0, 3)}
      </div>

      {phase.schritte.map((schritt, si) => {
        const fertig = schritt.istFertig(prozessDaten);
        const aktiv  = schritt.id === aktiverSchritt;
        const isLastInPhase = si === phase.schritte.length - 1;
        const circleColor = fertig ? '#059669' : aktiv ? phase.color : 'var(--bg-elevated)';
        const textColor   = fertig || aktiv ? '#fff' : 'var(--text-tertiary)';
        const borderColor = fertig ? '#059669' : aktiv ? phase.color : 'var(--border-medium)';

        return (
          <div key={schritt.id} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%' }}>
            {/* Step circle */}
            <button
              onClick={() => waehleSchritt(schritt)}
              title={`${schritt.nr}. ${schritt.label}`}
              style={{
                width: aktiv ? 32 : 26, height: aktiv ? 32 : 26,
                borderRadius: '50%',
                border: `2px solid ${borderColor}`,
                background: circleColor,
                color: textColor,
                fontSize: aktiv ? 12 : 10,
                fontWeight: 800,
                cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontFamily: 'var(--font-sans)',
                transition: 'all .2s',
                flexShrink: 0,
                boxShadow: aktiv ? `0 0 0 3px ${phase.color}30` : 'none',
                position: 'relative',
                zIndex: 1,
              }}
            >
              {fertig ? '✓' : schritt.nr}
            </button>

            {/* Connector line — between steps and between phases */}
            {(!isLastInPhase || !isLast) && (
              <div style={{
                width: 2,
                height: isLastInPhase ? 14 : 10,
                background: fertig ? '#059669' : 'var(--border-light)',
                borderRadius: 1,
                margin: '3px 0',
                flexShrink: 0,
              }} />
            )}
          </div>
        );
      })}
    </div>
  );
}
