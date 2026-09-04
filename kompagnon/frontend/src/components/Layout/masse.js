/**
 * Die zwei festen Hoehen der Mobilansicht (L-25, 30.08.2026).
 *
 * **Eigene Datei, weil sie beide Richtungen bedienen.** `AppLayout` rechnet
 * mit ihnen den Inhaltsbereich aus, `BottomNav` positioniert sich danach.
 * Stuenden sie in einer der beiden, muesste die andere ihre Nachbarin
 * importieren — und ein Ringschluss waere nur eine Frage der Zeit.
 */
export const MOBILE_HEADER_H = 52;   // px — fixed top bar
export const MOBILE_NAV_H    = 64;   // px — fixed bottom nav (ohne safe-area)
