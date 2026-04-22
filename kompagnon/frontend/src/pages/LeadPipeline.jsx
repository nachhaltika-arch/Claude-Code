import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import API_BASE_URL from '../config';

const PHASES = [
  { id: 'phase_1', label: 'Onboarding',  icon: '📋', color: '#008EAA' },
  { id: 'phase_2', label: 'Briefing',    icon: '📝', color: '#7c3aed' },
  { id: 'phase_3', label: 'Content',     icon: '✍️',  color: '#d97706' },
  { id: 'phase_4', label: 'Technik',     icon: '⚙️',  color: '#0891b2' },
  { id: 'phase_5', label: 'QA',          icon: '🔍',  color: '#dc7226' },
  { id: 'phase_6', label: 'Go-Live',     icon: '🚀',  color: '#059669' },
  { id: 'phase_7', label: 'Post-Launch', icon: '🌐',  color: '#16a34a' },
];

const CERT_STYLES = {
  bronze:  { bg: '#F5E6D3', text: '#7D4A1A' },
  silber:  { bg: '#EFEFEF', text: '#5A5A5A' },
  gold:    { bg: '#FEF3DC', text: '#BA7517' },
  platin:  { bg: '#E6F1FB', text: '#185FA5' },
  diamant: { bg: '#EAF4E0', text: '#1D9E75' },
};

function speedColor(s) {
  if (s === null || s === undefined) return null;
  if (s >= 90) return { bg: '#EAF4E0', text: '#3B6D11' };
  if (s >= 50) return { bg: '#FEF3DC', text: '#BA7517' };
  return { bg: '#FDEAEA', text: '#E24B4A' };
}

function getDomain(url) {
  if (!url) return null;
  try { return new URL(url.startsWith('http') ? url : 'https://' + url).hostname.replace('www.', ''); }
  catch { return url; }
}

// ── Unified card type ─────────────────────────────────────────────────────────
// { key, type, projectId, leadId, companyName, websiteUrl, phase, project, lead }

function buildCards(projArray, leadsArray) {
  const cards = [];
  const projLeadIds = new Set();

  // Cards from projects
  const leadsById = {};
  leadsArray.forEach(l => { leadsById[l.id] = l; });

  projArray.forEach(p => {
    const lead = leadsById[p.lead_id] || {};
    projLeadIds.add(p.lead_id);
    cards.push({
      key:         `p-${p.id}`,
      type:        'project',
      projectId:   p.id,
      leadId:      p.lead_id,
      companyName: p.company_name || lead.company_name || `Projekt #${p.id}`,
      websiteUrl:  p.website_url  || lead.website_url  || null,
      phase:       p.status || 'phase_1',
      project:     p,
      lead,
    });
  });

  // Won leads without a project → appear in Phase 1 as fallback
  leadsArray
    .filter(l => l.status === 'won' && !projLeadIds.has(l.id))
    .forEach(l => {
      cards.push({
        key:         `l-${l.id}`,
        type:        'lead',
        projectId:   null,
        leadId:      l.id,
        companyName: l.company_name || `Lead #${l.id}`,
        websiteUrl:  l.website_url  || null,
        phase:       'phase_1',
        project:     null,
        lead:        l,
      });
    });

  return cards;
}

export default function LeadPipeline() {
  const navigate         = useNavigate();
  const { user, token }  = useAuth();
  const { isMobile }     = useScreenSize();
  const [activeTab, setActiveTab]         = useState(0);
  const [activeLeadTab, setActiveLeadTab] = useState('alle');
  const [cards, setCards]                 = useState([]);
  const [loading, setLoading]     = useState(true);
  const [dragging, setDragging]   = useState(null);
  const [dragOver, setDragOver]   = useState(null);

  const fetchedRef = useRef(false);
  const mkH = () => ({ 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) });

  useEffect(() => {
    if (fetchedRef.current) return;
    fetchedRef.current = true;
    loadData();
  }, []); // eslint-disable-line

  const loadData = async () => {
    try {
      const [leadsRes, projRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/leads/?limit=500`, { headers: mkH() }),
        fetch(`${API_BASE_URL}/api/projects/?limit=200`, { headers: mkH() }),
      ]);
      const leadsData = await leadsRes.json();
      const projData  = await projRes.json();
      setCards(buildCards(
        Array.isArray(projData)  ? projData  : [],
        Array.isArray(leadsData) ? leadsData : [],
      ));
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const getColCards = (phaseId) => {
    const src = activeLeadTab === 'alle' ? cards : cards.filter(c => {
      const s = c.lead?.status || '';
      if (activeLeadTab === 'neu')     return !s || s === 'neu';
      if (activeLeadTab === 'kontakt') return s === 'kontaktiert';
      if (activeLeadTab === 'angebot') return s === 'angebot';
      return true;
    });
    return src.filter(c => c.phase === phaseId)
              .sort((a, b) => new Date(b.lead?.created_at || b.project?.created_at || 0)
                            - new Date(a.lead?.created_at || a.project?.created_at || 0));
  };

  const updatePhase = async (card, newPhase) => {
    if (!card.projectId) return; // won-lead fallback cards can't be dragged to a different phase
    try {
      await fetch(`${API_BASE_URL}/api/projects/${card.projectId}/phase`, {
        method: 'PATCH', headers: mkH(),
        body: JSON.stringify({ new_status: newPhase }),
      });
      setCards(prev => prev.map(c => c.key === card.key ? { ...c, phase: newPhase } : c));
    } catch (e) { console.error(e); }
  };

  const handleDragStart = (e, card) => { setDragging(card); e.dataTransfer.effectAllowed = 'move'; };
  const handleDrop = (e, phaseId) => {
    e.preventDefault();
    if (dragging && dragging.phase !== phaseId) updatePhase(dragging, phaseId);
    setDragging(null); setDragOver(null);
  };

  if (loading) return (
    <div style={{ display: 'flex', gap: 10 }}>
      {[1,2,3,4,5,6,7].map(i => <div key={i} className="skeleton" style={{ flex: 1, height: 280, borderRadius: 'var(--radius-lg)' }} />)}
    </div>
  );

  return (
    <div style={{ animation: 'fadeIn 0.3s ease', width: '100%', minWidth: 0, overflowX: 'hidden' }}>
      {/* Header */}
      <div style={{ marginBottom: 16 }}>
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 28, fontWeight: 700, color: 'var(--kc-dark)', textTransform: 'uppercase', letterSpacing: '0.02em', lineHeight: 1, margin: 0 }}>Projektpipeline</h1>
        <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '.1em', textTransform: 'uppercase', color: 'var(--text-30)', marginTop: 4, fontFamily: 'var(--font-sans)' }}>
          {cards.length} aktive Projekte · Drag & Drop zum Verschieben
        </div>
      </div>

      {/* Mobile status pills */}
      {isMobile && (
        <div style={{
          display: 'flex', gap: 8, overflowX: 'auto',
          scrollbarWidth: 'none', marginBottom: 12, paddingBottom: 2,
        }}>
          {[
            { id: 'alle',    label: 'Alle' },
            { id: 'neu',     label: 'Neu' },
            { id: 'kontakt', label: 'Kontaktiert' },
            { id: 'angebot', label: 'Angebot' },
          ].map(p => (
            <button key={p.id} onClick={() => setActiveLeadTab(p.id)} style={{
              flexShrink: 0, padding: '7px 14px', borderRadius: 20,
              fontSize: 12, fontWeight: 700, cursor: 'pointer', whiteSpace: 'nowrap',
              border: activeLeadTab === p.id ? 'none' : '1.5px solid #D5E0E2',
              background: activeLeadTab === p.id ? '#004F59' : '#fff',
              color: activeLeadTab === p.id ? '#fff' : '#4A5A5C',
              fontFamily: 'var(--font-sans)', transition: 'all .12s',
            }}>
              {p.label}
            </button>
          ))}
        </div>
      )}

      {/* KPI bar */}
      <div style={{ display: 'grid', gridTemplateColumns: isMobile ? 'repeat(4, 1fr)' : 'repeat(7, 1fr)', gap: 6, marginBottom: 16, minWidth: 0, width: '100%' }}>
        {PHASES.map(ph => (
          <div key={ph.id} style={{
            background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
            borderRadius: 'var(--radius-md)', padding: '8px 10px', borderTop: `3px solid ${ph.color}`,
          }}>
            <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginBottom: 2 }}>{ph.icon} {ph.label}</div>
            <div style={{ fontSize: 18, fontWeight: 700, color: ph.color }}>{getColCards(ph.id).length}</div>
          </div>
        ))}
      </div>

      {/* Kanban */}
      {isMobile ? (
        <div>
          <div style={{ position: 'relative' }}>
            <div style={{ display: 'flex', gap: 4, overflowX: 'auto', paddingBottom: 8, marginBottom: 4, scrollbarWidth: 'none', msOverflowStyle: 'none', WebkitOverflowScrolling: 'touch' }}>
              {PHASES.map((ph, idx) => (
                <button key={ph.id} onClick={() => setActiveTab(idx)} style={{
                  flexShrink: 0, whiteSpace: 'nowrap', padding: '6px 12px', borderRadius: 'var(--radius-full)',
                  border: 'none', cursor: 'pointer', fontFamily: 'var(--font-sans)', fontSize: 12,
                  background: activeTab === idx ? 'var(--bg-active)' : 'transparent',
                  color: activeTab === idx ? 'var(--brand-primary)' : 'var(--text-secondary)',
                  fontWeight: activeTab === idx ? 500 : 400,
                }}>
                  {ph.label} <span style={{ opacity: 0.6 }}>{getColCards(ph.id).length}</span>
                </button>
              ))}
            </div>
            <div style={{ position: 'absolute', right: 0, top: 0, bottom: 8, width: 32, background: 'linear-gradient(to right, transparent, var(--bg-app))', pointerEvents: 'none' }} />
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 8, textAlign: 'right' }}>
            Phase {activeTab + 1} / {PHASES.length} — wischen zum Wechseln
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {getColCards(PHASES[activeTab].id).map(card => (
              <ProjectKanbanCard key={card.key} card={card} phase={PHASES[activeTab]}
                onDragStart={() => {}}
                onOpen={() => card.projectId ? navigate(`/app/projects/${card.projectId}`) : navigate(`/app/leads/${card.leadId}`)} />
            ))}
            {getColCards(PHASES[activeTab].id).length === 0 && <EmptyCol />}
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start', overflowX: 'auto', paddingBottom: 8, minWidth: 0 }}>
          {PHASES.map(ph => {
            const colCards = getColCards(ph.id);
            const over     = dragOver === ph.id;
            return (
              <div key={ph.id}
                onDragOver={e => { e.preventDefault(); setDragOver(ph.id); }}
                onDrop={e => handleDrop(e, ph.id)}
                onDragLeave={() => setDragOver(null)}
                style={{
                  flex: '1 1 0', minWidth: 152,
                  background: over ? `${ph.color}08` : 'var(--bg-app)',
                  borderRadius: 'var(--radius-lg)',
                  border: `1.5px ${over ? 'dashed' : 'solid'} ${over ? ph.color : 'var(--border-light)'}`,
                  transition: 'all 0.15s', padding: 6,
                }}>
                <div style={{ padding: '6px 6px 4px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    {ph.icon} {ph.label}
                  </span>
                  <span style={{ fontSize: 10, padding: '1px 6px', borderRadius: 10, background: `${ph.color}20`, color: ph.color, fontWeight: 600 }}>{colCards.length}</span>
                </div>
                <div style={{ height: 2, background: ph.color, margin: '6px 4px', borderRadius: 2 }} />
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {colCards.map(card => (
                    <ProjectKanbanCard key={card.key} card={card} phase={ph}
                      onDragStart={handleDragStart}
                      onOpen={() => card.projectId ? navigate(`/app/projects/${card.projectId}`) : navigate(`/app/leads/${card.leadId}`)} />
                  ))}
                  {cards.length === 0 && <EmptyCol />}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ── Project Kanban Card ───────────────────────────────────────────────────────

function ProjectKanbanCard({ card, phase, onDragStart, onOpen }) {
  const { companyName, websiteUrl, project, type } = card;
  const domain  = getDomain(websiteUrl);
  const pNum    = phase ? PHASES.findIndex(p => p.id === phase.id) + 1 : null;
  const scM     = project?.pagespeed_mobile;
  const scStyle = speedColor(scM);
  const certKey = (project?.audit_level || '').toLowerCase();
  const certSt  = CERT_STYLES[certKey];

  return (
    <div
      draggable={!!card.projectId}
      onDragStart={e => onDragStart(e, card)}
      onClick={onOpen}
      style={{
        background: 'var(--bg-surface)', borderRadius: 'var(--radius-md)',
        border: `1px solid ${type === 'lead' ? 'rgba(13,110,253,0.25)' : 'var(--border-light)'}`,
        padding: '10px 11px', cursor: 'pointer',
        boxShadow: 'var(--shadow-card)', transition: 'all 0.15s',
        display: 'flex', flexDirection: 'column', gap: 6,
      }}
      onMouseEnter={e => { e.currentTarget.style.borderColor = phase?.color || 'var(--border-medium)'; e.currentTarget.style.boxShadow = 'var(--shadow-elevated)'; }}
      onMouseLeave={e => { e.currentTarget.style.borderColor = type === 'lead' ? 'rgba(13,110,253,0.25)' : 'var(--border-light)'; e.currentTarget.style.boxShadow = 'var(--shadow-card)'; }}
    >
      {/* Firmenname + domain */}
      <div>
        <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {companyName}
        </div>
        {domain && (
          <div style={{ fontSize: 10, color: 'var(--brand-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginTop: 1 }}>
            {domain}
          </div>
        )}
      </div>

      {/* Phase label + progress bar */}
      <div>
        <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginBottom: 3 }}>
          {type === 'lead' ? 'Gewonnen · kein Projekt' : `Phase ${pNum} von 7 · ${phase?.label}`}
        </div>
        <div style={{ height: 4, background: 'var(--border-light)', borderRadius: 2, overflow: 'hidden' }}>
          <div style={{ width: type === 'project' ? `${((pNum || 1) / 7) * 100}%` : '8%', height: '100%', background: 'var(--kc-mid)', borderRadius: 2 }} />
        </div>
      </div>

      {/* Badges row */}
      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', alignItems: 'center' }}>
        {scStyle && scM !== null && scM !== undefined && (
          <span style={{ fontSize: 10, fontWeight: 600, padding: '2px 6px', borderRadius: 10, background: scStyle.bg, color: scStyle.text }}>
            📱 {scM}
          </span>
        )}
        {certSt && (
          <span style={{ fontSize: 10, fontWeight: 600, padding: '2px 6px', borderRadius: 10, background: certSt.bg, color: certSt.text }}>
            🏅 {project.audit_level}
          </span>
        )}
        {type === 'lead' && !certSt && (
          <span style={{ fontSize: 10, color: 'var(--brand-primary)', fontWeight: 500 }}>→ Projekt anlegen</span>
        )}
      </div>
    </div>
  );
}

function EmptyCol() {
  return (
    <div style={{ padding: '16px 8px', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 11, border: '1.5px dashed var(--border-light)', borderRadius: 'var(--radius-md)' }}>
      Keine Projekte
    </div>
  );
}
