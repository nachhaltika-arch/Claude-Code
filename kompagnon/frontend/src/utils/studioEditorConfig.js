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

export const STUDIO_LICENSE_KEY =
  process.env.REACT_APP_GJS_LICENSE_KEY ||
  '251e7a07b6194ed78d85dc1e7f7f7a2c69fb8beee4c74faea53cf9492f89c357';

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
