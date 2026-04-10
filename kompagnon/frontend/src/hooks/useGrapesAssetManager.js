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
import { useState, useCallback } from 'react';
import API_BASE_URL from '../config';

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

  return { onAssetsLoad, onAssetsUpload, assetCount };
}
