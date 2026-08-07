#!/usr/bin/env node
// Schedule a carousel to personal IG (new public API) + AIW LinkedIn (old token)
// — two different Buffer accounts, one job file.
//
// Usage: node schedule_series.js <jobFile> [--dry-run] [--platform ig|li|both]
// Job file: { name, images: [urls], dueAt: { instagram: ISO, linkedin: ISO },
//             captions: { instagram: "...", linkedin: "..." } }

const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const ENV = fs.readFileSync(path.join(ROOT, '.env'), 'utf8');
const get = (k) => (ENV.match(new RegExp(`^${k}=(.+)$`, 'm')) || [, ''])[1].trim();

const LEGS = {
  ig: {
    label: 'personal IG',
    token: get('BUFFER_PB_TOKEN'),
    channelId: get('BUFFER_PB_INSTAGRAM'),
    metadata: { instagram: { type: 'post', shouldShareToFeed: true } },
    captionKey: 'instagram',
  },
  li: {
    label: 'AIW LinkedIn (company page)',
    token: get('BUFFER_ACCESS_TOKEN'),
    channelId: get('BUFFER_AIW_LINKEDIN_CHANNEL'),
    metadata: null,
    captionKey: 'linkedin',
  },
};

const argv = process.argv.slice(2);
const jobFile = argv.find(a => !a.startsWith('--'));
const DRY = argv.includes('--dry-run');
const PLATFORM = (() => {
  const i = argv.indexOf('--platform');
  return i >= 0 ? argv[i + 1] : 'both';
})();

if (!jobFile) { console.error('usage: node schedule_series.js <jobFile> [--dry-run] [--platform ig|li|both]'); process.exit(1); }
const job = JSON.parse(fs.readFileSync(path.resolve(jobFile), 'utf8'));

const M = `mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    __typename
    ... on PostActionSuccess { post { id status dueAt channel { service name } } }
    ... on MutationError { message }
  }
}`;

async function scheduleLeg(key) {
  const leg = LEGS[key];
  const dueAt = job.dueAt[leg.captionKey];
  const input = {
    channelId: leg.channelId,
    schedulingType: 'automatic',
    mode: 'customScheduled',
    dueAt,
    text: job.captions[leg.captionKey],
    assets: ((job.imagesByPlatform && job.imagesByPlatform[leg.captionKey]) || job.images).map(url => ({ image: { url } })),
  };
  if (leg.metadata) input.metadata = leg.metadata;

  if (DRY) {
    console.log(`\n[DRY] ${job.name} → ${leg.label}`);
    console.log(`  channel=${leg.channelId}  dueAt=${dueAt}  images=${input.assets.length}`);
    console.log(`  caption: ${input.text.slice(0, 100).replace(/\n/g, ' ')}…`);
    return true;
  }
  const res = await fetch('https://api.buffer.com', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${leg.token}` },
    body: JSON.stringify({ query: M, variables: { input } }),
  });
  const j = await res.json();
  const err = j.errors?.[0]?.message || (j.data?.createPost?.message);
  if (err) { console.log(`  ❌ ${leg.label}: ${err}`); return false; }
  const p = j.data.createPost.post;
  console.log(`  ✓ ${leg.label}: id=${p.id} status=${p.status} dueAt=${p.dueAt}`);
  return true;
}

(async () => {
  console.log(`schedule_series — ${DRY ? 'DRY RUN' : 'LIVE'} — ${job.name}`);
  const keys = PLATFORM === 'both' ? ['ig', 'li'] : [PLATFORM];
  let ok = true;
  for (const k of keys) ok = (await scheduleLeg(k)) && ok;
  process.exit(ok ? 0 : 2);
})();
