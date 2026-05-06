// ==UserScript==
// @name         KAS — Relume Bulk Downloader
// @namespace    kas-kompagnon
// @version      1.0.0
// @description  Walks Relume's component library, scrapes each HTML-Tab snippet, downloads as files. Used to bulk-import sections into KAS Kompagnon's component library.
// @author       KAS Kompagnon
// @match        https://www.relume.io/*
// @match        https://relume.io/*
// @grant        GM_download
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_deleteValue
// @run-at       document-idle
// ==/UserScript==

/* eslint-disable no-undef */
(function () {
  'use strict';

  // ── Config ────────────────────────────────────────────────────────────────

  const STORAGE = {
    queue:  'kas_relume_queue',    // URLs noch abzuarbeiten
    done:   'kas_relume_done',     // erfolgreich runtergeladene slugs
    failed: 'kas_relume_failed',   // Fehlgeschlagene mit reason
    running: 'kas_relume_running', // bool: Walker laeuft
  };

  const NAV_DELAY_MS  = 3000; // Pause zwischen 2 Component-Pages (anti-bot, react-render)
  const TAB_DELAY_MS  = 1500; // Wartezeit nach HTML-Tab-Klick bis Code da ist
  const MAX_WAIT_MS   = 10000; // Max-Wait fuer Code-Block bis zum Aufgeben

  // ── State helpers (persistent ueber GM-Storage) ───────────────────────────

  const getQueue  = () => GM_getValue(STORAGE.queue, []);
  const getDone   = () => GM_getValue(STORAGE.done, []);
  const getFailed = () => GM_getValue(STORAGE.failed, []);
  const isRunning = () => GM_getValue(STORAGE.running, false);

  const setQueue   = (q) => GM_setValue(STORAGE.queue, q);
  const setDone    = (d) => GM_setValue(STORAGE.done, d);
  const setFailed  = (f) => GM_setValue(STORAGE.failed, f);
  const setRunning = (b) => GM_setValue(STORAGE.running, b);

  const resetAll = () => {
    GM_deleteValue(STORAGE.queue);
    GM_deleteValue(STORAGE.done);
    GM_deleteValue(STORAGE.failed);
    GM_deleteValue(STORAGE.running);
    renderUI();
  };

  // ── DOM helpers ───────────────────────────────────────────────────────────

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  // Wartet bis `selector` einen passenden Knoten hat ODER timeout. Returns null bei timeout.
  function waitFor(selector, timeout = MAX_WAIT_MS) {
    return new Promise((resolve) => {
      const found = document.querySelector(selector);
      if (found) return resolve(found);
      const obs = new MutationObserver(() => {
        const el = document.querySelector(selector);
        if (el) { obs.disconnect(); resolve(el); }
      });
      obs.observe(document.body, { childList: true, subtree: true });
      setTimeout(() => { obs.disconnect(); resolve(null); }, timeout);
    });
  }

  function findHtmlTab() {
    // Sucht einen Tab/Button mit Text "HTML". Robust gegenueber DOM-Aenderungen.
    const candidates = document.querySelectorAll('button, [role="tab"], a');
    for (const c of candidates) {
      const t = (c.textContent || '').trim();
      if (t === 'HTML') return c;
    }
    return null;
  }

  function isComponentPage() {
    return /\/react-components\//.test(location.pathname);
  }

  function currentSlug() {
    return (location.pathname.split('/').pop() || '').trim();
  }

  function urlForSlug(slug) {
    return `https://www.relume.io/react-components/${slug}`;
  }

  // Filename-Schema: relume-{category}-{slug}.html — Category aus dem
  // Code-Block-Attribut "componenthtmlslug" (z.B. "navbars/navbar3_component").
  // Fallback ohne Category: relume-{slug}.html
  function buildFilename(codeEl, slug) {
    const attr = (codeEl?.getAttribute('componenthtmlslug') || '').trim();
    if (attr.includes('/')) {
      const cat = attr.split('/')[0].toLowerCase();
      return `relume-${cat}-${slug}.html`;
    }
    return `relume-${slug}.html`;
  }

  // ── Sammeln: Links auf der aktuellen Seite zur Queue hinzufuegen ──────────

  function collectLinksOnPage() {
    const links = document.querySelectorAll('a[href*="/react-components/"]');
    const slugs = new Set();
    links.forEach((a) => {
      try {
        const u = new URL(a.href, location.origin);
        if (!/\/react-components\//.test(u.pathname)) return;
        const slug = u.pathname.split('/').pop();
        if (slug) slugs.add(slug);
      } catch (_) { /* ignore */ }
    });
    return [...slugs].map(urlForSlug);
  }

  function addCollectedToQueue() {
    const found = collectLinksOnPage();
    const queue = getQueue();
    const done = new Set(getDone());
    const existing = new Set(queue);
    let added = 0;
    found.forEach((url) => {
      const slug = url.split('/').pop();
      if (done.has(slug)) return;
      if (existing.has(url)) return;
      queue.push(url);
      added++;
    });
    setQueue(queue);
    renderUI();
    alert(`+${added} URLs zur Queue hinzugefuegt (gesamt: ${queue.length}).`);
  }

  // ── Walker: aktuelle Page scrapen + naechste URL aufrufen ─────────────────

  async function scrapeCurrent() {
    const slug = currentSlug();

    // HTML-Tab aktivieren (Default ist React)
    const htmlTab = findHtmlTab();
    if (htmlTab) {
      htmlTab.click();
      await sleep(TAB_DELAY_MS);
    }

    // Auf Code-Block warten
    const codeEl = await waitFor('code[componenthtmlslug]', MAX_WAIT_MS);
    if (!codeEl) {
      const failed = getFailed();
      failed.push({ slug, reason: 'no code-block after tab click', t: Date.now() });
      setFailed(failed);
      return false;
    }

    const html = codeEl.textContent || '';
    if (html.length < 50) {
      const failed = getFailed();
      failed.push({ slug, reason: `code too short (${html.length} chars)`, t: Date.now() });
      setFailed(failed);
      return false;
    }

    const filename = buildFilename(codeEl, slug);
    const blob = new Blob([html], { type: 'text/html' });
    const dataUrl = URL.createObjectURL(blob);

    return new Promise((resolve) => {
      GM_download({
        url: dataUrl,
        name: filename,
        saveAs: false,
        onload: () => {
          URL.revokeObjectURL(dataUrl);
          const done = getDone();
          if (!done.includes(slug)) done.push(slug);
          setDone(done);
          resolve(true);
        },
        onerror: (e) => {
          URL.revokeObjectURL(dataUrl);
          const failed = getFailed();
          failed.push({ slug, reason: `download failed: ${JSON.stringify(e)}`, t: Date.now() });
          setFailed(failed);
          resolve(false);
        },
        ontimeout: () => {
          URL.revokeObjectURL(dataUrl);
          const failed = getFailed();
          failed.push({ slug, reason: 'download timeout', t: Date.now() });
          setFailed(failed);
          resolve(false);
        },
      });
    });
  }

  async function walkerStep() {
    if (!isRunning()) return;
    if (!isComponentPage()) return; // nicht auf Component-Page → nichts tun

    const queue = getQueue();
    const slug = currentSlug();
    // Scrape laufende Page (auch wenn nicht in Queue — User hat manuell navigiert)
    await scrapeCurrent();

    // URL aus Queue entfernen, falls drin
    const remaining = queue.filter((u) => u.split('/').pop() !== slug);
    setQueue(remaining);
    renderUI();

    // Naechste URL?
    if (remaining.length === 0) {
      setRunning(false);
      renderUI();
      alert(`Walker fertig. Done: ${getDone().length}, Failed: ${getFailed().length}.`);
      return;
    }

    await sleep(NAV_DELAY_MS);
    if (isRunning()) {
      location.href = remaining[0];
    }
  }

  // ── Floating UI ───────────────────────────────────────────────────────────

  let panel = null;

  function makePanel() {
    panel = document.createElement('div');
    panel.id = 'kas-relume-walker';
    panel.style.cssText = [
      'position:fixed','bottom:16px','right:16px','z-index:2147483647',
      'background:#0f172a','color:#fff','padding:12px 14px','border-radius:10px',
      'font:12px/1.4 system-ui,sans-serif','box-shadow:0 8px 24px rgba(0,0,0,.3)',
      'min-width:240px','max-width:320px',
    ].join(';');
    document.body.appendChild(panel);
  }

  function renderUI() {
    if (!panel) makePanel();
    const queue = getQueue();
    const done = getDone();
    const failed = getFailed();
    const running = isRunning();
    const onComp = isComponentPage();

    panel.innerHTML = `
      <div style="font-weight:700;letter-spacing:.04em;text-transform:uppercase;font-size:11px;margin-bottom:8px;color:#fbbf24">
        KAS · Relume Walker
      </div>
      <div style="display:flex;gap:6px;margin-bottom:8px;font-size:11px">
        <span>Queue: <b>${queue.length}</b></span>
        <span>·</span>
        <span>Done: <b style="color:#86efac">${done.length}</b></span>
        <span>·</span>
        <span>Fail: <b style="color:#fca5a5">${failed.length}</b></span>
      </div>
      <div style="font-size:10px;color:#94a3b8;margin-bottom:10px">
        ${running ? '⏳ running' : '⏸ paused'} · ${onComp ? 'on component page' : 'on overview page'}
      </div>
      <div style="display:flex;flex-direction:column;gap:4px">
        ${onComp ? `
          <button data-act="step"  style="${btn('#3b82f6')}">📥 Aktuelle Seite scrapen</button>
        ` : `
          <button data-act="add"   style="${btn('#3b82f6')}">➕ Sichtbare Links zur Queue</button>
        `}
        <button data-act="start" ${queue.length === 0 ? 'disabled' : ''} style="${btn('#10b981', queue.length === 0)}">▶ Walker starten</button>
        <button data-act="stop"  ${!running ? 'disabled' : ''} style="${btn('#ef4444', !running)}">⏸ Stop</button>
        <button data-act="show-failed" ${failed.length === 0 ? 'disabled' : ''} style="${btn('#f59e0b', failed.length === 0)}">📋 Failed anzeigen</button>
        <button data-act="reset" style="${btn('#475569')}">🗑 Reset alles</button>
      </div>
    `;
    panel.querySelectorAll('button').forEach((b) => {
      b.addEventListener('click', () => handleAction(b.dataset.act));
    });
  }

  function btn(color, disabled = false) {
    return [
      `background:${disabled ? '#334155' : color}`,
      'color:#fff','border:none','padding:6px 10px','border-radius:6px',
      'font:600 11px system-ui,sans-serif',
      `cursor:${disabled ? 'not-allowed' : 'pointer'}`,
      `opacity:${disabled ? 0.5 : 1}`,'text-align:left',
    ].join(';');
  }

  async function handleAction(act) {
    switch (act) {
      case 'add':
        addCollectedToQueue();
        break;
      case 'step':
        await scrapeCurrent();
        renderUI();
        alert(`Scrape fertig. Slug: ${currentSlug()}. Down: ${getDone().length}, Failed: ${getFailed().length}.`);
        break;
      case 'start':
        if (getQueue().length === 0) return alert('Queue leer. Erst Links sammeln.');
        setRunning(true);
        renderUI();
        // Falls schon auf Component-Page: direkt loslegen. Sonst: zur ersten URL navigieren.
        if (isComponentPage()) {
          walkerStep();
        } else {
          location.href = getQueue()[0];
        }
        break;
      case 'stop':
        setRunning(false);
        renderUI();
        break;
      case 'show-failed': {
        const f = getFailed();
        const txt = f.map((e) => `${e.slug} — ${e.reason}`).join('\n');
        prompt('Failed slugs (kopierbar):', txt);
        break;
      }
      case 'reset':
        if (confirm('Wirklich alles zuruecksetzen? Queue, Done, Failed werden geloescht.')) resetAll();
        break;
    }
  }

  // ── Boot ──────────────────────────────────────────────────────────────────

  function boot() {
    renderUI();
    // Auto-Walk: wenn running aktiv ist und wir auf einer Component-Page sind
    if (isRunning() && isComponentPage()) {
      // Kleine Verzoegerung damit React den Tab-Content fertig rendert
      setTimeout(walkerStep, 1500);
    }
  }

  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    boot();
  } else {
    window.addEventListener('DOMContentLoaded', boot);
  }
})();
