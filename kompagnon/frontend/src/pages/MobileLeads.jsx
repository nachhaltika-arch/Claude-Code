import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useScreenSize } from '../utils/responsive';
import { HubGrid, HubButton, HubSectionLabel } from '../components/MobileHub';

export default function MobileLeads() {
  const navigate = useNavigate();
  const { isMobile } = useScreenSize();

  if (!isMobile) { navigate('/app/leads', { replace: true }); return null; }

  return (
    <div style={{ background: '#F0F4F5', minHeight: '100%' }}>
      <HubSectionLabel>Ansicht wählen</HubSectionLabel>
      <HubGrid>
        <HubButton icon="📋" label="Alle Leads"  desc="Komplette Pipeline"     path="/app/leads"                       primary badge="12" />
        <HubButton icon="🆕" label="Neue Leads"  desc="Noch nicht kontaktiert" path="/app/leads?status=neu"            badge="5" />
        <HubButton icon="📞" label="Kontaktiert" desc="In Kommunikation"       path="/app/leads?status=kontaktiert" />
        <HubButton icon="🏢" label="Unternehmen" desc="Firmenkartei"           path="/app/companies" />
      </HubGrid>
    </div>
  );
}
