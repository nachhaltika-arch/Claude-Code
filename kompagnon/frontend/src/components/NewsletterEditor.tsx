import React, { useState, useRef, useEffect, useCallback } from 'react';
import EmailEditor, { EditorRef, EmailEditorProps } from 'react-email-editor';
import { ArrowLeft, Save, Send, X, Clock, LayoutTemplate } from 'lucide-react';
import { User } from '../types';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface NewsletterEditorProps {
  campaignId: string | null;   // 'new' or numeric id
  user: User;
  onBack: () => void;
}

interface NewsletterList {
  id: number;
  name: string;
  source: string;
  contact_count: number;
}

// ---------------------------------------------------------------------------
// API helper (same pattern as Newsletter.tsx)
// ---------------------------------------------------------------------------

const API_BASE = '/api/newsletter';

async function apiFetch<T = any>(path: string, opts: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('silva_token') || '';
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
  const res = await fetch(`${API_BASE}${path}`, { ...opts, headers });
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Unlayer template designs
// ---------------------------------------------------------------------------

const TEMPLATE_SIMPLE: Record<string, any> = {
  body: {
    rows: [
      {
        cells: [1],
        columns: [{
          contents: [{
            type: 'image',
            values: {
              src: { url: 'https://via.placeholder.com/200x60/008eaa/ffffff?text=Logo', width: 200, height: 60 },
              alt: 'Logo',
              action: { name: 'web', values: { href: '', target: '_blank' } },
              textAlign: 'center',
              containerPadding: '20px 10px',
            },
          }],
          values: { backgroundColor: '', padding: '0px', _meta: { htmlID: 'u_column_1', htmlClassNames: 'u_column' } },
        }],
        values: { backgroundColor: '#ffffff', padding: '0px', columnsBackgroundColor: '' },
      },
      {
        cells: [1],
        columns: [{
          contents: [{
            type: 'text',
            values: {
              text: '<h1 style="text-align:center;">Willkommen!</h1><p style="text-align:center; color:#666;">Hier steht Ihre Nachricht an die Leser. Ersetzen Sie diesen Text mit Ihrem Inhalt.</p>',
              containerPadding: '20px 40px',
            },
          }],
          values: { backgroundColor: '', padding: '0px' },
        }],
        values: { backgroundColor: '#ffffff', padding: '0px' },
      },
      {
        cells: [1],
        columns: [{
          contents: [{
            type: 'button',
            values: {
              text: 'Jetzt entdecken',
              href: { name: 'web', values: { href: 'https://example.com', target: '_blank' } },
              size: { autoWidth: false, width: '50%' },
              textAlign: 'center',
              lineHeight: '140%',
              border: {},
              borderRadius: '6px',
              buttonColors: { color: '#ffffff', backgroundColor: '#008eaa', hoverColor: '#ffffff', hoverBackgroundColor: '#006d87' },
              containerPadding: '20px 10px 30px',
              padding: '12px 24px',
            },
          }],
          values: { backgroundColor: '', padding: '0px' },
        }],
        values: { backgroundColor: '#ffffff', padding: '0px' },
      },
    ],
    values: {
      backgroundColor: '#f4f4f4',
      contentWidth: '600px',
      fontFamily: { label: 'Arial', value: 'arial,helvetica,sans-serif' },
    },
  },
};

const TEMPLATE_OFFER: Record<string, any> = {
  body: {
    rows: [
      {
        cells: [1],
        columns: [{
          contents: [{
            type: 'image',
            values: {
              src: { url: 'https://via.placeholder.com/600x250/008eaa/ffffff?text=Angebot', width: 600, height: 250 },
              alt: 'Angebot Header',
              containerPadding: '0px',
              textAlign: 'center',
            },
          }],
          values: { backgroundColor: '', padding: '0px' },
        }],
        values: { backgroundColor: '#008eaa', padding: '0px' },
      },
      {
        cells: [1],
        columns: [{
          contents: [{
            type: 'text',
            values: {
              text: '<h2>Unser Angebot fuer Sie</h2><ul><li>Vorteil 1: Beschreibung des ersten Vorteils</li><li>Vorteil 2: Beschreibung des zweiten Vorteils</li><li>Vorteil 3: Beschreibung des dritten Vorteils</li></ul>',
              containerPadding: '25px 30px 10px',
            },
          }],
          values: { backgroundColor: '', padding: '0px' },
        }],
        values: { backgroundColor: '#ffffff', padding: '0px' },
      },
      {
        cells: [1],
        columns: [{
          contents: [{
            type: 'text',
            values: {
              text: '<div style="text-align:center; padding:20px; background:#f0f9fb; border-radius:8px; border:2px solid #008eaa;"><p style="font-size:14px; color:#666; margin:0;">Ihr Preis</p><p style="font-size:32px; font-weight:bold; color:#008eaa; margin:8px 0;">49,00 &euro; / Monat</p><p style="font-size:13px; color:#999; margin:0;">zzgl. MwSt.</p></div>',
              containerPadding: '10px 40px 20px',
            },
          }],
          values: { backgroundColor: '', padding: '0px' },
        }],
        values: { backgroundColor: '#ffffff', padding: '0px' },
      },
      {
        cells: [1],
        columns: [{
          contents: [{
            type: 'button',
            values: {
              text: 'Angebot annehmen',
              href: { name: 'web', values: { href: 'https://example.com', target: '_blank' } },
              size: { autoWidth: false, width: '60%' },
              textAlign: 'center',
              borderRadius: '6px',
              buttonColors: { color: '#ffffff', backgroundColor: '#008eaa', hoverColor: '#ffffff', hoverBackgroundColor: '#006d87' },
              containerPadding: '10px 10px 30px',
              padding: '14px 28px',
            },
          }],
          values: { backgroundColor: '', padding: '0px' },
        }],
        values: { backgroundColor: '#ffffff', padding: '0px' },
      },
    ],
    values: {
      backgroundColor: '#f4f4f4',
      contentWidth: '600px',
      fontFamily: { label: 'Arial', value: 'arial,helvetica,sans-serif' },
    },
  },
};

const TEMPLATE_MONTHLY: Record<string, any> = {
  body: {
    rows: [
      {
        cells: [1],
        columns: [{
          contents: [{
            type: 'text',
            values: {
              text: '<h1 style="text-align:center; color:#ffffff; margin:0;">Monats-Update</h1><p style="text-align:center; color:#ffffffcc; margin:8px 0 0;">April 2026</p>',
              containerPadding: '30px 20px',
            },
          }],
          values: { backgroundColor: '#008eaa', padding: '0px' },
        }],
        values: { backgroundColor: '#008eaa', padding: '0px' },
      },
      {
        cells: [0.5, 0.5],
        columns: [
          {
            contents: [{
              type: 'text',
              values: {
                text: '<h3>Neuigkeit 1</h3><p style="color:#666;">Beschreibung der ersten Neuigkeit. Ersetzen Sie diesen Platzhaltertext mit Ihrem Inhalt.</p>',
                containerPadding: '20px',
              },
            }],
            values: { backgroundColor: '#ffffff', padding: '0px', borderRadius: '8px' },
          },
          {
            contents: [{
              type: 'text',
              values: {
                text: '<h3>Neuigkeit 2</h3><p style="color:#666;">Beschreibung der zweiten Neuigkeit. Ersetzen Sie diesen Platzhaltertext mit Ihrem Inhalt.</p>',
                containerPadding: '20px',
              },
            }],
            values: { backgroundColor: '#ffffff', padding: '0px', borderRadius: '8px' },
          },
        ],
        values: { backgroundColor: '', padding: '15px', columnsBackgroundColor: '' },
      },
      {
        cells: [1],
        columns: [{
          contents: [{
            type: 'text',
            values: {
              text: '<h3>Weiterer Beitrag</h3><p style="color:#666;">Hier koennen Sie einen laengeren Beitrag platzieren, z.B. einen Rueckblick oder eine Vorschau auf kommende Themen.</p>',
              containerPadding: '20px 30px',
            },
          }],
          values: { backgroundColor: '', padding: '0px' },
        }],
        values: { backgroundColor: '#ffffff', padding: '10px 15px' },
      },
      {
        cells: [1],
        columns: [{
          contents: [{
            type: 'button',
            values: {
              text: 'Alle News lesen',
              href: { name: 'web', values: { href: 'https://example.com', target: '_blank' } },
              size: { autoWidth: false, width: '50%' },
              textAlign: 'center',
              borderRadius: '6px',
              buttonColors: { color: '#ffffff', backgroundColor: '#008eaa', hoverColor: '#ffffff', hoverBackgroundColor: '#006d87' },
              containerPadding: '15px 10px 30px',
              padding: '12px 24px',
            },
          }],
          values: { backgroundColor: '', padding: '0px' },
        }],
        values: { backgroundColor: '#ffffff', padding: '0px 15px' },
      },
    ],
    values: {
      backgroundColor: '#f4f4f4',
      contentWidth: '600px',
      fontFamily: { label: 'Arial', value: 'arial,helvetica,sans-serif' },
    },
  },
};

const TEMPLATES = [
  { key: 'simple',  label: 'Einfache Nachricht', desc: 'Logo, Text und CTA-Button', design: TEMPLATE_SIMPLE },
  { key: 'offer',   label: 'Angebot',            desc: 'Bild-Header, Vorteile, Preis-Box', design: TEMPLATE_OFFER },
  { key: 'monthly', label: 'Monats-Update',      desc: 'Zweispaltig, News-Bloecke',       design: TEMPLATE_MONTHLY },
];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const NewsletterEditor: React.FC<NewsletterEditorProps> = ({ campaignId, user, onBack }) => {
  const emailEditorRef = useRef<EditorRef>(null);
  const isNew = !campaignId || campaignId === 'new';

  // Form state
  const [subject, setSubject] = useState('');
  const [previewText, setPreviewText] = useState('');
  const [saving, setSaving] = useState(false);
  const [existingId, setExistingId] = useState<number | null>(isNew ? null : Number(campaignId));

  // Editor ready flag
  const [editorReady, setEditorReady] = useState(false);
  const pendingDesign = useRef<any>(null);

  // Template picker
  const [showTemplatePicker, setShowTemplatePicker] = useState(isNew);

  // Send modal
  const [sendModal, setSendModal] = useState(false);
  const [lists, setLists] = useState<NewsletterList[]>([]);
  const [selectedListId, setSelectedListId] = useState<number | null>(null);
  const [sendMode, setSendMode] = useState<'now' | 'schedule'>('now');
  const [scheduledAt, setScheduledAt] = useState('');
  const [sending, setSending] = useState(false);

  // ---- Load existing campaign ----
  useEffect(() => {
    if (isNew) return;
    apiFetch(`/campaigns/${campaignId}`)
      .then((data: any) => {
        setSubject(data.subject || '');
        setPreviewText(data.preview_text || '');
        if (data.json_content) {
          if (editorReady) {
            emailEditorRef.current?.editor?.loadDesign(data.json_content);
          } else {
            pendingDesign.current = data.json_content;
          }
        }
      })
      .catch(() => alert('Newsletter konnte nicht geladen werden.'));
  }, [campaignId, isNew, editorReady]);

  // ---- Editor ready callback ----
  const onEditorReady: EmailEditorProps['onReady'] = useCallback(() => {
    setEditorReady(true);
    if (pendingDesign.current) {
      emailEditorRef.current?.editor?.loadDesign(pendingDesign.current);
      pendingDesign.current = null;
    }
  }, []);

  // ---- Template selection ----
  const applyTemplate = (design: any) => {
    emailEditorRef.current?.editor?.loadDesign(design);
    setShowTemplatePicker(false);
  };

  // ---- Save ----
  const handleSave = () => {
    const editor = emailEditorRef.current?.editor;
    if (!editor) return;

    editor.exportHtml((data: any) => {
      const { design, html } = data;
      const body = {
        title: subject || 'Ohne Titel',
        subject,
        preview_text: previewText,
        html_content: html,
        json_content: design,
      };

      setSaving(true);

      const request = existingId
        ? apiFetch(`/campaigns/${existingId}`, { method: 'PUT', body: JSON.stringify(body) })
        : apiFetch('/campaigns', { method: 'POST', body: JSON.stringify(body) });

      request
        .then((res: any) => {
          if (!existingId && res.id) setExistingId(res.id);
        })
        .catch(() => alert('Speichern fehlgeschlagen.'))
        .finally(() => setSaving(false));
    });
  };

  // ---- Open send modal ----
  const openSendModal = () => {
    if (!existingId) {
      alert('Bitte zuerst speichern.');
      return;
    }
    apiFetch<NewsletterList[]>('/lists')
      .then(setLists)
      .catch(() => {});
    setSendModal(true);
  };

  // ---- Send / Schedule ----
  const handleSend = async () => {
    if (!existingId || !selectedListId) return;
    setSending(true);
    try {
      const body: any = { list_ids: [selectedListId] };
      if (sendMode === 'schedule' && scheduledAt) {
        body.scheduled_at = new Date(scheduledAt).toISOString();
      }
      await apiFetch(`/campaigns/${existingId}/send`, { method: 'POST', body: JSON.stringify(body) });
      alert(sendMode === 'now' ? 'Newsletter wurde gesendet!' : 'Newsletter wurde geplant!');
      setSendModal(false);
      onBack();
    } catch {
      alert('Senden fehlgeschlagen.');
    } finally {
      setSending(false);
    }
  };

  // ====================================================================
  // RENDER
  // ====================================================================

  return (
    <div className="flex flex-col" style={{ height: 'calc(100vh - 120px)' }}>
      {/* ---------- Top bar ---------- */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-3 bg-white border-b border-slate-200 px-4 py-3 -mx-4 md:-mx-8 -mt-4 md:-mt-8 mb-0">
        <button onClick={onBack} className="p-2 rounded-lg hover:bg-slate-100 text-slate-500 shrink-0" title="Zurueck">
          <ArrowLeft size={20} />
        </button>

        <div className="flex-1 min-w-0 space-y-1">
          <input
            value={subject}
            onChange={e => setSubject(e.target.value)}
            placeholder="Betreff eingeben…"
            className="w-full text-lg font-bold text-slate-800 bg-transparent border-none outline-none placeholder:text-slate-300"
          />
          <input
            value={previewText}
            onChange={e => setPreviewText(e.target.value)}
            placeholder="Preview-Text (optional)…"
            className="w-full text-sm text-slate-400 bg-transparent border-none outline-none placeholder:text-slate-300"
          />
        </div>

        <div className="flex gap-2 shrink-0">
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 text-sm rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 disabled:opacity-50 transition-colors"
          >
            <Save size={16} /> {saving ? 'Speichern…' : 'Speichern'}
          </button>
          <button
            onClick={openSendModal}
            className="flex items-center gap-2 px-4 py-2 text-sm rounded-lg bg-[#008eaa] text-white hover:bg-[#007494] transition-colors"
          >
            <Send size={16} /> Senden / Planen
          </button>
        </div>
      </div>

      {/* ---------- Editor ---------- */}
      <div className="flex-1 -mx-4 md:-mx-8">
        <EmailEditor
          ref={emailEditorRef}
          onReady={onEditorReady}
          options={{
            locale: 'de-DE',
            appearance: { theme: 'light' as const },
            features: { textEditor: { spellChecker: true } },
          }}
          style={{ height: '100%' }}
        />
      </div>

      {/* ===== Template Picker Modal ===== */}
      {showTemplatePicker && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setShowTemplatePicker(false)}>
          <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl mx-4 p-6" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-5">
              <div className="flex items-center gap-2">
                <LayoutTemplate size={20} className="text-[#008eaa]" />
                <h3 className="text-lg font-bold text-slate-800">Vorlage auswaehlen</h3>
              </div>
              <button onClick={() => setShowTemplatePicker(false)} className="p-1 rounded hover:bg-slate-100 text-slate-400">
                <X size={20} />
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
              {TEMPLATES.map(t => (
                <button
                  key={t.key}
                  onClick={() => applyTemplate(t.design)}
                  className="text-left p-4 rounded-lg border-2 border-slate-200 hover:border-[#008eaa] hover:shadow-md transition-all group"
                >
                  <div className="h-24 bg-slate-50 rounded mb-3 flex items-center justify-center text-slate-300 group-hover:bg-[#008eaa]/5">
                    <LayoutTemplate size={32} className="group-hover:text-[#008eaa] transition-colors" />
                  </div>
                  <p className="font-semibold text-slate-800 text-sm">{t.label}</p>
                  <p className="text-xs text-slate-400 mt-1">{t.desc}</p>
                </button>
              ))}
            </div>

            <button
              onClick={() => setShowTemplatePicker(false)}
              className="w-full text-center text-sm text-slate-500 hover:text-slate-700 py-2"
            >
              Ohne Vorlage starten
            </button>
          </div>
        </div>
      )}

      {/* ===== Send / Schedule Modal ===== */}
      {sendModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setSendModal(false)}>
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-lg font-bold text-slate-800">Newsletter senden</h3>
              <button onClick={() => setSendModal(false)} className="p-1 rounded hover:bg-slate-100 text-slate-400">
                <X size={20} />
              </button>
            </div>

            {/* List selection */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-slate-700 mb-1">Kontaktliste</label>
              <select
                value={selectedListId ?? ''}
                onChange={e => setSelectedListId(Number(e.target.value) || null)}
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#008eaa]/40"
              >
                <option value="">Liste auswaehlen…</option>
                {lists.map(l => (
                  <option key={l.id} value={l.id}>{l.name} ({l.contact_count} Kontakte)</option>
                ))}
              </select>
            </div>

            {/* Send mode */}
            <div className="mb-4 space-y-2">
              <label className="block text-sm font-medium text-slate-700">Zeitpunkt</label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio" name="sendMode" checked={sendMode === 'now'}
                  onChange={() => setSendMode('now')}
                  className="accent-[#008eaa]"
                />
                <Send size={14} className="text-slate-400" />
                <span className="text-sm text-slate-700">Jetzt senden</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio" name="sendMode" checked={sendMode === 'schedule'}
                  onChange={() => setSendMode('schedule')}
                  className="accent-[#008eaa]"
                />
                <Clock size={14} className="text-slate-400" />
                <span className="text-sm text-slate-700">Planen</span>
              </label>
            </div>

            {/* Date picker */}
            {sendMode === 'schedule' && (
              <div className="mb-4">
                <label className="block text-sm font-medium text-slate-700 mb-1">Datum &amp; Uhrzeit</label>
                <input
                  type="datetime-local"
                  value={scheduledAt}
                  onChange={e => setScheduledAt(e.target.value)}
                  className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#008eaa]/40"
                />
              </div>
            )}

            {/* Confirm */}
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setSendModal(false)} className="px-4 py-2 text-sm rounded-lg border border-slate-200 hover:bg-slate-50">
                Abbrechen
              </button>
              <button
                onClick={handleSend}
                disabled={sending || !selectedListId || (sendMode === 'schedule' && !scheduledAt)}
                className="px-4 py-2 text-sm rounded-lg bg-[#008eaa] text-white hover:bg-[#007494] disabled:opacity-50 transition-colors"
              >
                {sending ? 'Wird gesendet…' : sendMode === 'now' ? 'Jetzt senden' : 'Planen'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default NewsletterEditor;
