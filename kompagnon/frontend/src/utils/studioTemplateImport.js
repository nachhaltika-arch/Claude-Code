/**
 * studioTemplateImport.js — v2
 * Priorität: 1) .grapesjs  2) index.html + style.css  3) index.html allein
 */
import JSZip from 'jszip';

function _findFile(files, pred) { return files.find(pred) || null; }

async function _readText(zip, name) {
  if (!name || !zip.files[name]) return '';
  return zip.files[name].async('string');
}

async function _loadAllCss(zip, files) {
  const parts = [];
  // style.css zuerst
  const main = _findFile(files, f => f === 'style.css' || f.endsWith('/style.css'));
  if (main) { const t = await _readText(zip, main); if (t) parts.push(t); }
  // alle anderen .css (max 3)
  for (const f of files.filter(f => f.endsWith('.css') && f !== main).slice(0, 3)) {
    const t = await _readText(zip, f); if (t) parts.push(t);
  }
  return parts.join('\n\n');
}

function _fontLinks(css) {
  const links = [];
  const re = /@import\s+url\(['"]?(https:\/\/fonts\.googleapis\.com[^'")\s]+)/g;
  let m; while ((m = re.exec(css)) !== null) links.push(m[1]);
  return links;
}

export async function parseTemplateFile(file) {
  const ext = file.name.split('.').pop().toLowerCase();

  // .grapesjs direkt
  if (ext === 'grapesjs') {
    try {
      return { success: true, source: 'grapesjs', project: JSON.parse(await file.text()), css: '', extraCss: '', fontUrls: [] };
    } catch (e) { return { success: false, error: `Ungültige .grapesjs Datei: ${e.message}` }; }
  }

  if (ext !== 'zip') return { success: false, error: `Format .${ext} nicht unterstützt` };

  let zip;
  try { zip = await JSZip.loadAsync(file); }
  catch (e) { return { success: false, error: `ZIP Fehler: ${e.message}` }; }

  const files = Object.keys(zip.files).filter(f => !zip.files[f].dir);

  // ── Priorität 1: .grapesjs in ZIP ────────────────────────────────────────
  const gjsFile = _findFile(files, f => f.endsWith('.grapesjs'));
  if (gjsFile) {
    try {
      const project  = JSON.parse(await _readText(zip, gjsFile));
      const extraCss = await _loadAllCss(zip, files);
      return { success: true, source: 'zip-grapesjs', project, css: '', extraCss, fontUrls: _fontLinks(extraCss) };
    } catch (e) { console.warn('grapesjs parse failed, fallback:', e); }
  }

  // ── Priorität 2: index.html + style.css ──────────────────────────────────
  const htmlFile = _findFile(files, f => f === 'index.html' || f.endsWith('/index.html'));
  if (!htmlFile) return { success: false, error: 'Keine index.html oder .grapesjs gefunden' };

  const htmlText = await _readText(zip, htmlFile);
  const doc      = new DOMParser().parseFromString(htmlText, 'text/html');
  const bodyHtml = doc.body?.innerHTML || htmlText;
  const headCss  = Array.from(doc.querySelectorAll('head style')).map(s => s.textContent).join('\n');
  const headFonts= Array.from(doc.querySelectorAll('head link[rel=stylesheet]'))
                     .map(l => l.href).filter(h => h.includes('fonts.googleapis'));

  const extCss   = await _loadAllCss(zip, files);
  const combined = [extCss, headCss].filter(Boolean).join('\n\n');

  return {
    success: true, source: 'zip-html',
    project: { pages: [{ name: 'index', component: bodyHtml }] },
    css: combined, extraCss: '', fontUrls: [...headFonts, ..._fontLinks(combined)],
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
        l.rel = 'stylesheet'; l.href = url;
        head.appendChild(l);
      });
    } catch (e) { console.warn('Font inject:', e); }
  };

  // Pfad A: loadProjectData (.grapesjs)
  if (['zip-grapesjs','grapesjs'].includes(parsed.source) && editor.loadProjectData) {
    try {
      editor.loadProjectData(parsed.project);
      // style.css nach dem Laden anhängen
      if (parsed.extraCss) {
        setTimeout(() => {
          try { editor.setStyle((editor.getCss?.() || '') + '\n\n' + parsed.extraCss); }
          catch(e) { console.warn('extraCss:', e); }
        }, 500);
      }
      setTimeout(injectFonts, 400);
      return;
    } catch (e) { console.warn('loadProjectData failed:', e); }
  }

  // Pfad B: HTML + CSS
  const page = parsed.project.pages?.[0];
  if (page?.component !== undefined) editor.setComponents?.(page.component || '');
  const css = parsed.css || page?.styles || '';
  if (css) setTimeout(() => { try { editor.setStyle(css); } catch(e){} }, 200);
  setTimeout(injectFonts, 400);
}
