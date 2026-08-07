---
name: buffer-scheduler
description: Schedule and manage short-form video posts across YouTube, Instagram and TikTok through Buffer's GraphQL API. Use when scheduling a Short/Reel, checking what's queued, fixing a failed post, or health-checking the calendar.
---

# Buffer Scheduler

Command-line scheduling for short-form video via Buffer. Talks to Buffer's
GraphQL API directly rather than the public REST API.

## Setup

1. Copy `.env.example` to `.env` and fill in your token, org ID and channel IDs.
2. `node list_posts.js` — if it prints your queue, you're connected.

## The one thing that will bite you

**Buffer re-fetches your media at PUBLISH time, not when you schedule.**

A post scheduled for next Tuesday will go and download the video URL *next
Tuesday*. If that URL is dead by then, the post fails silently and sits in
`error` until you notice.

So your media has to stay live until the post date. Temporary file hosts
(litterbox, uguu, and similar) expire in hours or days and will break scheduled
posts. Host on something permanent you control — a static site on Netlify,
Cloudflare Pages, S3, or similar.

Buffer is also picky about how the file is served: it needs a direct URL that
returns a correct `Content-Length` on a HEAD request. Some hosts return zero for
video and Buffer rejects it.

## Commands

| Command | What it does |
|---|---|
| `node post_short.js <jobFile> <channel> <mode> [dueISO]` | Schedule a vertical short. `channel` is `youtube`, `instagram` or `tiktok`. |
| `node list_posts.js [status]` | List queued posts with status, due date and ID. `node list_posts.js error` finds failures. |
| `node edit_post.js <jobFile> <channel> <postId> <videoUrl> <dueISO>` | Fix a post in place — swap a dead media URL or move the date. Keeps the calendar clean instead of delete-and-recreate. |
| `node verify_post.js <postId>` | Confirm one post is scheduled correctly. |
| `node schedule.js [--dry-run] [--only N]` | Batch-schedule from a job file. Always dry-run first. |
| `node schedule_series.js` | Schedule the same asset across several channels in one go. |
| `node health_check.js` | Flag any post sitting in `error` or pointing at dead media. Built to run on a daily timer. |

## Job files

A job file is JSON describing one piece of content — the video URL and a caption
per platform. Keep them in a `jobs/` folder next to the scripts.

```json
{
  "slug": "my-short",
  "video": "https://your-media-host.example.com/my-short.mp4",
  "captions": {
    "youtube": "Title for the Short",
    "instagram": "Caption for the Reel",
    "tiktok": "Caption for TikTok"
  }
}
```

## Health check

`health_check.js` is the piece that turns this from a script collection into
something you can trust. It exists because a scheduled TikTok once sat in
`error` for days — the media URL had expired on a temporary host — and was only
caught by manually eyeballing the Buffer calendar.

Run it on a daily timer (launchd, cron, a GitHub Action) and point
`TELEGRAM_ENV_PATH` at a file with `TELEGRAM_BOT_TOKEN` and `ALLOWED_USER_ID` if
you want it to message you. Without that config it just prints to stdout.
