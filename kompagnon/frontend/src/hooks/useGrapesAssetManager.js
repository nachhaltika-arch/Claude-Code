/**
 * useGrapesAssetManager — zentraler Hook für alle GrapesJS-Editoren.
 * Kapselt: Portal-Uploads, Admin-Uploads, gecrawlte Bilder, Direkt-Upload.
 *
 * Verwendung:
 *   const { onAssetsLoad, onAssetsUpload, assetCount } =
 *     useGrapesAssetManager({ leadId, projectId, token });
 *
 *   <StudioEditor options={{ assets: { onLoad: onAssetsLoad, onUpload: onAssetsUpload } }} />
 */
import { useState, useCallback, useEffect, useRef } from 'react';
import API_BASE_URL from '../config';

const IMAGE_MIME = new Set(['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml', 'image/bmp']);

export function useGrapesAssetManager({ leadId, projectId, token } = {}) {
  const [assetCount, setAssetCount] = useState(0);
  const authHeaders = token ? { Authorization: `Bearer ${token}` } : {};

  // onLoad: merge project assets + portal uploads + crawled images
  const onAssetsLoad = useCallback(async () => {
    const allAssets = [];

    // 1. Project assets (existing endpoint)
    if (projectId) {
      try {
        const res = await fetch(`${API_BASE_URL}/api/assets/project/${projectId}`, { headers: authHeaders });
        if (res.ok) {
          const data = await res.json();
          (data.assets || []).forEach(a => allAssets.push({
            type: 'image',
            src: a.src.startsWith('http') ? a.src : `${API_BASE_URL}${a.src}`,
            name: a.name,
          }));
        }
      } catch { /* silent */ }
    }

    // 2. Portal uploads + crawled images (unified endpoint)
    if (leadId) {
      try {
        const res = await fetch(
          `${API_BASE_URL}/api/files/${leadId}/grapesjs-assets?include_crawled=true`,
          { headers: authHeaders },
        );
        if (res.ok) {
          const portalAssets = await res.json();
          if (Array.isArray(portalAssets)) allAssets.push(...portalAssets);
        }
      } catch { /* silent */ }
    }

    setAssetCount(allAssets.length);
    return allAssets;
  }, [projectId, leadId, token]); // eslint-disable-line

  // onUpload: upload files to backend, return asset array
  const onAssetsUpload = useCallback(async ({ files }) => {
    if (!files?.length) return [];

    // Without leadId: can't upload, return empty
    if (!leadId && !projectId) return [];

    const results = [];
    for (const file of files) {
      try {
        const fd = new FormData();
        fd.append('file', file, file.name || 'upload.png');

        let res;
        if (leadId) {
          fd.append('file_type', 'foto');
          fd.append('note', 'Upload aus Editor');
          res = await fetch(`${API_BASE_URL}/api/files/upload/${leadId}`, {
            method: 'POST', headers: authHeaders, body: fd,
          });
        } else if (projectId) {
          res = await fetch(`${API_BASE_URL}/api/assets/project/${projectId}/upload`, {
            method: 'POST', headers: authHeaders, body: fd,
          });
        }

        if (res?.ok) {
          const data = await res.json();
          if (leadId) {
            results.push({
              src: `${API_BASE_URL}/api/files/download/${data.id}`,
              name: data.original_filename || file.name,
            });
          } else {
            (data.data || data.assets || []).forEach(d => results.push({
              ...d,
              src: d.src?.startsWith('http') ? d.src : `${API_BASE_URL}${d.src}`,
            }));
          }
        }
      } catch { /* silent */ }
    }

    setAssetCount(c => c + results.length);
    return results;
  }, [leadId, projectId, token]); // eslint-disable-line

  // editorRef: set from outside after editor init (editorRef.current = editor)
  const editorRef = useRef(null);

  // Single-file upload helper for paste
  const uploadSingleFile = useCallback(async (file) => {
    if (!file || !IMAGE_MIME.has(file.type)) return null;
    const name = file.name || `paste-${Date.now()}.png`;
    if (leadId) {
      try {
        const fd = new FormData();
        fd.append('file', file, name);
        fd.append('file_type', 'foto');
        fd.append('note', 'Paste aus Zwischenablage');
        const res = await fetch(`${API_BASE_URL}/api/files/upload/${leadId}`, { method: 'POST', headers: authHeaders, body: fd });
        if (res.ok) {
          const data = await res.json();
          return { src: `${API_BASE_URL}/api/files/download/${data.id}`, name: data.original_filename || name };
        }
      } catch { /* fall through */ }
    }
    // Base64 fallback
    return new Promise(resolve => {
      const reader = new FileReader();
      reader.onload = e => resolve({ src: e.target.result, name });
      reader.onerror = () => resolve(null);
      reader.readAsDataURL(file);
    });
  }, [leadId, authHeaders]); // eslint-disable-line

  // Clipboard paste listener (Ctrl+V / Cmd+V)
  useEffect(() => {
    const handlePaste = async (e) => {
      const editor = editorRef.current;
      if (!editor) return;
      const items = Array.from(e.clipboardData?.items || []);
      const imageItem = items.find(item => IMAGE_MIME.has(item.type));
      if (!imageItem) return;
      e.preventDefault();
      const file = imageItem.getAsFile();
      if (!file) return;
      let toast;
      try { toast = (await import('react-hot-toast')).default; } catch { /* optional */ }
      const tid = toast?.loading?.('Bild wird eingefügt…');
      const result = await uploadSingleFile(file);
      if (result) {
        try { editor.AssetManager?.add({ type: 'image', ...result }); } catch { /* Studio SDK may differ */ }
        toast?.success?.(`Bild eingefügt: ${result.name}`, { id: tid });
        setAssetCount(c => c + 1);
      } else {
        toast?.error?.('Bild konnte nicht eingefügt werden', { id: tid });
      }
    };
    document.addEventListener('paste', handlePaste);
    return () => document.removeEventListener('paste', handlePaste);
  }, [uploadSingleFile]);

  // Manual refresh: re-fetch all assets and inject into running editor
  const refreshAssets = useCallback(async () => {
    const fresh = await onAssetsLoad();
    if (editorRef.current) {
      try {
        const am = editorRef.current.AssetManager;
        fresh.forEach(a => { if (!am?.get?.(a.src)) am?.add?.(a); });
      } catch { /* Studio SDK may differ */ }
    }
    return fresh;
  }, [onAssetsLoad]);

  // Auto-refresh every 60s while editor is open
  useEffect(() => {
    if (!leadId) return;
    const interval = setInterval(() => {
      if (editorRef.current) refreshAssets();
    }, 60_000);
    return () => clearInterval(interval);
  }, [leadId, refreshAssets]);

  return { onAssetsLoad, onAssetsUpload, assetCount, editorRef, refreshAssets };
}
