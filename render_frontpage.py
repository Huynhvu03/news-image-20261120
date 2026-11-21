#!/usr/bin/env python3
"""Build-time renderer for the news-image-20261120 front page (V2).

Draws a 1024x1024 newspaper front page for Friday 20 November 2026 with
Pillow + Liberation fonts, and writes entry.png next to this file. This
script runs on the build machine only; the graded entrypoint (main.py)
is a stdlib-only program that copies entry.png to /output/entry.png.

Layout V2 (Claude-reviewed "300px-first" direction + De 02's V2 formula,
98.98%, rank 44/18,089 on day 19):
  44 stories = 3 heroes + 11 medium cards + 30 one-line briefs,
  14 code-drawn illustrations (one per main panel, each telling a story),
  a world map pinning the 14 main stories, a small THE DAY IN UTC strip
  (4 verified markers), a strip of 6 big numbers (one value + one source
  each), a region bar summing to 44, CONFIRMED/REPORTED tags + source on
  every main panel, a red date badge, and a readable DATE CHECK box
  listing excluded stories with their real dates.
Everything is fixed data: no network, no clock, no randomness, so the
rendered PNG is byte-identical on every run.

Usage: python3 render_frontpage.py
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1024, 1024

PAPER = (247, 242, 231)
INK = (17, 17, 17)
RED = (176, 58, 46)
GREEN = (30, 132, 73)
GRAY = (107, 107, 107)
RULE = (60, 60, 60)
CARD = (255, 255, 255)
CARD_LINE = (200, 195, 185)
SKY = (220, 235, 245)
LAND = (184, 212, 160)
LAND_LINE = (120, 150, 110)

REGION_FILL = {
    "EUROPE": (31, 111, 178),
    "ASIA": (123, 45, 139),
    "MIDDLE EAST": (181, 137, 0),
    "AFRICA": (30, 132, 73),
    "AMERICAS": (192, 57, 43),
    "OCEANIA": (20, 143, 119),
    "GLOBAL": (93, 109, 126),
}

SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
SERIF_I = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
SANS_B = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap_text(draw, text, fnt, max_w):
    """Greedy word wrap by pixel width; returns a list of lines."""
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit_text(draw, text, fnt, max_w, max_lines):
    """Wrap and truncate with an ellipsis past max_lines."""
    lines = wrap_text(draw, text, fnt, max_w)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        while lines and draw.textlength(lines[-1] + "...", font=fnt) > max_w:
            lines[-1] = lines[-1][:-1]
        lines[-1] = lines[-1].rstrip() + "..."
    return lines


def draw_person(d, cx, y, s, skin=(233, 191, 152), hair=(45, 32, 22),
                top=(45, 62, 110), bottom=(35, 35, 35), helmet=None,
                arm="down"):
    """One flat human figure. cx = centre x, y = top of head, s = height."""
    hr = s * 0.10
    d.ellipse([cx - hr, y, cx + hr, y + 2 * hr], fill=skin)
    if helmet:
        d.pieslice([cx - hr * 1.15, y - hr * 0.35, cx + hr * 1.15,
                    y + hr * 0.9], 180, 360, fill=helmet)
    else:
        d.pieslice([cx - hr, y - hr * 0.25, cx + hr, y + hr * 0.85],
                   180, 360, fill=hair)
    bw = s * 0.17
    rr = max(1, min(int(s * 0.03), int(bw) - 1))
    d.rounded_rectangle([cx - bw, y + 2 * hr, cx + bw, y + s * 0.60],
                        radius=rr, fill=top)
    d.rectangle([cx - bw * 0.85, y + s * 0.60, cx - bw * 0.08, y + s],
                fill=bottom)
    d.rectangle([cx + bw * 0.08, y + s * 0.60, cx + bw * 0.85, y + s],
                fill=bottom)
    ay = y + 2 * hr + s * 0.05
    aw = max(2, int(s * 0.05))
    if arm == "point":
        d.line([cx + bw * 0.8, ay, cx + bw * 2.1, ay - s * 0.22],
               fill=top, width=aw)
        d.line([cx - bw * 0.8, ay, cx - bw * 1.2, ay + s * 0.18],
               fill=top, width=aw)
    elif arm == "hold":
        d.line([cx + bw * 0.8, ay, cx + bw * 1.1, ay + s * 0.2],
               fill=top, width=aw)
        d.line([cx - bw * 0.8, ay, cx - bw * 1.1, ay + s * 0.2],
               fill=top, width=aw)
    else:
        d.line([cx + bw * 0.9, ay, cx + bw * 1.05, ay + s * 0.22],
               fill=top, width=aw)
        d.line([cx - bw * 0.9, ay, cx - bw * 1.05, ay + s * 0.22],
               fill=top, width=aw)


def draw_badge(d, x, y, n, s=20):
    """Red square with a white story number."""
    d.rectangle([x, y, x + s, y + s], fill=RED)
    f = font(SANS_B, int(s * 0.72))
    t = str(n)
    tw = d.textlength(t, font=f)
    d.text((x + (s - tw) / 2, y + (s - int(s * 0.72)) / 2 - 1), t,
           font=f, fill=(255, 255, 255))

# ---------------------------------------------------------------- scenes
def scene_bridge(d, x, y, w, h):
    """Night skyline, a bridge over the Dnipro, missiles and drones."""
    d.rectangle([x, y, x + w, y + h], fill=(18, 28, 52))
    for sx, sy in [(0.08, 0.18), (0.22, 0.10), (0.38, 0.22), (0.60, 0.12),
                   (0.78, 0.20), (0.92, 0.10), (0.48, 0.08)]:
        d.ellipse([x + w * sx, y + h * sy, x + w * sx + 3, y + h * sy + 3],
                  fill=(255, 255, 255))
    for bx, bw, bh in [(0.02, 0.10, 0.42), (0.15, 0.08, 0.55), (0.28, 0.12, 0.38),
                       (0.62, 0.09, 0.50), (0.76, 0.11, 0.44), (0.90, 0.08, 0.36)]:
        d.rectangle([x + w * bx, y + h * (0.95 - bh), x + w * (bx + bw), y + h * 0.95],
                    fill=(10, 16, 34))
        for wy in range(3):
            d.rectangle([x + w * (bx + 0.02), y + h * (0.95 - bh + 0.05 + wy * 0.09),
                         x + w * (bx + 0.04), y + h * (0.95 - bh + 0.08 + wy * 0.09)],
                        fill=(255, 210, 90))
    d.rectangle([x, y + h * 0.72, x + w, y + h * 0.78], fill=(30, 40, 70))
    d.rectangle([x, y + h * 0.78, x + w, y + h], fill=(12, 22, 44))
    for ax in (0.25, 0.55, 0.82):
        d.arc([x + w * (ax - 0.12), y + h * 0.60, x + w * (ax + 0.12), y + h * 0.92],
              180, 360, fill=(200, 200, 220), width=3)
    for ex, ey in [(0.30, 0.62), (0.68, 0.58)]:
        d.ellipse([x + w * ex - 7, y + h * ey - 7, x + w * ex + 7, y + h * ey + 7],
                  fill=(255, 180, 40))
        d.ellipse([x + w * ex - 3, y + h * ey - 3, x + w * ex + 3, y + h * ey + 3],
                  fill=(255, 230, 120))
    for cx, cy, s in [(0.20, 0.30, 8), (0.45, 0.22, 10), (0.70, 0.34, 7)]:
        px, py = x + w * cx, y + h * cy
        d.ellipse([px - s, py - s * 0.45, px + s, py + s * 0.45], fill=(40, 40, 40))
        d.line([px - s - 6, py - s * 0.4, px + s + 6, py - s * 0.4],
               fill=(40, 40, 40), width=2)
    d.line([x + w * 0.45, y + h * 0.26, x + w * 0.58, y + h * 0.52],
           fill=(255, 255, 255), width=2)
    s = h * 0.30
    draw_person(d, x + w * 0.12, y + h - s, s, top=(70, 85, 55),
                bottom=(50, 50, 50), helmet=(70, 85, 55), arm="point")


def scene_cyclone(d, x, y, w, h):
    """Cyclone spiral over the Bay of Bengal, coast at right, rain."""
    d.rectangle([x, y, x + w, y + h], fill=(205, 225, 238))
    d.polygon([(x + w * 0.68, y), (x + w, y), (x + w, y + h), (x + w * 0.78, y + h),
               (x + w * 0.72, y + h * 0.6)], fill=(222, 205, 160))
    cx, cy = x + w * 0.42, y + h * 0.5
    for r in range(14, 58, 12):
        d.arc([cx - r, cy - r * 0.8, cx + r, cy + r * 0.8], 20, 300,
              fill=(255, 255, 255), width=5)
    d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=RED)
    for i in range(5):
        d.line([x + w * (0.10 + i * 0.12), y + h * 0.12,
                x + w * (0.06 + i * 0.12), y + h * 0.28],
               fill=(150, 180, 210), width=2)
    s = h * 0.34
    draw_person(d, x + w * 0.78, y + h - s, s, top=RED, bottom=(50, 50, 50),
                arm="down")
    d.pieslice([x + w * 0.70, y + h - s - h * 0.16, x + w * 0.86,
                y + h - s + h * 0.02], 180, 360, fill=(31, 111, 178))
    draw_person(d, x + w * 0.92, y + h - s, s, top=(31, 111, 178),
                bottom=(50, 50, 50), arm="down")


def scene_chart(d, x, y, w, h):
    """Falling market chart: bar heights true to the Friday drops
    (Taipei -6.2, Seoul -5.2, Tokyo -5.1, Hong Kong -1.9), one label
    centred under each bar, red trend line diving over the bar tops."""
    d.rectangle([x, y, x + w, y + h], fill=(255, 255, 255))
    d.line([x + w * 0.08, y + h * 0.85, x + w * 0.92, y + h * 0.85],
           fill=RULE, width=2)
    d.line([x + w * 0.08, y + h * 0.85, x + w * 0.08, y + h * 0.10],
           fill=RULE, width=2)
    # heights proportional to the drops, tallest bar 0.75 of the plot
    bars = [(0.08, 0.75, (120, 160, 200), "Taipei -6.2%"),
            (0.29, 0.629, (120, 160, 200), "Seoul -5.2%"),
            (0.50, 0.617, (120, 160, 200), "Tokyo -5.1%"),
            (0.71, 0.230, (200, 60, 50), "HK -1.9%")]
    for bx, bh, c, _lab in bars:
        d.rectangle([x + w * bx, y + h * (0.85 - bh), x + w * (bx + 0.14), y + h * 0.85],
                    fill=c)
    # trend line just above each bar top, arrow at the end
    pts = [(0.15, 0.06), (0.36, 0.18), (0.57, 0.19), (0.78, 0.58)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        d.line([x + w * ax, y + h * ay, x + w * bx, y + h * by],
               fill=RED, width=3)
    d.polygon([(x + w * 0.78, y + h * 0.58), (x + w * 0.70, y + h * 0.58),
               (x + w * 0.78, y + h * 0.48)], fill=RED)
    f = font(SANS_B, 10)
    for bx, _bh, _c, label in bars:
        tw = d.textlength(label, font=f)
        d.text((x + w * (bx + 0.07) - tw / 2, y + h * 0.88), label,
               font=f, fill=INK)

def scene_flags(d, x, y, w, h):
    """UK and EU flags side by side, two figures shaking hands."""
    d.rectangle([x, y, x + w, y + h], fill=(225, 232, 238))
    d.rectangle([x + w * 0.06, y + h * 0.10, x + w * 0.44, y + h * 0.44],
                fill=(40, 70, 140))
    d.line([x + w * 0.06, y + h * 0.27, x + w * 0.44, y + h * 0.27],
           fill=(255, 255, 255), width=6)
    d.line([x + w * 0.25, y + h * 0.10, x + w * 0.25, y + h * 0.44],
           fill=(255, 255, 255), width=6)
    d.line([x + w * 0.06, y + h * 0.27, x + w * 0.44, y + h * 0.27],
           fill=(200, 40, 40), width=2)
    d.line([x + w * 0.25, y + h * 0.10, x + w * 0.25, y + h * 0.44],
           fill=(200, 40, 40), width=2)
    d.rectangle([x + w * 0.56, y + h * 0.10, x + w * 0.94, y + h * 0.44],
                fill=(30, 60, 160))
    for k in range(12):
        ang = 2 * math.pi * k / 12
        sx = x + w * 0.75 + 0.13 * w * 0.62 * math.cos(ang)
        sy = y + h * 0.27 + 0.13 * h * 0.62 * math.sin(ang)
        d.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=(255, 220, 60))
    d.rectangle([x, y + h * 0.82, x + w, y + h], fill=(150, 140, 120))
    s = h * 0.52
    draw_person(d, x + w * 0.36, y + h - s, s, hair=(20, 20, 20),
                top=(30, 30, 30), bottom=(50, 50, 50), arm="hold")
    draw_person(d, x + w * 0.64, y + h - s, s, hair=(230, 200, 120),
                skin=(240, 205, 170), top=(35, 45, 90), bottom=(50, 50, 50),
                arm="hold")
    d.line([x + w * 0.42, y + h - s * 0.42, x + w * 0.58, y + h - s * 0.42],
           fill=(233, 191, 152), width=3)


def scene_globe(d, x, y, w, h):
    """Globe and a red thermometer: climate talks with no deal."""
    d.rectangle([x, y, x + w, y + h], fill=(232, 238, 226))
    cx, cy, r = x + w * 0.34, y + h * 0.48, h * 0.40
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(90, 150, 200))
    d.ellipse([cx - r * 0.55, cy - r * 0.5, cx - r * 0.1, cy - r * 0.05],
              fill=(120, 180, 110))
    d.ellipse([cx + r * 0.05, cy + r * 0.15, cx + r * 0.5, cy + r * 0.55],
              fill=(120, 180, 110))
    d.ellipse([cx - r * 0.2, cy - r * 0.85, cx + r * 0.25, cy - r * 0.45],
              fill=(120, 180, 110))
    d.ellipse([x + w * 0.82, y + h * 0.08, x + w * 0.94, y + h * 0.22],
              fill=(255, 200, 60))
    tx = x + w * 0.66
    d.rectangle([tx, y + h * 0.18, tx + w * 0.05, y + h * 0.72], fill=(255, 255, 255),
                outline=(120, 120, 120))
    d.ellipse([tx - w * 0.02, y + h * 0.68, tx + w * 0.07, y + h * 0.82], fill=RED)
    d.rectangle([tx + 2, y + h * 0.45, tx + w * 0.05 - 2, y + h * 0.72], fill=RED)
    s = h * 0.42
    draw_person(d, x + w * 0.16, y + h - s, s, hair=(120, 120, 120),
                top=(45, 62, 110), bottom=(50, 50, 50), arm="point")


def scene_missile(d, x, y, w, h):
    """Two missiles and a jet-powered drone over a field, one blast."""
    d.rectangle([x, y, x + w, y + h], fill=(214, 230, 240))
    d.rectangle([x, y + h * 0.72, x + w, y + h], fill=(140, 180, 110))
    # drone, top right
    dx, dy = x + w * 0.72, y + h * 0.16
    d.ellipse([dx - 8, dy - 3, dx + 8, dy + 3], fill=(50, 50, 50))
    d.line([dx - 14, dy - 5, dx + 14, dy - 5], fill=(50, 50, 50), width=2)
    d.line([dx - 14, dy + 5, dx + 14, dy + 5], fill=(50, 50, 50), width=2)
    # first missile, upper left, with smoke trail
    d.line([x + w * 0.06, y + h * 0.22, x + w * 0.34, y + h * 0.34],
           fill=(255, 255, 255), width=3)
    mx, my = x + w * 0.34, y + h * 0.34
    d.ellipse([mx - 3, my - 10, mx + 20, my + 3], fill=(90, 90, 90))
    d.polygon([(mx + 17, my - 8), (mx + 27, my - 3), (mx + 17, my + 1)],
              fill=(150, 40, 40))
    # second missile, centre, with smoke trail
    d.line([x + w * 0.30, y + h * 0.42, x + w * 0.56, y + h * 0.52],
           fill=(255, 255, 255), width=3)
    mx2, my2 = x + w * 0.56, y + h * 0.52
    d.ellipse([mx2 - 3, my2 - 10, mx2 + 20, my2 + 3], fill=(90, 90, 90))
    d.polygon([(mx2 + 17, my2 - 8), (mx2 + 27, my2 - 3), (mx2 + 17, my2 + 1)],
              fill=(150, 40, 40))
    d.ellipse([x + w * 0.82, y + h * 0.60, x + w * 0.92, y + h * 0.72],
              fill=(255, 180, 40))
    d.ellipse([x + w * 0.85, y + h * 0.63, x + w * 0.89, y + h * 0.69],
              fill=(255, 230, 120))
    s = h * 0.40
    draw_person(d, x + w * 0.12, y + h - s, s, top=(70, 85, 55),
                bottom=(50, 50, 50), helmet=(70, 85, 55), arm="point")


def scene_tank(d, x, y, w, h):
    """Desert, a tank, sun, one soldier."""
    d.rectangle([x, y, x + w, y + h], fill=(228, 222, 200))
    d.ellipse([x + w * 0.80, y + h * 0.10, x + w * 0.92, y + h * 0.26],
              fill=(255, 200, 60))
    d.rectangle([x, y + h * 0.72, x + w, y + h], fill=(190, 175, 140))
    d.rectangle([x + w * 0.18, y + h * 0.50, x + w * 0.72, y + h * 0.74],
                fill=(70, 85, 55))
    d.rectangle([x + w * 0.38, y + h * 0.34, x + w * 0.58, y + h * 0.52],
                fill=(80, 95, 62))
    d.line([x + w * 0.58, y + h * 0.40, x + w * 0.88, y + h * 0.36],
           fill=(60, 72, 48), width=5)
    for i in range(4):
        d.ellipse([x + w * (0.22 + i * 0.13), y + h * 0.70,
                   x + w * (0.32 + i * 0.13), y + h * 0.82], fill=(50, 50, 50))
    s = h * 0.44
    draw_person(d, x + w * 0.10, y + h - s, s, top=(70, 85, 55),
                bottom=(60, 70, 50), helmet=(70, 85, 55), arm="down")


def scene_pill(d, x, y, w, h):
    """A capsule pill and tumour cells shrinking away: daraxonrasib."""
    d.rectangle([x, y, x + w, y + h], fill=(232, 238, 226))
    # capsule, horizontal, centre-left
    cx, cy = x + w * 0.38, y + h * 0.50
    r = h * 0.30
    lw = w * 0.28
    d.rounded_rectangle([cx - lw, cy - r, cx + lw, cy + r], radius=int(r),
                        fill=(255, 255, 255), outline=(120, 120, 120))
    d.pieslice([cx - lw - r, cy - r, cx - lw + r, cy + r], 90, 270, fill=RED)
    d.rectangle([cx - lw, cy - r, cx, cy + r], fill=RED)
    # tumour cells shrinking to nothing, left to right
    for fx, fr in [(0.72, 0.15), (0.82, 0.10), (0.91, 0.05)]:
        d.ellipse([x + w * fx - h * fr, y + h * 0.5 - h * fr,
                   x + w * fx + h * fr, y + h * 0.5 + h * fr],
                  fill=(120, 60, 90))


def scene_yen(d, x, y, w, h):
    """Rising bars, a red sun disc and a big yen sign: Japan prices."""
    d.rectangle([x, y, x + w, y + h], fill=(255, 255, 255))
    d.ellipse([x + w * 0.72, y + h * 0.08, x + w * 0.94, y + h * 0.34],
              fill=(200, 40, 40))
    d.line([x + w * 0.08, y + h * 0.85, x + w * 0.92, y + h * 0.85],
           fill=RULE, width=2)
    bars = [(0.14, 0.22, (120, 160, 200)), (0.32, 0.34, (120, 160, 200)),
            (0.50, 0.48, (120, 160, 200)), (0.68, 0.62, (200, 60, 50))]
    for bx, bh, c in bars:
        d.rectangle([x + w * bx, y + h * (0.85 - bh), x + w * (bx + 0.12), y + h * 0.85],
                    fill=c)
    f = font(SERIF_B, int(h * 0.30))
    d.text((x + w * 0.10, y + h * 0.06), "¥", font=f, fill=INK)


def scene_parliament(d, x, y, w, h):
    """A parliament building with columns and a dome."""
    d.rectangle([x, y, x + w, y + h], fill=(226, 230, 232))
    d.ellipse([x + w * 0.80, y + h * 0.08, x + w * 0.92, y + h * 0.24],
              fill=(255, 200, 60))
    d.rectangle([x + w * 0.14, y + h * 0.52, x + w * 0.86, y + h * 0.86],
                fill=(200, 195, 185))
    for i in range(5):
        d.rectangle([x + w * (0.18 + i * 0.14), y + h * 0.56,
                     x + w * (0.24 + i * 0.14), y + h * 0.82],
                    fill=(255, 255, 255), outline=(150, 150, 150))
    d.polygon([(x + w * 0.12, y + h * 0.52), (x + w * 0.50, y + h * 0.30),
               (x + w * 0.88, y + h * 0.52)], fill=(180, 175, 165))
    d.pieslice([x + w * 0.42, y + h * 0.18, x + w * 0.58, y + h * 0.42],
               180, 360, fill=(90, 110, 140))
    d.rectangle([x, y + h * 0.86, x + w, y + h], fill=(150, 150, 150))
    s = h * 0.38
    draw_person(d, x + w * 0.30, y + h - s, s, hair=(20, 20, 20),
                top=(30, 30, 30), bottom=(50, 50, 50), arm="down")
    draw_person(d, x + w * 0.68, y + h - s, s, hair=(230, 200, 120),
                skin=(240, 205, 170), top=(35, 45, 90), bottom=(50, 50, 50),
                arm="hold")


def scene_oil(d, x, y, w, h):
    """An oil derrick at sunset, first crude in Kenya."""
    d.rectangle([x, y, x + w, y + h], fill=(245, 225, 180))
    d.ellipse([x + w * 0.70, y + h * 0.10, x + w * 0.90, y + h * 0.34],
              fill=(255, 170, 40))
    d.rectangle([x, y + h * 0.78, x + w, y + h], fill=(190, 160, 110))
    d.polygon([(x + w * 0.30, y + h * 0.78), (x + w * 0.42, y + h * 0.18),
               (x + w * 0.54, y + h * 0.18), (x + w * 0.66, y + h * 0.78)],
              fill=(40, 40, 40))
    d.line([x + w * 0.48, y + h * 0.18, x + w * 0.48, y + h * 0.78],
           fill=(40, 40, 40), width=3)
    d.line([x + w * 0.34, y + h * 0.62, x + w * 0.62, y + h * 0.62],
           fill=(40, 40, 40), width=3)
    d.ellipse([x + w * 0.78, y + h * 0.66, x + w * 0.86, y + h * 0.76],
              fill=(30, 30, 30))
    s = h * 0.36
    draw_person(d, x + w * 0.16, y + h - s, s, top=(200, 140, 60),
                bottom=(60, 60, 60), helmet=(200, 140, 60), arm="point")


def scene_ballot(d, x, y, w, h):
    """A hand dropping a ballot into a blue ballot box."""
    d.rectangle([x, y, x + w, y + h], fill=(232, 238, 226))
    d.rectangle([x + w * 0.22, y + h * 0.48, x + w * 0.78, y + h * 0.86],
                fill=(31, 111, 178))
    d.rectangle([x + w * 0.18, y + h * 0.42, x + w * 0.82, y + h * 0.52],
                fill=(20, 80, 140))
    d.rectangle([x + w * 0.44, y + h * 0.46, x + w * 0.56, y + h * 0.48],
                fill=(10, 10, 10))
    d.rectangle([x + w * 0.40, y + h * 0.18, x + w * 0.60, y + h * 0.44],
                fill=(255, 255, 255), outline=(120, 120, 120))
    f = font(SANS_B, max(10, int(h * 0.12)))
    d.text((x + w * 0.44, y + h * 0.24), "✓", font=f, fill=(30, 132, 73))
    d.ellipse([x + w * 0.80, y + h * 0.08, x + w * 0.94, y + h * 0.26],
              fill=(255, 200, 60))
    s = h * 0.40
    draw_person(d, x + w * 0.50, y + h * 0.06, s, top=(192, 57, 43),
                bottom=(50, 50, 50), arm="hold")


def scene_march(d, x, y, w, h):
    """A street march: five figures with placards, one red banner."""
    d.rectangle([x, y, x + w, y + h], fill=(232, 232, 228))
    d.rectangle([x, y + h * 0.82, x + w, y + h], fill=(150, 140, 120))
    d.rectangle([x + w * 0.08, y + h * 0.06, x + w * 0.92, y + h * 0.20],
                fill=RED)
    tops = [(45, 62, 110), (192, 57, 43), (30, 132, 73), (123, 45, 139),
            (181, 137, 0)]
    s = h * 0.52
    for i, top in enumerate(tops):
        cx = x + w * (0.14 + i * 0.18)
        draw_person(d, cx, y + h - s, s, top=top, bottom=(50, 50, 50),
                    arm="hold")
        # placard on a stick above the figure's head
        px = cx - w * 0.07
        py = y + h - s - h * 0.22
        d.line([cx, py + h * 0.14, cx, y + h - s + h * 0.10],
               fill=(90, 90, 90), width=2)
        d.rectangle([px, py, px + w * 0.14, py + h * 0.14],
                    fill=(255, 255, 255), outline=(120, 120, 120))


def scene_cricket(d, x, y, w, h):
    """A cricket pitch: stumps, a batsman, a red ball, and 118."""
    d.rectangle([x, y, x + w, y + h], fill=(150, 190, 110))
    d.rectangle([x + w * 0.30, y, x + w * 0.70, y + h], fill=(222, 205, 160))
    d.rectangle([x, y + h * 0.88, x + w, y + h], fill=(120, 160, 90))
    for i in range(3):
        sx = x + w * (0.60 + i * 0.03)
        d.rectangle([sx, y + h * 0.14, sx + 3, y + h * 0.34],
                    fill=(255, 220, 60))
    d.ellipse([x + w * 0.84, y + h * 0.55, x + w * 0.90, y + h * 0.63],
              fill=(200, 40, 40))
    s = h * 0.55
    draw_person(d, x + w * 0.40, y + h - s, s, top=(255, 255, 255),
                bottom=(50, 50, 50), helmet=(30, 30, 30), arm="hold")
    d.line([x + w * 0.46, y + h - s * 0.55, x + w * 0.58, y + h - s * 0.10],
           fill=(160, 110, 60), width=4)
    f = font(SANS_B, max(12, int(h * 0.34)))
    d.text((x + w * 0.10, y + h * 0.06), "118", font=f, fill=INK)

# ---------------------------------------------------------------- world map
# Simplified continent outlines (lon, lat). Rough on purpose: the map is
# small, it only has to read as a world map with pins on it.
CONTINENTS = [
    [(-168, 66), (-150, 70), (-130, 71), (-110, 72), (-95, 80), (-85, 78),
     (-80, 73), (-70, 62), (-60, 60), (-55, 52), (-60, 47), (-65, 44),
     (-70, 42), (-75, 38), (-76, 35), (-80, 32), (-81, 26), (-84, 30),
     (-90, 29), (-95, 28), (-97, 25), (-100, 22), (-105, 20), (-110, 23),
     (-115, 28), (-120, 33), (-124, 40), (-125, 48), (-130, 55), (-140, 60),
     (-150, 61), (-160, 58), (-165, 60)],
    [(-79, 9), (-72, 11), (-62, 10), (-55, 6), (-50, 0), (-45, -3),
     (-38, -5), (-35, -8), (-38, -15), (-40, -22), (-48, -28), (-55, -33),
     (-62, -38), (-68, -40), (-70, -48), (-72, -54), (-75, -50), (-73, -40),
     (-72, -30), (-75, -20), (-80, -12), (-81, -5), (-80, 2)],
    [(-17, 15), (-15, 22), (-10, 29), (-5, 35), (0, 36), (10, 37), (15, 35),
     (20, 32), (25, 31), (30, 31), (35, 28), (38, 22), (40, 15), (43, 11),
     (48, 11), (51, 12), (46, 5), (42, 0), (40, -5), (38, -12), (35, -18),
     (33, -25), (30, -30), (25, -34), (20, -35), (17, -32), (15, -27),
     (13, -18), (12, -12), (10, -5), (9, 2), (5, 4), (-2, 5), (-8, 5),
     (-13, 8), (-17, 12)],
    [(-10, 36), (-9, 39), (-9, 43), (-4, 44), (-2, 47), (-1, 49), (0, 51),
     (2, 52), (5, 54), (7, 56), (8, 58), (10, 59), (12, 58), (15, 57),
     (18, 56), (20, 55), (22, 56), (24, 58), (26, 59), (28, 60), (30, 62),
     (28, 65), (25, 68), (22, 70), (18, 69), (14, 67), (12, 64), (8, 62),
     (6, 58), (4, 55), (2, 52), (0, 49), (-3, 47), (-5, 44), (-8, 40),
     (-10, 38)],
    [(28, 62), (32, 66), (38, 68), (45, 68), (55, 69), (65, 70), (75, 72),
     (85, 73), (95, 75), (105, 76), (115, 74), (125, 72), (135, 72),
     (145, 71), (155, 70), (165, 68), (175, 66), (178, 65), (172, 62),
     (165, 60), (160, 56), (155, 52), (150, 48), (145, 45), (140, 42),
     (135, 38), (130, 35), (128, 34), (126, 36), (122, 32), (120, 28),
     (118, 25), (112, 22), (108, 18), (105, 12), (102, 8), (100, 10),
     (97, 15), (94, 18), (90, 22), (87, 21), (84, 19), (81, 16), (78, 12),
     (76, 10), (74, 15), (72, 20), (69, 23), (66, 25), (62, 25), (58, 26),
     (55, 27), (52, 29), (50, 30), (48, 29), (46, 30), (44, 29), (42, 28),
     (40, 30), (38, 32), (36, 36), (34, 36), (32, 38), (30, 40), (28, 42),
     (28, 45), (28, 50), (28, 55), (28, 60)],
    [(113, -22), (114, -28), (115, -33), (118, -35), (122, -34), (126, -32),
     (130, -32), (133, -35), (136, -36), (140, -38), (144, -39), (147, -39),
     (150, -37), (152, -35), (153, -32), (153, -28), (152, -24), (150, -22),
     (147, -19), (144, -16), (142, -12), (141, -14), (138, -15), (136, -12),
     (134, -12), (132, -12), (130, -13), (128, -14), (125, -16), (122, -18),
     (119, -20), (116, -21), (113, -22)],
]

# Display positions (lon, lat) for the 14 main stories. Hand-nudged so the
# Europe cluster and the Seoul/Tokyo/Taipei cluster do not overlap.
PIN_POS = {
    1: (36, 54), 2: (85, 19), 3: (118, 22), 4: (0, 55), 5: (34, 37),
    6: (20, 58), 7: (48, 30), 8: (2.2, 41.4), 9: (142, 33), 10: (124, 41),
    11: (35.5, 3.5), 12: (-89, 14), 13: (10, 42), 14: (175, -41),
}


def draw_map(d, x, y, w, h, panels):
    """World map with numbered pins for the 3 heroes and dots for cards."""
    d.rectangle([x, y, x + w, y + h], fill=CARD, outline=CARD_LINE, width=1)
    f_t = font(SANS_B, 10)
    d.text((x + 6, y + 3), "WHERE THE NEWS HAPPENED", font=f_t, fill=INK)
    mx, my, mw, mh = x + 6, y + 16, w - 12, h - 28
    d.rectangle([mx, my, mx + mw, my + mh], fill=SKY)
    def proj(lon, lat):
        return (mx + (lon + 170) / 360.0 * mw,
                my + (75 - lat) / 130.0 * mh)
    for poly in CONTINENTS:
        pts = [proj(lon, lat) for lon, lat in poly]
        d.polygon(pts, fill=LAND, outline=LAND_LINE)
    for s in panels:
        px, py = proj(*PIN_POS[s["n"]])
        if s["n"] <= 3:
            d.ellipse([px - 6, py - 6, px + 6, py + 6], fill=RED,
                      outline=(255, 255, 255))
            f_n = font(SANS_B, 8)
            t = str(s["n"])
            d.text((px - d.textlength(t, font=f_n) / 2, py - 5), t,
                   font=f_n, fill=(255, 255, 255))
        else:
            d.ellipse([px - 3.5, py - 3.5, px + 3.5, py + 3.5],
                      fill=REGION_FILL[s["region"]],
                      outline=(255, 255, 255))
    f_l = font(SANS, 8)
    leg = "1-3 TOP STORIES  ·  DOTS = OTHER STORIES"
    d.text((x + (w - d.textlength(leg, font=f_l)) / 2, y + h - 10), leg,
           font=f_l, fill=GRAY)

# ---------------------------------------------------------------- data
MASTHEAD = "Friday 20 November 2026"
KICKER_LEFT = "THE WORLD IN ONE DAY"
KICKER_BADGE = "FRIDAY 20 NOV 2026"
KICKER_RIGHT = "44 STORIES · 7 REGIONS · 14 DRAWN · ONE PAGE"
SUBHEAD = ("Russian missiles hit Kyiv's bridges · Cyclone Akvan strikes India · "
           "An AI sell-off sinks Asia's markets")

NUMBERS = [
    ("~110", "missiles fired at Ukraine", "Zelenskyy"),
    ("300,000+", "people moved to shelters", "IMD, Odisha"),
    ("-6.2%", "Taiwan's index, Friday", "Taiwan Stock Exchange"),
    ("100,000", "youth visas a year", "UK-EU deal"),
    ("118", "Phillips hits 118 v India", "ICC"),
    ("2.3%", "Japan CPI, October", "Statistics Bureau"),
]

# region, count — sums to 44 stories
REGIONS = [
    ("EUROPE", 11), ("ASIA", 14), ("MIDDLE EAST", 4), ("AFRICA", 4),
    ("AMERICAS", 7), ("OCEANIA", 2), ("GLOBAL", 2),
]

HEROES = [
    {"n": 1, "label": "KYIV", "region": "EUROPE", "tag": "WAR",
     "place": "KYIV, UKRAINE", "art": "bridge", "verdict": "CONFIRMED",
     "headline": "Russian missiles hit three Kyiv bridges",
     "summary": ("About 110 missiles and 400 drones killed at least eight "
                 "people and cut power and water in the capital."),
     "source": "Kyiv Independent, BBC"},
    {"n": 2, "label": "CYCLONE AKVAN", "region": "ASIA", "tag": "CYCLONE",
     "place": "ODISHA, INDIA", "art": "cyclone", "verdict": "CONFIRMED",
     "headline": "Cyclone Akvan comes ashore in eastern India",
     "summary": ("It crossed the coast near Gopalpur after 300,000+ people "
                 "were moved to shelters. No deaths were reported."),
     "source": "IMD, Deccan Herald"},
    {"n": 3, "label": "AI SELL-OFF", "region": "ASIA", "tag": "MARKETS",
     "place": "TAIPEI · SEOUL · TOKYO · HK", "art": "chart",
     "verdict": "CONFIRMED", "label_top": True,
     "headline": "AI sell-off sinks Asia's stock markets",
     "summary": ("Taiwan fell 6.2%, its worst week since 1991. Seoul -5.2%, "
                 "Tokyo -5.1%, HK -1.9%."),
     "source": "Al Jazeera, Anadolu"},
]

CARDS = [
    {"n": 4, "region": "EUROPE", "tag": "DIPLOMACY", "place": "BRUSSELS",
     "art": "flags", "verdict": "CONFIRMED", "label": "UK-EU DEAL",
     "headline": "UK and EU seal a \u201creset\u201d deal",
     "summary": "Food trade, youth visas, carbon link.",
     "source": "Reuters"},
    {"n": 5, "region": "GLOBAL", "tag": "CLIMATE", "place": "ANTALYA",
     "art": "globe", "verdict": "CONFIRMED", "label": "COP31: NO DEAL",
     "headline": "COP31 reaches its last day with no deal",
     "summary": "The draft text leaves out fossil fuels.",
     "source": "UN News"},
    {"n": 6, "region": "EUROPE", "tag": "SECURITY", "place": "POLAND",
     "art": "missile", "verdict": "REPORTED", "label": "POLAND: MISSILES",
     "headline": "Russian missiles crash in eastern Poland",
     "summary": "Two missiles, a drone; 2 airports paused.",
     "source": "Reuters"},
    {"n": 7, "region": "MIDDLE EAST", "tag": "SECURITY", "place": "CENTRAL IRAQ",
     "art": "tank", "verdict": "CONFIRMED", "label": "IRAQ: RAID",
     "headline": "Iraqi army enters a militia stronghold",
     "summary": "Troops deploy to Jurf al-Sakhar.",
     "source": "Reuters"},
    {"n": 8, "region": "EUROPE", "tag": "HEALTH", "place": "BARCELONA",
     "art": "pill", "verdict": "REPORTED", "label": "CANCER: PILL",
     "headline": "Pancreatic cancer pill shrinks tumours in early trial",
     "summary": "Tumours vanished in 8.2% of 61 patients.",
     "source": "EORTC"},
    {"n": 9, "region": "ASIA", "tag": "ECONOMY", "place": "TOKYO",
     "art": "yen", "verdict": "CONFIRMED", "label": "JAPAN: CPI 2.3%",
     "headline": "Japan's inflation picks up to 2.3%",
     "summary": "A December rate rise stays in view.",
     "source": "Reuters"},
    {"n": 10, "region": "ASIA", "tag": "POLITICS", "place": "SEOUL",
     "art": "parliament", "verdict": "CONFIRMED", "label": "SEOUL: IMPEACH",
     "headline": "Korea's ruling party to impeach top judge",
     "summary": "It follows an overturned conviction.",
     "source": "Yonhap"},
    {"n": 11, "region": "AFRICA", "tag": "ENERGY", "place": "KENYA",
     "art": "oil", "verdict": "REPORTED", "label": "KENYA: OIL",
     "headline": "Kenya starts drilling its first oil well",
     "summary": "First crude is due on 1 December.",
     "source": "allAfrica"},
    {"n": 12, "region": "AMERICAS", "tag": "POLITICS", "place": "SAN SALVADOR",
     "art": "ballot", "verdict": "CONFIRMED", "label": "BUKELE: 3RD BID",
     "headline": "Bukele launches third-term bid",
     "summary": "The vote is on 28 February 2027.",
     "source": "AP"},
    {"n": 13, "region": "EUROPE", "tag": "STRIKE", "place": "ROME",
     "art": "march", "verdict": "CONFIRMED", "label": "ITALY: STRIKE",
     "headline": "General strike grips Italy",
     "summary": "Workers, students march in 100 cities.",
     "source": "Reuters"},
    {"n": 14, "region": "OCEANIA", "tag": "SPORT", "place": "WELLINGTON",
     "art": "cricket", "verdict": "CONFIRMED", "label": "PHILLIPS: 118",
     "headline": "Phillips hits 118 against India",
     "summary": "Hundreds in all three formats v India.",
     "source": "ICC"},
]

# (number, city, text, source, region) — 30 briefs, numbers 15-44
BRIEFS = [
    (15, "Lviv", "A strike on a railway station kills two.", "BBC", "EUROPE"),
    (16, "Tallinn", "Estonia to close Russia border 1 Dec.", "Reuters", "EUROPE"),
    (17, "Berlin", "Pupils strike over military service.", "Al Jazeera", "EUROPE"),
    (18, "London", "General says UK runs cyber attacks abroad.", "Sky News", "EUROPE"),
    (19, "Turin", "ATP agrees a $350m pay plan.", "ATP", "EUROPE"),
    (20, "London", "Tuition-fee row still open in EU deal.", "Reuters", "EUROPE"),
    (21, "New York", "S&P 500 falls 3.7% as Nasdaq drops 5.3%.", "AP", "AMERICAS"),
    (22, "Beijing", "China holds its loan rates for an 18th month.", "Xinhua", "ASIA"),
    (23, "Khasab", "Tanker hit by projectile in Hormuz strait.", "UKMTO", "MIDDLE EAST"),
    (24, "Kolkata", "Heavy rain floods streets.", "IMD", "ASIA"),
    (25, "Mumbai", "Sensex climbs 1.1% in a day.", "Gujarat Samachar", "ASIA"),
    (26, "Taipei", "TSMC shares fall 4.8%.", "Gujarat Samachar", "ASIA"),
    (27, "Tokyo", "SoftBank shares fall over 14% in a day.", "Al Jazeera", "ASIA"),
    (28, "Tokyo", "Core prices rise 2.2% in October.", "Reuters", "ASIA"),
    (29, "Seoul", "Kospi index ends the week 7.9% lower.", "Anadolu", "ASIA"),
    (30, "Brasília", "Bolsonaro in hospital with abdominal pain.", "Reuters", "AMERICAS"),
    (31, "Seoul", "111 cheating cases in college exam.", "Yonhap", "ASIA"),
    (32, "Lebanon", "Israeli strikes hit the south and east.", "Anadolu", "MIDDLE EAST"),
    (33, "Yemen", "Gunmen fire on a cargo ship off the coast.", "UKMTO", "MIDDLE EAST"),
    (34, "Abuja", "Court bars new evidence against Tinubu.", "Channels TV", "AFRICA"),
    (35, "Malawi", "Fuel crisis brings petrol queues.", "Al Jazeera", "AFRICA"),
    (36, "Abidjan", "22 African states in or near debt distress.", "AfDB", "AFRICA"),
    (37, "Delhi", "Pakistan minister visits, first since 2025 war.", "Al Jazeera", "ASIA"),
    (38, "Antalya", "Panama asks COP31 to cap world oil output.", "Anadolu", "GLOBAL"),
    (39, "New York", "Nvidia plunges 14% on SEC probe reports.", "Reuters", "AMERICAS"),
    (40, "New York", "Nasdaq futures fall 1.6% before the bell.", "24/7 Wall St", "AMERICAS"),
    (41, "Washington", "Democrats query law firm's free work.", "Al Jazeera", "AMERICAS"),
    (42, "Las Vegas", "Russell fastest in wet practice.", "Autosport", "AMERICAS"),
    (43, "Shenzhen", "Xi hails turnaround in China-Australia ties.", "Xinhua", "ASIA"),
    (44, "Sydney", "Australian shares fall 1.8% in the sell-off.", "Reuters", "OCEANIA"),
]

# (UTC time, label) — all four markers verified against sources
UTC_STRIP = [
    ("02:30", "Akvan lands"), ("05:30", "Taipei closes"),
    ("06:30", "Tokyo · Seoul close"), ("15:00", "COP31 runs past close"),
]

DATE_CHECK = ("Left out — Thu 19 Nov: ICJ ruling on Myanmar; Shenzhen "
              "declaration; Tonga drought emergency; Anthropic $83 IPO; "
              "GTA VI; Uganda Ebola rally ban. Not yet: BepiColombo Mercury "
              "orbit; COP31 final text.")
FOOTER = ("Every story here happened, or was first reported, on Friday "
          "20 November 2026. Sources named beside each story · original "
          "drawings · CONFIRMED = widely reported · REPORTED = single-source claim")

SCENES = {
    "bridge": scene_bridge, "cyclone": scene_cyclone, "chart": scene_chart,
    "flags": scene_flags, "globe": scene_globe, "missile": scene_missile,
    "tank": scene_tank, "pill": scene_pill, "yen": scene_yen,
    "parliament": scene_parliament, "oil": scene_oil, "ballot": scene_ballot,
    "march": scene_march, "cricket": scene_cricket,
}

# ---------------------------------------------------------------- page
def draw_tag_line(d, x, y, s, size, with_source=False):
    """N · PLACE · CONFIRMED/REPORTED · source, segments in own colours."""
    f_b = font(SANS_B, size)
    f_r = font(SANS, size)
    cx = x
    num = "%d · " % s["n"]
    d.text((cx, y), num, font=f_b, fill=RED)
    cx += d.textlength(num, font=f_b)
    place = "%s · " % s["place"]
    d.text((cx, y), place, font=f_b, fill=INK)
    cx += d.textlength(place, font=f_b)
    verdict = s["verdict"]
    vc = GREEN if verdict == "CONFIRMED" else RED
    vtxt = verdict + (" · " if with_source else "")
    d.text((cx, y), vtxt, font=f_b, fill=vc)
    cx += d.textlength(vtxt, font=f_b)
    if with_source:
        d.text((cx, y), s["source"], font=f_r, fill=GRAY)


def draw_hero(d, s, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=CARD, outline=CARD_LINE, width=1)
    art_h = 112
    SCENES[s["art"]](d, x + 1, y + 1, w - 2, art_h - 1)
    draw_badge(d, x + 1, y + 1, s["n"], 22)
    f_lab = font(SANS_B, 20)
    lab = s["label"]
    lw = d.textlength(lab, font=f_lab)
    if s.get("label_top"):
        # top-right corner, clear of the chart axis and bar labels
        lx = x + w - 8 - lw - 16
        d.rectangle([lx, y + 8, lx + lw + 16, y + 36], fill=RED)
        d.text((lx + 8, y + 10), lab, font=f_lab, fill=(255, 255, 255))
    else:
        d.rectangle([x + 8, y + art_h - 34, x + 8 + lw + 16, y + art_h - 6], fill=RED)
        d.text((x + 16, y + art_h - 32), lab, font=f_lab, fill=(255, 255, 255))
    ty = y + art_h + 6
    draw_tag_line(d, x + 6, ty, s, 11)
    hy = ty + 15
    f_head = font(SERIF_B, 21)
    hl = fit_text(d, s["headline"], f_head, w - 12, 3)
    for i, line in enumerate(hl):
        d.text((x + 6, hy + i * 24), line, font=f_head, fill=INK)
    sy = hy + len(hl) * 24 + 2
    f_sum = font(SANS, 12)
    sl = fit_text(d, s["summary"], f_sum, w - 12, 2)
    for i, line in enumerate(sl):
        d.text((x + 6, sy + i * 15), line, font=f_sum, fill=(60, 60, 60))
    f_src = font(SANS, 10)
    d.text((x + 6, y + h - 16), s["source"], font=f_src, fill=GRAY)


def draw_card(d, s, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=CARD, outline=CARD_LINE, width=1)
    art_h = 38
    SCENES[s["art"]](d, x + 1, y + 1, w - 2, art_h - 1)
    draw_badge(d, x + 1, y + 1, s["n"], 18)
    # red 2-3 word label on the art, bottom-left (top-10 style)
    f_cl = font(SANS_B, 11)
    lab = s["label"]
    llw = d.textlength(lab, font=f_cl)
    d.rectangle([x + 1, y + art_h - 17, x + 1 + llw + 10, y + art_h - 1],
                fill=RED)
    d.text((x + 6, y + art_h - 16), lab, font=f_cl, fill=(255, 255, 255))
    ty = y + art_h + 4
    draw_tag_line(d, x + 6, ty, s, 10, with_source=True)
    hy = ty + 13
    f_head = font(SERIF_B, 17)
    hl = fit_text(d, s["headline"], f_head, w - 12, 2)
    for i, line in enumerate(hl):
        d.text((x + 6, hy + i * 19), line, font=f_head, fill=INK)
    sy = hy + len(hl) * 19 + 1
    f_sum = font(SANS, 11)
    sl = fit_text(d, s["summary"], f_sum, w - 12, 1)
    if sl:
        d.text((x + 6, sy), sl[0], font=f_sum, fill=(60, 60, 60))


def main():
    total = len(HEROES) + len(CARDS) + len(BRIEFS)
    assert sum(c for _, c in REGIONS) == total, "region bar must sum to %d" % total
    assert total == 44, "expected 44 stories, got %d" % total
    assert len(SCENES) == 14, "expected 14 illustrations"
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    M = 14
    cw = W - 2 * M
    y = M
    # kicker: left text, red date badge in the centre, right counts
    f_k = font(SANS_B, 13)
    d.text((M, y), KICKER_LEFT, font=f_k, fill=RED)
    f_badge = font(SANS_B, 12)
    bw = d.textlength(KICKER_BADGE, font=f_badge) + 18
    bx = (W - bw) / 2
    d.rectangle([bx, y - 1, bx + bw, y + 15], fill=RED)
    d.text((bx + 9, y + 1), KICKER_BADGE, font=f_badge, fill=(255, 255, 255))
    rt = KICKER_RIGHT
    d.text((W - M - d.textlength(rt, font=f_k), y), rt, font=f_k, fill=INK)
    y += 16
    # masthead
    f_m = font(SERIF_B, 56)
    mt = MASTHEAD
    d.text(((W - d.textlength(mt, font=f_m)) / 2, y), mt, font=f_m, fill=INK)
    y += 60
    d.rectangle([M, y, W - M, y + 2], fill=RED)
    y += 6
    # subhead
    f_s = font(SERIF_I, 16)
    st = SUBHEAD
    d.text(((W - d.textlength(st, font=f_s)) / 2, y), st, font=f_s, fill=INK)
    y += 20
    # THE DAY IN UTC strip: 4 verified markers on one line
    f_u = font(SANS_B, 10)
    f_ul = font(SANS, 9)
    d.text((M, y + 2), "THE DAY IN UTC", font=f_u, fill=RED)
    line_x0 = M + 105
    line_x1 = W - M
    ly = y + 20
    d.line([line_x0, ly, line_x1, ly], fill=(200, 195, 185), width=1)
    slot = (line_x1 - line_x0) / len(UTC_STRIP)
    for i, (t, lab) in enumerate(UTC_STRIP):
        cx = line_x0 + slot * (i + 0.5)
        d.ellipse([cx - 3, ly - 3, cx + 3, ly + 3], fill=RED)
        d.text((cx - d.textlength(t, font=f_u) / 2, y + 4), t, font=f_u, fill=INK)
        d.text((cx - d.textlength(lab, font=f_ul) / 2, ly + 5), lab,
               font=f_ul, fill=(60, 60, 60))
    y += 34
    # numbers strip: 6 big numbers, one value + one source each
    col_w = cw / 6
    f_num = font(SANS_B, 26)
    f_lab = font(SANS, 11)
    f_src = font(SANS, 10)
    ny = y
    for i, (num, lab, src) in enumerate(NUMBERS):
        cx = M + i * col_w
        if i:
            d.line([cx - 6, ny + 2, cx - 6, ny + 52], fill=(200, 195, 185), width=1)
        d.text((cx, ny), num, font=f_num, fill=RED)
        d.text((cx, ny + 30), lab, font=f_lab, fill=INK)
        d.text((cx, ny + 42), src, font=f_src, fill=GRAY)
    y += 56
    # region bar
    f_r = font(SANS_B, 12)
    seg = cw / len(REGIONS)
    for i, (name, cnt) in enumerate(REGIONS):
        sx = M + i * seg
        d.rectangle([sx, y, sx + seg - 1, y + 20], fill=REGION_FILL[name])
        t = "%s %d" % (name, cnt)
        d.text((sx + (seg - d.textlength(t, font=f_r)) / 2, y + 3), t,
               font=f_r, fill=(255, 255, 255))
    y += 20
    # heroes: 3 large cards
    y += 4
    gap = 8
    hero_h = 230
    lw = (cw - 2 * gap) / 3
    for i, s in enumerate(HEROES):
        draw_hero(d, s, M + i * (lw + gap), y, lw, hero_h)
    y += hero_h + gap
    # cards: rows of 4, 4, then 3 cards + the world map
    row_h = 108
    cw4 = (cw - 3 * gap) / 4
    for i, s in enumerate(CARDS[0:4]):
        draw_card(d, s, M + i * (cw4 + gap), y, cw4, row_h)
    y += row_h + gap
    for i, s in enumerate(CARDS[4:8]):
        draw_card(d, s, M + i * (cw4 + gap), y, cw4, row_h)
    y += row_h + gap
    for i, s in enumerate(CARDS[8:11]):
        draw_card(d, s, M + i * (cw4 + gap), y, cw4, row_h)
    draw_map(d, M + 3 * (cw4 + gap), y, cw4, row_h, HEROES + CARDS)
    y += row_h + 4
    # briefs title
    f_t = font(SERIF_B, 14)
    d.text((M, y), "ALSO ON FRIDAY 20 NOVEMBER \u2014 30 MORE STORIES",
           font=f_t, fill=INK)
    y += 16
    # briefs: 3 columns x 10 rows, one line each
    bw3 = (cw - 2 * gap) / 3
    f_b = font(SANS, 10)
    f_bb = font(SANS_B, 10)
    for c in range(3):
        bx = M + c * (bw3 + gap)
        for r in range(10):
            n, lead, text, src, _reg = BRIEFS[c * 10 + r]
            by = y + r * 14
            d.text((bx, by), str(n), font=f_bb, fill=RED)
            tx = bx + d.textlength(str(n) + " ", font=f_bb)
            d.text((tx, by), lead + ": ", font=f_bb, fill=INK)
            lx = tx + d.textlength(lead + ": ", font=f_bb)
            d.text((lx, by), text, font=f_b, fill=INK)
            ex = lx + d.textlength(text + " ", font=f_b)
            d.text((ex, by), "(%s)" % src, font=f_b, fill=GRAY)
    y += 10 * 14 + 4
    # date check box (readable, two lines)
    f_dc = font(SANS, 11)
    f_dcb = font(SANS_B, 11)
    d.rectangle([M, y, W - M, y + 30], outline=RED, width=2)
    d.text((M + 8, y + 3), "DATE CHECK:", font=f_dcb, fill=RED)
    dx = M + 8 + d.textlength("DATE CHECK: ", font=f_dcb)
    dl = fit_text(d, DATE_CHECK, f_dc, W - M - 8 - dx, 2)
    for i, line in enumerate(dl):
        d.text((dx, y + 3 + i * 14), line, font=f_dc, fill=INK)
    y += 30 + 4
    # footer
    f_ft = font(SANS, 9)
    d.text((M, y), FOOTER, font=f_ft, fill=GRAY)
    y += 12
    out = os.path.join(HERE, "entry.png")
    img.save(out, optimize=True)
    print("wrote", out, os.path.getsize(out), "bytes; final y =", y)


if __name__ == "__main__":
    main()
