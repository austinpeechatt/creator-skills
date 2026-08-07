#!/usr/bin/env node
// Buffer GraphQL scheduler
// Usage:
//   node schedule.js [--dry-run] [--only <slot>]
//   --dry-run: print the mutations without firing
//   --only N : schedule only slot number N

const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const ENV = fs.readFileSync(path.join(ROOT, '.env'), 'utf8');
const get = k => (ENV.match(new RegExp(`${k}=(.+)`)) || [, ''])[1].trim();
const TOKEN = get('BUFFER_ACCESS_TOKEN');
const LI = get('BUFFER_LINKEDIN_CHANNEL');
const IG = get('BUFFER_INSTAGRAM_CHANNEL');
const API = 'https://api.buffer.com';

const config = JSON.parse(fs.readFileSync(path.join(ROOT, 'posts.json'), 'utf8'));

const argv = process.argv.slice(2);
const DRY = argv.includes('--dry-run');
const ONLY = (() => {
  const i = argv.indexOf('--only');
  return i >= 0 ? parseInt(argv[i + 1]) : null;
})();
const PLATFORM = (() => {
  const i = argv.indexOf('--platform');
  return i >= 0 ? argv[i + 1] : 'both';
})();

// "2026-05-17" + "09:00" America/New_York -> ISO UTC string
function localToUtcIso(dateStr, timeStr) {
  // America/New_York is UTC-4 (EDT) for all 10 posting dates (mid-May to early-June 2026)
  const [y, m, d] = dateStr.split('-').map(Number);
  const [hh, mm] = timeStr.split(':').map(Number);
  const utcHour = hh + 4;
  const dt = new Date(Date.UTC(y, m - 1, d, utcHour, mm, 0));
  return dt.toISOString();
}

async function gql(query, variables) {
  const res = await fetch(API, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${TOKEN}`,
    },
    body: JSON.stringify({ query, variables }),
  });
  return res.json();
}

const CREATE_POST = `
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    __typename
    ... on PostActionSuccess { post { id dueAt channel { service displayName } } }
    ... on MutationError { message }
  }
}`;

async function scheduleOne(post, channelId, channelLabel) {
  const dueAt = localToUtcIso(post.date, config.post_time_local);
  const hashtags = channelLabel === 'linkedin' ? config.hashtags.linkedin : config.hashtags.instagram;
  const text = `${post.caption}\n\n${hashtags}`;
  const assets = post.images.map(url => ({ image: { url } }));

  const input = {
    text,
    channelId,
    schedulingType: 'automatic',
    mode: 'customScheduled',
    dueAt,
    assets,
  };
  if (channelLabel === 'instagram') {
    input.metadata = {
      instagram: {
        type: 'post',
        shouldShareToFeed: true,
      },
    };
  }

  if (DRY) {
    console.log(`\n[DRY] slot ${post.slot} ${post.name} → ${channelLabel}`);
    console.log(`  dueAt=${dueAt} (${post.date} 9am ET)`);
    console.log(`  text=${text.slice(0, 80).replace(/\n/g, ' ')}…`);
    console.log(`  images=${post.images.length}`);
    return { ok: true };
  }

  const res = await gql(CREATE_POST, { input });
  const data = res.data?.createPost;
  const errs = res.errors;
  if (errs) {
    console.log(`  ❌ slot ${post.slot} ${channelLabel}: ${errs[0].message}`);
    return { ok: false, error: errs[0].message };
  }
  if (data?.message) {
    console.log(`  ❌ slot ${post.slot} ${channelLabel}: ${data.message}`);
    return { ok: false, error: data.message };
  }
  if (data?.failures?.length) {
    console.log(`  ⚠ slot ${post.slot} ${channelLabel}: partial — ${data.failures.map(f => f.message).join('; ')}`);
    return { ok: false, error: 'partial' };
  }
  console.log(`  ✓ slot ${post.slot} ${channelLabel}: id=${data.post.id}`);
  return { ok: true, id: data.post?.id };
}

(async () => {
  console.log(`Buffer Scheduler — ${DRY ? 'DRY RUN' : 'LIVE'}\n`);
  const posts = ONLY ? config.posts.filter(p => p.slot === ONLY) : config.posts;
  if (!posts.length) {
    console.log(`No posts match.`);
    return;
  }

  const results = [];
  for (const post of posts) {
    console.log(`\n— slot ${post.slot} (${post.type}) ${post.name} —`);
    const li = PLATFORM === 'ig' ? { ok: true, skipped: true } : await scheduleOne(post, LI, 'linkedin');
    const ig = PLATFORM === 'li' ? { ok: true, skipped: true } : await scheduleOne(post, IG, 'instagram');
    results.push({ slot: post.slot, linkedin: li, instagram: ig });
  }

  console.log(`\n\n=== SUMMARY ===`);
  const ok = results.filter(r => r.linkedin.ok && r.instagram.ok).length;
  const partial = results.filter(r => r.linkedin.ok !== r.instagram.ok).length;
  const fail = results.filter(r => !r.linkedin.ok && !r.instagram.ok).length;
  console.log(`${ok}/${results.length} fully scheduled, ${partial} partial, ${fail} failed`);
  for (const r of results) {
    if (!r.linkedin.ok || !r.instagram.ok) {
      console.log(`  slot ${r.slot}: LI=${r.linkedin.ok ? '✓' : '✗ ' + r.linkedin.error} | IG=${r.instagram.ok ? '✓' : '✗ ' + r.instagram.error}`);
    }
  }
})();
