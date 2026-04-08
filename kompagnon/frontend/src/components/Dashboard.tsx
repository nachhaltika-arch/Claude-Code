import React, { useState, useEffect } from 'react';
import {
  User, UserProfile, Operator, ServiceProvider, Unit, UnitGroup,
  ActivityLog, ContractInstance, DocumentInstance, EmissionFactor,
  UserRole, Anlage, KnowledgeEntry, DocTemplate
} from '../types';
import {
  LayoutDashboard, Users, Factory, Layers, FileText, Settings,
  HelpCircle, LogOut, Search, Plus, Filter, Bell, Menu, X,
  ShieldCheck, FileSignature, Award, FolderOpen, Database, TrendingDown,
  Wand2, Mail
} from 'lucide-react';

// Demo Data
import {
  DEMO_OPERATORS, DEMO_SERVICE_PROVIDERS, DEMO_UNITS,
  DEMO_GROUPS, DEMO_DOCUMENTS, DEMO_ACTIVITIES
} from '../utils/demoData';

// Components
import UnitDetailPage from './UnitDetailPage';
import GroupDetailPage from './GroupDetailPage';
import OperatorDetailPage from './OperatorDetailPage';
import ServiceProviderDetailPage from './ServiceProviderDetailPage';
import UserManagement from './UserManagement';
import ActivityFeed from './ActivityFeed';
import KnowledgeBase from './KnowledgeBase';
import ReportManager from './ReportManager';
import ContractManager from './ContractManager';
import VerificationCenter from './VerificationCenter';
import CertificationManager from './CertificationManager';
import SupportingDocumentsManager from './SupportingDocumentsManager';
import EmissionFactorSettings from './EmissionFactorSettings';
import TemplateManager from './TemplateManager';
import Onboarding from './Onboarding';
import AnlageForm from './AnlageForm';
import GroupForm from './GroupForm';
import CsvImporter from './CsvImporter';
import Newsletter from './Newsletter';
import NewsletterEditor from './NewsletterEditor';

interface DashboardProps {
  user: User;
  allUsers: UserProfile[];
  onCreateUser: (user: UserProfile) => void;
  onUpdateUser: (user: UserProfile) => void;
  onDeleteUser: (username: string) => void;
}

type DashboardView =
  | 'DASHBOARD'
  | 'UNITS'
  | 'GROUPS'
  | 'OPERATORS'
  | 'SERVICE_PROVIDERS'
  | 'DOCUMENTS'
  | 'REPORTS'
  | 'CONTRACTS'
  | 'VERIFICATION'
  | 'CERTIFICATES'
  | 'USERS'
  | 'SETTINGS'
  | 'KNOWLEDGE'
  | 'TEMPLATES'
  | 'NEWSLETTER'
  | 'NEWSLETTER_EDITOR';

// Mock Templates with HTML Content for Editing
const INITIAL_TEMPLATES: DocTemplate[] = [
    {
        id: 't1',
        name: 'Rahmenvertrag Betreiber Standard v2.1',
        type: 'CONTRACT',
        category: 'Rahmenvertrag',
        uploadedAt: '12.01.2024',
        fileData: null,
        htmlContent: `
<h1>Rahmenvertrag über die Zertifizierung von CO2-Minderungsleistungen</h1>
<p>Zwischen</p>
<p><strong>{{operator.name}}</strong><br>{{operator.address}}</p>
<p>(nachfolgend "Betreiber")</p>
<p>und</p>
<p><strong>Silva Viridis GmbH</strong></p>
<p>(nachfolgend "Zertifizierer")</p>

<h2>§ 1 Gegenstand des Vertrages</h2>
<p>Gegenstand dieses Vertrages ist die Validierung und Zertifizierung von CO2-Minderungsleistungen aus erneuerbaren Energieanlagen des Betreibers gemäß ISO 14064-2.</p>

<h2>§ 2 Pflichten des Betreibers</h2>
<p>Der Betreiber verpflichtet sich zur Übermittlung korrekter Produktionsdaten. Die MaStR-Nummer lautet: <strong>{{operator.abr}}</strong>.</p>

<p>Ort, Datum: ________________</p>
`
    },
    {
        id: 't2',
        name: 'Anlagenzuordnung Anhang B',
        type: 'CONTRACT',
        category: 'Anhang',
        uploadedAt: '15.02.2024',
        fileData: null,
        htmlContent: `
<h2>Anhang B: Anlagenzuordnung</h2>
<p>Zum Rahmenvertrag Nr. {{contract.id}}</p>

<table border="1" cellpadding="5" cellspacing="0" width="100%">
  <thead>
    <tr>
      <th>Anlage</th>
      <th>Standort</th>
      <th>Leistung (kW)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>{{unit.name}}</td>
      <td>{{unit.location}}</td>
      <td>{{unit.power}}</td>
    </tr>
  </tbody>
</table>
<p>Inbetriebnahme: {{unit.commissioning}}</p>
`
    },
    {
        id: 't3',
        name: 'ISO 14064 Monitoring Report 2024',
        type: 'DOCUMENT',
        category: 'Monitoring Report',
        uploadedAt: '01.03.2024',
        fileData: null,
        htmlContent: `
<h1>Monitoring Report {{year}}</h1>
<p><strong>Betreiber:</strong> {{operator.name}}</p>
<p><strong>Berichtszeitraum:</strong> 01.01.{{year}} bis 31.12.{{year}}</p>

<h2>1. Einleitung</h2>
<p>Dieser Bericht dokumentiert die THG-Minderungen.</p>

<h2>2. Quantifizierung</h2>
<p>Gesamterzeugung: <strong>{{total.kwh}} kWh</strong></p>
<p>CO2-Einsparung: <strong>{{total.co2}} t</strong></p>
`
    },
    {
        id: 't4',
        name: 'Verifizierungs-Statement V1',
        type: 'DOCUMENT',
        category: 'Statement',
        uploadedAt: '10.01.2023',
        fileData: null,
        htmlContent: `<h1>Verifizierungs-Statement</h1><p>Hiermit wird bestätigt, dass die Anlage {{unit.name}} geprüft wurde.</p>`
    }
];

const Dashboard: React.FC<DashboardProps> = ({
  user, allUsers, onCreateUser, onUpdateUser, onDeleteUser
}) => {
  // --- STATE ---
  const [operators, setOperators] = useState<Operator[]>(DEMO_OPERATORS);
  const [serviceProviders, setServiceProviders] = useState<ServiceProvider[]>(DEMO_SERVICE_PROVIDERS);
  const [units, setUnits] = useState<Unit[]>(DEMO_UNITS);
  const [groups, setGroups] = useState<UnitGroup[]>(DEMO_GROUPS);
  const [documents, setDocuments] = useState<DocumentInstance[]>(DEMO_DOCUMENTS);
  const [contracts, setContracts] = useState<ContractInstance[]>([]);
  const [activities, setActivities] = useState<ActivityLog[]>(DEMO_ACTIVITIES);
  const [emissionFactors, setEmissionFactors] = useState<EmissionFactor[]>([]);
  const [knowledgeEntries, setKnowledgeEntries] = useState<KnowledgeEntry[]>([]);
  const [templates, setTemplates] = useState<DocTemplate[]>(INITIAL_TEMPLATES);

  const [activeView, setActiveView] = useState<DashboardView>('DASHBOARD');
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [showOnboarding, setShowOnboarding] = useState(!user.hasCompletedOnboarding);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Forms State
  const [showUnitForm, setShowUnitForm] = useState(false);
  const [showGroupForm, setShowGroupForm] = useState(false);

  // Ensure Onboarding is triggered if user is new
  useEffect(() => {
      if (!user.hasCompletedOnboarding) {
          setShowOnboarding(true);
      }
  }, [user.hasCompletedOnboarding]);

  // --- HANDLERS ---
  // ... (alle Handler wie handleOnboardingComplete, handleUnitUpdate, etc.)
  // ... (vollstaendig wie oben ausgegeben)

  // --- NAVIGATION / renderContent / MAIN LAYOUT ---
  // ... (vollstaendig wie oben ausgegeben)
};

// NavItem sub-component
const NavItem = ({ icon, label, isActive, onClick }: { icon: any, label: string, isActive: boolean, onClick: () => void }) => (
    <button
        onClick={onClick}
        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
            isActive
            ? 'bg-emerald-50 text-emerald-800'
            : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
        }`}
    >
        <span className={isActive ? 'text-emerald-600' : 'text-slate-400'}>{icon}</span>
        {label}
    </button>
);

export default Dashboard;
