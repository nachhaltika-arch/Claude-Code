import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useScreenSize } from '../utils/responsive';
import { HubGrid, HubButton, HubSectionLabel } from '../components/MobileHub';

export default function MobileVertrieb() {
  const navigate = useNavigate();
  const { isMobile } = useScreenSize();

  // Desktop: Hub umgehen, direkt zur Pipeline.
  useEffect(() => {
    if (!isMobile) navigate('/app/deals', { replace: true });
  }, [isMobile, navigate]);

  if (!isMobile) return null;

  return (
    <div style={{ background: '#F0F4F5', minHeight: '100%', fontFamily: 'var(--font-sans)' }}>
      <HubSectionLabel>Bereich wählen</HubSectionLabel>
      <HubGrid>
        <HubButton icon="📋" label="Pipeline"      desc="Deals & Phasen"        path="/app/deals"      primary />
        <HubButton icon="🔍" label="Audit-Tool"    desc="Website analysieren"   path="/app/audit" />
        <HubButton icon="📣" label="Kampagnen"     desc="UTM & Landingpages"    path="/app/campaigns" />
        <HubButton icon="📧" label="Newsletter"    desc="Brevo · Listen"        path="/app/newsletter" badge="Brevo" badgeStyle="teal" />
        <HubButton icon="⬆️" label="Domain Import" desc="CSV hochladen"         path="/app/import" />
        <HubButton icon="⬇️" label="Massen-Export" desc="Lead-Daten als CSV"    path="/app/export" />
        <HubButton icon="🕷️" label="Scraper"       desc="Crawler-Steuerung"     path="/app/scraper" />
        <HubButton icon="💰" label="Retainer"      desc="Pflegepakete"          path="/app/retainer" />
      </HubGrid>
    </div>
  );
}
