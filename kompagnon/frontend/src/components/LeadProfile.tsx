import React, { useState, useEffect, useCallback } from 'react';
import {
  ArrowLeft, Edit2, ClipboardList, SearchCheck, Download, Loader2,
  CheckCircle2, Clock, Building, Mail, Phone, MapPin, Wand2, ExternalLink,
  FolderOpen, Plus,
} from 'lucide-react';
import BriefingWizard, { BriefingFormData } from './BriefingWizard';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface LeadData {
  id: number;
  firma?: string;
  name?: string;
  email?: string;
  telefon?: string;
  ort?: string;
  status?: string;
  created_at?: string;
}

interface BriefingRecord {
  id: number;
  lead_id: number;
  gewerk?: string;
  leistungen?: string;
  einzugsgebiet?: string;
  zielgruppe?: string;
  usp?: string;
  mitbewerber?: string;
  vorbilder?: string;
  farben?: string;
  stil?: string;
  wunschseiten?: string;
  logo_vorhanden?: boolean;
  fotos_vorhanden?: boolean;
  sonstige_hinweise?: string;
  status?: string;
  created_at?: string;
  updated_at?: string;
}

interface ProjectInfo {
  id: number;
  name: string;
  current_phase: number;
  status: string;
  lead_id: number;
}

interface LeadProfileProps {
  lead: LeadData;
  onBack: () => void;
  onEdit: (lead: LeadData) => void;
  onNavigateToProject?: (projectId: number) => void;
}

// ---------------------------------------------------------------------------
// API helper
// ---------------------------------------------------------------------------

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem('silva_token') || '';
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const LeadProfile: React.FC<LeadProfileProps> = ({ lead, onBack, onEdit, onNavigateToProject }) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'mockup'>('overview');

  // Project state
  const [project, setProject] = useState<ProjectInfo | null>(null);
  const [projectLoading, setProjectLoading] = useState(true);
  const [projectCreating, setProjectCreating] = useState(false);

  // Briefing state
  const [briefing, setBriefing] = useState<BriefingRecord | null>(null);
  const [briefingLoading, setBriefingLoading] = useState(true);
  const [showWizard, setShowWizard] = useState(false);

  // Mockup state
  const [mockupGenerating, setMockupGenerating] = useState(false);
  const [mockupResult, setMockupResult] = useState<string | null>(null);
  const [mockupError, setMockupError] = useState<string | null>(null);

  // ------ Fetch project ------

  const loadProject = useCallback(async () => {
    setProjectLoading(true);
    try {
      const res = await fetch(`/api/projects?lead_id=${lead.id}`, { headers: authHeaders() });
      if (res.ok) {
        const data = await res.json();
        const proj = Array.isArray(data) ? data[0] : data;
        setProject(proj?.id ? proj : null);
      } else {
        setProject(null);
      }
    } catch {
      setProject(null);
    } finally {
      setProjectLoading(false);
    }
  }, [lead.id]);

  useEffect(() => { loadProject(); }, [loadProject]);

  const handleCreateProject = async () => {
    setProjectCreating(true);
    try {
      const res = await fetch(`/api/projects/from-lead/${lead.id}`, {
        method: 'POST',
        headers: authHeaders(),
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => null);
        throw new Error(detail?.detail || 'Projekt konnte nicht angelegt werden.');
      }
      const proj = await res.json();
      setProject(proj);
    } catch (err: any) {
      alert(err.message);
    } finally {
      setProjectCreating(false);
    }
  };

  // ------ Fetch briefing status ------

  const loadBriefing = useCallback(async () => {
    setBriefingLoading(true);
    try {
      const res = await fetch(`/api/briefings/${lead.id}`, { headers: authHeaders() });
      if (res.ok) {
        setBriefing(await res.json());
      } else {
        setBriefing(null);
      }
    } catch {
      setBriefing(null);
    } finally {
      setBriefingLoading(false);
    }
  }, [lead.id]);

  useEffect(() => { loadBriefing(); }, [loadBriefing]);

  // ------ Briefing actions ------

  const handleStartBriefing = () => {
    setShowWizard(true);
  };

  const handleBriefingComplete = (_data: BriefingFormData) => {
    setShowWizard(false);
    loadBriefing();
  };

  const handleDownloadPdf = async () => {
    try {
      const res = await fetch(`/api/briefings/${lead.id}/pdf`, { headers: authHeaders() });
      if (!res.ok) throw new Error();
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `briefing-${lead.id}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch {
      alert('PDF-Download fehlgeschlagen.');
    }
  };

  // ------ Mockup generation with briefing data ------

  const handleGenerateMockup = async () => {
    setMockupGenerating(true);
    setMockupError(null);

    try {
      // Fetch latest briefing data to pass to mockup generator
      let briefingPayload: Record<string, any> = {};
      try {
        const bRes = await fetch(`/api/briefings/${lead.id}`, { headers: authHeaders() });
        if (bRes.ok) {
          const b = await bRes.json();
          briefingPayload = {
            gewerk: b.gewerk || '',
            leistungen: b.leistungen || '',
            usp: b.usp || '',
            zielgruppe: b.zielgruppe || '',
            einzugsgebiet: b.einzugsgebiet || '',
            wunschseiten: b.wunschseiten || '',
          };
        }
      } catch {
        // No briefing available — proceed with base data only
      }

      const res = await fetch('/api/mockup/generate', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({
          lead_id: lead.id,
          firma: lead.firma || '',
          name: lead.name || '',
          ...briefingPayload,
        }),
      });

      if (!res.ok) throw new Error(`Mockup-Generierung fehlgeschlagen (${res.status})`);
      const data = await res.json();
      setMockupResult(data.html || data.url || JSON.stringify(data));
    } catch (err: any) {
      setMockupError(err.message || 'Mockup konnte nicht generiert werden.');
    } finally {
      setMockupGenerating(false);
    }
  };

  // ======================================================================
  // RENDER
  // ======================================================================

  return (
    <div className="space-y-6">
      {/* ---- Header ---- */}
      <div>
        <button onClick={onBack} className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 mb-4">
          <ArrowLeft size={16} /> Zurueck zur Liste
        </button>

        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            {/* Lead info */}
            <div>
              <h1 className="text-xl font-bold text-slate-800">{lead.firma || lead.name || `Lead #${lead.id}`}</h1>
              {lead.name && lead.firma && (
                <p className="text-sm text-slate-500 mt-0.5">{lead.name}</p>
              )}
              <div className="flex flex-wrap gap-x-4 gap-y-1 mt-3 text-sm text-slate-500">
                {lead.email && (
                  <span className="flex items-center gap-1"><Mail size={14} /> {lead.email}</span>
                )}
                {lead.telefon && (
                  <span className="flex items-center gap-1"><Phone size={14} /> {lead.telefon}</span>
                )}
                {lead.ort && (
                  <span className="flex items-center gap-1"><MapPin size={14} /> {lead.ort}</span>
                )}
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex flex-wrap gap-2 shrink-0">
              <button
                onClick={() => onEdit(lead)}
                className="flex items-center gap-1.5 px-3 py-2 text-sm rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 transition-colors"
              >
                <Edit2 size={14} /> Bearbeiten
              </button>
              <button
                className="flex items-center gap-1.5 px-3 py-2 text-sm rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 transition-colors"
              >
                <SearchCheck size={14} /> Audit starten
              </button>
              <button
                onClick={handleStartBriefing}
                className="flex items-center gap-1.5 px-3 py-2 text-sm rounded-lg border border-[#008eaa] text-[#008eaa] hover:bg-[#008eaa]/5 transition-colors"
              >
                <ClipboardList size={14} /> Briefing starten
              </button>
            </div>
          </div>

          {/* Briefing status */}
          <div className="mt-4 pt-4 border-t border-slate-100">
            {briefingLoading ? (
              <span className="flex items-center gap-1.5 text-sm text-slate-400">
                <Loader2 size={14} className="animate-spin" /> Briefing-Status wird geladen…
              </span>
            ) : briefing ? (
              <div className="flex flex-wrap items-center gap-3">
                <span className="flex items-center gap-1.5 text-sm text-emerald-600 font-medium">
                  <CheckCircle2 size={14} /> Briefing ausgefuellt
                  {briefing.updated_at && (
                    <span className="font-normal text-slate-400 ml-1">
                      · {new Date(briefing.updated_at).toLocaleDateString('de-DE')}
                    </span>
                  )}
                </span>
                <button
                  onClick={handleDownloadPdf}
                  className="flex items-center gap-1 text-sm text-[#008eaa] hover:underline"
                >
                  <Download size={13} /> PDF herunterladen
                </button>
              </div>
            ) : (
              <span className="text-sm text-slate-400">Noch kein Briefing vorhanden</span>
            )}
          </div>
        </div>
      </div>

      {/* ---- Verknuepftes Projekt ---- */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
        <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wide mb-3 flex items-center gap-1.5">
          <FolderOpen size={14} /> Verknuepftes Projekt
        </h3>
        {projectLoading ? (
          <span className="flex items-center gap-1.5 text-sm text-slate-400">
            <Loader2 size={14} className="animate-spin" /> Wird geladen…
          </span>
        ) : project ? (
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-4 rounded-lg" style={{ backgroundColor: 'rgba(13,110,253,0.08)' }}>
            <div>
              <p className="text-sm font-medium text-slate-800">{project.name}</p>
              <div className="flex items-center gap-3 mt-1 text-xs text-slate-500">
                <span>Phase {project.current_phase} von 7</span>
                <span className="px-1.5 py-0.5 rounded-full bg-emerald-100 text-emerald-700 font-medium">{project.status}</span>
              </div>
            </div>
            <button
              onClick={() => onNavigateToProject?.(project.id)}
              className="flex items-center gap-1.5 px-3 py-2 text-sm rounded-lg bg-[#008eaa] text-white hover:bg-[#007494] transition-colors shrink-0"
            >
              <FolderOpen size={14} /> Zum Projekt
            </button>
          </div>
        ) : (
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <span className="text-sm text-slate-400">Noch kein Projekt angelegt</span>
            <button
              onClick={handleCreateProject}
              disabled={projectCreating}
              className="flex items-center gap-1.5 px-3 py-2 text-sm rounded-lg border border-[#008eaa] text-[#008eaa] hover:bg-[#008eaa]/5 disabled:opacity-50 transition-colors shrink-0"
            >
              {projectCreating ? (
                <><Loader2 size={14} className="animate-spin" /> Wird angelegt…</>
              ) : (
                <><Plus size={14} /> Projekt anlegen</>
              )}
            </button>
          </div>
        )}
      </div>

      {/* ---- Tabs ---- */}
      <div className="border-b border-slate-200">
        <div className="flex gap-6">
          <TabBtn label="Uebersicht" active={activeTab === 'overview'} onClick={() => setActiveTab('overview')} />
          <TabBtn label="Design" active={activeTab === 'mockup'} onClick={() => setActiveTab('mockup')} />
        </div>
      </div>

      {/* ---- Tab content ---- */}
      {activeTab === 'overview' && (
        <div className="space-y-4">
          {/* Lead details card */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
            <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wide mb-4">Kontaktdaten</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
              <InfoRow icon={<Building size={14} />} label="Firma" value={lead.firma} />
              <InfoRow icon={<Mail size={14} />} label="E-Mail" value={lead.email} />
              <InfoRow icon={<Phone size={14} />} label="Telefon" value={lead.telefon} />
              <InfoRow icon={<MapPin size={14} />} label="Ort" value={lead.ort} />
            </div>
          </div>

          {/* Briefing summary if available */}
          {briefing && (
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
              <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wide mb-4">Briefing-Zusammenfassung</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                <InfoRow label="Gewerk" value={briefing.gewerk} />
                <InfoRow label="Einzugsgebiet" value={briefing.einzugsgebiet} />
                <InfoRow label="Zielgruppe" value={briefing.zielgruppe} />
                <InfoRow label="Stil" value={briefing.stil} />
                <div className="sm:col-span-2">
                  <InfoRow label="USP" value={briefing.usp} />
                </div>
                <div className="sm:col-span-2">
                  <InfoRow label="Wunschseiten" value={briefing.wunschseiten} />
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'mockup' && (
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wide">KI-Design generieren</h3>
                <p className="text-sm text-slate-400 mt-1">
                  {briefing
                    ? 'Briefing-Daten werden automatisch an den Design-Editor uebergeben.'
                    : 'Ohne Briefing werden nur die Basisdaten verwendet. Fuer bessere Ergebnisse zuerst ein Briefing erstellen.'}
                </p>
              </div>
              {!briefing && (
                <button
                  onClick={handleStartBriefing}
                  className="shrink-0 flex items-center gap-1.5 text-sm text-[#008eaa] hover:underline"
                >
                  <ClipboardList size={14} /> Briefing erstellen
                </button>
              )}
            </div>

            {/* Briefing fields that will be passed */}
            {briefing && (
              <div className="mb-4 p-3 bg-slate-50 rounded-lg text-xs text-slate-500 space-y-0.5">
                <p className="font-medium text-slate-600 mb-1">Folgende Briefing-Daten fliessen ein:</p>
                <p>Gewerk: {briefing.gewerk || '—'} · Leistungen: {(briefing.leistungen || '—').slice(0, 60)}{(briefing.leistungen || '').length > 60 ? '…' : ''}</p>
                <p>USP: {(briefing.usp || '—').slice(0, 60)}{(briefing.usp || '').length > 60 ? '…' : ''}</p>
                <p>Zielgruppe: {briefing.zielgruppe || '—'} · Einzugsgebiet: {briefing.einzugsgebiet || '—'}</p>
                <p>Wunschseiten: {briefing.wunschseiten || '—'}</p>
              </div>
            )}

            <button
              onClick={handleGenerateMockup}
              disabled={mockupGenerating}
              className="flex items-center gap-2 px-5 py-2.5 text-sm rounded-lg bg-[#008eaa] text-white hover:bg-[#007494] disabled:opacity-50 transition-colors"
            >
              {mockupGenerating ? (
                <><Loader2 size={16} className="animate-spin" /> Wird generiert…</>
              ) : (
                <><Wand2 size={16} /> KI-Entwurf generieren</>
              )}
            </button>

            {mockupError && (
              <p className="mt-3 text-sm text-red-500">{mockupError}</p>
            )}
          </div>

          {/* Mockup result */}
          {mockupResult && (
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="px-6 py-3 border-b border-slate-200 flex items-center justify-between">
                <h4 className="text-sm font-medium text-slate-700">Generierter Entwurf</h4>
                <a
                  href={mockupResult.startsWith('http') ? mockupResult : undefined}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`flex items-center gap-1 text-sm text-[#008eaa] hover:underline ${mockupResult.startsWith('http') ? '' : 'hidden'}`}
                >
                  <ExternalLink size={13} /> In neuem Tab oeffnen
                </a>
              </div>
              {mockupResult.startsWith('<') ? (
                <iframe
                  srcDoc={mockupResult}
                  title="Design Vorschau"
                  sandbox=""
                  className="w-full border-0"
                  style={{ height: '500px' }}
                />
              ) : (
                <div className="p-6 text-sm text-slate-600 whitespace-pre-wrap">{mockupResult}</div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ---- BriefingWizard Modal ---- */}
      {showWizard && (
        <BriefingWizard
          leadId={lead.id}
          leadData={{ firma: lead.firma, name: lead.name }}
          onClose={() => setShowWizard(false)}
          onComplete={handleBriefingComplete}
        />
      )}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

const TabBtn: React.FC<{ label: string; active: boolean; onClick: () => void }> = ({ label, active, onClick }) => (
  <button
    onClick={onClick}
    className={`pb-3 text-sm font-medium transition-colors border-b-2 ${
      active
        ? 'border-[#008eaa] text-[#008eaa]'
        : 'border-transparent text-slate-500 hover:text-slate-700'
    }`}
  >
    {label}
  </button>
);

const InfoRow: React.FC<{ icon?: React.ReactNode; label: string; value?: string | null }> = ({ icon, label, value }) => (
  <div className="flex gap-2">
    {icon && <span className="text-slate-400 mt-0.5 shrink-0">{icon}</span>}
    <div>
      <p className="text-xs text-slate-400">{label}</p>
      <p className="text-slate-800">{value || '—'}</p>
    </div>
  </div>
);

export default LeadProfile;
