import { useState, useEffect } from 'react';
import AnalyseCentrale from './AnalyseCentrale';
import ContentWerkstatt from './ContentWerkstatt';
// Beide Schritte lebten bis zum 21.08.2026 nur in `ProzessFlowV3` — dem
// Legacy-Editor. Ihre Dateien ueberleben dessen Abbau; sie brauchten nur
// einen Platz im gemeinsamen Renderer.
import GeoOptimizerStep from './GeoOptimizerStep';
import { LeistungsseitenStep } from './LeistungsseitenWizard';
import DesignStudio from './DesignStudio';
import BriefingTab from './BriefingTab';
import BriefingWizard from './BriefingWizard';
import KiReportPanel from './KiReportPanel';
import MoodboardPanel from './MoodboardPanel';
import AuditReport from './AuditReport';
import BrandDesignEditor from './BrandDesignEditor';
import BrandDesignWerkstatt from './BrandDesignWerkstatt';
import BrandGuideline from './BrandGuideline';
import AssetsKlaeren from './briefing/AssetsKlaeren';
import Funktionen from './briefing/Funktionen';
import SeoZiele from './briefing/SeoZiele';
import ZieleZielgruppe from './briefing/ZieleZielgruppe';
import { useAudit } from '../hooks/useAudit';
import SitemapVorschlaege from './SitemapVorschlaege';
import API_BASE_URL from '../config';
import { loadJson, saveJson } from '../utils/apiRequest';
import { aufTaste } from '../utils/tastaturBedienung';

// Die Schritt-Einbettungen liegen seit dem 22.08.2026 in `./schritte/`
// (L-25) — nach Thema geschnitten, nicht nach Groesse.
import { SitemapEditorEmbed, SitemapKiVorschlag } from './schritte/sitemap';
import { AuditEmbed, BriefingUnternehmenEmbed } from './schritte/briefingAudit';
import { DNSEmbed, LiveDatenEmbed, NetlifyEmbed, ZugangsdatenEmbed } from './schritte/technik';
import { AbnahmeEmbed, QAEmbed, WebsiteVergleichEmbed } from './schritte/qualitaet';
import QAChecklist from './QAChecklist';
import { DesignStudioEmbed, GbpQrEmbed, TrustpilotEmbed, UpsellEmbed } from './schritte/marketing';
import Spinner from './schritte/Spinner';

// ── Was hier bis zum 22.08.2026 stand (L-25) ─────────────────────────
//
// `PHASEN`, `ALLE_SCHRITTE` und die Standardkomponente `ProzessFlow` —
// zusammen 493 Zeilen. **Keine davon wurde importiert.** Im ganzen Baum gibt
// es genau eine Einbindung dieser Datei, `OnlineFertigEditor.jsx:35`, und sie
// holt nur `SchrittInhalt`.
//
// `PHASEN` beschrieb die Schrittfolge ein zweites Mal; die gueltige steht in
// `KASSidebar.SCHRITT_FOLGE`. Zwei Fassungen derselben Liste laufen
// auseinander — bei `_serialize` in den Briefing-Routern war es am selben Tag
// schon passiert (L-27). `CustomerPortal.jsx` fuehrt uebrigens ein eigenes
// `PHASEN`; auch das kam nie von hier.
//
// **Beinahe waere die ganze Datei geloescht worden.** Keine Seite bindet
// `ProzessFlow` ein — wer nur nach `import ProzessFlow` sucht, findet nichts
// und haelt 2.307 Zeilen fuer tot. Gebraucht wird der **benannte** Export.

export function SchrittInhalt({ schritt, project, lead, leadId, token, headers,
  briefing, latestAudit, localBriefing, reloadBriefing, onAuditComplete,
  onSitemapReload, onAnalyseUpdate, sitemapPages, sitemapLoading,
  websiteContent, brandData, netlify, qaResult, onProjectRefresh,
  goWeiter, goZurueck,
  confirmedSteps, onStepConfirmed, onGuidelineGenerated }) {

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

    case 'GeoOptimizer':
      return (
        <div style={pad}>
          <GeoOptimizerStep
            projectId={project?.id}
            onComplete={(score) => onAnalyseUpdate && onAnalyseUpdate({ geoScore: score })}
          />
        </div>
      );

    case 'LeistungsseitenWizard':
      return (
        <LeistungsseitenStep
          projectId={project?.id}
          leadId={leadId}
          token={token}
          brandData={brandData}
          confirmedSteps={project?.steps_confirmed}
          onSave={() => { onProjectRefresh?.(); }}
        />
      );

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
          <div style={{ padding: '0 24px 20px' }}>
            <SitemapVorschlaege
              leadId={leadId}
              token={token}
              onAdded={onSitemapReload}
            />
          </div>
        </div>
      );

    case 'ContentWerkstatt':
    case 'ContentSeiteninhalte':
      return (
        <ContentWerkstatt
          project={project}
          sitemapPages={sitemapPages}
          sitemapLoading={sitemapLoading}
          token={token}
          leadId={project.lead_id}
          websiteContent={websiteContent}
          onProjectRefresh={onProjectRefresh}
          mode="inhalte"
        />
      );

    case 'ContentAssets':
      return (
        <ContentWerkstatt
          project={project}
          sitemapPages={sitemapPages}
          sitemapLoading={sitemapLoading}
          token={token}
          leadId={project.lead_id}
          websiteContent={websiteContent}
          onProjectRefresh={onProjectRefresh}
          mode="assets"
        />
      );

    case 'ContentFreigabe':
      return (
        <ContentWerkstatt
          project={project}
          sitemapPages={sitemapPages}
          sitemapLoading={sitemapLoading}
          token={token}
          leadId={project.lead_id}
          websiteContent={websiteContent}
          onProjectRefresh={onProjectRefresh}
          mode="freigaben"
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

    case 'BrandDesign':
      return (
        <BrandDesignWerkstatt
          project={project}
          lead={lead}
          token={token}
          onBrandSaved={(data) => {
            if (onAnalyseUpdate) onAnalyseUpdate({ brandPrimaryColor: data.primary_color, brandData: data });
            if (onProjectRefresh) onProjectRefresh();
          }}
        />
      );

    case 'AssetsKlaeren':
      return (
        <div style={{ padding: '20px 24px' }}>
          <AssetsKlaeren
            leadId={leadId}
            token={token}
            onSaved={() => { if (onProjectRefresh) onProjectRefresh(); }}
          />
        </div>
      );

    case 'ZieleZielgruppe':
      return (
        <div style={{ padding: '20px 24px' }}>
          <ZieleZielgruppe
            leadId={leadId}
            token={token}
            briefing={briefing}
            onSaved={() => { if (onProjectRefresh) onProjectRefresh(); }}
          />
        </div>
      );

    case 'Funktionen':
      return (
        <div style={{ padding: '20px 24px' }}>
          <Funktionen
            leadId={leadId}
            token={token}
            onSaved={() => {
              if (onProjectRefresh) onProjectRefresh();
              if (goWeiter) goWeiter();
            }}
          />
        </div>
      );

    case 'SeoZiele':
      return (
        <div style={{ padding: '20px 24px' }}>
          <SeoZiele
            leadId={leadId}
            token={token}
            projectId={project?.id}
            onStepConfirmed={(stepId) => {
              if (onStepConfirmed) onStepConfirmed(stepId);
              if (onProjectRefresh) onProjectRefresh();
              if (goWeiter) goWeiter();
            }}
            onSaved={() => { if (onProjectRefresh) onProjectRefresh(); }}
          />
        </div>
      );

    case 'BrandGuideline':
      return (
        <div style={{ padding: '20px 24px' }}>
          <BrandGuideline
            project={project}
            lead={lead}
            token={token}
            leadId={leadId}
            brandData={brandData}
            projectId={project?.id}
            confirmedSteps={confirmedSteps || {}}
            onGuidelineGenerated={() => {
              if (onGuidelineGenerated) onGuidelineGenerated();
            }}
            onStepConfirmed={(stepId) => {
              if (onStepConfirmed) onStepConfirmed(stepId);
              if (onProjectRefresh) onProjectRefresh();
            }}
          />
        </div>
      );

    case 'BrandDesignEditor':
      return (
        <div style={{ padding: '20px 24px' }}>
          <BrandDesignEditor
            leadId={project.lead_id}
            token={token}
            brandData={brandData}
            onSaved={(data) => {
              if (onAnalyseUpdate) onAnalyseUpdate({ brandPrimaryColor: data.primary, brandData: data });
              if (onProjectRefresh) onProjectRefresh();
            }}
          />
        </div>
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
      // **Getauscht am 24.08.2026 (L-95).** Hier stand `QmChecklisteEmbed`
      // mit 53 Zeilen und zehn Punkten. `QAChecklist` (303) prueft
      // dieselben Dinge und zusaetzlich Rechtliches, Browser-Tests,
      // Bildgroessen und Search Console — und die sieben Punkte der kurzen
      // Liste, die sie nicht hatte, sind mitsamt ihren Kennungen
      // uebernommen. Bereits gesetzte Haken wandern ueber
      // `gbpChecklistJson` mit; wer die kurze Liste schon ausgefuellt hatte,
      // faengt nicht von vorn an.
      return (
        <QAChecklist
          projectId={project.id}
          token={token}
          qaChecklistJson={project?.qa_checklist_json}
          gbpChecklistJson={project?.gbp_checklist_json}
          pagespeedMobile={project?.pagespeed_after_mobile}
          pagespeedDesktop={project?.pagespeed_after_desktop}
        />
      );

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

