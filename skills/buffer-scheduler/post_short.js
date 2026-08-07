#!/usr/bin/env node
// Post a vertical short to Austin's personal-brand channels via Buffer's
// official GraphQL API (new public API, personal API key).
//
// Usage:
//   node post_short.js <jobFile> <channel> <mode> [dueISO]
//     channel : youtube | instagram | tiktok
//     mode    : shareNow | customScheduled   (customScheduled needs dueISO, UTC)
//     dueISO  : e.g. 2026-07-07T18:00:00.000Z
//
// Job file (jobs/<slug>.json): { videoUrl, youtube:{title,text}, instagram:{text}, tiktok:{title,text} }

const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const ENV = fs.readFileSync(path.join(ROOT, '.env'), 'utf8');
const get = (k) => (ENV.match(new RegExp(`^${k}=(.+)$`, 'm')) || [, ''])[1].trim();

const TOKEN = get('BUFFER_PB_TOKEN');
const CH = {
  youtube: get('BUFFER_PB_YOUTUBE'),
  instagram: get('BUFFER_PB_INSTAGRAM'),
  tiktok: get('BUFFER_PB_TIKTOK'),
};

const [jobFile, channel, mode, dueISO] = process.argv.slice(2);
if (!jobFile || !channel || !mode) {
  console.error('usage: node post_short.js <jobFile> <channel> <mode> [dueISO]');
  process.exit(1);
}
if (!CH[channel]) { console.error('bad channel:', channel); process.exit(1); }
if (mode === 'customScheduled' && !dueISO) { console.error('customScheduled needs dueISO'); process.exit(1); }

const job = JSON.parse(fs.readFileSync(path.resolve(jobFile), 'utf8'));
const spec = job[channel];

const input = {
  channelId: CH[channel],
  schedulingType: 'automatic',
  mode,
  text: spec.text,
  assets: [{ video: { url: job.videoUrl } }],
};
if (mode === 'customScheduled') input.dueAt = dueISO;

// per-channel metadata
if (channel === 'instagram') {
  input.metadata = { instagram: { type: 'reel', shouldShareToFeed: true } };
} else if (channel === 'youtube') {
  input.metadata = { youtube: { title: spec.title, privacy: 'public', categoryId: (spec.categoryId || '27'), madeForKids: false, notifySubscribers: false } };
} else if (channel === 'tiktok') {
  input.metadata = { tiktok: { title: spec.title || undefined } };
}

const M = `mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    __typename
    ... on PostActionSuccess { post { id status dueAt channel { service name } } }
    ... on MutationError { message }
  }
}`;

(async () => {
  const res = await fetch('https://api.buffer.com', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${TOKEN}` },
    body: JSON.stringify({ query: M, variables: { input } }),
  });
  const j = await res.json();
  console.log(`[${channel} · ${mode}${dueISO ? ' ' + dueISO : ''}]`);
  console.log(JSON.stringify(j, null, 2));
  const err = j.errors || (j.data && j.data.createPost && j.data.createPost.message);
  process.exit(err ? 2 : 0);
})();
