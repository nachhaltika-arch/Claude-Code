// Parses a `.zip` or `.grapesjs` file into a Studio SDK project payload.
// Returns { success, project?, css?, error? } in all cases — no throws.

import JSZip from 'jszip';

export async function parseTemplateFile(file) {
  if (!file) return { success: false, error: 'Keine Datei ausgewählt' };

  const ext = (file.name.split('.').pop() || '').toLowerCase();

  if (ext === 'grapesjs') {
    const text = await file.text();
    try {
      return { success: true, project: JSON.parse(text), source: 'grapesjs' };
    } catch {
      return { success: false, error: 'Ungültige .grapesjs-Datei' };
    }
  }

  if (ext === 'zip') {
    try {
      const zip = await JSZip.loadAsync(file);
      const files = Object.keys(zip.files);

      const gjsFile = files.find(
        f => (f.endsWith('.grapesjs') || f.endsWith('grapesjs.json')) && !zip.files[f].dir,
      );
      if (gjsFile) {
        const text = await zip.files[gjsFile].async('string');
        let project;
        try {
          project = JSON.parse(text);
        } catch {
          // fall through to HTML path
        }
        if (project) {
          const cssEntry = files.find(
            f => (f === 'style.css' || f.endsWith('/style.css')) && !zip.files[f].dir,
          );
          const css = cssEntry ? await zip.files[cssEntry].async('string') : '';
          return { success: true, project, source: 'zip-grapesjs', css };
        }
      }

      const htmlFile = files.find(
        f => (f === 'index.html' || f.endsWith('/index.html')) && !zip.files[f].dir,
      );
      const cssEntry = files.find(
        f => (f === 'style.css' || f.endsWith('/style.css')) && !zip.files[f].dir,
      );
      if (htmlFile) {
        const html    = await zip.files[htmlFile].async('string');
        const extCss  = cssEntry ? await zip.files[cssEntry].async('string') : '';
        const bodyMatch   = html.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
        const bodyHtml    = bodyMatch ? bodyMatch[1].trim() : html;
        // Collect inline <style> blocks from <head>
        const headStyles  = [...html.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/gi)]
          .map(m => m[1])
          .join('\n');
        const css = [extCss, headStyles].filter(Boolean).join('\n\n');
        return {
          success: true,
          source:  'zip-html',
          project: { pages: [{ name: 'index', component: bodyHtml }] },
          css,
        };
      }

      return { success: false, error: 'Keine erkennbare Datei im ZIP (index.html oder .grapesjs erwartet)' };
    } catch (e) {
      return { success: false, error: `ZIP-Fehler: ${e.message}` };
    }
  }

  return { success: false, error: `Format .${ext} wird nicht unterstützt (nur .zip / .grapesjs)` };
}

// Applies a parsed project to a live Studio SDK editor instance.
// Uses the editor's project API when available, otherwise falls back to
// setComponents/setStyle.
export function applyTemplateToEditor(editor, parsed) {
  if (!editor || !parsed?.project) return;

  // Preferred: load the entire project payload (preserves pages, assets, styles).
  if (typeof editor.loadProjectData === 'function') {
    try {
      editor.loadProjectData(parsed.project);
      // Append extra CSS (e.g. style.css from ZIP) without overwriting project styles
      if (parsed.css) {
        const existing = editor.getCss?.() || '';
        editor.setStyle?.(existing + '\n\n' + parsed.css);
      }
      return;
    } catch {
      /* fall through to component-level fallback */
    }
  }

  // Fallback: push html/css of the first page directly.
  const firstPage = parsed.project.pages?.[0];
  if (firstPage?.component !== undefined) {
    editor.setComponents?.(firstPage.component || '');
  }
  if (parsed.css || firstPage?.styles) {
    editor.setStyle?.(parsed.css || firstPage.styles || '');
  }
}
