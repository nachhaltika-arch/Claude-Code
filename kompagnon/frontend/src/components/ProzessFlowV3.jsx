import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { PHASEN, ALLE_SCHRITTE, SchrittInhalt } from './ProzessFlow';
import API_BASE_URL from '../config';

export default function ProzessFlowV3({
  project, lead, token, briefing, latestAudit, onAuditUpdate,
  onSitemapReload, onBrandUpdate, onCrawlUpdate,
  crawlPages, sitemapPages, sitemapLoading,
  websiteContent, brandData, netlify, qaResult,
  onProjectRefresh, onNavigateBack, isAdmin, onShowEdit, onShowApproval, navigate,
}) {
  const nav = useNavigate();
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
    assetsGeklaert:          !!(briefing?.logo_vorhanden !== undefined && (briefing?.logo_vorhanden || briefing?.fotos_vorhanden)),
    sitemapCount:      sitemapPages?.length || 0,
    contentCount:      (websiteContent || []).filter(p => p.ki_content).length,
    credsCount:        0,
    hasAssets:         (websiteContent || []).some(p => p.images?.length > 0),
    designVersions:    0,
    editorSaved:       !!(project?.editor_saved || (sitemapPages || []).some(p => p.gjs_html?.trim())),
    netlifyUrl:        netlify?.netlify_site_url || netlify?.url || project?.netlify_site_url || null,
    netlifyReady:      !!(netlify?.state === 'ready' || netlify?.connected === true || project?.netlify_last_deploy || netlify?.netlify_last_deploy),
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

  // Init: erster nicht-fertiger Schritt — nur einmal beim Mount
  useEffect(() => {
    if (aktiverSchritt) return;
    const erster = ALLE_SCHRITTE.find(s => !s.istFertig(prozessDaten));
    setAktiverSchritt(erster?.id || ALLE_SCHRITTE[ALLE_SCHRITTE.length - 1].id);
  }, []); // eslint-disable-line

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

  const companyName = lead?.company_name || project?.company_name || '';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden', background: 'var(--bg-surface)' }}>
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes stepPulse {
          0%, 100% { box-shadow: 0 0 0 3px rgba(250,230,0,.3), 0 3px 12px rgba(250,230,0,.4); }
          50%       { box-shadow: 0 0 0 6px rgba(250,230,0,.15), 0 3px 16px rgba(250,230,0,.6); }
        }
      `}</style>

      {/* ── Breadcrumb ───────────────────────────────────────────────────── */}
      <div style={{ padding: '8px 16px', borderBottom: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0, background: 'var(--bg-app)' }}>
        <button onClick={() => nav('/app/dashboard')} style={{ background: 'none', border: 'none', padding: '2px 4px', borderRadius: 4, fontSize: 12, color: 'var(--text-tertiary)', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
          Dashboard
        </button>
        <span style={{ color: 'var(--text-tertiary)', fontSize: 13, userSelect: 'none' }}>›</span>
        <button onClick={() => nav('/app/projects')} style={{ background: 'none', border: 'none', padding: '2px 4px', borderRadius: 4, fontSize: 12, color: 'var(--text-tertiary)', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
          Projekte
        </button>
        <span style={{ color: 'var(--text-tertiary)', fontSize: 13, userSelect: 'none' }}>›</span>
        <span
          onClick={() => leadId && nav(`/app/leads/${leadId}`)}
          title="Zur Kundenkartei"
          style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '2px 6px', borderRadius: 4, fontSize: 12, color: 'var(--text-tertiary)', cursor: leadId ? 'pointer' : 'default', fontFamily: 'var(--font-sans)', transition: 'all .12s' }}
          onMouseEnter={e => { if (leadId) { e.currentTarget.style.color = 'var(--brand-primary)'; e.currentTarget.style.background = 'var(--bg-elevated)'; } }}
          onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-tertiary)'; e.currentTarget.style.background = 'transparent'; }}
        >
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--brand-primary)', display: 'inline-block', flexShrink: 0 }} />
          {companyName || `Projekt #${project?.id}`}
        </span>
        {aktivObj && (
          <>
            <span style={{ color: 'var(--text-tertiary)', fontSize: 13, userSelect: 'none' }}>›</span>
            <span style={{ fontSize: 12, color: 'var(--text-secondary)', fontWeight: 500 }}>
              Schritt {aktivObj.nr} · {aktivObj.label}
            </span>
          </>
        )}
      </div>

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
      <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr', flex: 1, minHeight: 0, overflow: 'hidden' }}>

        {/* Left 80px timeline */}
        <div style={{
          width: 80,
          background: 'linear-gradient(180deg, #004F59 0%, #003840 100%)',
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          height: '100%', flexShrink: 0,
          boxShadow: '2px 0 16px rgba(0,0,0,.25)',
        }}>

          {/* SVG Logo */}
          <div style={{ width: '100%', padding: '14px 0 12px', display: 'flex', justifyContent: 'center', alignItems: 'center', borderBottom: '0.5px solid rgba(255,255,255,.1)', marginBottom: 8, flexShrink: 0 }}>
            <svg width="36" height="36" viewBox="0 0 107.7 107.7" xmlns="http://www.w3.org/2000/svg" style={{ display: 'block' }}>
              <path fill="#008EAA" d="M5.7,53.8c0,11.8,4.3,22.7,11.3,31.1,3.4-19.9,14-59.4,20-76.2C18.7,15.5,5.7,33.1,5.7,53.8Z" />
              <path fill="#008EAA" d="M55.1,5.7c-1.4,5.4-6.4,24.1-10.4,38.4,7.1-8.9,16.2-15,23.5-15.5.8,0,1.4,0,2.3,0,4.5.2,14.6,4.8,15.5,13.5.3,5.4-4.1,15.5-8.2,15.8-5.1.3-9.7-6.1-9.8-7.4-.2-3,2.6-6.7,2.5-7.8,0-.4-.6-.5-1-.4-2.5.2-18.9,17.5-18,33.3.3,5.3,2.2,8.7,9.2,8.3,9.1-.6,18.2-8,28-22.4,1.1-1.6,2.4-2.3,3.5-2.4,2.3-.1,4.5,1.9,4.6,4.6,0,.8,0,1.7-.5,2.5-.7,1.4-5,8.2-10.9,14.5-7.8,8.5-17.6,13.2-26.5,14.5-4.9.7-10.6-.3-15.2-2.7-3.8-1.9-8.1-5.9-9.6-10.7-1.4,5.3-2.7,10.5-3.9,14.2,7,3.9,15,6.1,23.5,6.1,26.6,0,48.2-21.6,48.2-48.2S81.1,6.3,55.1,5.7Z" />
            </svg>
          </div>

          {/* Step circles */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, padding: '4px 0', overflowY: 'auto', width: '100%', scrollbarWidth: 'none' }}>
            {ALLE_SCHRITTE.map((s, idx) => {
              const fertig = s.istFertig(prozessDaten);
              const aktiv  = s.id === aktiverSchritt;
              const naechster = !fertig && !aktiv &&
                idx === ALLE_SCHRITTE.findIndex(x => x.id === aktiverSchritt) + 1;
              const size   = aktiv ? 36 : naechster || fertig ? 30 : 26;
              const bg     = fertig ? '#00875A' : aktiv ? '#FAE600' : naechster ? 'rgba(255,255,255,.15)' : 'rgba(255,255,255,.06)';
              const color  = fertig ? '#fff' : aktiv ? '#004F59' : naechster ? 'rgba(255,255,255,.7)' : 'rgba(255,255,255,.25)';
              const shadow = aktiv
                ? '0 0 0 3px rgba(250,230,0,.3), 0 3px 12px rgba(250,230,0,.4)'
                : fertig ? '0 2px 6px rgba(0,135,90,.35)'
                : naechster ? '0 0 0 1px rgba(255,255,255,.2)' : 'none';
              return (
                <div
                  key={s.id}
                  onClick={() => waehleSchritt(s)}
                  title={`${s.nr}. ${s.label}`}
                  style={{
                    width: size, height: size, borderRadius: '50%',
                    background: bg, color,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: aktiv ? 15 : size <= 26 ? 11 : 13,
                    fontWeight: 700, cursor: 'pointer', flexShrink: 0,
                    transition: 'all .2s', userSelect: 'none',
                    boxShadow: shadow,
                    animation: aktiv ? 'stepPulse 2s ease-in-out infinite' : 'none',
                    fontFamily: 'var(--font-sans)',
                  }}
                >
                  {fertig ? '✓' : s.nr}
                </div>
              );
            })}
          </div>

          {/* Progress % footer */}
          <div style={{ width: '100%', padding: '8px 0 10px', borderTop: '0.5px solid rgba(255,255,255,.1)', display: 'flex', justifyContent: 'center', flexShrink: 0 }}>
            <div style={{ fontSize: 9, fontWeight: 900, color: 'rgba(255,255,255,.35)', textTransform: 'uppercase', letterSpacing: '.06em' }}>
              {gesamtPct}%
            </div>
          </div>
        </div>

        {/* Right content area */}
        <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0, overflow: 'hidden' }}>

          {/* Active step header */}
          {aktivObj && (
            <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', gap: 14, background: `${aktivObj.phase.color}08`, flexShrink: 0 }}>
              <div style={{ width: 38, height: 38, borderRadius: '50%', flexShrink: 0, background: aktivObj.istFertig(prozessDaten) ? 'var(--success)' : aktivObj.phase.color, color: 'var(--text-inverse)', fontSize: 15, fontWeight: 800, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {aktivObj.istFertig(prozessDaten) ? '✓' : aktivObj.nr}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 10, fontWeight: 700, color: aktivObj.phase.color, textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 2 }}>
                  {aktivObj.phase.label} · Schritt {aktivObj.nr}/{ALLE_SCHRITTE.length}
                  {aktivObj.optional && <span style={{ marginLeft: 8, opacity: .6 }}>Optional</span>}
                  {aktivObj.istFertig(prozessDaten) && <span style={{ marginLeft: 8, background: 'var(--status-success-bg)', color: 'var(--status-success-text)', padding: '1px 6px', borderRadius: 99 }}>Fertig</span>}
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
                    style={{ padding: '6px 14px', borderRadius: 6, border: 'none', background: aktivObj.istFertig(prozessDaten) ? 'var(--success)' : aktivObj.phase.color, color: 'var(--text-inverse)', fontSize: 12, fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
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
                   <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--status-danger-text)', marginBottom: 4 }}>Noch nicht abgeschlossen:</div>
                   {fehlende.map((f, i) => <div key={i} style={{ fontSize: 12, color: 'var(--status-danger-text)', lineHeight: 1.6 }}>{f}</div>)}
                 </div>
               </div>
             );
           })()}

          {/* Step content — scrollable zone */}
          <div style={{ flex: 1, overflowY: 'auto', minHeight: 0 }}>
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
                goWeiter={() => goTo(1)} goZurueck={() => goTo(-1)}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

