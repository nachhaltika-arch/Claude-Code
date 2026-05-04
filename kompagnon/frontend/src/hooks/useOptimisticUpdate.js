import { useCallback } from 'react';
import toast from 'react-hot-toast';

/**
 * Optimistic Update: State sofort ändern, API im Hintergrund, Rollback bei Fehler.
 */
export function useOptimisticUpdate(setState) {
  return useCallback(async ({ update, apiFn, rollbackValue, errorMsg }) => {
    setState(prev => {
      if (Array.isArray(prev)) {
        return prev.map(item => item.id === update.id ? { ...item, ...update } : item);
      }
      return { ...prev, ...update };
    });
    try {
      const res = await apiFn();
      if (res && !res.ok) throw new Error(`HTTP ${res.status}`);
    } catch {
      if (rollbackValue !== undefined) setState(rollbackValue);
      toast.error(errorMsg || 'Aktion fehlgeschlagen — bitte erneut versuchen');
    }
  }, [setState]);
}
