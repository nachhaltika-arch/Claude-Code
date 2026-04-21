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
    brandPrimaryColor: localBrandColor || null,
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
    const idx     = ALLE_SCHRITTE.findIndex(s => s.id === schritt.id);
    const voriger = idx > 0 ? ALLE_SCHRITTE[idx - 1] : null;
    if (voriger && !voriger.optional && !voriger.istFertig(prozessDaten)) {
      setWarnung({ ziel: schritt, fehlt: voriger,
        text: `Schritt ${voriger.nr} „${voriger.label}" ist noch nicht abgeschlossen.` });
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

  const statusLabel = project?.status?.includes('abgeschlossen') ? 'Abgeschlossen'
    : project?.status?.includes('pausiert') ? 'Pausiert' : 'Aktiv';
  const companyName = project?.company_name || lead?.company_name || `Projekt #${project?.id}`;

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      display: 'flex', flexDirection: 'column',
      zIndex: 50, background: 'var(--bg-surface)',
      overflow: 'hidden', fontFamily: 'var(--font-sans)',
    }}>

      {/* ── Eigene Topbar mit Breadcrumb ────────────────────────────── */}
      <div style={{
        height: 44, flexShrink: 0,
        background: 'var(--bg-surface)',
        borderBottom: '1px solid var(--border-light)',
        display: 'flex', alignItems: 'center',
        padding: '0 20px 0 16px',
        zIndex: 10,
      }}>
        <nav style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, fontFamily: 'var(--font-sans)' }}>
          <button onClick={() => navigate && navigate('/app/dashboard')} style={{
            background: 'none', border: 'none', color: 'var(--text-tertiary)',
            cursor: 'pointer', fontSize: 12, fontFamily: 'var(--font-sans)', padding: 0,
          }}>
            Dashboard
          </button>
          <span style={{ color: 'var(--text-tertiary)', opacity: .5 }}>›</span>
          <button onClick={() => navigate && navigate('/app/projects')} style={{
            background: 'none', border: 'none', color: 'var(--text-tertiary)',
            cursor: 'pointer', fontSize: 12, fontFamily: 'var(--font-sans)', padding: 0,
          }}>
            Kundenprojekte
          </button>
          <span style={{ color: 'var(--text-tertiary)', opacity: .5 }}>›</span>
          <span style={{ color: 'var(--text-primary)', fontWeight: 700, fontSize: 12 }}>
            {companyName}
          </span>
        </nav>

        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 80, height: 4, background: 'var(--border-light)', borderRadius: 2, overflow: 'hidden' }}>
            <div style={{ height: '100%', width: `${gesamtPct}%`, background: 'linear-gradient(90deg,#008EAA,#059669)', borderRadius: 2, transition: 'width .5s' }} />
          </div>
          <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', whiteSpace: 'nowrap' }}>
            {fertigCount}/{ALLE_SCHRITTE.length}
          </span>
        </div>
      </div>

      {/* ── Hauptbereich: linkes Panel + rechter Inhalt ─────────────── */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden', minHeight: 0 }}>

      {/* ── LEFT: Process Navigation Sidebar ────────────────────────── */}
      <div style={{
        width: 220, flexShrink: 0,
        background: 'var(--kc-dark)',
        borderRight: '1px solid rgba(255,255,255,0.08)',
        display: 'flex', flexDirection: 'column',
        overflow: 'hidden',
      }}>

        {/* Header: back + project info */}
        <div style={{ padding: '14px 12px 10px', borderBottom: '1px solid rgba(255,255,255,0.1)', flexShrink: 0 }}>
          {onNavigateBack && (
            <button onClick={onNavigateBack} style={{
              display: 'flex', alignItems: 'center', gap: 5,
              background: 'none', border: 'none',
              color: 'rgba(255,255,255,0.45)', fontSize: 11,
              cursor: 'pointer', padding: '0 0 9px 0',
              fontFamily: 'var(--font-sans)',
            }}>
              ‹ Alle Projekte
            </button>
          )}
          <div style={{ fontSize: 13, fontWeight: 700, color: '#fff', lineHeight: 1.3, marginBottom: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {project?.company_name}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
            <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)' }}>#{project?.id}</span>
            <span style={{
              fontSize: 9, fontWeight: 700, padding: '1px 6px', borderRadius: 99,
              background: statusLabel === 'Aktiv' ? '#059669' : statusLabel === 'Pausiert' ? '#d97706' : 'rgba(255,255,255,0.15)',
              color: '#fff',
            }}>{statusLabel}</span>
          </div>
          {/* Progress bar */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
            <div style={{ flex: 1, height: 3, background: 'rgba(255,255,255,0.12)', borderRadius: 2, overflow: 'hidden' }}>
              <div style={{ width: `${gesamtPct}%`, height: '100%', background: 'linear-gradient(90deg,#008EAA,#059669)', transition: 'width .5s', borderRadius: 2 }} />
            </div>
            <span style={{ fontSize: 9, color: 'rgba(255,255,255,0.4)', flexShrink: 0, fontWeight: 600 }}>{fertigCount}/{ALLE_SCHRITTE.length}</span>
          </div>
        </div>

        {/* Phase + Step Navigation */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '6px 0 12px' }}>
          {PHASEN.map(phase => {
            const phaseFertig = phase.schritte.filter(s => s.istFertig(prozessDaten)).length;
            const phaseAktiv  = phase.schritte.some(s => s.id === aktiverSchritt);
            return (
              <div key={phase.id} style={{ marginBottom: 2 }}>
                {/* Phase header */}
                <div style={{ padding: '7px 12px 3px', display: 'flex', alignItems: 'center', gap: 5 }}>
                  <span style={{ fontSize: 10 }}>{phase.icon}</span>
                  <span style={{
                    fontSize: 9, fontWeight: 800,
                    color: phaseAktiv ? phase.color : 'rgba(255,255,255,0.28)',
                    textTransform: 'uppercase', letterSpacing: '.08em', flex: 1,
                  }}>{phase.label}</span>
                  <span style={{ fontSize: 9, color: 'rgba(255,255,255,0.25)' }}>
                    {phaseFertig}/{phase.schritte.length}
                  </span>
                </div>

                {/* Step items */}
                {phase.schritte.map(schritt => {
                  const fertig = schritt.istFertig(prozessDaten);
                  const aktiv  = schritt.id === aktiverSchritt;
                  return (
                    <button
                      key={schritt.id}
                      onClick={() => waehleSchritt(schritt)}
                      style={{
                        width: '100%', display: 'flex', alignItems: 'center', gap: 8,
                        padding: '5px 10px 5px 9px', border: 'none',
                        borderLeft: aktiv ? '3px solid var(--kc-yellow)' : '3px solid transparent',
                        background: aktiv ? 'rgba(255,255,255,0.09)' : 'transparent',
                        color: fertig ? '#86efac' : aktiv ? '#fff' : 'rgba(255,255,255,0.5)',
                        fontSize: 12, cursor: 'pointer', textAlign: 'left',
                        fontFamily: 'var(--font-sans)', transition: 'background .12s',
                      }}
                    >
                      <span style={{
                        width: 18, height: 18, borderRadius: '50%', flexShrink: 0,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: 9, fontWeight: 700,
                        background: fertig ? '#059669' : aktiv ? 'var(--kc-yellow)' : 'rgba(255,255,255,0.1)',
                        color: aktiv && !fertig ? '#004F59' : '#fff',
                      }}>
                        {fertig ? '✓' : schritt.nr}
                      </span>
                      <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1, fontSize: 11.5 }}>
                        {schritt.label}
                      </span>
                      {schritt.optional && <span style={{ fontSize: 9, opacity: .35, flexShrink: 0 }}>opt</span>}
                    </button>
                  );
                })}
              </div>
            );
          })}
        </div>

        {/* Sidebar footer: action buttons */}
        <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', padding: '10px 10px', flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 4 }}>
          {project?.lead_id && navigate && (
            <button onClick={() => navigate(`/app/leads/${project.lead_id}`)} style={{
              width: '100%', padding: '6px 10px', border: 'none', borderRadius: 'var(--radius-md)',
              background: 'rgba(255,255,255,0.07)', color: 'rgba(255,255,255,0.65)',
              fontSize: 11, cursor: 'pointer', textAlign: 'left', fontFamily: 'var(--font-sans)',
              display: 'flex', alignItems: 'center', gap: 6,
            }}>
              <span style={{ fontSize: 13 }}>👤</span> Kundenkartei
            </button>
          )}
          {onShowEdit && (
            <button onClick={onShowEdit} style={{
              width: '100%', padding: '6px 10px', border: 'none', borderRadius: 'var(--radius-md)',
              background: 'rgba(255,255,255,0.07)', color: 'rgba(255,255,255,0.65)',
              fontSize: 11, cursor: 'pointer', textAlign: 'left', fontFamily: 'var(--font-sans)',
              display: 'flex', alignItems: 'center', gap: 6,
            }}>
              <span style={{ fontSize: 13 }}>✏️</span> Projektdaten
            </button>
          )}
          {isAdmin && onShowApproval && (
            <button onClick={onShowApproval} style={{
              width: '100%', padding: '6px 10px', border: 'none', borderRadius: 'var(--radius-md)',
              background: 'rgba(250,230,0,0.15)', color: 'var(--kc-yellow)',
              fontSize: 11, cursor: 'pointer', textAlign: 'left', fontFamily: 'var(--font-sans)',
              display: 'flex', alignItems: 'center', gap: 6,
            }}>
              <span style={{ fontSize: 13 }}>🖊️</span> Freigabe anfragen
            </button>
          )}
        </div>
      </div>

      {/* ── RIGHT: Step Content Area ─────────────────────────────────── */}
      <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', overflow: 'hidden', background: 'var(--bg-app)' }}>

        {/* Active step header */}
        {aktivObj && (
          <div style={{
            padding: '14px 20px',
            borderBottom: '1px solid var(--border-light)',
            display: 'flex', alignItems: 'center', gap: 14,
            background: `${aktivObj.phase.color}08`,
            flexShrink: 0,
          }}>
            <div style={{
              width: 38, height: 38, borderRadius: '50%', flexShrink: 0,
              background: aktivObj.istFertig(prozessDaten) ? '#059669' : aktivObj.phase.color,
              color: '#fff', fontSize: 15, fontWeight: 800,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              {aktivObj.istFertig(prozessDaten) ? '✓' : aktivObj.nr}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: aktivObj.phase.color, textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 2 }}>
                {aktivObj.phase.label} · Schritt {aktivObj.nr}/{ALLE_SCHRITTE.length}
                {aktivObj.optional && <span style={{ marginLeft: 8, opacity: .6 }}>Optional</span>}
                {aktivObj.istFertig(prozessDaten) && (
                  <span style={{ marginLeft: 8, background: '#dcfce7', color: '#059669', padding: '1px 6px', borderRadius: 99 }}>Fertig</span>
                )}
              </div>
              <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>
                {aktivObj.icon} {aktivObj.label}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 1 }}>
                {aktivObj.istFertig(prozessDaten) ? aktivObj.fertigText(prozessDaten) : aktivObj.desc}
              </div>
            </div>
            <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
              {aktivObj.nr > 1 && (
                <button onClick={() => goTo(-1)} style={{
                  padding: '6px 12px', borderRadius: 6,
                  border: '1px solid var(--border-light)',
                  background: 'var(--bg-surface)', color: 'var(--text-secondary)',
                  fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)',
                }}>
                  ← Zurück
                </button>
              )}
              {aktivObj.nr < ALLE_SCHRITTE.length && (
                <button onClick={() => goTo(1)} style={{
                  padding: '6px 14px', borderRadius: 6, border: 'none',
                  background: aktivObj.istFertig(prozessDaten) ? '#059669' : aktivObj.phase.color,
                  color: '#fff', fontSize: 12, fontWeight: 700,
                  cursor: 'pointer', fontFamily: 'var(--font-sans)',
                }}>
                  Weiter →
                </button>
              )}
            </div>
          </div>
        )}

        {/* Scrollable step area */}
        <div style={{ flex: 1, overflowY: 'auto', minHeight: 0 }}>

          {/* Order warning */}
          {warnung && (
            <div style={{
              margin: '12px 16px 0', padding: '12px 16px',
              background: 'var(--status-warning-bg)',
              border: '1px solid var(--status-warning-text)',
              borderRadius: 'var(--radius-lg)',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ fontSize: 16 }}>⚠️</span>
                <div>
                  <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--status-warning-text)' }}>Empfohlene Reihenfolge</div>
                  <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{warnung.text}</div>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button onClick={() => { setWarnung(null); setAktiverSchritt(warnung.fehlt.id); }} style={{
                  padding: '6px 12px', borderRadius: 6, border: 'none',
                  background: 'var(--status-warning-text)', color: '#fff',
                  fontSize: 11, fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-sans)',
                }}>
                  Schritt {warnung.fehlt.nr} zuerst
                </button>
                <button onClick={() => { setWarnung(null); setAktiverSchritt(warnung.ziel.id); }} style={{
                  padding: '6px 12px', borderRadius: 6,
                  border: '1px solid var(--status-warning-text)',
                  background: 'transparent', color: 'var(--status-warning-text)',
                  fontSize: 11, cursor: 'pointer', fontFamily: 'var(--font-sans)',
                }}>
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
               <div style={{
                 margin: '12px 20px 0', padding: '10px 14px',
                 background: 'rgba(220,38,38,.06)', border: '1px solid rgba(220,38,38,.2)',
                 borderRadius: 8, display: 'flex', alignItems: 'flex-start', gap: 10,
               }}>
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
            />
          )}
        </div>
      </div>
      </div>{/* end Hauptbereich */}
    </div>
  );
}
