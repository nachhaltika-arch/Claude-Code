/**
 * useAudit — Zentraler Hook für Audit-Start, Polling und Ergebnis.
 *
 * Wird überall verwendet:
 *  - ProzessFlow AuditEmbed (Schritt 6 + QM)
 *  - LeadProfile.jsx
 *  - CustomerDetail.js
 *  - AuditTool.jsx
 *  - AuditHook.jsx
 *
 * Einheitlicher Endpoint: POST /api/audit/start + GET /api/audit/{id}
 * Sauberer Cleanup bei Unmount (kein Memory-Leak).
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import API_BASE_URL from '../config';

const MAX_ATTEMPTS  = 45;   // 45 × 4s = 3 Minuten
const POLL_INTERVAL = 4000; // ms

const PROGRESS_MSGS = [
  'Website wird aufgerufen…',
  'SSL und Erreichbarkeit prüfen…',
  'Performance wird gemessen…',
  'Rechtliche Anforderungen prüfen…',
  'Screenshot wird erstellt…',
  'KI-Analyse läuft…',
  'Fast fertig…',
];

export function useAudit({
  leadId,
  websiteUrl,
  companyName    = '',
  city           = '',
  trade          = '',
  headers        = {},
  autoStart      = false,   // true → startet sofort beim Mount wenn kein Ergebnis
  existingResult = null,    // bereits geladenes Audit-Ergebnis
}) {
  const [phase,    setPhase]    = useState(existingResult?.total_score > 0 ? 'done' : 'idle');
  const [result,   setResult]   = useState(existingResult || null);
  const [progress, setProgress] = useState('');
  const [error,    setError]    = useState('');

  const pollRef  = useRef(null);
  const msgRef   = useRef(null);
  const abortRef = useRef(false);

  // Cleanup bei Unmount — kein State-Update nach Unmount
  useEffect(() => {
    abortRef.current = false;
    return () => {
      abortRef.current = true;
      if (pollRef.current) clearInterval(pollRef.current);
      if (msgRef.current)  clearInterval(msgRef.current);
    };
  }, []);

  // Wenn existingResult von außen kommt → übernehmen
  useEffect(() => {
    if (existingResult?.total_score > 0) {
      setResult(existingResult);
      setPhase('done');
    }
  }, [existingResult]);

  const start = useCallback(async () => {
    if (!websiteUrl) {
      setError('Keine Website-URL hinterlegt.');
      setPhase('error');
      return;
    }
    if (abortRef.current) return;

    setPhase('running');
    setError('');

    // Fortschritts-Meldungen rotieren
    let msgIdx = 0;
    setProgress(PROGRESS_MSGS[0]);
    msgRef.current = setInterval(() => {
      if (abortRef.current) { clearInterval(msgRef.current); return; }
      msgIdx = (msgIdx + 1) % PROGRESS_MSGS.length;
      setProgress(PROGRESS_MSGS[msgIdx]);
    }, 5000);

    try {
      // ── Audit starten ────────────────────────────────────────────────────
      const startRes = await fetch(`${API_BASE_URL}/api/audit/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...headers },
        body: JSON.stringify({
          website_url:  websiteUrl,
          lead_id:      leadId      || undefined,
          company_name: companyName || '',
          city:         city        || '',
          trade:        trade       || '',
        }),
      });

      const startData = await startRes.json();
      if (!startRes.ok) throw new Error(startData.detail || `HTTP ${startRes.status}`);

      const auditId = startData.audit_id || startData.id;
      if (!auditId) throw new Error('Keine Audit-ID erhalten');

      // ── Polling — IMMER GET /api/audit/{id} ──────────────────────────────
      let attempts = 0;
      await new Promise((resolve, reject) => {
        pollRef.current = setInterval(async () => {
          if (abortRef.current) { clearInterval(pollRef.current); resolve(); return; }

          attempts++;
          if (attempts > MAX_ATTEMPTS) {
            clearInterval(pollRef.current);
            reject(new Error('Zeitüberschreitung (3 Min.) — bitte erneut starten.'));
            return;
          }

          try {
            const pollRes = await fetch(
              `${API_BASE_URL}/api/audit/${auditId}`,
              { headers }
            );
            if (!pollRes.ok) return; // Netzwerk-Hickup → weiter polling

            const data = await pollRes.json();

            if (data.status === 'completed') {
              clearInterval(pollRef.current);
              resolve(data);
            } else if (data.status === 'failed') {
              clearInterval(pollRef.current);
              reject(new Error(data.error_message || 'Audit fehlgeschlagen'));
            }
          } catch { /* Netzwerk-Fehler — weiter versuchen */ }
        }, POLL_INTERVAL);
      }).then(data => {
        if (abortRef.current || !data) return;
        setResult(data);
        setPhase('done');
      });

    } catch (e) {
      if (!abortRef.current) {
        setError(e.message);
        setPhase('error');
      }
    } finally {
      clearInterval(msgRef.current);
      if (!abortRef.current) setProgress('');
    }
  }, [websiteUrl, leadId, companyName, city, trade]); // eslint-disable-line

  // Auto-Start (nach start definition)
  useEffect(() => {
    if (autoStart && phase === 'idle' && !result) {
      start();
    }
  }, [autoStart]); // eslint-disable-line

  const reset = useCallback(() => {
    setPhase('idle');
    setResult(null);
    setError('');
    setProgress('');
  }, []);

  return { phase, result, progress, error, start, reset };
}
