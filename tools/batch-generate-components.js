#!/usr/bin/env node
/**
 * batch-generate-components.js — Bulk-Generator fuer den Component-Designer.
 *
 * Loopt ueber alle Layout-Presets und generiert N Varianten pro Preset via
 * POST /api/components/generate. Speichert die Resultate als JSON-Files in
 * tools/generated/ — KEIN automatisches Schreiben in die DB. Reviewen,
 * dann mit batch-import-components.js die approved Files persistieren.
 *
 * Konfiguration via CLI-Args oder Env-Variablen:
 *   --base URL          (default: $API_URL oder http://localhost:8000)
 *   --token TOKEN       (default: $API_TOKEN)
 *   --per-preset N      (default: 5)
 *   --presets PID,PID   (optional, Filter — sonst alle)
 *   --categories C,C    (optional, Filter — z.B. HERO,CTA)
 *   --industry KEY      (default: shk)
 *   --style VIBE        (default: elegant — minimal|elegant|bold)
 *   --out DIR           (default: tools/generated)
 *   --concurrency N     (default: 2 — parallele KI-Jobs)
 *   --dry-run           (kein API-Call, nur Plan ausgeben)
 *
 * Anthropic-Kosten-Schaetzung: ~$0.02 pro Komponente bei Sonnet 4.6 mit
 * 8000 max_tokens. 53 Presets x 5 Varianten = 265 Komponenten = ~$5-7.
 *
 * Aufruf:
 *   node tools/batch-generate-components.js --token $TOKEN --per-preset 3
 *   node tools/batch-generate-components.js --presets hero_centered,hero_split_image --per-preset 5
 *   node tools/batch-generate-components.js --dry-run
 */
const fs = require('fs');
const path = require('path');

// ── CLI-Args parsen ───────────────────────────────────────────────────────────
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
const PER_PRESET   = parseInt(getArg('per-preset', '5'), 10);
const PRESETS_FILTER = (getArg('presets') || '').split(',').filter(Boolean);
const CATS_FILTER  = (getArg('categories') || '').split(',').filter(Boolean).map((c) => c.toUpperCase());
const INDUSTRY     = getArg('industry', 'shk');
const STYLE_VIBE   = getArg('style', 'elegant');
const OUT_DIR      = path.resolve(getArg('out', path.join(__dirname, 'generated')));
const CONCURRENCY  = parseInt(getArg('concurrency', '2'), 10);
const DRY_RUN      = hasFlag('dry-run');

if (!TOKEN && !DRY_RUN) {
  console.error('ERROR: --token oder $API_TOKEN setzen (oder --dry-run nutzen).');
  process.exit(1);
}

// ── HTTP-Helper (native fetch, Node 18+) ──────────────────────────────────────
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
  if (!res.ok) {
    throw new Error(`HTTP ${res.status} ${pathPart}: ${typeof body === 'string' ? body : JSON.stringify(body)}`);
  }
  return body;
}

// ── Job-Polling: /api/components/generate/{job_id} alle 2s bis done|error ────
async function awaitJob(jobId) {
  const start = Date.now();
  while (Date.now() - start < 5 * 60 * 1000) {  // max 5 min
    await new Promise((r) => setTimeout(r, 2000));
    const job = await api(`/api/components/generate/${jobId}`);
    if (job.status === 'done') return job.result;
    if (job.status === 'error') throw new Error(job.error || 'unknown error');
  }
  throw new Error('Job timeout (>5 min)');
}

// ── Variant-Generator: ein einzelner KI-Call ──────────────────────────────────
async function generateOne(preset, variantIdx) {
  if (DRY_RUN) {
    return {
      _dryRun: true,
      preset_id: preset.id,
      variant: variantIdx,
      category: preset.category,
      label: preset.label,
    };
  }
  const job = await api('/api/components/generate', {
    method: 'POST',
    body: JSON.stringify({
      category:      preset.category,
      layout_preset: preset.id,
      style_vibe:    STYLE_VIBE,
      industry:      INDUSTRY,
      // Variant-Hint im user_prompt — damit KI nicht 5x dasselbe baut
      user_prompt:   `Variante ${variantIdx + 1} von ${PER_PRESET}. Leicht andere Komposition als typische Default.`,
    }),
  });
  const result = await awaitJob(job.job_id);
  return {
    preset_id: preset.id,
    variant: variantIdx,
    category: preset.category,
    layout_label: preset.label,
    generated_at: new Date().toISOString(),
    result,
  };
}

// ── Concurrency-Limit (semaphore-style) ───────────────────────────────────────
async function runWithConcurrency(tasks, limit) {
  const results = [];
  let idx = 0;
  const errors = [];
  async function worker() {
    while (idx < tasks.length) {
      const i = idx++;
      const task = tasks[i];
      try {
        const t0 = Date.now();
        const out = await task.fn();
        const dt = ((Date.now() - t0) / 1000).toFixed(1);
        results.push({ ok: true, task: task.label, dt, out });
        console.log(`  ✓ ${task.label} (${dt}s)`);
      } catch (e) {
        errors.push({ task: task.label, error: e.message });
        console.error(`  ✗ ${task.label}: ${e.message}`);
        results.push({ ok: false, task: task.label, error: e.message });
      }
    }
  }
  const workers = Array.from({ length: limit }, () => worker());
  await Promise.all(workers);
  return { results, errors };
}

// ── Main ─────────────────────────────────────────────────────────────────────
async function main() {
  console.log(`Base:         ${BASE}`);
  console.log(`Per-Preset:   ${PER_PRESET}`);
  console.log(`Concurrency:  ${CONCURRENCY}`);
  console.log(`Industry:     ${INDUSTRY}`);
  console.log(`Style-Vibe:   ${STYLE_VIBE}`);
  console.log(`Out-Dir:      ${OUT_DIR}`);
  console.log(`Dry-Run:      ${DRY_RUN}`);
  if (PRESETS_FILTER.length) console.log(`Presets:      ${PRESETS_FILTER.join(', ')}`);
  if (CATS_FILTER.length)    console.log(`Categories:   ${CATS_FILTER.join(', ')}`);
  console.log('');

  // 1. Layout-Presets vom Backend ziehen
  console.log('Lade Layout-Presets…');
  const presets = await api('/api/components/layout-presets');
  let filtered = presets;
  if (PRESETS_FILTER.length) {
    filtered = filtered.filter((p) => PRESETS_FILTER.includes(p.id));
  }
  if (CATS_FILTER.length) {
    filtered = filtered.filter((p) => CATS_FILTER.includes(p.category));
  }
  console.log(`${presets.length} Presets verfuegbar, ${filtered.length} nach Filter.`);

  // 2. Out-Dir vorbereiten
  if (!DRY_RUN) {
    fs.mkdirSync(OUT_DIR, { recursive: true });
  }

  // 3. Task-Liste bauen
  const tasks = [];
  for (const preset of filtered) {
    for (let v = 0; v < PER_PRESET; v++) {
      tasks.push({
        label: `${preset.id} v${v + 1}`,
        fn: async () => {
          const out = await generateOne(preset, v);
          if (!DRY_RUN) {
            const file = path.join(OUT_DIR, `${preset.id}-v${v + 1}.json`);
            fs.writeFileSync(file, JSON.stringify(out, null, 2), 'utf8');
          }
          return out;
        },
      });
    }
  }
  console.log(`Gesamt: ${tasks.length} KI-Calls geplant. Anthropic-Kosten ~$${(tasks.length * 0.02).toFixed(2)}.\n`);

  if (DRY_RUN) {
    console.log('Dry-Run — keine API-Calls. Plan:');
    tasks.forEach((t) => console.log(`  - ${t.label}`));
    return;
  }

  // 4. Run
  console.log('Starte Generation…\n');
  const t0 = Date.now();
  const { results, errors } = await runWithConcurrency(tasks, CONCURRENCY);
  const dt = ((Date.now() - t0) / 1000).toFixed(1);

  // 5. Summary
  console.log(`\n--- Done in ${dt}s ---`);
  console.log(`Erfolgreich: ${results.filter((r) => r.ok).length}/${results.length}`);
  console.log(`Fehler:      ${errors.length}`);
  if (errors.length) {
    console.log('\nFehler-Details:');
    errors.forEach((e) => console.log(`  ${e.task}: ${e.error}`));
  }
  console.log(`\nResultate liegen in ${OUT_DIR}/. Naechster Schritt: review + import via batch-import-components.js.`);
}

main().catch((e) => {
  console.error('FATAL:', e.message);
  process.exit(1);
});
