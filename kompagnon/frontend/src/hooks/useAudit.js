import { useState, useEffect, useRef, useCallback } from 'react';
import API_BASE_URL from '../config';

const MAX_ATTEMPTS  = 45;
const POLL_INTERVAL = 4000;

const PROGRESS_MSGS = [
  'Website wird aufgerufen…',
  'SSL und Erreichbarkeit pruefen…',
  'Performance wird gemessen…',
  'Rechtliche Anforderungen pruefen…',
  'Screenshot wird erstellt…',
  'KI-Analyse laeuft…',
  'Fast fertig…',
];

export function useAudit({
  leadId,
  websiteUrl,
  companyName = '',
  city        = '',
  trade       = '',
  headers     = {},
  autoStart   = false,
  existingResult = null,
}) {
  const [phase, setPhase]       = useState(existingResult?.total_score > 0 ? 'done' : 'idle');
  const [result, setResult]     = useState(existingResult || null);
  const [progress, setProgress] = useState('');
  const [error, setError]       = useState('');

  const pollRef  = useRef(null);
  const msgRef   = useRef(null);
  const abortRef = useRef(false);

  useEffect(() => {
    abortRef.current = false;
    return () => {
      abortRef.current = true;
      if (pollRef.current) clearInterval(pollRef.current);
      if (msgRef.current)  clearInterval(msgRef.current);
    };
  }, []);

  useEffect(() => {
    if (existingResult?.total_score > 0) {
      setResult(existingResult);
      setPhase('done');
    }
  }, [existingResult]);

  useEffect(() => {
    if (autoStart && phase === 'idle' && !result) start();
  }, [autoStart]); // eslint-disable-line

  const start = useCallback(async () => {
    if (!websiteUrl) { setError('Keine Website-URL hinterlegt.'); setPhase('error'); return; }
    if (abortRef.current) return;

    setPhase('running');
    setError('');

    let msgIdx = 0;
    setProgress(PROGRESS_MSGS[0]);
    msgRef.current = setInterval(() => {
      if (abortRef.current) { clearInterval(msgRef.current); return; }
      msgIdx = (msgIdx + 1) % PROGRESS_MSGS.length;
      setProgress(PROGRESS_MSGS[msgIdx]);
    }, 5000);

    try {
      const startRes = await fetch(`${API_BASE_URL}/api/audit/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...headers },
        body: JSON.stringify({
          website_url:  websiteUrl,
          lead_id:      leadId || undefined,
          company_name: companyName || '',
          city:         city || '',
          trade:        trade || '',
        }),
      });

      const startData = await startRes.json();
      if (!startRes.ok) throw new Error(startData.detail || `HTTP ${startRes.status}`);

      const auditId = startData.audit_id || startData.id;
      if (!auditId) throw new Error('Keine Audit-ID erhalten');

      let attempts = 0;
      await new Promise((resolve, reject) => {
        pollRef.current = setInterval(async () => {
          if (abortRef.current) { clearInterval(pollRef.current); resolve(); return; }
          attempts++;
          if (attempts > MAX_ATTEMPTS) {
            clearInterval(pollRef.current);
            reject(new Error('Zeitueberschreitung (3 Min.) — bitte erneut starten.'));
            return;
          }
          try {
            const pollRes = await fetch(`${API_BASE_URL}/api/audit/${auditId}`, { headers });
            if (!pollRes.ok) return;
            const data = await pollRes.json();
            if (data.status === 'completed') { clearInterval(pollRef.current); resolve(data); }
            else if (data.status === 'failed') { clearInterval(pollRef.current); reject(new Error(data.error_message || 'Audit fehlgeschlagen')); }
          } catch { /* weiter */ }
        }, POLL_INTERVAL);
      }).then(data => {
        if (abortRef.current || !data) return;
        setResult(data);
        setPhase('done');
      });
    } catch (e) {
      if (!abortRef.current) { setError(e.message); setPhase('error'); }
    } finally {
      clearInterval(msgRef.current);
      if (!abortRef.current) setProgress('');
    }
  }, [websiteUrl, leadId, companyName, city, trade]); // eslint-disable-line

  const reset = useCallback(() => {
    setPhase('idle'); setResult(null); setError(''); setProgress('');
  }, []);

  return { phase, result, progress, error, start, reset };
}
