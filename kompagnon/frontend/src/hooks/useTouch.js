import { useRef, useEffect } from 'react';

/**
 * Pull-to-Refresh für einen Scroll-Container.
 * Steuert den PullIndicator imperativ via data-Attribute (kein Re-render pro Pixel).
 */
export function usePullToRefresh(onRefresh, { threshold = 72, disabled = false } = {}) {
  const containerRef = useRef(null);
  const startY = useRef(0);
  const isPulling = useRef(false);
  const pullDist = useRef(0);

  useEffect(() => {
    const el = containerRef.current;
    if (!el || disabled) return;

    const updateIndicator = (progress, refreshing) => {
      const ind = el.querySelector('[data-ptr-indicator]');
      if (!ind) return;
      ind.style.transform = `translateX(-50%) translateY(${Math.min(progress * threshold, threshold)}px)`;
      ind.style.opacity = String(Math.min(progress * 2, 1));
      const spinner = ind.querySelector('[data-ptr-spinner]');
      if (spinner) spinner.style.transform = `rotate(${progress * 360}deg)`;
      ind.setAttribute('data-refreshing', refreshing ? '1' : '0');
    };

    const onTouchStart = (e) => {
      if (el.scrollTop > 0) return;
      startY.current = e.touches[0].clientY;
      isPulling.current = true;
    };

    const onTouchMove = (e) => {
      if (!isPulling.current) return;
      const dist = e.touches[0].clientY - startY.current;
      if (dist <= 0) { pullDist.current = 0; return; }
      pullDist.current = dist > 48 ? 48 + (dist - 48) * 0.3 : dist;
      updateIndicator(pullDist.current / threshold, false);
      if (dist > 8 && el.scrollTop === 0) e.preventDefault();
    };

    const onTouchEnd = async () => {
      if (!isPulling.current) return;
      isPulling.current = false;
      if (pullDist.current >= threshold) {
        updateIndicator(1, true);
        try { await onRefresh(); } catch { /* silent */ }
      }
      updateIndicator(0, false);
      pullDist.current = 0;
    };

    el.addEventListener('touchstart', onTouchStart, { passive: true });
    el.addEventListener('touchmove', onTouchMove, { passive: false });
    el.addEventListener('touchend', onTouchEnd, { passive: true });
    return () => {
      el.removeEventListener('touchstart', onTouchStart);
      el.removeEventListener('touchmove', onTouchMove);
      el.removeEventListener('touchend', onTouchEnd);
    };
  }, [onRefresh, threshold, disabled]);

  return { containerRef };
}

/**
 * Horizontales Swipe zwischen Tabs/Seiten.
 */
export function useSwipeNavigation({ onSwipeLeft, onSwipeRight, threshold = 60, disabled = false } = {}) {
  const ref = useRef(null);
  const startX = useRef(0);
  const startY = useRef(0);

  useEffect(() => {
    const el = ref.current;
    if (!el || disabled) return;

    const onTouchStart = (e) => {
      startX.current = e.touches[0].clientX;
      startY.current = e.touches[0].clientY;
    };

    const onTouchEnd = (e) => {
      const dx = e.changedTouches[0].clientX - startX.current;
      const dy = e.changedTouches[0].clientY - startY.current;
      if (Math.abs(dx) < threshold || Math.abs(dy) > Math.abs(dx)) return;
      if (dx < 0) onSwipeLeft?.();
      else onSwipeRight?.();
    };

    el.addEventListener('touchstart', onTouchStart, { passive: true });
    el.addEventListener('touchend', onTouchEnd, { passive: true });
    return () => {
      el.removeEventListener('touchstart', onTouchStart);
      el.removeEventListener('touchend', onTouchEnd);
    };
  }, [onSwipeLeft, onSwipeRight, threshold, disabled]);

  return ref;
}
