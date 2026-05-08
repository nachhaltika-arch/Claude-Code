#!/usr/bin/env node
/**
 * batch-import-components.js — schreibt von batch-generate-components.js
 * erzeugte JSON-Files in die DB via POST /api/components.
 *
 * Workflow:
 *   1. tools/batch-generate-components.js erzeugt JSON-Files in tools/generated/
 *   2. Mensch reviewed jede Datei (HTML-Validitaet, Slot-Definitionen, etc.)
 *   3. Approved Dateien bleiben im out-Dir, abgelehnte loescht man manuell
 *   4. Dieser Script importiert die uebrigen Files in die KAS-DB
 *
 * CLI-Args:
 *   --base URL           (default: $API_URL)
 *   --token TOKEN        (default: $API_TOKEN)
 *   --in DIR             (default: tools/generated)
 *   --slug-prefix PFX    (default: 'ai-' — vermeidet Slug-Kollisionen mit
 *                        existierenden Library-Eintraegen)
 *   --dry-run            (kein API-Call, nur Plan)
 *   --skip-existing      (Eintraege mit existierendem Slug ueberspringen statt
 *                        zu erroren)
 *
 * Aufruf:
 *   node tools/batch-import-components.js --token $TOKEN --slug-prefix kasai-
 *   node tools/batch-import-components.js --dry-run
 */
const fs = require('fs');
const path = require('path');

// ── CLI ─────────────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
function getArg(name, fallback = null) {
  const idx = args.indexOf(`--${name}`);
  if (idx === -1) return fallback;
  return args[idx + 1] ?? fallback;
}
function hasFlag(name) {
  return args.includes(`--${name}`);
}

const BASE         = getArg('base', process.env.API_URL || 'http://localhost:8000');
const TOKEN        = getArg('token', process.env.API_TOKEN);
const IN_DIR       = path.resolve(getArg('in', path.join(__dirname, 'generated')));
const SLUG_PREFIX  = getArg('slug-prefix', 'ai-');
const DRY_RUN      = hasFlag('dry-run');
const SKIP_EXISTING = hasFlag('skip-existing');

if (!TOKEN && !DRY_RUN) {
  console.error('ERROR: --token oder $API_TOKEN setzen.');
  process.exit(1);
}
if (!fs.existsSync(IN_DIR)) {
  console.error(`ERROR: Input-Dir existiert nicht: ${IN_DIR}`);
  process.exit(1);
}

async function api(pathPart, opts = {}) {
  const url = `${BASE}${pathPart}`;
  const res = await fetch(url, {
    ...opts,
    headers: {
      'Content-Type': 'application/json',
      ...(TOKEN ? { Authorization: `Bearer ${TOKEN}` } : {}),
      ...(opts.headers || {}),
    },
  });
  const text = await res.text();
  let body = null;
  try { body = JSON.parse(text); } catch { body = text; }
  return { ok: res.ok, status: res.status, body };
}

function slugify(s) {
  return String(s || '')
    .toLowerCase()
    .replace(/ä/g, 'ae').replace(/ö/g, 'oe').replace(/ü/g, 'ue').replace(/ß/g, 'ss')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

// ── Main ─────────────────────────────────────────────────────────────────────
async function main() {
  console.log(`Input:        ${IN_DIR}`);
  console.log(`Slug-Prefix:  ${SLUG_PREFIX}`);
  console.log(`Dry-Run:      ${DRY_RUN}`);
  console.log('');

  const files = fs.readdirSync(IN_DIR).filter((f) => f.endsWith('.json'));
  if (files.length === 0) {
    console.log('Keine JSON-Files im Input-Dir.');
    return;
  }
  console.log(`${files.length} Files gefunden.\n`);

  const stats = { imported: 0, skipped: 0, errored: 0, conflicts: 0 };

  for (const file of files) {
    const fullPath = path.join(IN_DIR, file);
    const baseName = path.basename(file, '.json');
    let raw;
    try {
      raw = JSON.parse(fs.readFileSync(fullPath, 'utf8'));
    } catch (e) {
      console.error(`  ✗ ${file}: JSON-Parse-Fehler: ${e.message}`);
      stats.errored++;
      continue;
    }

    const result = raw.result || raw;  // toleriere beide Schemas
    if (!result?.html_template || !result?.name) {
      console.error(`  ✗ ${file}: fehlende Pflichtfelder (html_template oder name)`);
      stats.errored++;
      continue;
    }

    // Slug bauen: prefix + name (slugified) + variant-Suffix wenn doppelt
    const baseSlug = `${SLUG_PREFIX}${slugify(result.name)}`;
    const slug = `${baseSlug}-${baseName.split('-v').pop()}`; // v1, v2, ...

    const payload = {
      slug,
      name:           result.name,
      category:       result.category || raw.category || 'CUSTOM',
      tags:           [...(result.tags || []), 'kas-ai-batch'],
      html_template:  result.html_template,
      slots:          result.slots || [],
      ki_prompt_hint: result.ki_prompt_hint || '',
      preview_note:   result.preview_note || '',
    };

    if (DRY_RUN) {
      console.log(`  → ${slug} (${payload.category}, ${payload.slots.length} slots)`);
      stats.imported++;
      continue;
    }

    const res = await api('/api/components', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    if (res.ok) {
      console.log(`  ✓ ${slug}`);
      stats.imported++;
    } else if (res.status === 409 && SKIP_EXISTING) {
      console.log(`  - ${slug} (Slug existiert, geskippt)`);
      stats.skipped++;
      stats.conflicts++;
    } else {
      console.error(`  ✗ ${slug}: HTTP ${res.status} ${typeof res.body === 'string' ? res.body : JSON.stringify(res.body)}`);
      stats.errored++;
      if (res.status === 409) stats.conflicts++;
    }
  }

  console.log(`\n--- Done ---`);
  console.log(`Importiert:   ${stats.imported}`);
  console.log(`Geskippt:     ${stats.skipped}`);
  console.log(`Konflikte:    ${stats.conflicts}`);
  console.log(`Fehler:       ${stats.errored}`);
}

main().catch((e) => {
  console.error('FATAL:', e.message);
  process.exit(1);
});
