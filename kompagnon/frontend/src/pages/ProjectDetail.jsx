import React, { useEffect, useState, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import toast from 'react-hot-toast';
import PhaseTracker from '../components/PhaseTracker';
import MarginBadge from '../components/MarginBadge';
import ProjectCard from '../components/ProjectCard';
import { useAuth } from '../context/AuthContext';

import API_BASE_URL from '../config';

// ── CMS options ───────────────────────────────────────────────────────────────
const CMS_OPTIONS  = ['WordPress', 'Wix', 'TYPO3', 'Webflow', 'Sonstige'];
const PKG_OPTIONS  = ['kompagnon', 'starter', 'professional', 'enterprise'];
const PAY_OPTIONS  = ['offen', 'bezahlt', 'überfällig'];

// ── Edit Modal ────────────────────────────────────────────────────────────────
function EditModal({ project, token, onClose, onSaved }) {
  const [form, setForm] = useState({
    website_url:    project.website_url    || '',
    cms_type:       project.cms_type       || '',
    contact_name:   project.contact_name   || '',
    contact_phone:  project.contact_phone  || '',
    contact_email:  project.contact_email  || '',
    go_live_date:   project.go_live_date
                      ? String(project.go_live_date).slice(0, 10)
                      : '',
    package_type:   project.package_type   || 'kompagnon',
    payment_status: project.payment_status || 'offen',
    desired_pages:  project.desired_pages  || '',
    has_logo:       !!project.has_logo,
    has_briefing:   !!project.has_briefing,
    has_photos:     !!project.has_photos,
    top_problems:   project.top_problems   || '',
    industry:       project.industry       || '',
  });
  const [saving, setSaving] = useState(false);

  const set = (key, val) => setForm(f => ({ ...f, [key]: val }));

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.put(
        `${API_BASE_URL}/api/projects/${project.id}`,
        form,
        { headers: { Authorization: `Bearer ${token}` } },
      );
      toast.success('Projektdaten gespeichert');
      onSaved();
    } catch {
      toast.error('Speichern fehlgeschlagen');
    } finally {
      setSaving(false);
    }
  };

  // ── styles ────────────────────────────────────────────────────────────────
  const overlay = {
    position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    zIndex: 1000, padding: 16,
  };
  const panel = {
    background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)',
    width: '100%', maxWidth: 600, maxHeight: '90vh', overflowY: 'auto',
    display: 'flex', flexDirection: 'column',
    boxShadow: '0 20px 60px rgba(0,0,0,0.25)',
  };
  const header = {
    padding: '18px 20px', borderBottom: '1px solid var(--border-light)',
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    position: 'sticky', top: 0, background: 'var(--bg-surface)', zIndex: 1,
  };
  const body = { padding: '20px', display: 'flex', flexDirection: 'column', gap: 16 };
  const footer = {
    padding: '14px 20px', borderTop: '1px solid var(--border-light)',
    display: 'flex', justifyContent: 'flex-end', gap: 8,
    position: 'sticky', bottom: 0, background: 'var(--bg-surface)',
  };
  const fieldGroup = (n = 1) => ({
    display: 'grid', gridTemplateColumns: `repeat(${n}, 1fr)`, gap: 12,
  });
  const label = { fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4, display: 'block' };
  const input = {
    width: '100%', padding: '8px 10px', borderRadius: 'var(--radius-md)',
    border: '1px solid var(--border-medium)', background: 'var(--bg-app)',
    color: 'var(--text-primary)', fontSize: 13, fontFamily: 'var(--font-sans)',
    outline: 'none', boxSizing: 'border-box',
  };
  const select = { ...input, cursor: 'pointer' };
  const textarea = { ...input, resize: 'vertical', minHeight: 72 };
  const checkRow = { display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: 'var(--text-primary)', cursor: 'pointer' };

  const Field = ({ label: lbl, children }) => (
    <div>
      <label style={label}>{lbl}</label>
      {children}
    </div>
  );

  return (
    <div style={overlay} onClick={e => e.target === e.currentTarget && onClose()}>
      <div style={panel}>
        <div style={header}>
          <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Projektdaten bearbeiten</span>
          <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', color: 'var(--text-tertiary)', lineHeight: 1 }}>×</button>
        </div>

        <div style={body}>
          {/* Website + CMS */}
          <div style={fieldGroup(2)}>
            <Field label="Website-URL">
              <input style={input} value={form.website_url} onChange={e => set('website_url', e.target.value)} placeholder="https://…" />
            </Field>
            <Field label="CMS-Typ">
              <select style={select} value={form.cms_type} onChange={e => set('cms_type', e.target.value)}>
                <option value="">– wählen –</option>
                {CMS_OPTIONS.map(o => <option key={o} value={o}>{o}</option>)}
              </select>
            </Field>
          </div>

          {/* Ansprechpartner */}
          <div style={fieldGroup(3)}>
            <Field label="Name">
              <input style={input} value={form.contact_name} onChange={e => set('contact_name', e.target.value)} placeholder="Max Mustermann" />
            </Field>
            <Field label="Telefon">
              <input style={input} value={form.contact_phone} onChange={e => set('contact_phone', e.target.value)} placeholder="+49 …" />
            </Field>
            <Field label="E-Mail">
              <input style={input} value={form.contact_email} onChange={e => set('contact_email', e.target.value)} placeholder="name@…" />
            </Field>
          </div>

          {/* Paket + Zahlung + Go-live */}
          <div style={fieldGroup(3)}>
            <Field label="Paket">
              <select style={select} value={form.package_type} onChange={e => set('package_type', e.target.value)}>
                {PKG_OPTIONS.map(o => <option key={o} value={o}>{o}</option>)}
              </select>
            </Field>
            <Field label="Zahlungsstatus">
              <select style={select} value={form.payment_status} onChange={e => set('payment_status', e.target.value)}>
                {PAY_OPTIONS.map(o => <option key={o} value={o}>{o}</option>)}
              </select>
            </Field>
            <Field label="Go-live Datum">
              <input style={input} type="date" value={form.go_live_date} onChange={e => set('go_live_date', e.target.value)} />
            </Field>
          </div>

          {/* Branche */}
          <Field label="Branche">
            <input style={input} value={form.industry} onChange={e => set('industry', e.target.value)} placeholder="z.B. Gastronomie" />
          </Field>

          {/* Gewünschte Seiten */}
          <Field label="Gewünschte Seiten (kommagetrennt)">
            <input style={input} value={form.desired_pages} onChange={e => set('desired_pages', e.target.value)} placeholder="Startseite, Über uns, Kontakt, …" />
          </Field>

          {/* Assets */}
          <div>
            <span style={label}>Assets vorhanden</span>
            <div style={{ display: 'flex', gap: 20, marginTop: 4 }}>
              {[['has_logo','Logo'], ['has_briefing','Briefing'], ['has_photos','Fotos']].map(([key, lbl]) => (
                <label key={key} style={checkRow}>
                  <input
                    type="checkbox"
                    checked={form[key]}
                    onChange={e => set(key, e.target.checked)}
                    style={{ width: 15, height: 15, accentColor: '#1D9E75', cursor: 'pointer' }}
                  />
                  {lbl}
                </label>
              ))}
            </div>
          </div>

          {/* Top-Probleme */}
          <Field label="Top-Probleme aus Audit (eine pro Zeile, max. 3)">
            <textarea style={textarea} value={form.top_problems} onChange={e => set('top_problems', e.target.value)} placeholder={"Problem 1\nProblem 2\nProblem 3"} rows={3} />
          </Field>
        </div>

        <div style={footer}>
          <button onClick={onClose} style={{ padding: '8px 16px', background: 'var(--bg-hover)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)', color: 'var(--text-secondary)' }}>
            Abbrechen
          </button>
          <button onClick={handleSave} disabled={saving} style={{ padding: '8px 18px', background: '#185FA5', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600, cursor: saving ? 'wait' : 'pointer', fontFamily: 'var(--font-sans)' }}>
            {saving ? 'Speichern…' : 'Speichern'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function ProjectDetail() {
  const { id }         = useParams();
  const { token }      = useAuth();
  const headers        = token ? { Authorization: `Bearer ${token}` } : {};

  const [project, setProject]     = useState(null);
  const [margin, setMargin]       = useState(null);
  const [loading, setLoading]     = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [showEdit, setShowEdit]   = useState(false);

  const loadProject = useCallback(async () => {
    try {
      setLoading(true);
      const [projectRes, marginRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/api/projects/${id}`, { headers }),
        axios.get(`${API_BASE_URL}/api/projects/${id}/margin`, { headers }),
      ]);
      setProject(projectRes.data);
      setMargin(marginRes.data);
    } catch {
      toast.error('Projekt konnte nicht geladen werden.');
    } finally {
      setLoading(false);
    }
  }, [id]); // eslint-disable-line

  useEffect(() => { loadProject(); }, [id]); // eslint-disable-line

  if (loading || !project) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div className="skeleton" style={{ height: 40, width: 300 }} />
        <div className="skeleton" style={{ height: 60 }} />
        <div className="skeleton" style={{ height: 200 }} />
      </div>
    );
  }

  const tabs = ['overview', 'checklists', 'zeit', 'kommunikation'];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ marginBottom: 0 }}>
          <span>Projekt #{project.id}</span>
          <h1 style={{ fontSize: 'var(--kc-text-3xl)', margin: 0 }}>{project.company_name}</h1>
        </div>
        {margin && <MarginBadge marginPercent={margin.margin_percent} status={margin.status} />}
      </div>

      {/* ── ProjectCard ─────────────────────────────────────────────────────── */}
      <ProjectCard project={project} />

      {/* ── Edit button ─────────────────────────────────────────────────────── */}
      <div>
        <button
          onClick={() => setShowEdit(true)}
          style={{
            padding: '9px 18px', background: 'var(--bg-surface)',
            border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
            fontSize: 13, fontWeight: 600, cursor: 'pointer',
            fontFamily: 'var(--font-sans)', color: 'var(--text-primary)',
            display: 'inline-flex', alignItems: 'center', gap: 6,
          }}
        >
          ✏️ Projektdaten bearbeiten
        </button>
      </div>

      {/* ── Phase Tracker ───────────────────────────────────────────────────── */}
      <div className="kc-card">
        <PhaseTracker currentPhase={project.status} />
      </div>

      {/* ── Tabs ───────────────────────────────────────────────────────────── */}
      <div className="kc-tabs">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`kc-tab ${activeTab === tab ? 'kc-tab--active' : ''}`}
          >
            {tab === 'overview'       ? 'Übersicht'    :
             tab === 'checklists'     ? 'Checklisten'  :
             tab === 'zeit'           ? 'Zeiterfassung': 'Kommunikation'}
          </button>
        ))}
      </div>

      {/* ── Overview Tab ────────────────────────────────────────────────────── */}
      {activeTab === 'overview' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          <div className="kc-card" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 24 }}>
            <InfoBlock label="Status" value={project.status.replace('phase_', 'Phase ')} />
            <InfoBlock label="Festpreis" value={`€${project.fixed_price.toFixed(2)}`} mono />
            <InfoBlock label="Stunden geloggt" value={`${project.actual_hours.toFixed(1)}h`} mono />
            {margin && <InfoBlock label="Gesamtkosten" value={`€${margin.total_costs.toFixed(2)}`} mono />}
          </div>

          {margin && (
            <div className="kc-card" style={{ background: margin.status === 'red' ? 'var(--kc-rot-subtle)' : 'var(--bg-app)', border: margin.status === 'red' ? '1px solid var(--brand-primary)' : '1px solid var(--border-light)' }}>
              <div style={{ marginBottom: 16 }}>
                <span>Marge</span>
                <h2 style={{ fontSize: 22, margin: 0 }}>Profitabilität</h2>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 24 }}>
                <InfoBlock label="Personenstunden" value={`${margin.human_hours.toFixed(1)}h × €${project.hourly_rate}/h`} mono />
                <InfoBlock label="KI-Kosten" value={`€${margin.ai_tool_costs.toFixed(2)}`} mono />
                <InfoBlock label="Verbleibend bis 70%" value={`${margin.hours_remaining_at_target.toFixed(1)}h`} mono />
                <InfoBlock label="Marge" value={<MarginBadge marginPercent={margin.margin_percent} status={margin.status} />} raw />
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Placeholder tabs ────────────────────────────────────────────────── */}
      {activeTab !== 'overview' && (
        <div className="kc-card" style={{ textAlign: 'center', padding: 'var(--kc-space-16)', color: 'var(--text-tertiary)' }}>
          <p style={{ fontSize: 16, fontWeight: 600 }}>
            {activeTab === 'checklists' ? 'Checklisten' : activeTab === 'zeit' ? 'Zeiterfassung' : 'Kommunikation'}
          </p>
          <p style={{ fontSize: 13 }}>In Entwicklung</p>
        </div>
      )}

      {/* ── Edit Modal ──────────────────────────────────────────────────────── */}
      {showEdit && (
        <EditModal
          project={project}
          token={token}
          onClose={() => setShowEdit(false)}
          onSaved={() => { setShowEdit(false); loadProject(); }}
        />
      )}
    </div>
  );
}

// ── InfoBlock ─────────────────────────────────────────────────────────────────
function InfoBlock({ label, value, mono = false, raw = false }) {
  return (
    <div>
      <p style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 'var(--kc-tracking-wide)', color: 'var(--text-tertiary)', marginBottom: 4 }}>
        {label}
      </p>
      {raw ? (
        <div>{value}</div>
      ) : (
        <p style={{ fontSize: 16, fontWeight: 700, fontFamily: mono ? 'var(--font-mono)' : 'var(--font-sans)', color: 'var(--text-primary)', margin: 0 }}>
          {value}
        </p>
      )}
    </div>
  );
}
