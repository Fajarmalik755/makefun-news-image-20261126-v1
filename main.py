#!/usr/bin/env python3
"""news-image-20261126 v1 — one 1024x1024 newspaper front page.

Thursday 26 November 2026: 40 dated stories, 7 regions.
Stdlib only (os, struct, sys, zlib). Deterministic: same bytes every run.
Written from scratch for this edition.
"""
import os
import struct
import sys
import zlib

W, H = 1024, 1024

PAPER = (246, 241, 222)
NAVY = (18, 32, 84)
RED = (178, 34, 34)
INK = (28, 28, 28)
GREY = (112, 110, 102)
TAN = (208, 188, 148)
WHITE = (255, 255, 255)
GOLD = (176, 132, 40)


def write_png(path, w, h, px):
    """Write 24-bit RGB pixels (bytes, row-major) as a PNG with filter 0 rows."""
    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += px[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    data = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s %d bytes" % (path, len(data)))


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def fill(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = yy * self.w * 3
            for xx in range(x0, x1):
                i = base + xx * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x, y, w, h, c, lw=1):
        self.fill(x, y, w, lw, c)
        self.fill(x, y + h - lw, w, lw, c)
        self.fill(x, y, lw, h, c)
        self.fill(x + w - lw, y, lw, h, c)

    def hline(self, x, y, w, c, lw=1):
        self.fill(x, y, w, lw, c)

    def vline(self, x, y, h, c, lw=1):
        self.fill(x, y, lw, h, c)

    def line(self, x0, y0, x1, y1, c):
        dx = x1 - x0
        dy = y1 - y0
        n = max(abs(dx), abs(dy), 1)
        for i in range(n + 1):
            self.set(x0 + dx * i // n, y0 + dy * i // n, c)

    def poly(self, pts, c):
        if len(pts) < 3:
            return
        for a, b in zip(pts, pts[1:] + pts[:1]):
            self.line(a[0], a[1], b[0], b[1], c)
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
                if y0 == y1:
                    continue
                if min(y0, y1) <= y < max(y0, y1):
                    xs.append(x0 + (x1 - x0) * (y - y0) // (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                for x in range(xs[k], xs[k + 1] + 1):
                    self.set(x, y, c)

    def circle(self, cx, cy, r, c, fill=True):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                d2 = (x - cx) ** 2 + (y - cy) ** 2
                if fill:
                    if d2 <= r * r:
                        self.set(x, y, c)
                else:
                    if r * r - 2 * r <= d2 <= r * r:
                        self.set(x, y, c)


# ---------------------------------------------------------------- font
# 5x8 bitmap glyphs, '#' = ink. Rows 0..7, row 7 is the baseline gap.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001", "00000"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110", "00000"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110", "00000"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110", "00000"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111", "00000"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000", "00000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111", "00000"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001", "00000"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110", "00000"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100", "00000"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001", "00000"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111", "00000"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001", "00000"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001", "00000"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110", "00000"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000", "00000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101", "00000"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001", "00000"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110", "00000"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100", "00000"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110", "00000"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100", "00000"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010", "00000"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001", "00000"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100", "00000"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111", "00000"),
    "a": ("00000", "00000", "01110", "00001", "01111", "10001", "01111", "00000"),
    "b": ("10000", "10000", "11110", "10001", "10001", "10001", "11110", "00000"),
    "c": ("00000", "00000", "01110", "10000", "10000", "10001", "01110", "00000"),
    "d": ("00001", "00001", "01111", "10001", "10001", "10001", "01111", "00000"),
    "e": ("00000", "00000", "01110", "10001", "11111", "10000", "01110", "00000"),
    "f": ("00110", "01001", "01000", "11110", "01000", "01000", "01000", "00000"),
    "g": ("00000", "00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    "h": ("10000", "10000", "11110", "10001", "10001", "10001", "10001", "00000"),
    "i": ("00100", "00000", "01100", "00100", "00100", "00100", "01110", "00000"),
    "j": ("00010", "00000", "00110", "00010", "00010", "00010", "10010", "01100"),
    "k": ("10000", "10000", "10010", "10100", "11000", "10100", "10010", "00000"),
    "l": ("01100", "00100", "00100", "00100", "00100", "00100", "01110", "00000"),
    "m": ("00000", "00000", "11010", "10101", "10101", "10101", "10101", "00000"),
    "n": ("00000", "00000", "11110", "10001", "10001", "10001", "10001", "00000"),
    "o": ("00000", "00000", "01110", "10001", "10001", "10001", "01110", "00000"),
    "p": ("00000", "00000", "11110", "10001", "10001", "11110", "10000", "10000"),
    "q": ("00000", "00000", "01111", "10001", "10001", "01111", "00001", "00001"),
    "r": ("00000", "00000", "10110", "11001", "10000", "10000", "10000", "00000"),
    "s": ("00000", "00000", "01111", "10000", "01110", "00001", "11110", "00000"),
    "t": ("01000", "01000", "11100", "01000", "01000", "01000", "00110", "00000"),
    "u": ("00000", "00000", "10001", "10001", "10001", "10011", "01101", "00000"),
    "v": ("00000", "00000", "10001", "10001", "10001", "01010", "00100", "00000"),
    "w": ("00000", "00000", "10001", "10101", "10101", "10101", "01010", "00000"),
    "x": ("00000", "00000", "10001", "01010", "00100", "01010", "10001", "00000"),
    "y": ("00000", "00000", "10001", "10001", "01011", "00101", "00010", "01100"),
    "z": ("00000", "00000", "11111", "00010", "00100", "01000", "11111", "00000"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110", "00000"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110", "00000"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111", "00000"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110", "00000"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010", "00000"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110", "00000"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110", "00000"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000", "00000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110", "00000"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100", "00000"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100", "00000"),
    ",": ("00000", "00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ";": ("00000", "00000", "01100", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "00000", "01100", "00000", "00000", "01100", "01100", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000", "00000"),
    "\u2013": ("00000", "00000", "00000", "01110", "00000", "00000", "00000", "00000"),
    "\u2014": ("00000", "00000", "00000", "11111", "00000", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000", "00000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011", "00000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101", "00000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100", "00000"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010", "00000"),
    "@": ("01110", "10001", "10111", "10101", "10110", "10000", "01110", "00000"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000", "00000"),
    "*": ("00000", "00100", "10101", "01110", "10101", "00100", "00000", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000", "00000"),
    "\u00b7": ("00000", "00000", "00000", "01100", "01100", "00000", "00000", "00000"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "[": ("01110", "01000", "01000", "01000", "01000", "01000", "01110", "00000"),
    "]": ("01110", "00010", "00010", "00010", "00010", "00010", "01110", "00000"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010", "00000"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000", "00000"),
    "\\": ("10000", "01000", "01000", "00100", "00010", "00010", "00001", "00000"),
    "|": ("00100", "00100", "00100", "00100", "00100", "00100", "00100", "00000"),
    "{": ("00010", "00100", "00100", "01100", "00100", "00100", "00010", "00000"),
    "}": ("01000", "00100", "00100", "00110", "00100", "00100", "01000", "00000"),
    "^": ("00100", "01010", "10001", "00000", "00000", "00000", "00000", "00000"),
    "~": ("00000", "00000", "01001", "10110", "00000", "00000", "00000", "00000"),
    "`": ("01000", "00100", "00010", "00000", "00000", "00000", "00000", "00000"),
    "\u2019": ("00100", "00100", "01000", "00000", "00000", "00000", "00000", "00000"),
    "\u00d7": ("00000", "10001", "01010", "00100", "01010", "10001", "00000", "00000"),
}


# ---------------------------------------------------------------- text

def text_w(s, scale):
    return len(s) * 6 * scale


def draw_text(cv, x, y, s, text, color, bold=False, italic=False):
    cx = x
    for ch in text:
        g = FONT.get(ch)
        if g is None:
            g = FONT["?"]
        for r in range(8):
            row = g[r]
            shift = (r // 3) if italic else 0
            for c in range(5):
                if row[c] == "1":
                    bw = s + (1 if bold else 0)
                    cv.fill(cx + c * s + shift, y + r * s, bw, s, color)
        cx += 6 * s
    return cx


def wrap(text, width_px, s):
    lines = []
    for chunk in text.split("\n"):
        words = chunk.split(" ")
        cur = ""
        for w in words:
            trial = (cur + " " + w).strip()
            if text_w(trial, s) <= width_px or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
    return lines


def draw_para(cv, x, y, width_px, s, text, color, lh=None, bold=False):
    if lh is None:
        lh = 8 * s + 3
    yy = y
    for ln in wrap(text, width_px, s):
        draw_text(cv, x, yy, s, ln, color, bold=bold)
        yy += lh
    return yy


# ---------------------------------------------------------------- data
# (big, label, source) for the KPI strip
KPI = [
    ("14", "tariff targets", "BBC"),
    ("3.25%", "BOK base rate", "Reuters"),
    ("-5%", "Nvidia falls", "BBC"),
    ("30", "Cairo fire dead", "AP"),
    ("76", "hostages freed", "BBC"),
    ("1,220", "IPL auction entries", "BCCI"),
    ("204", "Sooryavanshi runs", "BCCI"),
    ("36%", "Bangladesh wage rise", "Reuters"),
]

# (tag, tag_color, headline, body, source, art)
HEROES = [
    ("TRADE", RED,
     "Trump announces new tariffs on China, EU and 12 others",
     "The US unveils a new round of import duties on China, the European Union and "
     "twelve other jurisdictions, the Thanksgiving tariffs, as markets slide and the "
     "AI rout deepens.",
     "BBC", "bars"),
    ("SPACE", NAVY,
     "BepiColombo reaches Mercury orbit after eight-year journey",
     "The ESA-JAXA BepiColombo spacecraft slips into orbit around Mercury, ending an "
     "eight-year voyage from Earth. It will map the scorched planet and probe its "
     "magnetic field.",
     "ESA", "probe"),
    ("AFRICA", RED,
     "Fuel tanker fire kills at least 30 on Cairo ring road",
     "A vehicle carrying petroleum products overturns and erupts in flames on a major "
     "ring road in Greater Cairo. At least 30 people are killed and 25 injured in "
     "one of Egypt's worst road disasters this year.",
     "AP", "flame"),
]

# (num, headline, body, source) — cards 4..13
CARDS = [
    ("4", "US stocks tumble as AI rout deepens",
     "Nasdaq and the S&P 500 pare losses as AI stocks bounce off morning lows. "
     "Nvidia falls 5% as tariff fears rattle markets.", "BBC"),
    ("5", "Colombia police free 76 hostages",
     "Police storm a Cartagena supermarket and free 76 people held for 17 hours "
     "after a failed cash-truck robbery.", "BBC"),
    ("6", "Bank of Korea lifts rate to 3.25%",
     "The central bank resumes tightening with a quarter-point hike as the AI export "
     "boom keeps growth brisk and inflation above target.", "Reuters"),
    ("7", "Israel kills Hamas colonel in Gaza",
     "An Israeli strike kills Mohammad Abuelouf, who headed the militants' interior "
     "security service, with his wife and two children.", "Reuters"),
    ("8", "Sudan drone strikes kill 19",
     "Drone strikes in Blue Nile state kill 19 civilians as the war grinds on.",
     "Reuters"),
    ("9", "India marks 18 years since 26/11",
     "India honours the victims of the 2008 Mumbai attacks and celebrates "
     "Constitution Day, 77 years after adopting its constitution.", "AP"),
    ("10", "EU court orders farm cage ban date",
     "The EU court tells the Commission to set a timeline for ending caged farming.",
     "BBC"),
    ("11", "SpaceX cleared for a million satellites",
     "The US approves SpaceX's plan to send a million data satellites to space.",
     "BBC"),
    ("12", "Macy's parade postponed by storm",
     "The Thanksgiving parade is delayed by storms, the first weather postponement "
     "in its history.", "BBC"),
    ("13", "Gukesh-Sindarov title Game 2 drawn",
     "The world title match in Geneva stays level after a 20-move draw.",
     "FIDE"),
]

# (num, headline, source) — the ALSO list, 27 items
LIST = [
    ("14", "Supreme Court to weigh weapon bans.", "AP"),
    ("15", "US Army: Iowa blast a 'huge success'.", "BBC"),
    ("16", "Jolie and Pitt settle winery battle.", "BBC"),
    ("17", "Four-time MVP Rodgers released.", "BBC"),
    ("18", "44 Nvidia trades by Trump accounts.", "BBC"),
    ("19", "Two tankers hit mines off Hormuz.", "Reuters"),
    ("20", "UN tribunal doubts Gaza aid sackings.", "UN"),
    ("21", "Lebanon plans second airport.", "Reuters"),
    ("22", "Russia budget tops $600bn.", "EUR Radio"),
    ("23", "3.7m jobs at risk in Europe.", "EUR Radio"),
    ("24", "Puigdemont to return to Spain Dec 12.", "AP"),
    ("25", "Hera images show asteroid crater.", "ESA"),
    ("26", "Borthwick: Tests are practice.", "Sky Sports"),
    ("27", "Five held over $227m Nigeria meth lab.", "BBC"),
    ("28", "Elephant kills tourist in Cameroon.", "AP"),
    ("29", "Ramaphosa wins court fight.", "Reuters"),
    ("30", "Africa CDC chief faces Ebola turmoil.", "NYT"),
    ("31", "Bangladesh garment wage up 36%.", "Reuters"),
    ("32", "India unveils Rs 15,000cr Nepal aid.", "PTI"),
    ("33", "IPL auction draws 1,220 players.", "BCCI"),
    ("34", "Sooryavanshi, 15, smashes 204.", "BCCI"),
    ("35", "Malaysia sues Google for $146m.", "Reuters"),
    ("36", "Oceania Rugby loses council seat.", "RNZ"),
    ("37", "Senator Blyth defects to One Nation.", "ABC"),
    ("38", "RNZ battles an attempted cyber breach.", "RNZ"),
    ("39", "Argentina unions march over health.", "CGT"),
    ("40", "Five women killed hourly by a partner.", "UN"),
]

# stories deliberately left out (25 Nov or earlier)
LEFT_OUT = [
    ("Houthis claim Ras Tanura refinery strike", "25 Nov"),
    ("Russia's own figures: ~500,000 war dead", "25 Nov"),
    ("Duran Duran guitarist Andy Taylor dies, 65", "25 Nov"),
    ("North Korea expels Swiss diplomat", "25 Nov"),
    ("Pakistan astronaut joins Shenzhou-24", "25 Nov"),
    ("Sheikh Hasina seeks return to Bangladesh", "25 Nov"),
    ("Indonesia gold mine flood kills nine", "25 Nov?"),
    ("Saudi national kidnapped in Niger", "25 Nov"),
    ("US jobless claims fall to 189,000", "25 Nov"),
    ("Poundland prepares for administration", "25 Nov"),
]

DATE_NOTE = ("The Cartagena rescue: the hostage-taking began late 24 Nov in Colombia and was "
             "covered on 25 Nov, but the police storming that freed 76 hostages happened "
             "overnight and was first reported on 26 Nov in Asia and Europe. The Iowa blast: "
             "the 25 Nov edition covered Iowans bracing for it; the Army's verdict on the "
             "blast itself is a 26 Nov story. A story counts as 26 Nov when it happened, or "
             "was first reported, on 26 Nov in at least one time zone.")

# (story number, fx, fy) — dots on the world map
DOTS = [
    (1, 0.20, 0.28),
    (2, 0.60, 0.06),
    (3, 0.53, 0.50),
    (4, 0.27, 0.33),
    (5, 0.27, 0.58),
    (6, 0.82, 0.22),
    (7, 0.58, 0.38),
    (8, 0.60, 0.60),
    (9, 0.68, 0.42),
    (10, 0.48, 0.22),
    (11, 0.18, 0.42),
    (12, 0.25, 0.20),
    (13, 0.55, 0.16),
]


# ---------------------------------------------------------------- map

def draw_map(cv, x, y, w, h):
    def P(fx, fy):
        return (x + int(fx * w), y + int(fy * h))

    polys = [
        [(0.03, 0.08), (0.30, 0.02), (0.42, 0.10), (0.36, 0.30), (0.28, 0.48),
         (0.15, 0.45), (0.05, 0.30)],
        [(0.40, 0.02), (0.46, 0.04), (0.44, 0.12), (0.40, 0.10)],
        [(0.28, 0.52), (0.38, 0.55), (0.40, 0.75), (0.33, 0.95), (0.27, 0.80)],
        [(0.50, 0.05), (0.60, 0.03), (0.63, 0.18), (0.55, 0.25), (0.50, 0.15)],
        [(0.48, 0.12), (0.51, 0.13), (0.50, 0.20), (0.48, 0.18)],
        [(0.52, 0.30), (0.64, 0.32), (0.66, 0.55), (0.60, 0.85), (0.54, 0.70),
         (0.50, 0.45)],
        [(0.64, 0.02), (0.95, 0.05), (0.98, 0.30), (0.85, 0.45), (0.70, 0.40),
         (0.64, 0.20)],
        [(0.93, 0.25), (0.96, 0.28), (0.95, 0.40), (0.92, 0.38)],
        [(0.88, 0.18), (0.90, 0.22), (0.89, 0.30), (0.87, 0.26)],
        [(0.82, 0.72), (0.95, 0.75), (0.93, 0.88), (0.83, 0.85)],
        [(0.97, 0.85), (0.99, 0.88), (0.98, 0.95), (0.96, 0.92)],
    ]
    for poly in polys:
        cv.poly([P(fx, fy) for fx, fy in poly], TAN)
    for n, fx, fy in DOTS:
        dx, dy = x + int(fx * w), y + int(fy * h)
        cv.circle(dx, dy, 8, NAVY)
        cv.circle(dx, dy, 8, WHITE, fill=False)
        s = str(n)
        tx = dx - text_w(s, 1) // 2
        draw_text(cv, tx, dy - 4, 1, s, WHITE, bold=True)


# ---------------------------------------------------------------- hero art

def draw_art(cv, kind, x, y, w, h):
    if kind == "bars":
        base = y + h - 8
        heights = [26, 42, 58, 74]
        bw = 34
        gap = 14
        for i, hh in enumerate(heights):
            bx = x + 12 + i * (bw + gap)
            col = RED if i == 3 else NAVY
            cv.fill(bx, base - hh, bw, hh, col)
        cv.hline(x + 6, base, w - 12, NAVY, 2)
        draw_text(cv, x + w - 52, y + 6, 3, "%", RED, bold=True)
    elif kind == "probe":
        cv.circle(x + 52, y + h // 2, 26, GOLD)
        cv.circle(x + 52, y + h // 2, 26, NAVY, fill=False)
        for i in range(7):
            cv.set(x + 92 + i * 16, y + h // 2 - 6 - i * 3, NAVY)
            cv.set(x + 92 + i * 16, y + h // 2 - 5 - i * 3, NAVY)
        px, py = x + w - 66, y + h // 2 - 12
        cv.fill(px - 14, py - 2, 28, 4, NAVY)
        cv.fill(px - 4, py - 8, 8, 16, RED)
        cv.fill(px + 12, py - 2, 22, 4, NAVY)
        draw_text(cv, x + 8, y + h - 14, 1, "MERCURY", GREY)
    elif kind == "flame":
        fx, fy = x + w // 2, y + 12
        flame = [(fx, fy), (fx + 16, fy + 26), (fx + 10, fy + 30),
                 (fx + 18, fy + 48), (fx, fy + 62), (fx - 18, fy + 48),
                 (fx - 10, fy + 30), (fx - 16, fy + 26)]
        cv.poly(flame, RED)
        cv.poly([(fx, fy + 22), (fx + 8, fy + 40), (fx, fy + 54),
                 (fx - 8, fy + 40)], GOLD)
        cv.hline(x + 6, y + h - 10, w - 12, NAVY, 2)
        cv.hline(x + 6, y + h - 4, w - 12, NAVY, 1)


# ---------------------------------------------------------------- page

def build():
    cv = Canvas(W, H, PAPER)
    cv.rect(5, 5, W - 10, H - 10, NAVY, 2)
    cv.rect(9, 9, W - 18, H - 18, NAVY, 1)

    # masthead
    title = "Thursday 26 November 2026"
    tw = text_w(title, 6)
    draw_text(cv, (W - tw) // 2, 20, 6, title, NAVY, bold=True)
    sub = "THE WORLD IN ONE DAY"
    draw_text(cv, (W - text_w(sub, 2)) // 2, 72, 2, sub, NAVY, bold=True)
    line = "40 STORIES \u00b7 7 REGIONS \u00b7 AS REPORTED ON THURSDAY 26 NOVEMBER 2026"
    draw_text(cv, (W - text_w(line, 1)) // 2, 96, 1, line, RED, bold=True)
    teaser = "Tariffs land \u00b7 Mercury reached \u00b7 Cairo fire \u00b7 Asia slides"
    draw_text(cv, (W - text_w(teaser, 2)) // 2, 110, 2, teaser, RED, italic=True)
    cv.hline(12, 132, W - 24, NAVY, 2)

    # KPI strip
    kx, ky, kw, kh = 12, 136, W - 24, 46
    cw = kw // 8
    for i, (big, label, src) in enumerate(KPI):
        cx = kx + i * cw
        draw_text(cv, cx + (cw - text_w(big, 2)) // 2, ky + 2, 2, big, NAVY, bold=True)
        draw_text(cv, cx + (cw - text_w(label, 1)) // 2, ky + 20, 1, label, INK)
        draw_text(cv, cx + (cw - text_w(src, 1)) // 2, ky + kh - 10, 1, src, GREY)
        if i:
            cv.vline(cx, ky + 4, kh - 8, GREY, 1)

    # heroes
    hy, hh = 196, 232
    hw = 325
    for i, (tag, tcol, head, body, src, art) in enumerate(HEROES):
        hx = 12 + i * (hw + 12)
        cv.rect(hx, hy, hw, hh, NAVY, 1)
        cv.fill(hx + 1, hy + 1, hw - 2, 18, tcol)
        draw_text(cv, hx + 8, hy + 6, 1, tag, WHITE, bold=True)
        draw_text(cv, hx + hw - 20, hy + 6, 1, str(i + 1), WHITE, bold=True)
        draw_para(cv, hx + 8, hy + 24, hw - 16, 2, head, NAVY, lh=19, bold=True)
        draw_art(cv, art, hx + 8, hy + 88, hw - 16, 78)
        draw_para(cv, hx + 8, hy + 172, hw - 16, 1, body, INK, lh=11)
        draw_text(cv, hx + 8, hy + hh - 12, 1, src, GREY)

    # cards 4..13, two rows of five
    cw2 = 193
    for idx, (num, head, body, src) in enumerate(CARDS):
        row = idx // 5
        col = idx % 5
        cx = 12 + col * (cw2 + 8)
        cy = 438 + row * 126
        cv.rect(cx, cy, cw2, 118, NAVY, 1)
        draw_para(cv, cx + 6, cy + 6, cw2 - 12, 1, head, NAVY, lh=11, bold=True)
        draw_para(cv, cx + 6, cy + 40, cw2 - 12, 1, body, INK, lh=11)
        draw_text(cv, cx + 6, cy + 118 - 12, 1, num + " - " + src, GREY)

    # bottom section
    by0 = 700
    cv.hline(12, by0 - 6, W - 24, NAVY, 2)
    draw_text(cv, 12, by0, 1, "WHERE IT HAPPENED", NAVY, bold=True)
    draw_map(cv, 12, by0 + 16, 388, 176)
    draw_text(cv, 12, by0 + 196, 1, "Dots mark the 13 featured stories.", GREY)
    lx = 412
    draw_text(cv, lx, by0, 1, "ALSO ON THURSDAY 26 NOVEMBER \u2014 27 MORE STORIES",
              NAVY, bold=True)
    col_w = (W - 24 - lx + 12 - 16) // 2
    for j, (num, text, src) in enumerate(LIST):
        col = 0 if j < 14 else 1
        xx = lx + col * (col_w + 16)
        yy = by0 + 16 + (j % 14) * 14
        full = num + ". " + text + " \u2014 " + src
        if text_w(full, 1) > col_w:
            while text_w(full + "...", 1) > col_w and len(full) > 4:
                full = full[:-1]
            full = full + "..."
        draw_text(cv, xx, yy, 1, full, INK)

    # DATE CHECK
    dy = 912
    cv.rect(12, dy, W - 24, 102, RED, 1)
    dtitle = "DATE CHECK \u2014 WHAT WE LEFT OUT, AND WHAT WAS STILL UNCONFIRMED"
    draw_text(cv, (W - text_w(dtitle, 1)) // 2, dy + 6, 1, dtitle, RED, bold=True)
    draw_text(cv, 20, dy + 22, 1, "THROWN OUT AS OLD NEWS", NAVY, bold=True)
    draw_text(cv, 540, dy + 22, 1, "DATE NOTE \u2014 WHY TWO STORIES COUNT", NAVY, bold=True)
    short_out = [
        ("Ras Tanura strike claim", "25 Nov"),
        ("Russia ~500,000 war dead", "25 Nov"),
        ("Andy Taylor dies, 65", "25 Nov"),
        ("N. Korea expels Swiss diplomat", "25 Nov"),
        ("Pakistan astronaut in Shenzhou", "25 Nov"),
        ("Hasina seeks return home", "25 Nov"),
        ("Indonesia mine flood, 9 dead", "25 Nov?"),
        ("Saudi kidnapped in Niger", "25 Nov"),
        ("US jobless claims 189,000", "25 Nov"),
        ("Poundland for administration", "25 Nov"),
    ]
    for k, (item, when) in enumerate(short_out):
        col = 0 if k < 5 else 1
        xx = 20 + col * 260
        yy = dy + 36 + (k % 5) * 11
        s = "\u00d7 " + item + " \u2014 " + when
        if text_w(s, 1) > 250:
            while text_w(s + "...", 1) > 250 and len(s) > 4:
                s = s[:-1]
            s = s + "..."
        draw_text(cv, xx, yy, 1, s, INK)
    note = ("Cartagena: the hostage-taking began late 24 Nov and was covered on "
            "25 Nov, but the storming that freed 76 hostages was first reported on 26 Nov in "
            "Asia and Europe. Iowa: the 25 Nov edition covered Iowans bracing for the "
            "blast; the Army's verdict is a 26 Nov story. A story counts as 26 Nov when it "
            "happened, or was first reported, on 26 Nov in at least one time zone.")
    draw_para(cv, 540, dy + 36, 460, 1, note, INK, lh=11)
    foot = ("Every story here happened, or was first reported, on Thursday 26 November 2026 "
            "in at least one time zone.")
    draw_text(cv, (W - text_w(foot, 1)) // 2, dy + 92, 1, foot, GREY)
    return cv


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else None
    if out is None:
        out = os.path.join(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
                           if os.path.isdir(os.environ.get(
                               "MAKEFUN_OUTPUT_DIR", "/output")) else ".",
                           "entry.png")
    cv = build()
    write_png(out, W, H, cv.px)


if __name__ == "__main__":
    main()
