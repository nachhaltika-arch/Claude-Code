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

  const handleOnboardingComplete = (data: Partial<Operator>, unitData?: Partial<Anlage>) => {
      if (onUpdateUser) {
          onUpdateUser({ ...user, hasCompletedOnboarding: true } as UserProfile);
      }

      const newOperator: Operator = {
          id: user.username,
          name: data.name || user.fullName,
          contactEmail: data.contactEmail || '',
          ...data,
          contractStatus: 'LOCKED',
          verificationStatus: 'PENDING'
      } as Operator;

      setOperators(prev => {
          const exists = prev.find(op => op.id === newOperator.id);
          if (exists) return prev.map(op => op.id === newOperator.id ? { ...op, ...newOperator } : op);
          return [...prev, newOperator];
      });

      // Handle the new unit from Step 2
      if (unitData && unitData.anlagenName) {
          const newUnit: Unit = {
              ...unitData,
              id: `unit_${Math.random().toString(36).substr(2, 6)}`,
              anlagenbetreiber: newOperator.name,
              betriebsstatus: 'In Betrieb',
              systemstatus: 'Aktiviert',
              production: []
          } as Unit;

          setUnits(prev => [...prev, newUnit]);

          // Log activity for unit creation
          const newActivity: ActivityLog = {
              id: Math.random().toString(36),
              userId: user.username,
              userName: user.fullName,
              userRole: user.role,
              action: 'CREATE',
              targetType: 'UNIT',
              targetName: newUnit.anlagenName,
              details: 'Automatisch im Onboarding erstellt',
              timestamp: new Date().toISOString()
          };
          setActivities(prev => [newActivity, ...prev]);
      }

      setShowOnboarding(false);
  };

  const handleUnitUpdate = (updatedUnit: Unit) => {
      setUnits(prev => prev.map(u => u.id === updatedUnit.id ? updatedUnit : u));
      // Log activity
      const log: ActivityLog = {
          id: Math.random().toString(36),
          userId: user.username,
          userName: user.fullName,
          userRole: user.role,
          action: 'UPDATE',
          targetType: 'UNIT',
          targetName: updatedUnit.anlagenName,
          timestamp: new Date().toISOString()
      };
      setActivities(prev => [log, ...prev]);
  };

  const handleGroupUpdate = (updatedGroup: UnitGroup) => {
      setGroups(prev => prev.map(g => g.id === updatedGroup.id ? updatedGroup : g));
  };

  const handleOperatorUpdate = (updatedOp: Operator) => {
      setOperators(prev => prev.map(op => op.id === updatedOp.id ? updatedOp : op));
  };

  const handleServiceProviderUpdate = (updatedSP: ServiceProvider) => {
      setServiceProviders(prev => prev.map(sp => sp.id === updatedSP.id ? updatedSP : sp));
  };

  const handleCreateUnit = (newUnit: Anlage) => {
      const unit: Unit = {
          ...newUnit,
          id: `unit_${Math.random().toString(36).substr(2, 6)}`,
          production: []
      } as Unit;
      setUnits(prev => [...prev, unit]);
      setShowUnitForm(false);

      const log: ActivityLog = {
          id: Math.random().toString(36),
          userId: user.username,
          userName: user.fullName,
          userRole: user.role,
          action: 'CREATE',
          targetType: 'UNIT',
          targetName: unit.anlagenName,
          timestamp: new Date().toISOString()
      };
      setActivities(prev => [log, ...prev]);
  };

  const handleImportUnits = (importedUnits: Unit[]) => {
      setUnits(prev => [...prev, ...importedUnits]);
      const log: ActivityLog = {
          id: Math.random().toString(36),
          userId: user.username,
          userName: user.fullName,
          userRole: user.role,
          action: 'UPLOAD',
          targetType: 'UNIT',
          targetName: `${importedUnits.length} Anlagen`,
          details: 'Import via CSV (MaStR)',
          timestamp: new Date().toISOString()
      };
      setActivities(prev => [log, ...prev]);
  };

  const handleCreateGroup = (newGroup: UnitGroup) => {
      const group: UnitGroup = {
          ...newGroup,
          id: `grp_${Math.random().toString(36).substr(2, 6)}`
      };
      setGroups(prev => [...prev, group]);
      setShowGroupForm(false);
  };

  const handleCreateContract = (contract: ContractInstance) => {
      setContracts(prev => [...prev, contract]);
      const log: ActivityLog = {
          id: Math.random().toString(36),
          userId: user.username,
          userName: user.fullName,
          userRole: user.role,
          action: 'CREATE',
          targetType: 'CONTRACT',
          targetName: contract.id,
          timestamp: new Date().toISOString()
      };
      setActivities(prev => [log, ...prev]);
  };

  const handleGenerateDocuments = (newDocs: DocumentInstance[]) => {
      setDocuments(prev => [...prev, ...newDocs]);
      const log: ActivityLog = {
          id: Math.random().toString(36),
          userId: user.username,
          userName: user.fullName,
          userRole: user.role,
          action: 'GENERATE_DOC',
          targetType: 'DOCUMENT',
          targetName: `${newDocs.length} Dokumente`,
          timestamp: new Date().toISOString()
      };
      setActivities(prev => [log, ...prev]);
  };

  // --- NAVIGATION HELPERS ---

  const renderContent = () => {
      if (selectedItemId) {
          if (activeView === 'UNITS') {
              const unit = units.find(u => u.id === selectedItemId);
              if (unit) return <UnitDetailPage unit={unit} user={user} emissionFactors={emissionFactors} documents={documents} groups={groups} operators={operators} serviceProviders={serviceProviders} onBack={() => setSelectedItemId(null)} onUpdateUnit={handleUnitUpdate} onRefreshDocuments={() => {}} />;
          }
          if (activeView === 'GROUPS') {
              const group = groups.find(g => g.id === selectedItemId);
              if (group) return <GroupDetailPage group={group} user={user} units={units} emissionFactors={emissionFactors} documents={documents} operators={operators} serviceProviders={serviceProviders} onBack={() => setSelectedItemId(null)} onUpdateGroup={handleGroupUpdate} onRefreshDocuments={() => {}} />;
          }
          if (activeView === 'OPERATORS') {
              const op = operators.find(o => o.id === selectedItemId);
              if (op) return <OperatorDetailPage operator={op} user={user} onBack={() => setSelectedItemId(null)} onUpdateOperator={handleOperatorUpdate} contracts={contracts} onRefreshContracts={() => {}} />;
          }
          if (activeView === 'SERVICE_PROVIDERS') {
              const sp = serviceProviders.find(s => s.id === selectedItemId);
              if (sp) return <ServiceProviderDetailPage serviceProvider={sp} user={user} onBack={() => setSelectedItemId(null)} onUpdateServiceProvider={handleServiceProviderUpdate} operators={operators} contracts={contracts} onRefreshContracts={() => {}} />;
          }
      }

      switch(activeView) {
          case 'DASHBOARD':
              return (
                  <div className="space-y-6">
                      {/* Dashboard Stats & Activity Feed */}
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                          {/* Stats Cards */}
                          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                              <h3 className="text-slate-500 text-sm font-medium">Anlagen Gesamt</h3>
                              <p className="text-3xl font-bold text-slate-800 mt-2">{units.length}</p>
                          </div>
                          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                              <h3 className="text-slate-500 text-sm font-medium">Verifizierte CO₂-Minderung</h3>
                              <p className="text-3xl font-bold text-emerald-600 mt-2">1.240 t</p>
                          </div>
                          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                              <h3 className="text-slate-500 text-sm font-medium">Ausstehende Aufgaben</h3>
                              <p className="text-3xl font-bold text-amber-500 mt-2">3</p>
                          </div>
                      </div>
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                          <ActivityFeed activities={activities} limit={5} />
                      </div>
                  </div>
              );
          case 'UNITS':
              return (
                  <div className="space-y-6">
                      <div className="flex justify-between items-center">
                          <h2 className="text-2xl font-bold text-slate-800">Anlagenbestand</h2>
                          <div className="flex gap-2">
                              <button onClick={() => setShowUnitForm(true)} className="flex items-center gap-2 bg-emerald-800 text-white px-4 py-2 rounded-lg hover:bg-emerald-900 transition-colors">
                                  <Plus size={18} /> Neue Anlage
                              </button>
                          </div>
                      </div>
                      {showUnitForm && (
                          <div className="mb-8">
                              <AnlageForm onSave={handleCreateUnit} onCancel={() => setShowUnitForm(false)} />
                          </div>
                      )}

                      <CsvImporter onImport={handleImportUnits} />

                      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                          <table className="w-full text-left border-collapse">
                              <thead className="bg-slate-50 border-b border-slate-200">
                                  <tr>
                                      <th className="px-6 py-4 font-medium text-slate-500">Name</th>
                                      <th className="px-6 py-4 font-medium text-slate-500">Typ</th>
                                      <th className="px-6 py-4 font-medium text-slate-500">Leistung</th>
                                      <th className="px-6 py-4 font-medium text-slate-500">Status</th>
                                      <th className="px-6 py-4 font-medium text-slate-500 text-right">Aktion</th>
                                  </tr>
                              </thead>
                              <tbody className="divide-y divide-slate-100">
                                  {units.map(unit => (
                                      <tr key={unit.id} className="hover:bg-slate-50 cursor-pointer" onClick={() => setSelectedItemId(unit.id || null)}>
                                          <td className="px-6 py-4 font-medium text-slate-900">{unit.anlagenName}</td>
                                          <td className="px-6 py-4 text-slate-600">{unit.anlagenTyp}</td>
                                          <td className="px-6 py-4 text-slate-600">{unit.bruttoleistungKw} kW</td>
                                          <td className="px-6 py-4">
                                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${unit.betriebsstatus === 'In Betrieb' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'}`}>
                                                  {unit.betriebsstatus}
                                              </span>
                                          </td>
                                          <td className="px-6 py-4 text-right text-slate-400">Details &gt;</td>
                                      </tr>
                                  ))}
                              </tbody>
                          </table>
                      </div>
                  </div>
              );
          case 'GROUPS':
              return (
                  <div className="space-y-6">
                      <div className="flex justify-between items-center">
                          <h2 className="text-2xl font-bold text-slate-800">Anlagengruppen</h2>
                          <button onClick={() => setShowGroupForm(true)} className="flex items-center gap-2 bg-emerald-800 text-white px-4 py-2 rounded-lg hover:bg-emerald-900 transition-colors">
                              <Plus size={18} /> Neue Gruppe
                          </button>
                      </div>
                      {showGroupForm && (
                          <div className="mb-8">
                              <GroupForm units={units} user={user} onSave={handleCreateGroup} onCancel={() => setShowGroupForm(false)} />
                          </div>
                      )}
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                          {groups.map(group => (
                              <div key={group.id} onClick={() => setSelectedItemId(group.id)} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm hover:shadow-md cursor-pointer transition-all">
                                  <div className="flex items-center gap-3 mb-4">
                                      <div className="p-2 bg-purple-100 text-purple-700 rounded-lg"><Layers size={20} /></div>
                                      <h3 className="font-bold text-slate-900">{group.name}</h3>
                                  </div>
                                  <p className="text-slate-500 text-sm mb-4">{group.unitIds.length} Anlagen zugeordnet</p>
                                  <div className="flex justify-between items-center pt-4 border-t border-slate-100">
                                      <span className="text-xs text-slate-400">ID: {group.id}</span>
                                      <span className="text-emerald-600 text-sm font-medium hover:underline">Verwalten</span>
                                  </div>
                              </div>
                          ))}
                      </div>
                  </div>
              );
          case 'OPERATORS':
              return (
                  <div className="space-y-6">
                      <h2 className="text-2xl font-bold text-slate-800">Anlagenbetreiber</h2>
                      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                          <table className="w-full text-left border-collapse">
                              <thead className="bg-slate-50 border-b border-slate-200">
                                  <tr>
                                      <th className="px-6 py-4 font-medium text-slate-500">Name</th>
                                      <th className="px-6 py-4 font-medium text-slate-500">Ort</th>
                                      <th className="px-6 py-4 font-medium text-slate-500">Status</th>
                                      <th className="px-6 py-4 font-medium text-slate-500 text-right">Aktion</th>
                                  </tr>
                              </thead>
                              <tbody className="divide-y divide-slate-100">
                                  {operators.map(op => (
                                      <tr key={op.id} className="hover:bg-slate-50 cursor-pointer" onClick={() => setSelectedItemId(op.id)}>
                                          <td className="px-6 py-4 font-medium text-slate-900">{op.name}</td>
                                          <td className="px-6 py-4 text-slate-600">{op.ort}</td>
                                          <td className="px-6 py-4">
                                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${op.contractStatus === 'ACTIVE' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}`}>
                                                  {op.contractStatus || 'Ausstehend'}
                                              </span>
                                          </td>
                                          <td className="px-6 py-4 text-right text-slate-400">Details &gt;</td>
                                      </tr>
                                  ))}
                              </tbody>
                          </table>
                      </div>
                  </div>
              );
          case 'USERS':
              return <UserManagement users={allUsers} currentUser={user} onUpdateUser={onUpdateUser} onCreateUser={onCreateUser} onDeleteUser={onDeleteUser} />;
          case 'REPORTS':
              return <ReportManager operators={operators} units={units} groups={groups} />;
          case 'DOCUMENTS':
              return <SupportingDocumentsManager user={user} units={units} groups={groups} documents={documents} onGenerateDocuments={handleGenerateDocuments} operators={operators} serviceProviders={serviceProviders} />;
          case 'CONTRACTS':
              return <ContractManager user={user} contracts={contracts} operators={operators} serviceProviders={serviceProviders} onCreateContract={handleCreateContract} onUpdateContract={() => {}} />;
          case 'VERIFICATION':
              return <VerificationCenter operators={operators} onUpdateOperator={handleOperatorUpdate} />;
          case 'CERTIFICATES':
              return <CertificationManager user={user} units={units} groups={groups} operators={operators} documents={documents} />;
          case 'SETTINGS':
              return <EmissionFactorSettings factors={emissionFactors} onUpdateFactors={setEmissionFactors} />;
          case 'KNOWLEDGE':
              return <KnowledgeBase entries={knowledgeEntries} role={user.role} onCreate={entry => setKnowledgeEntries([...knowledgeEntries, entry])} onUpdate={entry => setKnowledgeEntries(knowledgeEntries.map(e => e.id === entry.id ? entry : e))} onDelete={id => setKnowledgeEntries(knowledgeEntries.filter(e => e.id !== id))} />;
          case 'NEWSLETTER':
              return (
                <Newsletter
                    user={user}
                    onEditCampaign={(id) => {
                        setSelectedItemId(id);
                        setActiveView('NEWSLETTER_EDITOR');
                    }}
                />
              );
          case 'NEWSLETTER_EDITOR':
              return (
                <NewsletterEditor
                    campaignId={selectedItemId}
                    user={user}
                    onBack={() => { setActiveView('NEWSLETTER'); setSelectedItemId(null); }}
                />
              );
          case 'TEMPLATES':
              return (
                <TemplateManager
                    templates={templates}
                    onAddTemplate={(t) => setTemplates([...templates, t])}
                    onUpdateTemplate={(updated) => setTemplates(templates.map(t => t.id === updated.id ? updated : t))}
                    onDeleteTemplate={(id) => setTemplates(templates.filter(t => t.id !== id))}
                />
              );
          default:
              return <div>Ansicht nicht gefunden</div>;
      }
  };

  // Onboarding Modal Overlay
  if (showOnboarding) {
      return (
          <div className="fixed inset-0 z-50 bg-slate-50 overflow-y-auto">
              <Onboarding user={user} onComplete={handleOnboardingComplete} />
          </div>
      );
  }

  // --- MAIN LAYOUT ---
  return (
    <div className="flex min-h-[calc(100vh-80px)] bg-slate-50">
        {/* Sidebar */}
        <aside className={`fixed inset-y-0 left-0 z-40 w-64 bg-white border-r border-slate-200 transform transition-transform duration-300 ease-in-out md:translate-x-0 md:static md:inset-auto mt-20 md:mt-0 ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}`}>
            <nav className="p-4 space-y-1">
                <NavItem icon={<LayoutDashboard size={20} />} label="Übersicht" isActive={activeView === 'DASHBOARD'} onClick={() => { setActiveView('DASHBOARD'); setSelectedItemId(null); }} />

                <div className="pt-4 pb-2 text-xs font-bold text-slate-400 uppercase tracking-wider pl-3">Verwaltung</div>
                <NavItem icon={<Factory size={20} />} label="Anlagen" isActive={activeView === 'UNITS'} onClick={() => { setActiveView('UNITS'); setSelectedItemId(null); }} />
                <NavItem icon={<Layers size={20} />} label="Gruppen" isActive={activeView === 'GROUPS'} onClick={() => { setActiveView('GROUPS'); setSelectedItemId(null); }} />
                {(user.role === UserRole.ADMIN || user.role === UserRole.SERVICE_PROVIDER) && (
                    <NavItem icon={<Users size={20} />} label="Betreiber" isActive={activeView === 'OPERATORS'} onClick={() => { setActiveView('OPERATORS'); setSelectedItemId(null); }} />
                )}
                {user.role === UserRole.ADMIN && (
                    <NavItem icon={<Database size={20} />} label="Serviceprovider" isActive={activeView === 'SERVICE_PROVIDERS'} onClick={() => { setActiveView('SERVICE_PROVIDERS'); setSelectedItemId(null); }} />
                )}

                <div className="pt-4 pb-2 text-xs font-bold text-slate-400 uppercase tracking-wider pl-3">Zertifizierung</div>
                <NavItem icon={<FolderOpen size={20} />} label="Begleitdokumente" isActive={activeView === 'DOCUMENTS'} onClick={() => setActiveView('DOCUMENTS')} />
                <NavItem icon={<FileText size={20} />} label="Berichte" isActive={activeView === 'REPORTS'} onClick={() => setActiveView('REPORTS')} />
                <NavItem icon={<Award size={20} />} label="Zertifikate" isActive={activeView === 'CERTIFICATES'} onClick={() => setActiveView('CERTIFICATES')} />
                {(user.role === UserRole.ADMIN || user.role === UserRole.SERVICE_PROVIDER) && (
                    <>
                    <NavItem icon={<ShieldCheck size={20} />} label="Verifizierung" isActive={activeView === 'VERIFICATION'} onClick={() => setActiveView('VERIFICATION')} />
                    <NavItem icon={<FileSignature size={20} />} label="Verträge" isActive={activeView === 'CONTRACTS'} onClick={() => setActiveView('CONTRACTS')} />
                    </>
                )}

                {(user.role === UserRole.ADMIN) && (
                    <NavItem icon={<Wand2 size={20} />} label="Vorlagengenerator" isActive={activeView === 'TEMPLATES'} onClick={() => setActiveView('TEMPLATES')} />
                )}

                {(user.role === UserRole.ADMIN || user.role === UserRole.SERVICE_PROVIDER) && (
                    <>
                    <div className="pt-4 pb-2 text-xs font-bold text-slate-400 uppercase tracking-wider pl-3">Marketing</div>
                    <NavItem icon={<Mail size={20} />} label="Newsletter" isActive={activeView === 'NEWSLETTER' || activeView === 'NEWSLETTER_EDITOR'} onClick={() => { setActiveView('NEWSLETTER'); setSelectedItemId(null); }} />
                    </>
                )}

                <div className="pt-4 pb-2 text-xs font-bold text-slate-400 uppercase tracking-wider pl-3">System</div>
                <NavItem icon={<Users size={20} />} label="Benutzer" isActive={activeView === 'USERS'} onClick={() => setActiveView('USERS')} />
                <NavItem icon={<HelpCircle size={20} />} label="Wissensdatenbank" isActive={activeView === 'KNOWLEDGE'} onClick={() => setActiveView('KNOWLEDGE')} />
                {user.role === UserRole.ADMIN && (
                    <NavItem icon={<TrendingDown size={20} />} label="Emissionsfaktoren" isActive={activeView === 'SETTINGS'} onClick={() => setActiveView('SETTINGS')} />
                )}
            </nav>
        </aside>

        {/* Mobile Toggle */}
        <button
            className="fixed bottom-6 right-6 md:hidden z-50 bg-silva-primary text-white p-3 rounded-full shadow-lg"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        >
            {mobileMenuOpen ? <X /> : <Menu />}
        </button>

        {/* Content Area */}
        <main className="flex-1 p-4 md:p-8 overflow-y-auto">
            <div className="max-w-7xl mx-auto">
                {renderContent()}
            </div>
        </main>
    </div>
  );
};

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
