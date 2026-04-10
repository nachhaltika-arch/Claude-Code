/**
 * @deprecated Use useGrapesAssetManager from hooks/useGrapesAssetManager.js instead.
 * Clipboard paste is now integrated into the hook automatically.
 */
import API_BASE_URL from '../config';

/**
 * Verarbeitet ein Bild aus der Zwischenablage.
 * Mit leadId: Upload zum Backend → permanente URL.
 * Ohne leadId: Base64-Data-URL (kein Backend nötig).
 */
export async function processClipboardImage(file, leadId, uploadHeaders) {
  const name = file.name || `screenshot-${Date.now()}.png`;

  if (leadId) {
    try {
      const form = new FormData();
      form.append('file', file, name);
      form.append('file_type', 'foto');
      form.append('note', 'Paste aus Zwischenablage');
      const res = await fetch(`${API_BASE_URL}/api/files/upload/${leadId}`, {
        method: 'POST', headers: uploadHeaders, body: form,
      });
      if (res.ok) {
        const data = await res.json();
        return {
          src: `${API_BASE_URL}/api/files/download/${data.id}`,
          name: data.original_filename || name,
        };
      }
    } catch { /* fall through to base64 */ }
  }

  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = e => resolve({ src: e.target.result, name });
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}
