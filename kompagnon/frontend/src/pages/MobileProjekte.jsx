import React from 'react';
import { Navigate } from 'react-router-dom';
import { useScreenSize } from '../utils/responsive';
import { HubGrid, HubButton, HubSectionLabel } from '../components/MobileHub';

export default function MobileProjekte() {
  const { isMobile } = useScreenSize();

  // Siehe MobileLeads: `navigate()` im Render leitet nicht um.
  if (!isMobile) return <Navigate to="/app/projects" replace />;

  return (
    <div style={{ background: 'var(--bg-app)', minHeight: '100%' }}>
      <HubSectionLabel>Bereich wählen</HubSectionLabel>
      <HubGrid>
        {/* „3", „2 offen" und „54 Punkte / Projekt" standen fest im Quelltext. */}
        <HubButton icon="🚀" label="Alle Projekte" desc="Aktive Aufträge"      path="/app/projects" primary />
        <HubButton icon="🎫" label="Tickets"       desc="Support & Aufgaben"   path="/app/tickets" />
        <HubButton icon="✅" label="Checklisten"   desc="Je Projekt abhaken"   path="/app/checklists" />
        <HubButton icon="📄" label="Templates"     desc="Vorlagen-Bibliothek"  path="/app/settings/templates" />
      </HubGrid>
    </div>
  );
}
