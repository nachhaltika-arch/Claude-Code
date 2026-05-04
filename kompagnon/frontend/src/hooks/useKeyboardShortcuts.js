import { useEffect } from 'react';

/**
 * Registriert globale Keyboard-Shortcuts.
 * handlers: Array von { key, meta?, shift?, action, allowInInput? }
 */
export function useKeyboardShortcuts(handlers) {
  useEffect(() => {
    const onKeyDown = (e) => {
      const tag = document.activeElement?.tagName?.toLowerCase();
      const isInput = ['input', 'textarea', 'select'].includes(tag)
        || document.activeElement?.isContentEditable;

      for (const h of handlers) {
        const keyMatch   = e.key === h.key;
        const metaMatch  = h.meta ? (e.metaKey || e.ctrlKey) : !(e.metaKey || e.ctrlKey);
        const shiftMatch = h.shift ? e.shiftKey : !e.shiftKey;
        const skipInput  = !h.allowInInput && isInput;

        if (keyMatch && metaMatch && shiftMatch && !skipInput) {
          e.preventDefault();
          h.action(e);
          return;
        }
      }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [handlers]);
}

/**
 * Schließt bei Esc — für Modals.
 */
export function useEscapeKey(onClose, enabled = true) {
  useEffect(() => {
    if (!enabled) return;
    const onKeyDown = (e) => {
      if (e.key === 'Escape') { e.preventDefault(); onClose(); }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [onClose, enabled]);
}
