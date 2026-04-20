// Shared configuration for the @grapesjs/studio-sdk editor.
// Every editor in the app imports from here so the plugin set,
// license key and default options stay consistent.

import {
  tableComponent,
  listPagesComponent,
  fsLightboxComponent,
  lightGalleryComponent,
  swiperComponent,
  iconifyComponent,
  accordionComponent,
  flexComponent,
  rteProseMirror,
  canvasEmptyState,
  canvasFullSize,
  canvasGridMode,
  layoutSidebarButtons,
  youtubeAssetProvider,
} from '@grapesjs/studio-sdk-plugins';

// License key wird ausschliesslich aus der Build-Time-Env geladen.
// Kein Hardcoded-Fallback — frueher war der Schluessel im Quellcode
// und damit in DevTools sowie Git-History sichtbar.
export const STUDIO_LICENSE_KEY = process.env.REACT_APP_GJS_LICENSE_KEY || '';

if (!STUDIO_LICENSE_KEY && typeof console !== 'undefined') {
  // eslint-disable-next-line no-console
  console.warn(
    '[Studio SDK] REACT_APP_GJS_LICENSE_KEY ist nicht gesetzt — ' +
    'der Editor wird mit einer Lizenz-Fehlermeldung starten.'
  );
}

// Build a fresh plugin list. We wrap in a function so each editor
// instance gets its own plugin descriptors (avoids shared state).
export const buildStudioPlugins = () => [
  tableComponent.init({}),
  listPagesComponent.init({}),
  fsLightboxComponent.init({}),
  lightGalleryComponent.init({}),
  swiperComponent.init({}),
  iconifyComponent.init({}),
  accordionComponent.init({}),
  flexComponent.init({}),
  rteProseMirror.init({}),
  canvasEmptyState.init({}),
  canvasFullSize.init({}),
  canvasGridMode.init({}),
  layoutSidebarButtons.init({}),
  youtubeAssetProvider.init({}),
];
