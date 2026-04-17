/**
 * studioTemplateImport.js — v2
 * Prioritaet: 1) .grapesjs  2) index.html + style.css  3) index.html allein
 *
 * GrapesJS Studio exportiert ZIPs mit 3 Dateien:
 *   - index.html              (HTML-Inhalt)
 *   - style.css               (alle Styles, oft 30KB+)
 *   - <slug>.grapesjs         (vollstaendige Projektdaten als JSON)
 *
 * Alle drei werden jetzt korrekt geladen. Font-Links werden in den
 * Canvas injiziert, damit Google Fonts sofort sichtbar sind.
 */
import JSZip from 'jszip';

function _findFile(files, pred) { return files.find(pred) || null; }

async function _readText(zip, name) {
  if (!name || !zip.files[name]) return '';
  return zip.files[name].async('string');
}

async function _loadAllCss(zip, files) {
  const parts = [];
  const main = _findFile(files, f => f === 'style.css' || f.endsWith('/style.css'));
  if (main) { const t = await _readText(zip, main); if (t) parts.push(t); }
  for (const f of files.filter(x => x.endsWith('.css') && x !== main).slice(0, 3)) {
    const t = await _readText(zip, f); if (t) parts.push(t);
  }
  return parts.join('\n\n');
}

function _fontLinks(css) {
  const links = [];
  const re = /@import\s+url\(['"]?(https:\/\/fonts\.googleapis\.com[^'")\s]+)/g;
  let m;
  while ((m = re.exec(css)) !== null) links.push(m[1]);
  return links;
}

export async function parseTemplateFile(file) {
  if (!file) return { success: false, error: 'Keine Datei ausgewaehlt' };
  const ext = (file.name.split('.').pop() || '').toLowerCase();

  if (ext === 'grapesjs') {
    try {
      return {
        success: true, source: 'grapesjs',
        project: JSON.parse(await file.text()),
        css: '', extraCss: '', fontUrls: [],
      };
    } catch (e) {
      return { success: false, error: `Ungueltige .grapesjs Datei: ${e.message}` };
    }
  }

  if (ext !== 'zip') return { success: false, error: `Format .${ext} nicht unterstuetzt (nur .zip / .grapesjs)` };

  let zip;
  try { zip = await JSZip.loadAsync(file); }
  catch (e) { return { success: false, error: `ZIP Fehler: ${e.message}` }; }

  const files = Object.keys(zip.files).filter(f => !zip.files[f].dir);

  // Prioritaet 1: .grapesjs in ZIP
  const gjsFile = _findFile(files, f => f.endsWith('.grapesjs') || f.endsWith('grapesjs.json'));
  if (gjsFile) {
    try {
      const project  = JSON.parse(await _readText(zip, gjsFile));
      const extraCss = await _loadAllCss(zip, files);
      return {
        success: true, source: 'zip-grapesjs',
        project, css: '', extraCss,
        fontUrls: _fontLinks(extraCss),
      };
    } catch (e) {
      console.warn('studioTemplateImport: .grapesjs parse failed, fallback:', e);
    }
  }

  // Prioritaet 2: index.html + style.css
  const htmlFile = _findFile(files, f => f === 'index.html' || f.endsWith('/index.html'));
  if (!htmlFile) return { success: false, error: 'Keine index.html oder .grapesjs gefunden' };

  const htmlText = await _readText(zip, htmlFile);
  const doc      = new DOMParser().parseFromString(htmlText, 'text/html');
  const bodyHtml = doc.body?.innerHTML || htmlText;
  const headCss  = Array.from(doc.querySelectorAll('head style'))
    .map(s => s.textContent || '')
    .filter(Boolean)
    .join('\n\n');
  const headFonts = Array.from(doc.querySelectorAll('head link[rel=stylesheet]'))
    .map(l => l.href)
    .filter(h => h && h.includes('fonts.googleapis'));

  const extCss   = await _loadAllCss(zip, files);
  const combined = [extCss, headCss].filter(Boolean).join('\n\n');

  return {
    success: true, source: 'zip-html',
    project: { pages: [{ name: 'index', component: bodyHtml }] },
    css: combined, extraCss: '',
    fontUrls: [...headFonts, ..._fontLinks(combined)],
  };
}

export function applyTemplateToEditor(editor, parsed) {
  if (!editor || !parsed?.project) return;

  const injectFonts = () => {
    try {
      const head = editor.Canvas?.getDocument?.()?.head;
      if (!head || !parsed.fontUrls?.length) return;
      parsed.fontUrls.forEach(url => {
        if (head.querySelector(`link[href="${url}"]`)) return;
        const l = document.createElement('link');
        l.rel = 'stylesheet';
        l.href = url;
        head.appendChild(l);
      });
    } catch (e) { console.warn('Font inject:', e); }
  };

  // Pfad A: loadProjectData (.grapesjs)
  if (['zip-grapesjs', 'grapesjs'].includes(parsed.source) && typeof editor.loadProjectData === 'function') {
    try {
      editor.loadProjectData(parsed.project);
      if (parsed.extraCss) {
        setTimeout(() => {
          try {
            const existing = (typeof editor.getCss === 'function' ? editor.getCss() : '') || '';
            editor.setStyle(existing + '\n\n' + parsed.extraCss);
          } catch (e) { console.warn('extraCss append:', e); }
        }, 500);
      }
      setTimeout(injectFonts, 400);
      return;
    } catch (e) { console.warn('loadProjectData failed, fallback:', e); }
  }

  // Pfad B: HTML + CSS
  const page = parsed.project.pages?.[0];
  if (page?.component !== undefined && typeof editor.setComponents === 'function') {
    editor.setComponents(page.component || '');
  }
  const css = parsed.css || page?.styles || parsed.extraCss || '';
  if (css && typeof editor.setStyle === 'function') {
    setTimeout(() => { try { editor.setStyle(css); } catch (e) { console.warn('setStyle:', e); } }, 200);
  }
  setTimeout(injectFonts, 400);
}
