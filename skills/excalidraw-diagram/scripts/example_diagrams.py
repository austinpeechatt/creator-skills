#!/usr/bin/env python
"""
Axiom Analytics — video B-roll diagrams (3).
Build:  axiom_diagrams.py <1|2|3|all>  -> writes to output/diagrams/
Each diagram uses the enhanced excalib (logos + shapes).
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from excalib import (txt, rect, oval, dmd, pill, card, arr, seg, polygon,
                     hexagon, chevron, ring, img, logo_chip, save, off,
                     PALETTE, BRAND, INK, MUTE)

OUT = os.path.join(os.path.dirname(__file__), "..", "output", "diagrams")
NAVY = "#0d1b3d"
BLUE = "#386cda"


def aiw_mark(idp, x, y, f, w=158):
    """Subtle AI Waterside wordmark, bottom-right brand stamp (blue on light)."""
    return [img(f"{idp}-aiw", x, y, w, "aiw", f, h=w / 5.922, op=85)]


def zone(idp, x, y, w, h, label, sc, bg):
    """Soft rounded backdrop zone with a small caps label top-left."""
    return [
        card(f"{idp}-z", x, y, w, h, sc=sc, bg=bg, rnd={"type": 3}, sw=1.5,
             rough=0),
        txt(f"{idp}-zl", x + 18, y + 14, w - 36, 20, label, fs=13, ta="left",
            sc=sc, ff=3),
    ]


# ───────────────────────── Diagram 1 — architecture spine ──────────────────
def d1():
    e = []; f = {}
    # title
    e += [txt("t", 46, 26, 760, 42, "Axiom Analytics", fs=34, ta="left",
              sc=NAVY)]
    e += [txt("st", 48, 72, 900, 22,
              "one dashboard, every platform — how the data actually flows",
              fs=15, ta="left", sc=MUTE)]

    # ZONE 1 — sources
    e += zone("s", 44, 120, 332, 600, "SOURCES",
              PALETTE["blue"][0], "#eef4ff")
    chips = [
        ("yt", "youtube", "YouTube", "Long-form + Shorts", "solid", 100),
        ("tt", "tiktok", "TikTok", "Live", "solid", 100),
        ("ig", "instagram", "Instagram", "Parked — Meta wall", "dashed", 60),
        ("vb", "buffer", "Vizard + Buffer", "Scheduled posts", "solid", 100),
        ("fu", "x", "X · LinkedIn", "Coming later", "dashed", 45),
    ]
    cy0 = 168
    for i, (cid, logo, lab, sub, ss, op) in enumerate(chips):
        yy = cy0 + i * 104
        e += logo_chip(f"c-{cid}", 66, yy, logo, f, lab, w=288, h=78,
                       sub=sub, ss=ss, op=op)
        # stub into the collector bus
        e += [seg(f"stub-{cid}", 354, yy + 39, [[0, 0], [44, 0]],
                  sc=PALETTE["slate"][0], sw=2)]
    # collector bus
    bus_x = 398
    e += [seg("bus", bus_x, cy0 + 39, [[0, 0], [0, 4 * 104]],
              sc=PALETTE["slate"][0], sw=3)]

    # ZONE 2 — sync engine (hexagon)
    hx, hy, hr = 560, 360, 92
    e += [hexagon("hex", hx, hy, hr, sc=PALETTE["violet"][0],
                  bg="#f3f0ff", sw=2.5)]
    e += [txt("hex-t", hx - 84, hy - 26, 168, 24, "/api/sync", fs=20,
              sc=NAVY, ff=3)]
    e += [txt("hex-s", hx - 84, hy + 4, 168, 18, "Next.js route", fs=13,
              sc=MUTE)]
    # bus -> hexagon
    e += [arr("a-bus", bus_x, cy0 + 39 + 192, [[0, 0], [hx - hr * 0.78 - bus_x, hy - (cy0 + 39 + 192)]],
              sc=PALETTE["slate"][0], sw=3)]
    e += [txt("a-bus-l", bus_x + 6, hy - 150, 150, 18, "pull + normalize",
              fs=12, ta="left", sc=MUTE)]
    # 30-min trigger (netlify scheduled fn) below hexagon
    e += logo_chip("nf", hx - 110, hy + hr + 26, "netlify",
                   f, "Netlify cron", w=220, h=58, sub="every 30 min")
    e += [arr("a-cron", hx, hy + hr + 26, [[0, 0], [0, -26]],
              sc=PALETTE["teal"][0], sw=2.5, crnd=None)]

    # ZONE 3 — store (Supabase)
    sx, sy, sw_, sh = 716, 250, 250, 232
    e += [card("db", sx, sy, sw_, sh, sc=PALETTE["green"][0], bg="#ebfbf0",
               rnd={"type": 3}, sw=2)]
    e += [img("db-lg", sx + 18, sy + 18, 40, "supabase", f)]
    e += [txt("db-t", sx + 66, sy + 20, 170, 24, "Supabase", fs=20,
              ta="left", sc=NAVY)]
    e += [txt("db-s", sx + 66, sy + 46, 170, 16, "Postgres", fs=12,
              ta="left", sc=MUTE)]
    tables = ["videos", "account_snapshots", "scheduled_posts"]
    for i, tb in enumerate(tables):
        ty = sy + 78 + i * 42
        e += [pill(f"tb-{i}", sx + 18, ty, sw_ - 36, 32, sc=PALETTE["green"][0],
                   bg="#d3f9d8", sw=1.5)]
        e += [txt(f"tb-{i}-t", sx + 30, ty + 7, sw_ - 56, 18, tb, fs=13,
                  ta="left", sc=NAVY, ff=3)]
    e += [txt("db-note", sx, sy + sh + 8, sw_, 16,
              "partitioned by platform", fs=12, sc=MUTE)]
    # hexagon -> db
    e += [arr("a-store", hx + hr * 0.78, hy - 8,
              [[0, 0], [sx - (hx + hr * 0.78), (sy + 70) - (hy - 8)]],
              sc=PALETTE["green"][0], sw=3)]
    e += [txt("a-store-l", hx + hr * 0.78 + 6, hy - 56, 130, 18, "upsert",
              fs=12, ta="left", sc=MUTE)]

    # ZONE 4 — app (browser window)
    bx, by, bw, bh = 1012, 222, 452, 300
    e += [card("win", bx, by, bw, bh, sc=NAVY, bg="#ffffff",
               rnd={"type": 3}, sw=2)]
    # header bar
    e += [rect("win-hdr", bx, by, bw, 42, sc=NAVY, bg=NAVY, rnd={"type": 3})]
    for i, col in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
        e += [oval(f"dot-{i}", bx + 18 + i * 22, by + 16, 12, 12, sc=col,
                   bg=col, sw=1)]
    e += [txt("win-url", bx + 96, by + 12, 300, 18,
              "axiom-analytics.netlify.app   · password", fs=12, ta="left",
              sc="#cdd5e6", ff=3)]
    # 4 tab pills
    tabs = [("Overview", "cadence + insights", PALETTE["blue"]),
            ("Reports", "charts + heatmap", PALETTE["teal"]),
            ("Calendar", "every post", PALETTE["amber"]),
            ("Ideas", "Notion-synced", PALETTE["violet"])]
    pw, ph, gx, gy = 200, 98, 16, 16
    for i, (lab, sub, pal) in enumerate(tabs):
        px = bx + 18 + (i % 2) * (pw + gx)
        py = by + 58 + (i // 2) * (ph + gy)
        e += [card(f"tab-{i}", px, py, pw, ph, sc=pal[0], bg=pal[1],
                   rnd={"type": 3}, sw=2)]
        e += [txt(f"tab-{i}-t", px + 14, py + 16, pw - 28, 26, lab, fs=19,
                  ta="left", sc=NAVY)]
        e += [txt(f"tab-{i}-s", px + 14, py + 50, pw - 28, 18, sub, fs=12,
                  ta="left", sc=MUTE)]
    # db -> window
    e += [arr("a-serve", sx + sw_, sy + 116, [[0, 0], [bx - (sx + sw_), (by + 150) - (sy + 116)]],
              sc=BLUE, sw=3)]
    e += [txt("a-serve-l", sx + sw_ + 8, sy + 92, 120, 18, "serve",
              fs=12, ta="left", sc=MUTE)]
    # netlify host tag
    e += logo_chip("host", bx, by + bh + 14, "netlify", f, "Hosted on Netlify",
                   w=210, h=48)
    # notion two-way to Ideas tab
    nx, ny = bx + 250, by + bh + 14
    e += logo_chip("nt", nx, ny, "notion", f, "Notion · Ideas DB", w=202, h=48)
    ideas_px = bx + 18 + (pw + gx)   # ideas pill x
    ideas_cx = ideas_px + pw / 2
    e += [arr("a-notion", ideas_cx, by + 58 + ph + gy + ph, [[0, 0], [nx + 100 - ideas_cx, ny - (by + 58 + ph + gy + ph)]],
              sc=PALETTE["violet"][0], sw=2.5, head="arrow", shead="arrow")]
    e += [txt("a-notion-l", ideas_cx - 30, ny - 36, 150, 16, "two-way sync",
              fs=11, ta="left", sc=PALETTE["violet"][0])]

    return e, f


def _check(idp, cx, cy, s=9, color="#2f9e44"):
    return [seg(idp, cx - s, cy, [[0, 0], [0.7 * s, 0.7 * s], [2 * s, -1.0 * s]],
               sc=color, sw=3.5, crnd=None)]


def _cross(idp, cx, cy, s=8, color="#c92a2a"):
    return [seg(f"{idp}a", cx - s, cy - s, [[0, 0], [2 * s, 2 * s]], sc=color,
               sw=3.5, crnd=None),
            seg(f"{idp}b", cx - s, cy + s, [[0, 0], [2 * s, -2 * s]], sc=color,
               sw=3.5, crnd=None)]


# ───────────────── Diagram 2 — what each platform gives you ────────────────
def d2():
    e = []; f = {}
    e += [txt("t", 46, 24, 1100, 42, "What each platform actually gives you",
              fs=33, ta="left", sc=NAVY)]
    e += [txt("st", 48, 70, 1100, 22,
              "same dashboard, wildly different data — this asymmetry is the "
              "whole story", fs=15, ta="left", sc=MUTE)]

    rows = ["Per-video stats", "Daily view history", "Follower history",
            "Watch-time / retention", "Audience demographics"]
    cards = [
        dict(idp="yt", logo="youtube", name="YouTube",
             verdict="The gold standard — 2 yrs deep", pal=PALETTE["green"],
             marks=[1, 1, 1, 1, 1], depth=0.95, blocked=False,
             foot="OAuth + Analytics API · full daily history"),
        dict(idp="tt", logo="tiktok", name="TikTok",
             verdict="Easy to connect, but shallow", pal=PALETTE["amber"],
             marks=[1, 0, 0, 0, 0], depth=0.18, blocked=False,
             foot="Display API · current snapshot only"),
        dict(idp="ig", logo="instagram", name="Instagram / Meta",
             verdict="A multi-hour wall", pal=PALETTE["red"],
             marks=[0, 0, 0, 0, 0], depth=0.0, blocked=True,
             foot="banned portfolios · couldn't even get in"),
    ]
    CW, CH, GAP, Y0 = 392, 452, 44, 132
    for ci, c in enumerate(cards):
        x = 52 + ci * (CW + GAP)
        pal = c["pal"]
        e += [card(f"{c['idp']}-c", x, Y0, CW, CH, sc=pal[0], bg="#ffffff",
                   rnd={"type": 3}, sw=2)]
        # header strip
        e += [rect(f"{c['idp']}-h", x, Y0, CW, 86, sc=pal[0], bg=pal[1],
                   rnd={"type": 3}, sw=1.5)]
        e += [img(f"{c['idp']}-lg", x + 22, Y0 + 21, 44, c["logo"], f)]
        e += [txt(f"{c['idp']}-n", x + 80, Y0 + 18, CW - 100, 26, c["name"],
                  fs=22, ta="left", sc=NAVY)]
        e += [txt(f"{c['idp']}-v", x + 80, Y0 + 50, CW - 100, 20, c["verdict"],
                  fs=13, ta="left", sc=pal[0])]
        # rows
        ry = Y0 + 110
        for ri, lab in enumerate(rows):
            yy = ry + ri * 46
            op = 35 if c["blocked"] else 100
            if c["marks"][ri]:
                e += [m | {"opacity": op} for m in _check(f"{c['idp']}-ck{ri}", x + 36, yy + 8)]
            else:
                e += [m | {"opacity": op} for m in _cross(f"{c['idp']}-cx{ri}", x + 34, yy + 6)]
            e += [txt(f"{c['idp']}-rl{ri}", x + 62, yy, CW - 86, 22, lab,
                      fs=15, ta="left", sc=INK, op=op)]
        # depth meter
        my = ry + 5 * 46 + 14
        e += [txt(f"{c['idp']}-ml", x + 24, my - 2, 160, 16, "DATA DEPTH",
                  fs=11, ta="left", sc=MUTE, ff=3)]
        e += [rect(f"{c['idp']}-mt", x + 24, my + 20, CW - 48, 16,
                   sc="#ced4da", bg="#f1f3f5", rnd={"type": 3}, sw=1.2)]
        if c["depth"] > 0:
            e += [rect(f"{c['idp']}-mf", x + 24, my + 20, (CW - 48) * c["depth"],
                       16, sc=pal[0], bg=pal[1], rnd={"type": 3}, sw=1.2)]
        e += [txt(f"{c['idp']}-ft", x + 24, my + 46, CW - 48, 16, c["foot"],
                  fs=11.5, ta="left", sc=MUTE)]
        # rejected stamp for Meta
        if c["blocked"]:
            sx, sy2 = x + CW / 2 - 96, Y0 + 200
            e += [rect(f"{c['idp']}-stmp", sx, sy2, 192, 56, sc="#c92a2a",
                       bg="transparent", rnd={"type": 3}, sw=4, angle=-0.32,
                       op=90)]
            e += [txt(f"{c['idp']}-stmpt", sx + 16, sy2 + 14, 160, 30,
                      "BLOCKED", fs=27, sc="#c92a2a", angle=-0.32, op=90)]

    # bottom caption — the quotable line
    by = Y0 + CH + 36
    e += [txt("cap", 52, by, 1280, 28,
              "YouTube hands you two years.   TikTok tells you today.   "
              "Meta tells you nothing.", fs=22, ta="left", sc=NAVY)]

    return e, f


# ───────────────── Diagram 3 — build method (steal best, rebuild) ──────────
def d3():
    e = []; f = {}
    e += [txt("t", 46, 24, 1150, 42,
              "How I built it: steal the best, skip the rest", fs=33,
              ta="left", sc=NAVY)]
    e += [txt("st", 48, 70, 1150, 22,
              "I didn't invent a dashboard — I surveyed the paid tools, "
              "screenshotted what worked, and rebuilt it as mine",
              fs=15, ta="left", sc=MUTE)]

    # LEFT — the paid tools
    e += [txt("lh", 56, 122, 320, 18, "THE PAID TOOLS I TRIED", fs=12,
              ta="left", sc=MUTE, ff=3)]
    comps = [("Metricool", "paywalled"), ("vidIQ", "cluttered UI"),
             ("Spotter", "$$$ enterprise"), ("SplitHero", "rigid, no control")]
    CX, CW, CH = 56, 312, 72
    for i, (nm, pain) in enumerate(comps):
        yy = 156 + i * 92
        e += [card(f"cm{i}", CX, yy, CW, CH, sc="#c4ccdb", bg="#ffffff",
                   rnd={"type": 3}, sw=1.8)]
        e += [txt(f"cm{i}-n", CX + 20, yy + 16, 180, 26, nm, fs=19,
                  ta="left", sc=NAVY)]
        e += [pill(f"cm{i}-p", CX + CW - 132, yy + CH / 2 - 15, 116, 30,
                   sc=PALETTE["red"][0], bg="#ffe3e3", sw=1.5)]
        e += [txt(f"cm{i}-pt", CX + CW - 130, yy + CH / 2 - 9, 112, 18, pain,
                  fs=12, sc=PALETTE["red"][0])]
        # arrow into funnel
        e += [arr(f"cm{i}-a", CX + CW, yy + CH / 2,
                  [[0, 0], [560 - (CX + CW), 232 - (yy + CH / 2)]],
                  sc="#aab4cc", sw=2, crnd={"type": 2})]

    # MIDDLE — funnel
    fx, fy = 648, 300
    e += [txt("fh", fx - 132, 150, 264, 18, "SCREENSHOT  ·  PICK & CHOOSE",
              fs=12, sc=MUTE, ff=3)]
    e += [polygon("funnel", fx, fy,
                  [(-132, -66), (132, -66), (60, 66), (-60, 66)],
                  sc=PALETTE["amber"][0], bg="#fff9db", sw=2.5)]
    e += [txt("ft", fx - 110, fy - 22, 220, 24, "keep the best", fs=20,
              sc=NAVY)]
    e += [txt("ft2", fx - 110, fy + 6, 220, 18, "parts only", fs=14, sc=MUTE)]

    # MIDDLE -> RIGHT (rebuild w/ Claude)
    e += [img("cl", 786, 296, 48, "claude", f)]
    e += [arr("fa", 716, 356, [[0, 0], [182, -14]], sc=PALETTE["violet"][0],
              sw=3)]
    e += [txt("cl-t", 700, 374, 232, 18, "rebuilt with Claude Code",
              fs=13, ta="center", sc=PALETTE["violet"][0])]

    # RIGHT — the output (mini Axiom window)
    bx, by, bw, bh = 900, 196, 396, 210
    e += [card("win", bx, by, bw, bh, sc=NAVY, bg="#ffffff",
               rnd={"type": 3}, sw=2)]
    e += [rect("win-h", bx, by, bw, 38, sc=NAVY, bg=NAVY, rnd={"type": 3})]
    for i, col in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
        e += [oval(f"d{i}", bx + 16 + i * 20, by + 14, 11, 11, sc=col, bg=col,
                   sw=1)]
    e += [txt("win-u", bx + 86, by + 11, 280, 16, "Axiom Analytics", fs=12,
              ta="left", sc="#cdd5e6", ff=3)]
    minis = [("Overview", PALETTE["blue"]), ("Reports", PALETTE["teal"]),
             ("Calendar", PALETTE["amber"]), ("Ideas", PALETTE["violet"])]
    for i, (lab, pal) in enumerate(minis):
        px = bx + 16 + (i % 2) * 188
        py = by + 52 + (i // 2) * 74
        e += [card(f"mt{i}", px, py, 176, 62, sc=pal[0], bg=pal[1],
                   rnd={"type": 3}, sw=1.8)]
        e += [txt(f"mt{i}-t", px + 14, py + 20, 150, 22, lab, fs=16,
                  ta="left", sc=NAVY)]
    # OWNED stamp
    e += [rect("own", bx + bw - 150, by - 22, 150, 48, sc=PALETTE["green"][0],
               bg="transparent", rnd={"type": 3}, sw=4, angle=0.18, op=92)]
    e += [txt("own-t", bx + bw - 138, by - 12, 128, 28, "OWNED", fs=24,
              sc=PALETTE["green"][0], angle=0.18, op=92)]

    # benefit pills under window
    bens = [("Built in a day", PALETTE["blue"]), ("$0 / month", PALETTE["green"]),
            ("Yours to customize", PALETTE["violet"])]
    bw2 = 190
    for i, (lab, pal) in enumerate(bens):
        px = bx + i * (bw2 + 12) - 2
        e += [pill(f"bn{i}", px, by + bh + 24, bw2, 46, sc=pal[0], bg=pal[1],
                   sw=1.8)]
        e += [txt(f"bn{i}-t", px, by + bh + 38, bw2, 22, lab, fs=15, sc=NAVY)]

    return e, f


SPECS = {"1": (d1, "axiom-d1-architecture"),
         "2": (d2, "axiom-d2-asymmetry"),
         "3": (d3, "axiom-d3-buildmethod")}
BAND = {"1": 0, "2": 840, "3": 1580}   # vertical offset in the combined file


def build_one(key):
    fn, name = SPECS[key]
    e, f = fn()
    save(e, f, os.path.join(OUT, f"{name}.excalidraw"))
    return e, f


def build_combined():
    alle, allf = [], {}
    for key in ("1", "2", "3"):
        e, f = SPECS[key][0]()
        allf.update(f)
        for el in off(e, 0, BAND[key]):
            alle.append({**el, "id": f"d{key}-{el['id']}"})
    save(alle, allf, os.path.join(OUT, "axiom-analytics-diagrams.excalidraw"))


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "1"
    if which == "all":
        for k in SPECS:
            build_one(k)
        build_combined()
    elif which == "combined":
        build_combined()
    else:
        build_one(which)
