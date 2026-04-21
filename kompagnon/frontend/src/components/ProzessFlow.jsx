import { useState, useEffect, useCallback } from 'react';
import AnalyseCentrale from './AnalyseCentrale';
import ContentWerkstatt from './ContentWerkstatt';
import DesignStudio from './DesignStudio';
import BriefingTab from './BriefingTab';
import BriefingWizard from './BriefingWizard';
import KiReportPanel from './KiReportPanel';
import MoodboardPanel from './MoodboardPanel';
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
    id: 'briefing', label: 'Report', icon: '🤖', color: '#0d6efd',
    schritte: [
      { id: 'ki-report', nr: 6, label: 'KI-Report erstellen', desc: 'KI-Analyse aus Briefing + Crawler-Daten', icon: '🤖', component: 'KiReport',
        istFertig: (d) => !!(d.kiReportDone),
        wasFehlts: () => ['Report noch nicht generiert'],
        fertigText: () => 'Report erstellt', optional: true },
    ],
  },
  {
    id: 'content', label: 'Content', icon: '📝', color: '#7c3aed',
    schritte: [
      { id: 'moodboard', nr: 7, label: 'Moodboard / Stilrichtung', desc: 'Stilrichtung und Farbwelt festlegen', icon: '🎨', component: 'Moodboard',
        istFertig: (d) => !!(d.moodboardDone),
        wasFehlts: () => ['Stilrichtung noch nicht gewaehlt'],
        fertigText: () => 'Stilrichtung festgelegt', optional: true },
      { id: 'sitemap', nr: 8, label: 'Sitemap anlegen', desc: 'Seitenstruktur definieren', icon: '🗺️', component: 'Sitemap',
        istFertig: (d) => (d.sitemapCount || 0) >= 3,
        wasFehlts: (d) => { const f = 3-(d.sitemapCount||0); return f > 0 ? [`Noch ${f} Seite(n) (mind. 3)`] : []; },
        fertigText: (d) => `${d.sitemapCount} Seiten` },
      { id: 'content-generieren', nr: 9, label: 'Content & Bilder', desc: 'KI-Texte + Bilder je Seite', icon: '📝', component: 'ContentWerkstatt',
        istFertig: (d) => (d.sitemapCount||0) > 0 && (d.contentCount||0) >= (d.sitemapCount||1),
        wasFehlts: (d) => { if (!d.sitemapCount) return ['Zuerst Sitemap anlegen']; const o = (d.sitemapCount||0)-(d.contentCount||0); return o > 0 ? [`${o}/${d.sitemapCount} Seiten ohne Content`] : []; },
        fertigText: (d) => `${d.contentCount}/${d.sitemapCount} Seiten` },
    ],
  },
  {
    id: 'design', label: 'Design', icon: '🎨', color: '#d97706',
    schritte: [
      { id: 'design-generieren', nr: 10, label: 'Design generieren', desc: 'Template + KI-Entwurf', icon: '✨', component: 'DesignStudio',
        istFertig: (d) => (d.designVersions || 0) >= 1,
        wasFehlts: (d) => (d.designVersions||0) === 0 ? ['Noch kein Design generiert'] : [],
        fertigText: (d) => `${d.designVersions} Version(en)` },
      { id: 'editor', nr: 11, label: 'Editor nachbearbeiten', desc: 'Feinschliff im GrapesJS', icon: '🖊️', component: 'Editor', optional: true,
        istFertig: (d) => !!(d.editorSaved),
        wasFehlts: () => ['Editor nicht geoeffnet'],
        fertigText: () => 'Gespeichert' },
    ],
  },
  {
    id: 'golive', label: 'Go Live', icon: '🚀', color: '#059669',
    schritte: [
      { id: 'netlify', nr: 12, label: 'Netlify deployen', desc: 'Website veroeffentlichen', icon: '🚀', component: 'Netlify',
        istFertig: (d) => !!(d.netlifyUrl && d.netlifyReady),
        wasFehlts: (d) => { if (!d.netlifyUrl) return ['Netlify nicht angelegt']; if (!d.netlifyReady) return ['Deploy nicht abgeschlossen']; return []; },
        fertigText: (d) => d.netlifyUrl || 'Deployed' },
      { id: 'dns', nr: 13, label: 'DNS umstellen', desc: 'CNAME beim Domain-Anbieter', icon: '🌍', component: 'DNS',
        istFertig: (d) => !!(d.domainReachable && d.domainStatusCode === 200),
        wasFehlts: (d) => { if (!d.netlifyUrl) return ['Zuerst Netlify deployen']; if (!d.domainReachable) return ['Domain nicht erreichbar']; return []; },
        fertigText: () => 'Domain erreichbar' },
      { id: 'qa', nr: 14, label: 'QA-Check', desc: 'Links, Mobile, Impressum', icon: '✓', component: 'QA',
        istFertig: (d) => !!(d.qaResult),
        wasFehlts: () => ['QA-Scan nicht durchgefuehrt'],
        fertigText: () => 'QA abgeschlossen' },
      { id: 'abnahme', nr: 15, label: 'Abnahme & Go Live', desc: 'Kundenfreigabe', icon: '🏁', component: 'Abnahme',
        istFertig: (d) => !!(d.goLiveConfirmed || d.projectStatus === 'fertig'),
        wasFehlts: (d) => { const f = []; if (!d.qaResult) f.push('QA-Check fehlt'); if (!d.domainReachable) f.push('DNS nicht umgestellt'); if (!d.goLiveConfirmed) f.push('Abnahme nicht erteilt'); return f; },
        fertigText: () => 'Live!' },
    ],
  },
  {
    id: 'qm', label: 'QM', icon: '✅', color: '#0891b2',
    schritte: [
      { id: 'qm-checkliste', nr: 16, label: 'QM-Checkliste', desc: 'Qualitaetssicherung nach Go Live', icon: '✅', component: 'QmCheckliste',
        istFertig: (d) => !!(d.qmDone),
        wasFehlts: () => ['Checkliste noch nicht abgehakt'],
        fertigText: () => 'QM abgeschlossen', optional: true },
      { id: 'ki-qa-scan', nr: 17, label: 'KI-QA-Scan', desc: 'Automatische Qualitaetspruefung per KI', icon: '🤖', component: 'KiQaScan',
        istFertig: (d) => !!(d.qaResult),
        wasFehlts: () => ['Scan noch nicht durchgefuehrt'],
        fertigText: () => 'Scan abgeschlossen', optional: true },
    ],
  },
  {
    id: 'postlaunch', label: 'Post-Launch', icon: '📈', color: '#dc2626',
    schritte: [
      { id: 'gbp-qr', nr: 18, label: 'GBP + QR-Code', desc: 'Google Business Profile & Bewertungs-QR', icon: '📍', component: 'GbpQr',
        istFertig: (d) => !!(d.gbpPlaceId),
        wasFehlts: () => ['GBP-Place-ID fehlt'],
        fertigText: () => 'GBP eingerichtet', optional: true },
      { id: 'trustpilot', nr: 19, label: 'Trustpilot', desc: 'Bewertungsanfrage an Kunden senden', icon: '⭐', component: 'Trustpilot',
        istFertig: () => false,
        wasFehlts: () => [],
        fertigText: () => 'Anfrage gesendet', optional: true },
      { id: 'website-vergleich', nr: 20, label: 'Website-Vergleich', desc: 'Vorher / Nachher Screenshots', icon: '📸', component: 'WebsiteVergleich',
        istFertig: (d) => !!(d.screenshotBefore && d.screenshotAfter),
        wasFehlts: (d) => { const f = []; if (!d.screenshotBefore) f.push('Vorher-Screenshot fehlt'); if (!d.screenshotAfter) f.push('Nachher-Screenshot fehlt'); return f; },
        fertigText: () => 'Screenshots erstellt', optional: true },
    ],
  },
  {
    id: 'fertig', label: 'Fertig', icon: '🌐', color: '#7c3aed',
    schritte: [
      { id: 'upsell', nr: 21, label: 'Up-Sales', desc: 'Retainer, SEO, Wartungspaket anbieten', icon: '💼', component: 'Upsell',
        istFertig: () => false,
        wasFehlts: () => [],
        fertigText: () => 'Angebot erstellt', optional: true },
      { id: 'live-daten', nr: 22, label: 'Live-Daten', desc: 'PageSpeed, Domain-Status, Projektabschluss', icon: '🌐', component: 'LiveDaten',
        istFertig: (d) => !!(d.domainReachable),
        wasFehlts: (d) => d.domainReachable ? [] : ['Domain noch nicht erreichbar'],
        fertigText: () => 'Website live' },
    ],
  },
];

export const ALLE_SCHRITTE = PHASEN.flatMap(p =>
  p.schritte.map(s => ({ ...s, phase: p }))
);

export { PHASEN };
export default function ProzessFlow({
  project, lead, token, briefing, latestAudit, onAuditUpdate,
  onSitemapReload, onBrandUpdate, onCrawlUpdate,
  crawlPages, sitemapPages, sitemapLoading,
  websiteContent, brandData, netlify, qaResult,
  onProjectRefresh,
}) {
  const [aktiverSchritt, setAktiverSchritt] = useState(null);
  const [warnung, setWarnung]               = useState(null);
  const [localBriefing, setLocalBriefing]   = useState(briefing);
  const [localLatestAudit, setLocalLatestAudit] = useState(latestAudit);
  const [localCrawlPages, setLocalCrawlPages] = useState(crawlPages);
  const [localBrandColor, setLocalBrandColor] = useState(brandData?.primary_color || null);

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
    crawlPages:       localCrawlPages || 0,
    brandPrimaryColor: localBrandColor || null,
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
    goLiveConfirmed:  !!(project?.abnahme_datum),
    // neue Schritte
    kiReportDone:     false,
    moodboardDone:    false,
    qmDone:           false,
    gbpPlaceId:       project?.gbp_place_id || null,
    screenshotBefore: project?.screenshot_before || null,
    screenshotAfter:  project?.screenshot_after  || null,
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
        </div>
      )}
    </div>
  );
}

export function SchrittInhalt({ schritt, project, lead, leadId, token, headers,
  briefing, latestAudit, localBriefing, reloadBriefing, onAuditComplete,
  onSitemapReload, onAnalyseUpdate, sitemapPages, sitemapLoading,
  websiteContent, brandData, netlify, qaResult, onProjectRefresh }) {

  const pad = { padding: '20px 24px' };

  switch (schritt.component) {

    case 'BriefingUnternehmen':
      return lead ? (
        <BriefingUnternehmenEmbed lead={lead} localBriefing={localBriefing} reloadBriefing={reloadBriefing} />
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
          onDataUpdate={onAnalyseUpdate}
        />
      );

    case 'Audit':
      return <AuditEmbed project={project} lead={lead} headers={headers} latestAudit={latestAudit} onAuditComplete={onAuditComplete} />;

    case 'Zugangsdaten':
      return <ZugangsdatenEmbed project={project} headers={headers} />;

    case 'Sitemap':
      return (
        <div>
          {sitemapPages.length === 0 && (
            <SitemapKiVorschlag project={project} leadId={leadId} headers={headers} onGenerated={onSitemapReload} />
          )}
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
          leadId={project.lead_id}
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
      return <NetlifyEmbed project={project} headers={headers} netlify={netlify} />;

    case 'DNS':
      return <DNSEmbed project={project} lead={lead} headers={headers} />;

    case 'QA':
      return <QAEmbed project={project} headers={headers} qaResult={qaResult} />;

    case 'Abnahme':
      return <AbnahmeEmbed project={project} lead={lead} headers={headers} netlify={netlify} />;

    case 'KiReport':
      return (
        <div style={pad}>
          <KiReportPanel projectId={project.id} leadId={project.lead_id} token={token} />
        </div>
      );

    case 'Moodboard':
      return (
        <div style={pad}>
          <MoodboardPanel projectId={project.id} leadId={project.lead_id} token={token} />
        </div>
      );

    case 'QmCheckliste':
      return <QmChecklisteEmbed project={project} headers={headers} />;

    case 'KiQaScan':
      return <QAEmbed project={project} headers={headers} qaResult={qaResult} />;

    case 'GbpQr':
      return <GbpQrEmbed project={project} headers={headers} />;

    case 'Trustpilot':
      return <TrustpilotEmbed project={project} />;

    case 'WebsiteVergleich':
      return <WebsiteVergleichEmbed project={project} headers={headers} />;

    case 'Upsell':
      return <UpsellEmbed />;

    case 'LiveDaten':
      return <LiveDatenEmbed project={project} />;

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

function SitemapEditorEmbed({ pages, leadId, headers, onReload }) {
  const [selectedId, setSelectedId] = useState(null);
  const [addOpen, setAddOpen]       = useState(false);
  const [addName, setAddName]       = useState('');
  const [addType, setAddType]       = useState('info');
  const [addParent, setAddParent]   = useState('');
  const [saving, setSaving]         = useState(false);
  const [editField, setEditField]   = useState(null); // { field, value }

  const contentPages = pages.filter(p => !p.ist_pflichtseite);
  const pflichtPages = pages.filter(p => p.ist_pflichtseite);
  const allPages     = [...contentPages, ...pflichtPages];
  const selected     = allPages.find(p => p.id === selectedId);

  const PAGE_TYPES = ['startseite', 'leistung', 'info', 'vertrauen', 'conversion', 'rechtlich'];
  const STATUSES = [
    { value: 'geplant',      label: 'Geplant',       color: 'var(--text-tertiary)',       bg: 'var(--bg-elevated)' },
    { value: 'in_arbeit',    label: 'In Arbeit',     color: '#854D0E',                    bg: '#FEF9C3' },
    { value: 'entwurf',      label: 'Entwurf',       color: '#7c3aed',                    bg: '#f3e8ff' },
    { value: 'review',       label: 'Zur Pruefung',  color: '#008EAA',                    bg: '#E6F6FA' },
    { value: 'freigegeben',  label: 'Freigegeben',   color: '#059669',                    bg: '#dcfce7' },
  ];

  const makeSlug = (name) => name.toLowerCase().replace(/[äa]/g,'ae').replace(/[öo]/g,'oe').replace(/[üu]/g,'ue').replace(/ß/g,'ss').replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
  const pagePath = (p) => {
    if (!p) return '/';
    const slug = makeSlug(p.page_name);
    if (p.page_type === 'startseite') return '/';
    if (p.parent_id) {
      const parent = allPages.find(pp => pp.id === p.parent_id);
      return parent ? `/${makeSlug(parent.page_name)}/${slug}` : `/${slug}`;
    }
    return `/${slug}`;
  };

  const jsonHeaders = { ...headers, 'Content-Type': 'application/json' };

  const savePage = async (id, data) => {
    setSaving(true);
    await fetch(`${API_BASE_URL}/api/sitemap/pages/${id}`, { method: 'PUT', headers: jsonHeaders, body: JSON.stringify(data) });
    setSaving(false);
    setEditField(null);
    onReload();
  };

  const deletePage = async (id) => {
    if (selectedId === id) setSelectedId(null);
    await fetch(`${API_BASE_URL}/api/sitemap/pages/${id}`, { method: 'DELETE', headers });
    onReload();
  };

  const addPage = async () => {
    if (!addName.trim()) return;
    setSaving(true);
    await fetch(`${API_BASE_URL}/api/sitemap/${leadId}/pages`, {
      method: 'POST', headers: jsonHeaders,
      body: JSON.stringify({ page_name: addName.trim(), page_type: addType, parent_id: addParent ? Number(addParent) : null, position: contentPages.length }),
    });
    setAddName(''); setAddType('info'); setAddParent(''); setAddOpen(false);
    setSaving(false);
    onReload();
  };

  const moveUp = async (idx) => {
    if (idx === 0) return;
    const reordered = [...contentPages];
    [reordered[idx - 1], reordered[idx]] = [reordered[idx], reordered[idx - 1]];
    await fetch(`${API_BASE_URL}/api/sitemap/${leadId}/reorder`, {
      method: 'PUT', headers: jsonHeaders,
      body: JSON.stringify(reordered.map((p, i) => ({ id: p.id, position: i, parent_id: p.parent_id || null }))),
    });
    onReload();
  };

  const moveDown = async (idx) => {
    if (idx >= contentPages.length - 1) return;
    const reordered = [...contentPages];
    [reordered[idx], reordered[idx + 1]] = [reordered[idx + 1], reordered[idx]];
    await fetch(`${API_BASE_URL}/api/sitemap/${leadId}/reorder`, {
      method: 'PUT', headers: jsonHeaders,
      body: JSON.stringify(reordered.map((p, i) => ({ id: p.id, position: i, parent_id: p.parent_id || null }))),
    });
    onReload();
  };

  const uploadTemplate = async (pageId, file) => {
    const text = await file.text();
    await savePage(pageId, { mockup_html: text });
  };

  const statusOf = (s) => STATUSES.find(st => st.value === s) || STATUSES[0];
  const inputStyle = { width: '100%', padding: '7px 10px', fontSize: 12, border: '1px solid var(--border-light)', borderRadius: 6, background: 'var(--bg-app)', color: 'var(--text-primary)', fontFamily: 'var(--font-sans)', outline: 'none', boxSizing: 'border-box' };
  const btnSm = { padding: '4px 8px', fontSize: 11, border: 'none', borderRadius: 4, cursor: 'pointer', fontFamily: 'var(--font-sans)' };

  return (
    <div style={{ display: 'flex', minHeight: 480 }}>

      {/* ── Linke Spalte: Seitenliste ── */}
      <div style={{ width: 300, borderRight: '1px solid var(--border-light)', display: 'flex', flexDirection: 'column', flexShrink: 0 }}>
        <div style={{ padding: '14px 16px', borderBottom: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)' }}>{allPages.length} Seiten</span>
          <button onClick={() => setAddOpen(!addOpen)} style={{ ...btnSm, background: 'var(--brand-primary)', color: '#fff', fontWeight: 700, padding: '5px 12px' }}>+ Neu</button>
        </div>

        {addOpen && (
          <div style={{ padding: 12, borderBottom: '1px solid var(--border-light)', background: 'var(--bg-app)', display: 'flex', flexDirection: 'column', gap: 8 }}>
            <input value={addName} onChange={e => setAddName(e.target.value)} placeholder="Seitenname..." style={inputStyle} autoFocus onKeyDown={e => e.key === 'Enter' && addPage()} />
            <div style={{ display: 'flex', gap: 6 }}>
              <select value={addType} onChange={e => setAddType(e.target.value)} style={{ ...inputStyle, flex: 1 }}>
                {PAGE_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
              <select value={addParent} onChange={e => setAddParent(e.target.value)} style={{ ...inputStyle, flex: 1 }}>
                <option value="">Hauptseite</option>
                {contentPages.map(p => <option key={p.id} value={p.id}>↳ {p.page_name}</option>)}
              </select>
            </div>
            <div style={{ display: 'flex', gap: 6 }}>
              <button onClick={addPage} disabled={saving || !addName.trim()} style={{ ...btnSm, background: '#059669', color: '#fff', fontWeight: 700, padding: '5px 14px' }}>Anlegen</button>
              <button onClick={() => setAddOpen(false)} style={{ ...btnSm, background: 'var(--border-light)', color: 'var(--text-secondary)' }}>Abb.</button>
            </div>
          </div>
        )}

        <div style={{ flex: 1, overflowY: 'auto' }}>
          {contentPages.map((p, idx) => {
            const st = statusOf(p.status);
            const isSel = selectedId === p.id;
            return (
              <div key={p.id} onClick={() => setSelectedId(p.id)} style={{
                padding: '10px 14px', cursor: 'pointer', borderBottom: '1px solid var(--border-light)',
                background: isSel ? `${st.bg}` : 'transparent',
                borderLeft: isSel ? `3px solid ${st.color}` : '3px solid transparent',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                  {p.parent_id && <span style={{ fontSize: 9, color: 'var(--text-tertiary)' }}>↳</span>}
                  <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.page_name}</span>
                  <div style={{ display: 'flex', gap: 2, flexShrink: 0 }}>
                    <button onClick={e => { e.stopPropagation(); moveUp(idx); }} disabled={idx === 0} style={{ ...btnSm, background: 'transparent', color: idx === 0 ? 'var(--border-light)' : 'var(--text-tertiary)', fontSize: 12, padding: '2px 4px' }}>↑</button>
                    <button onClick={e => { e.stopPropagation(); moveDown(idx); }} disabled={idx >= contentPages.length - 1} style={{ ...btnSm, background: 'transparent', color: idx >= contentPages.length - 1 ? 'var(--border-light)' : 'var(--text-tertiary)', fontSize: 12, padding: '2px 4px' }}>↓</button>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ fontSize: 10, color: 'var(--text-tertiary)', fontFamily: 'monospace' }}>{pagePath(p)}</span>
                  <span style={{ marginLeft: 'auto', fontSize: 9, padding: '1px 6px', borderRadius: 99, background: st.bg, color: st.color, fontWeight: 600, flexShrink: 0 }}>{st.label}</span>
                </div>
              </div>
            );
          })}

          {pflichtPages.length > 0 && (
            <>
              <div style={{ padding: '8px 14px', fontSize: 9, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', borderBottom: '1px solid var(--border-light)', background: 'var(--bg-app)' }}>Pflichtseiten</div>
              {pflichtPages.map(p => (
                <div key={p.id} onClick={() => setSelectedId(p.id)} style={{
                  padding: '8px 14px', cursor: 'pointer', borderBottom: '1px solid var(--border-light)',
                  background: selectedId === p.id ? 'var(--bg-app)' : 'transparent', opacity: 0.7,
                }}>
                  <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{p.page_name} 🔒</div>
                  <div style={{ fontSize: 10, color: 'var(--text-tertiary)', fontFamily: 'monospace' }}>{pagePath(p)}</div>
                </div>
              ))}
            </>
          )}
        </div>
      </div>

      {/* ── Rechte Spalte: Detail-Panel ── */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {selected ? (
          <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
              <div>
                <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>{selected.page_name}</div>
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)', fontFamily: 'monospace', marginTop: 2 }}>{pagePath(selected)}</div>
              </div>
              {!selected.ist_pflichtseite && (
                <button onClick={() => deletePage(selected.id)} style={{ ...btnSm, color: 'var(--status-danger-text)', background: 'var(--status-danger-bg)', padding: '5px 12px' }}>Loeschen</button>
              )}
            </div>

            {/* Status */}
            <div>
              <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 6 }}>Status</div>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {STATUSES.map(st => (
                  <button key={st.value} onClick={() => savePage(selected.id, { status: st.value })}
                    style={{
                      padding: '6px 14px', borderRadius: 99, fontSize: 11, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)',
                      background: selected.status === st.value ? st.color : st.bg,
                      color: selected.status === st.value ? '#fff' : st.color,
                      border: `1px solid ${st.color}`, transition: 'all .15s',
                    }}>
                    {st.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Felder-Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 20px' }}>
              {/* Seitenname */}
              <div>
                <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 4 }}>Seitenname</div>
                {editField?.field === 'page_name' ? (
                  <div style={{ display: 'flex', gap: 4 }}>
                    <input value={editField.value} onChange={e => setEditField({ ...editField, value: e.target.value })} style={inputStyle} autoFocus onKeyDown={e => e.key === 'Enter' && savePage(selected.id, { page_name: editField.value })} />
                    <button onClick={() => savePage(selected.id, { page_name: editField.value })} style={{ ...btnSm, background: '#059669', color: '#fff' }}>✓</button>
                  </div>
                ) : (
                  <div onClick={() => !selected.ist_pflichtseite && setEditField({ field: 'page_name', value: selected.page_name })} style={{ fontSize: 13, color: 'var(--text-primary)', cursor: selected.ist_pflichtseite ? 'default' : 'pointer', padding: '4px 0' }}>{selected.page_name}</div>
                )}
              </div>

              {/* Seitentyp */}
              <div>
                <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 4 }}>Typ</div>
                <select value={selected.page_type} onChange={e => savePage(selected.id, { page_type: e.target.value })} disabled={selected.ist_pflichtseite} style={inputStyle}>
                  {PAGE_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>

              {/* Keyword */}
              <div>
                <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 4 }}>Ziel-Keyword</div>
                {editField?.field === 'ziel_keyword' ? (
                  <div style={{ display: 'flex', gap: 4 }}>
                    <input value={editField.value} onChange={e => setEditField({ ...editField, value: e.target.value })} style={inputStyle} autoFocus onKeyDown={e => e.key === 'Enter' && savePage(selected.id, { ziel_keyword: editField.value })} />
                    <button onClick={() => savePage(selected.id, { ziel_keyword: editField.value })} style={{ ...btnSm, background: '#059669', color: '#fff' }}>✓</button>
                  </div>
                ) : (
                  <div onClick={() => setEditField({ field: 'ziel_keyword', value: selected.ziel_keyword || '' })} style={{ fontSize: 12, color: selected.ziel_keyword ? 'var(--text-primary)' : 'var(--text-tertiary)', cursor: 'pointer', padding: '4px 0', fontStyle: selected.ziel_keyword ? 'normal' : 'italic' }}>{selected.ziel_keyword || 'Klicken zum Setzen...'}</div>
                )}
              </div>

              {/* CTA */}
              <div>
                <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 4 }}>CTA</div>
                {editField?.field === 'cta_text' ? (
                  <div style={{ display: 'flex', gap: 4 }}>
                    <input value={editField.value} onChange={e => setEditField({ ...editField, value: e.target.value })} style={inputStyle} autoFocus onKeyDown={e => e.key === 'Enter' && savePage(selected.id, { cta_text: editField.value })} />
                    <button onClick={() => savePage(selected.id, { cta_text: editField.value })} style={{ ...btnSm, background: '#059669', color: '#fff' }}>✓</button>
                  </div>
                ) : (
                  <div onClick={() => setEditField({ field: 'cta_text', value: selected.cta_text || '' })} style={{ fontSize: 12, color: selected.cta_text ? 'var(--text-primary)' : 'var(--text-tertiary)', cursor: 'pointer', padding: '4px 0', fontStyle: selected.cta_text ? 'normal' : 'italic' }}>{selected.cta_text || 'Klicken zum Setzen...'}</div>
                )}
              </div>
            </div>

            {/* Zweck */}
            <div>
              <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 4 }}>Zweck / Beschreibung</div>
              {editField?.field === 'zweck' ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  <textarea value={editField.value} onChange={e => setEditField({ ...editField, value: e.target.value })} rows={3} style={{ ...inputStyle, resize: 'vertical' }} autoFocus />
                  <div style={{ display: 'flex', gap: 4 }}>
                    <button onClick={() => savePage(selected.id, { zweck: editField.value })} style={{ ...btnSm, background: '#059669', color: '#fff', fontWeight: 700 }}>Speichern</button>
                    <button onClick={() => setEditField(null)} style={{ ...btnSm, background: 'var(--border-light)', color: 'var(--text-secondary)' }}>Abb.</button>
                  </div>
                </div>
              ) : (
                <div onClick={() => setEditField({ field: 'zweck', value: selected.zweck || '' })} style={{ fontSize: 12, color: selected.zweck ? 'var(--text-secondary)' : 'var(--text-tertiary)', cursor: 'pointer', lineHeight: 1.5, padding: '4px 0', fontStyle: selected.zweck ? 'normal' : 'italic' }}>{selected.zweck || 'Klicken zum Beschreiben...'}</div>
              )}
            </div>

            {/* Notizen */}
            <div>
              <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 4 }}>Notizen</div>
              {editField?.field === 'notizen' ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  <textarea value={editField.value} onChange={e => setEditField({ ...editField, value: e.target.value })} rows={2} style={{ ...inputStyle, resize: 'vertical' }} autoFocus />
                  <div style={{ display: 'flex', gap: 4 }}>
                    <button onClick={() => savePage(selected.id, { notizen: editField.value })} style={{ ...btnSm, background: '#059669', color: '#fff', fontWeight: 700 }}>Speichern</button>
                    <button onClick={() => setEditField(null)} style={{ ...btnSm, background: 'var(--border-light)', color: 'var(--text-secondary)' }}>Abb.</button>
                  </div>
                </div>
              ) : (
                <div onClick={() => setEditField({ field: 'notizen', value: selected.notizen || '' })} style={{ fontSize: 12, color: selected.notizen ? 'var(--text-secondary)' : 'var(--text-tertiary)', cursor: 'pointer', lineHeight: 1.5, padding: '4px 0', fontStyle: selected.notizen ? 'normal' : 'italic' }}>{selected.notizen || 'Klicken fuer Notizen...'}</div>
              )}
            </div>

            {/* Template Upload */}
            <div>
              <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 6 }}>HTML-Template</div>
              {selected.mockup_html ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <div style={{ fontSize: 11, color: 'var(--status-success-text)', background: 'var(--status-success-bg)', padding: '6px 10px', borderRadius: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span>✓</span> Template vorhanden ({Math.round(selected.mockup_html.length / 1024)} KB)
                  </div>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <label style={{ ...btnSm, background: 'var(--brand-primary)', color: '#fff', fontWeight: 600, padding: '5px 14px', cursor: 'pointer', display: 'inline-block' }}>
                      Ersetzen
                      <input type="file" accept=".html,.htm" style={{ display: 'none' }} onChange={e => e.target.files[0] && uploadTemplate(selected.id, e.target.files[0])} />
                    </label>
                    <button onClick={() => savePage(selected.id, { mockup_html: '' })} style={{ ...btnSm, color: 'var(--status-danger-text)', background: 'var(--status-danger-bg)', padding: '5px 12px' }}>Entfernen</button>
                  </div>
                </div>
              ) : (
                <label style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                  padding: '16px 20px', border: '2px dashed var(--border-light)', borderRadius: 8,
                  cursor: 'pointer', background: 'var(--bg-app)', color: 'var(--text-tertiary)', fontSize: 12,
                  transition: 'border-color .2s',
                }}>
                  <span style={{ fontSize: 20 }}>📄</span>
                  HTML-Template hochladen (.html)
                  <input type="file" accept=".html,.htm" style={{ display: 'none' }} onChange={e => e.target.files[0] && uploadTemplate(selected.id, e.target.files[0])} />
                </label>
              )}
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', padding: 40 }}>
            <div style={{ textAlign: 'center', color: 'var(--text-tertiary)' }}>
              <div style={{ fontSize: 32, marginBottom: 8 }}>🗺️</div>
              <div style={{ fontSize: 13 }}>Seite auswaehlen zum Bearbeiten</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function BriefingUnternehmenEmbed({ lead, localBriefing, reloadBriefing }) {
  const [editing, setEditing] = useState(false);
  const b = localBriefing;
  const hasDaten = !!(b?.gewerk || b?.leistungen || b?.usp);

  if (editing || !hasDaten) {
    return (
      <div style={{ padding: '20px 24px' }}>
        {hasDaten && (
          <button onClick={() => setEditing(false)}
            style={{ marginBottom: 12, padding: '5px 14px', borderRadius: 6, border: '1px solid var(--border-light)', background: 'var(--bg-surface)', color: 'var(--text-secondary)', fontSize: 11, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
            Zurueck zur Uebersicht
          </button>
        )}
        <BriefingWizard
          leadId={lead.id}
          leadData={localBriefing}
          onClose={() => { if (hasDaten) setEditing(false); }}
          onComplete={() => { reloadBriefing(); setEditing(false); }}
          embedded
        />
      </div>
    );
  }

  const rows = [
    b.gewerk        && { label: 'Gewerk / Branche', value: b.gewerk },
    b.wz_title      && { label: 'WZ-Code',          value: `${b.wz_code} — ${b.wz_title}` },
    b.leistungen    && { label: 'Leistungen',        value: b.leistungen },
    b.einzugsgebiet && { label: 'Einzugsgebiet',     value: b.einzugsgebiet },
    b.usp           && { label: 'USP',               value: b.usp },
    b.zielgruppe    && { label: 'Zielgruppe',        value: typeof b.zielgruppe === 'string' ? b.zielgruppe : b.zielgruppe?.primaer || '' },
    b.farben        && { label: 'Farben',            value: b.farben },
    b.stil          && { label: 'Stil',              value: b.stil },
    b.mitbewerber   && { label: 'Mitbewerber',       value: b.mitbewerber },
    b.vorbilder     && { label: 'Vorbilder',         value: b.vorbilder },
    b.sonstige_hinweise && { label: 'Hinweise',      value: b.sonstige_hinweise },
  ].filter(Boolean);

  return (
    <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>Briefing-Daten</div>
        <button onClick={() => setEditing(true)}
          style={{ padding: '6px 16px', borderRadius: 6, border: '1px solid var(--brand-primary)', background: 'transparent', color: 'var(--brand-primary)', fontSize: 11, fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
          Bearbeiten
        </button>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px 20px' }}>
        {rows.map(({ label, value }) => (
          <div key={label}>
            <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 3 }}>{label}</div>
            <div style={{ fontSize: 12, color: 'var(--text-primary)', lineHeight: 1.5, whiteSpace: 'pre-line' }}>{value}</div>
          </div>
        ))}
      </div>
      {(b.logo_vorhanden || b.fotos_vorhanden) && (
        <div style={{ display: 'flex', gap: 12, marginTop: 4 }}>
          {b.logo_vorhanden && <span style={{ fontSize: 11, padding: '3px 10px', borderRadius: 99, background: '#dcfce7', color: '#059669', fontWeight: 600 }}>Logo vorhanden</span>}
          {b.fotos_vorhanden && <span style={{ fontSize: 11, padding: '3px 10px', borderRadius: 99, background: '#dcfce7', color: '#059669', fontWeight: 600 }}>Fotos vorhanden</span>}
        </div>
      )}
    </div>
  );
}

function SitemapKiVorschlag({ project, leadId, headers, onGenerated }) {
  const [loading, setLoading]       = useState(false);
  const [done, setDone]             = useState(false);
  const [error, setError]           = useState(null);
  const [gateBlocked, setGateBlocked] = useState(false);

  const generate = async () => {
    if (!leadId) { setError('Keine Lead-ID verfuegbar.'); return; }
    setLoading(true); setError(null); setGateBlocked(false);
    try {
      const res = await fetch(`${API_BASE_URL}/api/sitemap/${leadId}/generate`, { method: 'POST', headers });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        const detail = errData.detail;
        if (detail?.code === 'BRIEFING_NOT_APPROVED') { setGateBlocked(true); return; }
        throw new Error(typeof detail === 'string' ? detail : detail?.message || `HTTP ${res.status}`);
      }
      setDone(true);
      if (onGenerated) onGenerated();
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  if (done) return (
    <div style={{ padding: '12px 18px', background: 'var(--status-success-bg)', borderRadius: 8, fontSize: 13, color: 'var(--status-success-text)', marginBottom: 12 }}>
      Sitemap wurde generiert — wird geladen...
    </div>
  );

  if (gateBlocked) return (
    <div style={{ margin: '0 20px 16px', padding: '14px 18px', background: 'rgba(217,119,6,.06)', border: '1px solid rgba(217,119,6,.3)', borderRadius: 10, display: 'flex', alignItems: 'center', gap: 14 }}>
      <span style={{ fontSize: 28, flexShrink: 0 }}>🔒</span>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 3 }}>Briefing noch nicht freigegeben</div>
        <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Der Kunde hat das Briefing noch nicht freigegeben. Sobald die Freigabe erteilt wurde, kann die KI-Sitemap erstellt werden.</div>
      </div>
      <button onClick={generate} disabled={loading}
        style={{ padding: '9px 18px', borderRadius: 8, border: '1px solid rgba(217,119,6,.4)', background: 'transparent', color: '#d97706', fontSize: 12, fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-sans)', flexShrink: 0 }}>
        Erneut prüfen
      </button>
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

function AuditEmbed({ project, lead, headers, latestAudit, onAuditComplete }) {
  const [running, setRunning]   = useState(false);
  const [progress, setProgress] = useState('');
  const [error, setError]       = useState('');
  const [result, setResult]     = useState(latestAudit || null);

  // Sync from prop when parent loads audit data
  useEffect(() => { if (latestAudit) setResult(latestAudit); }, [latestAudit]);

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
        if (poll.status === 'completed') { clearInterval(iv); setResult(poll); if (onAuditComplete) onAuditComplete(poll); setProgress(''); setRunning(false); break; }
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

function NetlifyEmbed({ project, headers }) {
  const [status, setStatus]           = useState(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const [token, setToken]             = useState('');
  const [savingToken, setSavingToken] = useState(false);
  const [creating, setCreating]       = useState(false);
  const [deployHtml, setDeployHtml]   = useState('');
  const [deploying, setDeploying]     = useState(false);
  const [deployResult, setDeployResult] = useState(null);
  const [domain, setDomain]           = useState('');
  const [dnsGuide, setDnsGuide]       = useState(null);
  const [error, setError]             = useState('');

  const inputStyle = { width:'100%', padding:'9px 12px', fontSize:13, border:'1px solid var(--border-light)', borderRadius:8, background:'var(--bg-app)', color:'var(--text-primary)', fontFamily:'var(--font-sans)', boxSizing:'border-box' };
  const btnStyle = (disabled) => ({ padding:'9px 20px', borderRadius:8, border:'none', background: disabled ? 'var(--border-medium)' : 'var(--brand-primary)', color:'#fff', fontSize:13, fontWeight:700, cursor: disabled ? 'not-allowed' : 'pointer', fontFamily:'var(--font-sans)', display:'flex', alignItems:'center', gap:6 });
  const cardStyle = { background:'var(--bg-surface)', border:'1px solid var(--border-light)', borderRadius:10, padding:16, display:'flex', flexDirection:'column', gap:10 };

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/projects/${project.id}/netlify/status`, { headers })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setStatus(d); })
      .catch(() => {})
      .finally(() => setStatusLoading(false));
  }, []); // eslint-disable-line

  if (statusLoading) return <Spinner />;

  return (
    <div style={{ padding:'20px 24px', display:'flex', flexDirection:'column', gap:16 }}>
      {error && <div style={{ fontSize:12, color:'var(--status-danger-text)', background:'var(--status-danger-bg)', padding:'8px 12px', borderRadius:6 }}>{error}</div>}

      {/* 1: Token */}
      <div style={cardStyle}>
        <div style={{ fontSize:13, fontWeight:700, color:'var(--text-primary)' }}>
          {status?.has_token ? 'Netlify-Token gespeichert' : '1. Netlify API-Token des Kunden'}
        </div>
        {!status?.has_token && (<>
          <div style={{ fontSize:12, color:'var(--text-secondary)' }}>
            Kunde erstellt Token unter: <a href="https://app.netlify.com/user/applications" target="_blank" rel="noreferrer" style={{ color:'var(--brand-primary)' }}>app.netlify.com → Personal access tokens</a>
          </div>
          <div style={{ display:'flex', gap:8 }}>
            <input type="password" value={token} onChange={e => setToken(e.target.value)} placeholder="netlify_pat_XXXXXXXXXX" style={{ ...inputStyle, flex:1 }} />
            <button onClick={async () => {
              if (!token.trim()) return; setSavingToken(true); setError('');
              try {
                const r = await fetch(`${API_BASE_URL}/api/projects/${project.id}/netlify/save-token`, { method:'POST', headers, body: JSON.stringify({ token: token.trim() }) });
                if (!r.ok) throw new Error((await r.json().catch(()=>({}))).detail || 'Fehler');
                setStatus(s => ({ ...s, has_token: true })); setToken('');
              } catch (e) { setError(e.message); } finally { setSavingToken(false); }
            }} disabled={savingToken || !token.trim()} style={btnStyle(savingToken || !token.trim())}>
              {savingToken ? 'Speichert...' : 'Speichern'}
            </button>
          </div>
        </>)}
      </div>

      {/* 2: Site anlegen */}
      {status?.has_token && (
        <div style={cardStyle}>
          <div style={{ fontSize:13, fontWeight:700, color:'var(--text-primary)' }}>
            {status?.site_id ? 'Netlify-Site angelegt' : '2. Site auf Kunden-Account anlegen'}
          </div>
          {status?.site_id
            ? <a href={status.url} target="_blank" rel="noreferrer" style={{ fontSize:12, color:'var(--brand-primary)' }}>{status.url}</a>
            : <button onClick={async () => {
                setCreating(true); setError('');
                try {
                  const r = await fetch(`${API_BASE_URL}/api/projects/${project.id}/netlify/customer-create-site`, { method:'POST', headers });
                  if (!r.ok) throw new Error((await r.json().catch(()=>({}))).detail || 'Fehler');
                  const d = await r.json(); setStatus(s => ({ ...s, site_id: d.site_id, url: d.url }));
                } catch (e) { setError(e.message); } finally { setCreating(false); }
              }} disabled={creating} style={btnStyle(creating)}>
                {creating ? 'Anlegen...' : 'Site anlegen'}
              </button>
          }
        </div>
      )}

      {/* 3: Deploy */}
      {status?.site_id && (
        <div style={cardStyle}>
          <div style={{ fontSize:13, fontWeight:700, color:'var(--text-primary)' }}>3. HTML deployen</div>
          <textarea value={deployHtml} onChange={e => setDeployHtml(e.target.value)}
            placeholder={'Nur den Body-Inhalt einfügen (kein DOCTYPE nötig — wird automatisch ergänzt)'} rows={5}
            style={{ ...inputStyle, resize:'vertical', fontFamily:'monospace', fontSize:11 }} />
          <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
            Nur den Body-Inhalt aus GrapesJS einfügen. DOCTYPE, head und CSS-Link
            werden automatisch vom System ergänzt.
          </div>
          <button onClick={async () => {
            if (!deployHtml.trim()) { setError('HTML fehlt'); return; }
            setDeploying(true); setError('');
            try {
              const r = await fetch(`${API_BASE_URL}/api/projects/${project.id}/netlify/customer-deploy`, { method:'POST', headers, body: JSON.stringify({ html: deployHtml }) });
              if (!r.ok) throw new Error((await r.json().catch(()=>({}))).detail || 'Fehler');
              setDeployResult(await r.json());
            } catch (e) { setError(e.message); } finally { setDeploying(false); }
          }} disabled={deploying || !deployHtml.trim()} style={btnStyle(deploying || !deployHtml.trim())}>
            {deploying ? (<><span style={{ width:12, height:12, border:'2px solid rgba(255,255,255,.3)', borderTopColor:'#fff', borderRadius:'50%', animation:'spin .8s linear infinite', display:'inline-block' }} />Deploy laeuft...</>) : 'Jetzt deployen'}
          </button>
          {deployResult && (
            <div style={{ background:'var(--status-success-bg)', borderRadius:8, padding:'10px 14px', fontSize:13 }}>
              Deployed: <a href={deployResult.deploy_url} target="_blank" rel="noreferrer" style={{ color:'var(--status-success-text)', fontWeight:600 }}>{deployResult.deploy_url}</a>
            </div>
          )}
        </div>
      )}

      {/* 3b: Multi-Page Deploy — alle Sitemap-Seiten auf einmal */}
      {status?.site_id && (
        <div style={cardStyle}>
          <div style={{ fontSize:13, fontWeight:700, color:'var(--text-primary)' }}>3b. Alle Seiten deployen</div>
          <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
            Deployt alle Seiten aus dem Seitenmanager auf einmal — jede Seite als eigene URL.
            Voraussetzung: Seiten im GrapesJS-Editor gespeichert.
          </div>
          <button onClick={async () => {
            setDeploying(true); setError('');
            try {
              const r = await fetch(`${API_BASE_URL}/api/projects/${project.id}/netlify/deploy-all`, { method:'POST', headers });
              if (!r.ok) throw new Error((await r.json().catch(()=>({}))).detail || `HTTP ${r.status}`);
              const d = await r.json();
              setDeployResult(d);
            } catch (e) { setError(e.message); } finally { setDeploying(false); }
          }} disabled={deploying} style={{
            padding: '10px 18px', borderRadius: 8, border: 'none',
            background: deploying ? '#94a3b8' : '#7c3aed',
            color: '#fff', fontSize: 13, fontWeight: 700,
            cursor: deploying ? 'not-allowed' : 'pointer',
            fontFamily: 'var(--font-sans)',
            display: 'inline-flex', alignItems: 'center', gap: 8,
          }}>
            {deploying ? (<><span style={{ width:12, height:12, border:'2px solid rgba(255,255,255,.3)', borderTopColor:'#fff', borderRadius:'50%', animation:'spin .8s linear infinite', display:'inline-block' }} />Deploy laeuft...</>) : 'Alle Seiten deployen'}
          </button>
          {deployResult?.pages_deployed && (
            <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
              <strong>{deployResult.pages_deployed.length} Seiten deployed:</strong>{' '}
              {deployResult.pages_deployed.join(' · ')}
            </div>
          )}
        </div>
      )}

      {/* 4: Domain */}
      {status?.site_id && (
        <div style={cardStyle}>
          <div style={{ fontSize:13, fontWeight:700, color:'var(--text-primary)' }}>4. Eigene Domain verbinden</div>
          <div style={{ display:'flex', gap:8 }}>
            <input value={domain} onChange={e => setDomain(e.target.value)} placeholder="www.kundenwebsite.de" style={{ ...inputStyle, flex:1 }} />
            <button onClick={async () => {
              if (!domain.trim()) return;
              try {
                const r = await fetch(`${API_BASE_URL}/api/projects/${project.id}/netlify/set-domain`, { method:'POST', headers, body: JSON.stringify({ domain: domain.trim() }) });
                if (!r.ok) throw new Error((await r.json().catch(()=>({}))).detail || 'Fehler');
                setDnsGuide(await r.json());
              } catch (e) { setError(e.message); }
            }} disabled={!domain.trim()} style={btnStyle(!domain.trim())}>Verbinden</button>
          </div>
          {dnsGuide && (
            <div style={{ background:'#E6F1FB', border:'1px solid #93c5fd', borderRadius:8, padding:14 }}>
              <div style={{ fontSize:12, fontWeight:700, color:'#185FA5', marginBottom:8 }}>DNS-Eintrag beim Domain-Anbieter setzen:</div>
              {[['Typ','CNAME'],['Name','www'],['Ziel',dnsGuide.cname_target],['TTL','3600']].map(([k,v]) => (
                <div key={k} style={{ display:'flex', gap:16, fontSize:12, padding:'3px 0' }}>
                  <span style={{ width:50, fontWeight:700, color:'#185FA5', flexShrink:0 }}>{k}</span>
                  <span style={{ fontFamily:'monospace' }}>{v}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function DNSEmbed({ project, lead, headers }) {
  const [domain, setDomain]       = useState(lead?.website_url?.replace(/https?:\/\/(www\.)?/,'').split('/')[0] || '');
  const [netlifyUrl, setNetlifyUrl] = useState('');
  const [sent, setSent]           = useState(false);
  const [sending, setSending]     = useState(false);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/projects/${project.id}/netlify/status`, { headers })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d?.url) setNetlifyUrl(d.url.replace('https://', '')); })
      .catch(() => {});
  }, []); // eslint-disable-line

  return (
    <div style={{ padding:'20px 24px', display:'flex', flexDirection:'column', gap:20 }}>
      <div style={{ fontSize:13, color:'var(--text-secondary)', lineHeight:1.7 }}>
        Der Kunde muss bei seinem Domain-Anbieter einen CNAME-Eintrag setzen, der auf die Netlify-URL zeigt. Das kann 24-48 Stunden dauern.
      </div>

      <div style={{ background:'var(--bg-surface)', border:'1px solid var(--border-light)', borderRadius:10, padding:16 }}>
        <div style={{ fontSize:11, fontWeight:700, color:'var(--text-tertiary)', textTransform:'uppercase', letterSpacing:'.07em', marginBottom:6 }}>Netlify-URL (CNAME-Ziel)</div>
        <div style={{ fontFamily:'monospace', fontSize:14, color:'var(--text-primary)', padding:'8px 12px', background:'var(--bg-app)', borderRadius:6 }}>
          {netlifyUrl || '— Erst Schritt 10 (Netlify deploy) abschliessen —'}
        </div>
      </div>

      {netlifyUrl && (
        <div style={{ background:'#E6F1FB', border:'1px solid #93c5fd', borderRadius:10, padding:16 }}>
          <div style={{ fontSize:13, fontWeight:700, color:'#185FA5', marginBottom:12 }}>DNS-Eintrag beim Domain-Anbieter:</div>
          <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13 }}>
            <tbody>
              {[['Typ','CNAME'],['Name','www'],['Ziel',netlifyUrl],['TTL','3600']].map(([k,v]) => (
                <tr key={k}><td style={{ padding:'6px 16px 6px 0', fontWeight:700, color:'#185FA5', width:80 }}>{k}</td><td style={{ padding:'6px 0', fontFamily:'monospace', color:'#1e3a5f' }}>{v}</td></tr>
              ))}
            </tbody>
          </table>
          <div style={{ marginTop:14 }}>
            <div style={{ fontSize:11, fontWeight:700, color:'var(--text-tertiary)', textTransform:'uppercase', letterSpacing:'.07em', marginBottom:6 }}>Domain des Kunden</div>
            <input value={domain} onChange={e => setDomain(e.target.value)} placeholder="www.kundenwebsite.de"
              style={{ width:'100%', padding:'8px 12px', fontSize:13, border:'1px solid var(--border-light)', borderRadius:6, background:'var(--bg-app)', color:'var(--text-primary)', fontFamily:'var(--font-sans)', boxSizing:'border-box' }} />
          </div>
          <button onClick={async () => {
            setSending(true);
            try { await fetch(`${API_BASE_URL}/api/projects/${project.id}/request-approval`, { method:'POST', headers, body: JSON.stringify({ topic:'DNS-Einrichtung', notes:`CNAME: www -> ${netlifyUrl}` }) }); setSent(true); } catch {}
            finally { setSending(false); }
          }} disabled={sending || sent || !domain.trim()}
            style={{ marginTop:12, padding:'9px 18px', borderRadius:8, border:'none', background: sent ? 'var(--status-success-bg)' : '#185FA5', color: sent ? 'var(--status-success-text)' : '#fff', fontSize:12, fontWeight:700, cursor: sent ? 'default' : 'pointer', fontFamily:'var(--font-sans)' }}>
            {sent ? 'Anleitung gesendet' : sending ? 'Sendet...' : 'Anleitung per E-Mail senden'}
          </button>
        </div>
      )}

      <div style={{ background:'var(--bg-surface)', border:'1px solid var(--border-light)', borderRadius:10, padding:16 }}>
        <div style={{ fontSize:13, fontWeight:700, color:'var(--text-primary)', marginBottom:8 }}>Domain-Erreichbarkeit pruefen</div>
        <div style={{ fontSize:12, color:'var(--text-secondary)', marginBottom:10 }}>
          {project.domain_reachable
            ? <span style={{ color:'var(--status-success-text)' }}>Domain ist erreichbar (HTTP {project.domain_status_code})</span>
            : <span style={{ color:'var(--text-tertiary)' }}>Noch nicht erreichbar — DNS-Propagation kann bis zu 48h dauern</span>}
        </div>
        <button onClick={async () => { await fetch(`${API_BASE_URL}/api/projects/${project.id}/domain-check`, { method:'POST', headers }); window.location.reload(); }}
          style={{ padding:'7px 16px', borderRadius:6, border:'1px solid var(--border-light)', background:'var(--bg-surface)', color:'var(--text-secondary)', fontSize:12, cursor:'pointer', fontFamily:'var(--font-sans)' }}>
          Jetzt pruefen
        </button>
      </div>
    </div>
  );
}

function QAEmbed({ project, headers, qaResult: initialResult }) {
  const [result, setResult]   = useState(initialResult || null);
  const [running, setRunning] = useState(false);
  const [error, setError]     = useState('');

  const CHECKS = [
    { key:'ssl', label:'SSL / HTTPS aktiv' },
    { key:'impressum', label:'Impressum vorhanden' },
    { key:'datenschutz', label:'Datenschutz vorhanden' },
    { key:'kontakt', label:'Kontakt-Formular / Telefon' },
    { key:'mobile', label:'Mobile-Ansicht korrekt' },
    { key:'links', label:'Keine defekten Links' },
    { key:'pagespeed', label:'PageSpeed > 70' },
  ];

  const run = async () => {
    setRunning(true); setError('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/projects/${project.id}/qa/run`, { method:'POST', headers });
      const d = await res.json();
      if (!res.ok) throw new Error(d.detail || 'Fehler');
      setResult(d);
    } catch (e) { setError(e.message); }
    finally { setRunning(false); }
  };

  return (
    <div style={{ padding:'20px 24px', display:'flex', flexDirection:'column', gap:16 }}>
      <button onClick={run} disabled={running}
        style={{ alignSelf:'flex-start', padding:'10px 22px', borderRadius:8, border:'none', background: running ? 'var(--border-medium)' : 'var(--brand-primary)', color:'#fff', fontSize:13, fontWeight:700, cursor: running ? 'not-allowed' : 'pointer', fontFamily:'var(--font-sans)', display:'flex', alignItems:'center', gap:8 }}>
        {running ? (<><span style={{ width:14, height:14, border:'2px solid rgba(255,255,255,.3)', borderTopColor:'#fff', borderRadius:'50%', animation:'spin .8s linear infinite', display:'inline-block' }} />QA-Scan laeuft...</>) : result ? 'Erneut scannen' : 'QA-Check starten'}
      </button>
      {error && <div style={{ fontSize:12, color:'var(--status-danger-text)', background:'var(--status-danger-bg)', padding:'8px 12px', borderRadius:6 }}>{error}</div>}
      {result ? (
        <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
          {CHECKS.map(c => {
            const passed = result[c.key] === true || result[c.key] === 'ok';
            const warn = result[c.key] === 'warn';
            return (
              <div key={c.key} style={{ display:'flex', alignItems:'center', gap:12, padding:'10px 14px', background:'var(--bg-surface)', border:'1px solid var(--border-light)', borderRadius:8 }}>
                <span style={{ fontSize:16, flexShrink:0 }}>{passed ? '\u2705' : warn ? '\u26A0\uFE0F' : '\u274C'}</span>
                <span style={{ fontSize:13, color:'var(--text-primary)', flex:1 }}>{c.label}</span>
                {result[c.key + '_detail'] && <span style={{ fontSize:11, color:'var(--text-tertiary)' }}>{result[c.key + '_detail']}</span>}
              </div>
            );
          })}
          {result.ai_summary && (
            <div style={{ marginTop:8, padding:'12px 14px', background:'var(--bg-app)', borderRadius:8, borderLeft:'3px solid var(--brand-primary)', fontSize:12, color:'var(--text-secondary)', lineHeight:1.7 }}>
              {result.ai_summary}
            </div>
          )}
        </div>
      ) : (
        <div style={{ textAlign:'center', padding:'32px 0', color:'var(--text-tertiary)', fontSize:13 }}>
          QA-Scan noch nicht durchgefuehrt. Prueft SSL, Impressum, Datenschutz, Links, Mobile und PageSpeed.
        </div>
      )}
    </div>
  );
}

function AbnahmeEmbed({ project, lead, headers, netlify }) {
  const [confirmed, setConfirmed] = useState(project?.status === 'fertig');
  const [saving, setSaving]       = useState(false);

  const liveUrl = netlify?.url || project?.website_url;

  const goLive = async () => {
    setSaving(true);
    try {
      await fetch(`${API_BASE_URL}/api/projects/${project.id}`, {
        method:'PUT', headers,
        body: JSON.stringify({ status:'fertig', go_live_date: new Date().toISOString().slice(0,10) }),
      });
      setConfirmed(true);
    } catch {}
    finally { setSaving(false); }
  };

  return (
    <div style={{ padding:'20px 24px', display:'flex', flexDirection:'column', gap:20 }}>
      {confirmed ? (
        <div style={{ textAlign:'center', padding:'32px 20px' }}>
          <div style={{ fontSize:56, marginBottom:12 }}>🎉</div>
          <div style={{ fontSize:22, fontWeight:800, color:'var(--text-primary)', marginBottom:8 }}>Website ist live!</div>
          {liveUrl && <a href={liveUrl} target="_blank" rel="noreferrer" style={{ fontSize:14, color:'var(--brand-primary)', fontWeight:600 }}>{liveUrl}</a>}
          <div style={{ marginTop:24, display:'flex', flexDirection:'column', gap:10, alignItems:'center' }}>
            <div style={{ fontSize:13, color:'var(--text-secondary)', fontWeight:600 }}>Naechste Schritte:</div>
            {['Trustpilot-Bewertung anfragen', 'Google Business Profil aktualisieren', 'Google Analytics einrichten', 'Vorher/Nachher-Screenshot fuer Portfolio'].map(s => (
              <div key={s} style={{ fontSize:13, color:'var(--text-secondary)' }}>{s}</div>
            ))}
          </div>
        </div>
      ) : (<>
        <div>
          <div style={{ fontSize:13, fontWeight:700, color:'var(--text-primary)', marginBottom:12 }}>Vor der Abnahme pruefen:</div>
          {[
            { label:'QA-Check bestanden', done: !!project?.qa_result },
            { label:'Domain erreichbar', done: !!project?.domain_reachable },
            { label:'Netlify deployed', done: !!netlify?.url },
            { label:'Kunde informiert', done: false },
          ].map(c => (
            <div key={c.label} style={{ display:'flex', alignItems:'center', gap:10, padding:'8px 0', borderBottom:'1px solid var(--border-light)' }}>
              <span style={{ fontSize:16 }}>{c.done ? '\u2705' : '\u25CB'}</span>
              <span style={{ fontSize:13, color: c.done ? 'var(--text-primary)' : 'var(--text-tertiary)' }}>{c.label}</span>
            </div>
          ))}
        </div>
        {liveUrl && (
          <div style={{ background:'var(--bg-surface)', border:'1px solid var(--border-light)', borderRadius:10, padding:14 }}>
            <div style={{ fontSize:12, color:'var(--text-tertiary)', marginBottom:4 }}>Live-URL</div>
            <a href={liveUrl} target="_blank" rel="noreferrer" style={{ fontSize:14, color:'var(--brand-primary)', fontWeight:600 }}>{liveUrl}</a>
          </div>
        )}
        <button onClick={goLive} disabled={saving}
          style={{ padding:'14px 0', borderRadius:10, border:'none', background: saving ? 'var(--border-medium)' : '#059669', color:'#fff', fontSize:15, fontWeight:700, cursor: saving ? 'not-allowed' : 'pointer', fontFamily:'var(--font-sans)' }}>
          {saving ? 'Wird gespeichert...' : 'Go Live — Projekt abschliessen'}
        </button>
        <div style={{ fontSize:11, color:'var(--text-tertiary)', textAlign:'center' }}>
          Das Projekt wird als Fertig markiert.
        </div>
      </>)}
    </div>
  );
}

// ── QM-Checkliste ─────────────────────────────────────────────────────────────
function QmChecklisteEmbed({ project, headers }) {
  const ITEMS = [
    { id: 'speed',     label: 'PageSpeed > 80 (Mobile + Desktop)' },
    { id: 'links',     label: 'Alle Links funktionieren (kein 404)' },
    { id: 'mobile',    label: 'Mobile Ansicht korrekt auf iOS & Android' },
    { id: 'impressum', label: 'Impressum + Datenschutz vorhanden' },
    { id: 'ssl',       label: 'SSL-Zertifikat aktiv (https://)' },
    { id: 'forms',     label: 'Kontaktformular sendet korrekt' },
    { id: 'analytics', label: 'Google Analytics / GA4 eingebunden' },
    { id: 'favicon',   label: 'Favicon + Meta-Titel korrekt' },
    { id: 'maps',      label: 'Google Maps / Adresse stimmt' },
    { id: 'social',    label: 'Social Media Links korrekt' },
  ];
  const [checked, setChecked] = useState(() => {
    try { return JSON.parse(project?.gbp_checklist_json || '{}'); } catch { return {}; }
  });

  const toggle = (id) => {
    const next = { ...checked, [id]: !checked[id] };
    setChecked(next);
    fetch(`${API_BASE_URL}/api/projects/${project.id}/gbp-checklist`, {
      method: 'PATCH', headers,
      body: JSON.stringify({ checked: next }),
    }).catch(() => {});
  };

  const done = ITEMS.filter(i => checked[i.id]).length;
  return (
    <div style={{ padding: '20px 24px' }}>
      <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 16 }}>
        {done}/{ITEMS.length} Punkte abgehakt
        <div style={{ marginTop: 6, height: 4, background: 'var(--border-light)', borderRadius: 2, overflow: 'hidden' }}>
          <div style={{ height: '100%', width: `${Math.round(done / ITEMS.length * 100)}%`, background: '#059669', borderRadius: 2, transition: 'width .3s' }} />
        </div>
      </div>
      {ITEMS.map(item => (
        <label key={item.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 0', borderBottom: '1px solid var(--border-light)', cursor: 'pointer' }}>
          <input type="checkbox" checked={!!checked[item.id]} onChange={() => toggle(item.id)} style={{ width: 16, height: 16, cursor: 'pointer', accentColor: '#059669' }} />
          <span style={{ fontSize: 13, color: checked[item.id] ? 'var(--text-tertiary)' : 'var(--text-primary)', textDecoration: checked[item.id] ? 'line-through' : 'none' }}>
            {item.label}
          </span>
        </label>
      ))}
    </div>
  );
}

// ── GBP + QR-Code ─────────────────────────────────────────────────────────────
function GbpQrEmbed({ project, headers }) {
  const [gbpData, setGbpData]     = useState(null);
  const [qrData, setQrData]       = useState(null);
  const [qrLoading, setQrLoading] = useState(false);
  const [qrError, setQrError]     = useState('');

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/projects/${project.id}/bewertungs-url`, { headers })
      .then(r => r.ok ? r.json() : null).then(d => d && setGbpData(d)).catch(() => {});
  }, [project.id]); // eslint-disable-line

  const loadQr = async () => {
    setQrLoading(true); setQrError('');
    try {
      const r = await fetch(`${API_BASE_URL}/api/projects/${project.id}/bewertungs-qrcode`, { headers });
      if (!r.ok) { setQrError('QR-Code konnte nicht geladen werden'); return; }
      const blob = await r.blob();
      const reader = new FileReader();
      reader.onloadend = () => setQrData(reader.result);
      reader.readAsDataURL(blob);
    } catch { setQrError('Verbindungsfehler'); }
    finally { setQrLoading(false); }
  };

  const downloadQr = () => {
    if (!qrData) return;
    const a = document.createElement('a');
    a.href = qrData; a.download = `bewertungs-qr-${project.company_name || project.id}.png`; a.click();
  };

  return (
    <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 16 }}>
      {gbpData?.review_url && (
        <div style={{ padding: 14, background: 'var(--bg-app)', border: '1px solid var(--border-light)', borderRadius: 10 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', marginBottom: 6 }}>Google Bewertungs-Link</div>
          <a href={gbpData.review_url} target="_blank" rel="noreferrer" style={{ fontSize: 13, color: 'var(--brand-primary)', wordBreak: 'break-all' }}>{gbpData.review_url}</a>
        </div>
      )}
      {project.gbp_rating && (
        <div style={{ display: 'flex', gap: 12 }}>
          <div style={{ flex: 1, padding: 14, background: 'var(--bg-app)', border: '1px solid var(--border-light)', borderRadius: 10, textAlign: 'center' }}>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 4 }}>Google Bewertung</div>
            <div style={{ fontSize: 22, fontWeight: 800, color: '#d97706' }}>⭐ {project.gbp_rating}</div>
          </div>
          <div style={{ flex: 1, padding: 14, background: 'var(--bg-app)', border: '1px solid var(--border-light)', borderRadius: 10, textAlign: 'center' }}>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 4 }}>Anzahl Bewertungen</div>
            <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)' }}>{project.gbp_ratings_total}</div>
          </div>
        </div>
      )}
      <div style={{ display: 'flex', gap: 10 }}>
        <button onClick={loadQr} disabled={qrLoading}
          style={{ flex: 1, padding: '10px 0', background: '#008EAA', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, fontSize: 13, cursor: qrLoading ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)' }}>
          {qrLoading ? 'Laden...' : '📲 QR-Code laden'}
        </button>
        {qrData && (
          <button onClick={downloadQr}
            style={{ padding: '10px 16px', background: 'var(--bg-app)', border: '1px solid var(--border-medium)', borderRadius: 8, fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
            ⬇ Herunterladen
          </button>
        )}
      </div>
      {qrError && <div style={{ fontSize: 12, color: '#dc2626' }}>{qrError}</div>}
      {qrData && <img src={qrData} alt="Bewertungs-QR" style={{ width: 160, height: 160, margin: '0 auto', display: 'block', borderRadius: 8 }} />}
    </div>
  );
}

// ── Trustpilot ────────────────────────────────────────────────────────────────
function TrustpilotEmbed({ project }) {
  return (
    <div style={{ padding: '32px 24px', textAlign: 'center', display: 'flex', flexDirection: 'column', gap: 16, alignItems: 'center' }}>
      <div style={{ fontSize: 40 }}>⭐</div>
      <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Trustpilot-Bewertung anfragen</div>
      <div style={{ fontSize: 13, color: 'var(--text-secondary)', maxWidth: 360 }}>
        Fordere {project?.company_name || 'den Kunden'} auf, eine Bewertung auf Trustpilot zu hinterlassen und stärke die Online-Reputation.
      </div>
      <a href="https://www.trustpilot.com" target="_blank" rel="noreferrer"
        style={{ padding: '10px 28px', background: '#00b67a', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)', textDecoration: 'none', display: 'inline-block' }}>
        ⭐ Zu Trustpilot
      </a>
    </div>
  );
}

// ── Website-Vergleich ─────────────────────────────────────────────────────────
function WebsiteVergleichEmbed({ project, headers }) {
  const [screenshots, setScreenshots] = useState({ before: null, after: null });
  const [takingBefore, setTakingBefore] = useState(false);
  const [takingAfter, setTakingAfter]   = useState(false);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/projects/${project.id}/screenshots`, { headers })
      .then(r => r.ok ? r.json() : null).then(d => d && setScreenshots(d)).catch(() => {});
  }, [project.id]); // eslint-disable-line

  const takeBefore = async () => {
    setTakingBefore(true);
    try {
      const r = await fetch(`${API_BASE_URL}/api/projects/${project.id}/screenshot/before`, { method: 'POST', headers });
      if (r.ok) { const d = await r.json(); setScreenshots(s => ({ ...s, before: { data: d.screenshot_url, date: new Date().toISOString() } })); }
    } catch {} finally { setTakingBefore(false); }
  };

  const takeAfter = async () => {
    setTakingAfter(true);
    try {
      const r = await fetch(`${API_BASE_URL}/api/projects/${project.id}/screenshot/after`, { method: 'POST', headers });
      if (r.ok) { const d = await r.json(); setScreenshots(s => ({ ...s, after: { data: d.screenshot_url, date: new Date().toISOString() } })); }
    } catch {} finally { setTakingAfter(false); }
  };

  const fmtDate = (iso) => iso ? new Date(iso).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' }) : null;
  const Placeholder = ({ text }) => (
    <div style={{ height: 160, background: 'var(--bg-app)', border: '1.5px dashed var(--border-medium)', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>{text}</span>
    </div>
  );

  return (
    <div style={{ padding: '20px 24px' }}>
      <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 16 }}>📸 Website-Vergleich</div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', marginBottom: 8 }}>VORHER</div>
          {screenshots.before?.data
            ? <img src={screenshots.before.data} alt="Vorher" style={{ width: '100%', borderRadius: 8, border: '1px solid var(--border-light)' }} />
            : <Placeholder text="Noch kein Screenshot" />}
          <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
            <button onClick={takeBefore} disabled={takingBefore}
              style={{ flex: 1, padding: '8px 0', background: 'var(--bg-elevated)', border: '1px solid var(--border-medium)', borderRadius: 7, fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
              {takingBefore ? 'Erstelle...' : '📷 Screenshot erstellen'}
            </button>
          </div>
          {screenshots.before?.date && <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>{fmtDate(screenshots.before.date)}</div>}
        </div>
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, color: '#059669', marginBottom: 8 }}>NACHHER</div>
          {screenshots.after?.data
            ? <img src={screenshots.after.data} alt="Nachher" style={{ width: '100%', borderRadius: 8, border: '1px solid var(--border-light)' }} />
            : <Placeholder text="Noch kein Screenshot" />}
          <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
            <button onClick={takeAfter} disabled={takingAfter}
              style={{ flex: 1, padding: '8px 0', background: '#059669', color: '#fff', border: 'none', borderRadius: 7, fontSize: 12, fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
              {takingAfter ? 'Erstelle...' : '📷 Screenshot erstellen'}
            </button>
          </div>
          {screenshots.after?.date && <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>{fmtDate(screenshots.after.date)}</div>}
        </div>
      </div>
    </div>
  );
}

// ── Upsell ────────────────────────────────────────────────────────────────────
function UpsellEmbed() {
  const PAKETE = [
    { name: 'SEO-Retainer',     price: '129€/Monat', color: '#0d6efd', features: ['Monatliche Keyword-Analyse', 'On-Page Optimierung', 'Monatlicher Report'] },
    { name: 'Wartungspaket',    price: '49€/Monat',  color: '#7c3aed', features: ['Updates & Sicherheit', 'Backup täglich', 'Support per Chat'] },
    { name: 'Digital Rundum',   price: '249€/Monat', color: '#059669', features: ['SEO + Wartung', 'Google Ads Management', 'Monatliches Strategie-Call'] },
  ];
  return (
    <div style={{ padding: '20px 24px' }}>
      <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 16 }}>💼 Upsell-Produkte</div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
        {PAKETE.map(pkg => (
          <div key={pkg.name} style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 10, padding: 20, display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>{pkg.name}</div>
            <div style={{ fontSize: 20, fontWeight: 800, color: pkg.color }}>{pkg.price}</div>
            <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.8 }}>
              {pkg.features.map(f => <li key={f}>{f}</li>)}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Live-Daten ────────────────────────────────────────────────────────────────
function LiveDatenEmbed({ project }) {
  const fields = [
    { label: 'Phase',             value: project?.status?.replace('phase_', 'Phase ') || '—' },
    { label: 'PageSpeed Mobile',  value: project?.pagespeed_mobile  != null ? `${project.pagespeed_mobile}/100`  : '—' },
    { label: 'PageSpeed Desktop', value: project?.pagespeed_desktop != null ? `${project.pagespeed_desktop}/100` : '—' },
    { label: 'Domain erreichbar', value: project?.domain_reachable === true ? '✅ Ja' : project?.domain_reachable === false ? '❌ Nein' : '—' },
    { label: 'Go-Live Datum',     value: project?.abnahme_datum ? new Date(project.abnahme_datum).toLocaleDateString('de-DE') : '—' },
    { label: 'Abnahme durch',     value: project?.abnahme_durch || '—' },
  ];
  return (
    <div style={{ padding: '20px 24px' }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>
        {fields.map(f => (
          <div key={f.label} style={{ padding: 14, background: 'var(--bg-app)', border: '1px solid var(--border-light)', borderRadius: 10 }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 4 }}>{f.label}</div>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums' }}>{f.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
