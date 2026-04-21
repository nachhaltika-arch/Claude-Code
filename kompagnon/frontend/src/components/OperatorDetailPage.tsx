import React, { useState } from 'react';
import { Operator, User, canEditOperator, ContractInstance, UserRole } from '../types';
import { ArrowLeft, Edit2, MapPin, Mail, Building, User as UserIcon, Phone, Globe, FileText, Briefcase, CheckCircle2, AlertTriangle, FileSignature, Eye, Download, Loader2 } from 'lucide-react';
import OperatorForm from './OperatorForm';
import * as API from '../services/api';

interface OperatorDetailPageProps {
  operator: Operator;
  user: User;
  onBack: () => void;
  onUpdateOperator: (updatedOperator: Operator) => void;
  contracts: ContractInstance[]; // NEW
  onRefreshContracts: () => void; // NEW
  hideBackButton?: boolean;
}

const OperatorDetailPage: React.FC<OperatorDetailPageProps> = ({
  operator,
  user,
  onBack,
  onUpdateOperator,
  contracts,
  onRefreshContracts,
  hideBackButton = false
}) => {
  const [activeTab, setActiveTab] = useState<'OVERVIEW' | 'CONTRACTS'>('OVERVIEW');
  const [isEditing, setIsEditing] = useState(false);
  const [isGeneratingContract, setIsGeneratingContract] = useState(false);

  const handleSave = (updatedData: Operator) => {
    onUpdateOperator(updatedData);
    setIsEditing(false);
  };

  const handleCreateContract = async () => {
      if (user.role !== UserRole.ADMIN) return;
      setIsGeneratingContract(true);
      try {
          const dbContext: API.DbContext = {
              units: [], groups: [], operators: [operator], serviceProviders: [], documents: [], contracts
          };
          await API.postOperatorContract(operator.id, { validFrom: new Date().toISOString().split('T')[0] }, user.username, dbContext);
          onRefreshContracts();
          alert("Rahmenvertrag erfolgreich erstellt.");
      } catch (e: any) {
          console.error(e);
          alert("Fehler bei Vertragserstellung.");
      } finally {
          setIsGeneratingContract(false);
      }
  };

  const hasPermission = canEditOperator(user, operator);
  const opContracts = contracts.filter(c => c.operatorId === operator.id);

  const getStatusBadge = (status: string) => {
      switch(status) {
          case 'signed': return <span className="bg-emerald-100 text-emerald-800 px-2 py-1 rounded-full text-xs font-bold flex items-center gap-1 w-fit"><CheckCircle2 size={12}/> Aktiv</span>;
          case 'draft': return <span className="bg-slate-100 text-slate-600 px-2 py-1 rounded-full text-xs font-bold flex items-center gap-1 w-fit"><FileSignature size={12}/> Entwurf</span>;
          default: return <span className="bg-slate-100 text-slate-500 px-2 py-1 rounded-full text-xs font-bold w-fit">{status}</span>;
      }
  };

  if (isEditing) {
      return (
          <div className="animate-fade-in">
              <OperatorForm
                initialData={operator}
                onSave={handleSave}
                onCancel={() => setIsEditing(false)}
              />
          </div>
      );
  }

  // Display Logic Helpers
  const displayAddress = operator.strasse
    ? `${operator.strasse} ${operator.hausnummer || ''}, ${operator.plz} ${operator.ort}`
    : operator.address || '-';

  return (
    <div className="animate-fade-in space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          {!hideBackButton && (
            <button
                onClick={onBack}
                className="p-2 rounded-full hover:bg-slate-100 text-slate-600 transition-colors"
            >
                <ArrowLeft size={24} />
            </button>
          )}
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-slate-900">
                {operator.name}
              </h1>
              <span className="bg-emerald-100 text-emerald-800 px-2.5 py-0.5 rounded-full text-xs font-medium">
                {operator.rechtsform || 'Anlagenbetreiber'}
              </span>
            </div>
            <p className="text-slate-500 flex items-center gap-2 mt-1">
              ID: {operator.id}
            </p>
          </div>
        </div>

        {activeTab === 'OVERVIEW' && hasPermission && (
          <button
            onClick={() => setIsEditing(true)}
            className="flex items-center gap-2 px-4 py-2 border border-slate-300 rounded-lg text-slate-700 hover:bg-slate-50 transition-colors font-medium"
          >
            <Edit2 size={16} /> Bearbeiten
          </button>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200 mb-6">
          <nav className="-mb-px flex gap-6">
              <button onClick={() => setActiveTab('OVERVIEW')} className={`py-4 px-1 border-b-2 font-medium text-sm ${activeTab === 'OVERVIEW' ? 'border-emerald-500 text-emerald-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}>Übersicht</button>
              <button onClick={() => setActiveTab('CONTRACTS')} className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${activeTab === 'CONTRACTS' ? 'border-emerald-500 text-emerald-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}>
                  <FileSignature size={16} /> Verträge
              </button>
          </nav>
      </div>

      {activeTab === 'CONTRACTS' ? (
          <div className="space-y-6 animate-fade-in">
              {user.role === UserRole.ADMIN && (
                  <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex justify-between items-center">
                      <div>
                          <h3 className="font-bold text-slate-800">Neuen Vertrag erstellen</h3>
                          <p className="text-sm text-slate-500">Erstellt einen Standard-Rahmenvertrag für diesen Anlagenbetreiber.</p>
                      </div>
                      <button
                          onClick={handleCreateContract}
                          disabled={isGeneratingContract}
                          className="flex items-center gap-2 bg-silva-primary text-white px-5 py-2 rounded-lg font-bold shadow-md hover:bg-silva-dark transition-all disabled:opacity-50"
                      >
                          {isGeneratingContract ? <Loader2 className="animate-spin" size={18} /> : <FileSignature size={18} />}
                          Rahmenvertrag erstellen
                      </button>
                  </div>
              )}

              <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                  <div className="px-6 py-4 border-b border-slate-100 bg-slate-50">
                      <h4 className="font-bold text-slate-800">Vertragsübersicht</h4>
                  </div>
                  {opContracts.length === 0 ? (
                      <div className="p-12 text-center text-slate-500">Keine Verträge vorhanden.</div>
                  ) : (
                      <div className="divide-y divide-slate-100">
                          {opContracts.map(contract => (
                              <div key={contract.id} className="px-6 py-4 flex items-center justify-between hover:bg-slate-50">
                                  <div>
                                      <div className="font-medium text-slate-900">
                                          {contract.contractType === 'OPERATOR_FRAME' ? 'Rahmenvertrag Betreiber' : 'Anlagenzuordnung'}
                                      </div>
                                      <div className="text-xs text-slate-500 mt-1 flex gap-3">
                                          <span>ID: {contract.id}</span>
                                          <span>•</span>
                                          <span>Vom: {new Date(contract.createdAt).toLocaleDateString()}</span>
                                      </div>
                                  </div>
                                  <div className="flex items-center gap-6">
                                      {getStatusBadge(contract.status)}
                                      <div className="flex gap-2">
                                          <button className="p-2 text-slate-400 hover:text-blue-600 bg-slate-50 rounded"><Eye size={16}/></button>
                                          <button className="p-2 text-slate-400 hover:text-emerald-600 bg-slate-50 rounded"><Download size={16}/></button>
                                      </div>
                                  </div>
                              </div>
                          ))}
                      </div>
                  )}
              </div>
          </div>
      ) : (
          /* OVERVIEW CONTENT */
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Card: MaStR Status */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden md:col-span-2">
                <div className="px-6 py-4 border-b border-slate-100 bg-slate-50 flex items-center gap-2">
                    <Building size={18} className="text-slate-600" />
                    <h3 className="font-bold text-slate-800">Marktstammdatenregister</h3>
                </div>
                <div className="p-6 flex flex-col md:flex-row gap-6">
                    <div className="flex-1">
                        <span className="block text-sm font-medium text-slate-500 mb-1">ABR-Nummer</span>
                        <div className="flex items-center gap-2">
                            {operator.abrNummer ? (
                                <span className="text-lg font-mono font-medium text-slate-900">{operator.abrNummer}</span>
                            ) : (
                                <span className="flex items-center gap-1.5 text-amber-600 bg-amber-50 px-2 py-1 rounded text-sm font-medium">
                                    <AlertTriangle size={14} /> Fehlt
                                </span>
                            )}
                        </div>
                    </div>
                    <div className="flex-1">
                        <span className="block text-sm font-medium text-slate-500 mb-1">Nachweis-Dokument</span>
                        {operator.maStRProof ? (
                            <div className="flex items-center gap-2 text-emerald-700 bg-emerald-50 px-3 py-2 rounded-lg border border-emerald-100">
                                <CheckCircle2 size={16} />
                                <span className="text-sm font-medium">{operator.maStRProof.fileName}</span>
                            </div>
                        ) : (
                            <span className="flex items-center gap-1.5 text-slate-400 italic text-sm mt-1">
                                Kein Dokument hochgeladen
                            </span>
                        )}
                    </div>
                </div>
            </div>

            {/* Card: Kontakt & Adresse */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-100 bg-slate-50 flex items-center gap-2">
                    <MapPin size={18} className="text-emerald-600" />
                    <h3 className="font-bold text-slate-800">Adresse & Kontakt</h3>
                </div>
                <div className="p-6 space-y-4">
                    <div className="flex items-start gap-3">
                        <MapPin className="text-slate-400 mt-0.5 flex-shrink-0" size={18} />
                        <div>
                            <span className="block text-sm font-medium text-slate-500">Anschrift</span>
                            <span className="text-slate-900">{displayAddress}</span>
                            {operator.land && <span className="block text-slate-600 text-sm">{operator.land}</span>}
                        </div>
                    </div>
                    <div className="flex items-start gap-3">
                        <Mail className="text-slate-400 mt-0.5 flex-shrink-0" size={18} />
                        <div>
                            <span className="block text-sm font-medium text-slate-500">E-Mail</span>
                            <a href={`mailto:${operator.contactEmail}`} className="text-emerald-600 hover:underline">{operator.contactEmail}</a>
                        </div>
                    </div>
                    {operator.telefon && (
                        <div className="flex items-start gap-3">
                            <Phone className="text-slate-400 mt-0.5 flex-shrink-0" size={18} />
                            <div>
                                <span className="block text-sm font-medium text-slate-500">Telefon</span>
                                <span className="text-slate-900">{operator.telefon}</span>
                            </div>
                        </div>
                    )}
                    {operator.webseite && (
                        <div className="flex items-start gap-3">
                            <Globe className="text-slate-400 mt-0.5 flex-shrink-0" size={18} />
                            <div>
                                <span className="block text-sm font-medium text-slate-500">Webseite</span>
                                <a href={operator.webseite} target="_blank" rel="noreferrer" className="text-emerald-600 hover:underline">{operator.webseite}</a>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Card: Rechtliches */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-100 bg-slate-50 flex items-center gap-2">
                    <FileText size={18} className="text-blue-600" />
                    <h3 className="font-bold text-slate-800">Rechtliches & Steuer</h3>
                </div>
                <div className="p-6 space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <span className="block text-sm font-medium text-slate-500">Rechtsform</span>
                            <span className="text-slate-900">{operator.rechtsform || '-'}</span>
                        </div>
                        <div>
                            <span className="block text-sm font-medium text-slate-500">Umsatzsteuer-ID</span>
                            <span className="text-slate-900 font-mono text-sm">{operator.ustId || '-'}</span>
                        </div>
                        <div>
                            <span className="block text-sm font-medium text-slate-500">Registergericht</span>
                            <span className="text-slate-900">{operator.registergericht || '-'}</span>
                        </div>
                        <div>
                            <span className="block text-sm font-medium text-slate-500">Registernummer</span>
                            <span className="text-slate-900">{operator.registernummer || '-'}</span>
                        </div>
                    </div>
                    <div>
                        <span className="block text-sm font-medium text-slate-500">ACER-Code</span>
                        <span className="text-slate-900 font-mono text-sm">{operator.acerCode || '-'}</span>
                    </div>
                </div>
            </div>

            {/* Card: Wirtschaft */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-100 bg-slate-50 flex items-center gap-2">
                    <Briefcase size={18} className="text-purple-600" />
                    <h3 className="font-bold text-slate-800">Wirtschaftsdaten</h3>
                </div>
                <div className="p-6 space-y-4">
                     <div>
                         <span className="block text-sm font-medium text-slate-500">Wirtschaftszweig</span>
                         <span className="text-slate-900">{operator.wirtschaftszweigAbschnitt || '-'}</span>
                     </div>
                     <div className="flex items-center gap-2">
                        <span className={`w-3 h-3 rounded-full ${operator.kmuKriterium ? 'bg-emerald-500' : 'bg-slate-300'}`}></span>
                        <span className="text-slate-700">KMU Kriterien erfüllt</span>
                     </div>
                </div>
            </div>

            {/* Card: System & Zuordnung */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-100 bg-slate-50 flex items-center gap-2">
                    <Building size={18} className="text-slate-600" />
                    <h3 className="font-bold text-slate-800">Systemzuordnung</h3>
                </div>
                 <div className="p-6 space-y-4">
                <div>
                    <span className="block text-sm font-medium text-slate-500 mb-1">Zugeordneter Serviceprovider</span>
                    <div className="flex items-center gap-2">
                    {operator.serviceProviderId ? (
                        <span className="bg-blue-50 text-blue-700 px-3 py-1 rounded-full text-sm font-medium border border-blue-100">
                        {operator.serviceProviderId}
                        </span>
                    ) : (
                        <span className="text-slate-400 italic">Keine Zuordnung</span>
                    )}
                    </div>
                </div>
            </div>
        </div>

          </div>
      )}
    </div>
  );
};

export default OperatorDetailPage;
