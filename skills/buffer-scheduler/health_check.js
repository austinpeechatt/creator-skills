#!/usr/bin/env node
// Buffer health check — catches dead/errored personal-brand posts BEFORE they fail at publish.
//
// Born 2026-07-21: a scheduled TikTok sat in `error` for days (media URL on a 72h
// temp host had expired) and was only caught by Austin eyeballing the Buffer calendar.
// This runs daily via launchd (com.axiom.buffer-health-check) and pings Telegram if:
//   - ANY personal-brand post is status=error, OR
//   - any SCHEDULED post's media URL (asset.source) is unreachable / zero-length
//     (i.e. it WILL fail when Buffer re-fetches it at publish time).
//
// Usage: node health_check.js [--notify]
//   default (no flag) : audit + print only (safe to run by hand)
//   --notify          : also send a Telegram alert if problems found (launchd uses this)
//
// Media rule it enforces: everything must live on apeechatt-media.netlify.app (permanent).
// See memory project_buffer_personal_brand for the digest-deploy re-host procedure.

const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const NOTIFY = process.argv.includes('--notify');

// --- creds (manual parse; no dotenv in the skill dir) ---
const readEnv = (p) => { try { return fs.readFileSync(p, 'utf8'); } catch { return ''; } };
const val = (env, k) => (env.match(new RegExp(`^${k}=(.+)$`, 'm')) || [, ''])[1].trim();

const skillEnv = readEnv(path.join(ROOT, '.env'));
const TOKEN = val(skillEnv, 'BUFFER_PB_TOKEN');
const ORG = val(skillEnv, 'BUFFER_PB_ORG');
const CHANNELS = {
  youtube: val(skillEnv, 'BUFFER_PB_YOUTUBE'),
  instagram: val(skillEnv, 'BUFFER_PB_INSTAGRAM'),
  tiktok: val(skillEnv, 'BUFFER_PB_TIKTOK'),
};
const chanName = (id) => Object.keys(CHANNELS).find((k) => CHANNELS[k] === id) || id;

const tgEnv = readEnv(process.env.TELEGRAM_ENV_PATH || path.join(process.env.HOME, '.config/buffer-scheduler/telegram.env'));
const TG_TOKEN = val(tgEnv, 'TELEGRAM_BOT_TOKEN');
const TG_CHAT = val(tgEnv, 'ALLOWED_USER_ID');

const gql = async (query, variables) => {
  const res = await fetch('https://api.buffer.com', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${TOKEN}` },
    body: JSON.stringify({ query, variables }),
  });
  return res.json();
};

// Is a media URL actually fetchable? HEAD first; some hosts lie on HEAD (content-length 0)
// so fall back to a 1-byte ranged GET before declaring it dead — avoids false alarms.
const mediaLive = async (url) => {
  try {
    const h = await fetch(url, { method: 'HEAD' });
    if (h.ok && Number(h.headers.get('content-length')) > 0) return true;
  } catch {}
  try {
    const g = await fetch(url, { headers: { Range: 'bytes=0-0' } });
    if (g.status === 200 || g.status === 206) return true;
  } catch {}
  return false;
};

const sendTelegram = async (text) => {
  if (!TG_TOKEN || !TG_CHAT) { console.error('no telegram creds — cannot notify'); return; }
  const res = await fetch(`https://api.telegram.org/bot${TG_TOKEN}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chat_id: TG_CHAT, text, parse_mode: 'HTML', disable_web_page_preview: true }),
  });
  const j = await res.json();
  if (!j.ok) console.error('telegram send failed:', JSON.stringify(j));
  else console.log('telegram alert sent');
};

const Q = `query($input: PostsInput!) {
  posts(input: $input) {
    edges { node { id status dueAt text channelId assets { __typename source } } }
  }
}`;

(async () => {
  const input = {
    organizationId: ORG,
    filter: { channelIds: Object.values(CHANNELS).filter(Boolean), status: ['scheduled', 'error', 'sending'] },
  };
  const j = await gql(Q, { input });
  if (!j.data || !j.data.posts) { console.error('query failed:', JSON.stringify(j.errors || j)); process.exit(0); }

  const posts = j.data.posts.edges.map((e) => e.node);
  const problems = [];

  for (const p of posts) {
    const where = `${chanName(p.channelId)} @ ${p.dueAt || '?'}`;
    const snippet = (p.text || '').slice(0, 50).replace(/\n/g, ' ');
    if (p.status === 'error') {
      problems.push(`❌ ERROR  ${where}\n   "${snippet}"  (id ${p.id})`);
      continue;
    }
    // scheduled/sending: verify every media asset is reachable
    for (const a of (p.assets || [])) {
      if (!a.source) continue;
      const ok = await mediaLive(a.source);
      if (!ok) {
        problems.push(`⚠️ DEAD MEDIA  ${where}\n   "${snippet}"\n   ${a.source}  (id ${p.id})`);
      }
    }
  }

  console.log(`checked ${posts.length} scheduled/error posts — ${problems.length} problem(s)`);
  if (problems.length === 0) { console.log('✅ all clear'); process.exit(0); }

  const body = problems.join('\n\n');
  console.log('\n' + body);

  if (NOTIFY) {
    const msg = `🚨 <b>Buffer health check</b> — ${problems.length} post(s) need attention:\n\n` +
      problems.map((s) => s.replace(/</g, '&lt;')).join('\n\n') +
      `\n\nFix: re-host on apeechatt-media (digest deploy) + edit_post.js. See buffer-scheduler skill.`;
    await sendTelegram(msg);
  }
  process.exit(0);
})();
