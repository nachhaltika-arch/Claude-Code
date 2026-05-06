#!/usr/bin/env node
/**
 * Bulk-Importer fuer Relume-HTML-Snippets in die KAS Komponenten-Bibliothek.
 *
 * Liest:    {inputDir}/relume-{category}-{slug}.html (Roh-Exports vom Walker)
 * Schreibt: kompagnon/frontend/src/components/library/external/relume/{slug}.html
 *           kompagnon/frontend/src/components/library/external/relume/index.json
 *           (ueberschreibt bestehende Eintraege, behaelt aber relume-navbar-1/2/3)
 *
 * Usage:
 *   node tools/import-relume-bulk.mjs <inputDir> [--smart] [--dry-run] [--limit=N]
 *
 *   <inputDir>     Pfad zum Walker-Output-Folder (z.B. C:/Users/.../Desktop/relume-raw)
 *   --smart        Slot-Detection ueber Claude Haiku 4.5 (semantisch).
 *                  Braucht ANTHROPIC_API_KEY in env. Kostet ~$0.001 / Snippet.
 *   --dry-run      Schreibt nichts, zeigt nur was passieren wuerde.
 *   --limit=N      Verarbeitet nur die ersten N Files (zum Testen).
 *
 * Beispiele:
 *   node tools/import-relume-bulk.mjs C:/Users/DavidVaeth/Desktop/relume-raw --dry-run --limit=5
 *   node tools/import-relume-bulk.mjs C:/Users/DavidVaeth/Desktop/relume-raw --smart
 *
 * Nach dem Lauf: nicht vergessen den Backend-Redeploy zu triggern via Edit
 * in seed_component_library.py LIBRARY_VERSION_LOG (siehe README).
 */
import fs from 'node:fs/promises';
import fsSync from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, '..');
const OUTPUT_DIR = path.join(REPO_ROOT, 'kompagnon', 'frontend', 'src', 'components', 'library', 'external', 'relume');
const INDEX_PATH = path.join(OUTPUT_DIR, 'index.json');

// Eintraege die NICHT ueberschrieben werden — manuell kuratierte navbars
// behalten ihren Zustand (Slots, ki_prompt_hint), die Bulk-Pipeline ergaenzt
// nur was noch nicht da ist.
const PRESERVE_SLUGS = new Set(['relume-navbar-1', 'relume-navbar-2', 'relume-navbar-3']);

// ── Token-Mapping: Relume-eigene Tokens -> Standard-Tailwind ──────────────────

const TOKEN_REPLACEMENTS = [
  // Section-Border (border ohne weiteren modifier vor border-border-primary)
  // Buttons mit `border border-border-primary` werden separat gemappt
  { pattern: /\bborder\s+border-border-primary\b/g, replacement: 'border border-gray-300' },
  { pattern: /\bborder-border-primary\b/g, replacement: 'border-gray-200' },
  { pattern: /\bbg-background-primary\b/g, replacement: 'bg-white' },
  { pattern: /\bbg-background-alternative\b/g, replacement: 'bg-gray-900' },
  { pattern: /\btext-text-primary\b/g, replacement: 'text-gray-900' },
  { pattern: /\btext-text-alternative\b/g, replacement: 'text-white' },
  { pattern: /\bfocus-visible:ring-border-primary\b/g, replacement: 'focus-visible:ring-gray-300' },
  { pattern: /\btext-md\b/g, replacement: 'text-base' },
  { pattern: /\bmin-h-18\b/g, replacement: 'min-h-[4.5rem]' },
  // id="relume" ohne weitere Klassen entfernen (mit umgebenden whitespace)
  { pattern: /\s+id="relume"/g, replacement: '' },
];

// Cloudfront-Logo durch Logo-Slot ersetzen.
// Greift sowohl <img src="..."> standalone als auch <a><img>...</a> Konstrukte.
const CLOUDFRONT_LOGO_RE = /<img\s+src="https:\/\/d22po4pjz3o32e\.cloudfront\.net\/logo-image\.svg"\s+alt="Logo image"\s*\/?>/g;
const CLOUDFRONT_LOGO_REPLACEMENT = '<span class="text-xl font-bold text-gray-900">{{logo_text}}</span>';

// ── Relume-Category -> KAS-Category-Code ──────────────────────────────────────

const CATEGORY_MAP = {
  navbars: { kas: 'NAV', section_hint: 'header_nav' },
  heroes: { kas: 'HERO', section_hint: 'hero' },
  heros: { kas: 'HERO', section_hint: 'hero' },
  banners: { kas: 'HERO', section_hint: 'hero' },
  headers: { kas: 'HERO', section_hint: 'hero' },
  features: { kas: 'LEIST', section_hint: 'features' },
  'feature-sections': { kas: 'LEIST', section_hint: 'features' },
  layouts: { kas: 'LEIST', section_hint: 'features' },
  testimonials: { kas: 'TRUST', section_hint: 'proof' },
  'social-proof': { kas: 'TRUST', section_hint: 'proof' },
  logos: { kas: 'TRUST', section_hint: 'proof' },
  stats: { kas: 'TRUST', section_hint: 'proof' },
  pricing: { kas: 'CTA', section_hint: 'pricing' },
  ctas: { kas: 'CTA', section_hint: 'cta' },
  cta: { kas: 'CTA', section_hint: 'cta' },
  faqs: { kas: 'CTA', section_hint: 'faq' },
  faq: { kas: 'CTA', section_hint: 'faq' },
  contact: { kas: 'CTA', section_hint: 'contact' },
  contacts: { kas: 'CTA', section_hint: 'contact' },
  forms: { kas: 'CTA', section_hint: 'contact' },
  footers: { kas: 'FOOT', section_hint: 'footer' },
  blog: { kas: 'SEO', section_hint: 'blog' },
  // Unbekannte Kategorien -> CUSTOM, section_hint=null
};

function mapCategory(relumeCat) {
  const c = (relumeCat || '').toLowerCase();
  if (CATEGORY_MAP[c]) return CATEGORY_MAP[c];
  return { kas: 'CUSTOM', section_hint: null };
}

// ── Filename-Parsing: relume-{category}-{slug}.html ───────────────────────────

function parseFilename(filename) {
  // Erwartet: relume-{category}-{slug}.html
  // Slug kann Bindestriche enthalten, also greedy nach erstem Bindestrich.
  const m = filename.match(/^relume-([a-z0-9]+)-(.+)\.html$/i);
  if (!m) return null;
  return {
    category: m[1].toLowerCase(),
    slug: m[2].toLowerCase(),
    fullSlug: `relume-${m[2].toLowerCase()}`, // im Repo: relume-{slug} ohne category
  };
}

// ── Cleanup: HTML durchnudeln ────────────────────────────────────────────────

function cleanHtml(rawHtml) {
  let html = rawHtml;
  for (const { pattern, replacement } of TOKEN_REPLACEMENTS) {
    html = html.replace(pattern, replacement);
  }
  // Cloudfront-Logo kann mehrfach im Snippet auftauchen (Mobile + Desktop) —
  // alle durch denselben Slot-Marker ersetzen, sie zeigen ja auch dasselbe Logo.
  html = html.replace(CLOUDFRONT_LOGO_RE, CLOUDFRONT_LOGO_REPLACEMENT);
  return html;
}

// ── Slot-Detection: Pattern-Match ─────────────────────────────────────────────

function detectSlotsPattern(html, parsed) {
  const slots = [];
  let working = html;

  // Logo: schon durch Cloudfront-Replacement als {{logo_text}} drin
  if (working.includes('{{logo_text}}')) {
    slots.push({ key: 'logo_text', label: 'Logo-Text', default: 'KOMPAGNON' });
  }

  // Headlines: <h1>...</h1>, <h2>...</h2>
  // Wir matchen den TEXT-Inhalt (innen <h1>...) und ersetzen ihn durch Slot-Marker.
  let hCount = { h1: 0, h2: 0, h3: 0 };
  working = working.replace(/<(h[123])([^>]*)>([\s\S]*?)<\/\1>/g, (m, tag, attrs, inner) => {
    const trimmed = inner.trim();
    // Skip wenn Inner zu lang oder enthaelt schon Slots / komplexe HTML
    if (!trimmed || trimmed.length > 200 || trimmed.includes('{{') || /<[a-z]/.test(trimmed)) return m;
    hCount[tag]++;
    const key = hCount[tag] === 1 && tag === 'h1' ? 'headline' :
                hCount[tag] === 1 && tag === 'h2' ? 'subheadline' :
                `${tag}_${hCount[tag]}`;
    if (!slots.find((s) => s.key === key)) {
      slots.push({ key, label: tag.toUpperCase() + ' Heading', default: trimmed });
    }
    return `<${tag}${attrs}>{{${key}}}</${tag}>`;
  });

  // Buttons mit Text "Button" -> cta_label_N
  let buttonCount = 0;
  working = working.replace(/<button([^>]*)>([\s\S]*?)<\/button>/g, (m, attrs, inner) => {
    const trimmed = inner.trim();
    // Wenn Inner nur ein einfacher Text ist (kein verschachteltes HTML)
    if (/^[A-Za-z0-9 .,!?\-äöüÄÖÜß]+$/.test(trimmed) && trimmed.length < 50) {
      buttonCount++;
      const key = buttonCount === 1 ? 'cta_label' : `cta_label_${buttonCount}`;
      if (!slots.find((s) => s.key === key)) {
        slots.push({ key, label: `CTA-Button ${buttonCount}`, default: trimmed });
      }
      return `<button${attrs}>{{${key}}}</button>`;
    }
    return m;
  });

  // Links mit Pattern "Link N" -> nav_link_N
  let linkCount = 0;
  working = working.replace(/<a([^>]*)>([\s\S]*?)<\/a>/g, (m, attrs, inner) => {
    const trimmed = inner.trim();
    if (/^Link\s+(One|Two|Three|Four|Five|Six|Seven|Eight)$/i.test(trimmed)) {
      linkCount++;
      const key = `nav_link_${linkCount}`;
      if (!slots.find((s) => s.key === key)) {
        slots.push({ key, label: `Nav-Link ${linkCount}`, default: trimmed });
      }
      return `<a${attrs}>{{${key}}}</a>`;
    }
    return m;
  });

  return { html: working, slots };
}

// ── Slot-Detection: Smart (Claude Haiku) ─────────────────────────────────────

const SMART_PROMPT = `Du bist ein HTML-Strukturanalyst. Analysiere das folgende HTML-Snippet und identifiziere alle Texte, die zu semantischen Slots werden sollten — also Texte die bei Wiederverwendung der Section vom Endkunden befuellt werden (Headlines, Subtexte, Button-Labels, Link-Texte, Logo-Text).

Antworte AUSSCHLIESSLICH als JSON, keine Markdown-Wrapper, keine Erklaerung:

{
  "slots": [
    {
      "key":     "<snake_case key z.B. hero_headline, cta_primary, feature_title_1>",
      "label":   "<menschenlesbares Label auf Deutsch>",
      "default": "<sinnvoller Default-Wert auf Deutsch fuer SHK-Branche>",
      "find":    "<exakter Originaltext aus dem HTML, 1:1 zu finden>"
    }
  ]
}

Regeln:
- "find" muss EXAKT im HTML vorkommen (verbatim, inkl. Leerzeichen). Tools werden danach replace machen.
- Wenn ein Text mehrfach vorkommt (z.B. Logo, "Button"), gib ihn nur EINMAL — der Replacer ersetzt alle Vorkommen mit dem gleichen Slot.
- SHK-Branche (Heizung/Sanitaer/Elektrik) als Default-Kontext: "Termin vereinbaren", "Kostenloser Beratungstermin", "Wallbox installieren" etc.
- Nur 5-15 Slots pro Section, sonst wird's unbenutzbar. Nicht jeden Listpunkt, nur Headlines + CTAs + Hauptlabels.
`;

async function detectSlotsSmart(html, parsed) {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) throw new Error('ANTHROPIC_API_KEY env var nicht gesetzt');

  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
    },
    body: JSON.stringify({
      model: 'claude-haiku-4-5-20251001',
      max_tokens: 1500,
      messages: [{
        role: 'user',
        content: `${SMART_PROMPT}\n\nHTML:\n\`\`\`html\n${html}\n\`\`\``,
      }],
    }),
  });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`Anthropic API HTTP ${res.status}: ${txt.slice(0, 200)}`);
  }

  const body = await res.json();
  const text = (body.content || []).filter((b) => b.type === 'text').map((b) => b.text).join('').trim();

  // Robust gegen versehentliche Codefences
  const cleaned = text.startsWith('```')
    ? text.replace(/^```(?:json)?\n?/, '').replace(/\n?```$/, '').trim()
    : text;

  let parsed_resp;
  try { parsed_resp = JSON.parse(cleaned); }
  catch (e) { throw new Error(`Smart-Mode JSON-Parse failed: ${e.message}; raw: ${cleaned.slice(0, 200)}`); }

  const slots = parsed_resp.slots || [];

  // Replace `find` mit `{{key}}` im HTML
  let working = html;
  const finalSlots = [];
  for (const s of slots) {
    if (!s.key || !s.find) continue;
    const before = working;
    working = working.split(s.find).join(`{{${s.key}}}`);
    if (working !== before) {
      finalSlots.push({ key: s.key, label: s.label || s.key, default: s.default || '' });
    }
  }

  return { html: working, slots: finalSlots };
}

// ── Index-Eintrag-Builder ─────────────────────────────────────────────────────

function buildIndexEntry(parsed, slots) {
  const cat = mapCategory(parsed.category);
  const tags = [parsed.category, 'relume', 'open-source', 'tailwind'];
  const niceName = parsed.slug.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

  return {
    slug: parsed.fullSlug,
    name: `Relume - ${niceName}`,
    category: cat.kas,
    section_hint: cat.section_hint,
    tags,
    slots,
    ki_prompt_hint: `Auto-importiert: ${parsed.category} / ${parsed.slug}. Bitte ki_prompt_hint manuell verfeinern.`,
    preview_note: `Bulk-import via tools/import-relume-bulk.mjs. Mobile-Interaktivitaet ggf. statisch (ohne React-State).`,
    source: 'relume',
  };
}

// ── CLI-Args ──────────────────────────────────────────────────────────────────

function parseArgs() {
  const args = process.argv.slice(2);
  const opts = { inputDir: null, smart: false, dryRun: false, limit: Infinity };
  for (const a of args) {
    if (a === '--smart') opts.smart = true;
    else if (a === '--dry-run') opts.dryRun = true;
    else if (a.startsWith('--limit=')) opts.limit = parseInt(a.split('=')[1], 10);
    else if (!opts.inputDir && !a.startsWith('--')) opts.inputDir = a;
  }
  if (!opts.inputDir) {
    console.error('Usage: node tools/import-relume-bulk.mjs <inputDir> [--smart] [--dry-run] [--limit=N]');
    process.exit(1);
  }
  return opts;
}

// ── Main ──────────────────────────────────────────────────────────────────────

async function main() {
  const opts = parseArgs();

  // Existierenden index.json laden (wir wollen die manuell-kuratierten Eintraege erhalten)
  let existing = { components: [] };
  if (fsSync.existsSync(INDEX_PATH)) {
    existing = JSON.parse(await fs.readFile(INDEX_PATH, 'utf8'));
  }
  const existingMap = new Map(existing.components.map((c) => [c.slug, c]));

  // Files aus Input-Dir lesen
  const allFiles = (await fs.readdir(opts.inputDir))
    .filter((f) => f.endsWith('.html'))
    .sort();
  const files = allFiles.slice(0, opts.limit);

  console.log(`Found ${allFiles.length} files in ${opts.inputDir}, processing ${files.length} (limit=${opts.limit === Infinity ? '-' : opts.limit})`);
  console.log(`Mode: ${opts.smart ? 'SMART (Claude Haiku)' : 'PATTERN'}, dry-run: ${opts.dryRun}`);

  const summary = { processed: 0, skipped: 0, errors: 0 };
  const newEntries = [];

  for (const file of files) {
    const parsed = parseFilename(file);
    if (!parsed) {
      console.warn(`  SKIP: ${file} — kein gueltiger relume-{category}-{slug}.html-Name`);
      summary.skipped++;
      continue;
    }
    if (PRESERVE_SLUGS.has(parsed.fullSlug)) {
      console.log(`  PRESERVE: ${parsed.fullSlug} — manuell kuratiert, nicht ueberschreiben`);
      summary.skipped++;
      continue;
    }

    try {
      const raw = await fs.readFile(path.join(opts.inputDir, file), 'utf8');
      const cleaned = cleanHtml(raw);
      const { html: withSlots, slots } = opts.smart
        ? await detectSlotsSmart(cleaned, parsed)
        : detectSlotsPattern(cleaned, parsed);

      const entry = buildIndexEntry(parsed, slots);
      newEntries.push({ entry, html: withSlots, parsed });

      console.log(`  OK: ${parsed.fullSlug} — ${slots.length} slots, ${withSlots.length} chars`);
      summary.processed++;
    } catch (e) {
      console.error(`  ERROR: ${file} — ${e.message}`);
      summary.errors++;
    }
  }

  if (opts.dryRun) {
    console.log(`\n[DRY-RUN] would write ${newEntries.length} files + update index.json`);
    if (newEntries.length > 0) {
      console.log('Sample entry:', JSON.stringify(newEntries[0].entry, null, 2).slice(0, 800));
    }
  } else {
    // Write HTML files
    await fs.mkdir(OUTPUT_DIR, { recursive: true });
    for (const { entry, html } of newEntries) {
      const filename = `${entry.slug}.html`;
      await fs.writeFile(path.join(OUTPUT_DIR, filename), html, 'utf8');
    }
    // Merge index.json: preserve manuelle, ueberschreibe Bulk
    for (const { entry } of newEntries) {
      existingMap.set(entry.slug, entry);
    }
    existing.components = [...existingMap.values()].sort((a, b) => a.slug.localeCompare(b.slug));
    await fs.writeFile(INDEX_PATH, JSON.stringify(existing, null, 2) + '\n', 'utf8');
    console.log(`\nWrote ${newEntries.length} HTMLs + updated index.json (${existing.components.length} total entries)`);
  }

  console.log(`\nSummary: processed=${summary.processed}, skipped=${summary.skipped}, errors=${summary.errors}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
