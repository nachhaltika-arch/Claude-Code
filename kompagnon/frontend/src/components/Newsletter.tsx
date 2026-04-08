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
  // TODO: Datei war hier abgeschnitten — Rest muss noch aus Silva-Viridis-Portal übernommen werden
  // const [copiedTag ...

  return <div>Newsletter — teilweise übernommen, Rest fehlt noch.</div>;
};

export default Newsletter;
