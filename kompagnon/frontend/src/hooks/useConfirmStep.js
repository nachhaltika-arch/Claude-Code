import { useState, useCallback } from 'react';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';

export function useConfirmStep({ projectId, stepId, token, onConfirmed }) {
  const [confirming, setConfirming] = useState(false);

  const confirm = useCallback(async () => {
    if (!projectId || !stepId) return;
    setConfirming(true);
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/projects/${projectId}/confirm-step`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify({ step_id: stepId }),
        }
      );
      if (!res.ok) throw new Error('Speichern fehlgeschlagen');
      if (onConfirmed) onConfirmed();
    } catch (e) {
      toast.error(e.message || 'Fehler');
    } finally {
      setConfirming(false);
    }
  }, [projectId, stepId, token, onConfirmed]); // eslint-disable-line

  return { confirm, confirming };
}
