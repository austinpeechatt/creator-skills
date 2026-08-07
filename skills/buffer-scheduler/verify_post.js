#!/usr/bin/env node
// verify_post.js — one-liner check that a Buffer post is scheduled correctly.
//   node verify_post.js <postId> [pb|aiw]
// pb = personal account (BUFFER_PB_TOKEN), aiw = AIW account (BUFFER_ACCESS_TOKEN).
// With no account arg it tries both tokens and reports whichever finds the post.
// Endpoint MUST be the API root (https://api.buffer.com) — /1/graphql rejects valid tokens.
const fs = require('fs');
const path = require('path');

const ENV = fs.readFileSync(path.join(__dirname, '.env'), 'utf8');
const get = k => (ENV.match(new RegExp('^' + k + '=(.*)$', 'm')) || [])[1];

const [postId, account] = process.argv.slice(2);
if (!postId) {
  console.error('usage: node verify_post.js <postId> [pb|aiw]');
  process.exit(1);
}

const TOKENS = {
  pb: get('BUFFER_PB_TOKEN'),
  aiw: get('BUFFER_ACCESS_TOKEN'),
};

const QUERY = `query($id: PostId!){ post(input:{id:$id}){ id status dueAt channelId text assets{ __typename } } }`;

async function check(label, token) {
  const res = await fetch('https://api.buffer.com', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ query: QUERY, variables: { id: postId } }),
  });
  const j = await res.json();
  const p = j.data && j.data.post;
  if (!p) return { label, ok: false, err: JSON.stringify(j.errors || j) };
  return { label, ok: true, post: p };
}

(async () => {
  const tries = account ? [account] : ['pb', 'aiw'];
  for (const t of tries) {
    if (!TOKENS[t]) { console.error(`no token for account "${t}" in .env`); continue; }
    const r = await check(t, TOKENS[t]);
    if (r.ok) {
      const p = r.post;
      console.log(`[${r.label}] ${p.id}  status=${p.status}  dueAt=${p.dueAt}  assets=${p.assets.length}`);
      console.log(`  channel=${p.channelId}`);
      console.log(`  text: ${(p.text || '').replace(/\s+/g, ' ').slice(0, 90)}…`);
      process.exit(p.status === 'scheduled' || p.status === 'sent' ? 0 : 2);
    }
    if (account) { console.error(`[${r.label}] ${r.err}`); process.exit(1); }
  }
  console.error(`post ${postId} not found on either account`);
  process.exit(1);
})();
