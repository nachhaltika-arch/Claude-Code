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
        f => f.endsWith('.grapesjs') || f.endsWith('grapesjs.json'),
      );
      if (gjsFile) {
        const text = await zip.files[gjsFile].async('string');
        return { success: true, project: JSON.parse(text), source: 'zip-grapesjs' };
      }

      const htmlFile = files.find(f => f.endsWith('index.html'));
      const cssFile  = files.find(f => f.endsWith('style.css'));
      if (htmlFile) {
        const html = await zip.files[htmlFile].async('string');
        const css  = cssFile ? await zip.files[cssFile].async('string') : '';
        const bodyMatch = html.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
        const bodyHtml  = bodyMatch ? bodyMatch[1].trim() : html;
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
      if (parsed.css) {
        editor.setStyle?.(parsed.css);
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
