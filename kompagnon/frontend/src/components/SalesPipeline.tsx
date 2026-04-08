import React, { useState, useEffect, useCallback, DragEvent } from 'react';
import {
  Plus, GripVertical, Building, Mail, X, CheckCircle2, Loader2, Trophy,
  FolderOpen,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Lead {
  id: number;
  firma: string;
  name: string;
  email?: string;
  status: string;
  created_at?: string;
}

interface ProjectInfo {
  id: number;
  name: string;
  current_phase: number;
  status: string;
  lead_id: number;
}

interface SalesPipelineProps {
  onSelectLead?: (lead: Lead) => void;
  onNavigateToProject?: (projectId: number) => void;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const STAGES: { key: string; label: string; color: string }[] = [
  { key: 'neu',          label: 'Neu',          color: 'bg-slate-100 text-slate-600' },
  { key: 'kontaktiert',  label: 'Kontaktiert',  color: 'bg-blue-100 text-blue-700' },
  { key: 'angebot',      label: 'Angebot',      color: 'bg-amber-100 text-amber-700' },
  { key: 'verhandlung',  label: 'Verhandlung',  color: 'bg-purple-100 text-purple-700' },
  { key: 'gewonnen',     label: 'Gewonnen',     color: 'bg-emerald-100 text-emerald-700' },
  { key: 'verloren',     label: 'Verloren',     color: 'bg-red-100 text-red-600' },
];

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

const SalesPipeline: React.FC<SalesPipelineProps> = ({ onSelectLead, onNavigateToProject }) => {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [draggedId, setDraggedId] = useState<number | null>(null);
  const [dragOverStage, setDragOverStage] = useState<string | null>(null);

  // Projects for won leads (keyed by lead_id)
  const [projects, setProjects] = useState<Record<number, ProjectInfo>>({});

  // "Gewonnen" modal
  const [wonModal, setWonModal] = useState<{ lead: Lead; targetStatus: string } | null>(null);
  const [projectCreating, setProjectCreating] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // ------ Data fetching ------

  const loadProjects = useCallback(async (allLeads: Lead[]) => {
    const wonLeads = allLeads.filter(l => l.status === 'gewonnen');
    if (wonLeads.length === 0) return;
    const results: Record<number, ProjectInfo> = {};
    await Promise.all(
      wonLeads.map(async (l) => {
        try {
          const res = await fetch(`/api/projects?lead_id=${l.id}`, { headers: authHeaders() });
          if (res.ok) {
            const data = await res.json();
            const proj = Array.isArray(data) ? data[0] : data;
            if (proj?.id) results[l.id] = proj;
          }
        } catch { /* ignore */ }
      }),
    );
    setProjects(results);
  }, []);

  const loadLeads = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/leads', { headers: authHeaders() });
      if (res.ok) {
        const data = await res.json();
        setLeads(data);
        loadProjects(data);
      }
    } catch { /* empty */ }
    finally { setLoading(false); }
  }, [loadProjects]);

  useEffect(() => { loadLeads(); }, [loadLeads]);

  // ------ Status update ------

  const saveStatus = async (leadId: number, newStatus: string) => {
    try {
      await fetch(`/api/leads/${leadId}/status`, {
        method: 'PUT',
        headers: authHeaders(),
        body: JSON.stringify({ status: newStatus }),
      });
      setLeads(prev => prev.map(l => l.id === leadId ? { ...l, status: newStatus } : l));
    } catch {
      alert('Status-Update fehlgeschlagen.');
    }
  };

  // ------ "Gewonnen" flow ------

  const initiateStatusChange = (lead: Lead, newStatus: string) => {
    if (newStatus === 'gewonnen' && lead.status !== 'gewonnen') {
      setWonModal({ lead, targetStatus: newStatus });
    } else {
      saveStatus(lead.id, newStatus);
    }
  };

  const handleWonSaveOnly = async () => {
    if (!wonModal) return;
    await saveStatus(wonModal.lead.id, wonModal.targetStatus);
    setWonModal(null);
  };

  const handleWonCreateProject = async () => {
    if (!wonModal) return;
    setProjectCreating(true);
    try {
      await saveStatus(wonModal.lead.id, wonModal.targetStatus);
      const res = await fetch(`/api/projects/from-lead/${wonModal.lead.id}`, {
        method: 'POST',
        headers: authHeaders(),
      });
      if (!res.ok) throw new Error();
      const projData = await res.json();
      setProjects(prev => ({ ...prev, [wonModal.lead.id]: projData }));
      setWonModal(null);
      setSuccessMsg('Projekt wurde angelegt!');
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch {
      alert('Projekt konnte nicht angelegt werden.');
    } finally {
      setProjectCreating(false);
    }
  };

  // ------ Drag & Drop ------

  const handleDragStart = (e: DragEvent, lead: Lead) => {
    setDraggedId(lead.id);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', String(lead.id));
  };

  const handleDragOver = (e: DragEvent, stageKey: string) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOverStage(stageKey);
  };

  const handleDragLeave = () => {
    setDragOverStage(null);
  };

  const handleDrop = (e: DragEvent, stageKey: string) => {
    e.preventDefault();
    setDragOverStage(null);
    const id = Number(e.dataTransfer.getData('text/plain'));
    const lead = leads.find(l => l.id === id);
    if (!lead || lead.status === stageKey) {
      setDraggedId(null);
      return;
    }
    initiateStatusChange(lead, stageKey);
    setDraggedId(null);
  };

  const handleDragEnd = () => {
    setDraggedId(null);
    setDragOverStage(null);
  };

  // ------ Dropdown status change ------

  const handleDropdownChange = (lead: Lead, newStatus: string) => {
    if (newStatus === lead.status) return;
    initiateStatusChange(lead, newStatus);
  };

  // ======================================================================
  // RENDER
  // ======================================================================

  const leadsForStage = (stageKey: string) => leads.filter(l => l.status === stageKey);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Vertriebspipeline</h1>
      </div>

      {/* Success toast */}
      {successMsg && (
        <div className="flex items-center gap-2 px-4 py-3 bg-emerald-50 border border-emerald-200 rounded-lg text-sm text-emerald-700 font-medium">
          <CheckCircle2 size={16} /> {successMsg}
        </div>
      )}

      {loading ? (
        <div className="text-center py-16 text-slate-400">Leads werden geladen…</div>
      ) : (
        /* Kanban board */
        <div className="flex gap-4 overflow-x-auto pb-4">
          {STAGES.map(stage => {
            const stageLeads = leadsForStage(stage.key);
            const isOver = dragOverStage === stage.key;
            return (
              <div
                key={stage.key}
                className={`flex-shrink-0 w-64 rounded-xl border transition-colors ${
                  isOver ? 'border-[#008eaa] bg-[#008eaa]/5' : 'border-slate-200 bg-slate-50'
                }`}
                onDragOver={e => handleDragOver(e, stage.key)}
                onDragLeave={handleDragLeave}
                onDrop={e => handleDrop(e, stage.key)}
              >
                {/* Column header */}
                <div className="px-4 py-3 border-b border-slate-200">
                  <div className="flex items-center justify-between">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${stage.color}`}>
                      {stage.label}
                    </span>
                    <span className="text-xs text-slate-400">{stageLeads.length}</span>
                  </div>
                </div>

                {/* Cards */}
                <div className="p-2 space-y-2 min-h-[120px]">
                  {stageLeads.map(lead => (
                    <div
                      key={lead.id}
                      draggable
                      onDragStart={e => handleDragStart(e, lead)}
                      onDragEnd={handleDragEnd}
                      className={`bg-white rounded-lg border border-slate-200 p-3 cursor-grab active:cursor-grabbing shadow-sm hover:shadow-md transition-all ${
                        draggedId === lead.id ? 'opacity-40' : ''
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        <GripVertical size={14} className="text-slate-300 mt-0.5 shrink-0" />
                        <div className="flex-1 min-w-0">
                          <p
                            className="text-sm font-medium text-slate-800 truncate cursor-pointer hover:text-[#008eaa]"
                            onClick={() => onSelectLead?.(lead)}
                          >
                            {lead.firma || lead.name}
                          </p>
                          {lead.name && lead.firma && (
                            <p className="text-xs text-slate-400 truncate">{lead.name}</p>
                          )}
                          {lead.email && (
                            <p className="text-xs text-slate-400 truncate flex items-center gap-1 mt-0.5">
                              <Mail size={10} /> {lead.email}
                            </p>
                          )}
                          {/* Inline status dropdown */}
                          <select
                            value={lead.status}
                            onChange={e => handleDropdownChange(lead, e.target.value)}
                            onClick={e => e.stopPropagation()}
                            className="mt-2 w-full text-xs border border-slate-200 rounded px-1.5 py-1 text-slate-500 bg-white focus:outline-none focus:ring-1 focus:ring-[#008eaa]/40"
                          >
                            {STAGES.map(s => (
                              <option key={s.key} value={s.key}>{s.label}</option>
                            ))}
                          </select>
                        </div>
                      </div>

                      {/* Project card for won leads */}
                      {lead.status === 'gewonnen' && projects[lead.id] && (
                        <div
                          onClick={(e) => { e.stopPropagation(); onNavigateToProject?.(projects[lead.id].id); }}
                          className="mt-2 p-2 rounded-md cursor-pointer hover:brightness-95 transition-all"
                          style={{ backgroundColor: 'rgba(13,110,253,0.08)' }}
                        >
                          <div className="flex items-center gap-1.5">
                            <FolderOpen size={12} className="text-blue-600" />
                            <span className="text-xs font-medium text-blue-700">Projekt aktiv</span>
                          </div>
                          <p className="text-[10px] text-blue-500 mt-0.5">
                            Phase {projects[lead.id].current_phase} von 7
                          </p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ===== "Gewonnen" Modal ===== */}
      {wonModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setWonModal(null)}>
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Trophy size={20} className="text-[#008eaa]" />
                <h3 className="text-lg font-bold text-slate-800">Projekt anlegen?</h3>
              </div>
              <button onClick={() => setWonModal(null)} className="p-1 rounded hover:bg-slate-100 text-slate-400">
                <X size={20} />
              </button>
            </div>

            <p className="text-sm text-slate-600 mb-6">
              Der Lead <strong>{wonModal.lead.firma || wonModal.lead.name}</strong> wurde als gewonnen markiert.
              Soll jetzt automatisch ein Projekt angelegt werden?
            </p>

            <div className="flex flex-col sm:flex-row gap-2">
              <button
                onClick={handleWonCreateProject}
                disabled={projectCreating}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg bg-[#008eaa] text-white hover:bg-[#007494] disabled:opacity-50 transition-colors"
              >
                {projectCreating ? (
                  <><Loader2 size={16} className="animate-spin" /> Wird angelegt…</>
                ) : (
                  'Ja, Projekt anlegen'
                )}
              </button>
              <button
                onClick={handleWonSaveOnly}
                disabled={projectCreating}
                className="flex-1 px-4 py-2.5 text-sm font-medium rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-50 transition-colors"
              >
                Nur Status speichern
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SalesPipeline;
