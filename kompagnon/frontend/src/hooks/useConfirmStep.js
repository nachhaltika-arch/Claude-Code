import { useCallback, useState } from 'react';

const API = import.meta.env.VITE_API_URL || '';

export function useConfirmStep({ projectId, token }) {
  const [loading, setLoading] = useState(false);

  const confirmStep = useCallback(async (stepId, onConfirmed) => {
    if (!projectId || !stepId) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/projects/${projectId}/confirm-step`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ step_id: stepId }),
      });
      if (res.ok && onConfirmed) onConfirmed(stepId);
    } catch (e) {
      console.error('confirm-step error', e);
    } finally {
      setLoading(false);
    }
  }, [projectId, token]);

  return { confirmStep, loading };
}
