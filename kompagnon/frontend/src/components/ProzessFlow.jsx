import { useState, useEffect, useCallback } from 'react';
import AnalyseCentrale from './AnalyseCentrale';
import ContentWerkstatt from './ContentWerkstatt';
import DesignStudio from './DesignStudio';
import BriefingTab from './BriefingTab';

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
export default function ProzessFlow(props) {
  // Implementierung in Teil 2
  return <div>Wird in Teil 2 implementiert</div>;
}
