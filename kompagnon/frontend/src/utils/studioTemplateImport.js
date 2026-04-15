// Parses a `.zip` or `.grapesjs` file into a Studio SDK project payload.
// Returns { success, project?, css?, extraCss?, source?, error? } in all cases — no throws.
//
// Wichtig: GrapesJS Studio exportiert ZIPs mit DREI Dateien:
//   - index.html              (HTML-Inhalt)
//   - style.css               (alle Styles, oft 30 KB+ — kritisch fuer Layout)
//   - <slug>.grapesjs         (vollstaendige Projektdaten als JSON)
//
// Frueher hat der Parser im .grapesjs-Pfad das style.css ignoriert. Resultat:
// das Projekt-Modell wurde geladen, aber externe Asset-URLs / Font-Imports /
// Custom-Rules aus style.css fehlten. Templates erschienen "zerschossen".
//
// Neue Logik:
//   1. Bei .grapesjs (im ZIP oder standalone) wird die Projektdatei geladen.
//   2. Falls im ZIP zusaetzlich eine style.css existiert, wird sie als
//      `extraCss` mitgegeben. applyTemplateToEditor haengt sie an das von
//      loadProjectData gesetzte CSS an, statt es zu ueberschreiben.
//   3. Im HTML+CSS-Fallback-Pfad wird sowohl style.css als auch der Inhalt
//      aller <style>-Tags im <head> zusammengefuehrt — DOMParser statt
//      Regex fuer robustes Parsing.

import JSZip from 'jszip';

function _findFile(files, predicate) {
  return files.find(predicate);
}

async function _loadCssFromZip(zip, files) {
  const cssFile = _findFile(
    files,
    f => (f === 'style.css' || f.endsWith('/style.css')) && !zip.files[f].dir,
  );
  return cssFile ? await zip.files[cssFile].async('string') : '';
}

export async function parseTemplateFile(file) {
  if (!file) return { success: false, error: 'Keine Datei ausgewählt' };

  const ext = (file.name.split('.').pop() || '').toLowerCase();

  // ── Standalone .grapesjs Datei ───────────────────────────────────────────
  if (ext === 'grapesjs') {
    const text = await file.text();
    try {
      return {
        success:  true,
        project:  JSON.parse(text),
        extraCss: '',
        source:   'grapesjs',
      };
    } catch {
      return { success: false, error: 'Ungültige .grapesjs-Datei' };
    }
  }

  // ── ZIP (GrapesJS Studio Export) ─────────────────────────────────────────
  if (ext === 'zip') {
    let zip;
    try {
      zip = await JSZip.loadAsync(file);
    } catch (e) {
      return { success: false, error: `ZIP-Fehler: ${e.message}` };
    }

    const files = Object.keys(zip.files);

    // Priorität 1: .grapesjs Projektdatei → vollstaendiges Projekt-Modell
    const gjsFile = _findFile(
      files,
      f => (f.endsWith('.grapesjs') || f.endsWith('grapesjs.json')) && !zip.files[f].dir,
    );

    if (gjsFile) {
      try {
        const text = await zip.files[gjsFile].async('string');
        const project = JSON.parse(text);
        // Auch style.css aus dem ZIP mitnehmen — wird beim Apply
        // an das Projekt-CSS angehaengt, nicht ueberschrieben.
        const extraCss = await _loadCssFromZip(zip, files);
        return {
          success:  true,
          project,
          extraCss,
          source:   'zip-grapesjs',
        };
      } catch (e) {
        // .grapesjs nicht parsbar → fallthrough zum HTML-Pfad
        console.warn('studioTemplateImport: .grapesjs nicht parsbar, fallback auf HTML', e);
      }
    }

    // Priorität 2: index.html (+ optional style.css + Inline-<style>)
    const htmlFile = _findFile(
      files,
      f => (f === 'index.html' || f.endsWith('/index.html')) && !zip.files[f].dir,
    );

    if (!htmlFile) {
      return {
        success: false,
        error:   'Keine index.html oder .grapesjs Datei gefunden',
      };
    }

    let bodyHtml = '';
    let headStyles = '';
    try {
      const html = await zip.files[htmlFile].async('string');
      // DOMParser ist robuster als Regex (handhabt verschachtelte <style>,
      // self-closing Tags und Whitespace korrekt).
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, 'text/html');
      bodyHtml = doc.body ? doc.body.innerHTML : html;
      headStyles = Array.from(doc.querySelectorAll('head style'))
        .map(s => s.textContent || '')
        .filter(Boolean)
        .join('\n\n');
    } catch (e) {
      return { success: false, error: `HTML-Parse-Fehler: ${e.message}` };
    }

    const externalCss = await _loadCssFromZip(zip, files);
    const combinedCss = [externalCss, headStyles].filter(Boolean).join('\n\n');

    return {
      success:  true,
      source:   'zip-html',
      project:  { pages: [{ name: 'index', component: bodyHtml }] },
      css:      combinedCss,
      extraCss: '',
    };
  }

  return { success: false, error: `Format .${ext} wird nicht unterstützt (nur .zip / .grapesjs)` };
}

// Applies a parsed project to a live Studio SDK editor instance.
// Uses the editor's project API when available, otherwise falls back to
// setComponents/setStyle.
//
// Wichtig: extraCss wird IMMER zusaetzlich angehaengt (nicht ersetzt).
// Wenn das Projekt-Modell bereits CSS bringt (z.B. aus loadProjectData),
// wird das Zusatz-CSS dahinter konkateniert.
export function applyTemplateToEditor(editor, parsed) {
  if (!editor || !parsed?.project) return;

  // Preferred: load the entire project payload (preserves pages, assets, styles).
  if (typeof editor.loadProjectData === 'function') {
    try {
      editor.loadProjectData(parsed.project);

      // Extra-CSS aus style.css an existing CSS anhaengen, nicht ueberschreiben.
      if (parsed.extraCss && typeof editor.setStyle === 'function') {
        const existing = (typeof editor.getCss === 'function' ? editor.getCss() : '') || '';
        editor.setStyle(existing + '\n\n' + parsed.extraCss);
      }

      // Im HTML+CSS-Fallback-Pfad kommt das CSS via parsed.css (kombiniert).
      // Hier setzen wir es direkt — das Projekt aus pages/component hat noch
      // kein eigenes CSS, also ist Override hier korrekt.
      if (parsed.css && typeof editor.setStyle === 'function' && !parsed.extraCss) {
        editor.setStyle(parsed.css);
      }
      return;
    } catch {
      /* fall through to component-level fallback */
    }
  }

  // Fallback: push html/css of the first page directly.
  const firstPage = parsed.project.pages?.[0];
  if (firstPage?.component !== undefined && typeof editor.setComponents === 'function') {
    editor.setComponents(firstPage.component || '');
  }

  const cssToApply = parsed.css || firstPage?.styles || parsed.extraCss || '';
  if (cssToApply && typeof editor.setStyle === 'function') {
    editor.setStyle(cssToApply);
  }
}
