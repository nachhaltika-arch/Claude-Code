import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import API_BASE_URL from '../config';
import { saveJson } from '../utils/apiRequest';
import AssistentPanel from './AssistentPanel';
import { textUebernehmen } from '../utils/assistentUebernahme';
import { useScreenSize } from '../utils/responsive';
import { useEscapeKey } from '../hooks/useKeyboardShortcuts';
import { useAuth } from '../context/AuthContext';
import { aufTaste } from '../utils/tastaturBedienung';
import {
  ASSISTENT_FELD, STEPS, Step1, Step2, Step3, Step4, Step5, Step6, TEAL,
  clearDraft, formatDraftAge, loadDraft, saveDraft,
} from './briefing2/briefingSchritte';

export default function BriefingWizard({ leadId, leadData, onClose, onComplete, embedded = false,
  /**
   * Ohne die KI-Vorschlagsknoepfe (26.08.2026). Im Kundenportal sind sie
   * gesperrt — jeder Klick ist ein Modellaufruf, und ob Kunden ihn ausloesen
   * duerfen, ist eine Preisfrage. Der Knopf gehoert dann weg, nicht ins
   * Leere: Ein Knopf, der zuverlaessig „Nur fuer den Innendienst" antwortet,
   * ist schlechter als keiner.
   */
  ohneVorschlaege = false,
  /**
   * Bedient ein **Kunde** den Assistenten? (26.08.2026)
   *
   * Der Innendienst spricht `/api/briefings/{id}`, der Kunde
   * `/api/briefings/mein/{id}`. **Warum nicht dieselbe Adresse fuer beide:**
   * Zwei Router auf einer Adresse verdecken sich still — das hat L-27
   * gekostet, und ein Test verbietet es seither.
   *
   * **Warum ein Wahrheitswert und kein Pfad-Parameter:** Ein Vorgabewert
   * `'/api/briefings'` sieht fuer `test_frontend_adressen.py` aus wie ein
   * Aufruf einer Adresse, die es so nicht gibt — der Waechter schlug beim
   * Bauen genau darauf an. Jetzt stehen beide Adressen ausgeschrieben da,
   * und er prueft zwei echte.
   */
  kundenweg = false }) {
  const { isMobile, isTablet } = useScreenSize();
  // Bei Tablet UND Mobile (Width < 1024) den Stepper-Bereich kompakt halten,
  // sonst frisst die 6-stufige Stepper-Liste den knappen Body-Platz auf
  // kurzen / schmalen Browsern.
  const isCompact = isMobile || isTablet;
  const { token } = useAuth();
  const suggestHeaders = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };
  const briefingAdresse = (zusatz = '') => (kundenweg
    ? `${API_BASE_URL}/api/briefings/mein/${leadId}${zusatz}`
    : `${API_BASE_URL}/api/briefings/${leadId}${zusatz}`);
  const existingDraft = loadDraft(leadId);

  const [step, setStep] = useState(existingDraft?.step ?? 0);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [draftBanner, setDraftBanner] = useState(existingDraft ? formatDraftAge(existingDraft.savedAt) : null);
  const [suggestions, setSuggestions] = useState({});
  const [showErrors, setShowErrors] = useState(false);
  const [autoSaveStatus, setAutoSaveStatus] = useState('');
  const firstFieldRef = useRef(null);

  const suggestField = async (field) => {
    setSuggestions(prev => ({ ...prev, [field]: { loading: true, value: null, error: null } }));
    try {
      const res = await fetch(`${API_BASE_URL}/api/briefings/${leadId}/suggest-field`, { method: 'POST', headers: suggestHeaders, body: JSON.stringify({ field }) });
      if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.detail || 'Fehler'); }
      const { suggestion } = await res.json();
      setSuggestions(prev => ({ ...prev, [field]: { loading: false, value: suggestion, error: null } }));
    } catch (e) {
      setSuggestions(prev => ({ ...prev, [field]: { loading: false, value: null, error: e.message } }));
    }
  };
  const applySuggestion = (field) => setSuggestions(prev => ({ ...prev, [field]: { ...prev[field], value: null } }));

  // Esc schließt den Wizard
  useEscapeKey(onClose, true);

  // Auto-Focus auf erstes Feld bei Schritt-Wechsel
  useEffect(() => {
    const t = setTimeout(() => {
      if (firstFieldRef.current) {
        const el = firstFieldRef.current.querySelector('input,textarea,select');
        el?.focus();
      }
    }, 120);
    return () => clearTimeout(t);
  }, [step]);

  // Draft-Banner nach 5 Sekunden ausblenden
  useEffect(() => {
    if (!draftBanner) return;
    const t = setTimeout(() => setDraftBanner(null), 5000);
    return () => clearTimeout(t);
  }, [draftBanner]);

  const defaultData = {
    gewerk:            leadData?.gewerk            || '',
    wz_code:           leadData?.wz_code           || '',
    wz_title:          leadData?.wz_title          || '',
    leistungen:        leadData?.leistungen        || '',
    einzugsgebiet:     leadData?.einzugsgebiet     || '',
    zielgruppe:        typeof leadData?.zielgruppe === 'string' ? leadData.zielgruppe : leadData?.zielgruppe?.primaer || '',
    typischerKunde:    leadData?.typischerKunde    || '',
    haeufigeAnfrage:   leadData?.haeufigeAnfrage   || '',
    usp:               leadData?.usp               || '',
    mitbewerber:       leadData?.mitbewerber       || '',
    vorbilder:         leadData?.vorbilder         || '',
    inspiration_url_1: leadData?.inspiration_url_1 || '',
    inspiration_url_2: leadData?.inspiration_url_2 || '',
    inspiration_url_3: leadData?.inspiration_url_3 || '',
    farben:            leadData?.farben            || '',
    stil:              leadData?.stil              || '',
    wunschseiten:      leadData?.wunschseiten
      ? (Array.isArray(leadData.wunschseiten)
          ? leadData.wunschseiten
          : leadData.wunschseiten.split(', ').filter(Boolean))
      : [],
    logo_vorhanden:    leadData?.logo_vorhanden    ?? false,
    fotos_vorhanden:   leadData?.fotos_vorhanden   ?? false,
    sonstige_hinweise: leadData?.sonstige_hinweise || '',
  };

  const [data, setData] = useState(() => existingDraft?.data || defaultData);

  // Sync from leadData when it arrives (e.g. after async briefing load)
  useEffect(() => {
    if (!leadData) return;
    setData(prev => {
      // Only fill empty fields — don't overwrite user edits
      const hasUserInput = prev.gewerk || prev.leistungen || prev.usp;
      if (hasUserInput) return prev;
      const updated = { ...prev };
      for (const key of Object.keys(prev)) {
        if (!prev[key] && leadData[key]) {
          if (key === 'zielgruppe') {
            updated[key] = typeof leadData[key] === 'string' ? leadData[key] : leadData[key]?.primaer || '';
          } else if (key === 'wunschseiten') {
            updated[key] = Array.isArray(leadData[key]) ? leadData[key] : (leadData[key] || '').split(', ').filter(Boolean);
          } else {
            updated[key] = leadData[key];
          }
        }
      }
      return updated;
    });
  }, [leadData]); // eslint-disable-line

  const set = (key, val) => setData(d => ({ ...d, [key]: val }));

  // ── Assistent ──────────────────────────────────────────────────────────────
  // Er sieht immer nur das Feld des aktuellen Schritts. Ein übernommener
  // Vorschlag hängt sich an vorhandenen Text an, statt ihn zu ersetzen —
  // niemand soll durch einen Klick eigene Arbeit verlieren.
  const assistentFeld = ASSISTENT_FELD[step] || { regel: '', formular: '' };
  const uebernehmen = assistentFeld.formular
    ? (text) => set(
        assistentFeld.formular,
        textUebernehmen(data[assistentFeld.formular], text),
      )
    : null;
  const assistent = (
    <AssistentPanel
      leadId={leadId}
      feld={assistentFeld.regel}
      schritt={STEPS[step]}
      wert={assistentFeld.regel ? (data[assistentFeld.formular] || '') : ''}
      onUebernehmen={uebernehmen}
      kompakt={isCompact}
    />
  );

  // Auto-Save Draft bei jeder Änderung (nur wenn echte Daten vorhanden)
  useEffect(() => {
    if (data.gewerk || data.leistungen || data.usp || data.farben || data.stil) {
      saveDraft(leadId, data, step);
    }
  }, [data, step, leadId]);

  const [touched, setTouched] = useState({});
  const touch = (field) => setTouched(prev => ({ ...prev, [field]: true }));
  const touchStep = (stepIndex) => {
    const fields = { 0: ['gewerk', 'leistungen'], 1: ['zielgruppe'], 2: ['usp'], 3: ['stil'], 4: [] };
    const toTouch = {};
    (fields[stepIndex] || []).forEach(f => { toTouch[f] = true; });
    setTouched(prev => ({ ...prev, ...toTouch }));
  };
  const fieldError = (field) => {
    if (!touched[field]) return null;
    const msgs = { gewerk: 'Bitte Branche auswählen', leistungen: 'Bitte Leistungen eintragen', zielgruppe: 'Bitte Zielgruppe auswählen', usp: 'Bitte USP eintragen', stil: 'Bitte Designstil auswählen' };
    const empty = { gewerk: !data.gewerk && !data.wz_code, leistungen: !data.leistungen?.trim(), zielgruppe: !data.zielgruppe, usp: !data.usp?.trim(), stil: !data.stil };
    return empty[field] ? (msgs[field] || 'Pflichtfeld') : null;
  };

  const canNext = () => {
    if (step === 0) return !!(data.gewerk || data.wz_code) && !!data.leistungen.trim();
    if (step === 1) return !!data.zielgruppe;
    if (step === 2) return !!data.usp.trim();
    if (step === 3) return !!data.stil;
    if (step === 4) return data.wunschseiten.length > 0;
    return true;
  };

  const handleSaveAndPdf = async () => {
    setSaving(true);
    setSaveError('');
    try {
      const token = localStorage.getItem('kompagnon_token');
      const payload = {
        gewerk:            data.gewerk,
        wz_code:           data.wz_code,
        wz_title:          data.wz_title,
        leistungen:        data.leistungen,
        einzugsgebiet:     data.einzugsgebiet,
        usp:               data.usp,
        mitbewerber:       data.mitbewerber,
        vorbilder:         data.vorbilder,
        inspiration_url_1: data.inspiration_url_1,
        inspiration_url_2: data.inspiration_url_2,
        inspiration_url_3: data.inspiration_url_3,
        farben:            data.farben,
        stil:              data.stil,
        wunschseiten:      data.wunschseiten.join(', '),
        logo_vorhanden:    data.logo_vorhanden,
        fotos_vorhanden:   data.fotos_vorhanden,
        sonstige_hinweise: data.sonstige_hinweise,
      };
      const res = await fetch(briefingAdresse(), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Fehler ${res.status}`);
      }
      // Additionally persist inspiration URLs on the lead itself
      try {
        await fetch(`${API_BASE_URL}/api/leads/${leadId}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify({
            inspiration_url_1: data.inspiration_url_1 || null,
            inspiration_url_2: data.inspiration_url_2 || null,
            inspiration_url_3: data.inspiration_url_3 || null,
          }),
        });
      } catch (_) { /* non-fatal */ }
      // Open PDF in new tab (with auth)
      clearDraft(leadId);
      try {
        const pdfRes = await fetch(briefingAdresse('/pdf'), {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (pdfRes.ok) {
          const blob = await pdfRes.blob();
          const url = URL.createObjectURL(blob);
          window.open(url, '_blank');
          setTimeout(() => URL.revokeObjectURL(url), 60000);
        }
      } catch (_) { /* PDF download non-fatal */ }
      if (onComplete) onComplete(data);
    } catch (e) {
      setSaveError(e.message || 'Speichern fehlgeschlagen.');
    } finally {
      setSaving(false);
    }
  };

  const buildPayload = () => ({
    gewerk: data.gewerk, wz_code: data.wz_code, wz_title: data.wz_title,
    leistungen: data.leistungen, einzugsgebiet: data.einzugsgebiet,
    usp: data.usp, mitbewerber: data.mitbewerber, vorbilder: data.vorbilder,
    farben: data.farben, stil: data.stil,
    wunschseiten: Array.isArray(data.wunschseiten) ? data.wunschseiten.join(', ') : data.wunschseiten || '',
    logo_vorhanden: data.logo_vorhanden, fotos_vorhanden: data.fotos_vorhanden,
    sonstige_hinweise: data.sonstige_hinweise,
  });

  const autoSave = async () => {
    setAutoSaveStatus('saving');
    // apiRequest statt fetch: der Status wurde nie geprüft, eine abgelehnte
    // Speicherung zeigte trotzdem "gespeichert".
    const t = localStorage.getItem('kompagnon_token');
    const saved = await saveJson(
      briefingAdresse(),
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${t}` },
        body: JSON.stringify(buildPayload()),
      },
      { context: 'Briefing sichern' },
    );

    if (!saved) {
      setAutoSaveStatus('error');
      setTimeout(() => setAutoSaveStatus(''), 3000);
      return;
    }
    setAutoSaveStatus('saved');
    setTimeout(() => setAutoSaveStatus(''), 2000);
  };

  const handleNext = async () => {
    if (!canNext()) { touchStep(step); setShowErrors(true); return; }
    setShowErrors(false);
    await autoSave();
    if (step < STEPS.length - 1) setStep(s => s + 1);
  };

  const handleBack = () => {
    if (step > 0) setStep(s => s - 1);
    else if (onClose) onClose();
  };

  const handleSaveOnly = async () => {
    setSaving(true); setSaveError('');
    try {
      const t = localStorage.getItem('kompagnon_token');
      const res = await fetch(briefingAdresse(), {
        method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${t}` },
        body: JSON.stringify(buildPayload()),
      });
      if (!res.ok) throw new Error((await res.json().catch(()=>({}))).detail || 'Fehler');
      clearDraft(leadId);
      if (onComplete) onComplete(data);
    } catch (e) { setSaveError(e.message); }
    finally { setSaving(false); }
  };

  const renderStep = () => {
    const suggestProps = ohneVorschlaege
      ? { suggestions: {}, onSuggest: null, onApply: applySuggestion }
      : { suggestions, onSuggest: suggestField, onApply: applySuggestion };
    const p = { data, set, touch, fieldError, firstRef: firstFieldRef, ...suggestProps };
    switch (step) {
      case 0: return <Step1 {...p} />;
      case 1: return <Step2 {...p} />;
      case 2: return <Step3 {...p} />;
      case 3: return <Step4 {...p} showErrors={showErrors} />;
      case 4: return <Step5 {...p} />;
      case 5: return <Step6 data={data} saving={saving} error={saveError} onSaveAndPdf={handleSaveAndPdf} onSaveOnly={handleSaveOnly} />;
      default: return null;
    }
  };

  const panelStyle = isMobile
    ? {
        position: 'fixed', left: 0, right: 0, bottom: 0,
        top: 'auto', transform: 'none',
        width: '100%', maxWidth: '100%', maxHeight: '92vh',
        borderRadius: '20px 20px 0 0',
        animation: 'bwSlideUpMobile 0.28s cubic-bezier(0.34, 1.56, 0.64, 1)',
      }
    : {
        position: 'fixed', top: '50%', left: '50%',
        transform: 'translate(-50%, -50%)',
        width: '100%', maxWidth: 680, maxHeight: '95vh',
        borderRadius: 20,
        animation: 'bwSlideUp 0.28s cubic-bezier(0.34, 1.56, 0.64, 1)',
      };

  // ── Embedded: render inline without portal ──
  if (embedded) {
    return (
      <div style={{ borderRadius: 12, border: '1px solid var(--border-light)', background: 'var(--bg-surface)', display: 'flex', flexDirection: 'column', overflow: 'hidden', maxHeight: 600 }}>
        {/* Header */}
        <div style={{ padding: '16px 20px 12px', borderBottom: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'var(--bg-surface)', flexShrink: 0 }}>
          <div>
            <div style={{ fontSize: 12, fontWeight: 600, letterSpacing: '.08em', color: TEAL, textTransform: 'uppercase' }}>Schritt {step + 1} von {STEPS.length}</div>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginTop: 2 }}>{STEPS[step]}</div>
            {leadData?.gewerk ? (
              <div style={{ fontSize: 12, color: '#1D9E75', marginTop: 2 }}>Bestehendes Briefing wird bearbeitet</div>
            ) : (
              <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 2 }}>Neues Briefing anlegen</div>
            )}
          </div>
        </div>
        {/* Body — auf breiten Schirmen steht der Assistent daneben, auf
            schmalen als aufklappbares Widget über dem Formular. */}
        <div style={{ flex: 1, display: 'flex', minHeight: 0 }}>
          <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px' }}>
            {renderStep()}
          </div>
          {!isCompact && (
            <div style={{ width: 300, flexShrink: 0, padding: '20px 20px 20px 0' }}>
              {assistent}
            </div>
          )}
        </div>
        {isCompact && assistent}
        {/* Footer */}
        <div style={{ padding: '12px 20px', borderTop: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0 }}>
          <button onClick={handleBack} style={{ padding: '8px 16px', borderRadius: 8, border: '1px solid var(--border-light)', background: 'var(--bg-app)', color: 'var(--text-secondary)', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
            {step === 0 ? 'Abbrechen' : 'Zurueck'}
          </button>
          <div style={{ fontSize: 12, color: 'var(--text-tertiary)', display: 'flex', alignItems: 'center', gap: 6 }}>
            {autoSaveStatus === 'saving' && (<><span style={{ width: 10, height: 10, border: '1.5px solid var(--border-light)', borderTopColor: TEAL, borderRadius: '50%', animation: 'spin .7s linear infinite', display: 'inline-block' }} /><span>Speichert...</span></>)}
            {autoSaveStatus === 'saved' && <span style={{ color: '#1D9E75' }}>Gespeichert</span>}
            {autoSaveStatus === 'error' && <span style={{ color: '#C0392B' }}>Fehler</span>}
            {!autoSaveStatus && <span>{step + 1} / {STEPS.length}</span>}
          </div>
          {step < STEPS.length - 1 ? (
            <button onClick={handleNext} style={{ padding: '8px 20px', borderRadius: 8, border: 'none', background: canNext() ? TEAL : 'var(--border-medium)', color: '#fff', fontSize: 13, fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
              Weiter
            </button>
          ) : (
            <button onClick={handleSaveAndPdf} disabled={saving} style={{ padding: '8px 20px', borderRadius: 8, border: 'none', background: saving ? 'var(--border-medium)' : 'var(--success)', color: 'var(--text-on-brand)', fontSize: 13, fontWeight: 700, cursor: saving ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)' }}>
              {saving ? 'Speichert...' : 'Speichern'}
            </button>
          )}
        </div>
        {saveError && <div style={{ padding: '8px 20px', fontSize: 12, color: 'var(--status-danger-text)', background: 'var(--status-danger-bg)' }}>{saveError}</div>}
      </div>
    );
  }

  return createPortal(
    <>
      {/* ── Overlay ── */}
      <div
        onClick={async () => {
          const hasData = !!(data.gewerk || data.leistungen || data.usp);
          if (hasData && step > 0) await autoSave(); // meldet eigene Fehler
          onClose?.();
        }}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0, 0, 0, 0.55)',
          backdropFilter: 'blur(4px)',
          WebkitBackdropFilter: 'blur(4px)',
          zIndex: 2000,
          animation: 'bwFadeIn 0.2s ease',
        }}
      />

      {/* ── Modal-Box ── */}
      <div role="button" tabIndex={0} onKeyDown={aufTaste(e => e.stopPropagation())}
        onClick={e => e.stopPropagation()}
        style={{
          ...panelStyle,
          zIndex: 2001,
          background: 'var(--bg-surface)',
          boxShadow: '0 32px 80px rgba(0,0,0,0.25), 0 8px 24px rgba(0,0,0,0.12)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        {/* Drag Handle — Mobile only */}
        {isMobile && (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '10px 0 2px', flexShrink: 0 }}>
            <div style={{ width: 36, height: 4, background: 'var(--border-medium)', borderRadius: 2 }} />
          </div>
        )}

        {/* ── Header ── */}
        <div style={{
          padding: isCompact ? '14px 20px 10px' : '20px 28px 16px',
          borderBottom: '1px solid var(--border-light)',
          flexShrink: 0,
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          gap: 16,
          background: 'var(--bg-surface)',
        }}>
          <div>
            <div style={{
              fontSize: 12,
              fontWeight: 600,
              letterSpacing: '0.08em',
              color: TEAL,
              textTransform: 'uppercase',
              marginBottom: 4,
            }}>
              Website-Briefing · Lead #{leadId}
            </div>
            <div style={{
              fontSize: 20,
              fontWeight: 700,
              color: 'var(--text-primary)',
              lineHeight: 1.2,
            }}>
              {STEPS[step]}
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              flexShrink: 0,
              width: 32, height: 32,
              borderRadius: 8,
              border: '1px solid var(--border-light)',
              background: 'var(--bg-app)',
              cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'var(--text-secondary)',
              fontSize: 18, lineHeight: 1,
              transition: 'background 0.15s',
              fontFamily: 'var(--font-sans)',
              padding: 0,
            }}
            title="Schließen"
          >
            ×
          </button>
        </div>

        {/* ── Stepper / Progress ──
            Auf Tablet+Mobile (isCompact) nur Progress-Bar + Step-Label-Zeile,
            damit der Body-Bereich nicht durch 6 nummerierte Step-Bubbles
            erdrückt wird. Auf Desktop bleibt die volle Stepper-Liste. */}
        <div style={{
          padding: isCompact ? '10px 20px 12px' : '12px 28px 14px',
          flexShrink: 0,
          borderBottom: '1px solid var(--border-light)',
          background: 'var(--bg-surface)',
        }}>
          <div style={{ display: 'flex', gap: 5, marginBottom: isCompact ? 6 : 10 }}>
            {STEPS.map((label, i) => (
              <div
                key={i}
                title={label}
                style={{
                  flex: 1,
                  height: 5,
                  borderRadius: 3,
                  background: i <= step ? TEAL : 'var(--border-light)',
                  opacity: i <= step ? 1 : 0.5,
                  transition: 'background 0.3s, opacity 0.3s',
                }}
              />
            ))}
          </div>
          {isCompact ? (
            <div style={{
              fontSize: 12,
              color: 'var(--text-tertiary)',
              display: 'flex',
              gap: 6,
              alignItems: 'baseline',
            }}>
              <span style={{ fontWeight: 700, color: TEAL }}>Schritt {step + 1} / {STEPS.length}</span>
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                · {STEPS[step]}
              </span>
            </div>
          ) : (
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            {STEPS.map((label, i) => (
              <div key={i} style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 3,
                flex: 1,
                minWidth: 0,
              }}>
                <div style={{
                  width: 22, height: 22,
                  borderRadius: '50%',
                  background: i <= step ? TEAL : 'var(--border-light)',
                  color: i <= step ? '#fff' : 'var(--text-tertiary)',
                  fontSize: 12, fontWeight: 700,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  transition: 'all 0.3s',
                }}>
                  {i < step ? '✓' : i + 1}
                </div>
                <span style={{
                  fontSize: 12,
                  color: i === step ? TEAL : 'var(--text-tertiary)',
                  fontWeight: i === step ? 600 : 400,
                  whiteSpace: 'nowrap',
                  maxWidth: 70,
                  textAlign: 'center',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}>
                  {label}
                </span>
              </div>
            ))}
          </div>
          )}
        </div>

        {/* Draft-Banner */}
        {draftBanner && (
          <div style={{
            margin: '10px 24px 0', padding: '8px 14px',
            background: 'var(--status-warning-bg)', border: '1px solid var(--status-warning-text)',
            borderRadius: 'var(--radius-md, 6px)', fontSize: 12,
            color: 'var(--status-warning-text)',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12,
          }}>
            <span>Entwurf {draftBanner} wiederhergestellt{existingDraft?.step > 0 ? ` — Schritt ${existingDraft.step + 1}` : ''}</span>
            <button
              onClick={() => { clearDraft(leadId); setDraftBanner(null); setData(defaultData); setStep(0); }}
              style={{ background: 'none', border: 'none', fontSize: 12, fontWeight: 600, color: 'var(--status-warning-text)', cursor: 'pointer', textDecoration: 'underline', padding: 0, fontFamily: 'var(--font-sans)' }}
            >Verwerfen</button>
          </div>
        )}

        {/* ── Scrollbarer Formular-Bereich ── */}
        <div style={{ flex: 1, display: 'flex', minHeight: 0, background: 'var(--bg-app)' }}>
          <div style={{
            flex: 1,
            overflowY: 'auto',
            padding: isCompact ? '16px 20px' : '24px 28px',
            scrollbarWidth: 'thin',
            scrollbarColor: 'var(--border-light) transparent',
          }}>
            {renderStep()}
          </div>
          {!isCompact && (
            <div style={{ width: 320, flexShrink: 0, padding: '24px 28px 24px 0' }}>
              {assistent}
            </div>
          )}
        </div>
        {isCompact && assistent}

        {/* ── Footer / Navigation ── */}
        <div style={{
          padding: '16px 28px',
          borderTop: '1px solid var(--border-light)',
          flexShrink: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'var(--bg-surface)',
        }}>
          <button
            onClick={handleBack}
            style={{
              padding: '10px 20px',
              borderRadius: 10,
              border: '1px solid var(--border-light)',
              background: 'var(--bg-app)',
              color: 'var(--text-secondary)',
              fontSize: 14,
              fontWeight: 500,
              cursor: 'pointer',
              fontFamily: 'var(--font-sans)',
              transition: 'all 0.15s',
            }}
          >
            {step === 0 ? 'Abbrechen' : '← Zurück'}
          </button>

          <span style={{
            fontSize: 13,
            color: 'var(--text-tertiary)',
            fontWeight: 500,
          }}>
            {step + 1} / {STEPS.length}
          </span>

          {step < STEPS.length - 1 ? (
            <button
              onClick={handleNext}
              style={{
                padding: '10px 24px',
                borderRadius: 10,
                border: 'none',
                background: canNext() ? TEAL : 'var(--border-medium)',
                color: 'var(--text-inverse)',
                fontSize: 14,
                fontWeight: 700,
                cursor: 'pointer',
                fontFamily: 'var(--font-sans)',
                transition: 'background var(--transition-fast)',
                opacity: canNext() ? 1 : 0.7,
              }}
            >
              Weiter →
            </button>
          ) : (
            <div style={{ width: 120 }} />
          )}
        </div>
      </div>

      {/* ── CSS Animationen ── */}
      <style>{`
        @keyframes bwFadeIn {
          from { opacity: 0; }
          to   { opacity: 1; }
        }
        @keyframes bwSlideUp {
          from { opacity: 0; transform: translate(-50%, calc(-50% + 24px)); }
          to   { opacity: 1; transform: translate(-50%, -50%); }
        }
        @keyframes bwSlideUpMobile {
          from { transform: translateY(100%); }
          to   { transform: translateY(0); }
        }
      `}</style>
    </>,
    document.body
  );
}

