#!/usr/bin/env node
/*
 * Post a graphic-carousel to @austinpeechatt (Instagram) and/or the AI Waterside
 * LinkedIn company page via Buffer.
 *
 * Usage:
 *   node post_to_buffer.js --images <dir> --config <gc.json> [--target ig|li|both] [--now | --at "YYYY-MM-DD HH:MM"] [--dry-run]
 *
 *   --images <dir>   directory holding slide-1.png ... slide-N.png (exported from open-carrusel)
 *   --config <path>  the gc config JSON (caption + hashtags; optional caption_linkedin / hashtags_linkedin)
 *   --target         ig (default) | li | both
 *   --now            publish immediately (Buffer shareNow)
 *   --at "..."       schedule for a local America/New_York time (EDT, UTC-4)
 *   --dry-run        print everything, upload nothing, post nothing
 *
 * Hosting: Buffer fetches images over the internet, so each PNG is uploaded to
 * catbox.moe ONCE and the URLs are reused across targets (unless --dry-run).
 *
 * Reads BUFFER_ACCESS_TOKEN + BUFFER_IG_CHANNEL + BUFFER_LINKEDIN_CHANNEL from ../.env
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const ENV = fs.readFileSync(path.join(ROOT, '.env'), 'utf8');
const getEnv = k => (ENV.match(new RegExp(`${k}=(.+)`)) || [, ''])[1].trim();
const TOKEN = getEnv('BUFFER_ACCESS_TOKEN');
const CH_IG = getEnv('BUFFER_IG_CHANNEL');
const CH_LI = getEnv('BUFFER_LINKEDIN_CHANNEL');
const API = 'https://api.buffer.com';

const argv = process.argv.slice(2);
const flag = (name, def = null) => {
  const i = argv.indexOf(name);
  return i >= 0 ? (argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[i + 1] : true) : def;
};
const DRY = argv.includes('--dry-run');
const NOW = argv.includes('--now');
const AT = flag('--at');
const TARGET = flag('--target', 'ig');
const IMAGES_DIR = flag('--images');
const CONFIG_PATH = flag('--config');

if (!IMAGES_DIR || !CONFIG_PATH) {
  console.error('Required: --images <dir> --config <gc.json>');
  process.exit(1);
}
if (!NOW && !AT && !DRY) {
  console.error('Specify --now or --at "YYYY-MM-DD HH:MM" (or --dry-run).');
  process.exit(1);
}

const cfg = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
const tagStr = arr => (arr || []).map(h => '#' + h.replace(/^#/, '')).join(' ');
function captionFor(platform) {
  const cap = (platform === 'li' && cfg.caption_linkedin) ? cfg.caption_linkedin : cfg.caption || '';
  const tags = (platform === 'li' && cfg.hashtags_linkedin) ? cfg.hashtags_linkedin : cfg.hashtags;
  const t = tagStr(tags);
  return t ? `${cap}\n\n${t}` : cap;
}
const TARGETS = TARGET === 'both' ? ['ig', 'li'] : [TARGET];

// ordered slide-*.png
const files = fs.readdirSync(IMAGES_DIR)
  .filter(f => /^slide-\d+\.png$/.test(f))
  .sort((a, b) => parseInt(a.match(/\d+/)[0]) - parseInt(b.match(/\d+/)[0]))
  .map(f => path.join(IMAGES_DIR, f));

if (!files.length) {
  console.error(`No slide-*.png found in ${IMAGES_DIR}`);
  process.exit(1);
}

// America/New_York (EDT, UTC-4) local -> ISO UTC
function atToUtcIso(s) {
  const [datePart, timePart] = s.trim().split(/\s+/);
  const [y, m, d] = datePart.split('-').map(Number);
  const [hh, mm] = (timePart || '09:00').split(':').map(Number);
  return new Date(Date.UTC(y, m - 1, d, hh + 4, mm, 0)).toISOString();
}

async function uploadCatbox(file) {
  const data = fs.readFileSync(file);
  const fd = new FormData();
  fd.append('reqtype', 'fileupload');
  fd.append('fileToUpload', new Blob([data], { type: 'image/png' }), path.basename(file));
  const r = await fetch('https://catbox.moe/user/api.php', { method: 'POST', body: fd });
  const url = (await r.text()).trim();
  if (!/^https?:\/\//.test(url)) throw new Error(`catbox upload failed for ${file}: ${url}`);
  return url;
}

const CREATE_POST = `mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    __typename
    ... on PostActionSuccess { post { id dueAt channel { service displayName } } }
    ... on MutationError { message }
  }
}`;

const LABEL = { ig: '@austinpeechatt (Instagram)', li: 'AI Waterside (LinkedIn)' };
const CHAN = { ig: CH_IG, li: CH_LI };

async function postOne(platform, urls) {
  const channelId = CHAN[platform];
  if (!channelId) { console.log(`  ✗ ${platform}: no channel id in .env`); return; }
  const input = {
    text: captionFor(platform),
    channelId,
    schedulingType: 'automatic',
    mode: NOW ? 'shareNow' : 'customScheduled',
    assets: urls.map(url => ({ image: { url } })),
  };
  if (platform === 'ig') input.metadata = { instagram: { type: 'post', shouldShareToFeed: true } };
  if (!NOW) input.dueAt = atToUtcIso(AT);

  const res = await fetch(API, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${TOKEN}` },
    body: JSON.stringify({ query: CREATE_POST, variables: { input } }),
  });
  const j = await res.json();
  const data = j.data?.createPost;
  if (j.errors) { console.log(`  ❌ ${LABEL[platform]}:`, JSON.stringify(j.errors)); return; }
  if (data?.message) { console.log(`  ❌ ${LABEL[platform]}: ${data.message}`); return; }
  console.log(`  ✓ ${LABEL[platform]} — ${NOW ? 'published' : 'scheduled'} (id ${data.post.id})`);
}

(async () => {
  console.log(`Buffer post → ${TARGETS.map(t => LABEL[t]).join(' + ')} ${DRY ? '(DRY RUN)' : NOW ? '(SHARE NOW)' : '(SCHEDULED)'}`);
  console.log(`Slides: ${files.length}`);
  if (AT) console.log(`Scheduled for: ${AT} ET  →  ${atToUtcIso(AT)}`);
  for (const t of TARGETS) {
    console.log(`\n--- ${LABEL[t]} caption ---\n${captionFor(t)}`);
  }

  if (DRY) {
    console.log('\n[DRY] would upload these to catbox, in order:');
    files.forEach((f, i) => console.log(`  ${i + 1}. ${f}`));
    console.log(`\n[DRY] targets=${TARGETS.join(',')}  mode=${NOW ? 'shareNow' : AT ? 'customScheduled' : '(pick --now/--at)'}`);
    return;
  }

  console.log('\nUploading images to catbox…');
  const urls = [];
  for (const f of files) {
    const u = await uploadCatbox(f);
    console.log(`  ${path.basename(f)} → ${u}`);
    urls.push(u);
  }
  console.log('Posting…');
  for (const t of TARGETS) await postOne(t, urls);
})().catch(e => { console.error('ERROR:', e.message); process.exit(1); });
