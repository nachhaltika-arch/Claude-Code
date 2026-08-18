import React from 'react';
import { Navigate } from 'react-router-dom';
import { useScreenSize } from '../utils/responsive';
import { HubGrid, HubButton, HubSectionLabel } from '../components/MobileHub';

export default function MobileLeads() {
  const { isMobile } = useScreenSize();

  // `navigate()` im Rumpf einer Komponente aufzurufen, leitet nicht um: Der
  // Router verwirft den Aufruf, `return null` bleibt stehen — und auf einem
  // breiten Bildschirm zeigte diese Adresse eine **leere Seite**. Nachgemessen
  // am 18.08.2026 an /app/vertrieb und /app/m-leads.
  if (!isMobile) return <Navigate to="/app/projektpipeline" replace />;

  return (
    <div style={{ background: 'var(--bg-app)', minHeight: '100%' }}>
      <HubSectionLabel>Ansicht wählen</HubSectionLabel>
      <HubGrid>
        {/* Die Zahlen auf den Kacheln waren fest eingetragen: „12" und „5",
          * gleich welchen Bestand die Datenbank hat. Im lokalen Stand steht
          * **ein** Betrieb. Eine erfundene Zahl ist schlimmer als keine — sie
          * wird geglaubt. Bis sie aus den Daten kommt, steht keine da. */}
        <HubButton icon="📋" label="Alle Leads"  desc="Komplette Pipeline"     path="/app/projektpipeline"                    primary />
        <HubButton icon="🆕" label="Neue Leads"  desc="Noch nicht kontaktiert" path="/app/projektpipeline?status=neu" />
        <HubButton icon="📞" label="Kontaktiert" desc="In Kommunikation"       path="/app/projektpipeline?status=kontaktiert" />
        <HubButton icon="🏢" label="Betriebe"    desc="Firmenkartei"           path="/app/betriebe" />
      </HubGrid>
    </div>
  );
}
