import React, { useState, useEffect, useCallback } from 'react';
import {
  Mail, Plus, Edit2, BarChart3, Trash2, RefreshCw, Upload, X,
  Send, Users, ListChecks, MousePointerClick, Copy, ChevronDown,
  ChevronRight, Eye, Loader2, Calendar, Zap, Hash, Clipboard, Check,
  ToggleLeft, ToggleRight,
} from 'lucide-react';
import { User } from '../types';
import NewsletterAnalytics from './NewsletterAnalytics';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Campaign {
  id: number;
  title: string;
  subject: string;
  status: string;
  sent_at: string | null;
  brevo_campaign_id: number | null;
}

interface CampaignDetail extends Campaign {
  preview_text: string | null;
  html_content: string | null;
  json_content: any;
  scheduled_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

interface NewsletterList {
  id: number;
  name: string;
  source: string;
  contact_count: number;
}

interface CampaignStats {
  openRate: number | null;
  clickRate: number | null;
  unsubscriptions: number | null;
}

interface NewsletterProps {
  user: User;
  onEditCampaign: (id: string) => void;
}

// ---------------------------------------------------------------------------
// API helper
// ---------------------------------------------------------------------------

const API_BASE = '/api/newsletter';

async function apiFetch<T = any>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('silva_token') || '';
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

type StatusFilter = 'all' | 'draft' | 'scheduled' | 'sent';

const STATUS_MAP: Record<string, { label: string; cls: string }> = {
  draft:     { label: 'Entwurf',   cls: 'bg-slate-100 text-slate-600' },
  scheduled: { label: 'Geplant',   cls: 'bg-blue-100 text-blue-700' },
  sent:      { label: 'Versendet', cls: 'bg-emerald-100 text-emerald-700' },
};

const SOURCE_MAP: Record<string, string> = {
  manual:   'Manuell',
  crm_sync: 'CRM',
  import:   'Import',
};

function fmtDate(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

function fmtDateTime(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('de-DE', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

function fmtPct(val: number | null): string {
  if (val == null) return '—';
  return `${(val * 100).toFixed(1)} %`;
}

// ---------------------------------------------------------------------------
// Automations & Merge Tags
// ---------------------------------------------------------------------------

interface AutomatedEmail {
  id: string;
  name: string;
  trigger: string;
  triggerLabel: string;
  subject: string;
  active: boolean;
  lastEdited?: string;
}

const MERGE_TAGS: { category: string; tags: { token: string; label: string }[] }[] = [
  {
    category: 'Kontakt / Empfaenger',
    tags: [
      { token: '{{kontakt.vorname}}', label: 'Vorname' },
      { token: '{{kontakt.nachname}}', label: 'Nachname' },
      { token: '{{kontakt.email}}', label: 'E-Mail-Adresse' },
      { token: '{{kontakt.anrede}}', label: 'Anrede (Herr/Frau)' },
    ],
  },
  {
    category: 'Firma / Stammdaten',
    tags: [
      { token: '{{firma.name}}', label: 'Firmenname' },
      { token: '{{firma.branche}}', label: 'Branche / Gewerk' },
      { token: '{{firma.ort}}', label: 'Ort' },
      { token: '{{firma.telefon}}', label: 'Telefonnummer' },
      { token: '{{firma.website}}', label: 'Website-URL' },
    ],
  },
  {
    category: 'Projekt',
    tags: [
      { token: '{{projekt.name}}', label: 'Projektname' },
      { token: '{{projekt.phase}}', label: 'Aktuelle Phase' },
      { token: '{{projekt.status}}', label: 'Projektstatus' },
    ],
  },
  {
    category: 'System',
    tags: [
      { token: '{{datum.heute}}', label: 'Heutiges Datum' },
      { token: '{{absender.name}}', label: 'Absender-Name' },
      { token: '{{absender.email}}', label: 'Absender-E-Mail' },
      { token: '{{abmelde_link}}', label: 'Abmelde-Link' },
    ],
  },
];

const DEFAULT_AUTOMATIONS: AutomatedEmail[] = [
  { id: 'auto-1', name: 'Willkommensmail', trigger: 'lead_created', triggerLabel: 'Neuer Lead erstellt', subject: 'Willkommen bei {{firma.name}}!', active: true, lastEdited: '2026-03-15' },
  { id: 'auto-2', name: 'Angebot Follow-up', trigger: 'status_angebot', triggerLabel: 'Status → Angebot (nach 3 Tagen)', subject: 'Ihr Angebot von {{firma.name}}', active: true, lastEdited: '2026-03-20' },
  { id: 'auto-3', name: 'Projekt-Kickoff', trigger: 'project_created', triggerLabel: 'Projekt angelegt', subject: 'Ihr Projekt "{{projekt.name}}" startet!', active: false, lastEdited: '2026-04-01' },
  { id: 'auto-4', name: 'Bewertungsanfrage', trigger: 'project_completed', triggerLabel: 'Projekt abgeschlossen', subject: 'Wie zufrieden sind Sie, {{kontakt.vorname}}?', active: false },
  { id: 'auto-5', name: 'Geburtstagswunsch', trigger: 'contact_birthday', triggerLabel: 'Geburtstag des Kontakts', subject: 'Alles Gute, {{kontakt.vorname}}!', active: false },
];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const Newsletter: React.FC<NewsletterProps> = ({ user, onEditCampaign }) => {
  const [activeTab, setActiveTab] = useState<'campaigns' | 'lists' | 'automations'>('campaigns');

  // Data
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [lists, setLists] = useState<NewsletterList[]>([]);
  const [loading, setLoading] = useState(true);

  // Automations
  const [automations, setAutomations] = useState<AutomatedEmail[]>(DEFAULT_AUTOMATIONS);
  const [copiedTag, setCopiedTag] = useState<string | null>(null);

  // Aggregate stats
  const [sentCount, setSentCount] = useState(0);
  const [avgOpen, setAvgOpen] = useState<number | null>(null);
  const [avgClick, setAvgClick] = useState<number | null>(null);

  // Campaign management
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [expandedData, setExpandedData] = useState<CampaignDetail | null>(null);
  const [expandLoading, setExpandLoading] = useState(false);

  // Modals
  const [analyticsCampaignId, setAnalyticsCampaignId] = useState<number | null>(null);
  const [importListId, setImportListId] = useState<number | null>(null);
  const [csvText, setCsvText] = useState('');
  const [newListModal, setNewListModal] = useState(false);
  const [newListName, setNewListName] = useState('');
  const [newListDesc, setNewListDesc] = useState('');
  const [busyAction, setBusyAction] = useState(false);

  // ------ Data fetching ------

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [cRes, lRes] = await Promise.all([
        apiFetch<Campaign[]>('/campaigns').catch(() => [] as Campaign[]),
        apiFetch<NewsletterList[]>('/lists').catch(() => [] as NewsletterList[]),
      ]);
      setCampaigns(cRes);
      setLists(lRes);

      const sent = cRes.filter(c => c.status === 'sent');
      setSentCount(sent.length);

      if (sent.length > 0) {
        const statsResults = await Promise.all(
          sent.map(c => apiFetch<CampaignStats>(`/campaigns/${c.id}/stats`).catch(() => null)),
        );
        const valid = statsResults.filter(Boolean) as CampaignStats[];
        if (valid.length > 0) {
          setAvgOpen(valid.reduce((s, v) => s + (v.openRate ?? 0), 0) / valid.length);
          setAvgClick(valid.reduce((s, v) => s + (v.clickRate ?? 0), 0) / valid.length);
        }
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  // ------ Campaign management actions ------

  const handleExpandCampaign = async (id: number) => {
    if (expandedId === id) {
      setExpandedId(null);
      setExpandedData(null);
      return;
    }
    setExpandedId(id);
    setExpandedData(null);
    setExpandLoading(true);
    try {
      const data = await apiFetch<CampaignDetail>(`/campaigns/${id}`);
      setExpandedData(data);
    } catch {
      setExpandedData(null);
    } finally {
      setExpandLoading(false);
    }
  };

  const handleDeleteCampaign = async (id: number) => {
    if (!confirm('Newsletter wirklich loeschen?')) return;
    try {
      await apiFetch(`/campaigns/${id}`, { method: 'DELETE' });
      setCampaigns(prev => prev.filter(c => c.id !== id));
      if (expandedId === id) {
        setExpandedId(null);
        setExpandedData(null);
      }
    } catch {
      alert('Loeschen fehlgeschlagen.');
    }
  };

  const handleDuplicateCampaign = async (campaign: CampaignDetail) => {
    setBusyAction(true);
    try {
      await apiFetch('/campaigns', {
        method: 'POST',
        body: JSON.stringify({
          title: `${campaign.title} (Kopie)`,
          subject: `${campaign.subject} (Kopie)`,
          preview_text: campaign.preview_text,
          html_content: campaign.html_content,
          json_content: campaign.json_content,
        }),
      });
      loadData();
      setExpandedId(null);
      setExpandedData(null);
    } catch {
      alert('Duplizieren fehlgeschlagen.');
    } finally {
      setBusyAction(false);
    }
  };

  // ------ List actions ------

  const handleSyncCrm = async (listId: number) => {
    setBusyAction(true);
    try {
      const res = await apiFetch<{ synced_count: number }>(`/lists/${listId}/sync-crm`, { method: 'POST' });
      alert(`${res.synced_count} Kontakte synchronisiert.`);
      loadData();
    } catch {
      alert('CRM-Sync fehlgeschlagen.');
    } finally {
      setBusyAction(false);
    }
  };

  const handleImport = async () => {
    if (!importListId || !csvText.trim()) return;
    const contacts = csvText
      .trim()
      .split('\n')
      .map(line => {
        const [email, first_name, last_name] = line.split(',').map(s => s.trim());
        return { email, first_name: first_name || null, last_name: last_name || null };
      })
      .filter(c => c.email);

    setBusyAction(true);
    try {
      const res = await apiFetch<{ imported_count: number }>(`/lists/${importListId}/import`, {
        method: 'POST',
        body: JSON.stringify({ contacts }),
      });
      alert(`${res.imported_count} Kontakte importiert.`);
      setImportListId(null);
      setCsvText('');
      loadData();
    } catch {
      alert('Import fehlgeschlagen.');
    } finally {
      setBusyAction(false);
    }
  };

  const handleCreateList = async () => {
    if (!newListName.trim()) return;
    setBusyAction(true);
    try {
      await apiFetch('/lists', {
        method: 'POST',
        body: JSON.stringify({ name: newListName, description: newListDesc, source: 'manual' }),
      });
      setNewListModal(false);
      setNewListName('');
      setNewListDesc('');
      loadData();
    } catch {
      alert('Liste konnte nicht erstellt werden.');
    } finally {
      setBusyAction(false);
    }
  };

  // ------ Derived data ------

  const filteredCampaigns = statusFilter === 'all'
    ? campaigns
    : campaigns.filter(c => c.status === statusFilter);

  const filterCounts: Record<StatusFilter, number> = {
    all: campaigns.length,
    draft: campaigns.filter(c => c.status === 'draft').length,
    scheduled: campaigns.filter(c => c.status === 'scheduled').length,
    sent: campaigns.filter(c => c.status === 'sent').length,
  };

  // ======================================================================
  // RENDER
  // ======================================================================

  return (
    <div className="space-y-6">
      {/* ---------- Header ---------- */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-[#008eaa]/10">
            <Mail size={24} className="text-[#008eaa]" />
          </div>
          <h1 className="text-2xl font-bold text-slate-800">Newsletter</h1>
        </div>
        <button
          onClick={() => onEditCampaign('new')}
          className="flex items-center gap-2 bg-[#008eaa] text-white px-4 py-2 rounded-lg hover:bg-[#007494] transition-colors"
        >
          <Plus size={18} /> Neuer Newsletter
        </button>
      </div>

      {/* ---------- Stats Cards ---------- */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={<Send size={20} />} label="Gesamt verschickt" value={String(sentCount)} />
        <StatCard icon={<MousePointerClick size={20} />} label="Ø Öffnungsrate" value={fmtPct(avgOpen)} />
        <StatCard icon={<BarChart3 size={20} />} label="Ø Klickrate" value={fmtPct(avgClick)} />
        <StatCard icon={<ListChecks size={20} />} label="Aktive Listen" value={String(lists.length)} />
      </div>

      {/* ---------- Tabs ---------- */}
      <div className="border-b border-slate-200">
        <div className="flex gap-6">
          <TabButton label="Kampagnen" active={activeTab === 'campaigns'} onClick={() => setActiveTab('campaigns')} />
          <TabButton label="Automationen" active={activeTab === 'automations'} onClick={() => setActiveTab('automations')} />
          <TabButton label="Kontaktlisten" active={activeTab === 'lists'} onClick={() => setActiveTab('lists')} />
        </div>
      </div>

      {/* ---------- Content ---------- */}
      {loading ? (
        <div className="text-center py-16 text-slate-400">Daten werden geladen…</div>
      ) : activeTab === 'campaigns' ? (
        /* ==== CAMPAIGNS MANAGEMENT ==== */
        <div className="space-y-4">
          {/* Status filter chips */}
          <div className="flex flex-wrap gap-2">
            {([
              ['all', 'Alle'],
              ['draft', 'Entwuerfe'],
              ['scheduled', 'Geplant'],
              ['sent', 'Versendet'],
            ] as [StatusFilter, string][]).map(([key, label]) => (
              <button
                key={key}
                onClick={() => { setStatusFilter(key); setExpandedId(null); setExpandedData(null); }}
                className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
                  statusFilter === key
                    ? 'bg-[#008eaa] text-white border-[#008eaa]'
                    : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                }`}
              >
                {label} <span className="ml-1 opacity-70">({filterCounts[key]})</span>
              </button>
            ))}
          </div>

          {filteredCampaigns.length === 0 ? (
            <EmptyState message={statusFilter === 'all' ? 'Noch keine Newsletter vorhanden.' : 'Keine Kampagnen mit diesem Status.'} />
          ) : (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
              <table className="w-full text-left border-collapse">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-6 py-4 font-medium text-slate-500 w-8"></th>
                    <th className="px-6 py-4 font-medium text-slate-500">Betreff</th>
                    <th className="px-6 py-4 font-medium text-slate-500">Status</th>
                    <th className="px-6 py-4 font-medium text-slate-500">Erstellt am</th>
                    <th className="px-6 py-4 font-medium text-slate-500">Versendet am</th>
                    <th className="px-6 py-4 font-medium text-slate-500 text-right">Aktionen</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredCampaigns.map(c => {
                    const badge = STATUS_MAP[c.status] || STATUS_MAP.draft;
                    const isExpanded = expandedId === c.id;
                    return (
                      <React.Fragment key={c.id}>
                        <tr
                          className={`hover:bg-slate-50 cursor-pointer transition-colors ${isExpanded ? 'bg-slate-50' : ''}`}
                          onClick={() => handleExpandCampaign(c.id)}
                        >
                          <td className="pl-6 py-4 text-slate-400">
                            {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                          </td>
                          <td className="px-6 py-4 font-medium text-slate-900">{c.subject}</td>
                          <td className="px-6 py-4">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${badge.cls}`}>
                              {badge.label}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-slate-600">{fmtDate((c as any).created_at)}</td>
                          <td className="px-6 py-4 text-slate-600">{fmtDate(c.sent_at)}</td>
                          <td className="px-6 py-4 text-right" onClick={e => e.stopPropagation()}>
                            <div className="flex items-center justify-end gap-2">
                              <button
                                onClick={() => onEditCampaign(String(c.id))}
                                className="p-1.5 rounded-md hover:bg-slate-100 text-slate-400 hover:text-[#008eaa]"
                                title="Bearbeiten"
                              >
                                <Edit2 size={16} />
                              </button>
                              {c.status === 'sent' && (
                                <button
                                  onClick={() => setAnalyticsCampaignId(c.id)}
                                  className="p-1.5 rounded-md hover:bg-slate-100 text-slate-400 hover:text-[#008eaa]"
                                  title="Statistiken"
                                >
                                  <BarChart3 size={16} />
                                </button>
                              )}
                              <button
                                onClick={() => handleDeleteCampaign(c.id)}
                                className="p-1.5 rounded-md hover:bg-red-50 text-slate-400 hover:text-red-500"
                                title="Loeschen"
                              >
                                <Trash2 size={16} />
                              </button>
                            </div>
                          </td>
                        </tr>

                        {/* ---- Expanded detail panel ---- */}
                        {isExpanded && (
                          <tr>
                            <td colSpan={6} className="bg-slate-50 px-6 py-0">
                              {expandLoading ? (
                                <div className="flex items-center justify-center py-8 text-slate-400">
                                  <Loader2 size={20} className="animate-spin mr-2" /> Details werden geladen…
                                </div>
                              ) : expandedData ? (
                                <div className="py-5 space-y-4">
                                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
                                    {/* Left: metadata */}
                                    <div className="lg:col-span-1 space-y-3">
                                      <div>
                                        <p className="text-xs text-slate-400 uppercase tracking-wide mb-0.5">Titel</p>
                                        <p className="text-sm font-medium text-slate-800">{expandedData.title}</p>
                                      </div>
                                      <div>
                                        <p className="text-xs text-slate-400 uppercase tracking-wide mb-0.5">Betreff</p>
                                        <p className="text-sm text-slate-700">{expandedData.subject}</p>
                                      </div>
                                      {expandedData.preview_text && (
                                        <div>
                                          <p className="text-xs text-slate-400 uppercase tracking-wide mb-0.5">Preview-Text</p>
                                          <p className="text-sm text-slate-500 italic">{expandedData.preview_text}</p>
                                        </div>
                                      )}
                                      <div className="pt-2 space-y-1.5 text-sm text-slate-500">
                                        <p className="flex items-center gap-2">
                                          <Calendar size={14} className="text-slate-400" />
                                          Erstellt: {fmtDateTime(expandedData.created_at)}
                                        </p>
                                        <p className="flex items-center gap-2">
                                          <Calendar size={14} className="text-slate-400" />
                                          Aktualisiert: {fmtDateTime(expandedData.updated_at)}
                                        </p>
                                        {expandedData.scheduled_at && (
                                          <p className="flex items-center gap-2">
                                            <Calendar size={14} className="text-blue-400" />
                                            Geplant: {fmtDateTime(expandedData.scheduled_at)}
                                          </p>
                                        )}
                                        {expandedData.sent_at && (
                                          <p className="flex items-center gap-2">
                                            <Calendar size={14} className="text-emerald-400" />
                                            Versendet: {fmtDateTime(expandedData.sent_at)}
                                          </p>
                                        )}
                                      </div>
                                    </div>

                                    {/* Right: HTML preview */}
                                    <div className="lg:col-span-2">
                                      <p className="text-xs text-slate-400 uppercase tracking-wide mb-1.5 flex items-center gap-1">
                                        <Eye size={12} /> Vorschau
                                      </p>
                                      {expandedData.html_content ? (
                                        <div className="border border-slate-200 rounded-lg overflow-hidden bg-white">
                                          <iframe
                                            srcDoc={expandedData.html_content}
                                            title="Newsletter Vorschau"
                                            sandbox=""
                                            className="w-full border-0"
                                            style={{ height: '220px' }}
                                          />
                                        </div>
                                      ) : (
                                        <div className="border border-dashed border-slate-200 rounded-lg flex items-center justify-center text-slate-300 text-sm"
                                          style={{ height: '220px' }}
                                        >
                                          Kein Inhalt vorhanden
                                        </div>
                                      )}
                                    </div>
                                  </div>

                                  {/* Action buttons */}
                                  <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-200">
                                    <button
                                      onClick={() => onEditCampaign(String(expandedData.id))}
                                      className="flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-md bg-[#008eaa] text-white hover:bg-[#007494] transition-colors"
                                    >
                                      <Edit2 size={14} /> Bearbeiten
                                    </button>
                                    <button
                                      onClick={() => handleDuplicateCampaign(expandedData)}
                                      disabled={busyAction}
                                      className="flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-md border border-slate-200 hover:bg-white text-slate-600 transition-colors disabled:opacity-50"
                                    >
                                      <Copy size={14} /> Duplizieren
                                    </button>
                                    {expandedData.status === 'sent' && (
                                      <button
                                        onClick={() => setAnalyticsCampaignId(expandedData.id)}
                                        className="flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-md border border-slate-200 hover:bg-white text-slate-600 transition-colors"
                                      >
                                        <BarChart3 size={14} /> Statistiken
                                      </button>
                                    )}
                                    <button
                                      onClick={() => handleDeleteCampaign(expandedData.id)}
                                      className="flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-md border border-red-200 hover:bg-red-50 text-red-600 transition-colors ml-auto"
                                    >
                                      <Trash2 size={14} /> Loeschen
                                    </button>
                                  </div>
                                </div>
                              ) : (
                                <div className="py-8 text-center text-slate-400 text-sm">Details nicht verfuegbar.</div>
                              )}
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : activeTab === 'lists' ? (
        /* ==== CONTACT LISTS ==== */
        <div className="space-y-4">
          <div className="flex justify-end">
            <button
              onClick={() => setNewListModal(true)}
              className="flex items-center gap-2 bg-[#008eaa] text-white px-4 py-2 rounded-lg hover:bg-[#007494] transition-colors"
            >
              <Plus size={18} /> Neue Liste
            </button>
          </div>

          {lists.length === 0 ? (
            <EmptyState message="Noch keine Kontaktlisten vorhanden." />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {lists.map(list => (
                <div key={list.id} className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 flex flex-col">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="p-2 bg-[#008eaa]/10 rounded-lg">
                      <Users size={20} className="text-[#008eaa]" />
                    </div>
                    <h3 className="font-bold text-slate-900 truncate">{list.name}</h3>
                  </div>

                  <div className="flex items-center gap-2 mb-4">
                    <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600">
                      {SOURCE_MAP[list.source] || list.source}
                    </span>
                    <span className="text-sm text-slate-500">{list.contact_count} Kontakte</span>
                  </div>

                  <div className="mt-auto flex flex-wrap gap-2 pt-4 border-t border-slate-100">
                    <button
                      onClick={() => handleSyncCrm(list.id)}
                      disabled={busyAction}
                      className="flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-md border border-slate-200 hover:bg-slate-50 text-slate-600 transition-colors"
                    >
                      <RefreshCw size={14} /> CRM synchronisieren
                    </button>
                    <button
                      onClick={() => setImportListId(list.id)}
                      className="flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-md border border-slate-200 hover:bg-slate-50 text-slate-600 transition-colors"
                    >
                      <Upload size={14} /> Importieren
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : null}

      {/* ==== AUTOMATIONS TAB ==== */}
      {!loading && activeTab === 'automations' && (
        <div className="space-y-6">
          {/* --- Automation list --- */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wide">Automatisierte E-Mails</h3>
            </div>

            {automations.map(auto => (
              <div key={auto.id} className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${auto.active ? 'bg-[#008eaa]/10' : 'bg-slate-100'}`}>
                      <Zap size={18} className={auto.active ? 'text-[#008eaa]' : 'text-slate-400'} />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-slate-800">{auto.name}</p>
                      <p className="text-xs text-slate-400 mt-0.5">
                        Trigger: {auto.triggerLabel}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {/* Active toggle */}
                    <button
                      onClick={() => setAutomations(prev => prev.map(a => a.id === auto.id ? { ...a, active: !a.active } : a))}
                      className={`flex items-center gap-1.5 px-2.5 py-1 text-xs rounded-full border transition-colors ${
                        auto.active
                          ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                          : 'bg-slate-50 border-slate-200 text-slate-500'
                      }`}
                    >
                      {auto.active ? <ToggleRight size={14} /> : <ToggleLeft size={14} />}
                      {auto.active ? 'Aktiv' : 'Inaktiv'}
                    </button>

                    {/* Edit in designer */}
                    <button
                      onClick={() => onEditCampaign(auto.id)}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md bg-[#008eaa] text-white hover:bg-[#007494] transition-colors"
                    >
                      <Edit2 size={13} /> Im Designer bearbeiten
                    </button>
                  </div>
                </div>

                {/* Subject preview with merge tags highlighted */}
                <div className="mt-3 pt-3 border-t border-slate-100">
                  <p className="text-xs text-slate-400 mb-1">Betreff:</p>
                  <p className="text-sm text-slate-600">
                    {auto.subject.split(/({{[^}]+}})/).map((part, i) =>
                      part.startsWith('{{') ? (
                        <code key={i} className="px-1 py-0.5 rounded bg-[#008eaa]/10 text-[#008eaa] text-xs font-mono">{part}</code>
                      ) : (
                        <span key={i}>{part}</span>
                      )
                    )}
                  </p>
                  {auto.lastEdited && (
                    <p className="text-xs text-slate-300 mt-1">Zuletzt bearbeitet: {fmtDate(auto.lastEdited)}</p>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* --- Merge Tags Reference --- */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
            <div className="flex items-center gap-2 mb-4">
              <Hash size={18} className="text-[#008eaa]" />
              <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wide">Variablenfelder (Merge-Tags)</h3>
            </div>
            <p className="text-xs text-slate-400 mb-4">
              Verwenden Sie diese Platzhalter in Betreff und Inhalt. Sie werden beim Versand automatisch mit den Stammdaten des Empfaengers ersetzt. Klicken Sie auf ein Tag, um es zu kopieren.
            </p>

            <div className="space-y-4">
              {MERGE_TAGS.map(cat => (
                <div key={cat.category}>
                  <p className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">{cat.category}</p>
                  <div className="flex flex-wrap gap-2">
                    {cat.tags.map(tag => (
                      <button
                        key={tag.token}
                        onClick={() => {
                          navigator.clipboard.writeText(tag.token);
                          setCopiedTag(tag.token);
                          setTimeout(() => setCopiedTag(null), 1500);
                        }}
                        className="group flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-slate-200 hover:border-[#008eaa] hover:bg-[#008eaa]/5 transition-colors text-left"
                        title={`Klicken zum Kopieren: ${tag.token}`}
                      >
                        <code className="text-xs font-mono text-[#008eaa]">{tag.token}</code>
                        <span className="text-[10px] text-slate-400 hidden sm:inline">— {tag.label}</span>
                        {copiedTag === tag.token ? (
                          <Check size={12} className="text-emerald-500 shrink-0" />
                        ) : (
                          <Clipboard size={12} className="text-slate-300 group-hover:text-[#008eaa] shrink-0" />
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ===== MODALS ===== */}

      {/* --- Analytics Modal (dedicated component) --- */}
      {analyticsCampaignId !== null && (
        <NewsletterAnalytics campaignId={analyticsCampaignId} onClose={() => setAnalyticsCampaignId(null)} />
      )}

      {/* --- Import Modal --- */}
      {importListId !== null && (
        <Modal title="Kontakte importieren" onClose={() => { setImportListId(null); setCsvText(''); }}>
          <p className="text-sm text-slate-500 mb-3">
            CSV-Format: <code className="bg-slate-100 px-1 rounded">email,vorname,nachname</code> — eine Zeile pro Kontakt.
          </p>
          <textarea
            value={csvText}
            onChange={e => setCsvText(e.target.value)}
            rows={8}
            className="w-full border border-slate-200 rounded-lg p-3 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-[#008eaa]/40"
            placeholder={"max@beispiel.de,Max,Mustermann\nerika@beispiel.de,Erika,Muster"}
          />
          <div className="flex justify-end gap-2 mt-4">
            <button onClick={() => { setImportListId(null); setCsvText(''); }} className="px-4 py-2 text-sm rounded-lg border border-slate-200 hover:bg-slate-50">
              Abbrechen
            </button>
            <button
              onClick={handleImport}
              disabled={busyAction || !csvText.trim()}
              className="px-4 py-2 text-sm rounded-lg bg-[#008eaa] text-white hover:bg-[#007494] disabled:opacity-50 transition-colors"
            >
              Importieren
            </button>
          </div>
        </Modal>
      )}

      {/* --- New List Modal --- */}
      {newListModal && (
        <Modal title="Neue Kontaktliste" onClose={() => setNewListModal(false)}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Name</label>
              <input
                value={newListName}
                onChange={e => setNewListName(e.target.value)}
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#008eaa]/40"
                placeholder="z.B. Kunden Q2 2026"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Beschreibung</label>
              <textarea
                value={newListDesc}
                onChange={e => setNewListDesc(e.target.value)}
                rows={3}
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#008eaa]/40"
                placeholder="Optionale Beschreibung…"
              />
            </div>
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <button onClick={() => setNewListModal(false)} className="px-4 py-2 text-sm rounded-lg border border-slate-200 hover:bg-slate-50">
              Abbrechen
            </button>
            <button
              onClick={handleCreateList}
              disabled={busyAction || !newListName.trim()}
              className="px-4 py-2 text-sm rounded-lg bg-[#008eaa] text-white hover:bg-[#007494] disabled:opacity-50 transition-colors"
            >
              Erstellen
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

const StatCard: React.FC<{ icon: React.ReactNode; label: string; value: string }> = ({ icon, label, value }) => (
  <div className="bg-white p-5 rounded-xl shadow-sm border border-slate-200">
    <div className="flex items-center gap-3 mb-2">
      <span className="text-[#008eaa]">{icon}</span>
      <span className="text-sm text-slate-500">{label}</span>
    </div>
    <p className="text-2xl font-bold text-slate-800">{value}</p>
  </div>
);

const TabButton: React.FC<{ label: string; active: boolean; onClick: () => void }> = ({ label, active, onClick }) => (
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

const EmptyState: React.FC<{ message: string }> = ({ message }) => (
  <div className="text-center py-16 text-slate-400 bg-white rounded-xl border border-slate-200">{message}</div>
);

const Modal: React.FC<{ title: string; onClose: () => void; children: React.ReactNode }> = ({ title, onClose, children }) => (
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
    <div className="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 p-6" onClick={e => e.stopPropagation()}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-slate-800">{title}</h3>
        <button onClick={onClose} className="p-1 rounded hover:bg-slate-100 text-slate-400"><X size={20} /></button>
      </div>
      {children}
    </div>
  </div>
);

export default Newsletter;
