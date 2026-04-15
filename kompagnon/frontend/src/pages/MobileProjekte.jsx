import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useScreenSize } from '../utils/responsive';
import { HubGrid, HubButton, HubSectionLabel } from '../components/MobileHub';

export default function MobileProjekte() {
  const navigate = useNavigate();
  const { isMobile } = useScreenSize();

  useEffect(() => {
    if (!isMobile) navigate('/app/projects', { replace: true });
  }, [isMobile, navigate]);

  if (!isMobile) return null;

  return (
    <div style={{ background: '#F0F4F5', minHeight: '100%', fontFamily: 'var(--font-sans)' }}>
      <HubSectionLabel>Bereich wählen</HubSectionLabel>
      <HubGrid>
        <HubButton icon="🚀" label="Alle Projekte" desc="Aktive Aufträge"      path="/app/projects"            primary />
        <HubButton icon="🎫" label="Tickets"       desc="Support & Aufgaben"   path="/app/tickets" />
        <HubButton icon="✅" label="Checklisten"   desc="54 Punkte / Projekt"  path="/app/checklists" />
        <HubButton icon="📄" label="Templates"     desc="Vorlagen-Bibliothek"  path="/app/settings/templates" />
      </HubGrid>
    </div>
  );
}
