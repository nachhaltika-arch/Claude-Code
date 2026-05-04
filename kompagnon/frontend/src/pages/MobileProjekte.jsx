import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useScreenSize } from '../utils/responsive';
import { HubGrid, HubButton, HubSectionLabel } from '../components/MobileHub';

export default function MobileProjekte() {
  const navigate = useNavigate();
  const { isMobile } = useScreenSize();

  if (!isMobile) { navigate('/app/projects', { replace: true }); return null; }

  return (
    <div style={{ background: '#F0F4F5', minHeight: '100%' }}>
      <HubSectionLabel>Bereich wählen</HubSectionLabel>
      <HubGrid>
        <HubButton icon="🚀" label="Alle Projekte" desc="Aktive Aufträge"      path="/app/projects"           primary badge="3" />
        <HubButton icon="🎫" label="Tickets"       desc="Support & Aufgaben"   path="/app/tickets"            badge="2 offen" />
        <HubButton icon="✅" label="Checklisten"   desc="54 Punkte / Projekt"  path="/app/checklists" />
        <HubButton icon="📄" label="Templates"     desc="Vorlagen-Bibliothek"  path="/app/settings/templates" />
      </HubGrid>
    </div>
  );
}
