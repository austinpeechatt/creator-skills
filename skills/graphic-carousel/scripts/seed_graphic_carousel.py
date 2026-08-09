#!/usr/bin/env python3
"""
Seed a premium AI Waterside-branded carousel into a running open-carrusel instance.

Usage:  python3 seed_graphic_carousel.py config.json
Prints the carousel URL on success (line prefixed CAROUSEL_URL:).

Three AIW-native style generators (auto-picked by Claude, override per carousel or per slide):
  A = Blueprint        (pale-blue bg + navy grid, Space Grotesk, blue accents, mono counter)
  B = Bold block       (color-blocked BLUE/OFFWHITE/INK panels, giant Space Grotesk display)
  C = Editorial clean  (off-white bg, whitespace, centered, blue underline/highlight accent)

Shared: BLUE accent, a minimal `01 / 05` mono counter (no beat strip), and the AIW logo
mark bottom-right (white on dark panels, blue on light) — always present per Austin's rule.

Slide types: cover / problem / system / proof / who / cta / image / cta_image. System
renders as a numbered node-rail (B/C) or numbered list (A); `who` renders icon cards
(agencies/e-com/etc.). `image` / `cta_image` (folded in from the GEO v2 project seeder,
2026-07-07) are framed-image slides — kicker/heading/short body + a big white rounded
card holding a diagram/screenshot + optional mono footer line; they always render in
Style A (Blueprint) and the referenced file must already sit in open-carrusel's
public/uploads/ (referenced by bare filename).

config.json shape:
{
  "name": "...", "aspectRatio": "4:5",
  "style": "A" | "B" | "C" | "auto",
  "caption": "...", "hashtags": ["aiautomation","..."],
  "slides": [
    {"type":"cover","kicker":"AI AUTOMATION AGENCY","hero":"...","subline":"..."},
    {"type":"problem","kicker":"...","heading":"...","items":["...","..."]},
    {"type":"system","kicker":"...","heading":"...","steps":["...","..."]},
    {"type":"who","kicker":"...","heading":"Who it's for","items":["Agencies","E-commerce brands","Professional services","SaaS & startups"]},
    {"type":"image","kicker":"...","heading":"...","body":"...","image":"diag-foo.png","footer":"aiwaterside.com"},
    {"type":"cta_image","heading":"...","body":"...","image":"screenshot.png","footer":"..."},
    {"type":"cta","heading":"...","keyword":"WAVE","handle":"@austinpeechatt"}
  ]
  # any slide may carry "style":"A|B|C" to override (used when carousel style is "mix")
}
"""
import json, re, sys, urllib.request

cfg = json.load(open(sys.argv[1]))
BASE = cfg.get("base_url", "http://localhost:3000")
slides = cfg["slides"]
N = len(slides)

# ---- AI Waterside palette -------------------------------------------------
PALE       = "#b5d0f4"
OFFWHITE   = "#f9f8fd"
BLUE_LIGHT = "#8baeeb"
BLUE_MID   = "#618de2"
BLUE       = "#386cda"
INK        = "#0d1b3d"

DISPLAY = "Space Grotesk"   # headlines
BODY    = "Inter"           # body
MONO    = "JetBrains Mono"  # labels + counter

LOGO_BLUE  = "aiw-logo-blue.png"    # dark-blue mark — use on light backgrounds
LOGO_WHITE = "aiw-logo-white.png"   # white mark — use on dark backgrounds

ICONS = ["building", "cart", "briefcase", "saas"]  # mapped to `who` items by index


def li(items, bullet, fs=36, lh=1.45, color=None, mb=18, font=BODY):
    c = f"color:{color};" if color else ""
    rows = "".join(
        f'<li style="margin-bottom:{mb}px;{c}">{bullet}&nbsp;&nbsp;{x}</li>' for x in items)
    return f'<ul style="list-style:none;font-family:{font},sans-serif;font-size:{fs}px;line-height:{lh};">{rows}</ul>'


def counter(idx, muted):
    return (f'<div style="position:absolute;top:80px;right:80px;font-family:{MONO},monospace;'
            f'font-size:24px;letter-spacing:0.14em;color:{muted};">{idx+1:02d} / {N:02d}</div>')


def kicker(txt, color):
    if not txt:
        return ""
    return (f'<div style="display:inline-block;font-family:{MONO},monospace;font-size:22px;'
            f'letter-spacing:0.14em;text-transform:uppercase;color:{color};margin-bottom:30px;">{txt}</div>')


def logo(dark_bg, size=178):
    name = LOGO_WHITE if dark_bg else LOGO_BLUE
    return (f'<img src="{BASE}/uploads/{name}" alt="AI Waterside" '
            f'style="position:absolute;bottom:44px;right:52px;width:{size}px;height:auto;opacity:0.95;"/>')


def icon_svg(name, color, size=50):
    attrs = (f'width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
             f'stroke="{color}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"')
    paths = {
        "building": '<rect x="5" y="3" width="14" height="18" rx="1"/><path d="M9 7h.01M12 7h.01M15 7h.01M9 11h.01M12 11h.01M15 11h.01M9 15h.01M12 15h.01M15 15h.01"/><path d="M10 21v-3.5h4V21"/>',
        "cart": '<circle cx="9" cy="20" r="1.4"/><circle cx="17" cy="20" r="1.4"/><path d="M2.5 4H5l2.2 11.1a1 1 0 0 0 1 .8h8a1 1 0 0 0 1-.8L20.5 7H6"/>',
        "briefcase": '<rect x="3" y="7.5" width="18" height="12.5" rx="2"/><path d="M8 7.5V5.5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="3" y1="13" x2="21" y2="13"/>',
        "saas": '<path d="M7 18a4 4 0 0 1-.5-7.97A5 5 0 0 1 16 9.5a3.5 3.5 0 0 1 .5 8.5"/><path d="M12 12.5v6M9.5 15 12 12.5 14.5 15"/>',
        "clinic": '<rect x="4" y="4" width="16" height="16" rx="3"/><path d="M12 8.5v7M8.5 12h7"/>',
        "store": '<path d="M4 9.5 5 5h14l1 4.5"/><path d="M4 9.5h16v9.5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1z"/><path d="M4 9.5a2.5 2.5 0 0 0 5 0 2.5 2.5 0 0 0 5 0 2.5 2.5 0 0 0 5 0"/>',
    }
    return f'<svg {attrs}>{paths.get(name, "")}</svg>'


def who_grid(items, card_bg, border, icon_color, label_color, center=False, mw=None, icons=None):
    icons = icons or ICONS
    al = "center" if center else "left"
    cells = []
    for i, it in enumerate(items[:4]):
        ic = icon_svg(icons[i % len(icons)], icon_color, 50)
        cells.append(
            f'<div style="border:2px solid {border};border-radius:16px;padding:30px 28px;background:{card_bg};text-align:{al};">'
            f'{ic}'
            f'<div style="margin-top:14px;font-family:{DISPLAY},sans-serif;font-weight:600;font-size:32px;line-height:1.15;color:{label_color};">{it}</div>'
            f'</div>')
    style = "display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-top:38px;"
    if mw:
        style += f"max-width:{mw}px;margin-left:auto;margin-right:auto;"
    return f'<div style="{style}">{"".join(cells)}</div>'


def node_rail(steps, line_color, node_bg, node_fg, label_color, center=False):
    n = len(steps)
    rows = []
    for i, st in enumerate(steps):
        last = (i == n - 1)
        connector = "" if last else (
            f'<div style="position:absolute;left:29px;top:62px;bottom:-26px;width:3px;background:{line_color};"></div>')
        rows.append(
            f'<div style="position:relative;display:flex;gap:28px;align-items:flex-start;margin-bottom:26px;text-align:left;">'
            f'{connector}'
            f'<div style="flex:0 0 auto;width:60px;height:60px;border-radius:50%;background:{node_bg};color:{node_fg};'
            f'display:flex;align-items:center;justify-content:center;font-family:{DISPLAY},sans-serif;font-weight:700;font-size:26px;z-index:1;">{i+1:02d}</div>'
            f'<div style="padding-top:11px;font-family:{BODY},sans-serif;font-size:36px;line-height:1.3;color:{label_color};">{st}</div>'
            f'</div>')
    wrap = "margin-top:40px;"
    if center:
        wrap += "max-width:680px;margin-left:auto;margin-right:auto;"
    return f'<div style="{wrap}">{"".join(rows)}</div>'


def wave_svg(color, w=420, opacity=0.55):
    return (f'<svg width="{w}" viewBox="0 0 200 34" fill="none" stroke="{color}" stroke-width="4" '
            f'stroke-linecap="round" style="opacity:{opacity};display:block;">'
            f'<path d="M2 24 C 38 6, 66 6, 98 18 S 162 32, 198 10"/></svg>')


def img_card(src):
    # big white rounded card holding an uploaded diagram/screenshot (GEO v2 / Alex-carousel ref);
    # `src` = bare filename already present in open-carrusel's public/uploads/
    return (f'<div style="margin-top:44px;background:#ffffff;border-radius:22px;padding:24px;'
            f'box-shadow:0 26px 60px rgba(13,27,61,0.18);border:1px solid rgba(255,255,255,0.9);">'
            f'<img src="{BASE}/uploads/{src}" style="display:block;width:100%;height:auto;border-radius:12px;"/></div>')


def footer_line(txt, color):
    if not txt:
        return ""
    return (f'<div style="position:absolute;left:80px;bottom:58px;font-family:{MONO},monospace;'
            f'font-size:26px;letter-spacing:0.06em;color:{color};">{txt}</div>')


# ===========================================================================
# STYLE A — Blueprint
# ===========================================================================
def render_A(s, idx, eff_idx):
    grid = ("background-image:"
            "repeating-linear-gradient(0deg,rgba(13,27,61,0.07) 0 1px,transparent 1px 56px),"
            "repeating-linear-gradient(90deg,rgba(13,27,61,0.07) 0 1px,transparent 1px 56px);")
    muted = "#3f5891"
    rule = f'<div style="width:90px;height:5px;background:{BLUE};margin:0 0 30px;"></div>'
    t = s.get("type")
    top_anchor = False  # image slides anchor content at the top so the img card has room
    if t == "cover":
        body = (kicker(s.get("kicker", ""), BLUE)
                + f'<div style="font-family:{DISPLAY},sans-serif;font-weight:700;font-size:104px;'
                  f'line-height:1.02;letter-spacing:-0.02em;color:{INK};">{s.get("hero","")}</div>'
                + f'<div style="margin-top:30px;">{wave_svg(BLUE, 360, 0.7)}</div>'
                + f'<div style="margin-top:30px;font-family:{BODY},sans-serif;font-size:38px;'
                  f'line-height:1.4;max-width:820px;color:{INK};opacity:0.82;">{s.get("subline","")}</div>')
    elif t == "who":
        cards = who_grid(s.get("items", []), "rgba(255,255,255,0.5)", BLUE, BLUE, INK, icons=s.get("icons"))
        body = (kicker(s.get("kicker", ""), BLUE) + rule
                + f'<div style="font-family:{DISPLAY},sans-serif;font-weight:700;font-size:72px;'
                  f'line-height:1.04;letter-spacing:-0.02em;color:{INK};">{s.get("heading","")}</div>'
                + cards)
    elif t == "proof":
        body = (kicker(s.get("kicker", ""), BLUE)
                + f'<div style="font-family:{DISPLAY},sans-serif;font-weight:700;font-size:200px;'
                  f'line-height:0.92;color:{BLUE};letter-spacing:-0.03em;">{s.get("stat","")}</div>'
                + f'<div style="font-family:{BODY},sans-serif;font-size:38px;margin-top:18px;color:{INK};">{s.get("statlabel","")}</div>'
                + f'<div style="margin-top:34px;">{li(s.get("checks", []), "&#10003;", fs=34, color=INK, mb=16)}</div>')
    elif t == "cta":
        kw = s.get("keyword", "")
        body = (f'<div style="font-family:{DISPLAY},sans-serif;font-weight:700;font-size:88px;'
                f'line-height:1.02;letter-spacing:-0.02em;color:{INK};">{s.get("heading","")}</div>'
                f'<div style="margin-top:36px;">{wave_svg(BLUE, 360, 0.7)}</div>'
                f'<div style="margin-top:30px;font-family:{BODY},sans-serif;font-size:38px;line-height:1.35;color:{INK};">'
                f'Comment <span style="background:{BLUE};color:{OFFWHITE};padding:4px 18px;border-radius:6px;font-weight:600;">{kw}</span> and I\'ll reach out.</div>'
                f'<div style="margin-top:26px;font-family:{MONO},monospace;font-size:30px;color:{muted};">Follow {s.get("handle","@austinpeechatt")} &rarr;</div>')
    elif t == "image":
        # framed-image slide: kicker + heading + optional short body + big white image card
        top_anchor = True
        body_txt = (f'<div style="margin-top:22px;font-family:{BODY},sans-serif;font-size:31px;'
                    f'line-height:1.42;color:{INK};opacity:0.82;max-width:900px;">{s.get("body","")}</div>'
                    if s.get("body") else "")
        body = (kicker(s.get("kicker", ""), BLUE)
                + f'<div style="font-family:{DISPLAY},sans-serif;font-weight:700;font-size:60px;'
                  f'line-height:1.06;letter-spacing:-0.02em;color:{INK};">{s.get("heading","")}</div>'
                + body_txt + img_card(s["image"]))
    elif t == "cta_image":
        # closer variant: heading + wave + body + image card (e.g. product/landing screenshot)
        top_anchor = True
        body = (f'<div style="font-family:{DISPLAY},sans-serif;font-weight:700;font-size:66px;'
                f'line-height:1.04;letter-spacing:-0.02em;color:{INK};">{s.get("heading","")}</div>'
                + f'<div style="margin-top:24px;">{wave_svg(BLUE, 360, 0.7)}</div>'
                + f'<div style="margin-top:24px;font-family:{BODY},sans-serif;font-size:34px;line-height:1.35;color:{INK};">{s.get("body","")}</div>'
                + img_card(s["image"]))
    else:  # problem / system
        items = s.get("items") or s.get("steps") or []
        if t == "system":
            rows = "".join(
                f'<li style="margin-bottom:22px;display:flex;gap:24px;align-items:baseline;">'
                f'<span style="font-family:{DISPLAY},sans-serif;font-weight:700;font-size:46px;color:{BLUE};">{i+1:02d}</span>'
                f'<span>{x}</span></li>' for i, x in enumerate(items))
            lst = f'<ul style="list-style:none;font-family:{BODY},sans-serif;font-size:38px;line-height:1.35;margin-top:40px;color:{INK};">{rows}</ul>'
        else:
            arrow = f'<span style="color:{BLUE};">&rarr;</span>'
            lst = f'<div style="margin-top:40px;">{li(items, arrow, fs=38, mb=20, color=INK)}</div>'
        body = (kicker(s.get("kicker", ""), BLUE) + rule
                + f'<div style="font-family:{DISPLAY},sans-serif;font-weight:700;font-size:72px;'
                  f'line-height:1.04;letter-spacing:-0.02em;color:{INK};">{s.get("heading","")}</div>'
                + lst)
    content_pos = "top:170px;" if top_anchor else "top:52%;transform:translateY(-50%);"
    return (f'<div style="position:relative;width:1080px;height:1350px;background:{PALE};{grid}'
            f'color:{INK};font-family:{BODY},sans-serif;padding:80px;overflow:hidden;">'
            f'{counter(eff_idx, muted)}'
            f'<div style="position:absolute;left:80px;right:80px;{content_pos}">{body}</div>'
            f'{footer_line(s.get("footer", ""), BLUE)}{logo(False)}</div>')


# ===========================================================================
# STYLE B — Bold block
# ===========================================================================
B_PANELS = [BLUE, OFFWHITE, INK]
B_FG  = {BLUE: OFFWHITE, OFFWHITE: INK,  INK: OFFWHITE}
B_ACC = {BLUE: OFFWHITE, OFFWHITE: BLUE, INK: BLUE_LIGHT}
B_MUT = {BLUE: "#cfe0fa", OFFWHITE: "#7e93c4", INK: "#6b7da6"}


def render_B(s, idx, eff_idx):
    bg = B_PANELS[idx % 3]
    fg, acc, muted = B_FG[bg], B_ACC[bg], B_MUT[bg]
    t = s.get("type")
    head_sm = "font-family:%s,sans-serif;font-weight:700;font-size:84px;line-height:1.0;letter-spacing:-0.02em;" % DISPLAY
    if t == "cover":
        body = (kicker(s.get("kicker", ""), acc)
                + f'<div style="font-family:{DISPLAY},sans-serif;font-weight:700;font-size:150px;'
                  f'line-height:0.96;letter-spacing:-0.03em;">{s.get("hero","")}</div>'
                + f'<div style="margin-top:34px;">{wave_svg(acc, 400, 0.85)}</div>'
                + f'<div style="margin-top:30px;font-family:{BODY},sans-serif;font-size:40px;'
                  f'line-height:1.35;max-width:840px;color:{muted};">{s.get("subline","")}</div>')
    elif t == "who":
        ic = s.get("icons")
        if bg == OFFWHITE:
            cards = who_grid(s.get("items", []), "rgba(56,108,218,0.06)", BLUE, BLUE, INK, icons=ic)
        elif bg == BLUE:
            cards = who_grid(s.get("items", []), "rgba(255,255,255,0.12)", "rgba(255,255,255,0.45)", OFFWHITE, OFFWHITE, icons=ic)
        else:
            cards = who_grid(s.get("items", []), "rgba(255,255,255,0.06)", BLUE_LIGHT, BLUE_LIGHT, OFFWHITE, icons=ic)
        body = (kicker(s.get("kicker", ""), acc)
                + f'<div style="{head_sm}">{s.get("heading","")}</div>' + cards)
    elif t == "system":
        rail = node_rail(s.get("steps", []), acc, acc, bg, fg)
        body = (kicker(s.get("kicker", ""), acc)
                + f'<div style="{head_sm}">{s.get("heading","")}</div>' + rail)
    elif t == "proof":
        body = (kicker(s.get("kicker", ""), acc)
                + f'<div style="font-family:{DISPLAY},sans-serif;font-weight:700;font-size:240px;'
                  f'line-height:0.9;color:{acc};letter-spacing:-0.04em;">{s.get("stat","")}</div>'
                + f'<div style="font-family:{BODY},sans-serif;font-size:40px;margin-top:18px;">{s.get("statlabel","")}</div>'
                + f'<div style="margin-top:34px;">{li(s.get("checks", []), "&#10003;", fs=36, color=fg, mb=16)}</div>')
    elif t == "cta":
        kw = s.get("keyword", "")
        body = (f'<div style="font-family:{DISPLAY},sans-serif;font-weight:700;font-size:110px;'
                f'line-height:0.98;letter-spacing:-0.03em;">{s.get("heading","")}</div>'
                f'<div style="margin-top:34px;">{wave_svg(acc, 400, 0.85)}</div>'
                f'<div style="margin-top:30px;font-family:{BODY},sans-serif;font-size:40px;line-height:1.3;">'
                f'Comment <span style="background:{acc};color:{bg};padding:4px 18px;border-radius:6px;font-weight:700;">{kw}</span> and I\'ll reach out.</div>'
                f'<div style="margin-top:26px;font-family:{MONO},monospace;font-size:32px;color:{muted};">Follow {s.get("handle","@austinpeechatt")} &rarr;</div>')
    else:  # problem
        items = s.get("items") or s.get("steps") or []
        arrow = f'<span style="color:{acc};">&rarr;</span>'
        lst = f'<div style="margin-top:44px;">{li(items, arrow, fs=40, mb=20)}</div>'
        body = (f'<div style="font-family:{DISPLAY},sans-serif;font-weight:700;font-size:110px;'
                f'line-height:0.98;letter-spacing:-0.03em;">{s.get("heading","")}</div>' + lst)
    return (f'<div style="position:relative;width:1080px;height:1350px;background:{bg};color:{fg};'
            f'font-family:{BODY},sans-serif;padding:80px;overflow:hidden;">'
            f'{counter(eff_idx, muted)}'
            f'<div style="position:absolute;left:80px;right:80px;top:52%;transform:translateY(-50%);">{body}</div>'
            f'{logo(bg != OFFWHITE)}</div>')


# ===========================================================================
# STYLE C — Editorial clean
# ===========================================================================
def render_C(s, idx, eff_idx):
    muted = "#54618a"
    t = s.get("type")
    underline = f'<div style="width:90px;height:4px;background:{BLUE};margin:34px auto;"></div>'
    if t == "cover":
        inner = (kicker(s.get("kicker", ""), BLUE)
                 + f'<div style="font-family:{DISPLAY},sans-serif;font-weight:600;font-size:88px;'
                   f'line-height:1.08;letter-spacing:-0.02em;color:{INK};">{s.get("hero","")}</div>'
                 + f'<div style="margin:34px auto;display:flex;justify-content:center;">{wave_svg(BLUE, 300, 0.7)}</div>'
                 + f'<div style="font-family:{BODY},sans-serif;font-size:34px;line-height:1.5;'
                   f'color:{muted};max-width:720px;margin:0 auto;">{s.get("subline","")}</div>')
    elif t == "who":
        cards = who_grid(s.get("items", []), OFFWHITE, BLUE_LIGHT, BLUE, INK, center=True, mw=720, icons=s.get("icons"))
        inner = (kicker(s.get("kicker", ""), BLUE)
                 + f'<div style="font-family:{DISPLAY},sans-serif;font-weight:600;font-size:72px;'
                   f'line-height:1.08;letter-spacing:-0.02em;color:{INK};">{s.get("heading","")}</div>'
                 + underline + cards)
    elif t == "system":
        rail = node_rail(s.get("steps", []), BLUE_LIGHT, BLUE, OFFWHITE, INK, center=True)
        inner = (kicker(s.get("kicker", ""), BLUE)
                 + f'<div style="font-family:{DISPLAY},sans-serif;font-weight:600;font-size:72px;'
                   f'line-height:1.08;letter-spacing:-0.02em;color:{INK};">{s.get("heading","")}</div>'
                 + underline + rail)
    elif t == "proof":
        inner = (kicker(s.get("kicker", ""), BLUE)
                 + f'<div style="font-family:{DISPLAY},sans-serif;font-weight:700;font-size:200px;'
                   f'line-height:0.92;color:{BLUE};letter-spacing:-0.03em;">{s.get("stat","")}</div>'
                 + f'<div style="font-family:{DISPLAY},sans-serif;font-weight:600;font-size:46px;margin-top:14px;color:{INK};">{s.get("statlabel","")}</div>'
                 + f'<div style="margin-top:30px;">{li(s.get("checks", []), "&#10003;", fs=32, color=muted, mb=14)}</div>')
    elif t == "cta":
        inner = (f'<div style="font-family:{DISPLAY},sans-serif;font-weight:600;font-size:80px;'
                 f'line-height:1.06;letter-spacing:-0.02em;color:{INK};">{s.get("heading","")}</div>'
                 + underline
                 + f'<div style="font-family:{BODY},sans-serif;font-size:34px;color:{muted};">'
                   f'Comment <b style="color:{BLUE};">{s.get("keyword","")}</b> &middot; Follow {s.get("handle","@austinpeechatt")}</div>')
    else:  # problem
        items = s.get("items") or s.get("steps") or []
        rows = "".join(
            f'<div style="margin-bottom:22px;"><span style="color:{BLUE};">&rarr;</span>&nbsp;&nbsp;{x}</div>'
            for x in items)
        inner = (kicker(s.get("kicker", ""), BLUE)
                 + f'<div style="font-family:{DISPLAY},sans-serif;font-weight:600;font-size:72px;'
                   f'line-height:1.08;letter-spacing:-0.02em;color:{INK};">{s.get("heading","")}</div>'
                 + underline
                 + f'<div style="font-family:{BODY},sans-serif;font-size:34px;line-height:1.5;'
                   f'color:{muted};max-width:680px;margin:0 auto;text-align:left;">{rows}</div>')
    return (f'<div style="position:relative;width:1080px;height:1350px;background:{OFFWHITE};color:{INK};'
            f'font-family:{BODY},sans-serif;padding:150px 96px;display:flex;flex-direction:column;'
            f'align-items:center;justify-content:center;text-align:center;overflow:hidden;">'
            f'{counter(eff_idx, "#9aa6c7")}{inner}{logo(False)}</div>')


# ---- dispatch + seed ------------------------------------------------------
RENDERERS = {"A": render_A, "B": render_B, "C": render_C}


def eff_style(s):
    if s.get("type") in ("image", "cta_image"):
        return "A"  # framed-image slides are Blueprint-only (only render_A implements them)
    st = s.get("style") or cfg.get("style", "A")
    return st if st in RENDERERS else "A"


def req(path, payload, method="POST"):
    r = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(),
                               headers={"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(r) as resp:
        return json.loads(resp.read())


car = req("/api/carousels", {"name": cfg["name"], "aspectRatio": cfg.get("aspectRatio", "4:5")})
cid = car["id"]
for i, s in enumerate(slides):
    html = RENDERERS[eff_style(s)](s, i, i)
    # open-carrusel's font extractor fails on quoted family names followed by a comma
    # (font-family:'Anton',sans-serif) -> normalize to unquoted so fonts inline on export.
    html = re.sub(r"font-family:'([^']+)'", r"font-family:\1", html)
    req(f"/api/carousels/{cid}/slides", {"html": html, "notes": f"slide {i+1} [{eff_style(s)}/{s.get('type')}]"})
    print(f"  slide {i+1} [{eff_style(s)}/{s.get('type')}] added")
if cfg.get("caption") or cfg.get("hashtags"):
    req(f"/api/carousels/{cid}", {"caption": cfg.get("caption", ""), "hashtags": cfg.get("hashtags", [])}, method="PUT")
print("CAROUSEL_URL:", f"{BASE}/carousel/{cid}")
print("CAROUSEL_ID:", cid)
