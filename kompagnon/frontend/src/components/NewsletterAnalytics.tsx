import React, { useState, useEffect } from 'react';
import {
  X, BarChart3, MousePointerClick, UserMinus, Send,
  CheckCircle2, AlertTriangle, AlertCircle, FileDown, Loader2,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface CampaignStats {
  openRate: number | null;
  clickRate: number | null;
  unsubscriptions: number | null;
  sentCount?: number | null;
}

interface NewsletterAnalyticsProps {
  campaignId: number;
  onClose: () => void;
}

// ---------------------------------------------------------------------------
// API helper
// ---------------------------------------------------------------------------

const API_BASE = '/api/newsletter';

async function apiFetch<T = any>(path: string): Promise<T> {
  const token = localStorage.getItem('silva_token') || '';
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
  const res = await fetch(`${API_BASE}${path}`, { headers });
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function toPct(val: number | null): number {
  if (val == null) return 0;
  return Math.round(val * 1000) / 10; // e.g. 0.254 → 25.4
}

function fmtPct(val: number | null): string {
  if (val == null) return '—';
  return `${toPct(val).toFixed(1)} %`;
}

function fmtNum(val: number | null | undefined): string {
  if (val == null) return '—';
  return val.toLocaleString('de-DE');
}

function ratingBadge(openRate: number | null): { label: string; cls: string; icon: React.ReactNode } {
  const pct = openRate != null ? openRate : 0;
  if (pct > 0.25) {
    return {
      label: 'Sehr gute Oeffnungsrate',
      cls: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      icon: <CheckCircle2 size={16} className="text-emerald-500" />,
    };
  }
  if (pct >= 0.15) {
    return {
      label: 'Durchschnittliche Oeffnungsrate',
      cls: 'bg-amber-50 text-amber-700 border-amber-200',
      icon: <AlertTriangle size={16} className="text-amber-500" />,
    };
  }
  return {
    label: 'Oeffnungsrate verbessern',
    cls: 'bg-red-50 text-red-700 border-red-200',
    icon: <AlertCircle size={16} className="text-red-500" />,
  };
}

// ---------------------------------------------------------------------------
// Print styles (injected once)
// ---------------------------------------------------------------------------

const PRINT_STYLE_ID = 'newsletter-analytics-print-style';

function ensurePrintStyles() {
  if (document.getElementById(PRINT_STYLE_ID)) return;
  const style = document.createElement('style');
  style.id = PRINT_STYLE_ID;
  style.textContent = `
    @media print {
      body * { visibility: hidden !important; }
      #newsletter-analytics-print,
      #newsletter-analytics-print * { visibility: visible !important; }
      #newsletter-analytics-print {
        position: absolute; left: 0; top: 0; width: 100%;
        padding: 24px; box-shadow: none; border: none;
      }
      .no-print { display: none !important; }
    }
  `;
  document.head.appendChild(style);
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const NewsletterAnalytics: React.FC<NewsletterAnalyticsProps> = ({ campaignId, onClose }) => {
  const [stats, setStats] = useState<CampaignStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    ensurePrintStyles();
    setLoading(true);
    setError(null);
    apiFetch<CampaignStats>(`/campaigns/${campaignId}/stats`)
      .then(setStats)
      .catch(() => setError('Statistiken konnten nicht geladen werden.'))
      .finally(() => setLoading(false));
  }, [campaignId]);

  const handlePrint = () => window.print();

  const rating = stats ? ratingBadge(stats.openRate) : null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 no-print-backdrop" onClick={onClose}>
      <div
        id="newsletter-analytics-print"
        className="bg-white rounded-xl shadow-xl w-full max-w-2xl mx-4 p-6 max-h-[90vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <BarChart3 size={20} className="text-[#008eaa]" />
            <h3 className="text-lg font-bold text-slate-800">Newsletter-Analyse</h3>
          </div>
          <button onClick={onClose} className="p-1 rounded hover:bg-slate-100 text-slate-400 no-print">
            <X size={20} />
          </button>
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-16 text-slate-400">
            <Loader2 size={32} className="animate-spin mb-3" />
            <p className="text-sm">Statistiken werden geladen…</p>
          </div>
        )}

        {/* Error */}
        {error && !loading && (
          <div className="text-center py-12">
            <AlertCircle size={32} className="mx-auto mb-3 text-red-400" />
            <p className="text-sm text-red-500">{error}</p>
          </div>
        )}

        {/* Stats content */}
        {stats && !loading && (
          <div className="space-y-6">
            {/* ---- 4 KPI tiles ---- */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <KpiTile
                icon={<MousePointerClick size={20} />}
                label="Oeffnungsrate"
                value={fmtPct(stats.openRate)}
                progress={toPct(stats.openRate)}
              />
              <KpiTile
                icon={<BarChart3 size={20} />}
                label="Klickrate"
                value={fmtPct(stats.clickRate)}
                progress={toPct(stats.clickRate)}
              />
              <KpiTile
                icon={<UserMinus size={20} />}
                label="Abmeldungen"
                value={fmtNum(stats.unsubscriptions)}
              />
              <KpiTile
                icon={<Send size={20} />}
                label="Versendet an"
                value={fmtNum(stats.sentCount)}
              />
            </div>

            {/* ---- Explanation ---- */}
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 text-sm text-slate-500 leading-relaxed space-y-1">
              <p><span className="font-medium text-slate-600">Oeffnungsrate:</span> Anteil der Empfaenger, die die E-Mail geoeffnet haben.</p>
              <p><span className="font-medium text-slate-600">Klickrate:</span> Anteil, die auf mindestens einen Link geklickt haben.</p>
              <p><span className="font-medium text-slate-600">Abmeldungen:</span> Empfaenger, die sich vom Newsletter abgemeldet haben.</p>
            </div>

            {/* ---- Rating badge ---- */}
            {rating && (
              <div className={`flex items-center gap-2 px-4 py-3 rounded-lg border ${rating.cls}`}>
                {rating.icon}
                <span className="text-sm font-medium">{rating.label}</span>
              </div>
            )}

            {/* ---- Footer buttons ---- */}
            <div className="flex justify-end gap-2 pt-2 no-print">
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 transition-colors"
              >
                Schliessen
              </button>
              <button
                onClick={handlePrint}
                className="flex items-center gap-2 px-4 py-2 text-sm rounded-lg bg-[#008eaa] text-white hover:bg-[#007494] transition-colors"
              >
                <FileDown size={16} /> Als PDF exportieren
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// KPI Tile sub-component
// ---------------------------------------------------------------------------

const KpiTile: React.FC<{
  icon: React.ReactNode;
  label: string;
  value: string;
  progress?: number; // 0–100
}> = ({ icon, label, value, progress }) => (
  <div className="bg-white border border-slate-200 rounded-xl p-5">
    <div className="flex items-center gap-2 mb-1">
      <span className="text-[#008eaa]">{icon}</span>
      <span className="text-sm text-slate-500">{label}</span>
    </div>
    <p className="text-3xl font-bold text-slate-800 mb-2">{value}</p>
    {progress != null && (
      <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full bg-[#008eaa] transition-all duration-500"
          style={{ width: `${Math.min(progress, 100)}%` }}
        />
      </div>
    )}
  </div>
);

export default NewsletterAnalytics;
