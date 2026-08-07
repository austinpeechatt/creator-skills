#!/usr/bin/env node
// Edit an EXISTING Buffer post in place — swap its video URL and/or reschedule.
// Use this to FIX failed posts (dead media URL) or move a post to a new date
// without deleting + recreating (keeps the calendar clean).
//
// Usage:
//   node edit_post.js <jobFile> <channel> <postId> <videoUrl> <dueISO>
//     channel  : youtube | instagram | tiktok
//     postId   : the Buffer post id (get it from list_posts.js)
//     videoUrl : a LIVE, durable URL — re-host first with ./rehost.sh (litterbox)
//     dueISO   : UTC, e.g. 2026-07-14T18:00:00.000Z  (2 PM ET = 18:00Z in summer/EDT)
//
// Note: editPost requires schedulingType + mode + (for YouTube) metadata.title +
// category, or it errors "YouTube posts require a title/category". This script
// re-supplies all of that from the job file, so pass the same job file as post_short.js.

const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const ENV = fs.readFileSync(path.join(ROOT, '.env'), 'utf8');
const get = (k) => (ENV.match(new RegExp(`^${k}=(.+)$`, 'm')) || [, ''])[1].trim();
const TOKEN = get('BUFFER_PB_TOKEN');

const [jobFile, channel, postId, videoUrl, dueISO] = process.argv.slice(2);
if (!jobFile || !channel || !postId || !videoUrl || !dueISO) {
  console.error('usage: node edit_post.js <jobFile> <channel> <postId> <videoUrl> <dueISO>');
  process.exit(1);
}
if (!['youtube', 'instagram', 'tiktok'].includes(channel)) { console.error('bad channel:', channel); process.exit(1); }

const job = JSON.parse(fs.readFileSync(path.resolve(jobFile), 'utf8'));
const spec = job[channel] || {};

const input = {
  id: postId,
  schedulingType: 'automatic',
  mode: 'customScheduled',
  dueAt: dueISO,
  assets: [{ video: { url: videoUrl } }],
};
if (channel === 'instagram') {
  input.metadata = { instagram: { type: 'reel', shouldShareToFeed: true } };
} else if (channel === 'youtube') {
  input.metadata = { youtube: { title: spec.title, privacy: 'public', categoryId: (spec.categoryId || '27'), madeForKids: false, notifySubscribers: false } };
} else if (channel === 'tiktok') {
  input.metadata = { tiktok: { title: spec.title || undefined } };
}

const M = `mutation Edit($input: EditPostInput!) {
  editPost(input: $input) {
    __typename
    ... on PostActionSuccess { post { id status dueAt } }
    ... on MutationError { message }
    ... on UnexpectedError { message }
    ... on RestProxyError { message code }
  }
}`;

(async () => {
  const res = await fetch('https://api.buffer.com', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${TOKEN}` },
    body: JSON.stringify({ query: M, variables: { input } }),
  });
  const j = await res.json();
  const e = j.data && j.data.editPost;
  if (e && e.__typename === 'PostActionSuccess') {
    console.log(`OK [${channel}] ${e.post.id} -> ${e.post.status} @ ${e.post.dueAt}`);
    process.exit(0);
  }
  console.error(`FAIL [${channel}]`, JSON.stringify(j.errors || e));
  process.exit(2);
})();
