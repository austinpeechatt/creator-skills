#!/usr/bin/env node
// List Buffer posts per personal-brand channel with status + dueAt + id.
// Use to find failed posts (status 'error') and grab their ids for edit_post.js.
//
// Usage:
//   node list_posts.js            # all statuses, all 3 channels
//   node list_posts.js error      # only failed posts (any status filter works:
//                                  # draft|needs_approval|scheduled|sending|sent|error)

const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const ENV = fs.readFileSync(path.join(ROOT, '.env'), 'utf8');
const get = (k) => (ENV.match(new RegExp(`^${k}=(.+)$`, 'm')) || [, ''])[1].trim();
const TOKEN = get('BUFFER_PB_TOKEN');
const ORG = get('BUFFER_PB_ORG');
const CH = { youtube: get('BUFFER_PB_YOUTUBE'), instagram: get('BUFFER_PB_INSTAGRAM'), tiktok: get('BUFFER_PB_TIKTOK') };

const statusFilter = process.argv[2]; // optional

const Q = `query Posts($input: PostsInput!) {
  posts(input: $input) { edges { node { id status dueAt text } } }
}`;

(async () => {
  let anyErr = false;
  for (const [name, id] of Object.entries(CH)) {
    const filter = { channelIds: [id] };
    if (statusFilter) filter.status = [statusFilter];
    const res = await fetch('https://api.buffer.com', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${TOKEN}` },
      body: JSON.stringify({ query: Q, variables: { input: { organizationId: ORG, filter } } }),
    });
    const j = await res.json();
    console.log(`\n===== ${name} =====`);
    if (j.errors) { console.log('ERR', JSON.stringify(j.errors).slice(0, 500)); continue; }
    const edges = (j.data && j.data.posts && j.data.posts.edges) || [];
    edges.sort((a, b) => (a.node.dueAt || '').localeCompare(b.node.dueAt || ''));
    for (const e of edges) {
      const n = e.node;
      if (n.status === 'error') anyErr = true;
      console.log(`${n.status.padEnd(10)} ${(n.dueAt || '-').slice(0, 16)}  id=${n.id}  ${(n.text || '').replace(/\n/g, ' ').slice(0, 45)}`);
    }
  }
  console.log(`\n${anyErr ? '⚠️  errors present — re-host with ./rehost.sh then fix with edit_post.js' : '✅ no error posts'}`);
})();
