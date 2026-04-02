#!/usr/bin/env python3
"""
Project Video Generator — renders scene PNGs with Pillow and assembles MP4 with FFmpeg.

Supports three modes:
  - Showcase: highlight reel for a single repo
  - Comparison: head-to-head of multiple repos
  - Changelog: sprint recap of recent PRs

Usage:
  python3 generate_video.py --repo https://github.com/user/app
  python3 generate_video.py --research /tmp/research.json --theme aurora
  python3 generate_video.py compare https://github.com/user/a https://github.com/user/b
  python3 generate_video.py changelog --repo https://github.com/user/app --since "last week"
"""

import argparse
import json
import platform
import random
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ── Config ───────────────────────────────────────────────────────────────────

W, H = 1920, 1080
FPS = 30

BASE_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = Path(__file__).parent
FRAMES_DIR = BASE_DIR / "output" / "frames"
OUTPUT_DIR = BASE_DIR / "output"

# ── Font handling (cross-platform) ───────────────────────────────────────────

_font_cache = {}


def _find_font_path():
    """Locate a usable font, preferring system fonts, falling back to bundled."""
    if platform.system() == "Darwin":
        for p in [
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/SFNSText.ttf",
        ]:
            if Path(p).exists():
                return p, {"regular": 0, "bold": 1, "light": 4}
    # Linux / fallback
    for p in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ]:
        if Path(p).exists():
            return p, {"regular": 0, "bold": 0, "light": 0}
    # Last resort: bundled font
    bundled = BASE_DIR / "fonts" / "Inter-Regular.ttf"
    if bundled.exists():
        return str(bundled), {"regular": 0, "bold": 0, "light": 0}
    raise RuntimeError("No suitable font found")


FONT_PATH, FONT_INDICES = _find_font_path()


def font(style="regular", size=40):
    """Load a font with caching."""
    idx = FONT_INDICES[style]
    key = (idx, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(FONT_PATH, size, index=idx)
    return _font_cache[key]


# ── Themes ───────────────────────────────────────────────────────────────────

THEMES = {
    "midnight": {
        "bg": "#0f0f1a",
        "bg_alt": "#141428",
        "bg_dark": "#0a0a12",
        "white": "#FFFFFF",
        "muted": "#8888AA",
        "very_muted": "#555577",
        "accents": ["#7B68EE", "#36C5F0", "#E01E5A", "#ECB22E", "#2BAC76", "#FF6B6B"],
    },
    "aurora": {
        "bg": "#0B1120",
        "bg_alt": "#0F1A2E",
        "bg_dark": "#080D18",
        "white": "#E8F0FF",
        "muted": "#7A9CC6",
        "very_muted": "#4A6A8A",
        "accents": ["#00D4AA", "#4ECDC4", "#FF6B9D", "#C084FC", "#FCD34D", "#60A5FA"],
    },
    "ember": {
        "bg": "#1A0A0A",
        "bg_alt": "#241010",
        "bg_dark": "#120808",
        "white": "#FFF0E8",
        "muted": "#C69A88",
        "very_muted": "#8A6A5A",
        "accents": ["#FF6B35", "#FF4444", "#FFB347", "#E85D75", "#C084FC", "#4ECDC4"],
    },
    "mono": {
        "bg": "#111111",
        "bg_alt": "#1A1A1A",
        "bg_dark": "#0A0A0A",
        "white": "#EEEEEE",
        "muted": "#888888",
        "very_muted": "#555555",
        "accents": ["#FFFFFF", "#CCCCCC", "#AAAAAA", "#999999", "#777777", "#DDDDDD"],
    },
}

# ── Color helpers ────────────────────────────────────────────────────────────


def hex_to_rgb(h):
    """Convert hex color string to RGB tuple."""
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def gradient_bg(color1, color2):
    """Create a vertical gradient background."""
    img = Image.new("RGB", (W, H))
    c1, c2 = hex_to_rgb(color1), hex_to_rgb(color2)
    for y in range(H):
        r = y / H
        row_color = tuple(int(c1[i] + (c2[i] - c1[i]) * r) for i in range(3))
        for x in range(W):
            img.putpixel((x, y), row_color)
    return img


def solid_bg(color):
    """Create a solid color background."""
    return Image.new("RGB", (W, H), hex_to_rgb(color))


# ── Text and accent helpers ──────────────────────────────────────────────────


def draw_text_centered(draw, y, text, f, color):
    """Draw text horizontally centered at given y."""
    bbox = draw.textbbox((0, 0), text, font=f)
    tw = bbox[2] - bbox[0]
    x = (W - tw) // 2
    draw.text((x, y), text, font=f, fill=hex_to_rgb(color))


def draw_accent_bar(draw, color, x=160, y_start=260, y_end=820):
    """Draw a vertical accent bar."""
    draw.rectangle([x, y_start, x + 5, y_end], fill=hex_to_rgb(color))


def draw_horizontal_rule(draw, y, color, margin=500):
    """Draw a thin horizontal rule."""
    draw.rectangle([margin, y, W - margin, y + 1], fill=hex_to_rgb(color))


def wrap_text(text, f, max_width, draw):
    """Wrap text to fit within max_width, returning list of lines."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=f)
        if bbox[2] - bbox[0] > max_width and current:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)
    return lines


# ── Screenshot inset ─────────────────────────────────────────────────────────


def add_screenshot_inset(img, screenshot_path, accent, large=False):
    """Overlay a screenshot as a bordered inset."""
    if screenshot_path is None or not Path(screenshot_path).exists():
        return img

    screenshot = Image.open(screenshot_path)

    if large:
        # Centered, large inset for demo scenes
        inset_w, inset_h = 1200, 650
        inset_x = (W - inset_w) // 2
        inset_y = 280
    else:
        # Right-side inset for content cards
        inset_w, inset_h = 700, 440
        inset_x = W - inset_w - 100
        inset_y = 300

    shot = screenshot.copy()
    shot.thumbnail((inset_w - 8, inset_h - 8), Image.LANCZOS)
    sw, sh = shot.size

    draw = ImageDraw.Draw(img)
    border = 3
    frame_x = inset_x + (inset_w - sw) // 2 - border
    frame_y = inset_y + (inset_h - sh) // 2 - border
    draw.rectangle(
        [frame_x, frame_y, frame_x + sw + 2 * border, frame_y + sh + 2 * border],
        fill=hex_to_rgb(accent),
    )
    img.paste(shot, (frame_x + border, frame_y + border))
    return img


# ── Film grain overlay ───────────────────────────────────────────────────────


def add_grain(img, intensity=8):
    """Add subtle film grain for a premium feel (~3% opacity equivalent)."""
    pixels = img.load()
    for y in range(0, H, 2):
        for x in range(0, W, 2):
            noise = random.randint(-intensity, intensity)
            r, g, b = pixels[x, y]
            pixels[x, y] = (
                max(0, min(255, r + noise)),
                max(0, min(255, g + noise)),
                max(0, min(255, b + noise)),
            )
    return img


# ── Accent color cycling ────────────────────────────────────────────────────


def accent(theme, index):
    """Get an accent color by cycling through the theme's palette."""
    return theme["accents"][index % len(theme["accents"])]


# ══════════════════════════════════════════════════════════════════════════════
# SHOWCASE scene generators
# ══════════════════════════════════════════════════════════════════════════════


def scene_title(data, theme):
    """Title card: gradient bg, project name, description, repo URL."""
    img = gradient_bg(theme["bg"], theme["bg_alt"])
    draw = ImageDraw.Draw(img)

    name = data.get("name", "Project")
    description = data.get("description", "")
    repo_url = data.get("repo_url", "")

    draw_text_centered(draw, 360, name.upper(), font("bold", 72), theme["white"])

    # Thin horizontal rule
    draw_horizontal_rule(draw, 460, theme["very_muted"])

    if description:
        lines = wrap_text(description, font("light", 32), W - 400, draw)
        for i, line in enumerate(lines[:2]):
            draw_text_centered(
                draw, 490 + i * 45, line, font("light", 32), theme["muted"]
            )

    if repo_url:
        # Strip protocol for display
        display_url = repo_url.replace("https://", "").replace("http://", "")
        draw_text_centered(
            draw, 650, display_url, font("regular", 22), theme["very_muted"]
        )

    return img


def scene_context(data, theme):
    """Context card: project overview from README summary."""
    img = solid_bg(theme["bg"])
    draw = ImageDraw.Draw(img)

    a = accent(theme, 0)
    draw_accent_bar(draw, a, x=160, y_start=260, y_end=700)

    draw.text((200, 180), "THE PROJECT", font=font("bold", 48), fill=hex_to_rgb(a))

    summary = data.get("readme_summary", "No summary available.")
    lines = wrap_text(summary, font("light", 28), W - 450, draw)
    for i, line in enumerate(lines[:6]):
        draw.text(
            (200, 290 + i * 50), line, font=font("light", 28), fill=hex_to_rgb(theme["muted"])
        )

    return img


def scene_tech_stack(data, theme):
    """Tech stack card: primary language, other languages, tech items with percentage bars."""
    img = solid_bg(theme["bg"])
    draw = ImageDraw.Draw(img)

    a = accent(theme, 1)
    draw.text((200, 180), "TECH STACK", font=font("bold", 48), fill=hex_to_rgb(a))

    # Primary language
    languages = data.get("languages", {})
    tech_stack = data.get("tech_stack", [])

    if languages:
        sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
        primary = sorted_langs[0][0]
        draw.text(
            (200, 280), primary, font=font("bold", 56), fill=hex_to_rgb(theme["white"])
        )

        # Other languages with percentage bars
        y = 380
        max_bar_w = 400
        for i, (lang, pct) in enumerate(sorted_langs[:6]):
            color = accent(theme, i)
            # Colored dot
            dot_x, dot_y = 200, y + 14
            draw.ellipse(
                [dot_x, dot_y, dot_x + 12, dot_y + 12], fill=hex_to_rgb(color)
            )
            # Language name and percentage
            draw.text(
                (225, y), f"{lang}", font=font("regular", 24), fill=hex_to_rgb(theme["white"])
            )
            pct_val = float(pct) if isinstance(pct, (int, float)) else 0
            draw.text(
                (225 + 200, y),
                f"{pct_val:.1f}%",
                font=font("regular", 24),
                fill=hex_to_rgb(theme["muted"]),
            )
            # Percentage bar
            bar_x = 500
            bar_y = y + 8
            bar_h = 12
            bar_w = int(max_bar_w * (pct_val / 100.0))
            draw.rectangle(
                [bar_x, bar_y, bar_x + max_bar_w, bar_y + bar_h],
                fill=hex_to_rgb(theme["bg_alt"]),
            )
            draw.rectangle(
                [bar_x, bar_y, bar_x + bar_w, bar_y + bar_h],
                fill=hex_to_rgb(color),
            )
            y += 50

    # Tech stack items on the right
    if tech_stack:
        x_right = 1050
        draw.text(
            (x_right, 280), "DEPENDENCIES", font=font("bold", 24), fill=hex_to_rgb(theme["muted"])
        )
        for i, item in enumerate(tech_stack[:10]):
            color = accent(theme, i)
            iy = 330 + i * 40
            draw.ellipse(
                [x_right, iy + 8, x_right + 10, iy + 18], fill=hex_to_rgb(color)
            )
            draw.text(
                (x_right + 22, iy),
                str(item),
                font=font("regular", 22),
                fill=hex_to_rgb(theme["white"]),
            )

    return img


def scene_architecture(data, theme, screenshot_path=None):
    """Architecture card: directory tree, file count, optional screenshot."""
    img = solid_bg(theme["bg"])
    draw = ImageDraw.Draw(img)

    a = accent(theme, 2)
    draw.text((200, 180), "ARCHITECTURE", font=font("bold", 48), fill=hex_to_rgb(a))

    tree = data.get("tree_summary", "")
    total_files = data.get("total_files", 0)

    has_shot = screenshot_path and Path(screenshot_path).exists()
    max_text_x = 900 if has_shot else W - 200

    # Render tree as monospaced directory listing
    # tree_summary may be comma-separated or newline-separated
    if tree:
        lines = [s.strip() for s in tree.replace(", ", "\n").strip().split("\n") if s.strip()]
    else:
        lines = []
    y = 280
    for i, line in enumerate(lines[:16]):
        # Truncate long lines
        max_chars = 50 if has_shot else 80
        display = line[:max_chars] + ("..." if len(line) > max_chars else "")
        draw.text(
            (200, y + i * 32),
            display,
            font=font("regular", 22),
            fill=hex_to_rgb(theme["muted"]),
        )

    # Total files count
    if total_files:
        draw.text(
            (200, 820),
            f"{total_files} files total",
            font=font("regular", 22),
            fill=hex_to_rgb(theme["very_muted"]),
        )

    if has_shot:
        img = add_screenshot_inset(img, screenshot_path, a)

    return img


def scene_feature(data, theme, feature_text, index, screenshot_path=None):
    """Feature card: accent bar, feature text, optional screenshot."""
    img = solid_bg(theme["bg"])
    draw = ImageDraw.Draw(img)

    a = accent(theme, index)
    has_shot = screenshot_path and Path(screenshot_path).exists()

    draw_accent_bar(draw, a, x=140, y_start=250, y_end=780)

    # Feature number
    draw.text(
        (180, 260),
        f"FEATURE {index + 1:02d}",
        font=font("bold", 22),
        fill=hex_to_rgb(theme["very_muted"]),
    )

    # Feature text
    max_w = 700 if has_shot else W - 400
    lines = wrap_text(feature_text, font("bold", 40), max_w, draw)
    for i, line in enumerate(lines[:4]):
        draw.text(
            (180, 320 + i * 60), line, font=font("bold", 40), fill=hex_to_rgb(theme["white"])
        )

    if has_shot:
        img = add_screenshot_inset(img, screenshot_path, a)

    return img


def scene_demo(data, theme, screenshot_path):
    """Demo card: large centered screenshot, URL below."""
    img = gradient_bg(theme["bg"], theme["bg_alt"])
    draw = ImageDraw.Draw(img)

    a = accent(theme, 3)
    draw_text_centered(draw, 120, "LIVE DEMO", font("bold", 48), a)

    img = add_screenshot_inset(img, screenshot_path, a, large=True)

    # URL below screenshot
    url = data.get("homepage", data.get("repo_url", ""))
    if url:
        display_url = url.replace("https://", "").replace("http://", "")
        draw_text_centered(
            draw, 970, display_url, font("regular", 24), theme["very_muted"]
        )

    return img


def scene_stats(data, theme):
    """Stats card: 2x3 grid of key numbers."""
    img = solid_bg(theme["bg_dark"])
    draw = ImageDraw.Draw(img)

    a = accent(theme, 4)
    draw_text_centered(draw, 140, "BY THE NUMBERS", font("bold", 48), a)

    def stat_val(v, default="0"):
        return str(v) if v is not None else default

    stats = [
        (stat_val(data.get("stars")), "STARS"),
        (stat_val(data.get("forks")), "FORKS"),
        (stat_val(data.get("contributors")), "CONTRIBUTORS"),
        (stat_val(data.get("total_files")), "FILES"),
        (str(len(data.get("recent_prs", []))), "RECENT PRs"),
        (stat_val(data.get("license"), "N/A"), "LICENSE"),
    ]

    # 2x3 grid layout
    cols, rows = 3, 2
    cell_w = W // (cols + 1)
    cell_h = 200
    start_x = (W - cell_w * cols) // 2
    start_y = 300

    for i, (value, label) in enumerate(stats):
        col = i % cols
        row = i // cols
        cx = start_x + col * cell_w + cell_w // 2
        cy = start_y + row * cell_h

        # Large value
        bbox = draw.textbbox((0, 0), value, font=font("bold", 52))
        vw = bbox[2] - bbox[0]
        draw.text(
            (cx - vw // 2, cy),
            value,
            font=font("bold", 52),
            fill=hex_to_rgb(theme["white"]),
        )

        # Small label below
        bbox = draw.textbbox((0, 0), label, font=font("regular", 18))
        lw = bbox[2] - bbox[0]
        draw.text(
            (cx - lw // 2, cy + 65),
            label,
            font=font("regular", 18),
            fill=hex_to_rgb(theme["very_muted"]),
        )

    return img


def scene_closing(data, theme):
    """Closing card: project name, pitch, repo URL, install command."""
    img = gradient_bg(theme["bg"], theme["bg_alt"])
    draw = ImageDraw.Draw(img)

    name = data.get("name", "Project")
    description = data.get("description", "")
    repo_url = data.get("repo_url", "")
    install_cmd = data.get("install_command", "")

    a = accent(theme, 0)

    draw_text_centered(draw, 320, name.upper(), font("bold", 64), theme["white"])

    draw_horizontal_rule(draw, 410, a, margin=600)

    if description:
        lines = wrap_text(description, font("light", 28), W - 500, draw)
        for i, line in enumerate(lines[:2]):
            draw_text_centered(
                draw, 440 + i * 42, line, font("light", 28), theme["muted"]
            )

    if repo_url:
        display = repo_url.replace("https://", "").replace("http://", "")
        draw_text_centered(
            draw, 570, display, font("regular", 24), theme["very_muted"]
        )

    if install_cmd:
        draw_text_centered(
            draw, 640, f"$ {install_cmd}", font("regular", 22), theme["muted"]
        )

    return img


# ══════════════════════════════════════════════════════════════════════════════
# COMPARISON scene generators
# ══════════════════════════════════════════════════════════════════════════════


def scene_compare_title(repos, theme):
    """Comparison title: HEAD TO HEAD + repo count."""
    img = gradient_bg(theme["bg"], theme["bg_alt"])
    draw = ImageDraw.Draw(img)

    a = accent(theme, 0)
    draw_text_centered(draw, 340, "HEAD TO HEAD", font("bold", 72), a)
    draw_horizontal_rule(draw, 440, theme["very_muted"])
    draw_text_centered(
        draw,
        480,
        f"{len(repos)} repositories compared",
        font("light", 32),
        theme["muted"],
    )

    # Colored dots for each repo
    spacing = 60
    start_x = (W - (len(repos) - 1) * spacing) // 2
    dot_y = 580
    for i in range(len(repos)):
        color = accent(theme, i)
        x = start_x + i * spacing
        draw.ellipse([x - 10, dot_y - 10, x + 10, dot_y + 10], fill=hex_to_rgb(color))

    return img


def scene_compare_setup(repos, theme):
    """Experiment description with colored dots per repo."""
    img = solid_bg(theme["bg"])
    draw = ImageDraw.Draw(img)

    draw_text_centered(
        draw, 200, "THE COMPARISON", font("bold", 48), accent(theme, 0)
    )

    y = 340
    for i, repo_data in enumerate(repos):
        color = accent(theme, i)
        name = repo_data.get("name", f"Repo {i+1}")
        desc = repo_data.get("description", "")

        # Colored dot + name
        draw.ellipse([200, y + 8, 220, y + 28], fill=hex_to_rgb(color))
        draw.text(
            (235, y), name, font=font("bold", 30), fill=hex_to_rgb(theme["white"])
        )
        if desc:
            truncated = desc[:80] + ("..." if len(desc) > 80 else "")
            draw.text(
                (235, y + 40),
                truncated,
                font=font("light", 22),
                fill=hex_to_rgb(theme["muted"]),
            )
        y += 100

    return img


def scene_compare_repo(data, theme, color):
    """Per-repo comparison card: name, description, stats grid, optional screenshot."""
    img = solid_bg(theme["bg"])
    draw = ImageDraw.Draw(img)

    screenshot_path = data.get("screenshot_path")
    has_shot = screenshot_path and Path(screenshot_path).exists()
    left = 120 if has_shot else 200

    draw_accent_bar(draw, color, x=left - 30, y_start=250, y_end=780)

    name = data.get("name", "Repository")
    desc = data.get("description", "")

    draw.text(
        (left, 260), name.upper(), font=font("bold", 48), fill=hex_to_rgb(color)
    )

    if desc:
        truncated = desc[:100] + ("..." if len(desc) > 100 else "")
        draw.text(
            (left, 335), truncated, font=font("light", 26), fill=hex_to_rgb(theme["muted"])
        )

    # Stats grid
    stats = [
        ("stars", str(data.get("stars", 0))),
        ("forks", str(data.get("forks", 0))),
        ("files", str(data.get("total_files", 0))),
        ("contributors", str(data.get("contributors", 0))),
    ]

    grid_y = 420
    col2_x = left + 380 if has_shot else left + 480
    row_h = 70
    for i, (label, value) in enumerate(stats):
        row = i // 2
        col = i % 2
        x = left if col == 0 else col2_x
        y = grid_y + row * row_h
        draw.text((x, y), value, font=font("bold", 26), fill=hex_to_rgb(theme["white"]))
        draw.text(
            (x, y + 30), label, font=font("regular", 16), fill=hex_to_rgb(theme["very_muted"])
        )

    if has_shot:
        img = add_screenshot_inset(img, screenshot_path, color)

    return img


def scene_compare_verdict(repos, winner_index, theme):
    """Winner announcement."""
    img = gradient_bg(theme["bg"], theme["bg_dark"])
    draw = ImageDraw.Draw(img)

    color = accent(theme, winner_index)
    winner = repos[winner_index] if winner_index < len(repos) else repos[0]
    name = winner.get("name", "Winner")

    draw_text_centered(draw, 240, "WINNER", font("bold", 36), theme["muted"])
    draw_horizontal_rule(draw, 300, color, margin=650)
    draw_text_centered(draw, 340, name.upper(), font("bold", 80), color)
    draw_text_centered(
        draw,
        480,
        winner.get("description", ""),
        font("regular", 28),
        theme["white"],
    )

    return img


def scene_compare_closing(theme):
    """Comparison takeaway."""
    img = gradient_bg(theme["bg"], theme["bg_alt"])
    draw = ImageDraw.Draw(img)

    draw_text_centered(
        draw, 400, "Choose what fits your needs.", font("bold", 48), theme["white"]
    )
    draw_text_centered(
        draw,
        500,
        "Stars and forks tell part of the story. Your use case tells the rest.",
        font("light", 26),
        theme["muted"],
    )

    return img


# ══════════════════════════════════════════════════════════════════════════════
# CHANGELOG scene generators
# ══════════════════════════════════════════════════════════════════════════════


def scene_changelog_title(data, theme, since):
    """Changelog title: WHAT SHIPPED + time period."""
    img = gradient_bg(theme["bg"], theme["bg_alt"])
    draw = ImageDraw.Draw(img)

    a = accent(theme, 0)
    name = data.get("name", "Project")

    draw_text_centered(draw, 300, "WHAT SHIPPED", font("bold", 72), a)
    draw_horizontal_rule(draw, 400, theme["very_muted"])
    draw_text_centered(
        draw, 440, name, font("light", 36), theme["white"]
    )
    if since:
        draw_text_centered(
            draw, 520, f"Since {since}", font("regular", 26), theme["muted"]
        )

    return img


def scene_changelog_pr(pr, theme, color):
    """Per-PR card: title, number, diff stats."""
    img = solid_bg(theme["bg"])
    draw = ImageDraw.Draw(img)

    draw_accent_bar(draw, color, x=160, y_start=300, y_end=700)

    title = pr.get("title", "Untitled PR")
    number = pr.get("number", "")
    additions = pr.get("additions", 0)
    deletions = pr.get("deletions", 0)

    # PR number
    draw.text(
        (200, 310),
        f"#{number}" if number else "",
        font=font("bold", 24),
        fill=hex_to_rgb(theme["very_muted"]),
    )

    # PR title
    lines = wrap_text(title, font("bold", 40), W - 450, draw)
    for i, line in enumerate(lines[:3]):
        draw.text(
            (200, 360 + i * 55), line, font=font("bold", 40), fill=hex_to_rgb(theme["white"])
        )

    # Diff stats
    stats_y = 560
    if additions:
        draw.text(
            (200, stats_y),
            f"+{additions}",
            font=font("bold", 28),
            fill=hex_to_rgb("#2BAC76"),
        )
    if deletions:
        draw.text(
            (380, stats_y),
            f"-{deletions}",
            font=font("bold", 28),
            fill=hex_to_rgb("#E01E5A"),
        )

    return img


def scene_changelog_stats(data, prs, theme):
    """Changelog summary: total PRs, lines changed, contributors."""
    img = solid_bg(theme["bg_dark"])
    draw = ImageDraw.Draw(img)

    a = accent(theme, 4)
    draw_text_centered(draw, 200, "SPRINT SUMMARY", font("bold", 48), a)

    total_prs = len(prs)
    total_additions = sum(pr.get("additions", 0) for pr in prs)
    total_deletions = sum(pr.get("deletions", 0) for pr in prs)
    total_lines = total_additions + total_deletions
    contributors = len(set(pr.get("author", "") for pr in prs if pr.get("author")))

    stats = [
        (str(total_prs), "PRs MERGED"),
        (f"{total_lines:,}", "LINES CHANGED"),
        (str(contributors), "CONTRIBUTORS"),
    ]

    cell_w = W // (len(stats) + 1)
    start_x = (W - cell_w * len(stats)) // 2

    for i, (value, label) in enumerate(stats):
        cx = start_x + i * cell_w + cell_w // 2
        cy = 420

        bbox = draw.textbbox((0, 0), value, font=font("bold", 60))
        vw = bbox[2] - bbox[0]
        draw.text(
            (cx - vw // 2, cy), value, font=font("bold", 60), fill=hex_to_rgb(theme["white"])
        )

        bbox = draw.textbbox((0, 0), label, font=font("regular", 20))
        lw = bbox[2] - bbox[0]
        draw.text(
            (cx - lw // 2, cy + 75),
            label,
            font=font("regular", 20),
            fill=hex_to_rgb(theme["very_muted"]),
        )

    return img


def scene_changelog_closing(data, theme):
    """Changelog closing: repo URL."""
    img = gradient_bg(theme["bg"], theme["bg_alt"])
    draw = ImageDraw.Draw(img)

    name = data.get("name", "Project")
    repo_url = data.get("repo_url", "")

    draw_text_centered(draw, 400, name.upper(), font("bold", 56), theme["white"])

    if repo_url:
        display = repo_url.replace("https://", "").replace("http://", "")
        draw_text_centered(
            draw, 500, display, font("regular", 26), theme["very_muted"]
        )

    return img


# ══════════════════════════════════════════════════════════════════════════════
# Frame rendering and FFmpeg assembly
# ══════════════════════════════════════════════════════════════════════════════


def render_frames(scene_list):
    """
    Render scene images to PNG files.

    scene_list: list of (image_fn, duration, transition_type, transition_duration)
        where image_fn is a callable returning a PIL Image
    Returns: list of Path objects for saved PNGs
    """
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, (image_fn, *_rest) in enumerate(scene_list):
        path = FRAMES_DIR / f"scene_{i + 1:02d}.png"
        print(f"  Rendering {path.name}...")
        img = image_fn()
        img = add_grain(img)
        img.save(path, "PNG")
        paths.append(path)
    return paths


def build_ffmpeg_cmd(scenes, frame_paths, output_path):
    """
    Build FFmpeg command with chained xfade transitions.

    scenes: list of (duration_secs, transition_type, transition_duration)
    frame_paths: list of Path objects for scene PNGs
    """
    n = len(scenes)
    inputs = []
    for i, (dur, _, _) in enumerate(scenes):
        inputs.extend(["-loop", "1", "-t", str(dur), "-i", str(frame_paths[i])])

    filters = []
    cumulative = scenes[0][0]  # duration of first scene

    for i in range(1, n):
        dur_i, _, _ = scenes[i]
        _, out_trans, out_dur = scenes[i - 1]

        left = f"[{0}]" if i == 1 else f"[v{i - 1}]"
        right = f"[{i}]"

        offset = cumulative - out_dur

        if i < n - 1:
            filters.append(
                f"{left}{right}xfade=transition={out_trans}:duration={out_dur}:offset={offset:.2f}[v{i}]"
            )
        else:
            filters.append(
                f"{left}{right}xfade=transition={out_trans}:duration={out_dur}:offset={offset:.2f}[vlast]"
            )

        cumulative += dur_i - out_dur

    # Final fade to black
    filters.append(f"[vlast]fade=t=out:st={cumulative - 1.0:.2f}:d=1.0[vout]")

    filter_complex = ";\n    ".join(filters)

    cmd = [
        "ffmpeg",
        "-y",
        *inputs,
        "-filter_complex",
        filter_complex,
        "-map",
        "[vout]",
        "-r",
        str(FPS),
        "-pix_fmt",
        "yuv420p",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        str(output_path),
    ]
    return cmd


# ══════════════════════════════════════════════════════════════════════════════
# Scene list builders (per mode)
# ══════════════════════════════════════════════════════════════════════════════


def build_showcase_scenes(data, theme, screenshot_path=None):
    """
    Build scene list for showcase mode.

    Returns: list of (image_fn, duration, transition_type, transition_duration)
    """
    scenes = []

    # Title — 3s
    scenes.append((lambda: scene_title(data, theme), 3.0, "fadeblack", 0.5))

    # Context — 4s
    scenes.append((lambda: scene_context(data, theme), 4.0, "fadeblack", 0.5))

    # Tech stack — 4s
    scenes.append((lambda: scene_tech_stack(data, theme), 4.0, "fadeblack", 0.5))

    # Architecture — 4s
    scenes.append(
        (lambda: scene_architecture(data, theme, screenshot_path), 4.0, "slideleft", 0.4)
    )

    # Features — 4s each, slideleft between them
    features = data.get("features", [])
    if len(features) >= 2:
        for i, feat in enumerate(features[:4]):
            feat_text = feat if isinstance(feat, str) else str(feat)
            # Capture loop variable
            scenes.append(
                (
                    (lambda ft=feat_text, ix=i: scene_feature(data, theme, ft, ix)),
                    4.0,
                    "slideleft",
                    0.4,
                )
            )

    # Demo — 4s (only if screenshot exists)
    if screenshot_path and Path(screenshot_path).exists():
        scenes.append(
            (lambda: scene_demo(data, theme, screenshot_path), 4.0, "fadeblack", 0.5)
        )

    # Stats — 3.5s
    scenes.append((lambda: scene_stats(data, theme), 3.5, "fadeblack", 0.5))

    # Closing — 4s, no outgoing transition
    scenes.append((lambda: scene_closing(data, theme), 4.0, None, 0))

    return scenes


def build_comparison_scenes(repos, theme, winner_index=0):
    """Build scene list for comparison mode."""
    scenes = []

    # Title
    scenes.append((lambda: scene_compare_title(repos, theme), 3.0, "fadeblack", 0.5))

    # Setup
    scenes.append((lambda: scene_compare_setup(repos, theme), 4.0, "fadeblack", 0.5))

    # Per-repo cards
    for i, repo_data in enumerate(repos):
        color = accent(theme, i)
        scenes.append(
            (
                (lambda d=repo_data, c=color: scene_compare_repo(d, theme, c)),
                4.0,
                "slideleft",
                0.4,
            )
        )

    # Verdict
    scenes.append(
        (lambda: scene_compare_verdict(repos, winner_index, theme), 4.0, "fadeblack", 0.5)
    )

    # Closing — no outgoing transition
    scenes.append((lambda: scene_compare_closing(theme), 4.0, None, 0))

    return scenes


def build_changelog_scenes(data, theme, since=None):
    """Build scene list for changelog mode."""
    scenes = []
    prs = data.get("recent_prs", [])

    # Title
    scenes.append(
        (lambda: scene_changelog_title(data, theme, since), 3.0, "fadeblack", 0.5)
    )

    # Per-PR cards
    for i, pr in enumerate(prs[:8]):
        color = accent(theme, i)
        scenes.append(
            (
                (lambda p=pr, c=color: scene_changelog_pr(p, theme, c)),
                4.0,
                "slideleft",
                0.4,
            )
        )

    # Summary stats
    scenes.append(
        (lambda: scene_changelog_stats(data, prs, theme), 3.5, "fadeblack", 0.5)
    )

    # Closing — no outgoing transition
    scenes.append((lambda: scene_changelog_closing(data, theme), 4.0, None, 0))

    return scenes


# ══════════════════════════════════════════════════════════════════════════════
# Orchestration
# ══════════════════════════════════════════════════════════════════════════════


def load_research(path):
    """Load research JSON from file."""
    with open(path, "r") as f:
        return json.load(f)


def run_research(repo_url, app_url=None):
    """Import and run the research module."""
    sys.path.insert(0, str(SCRIPTS_DIR))
    try:
        from research_project import research_project

        return research_project(repo_url, url=app_url)
    except ImportError:
        print("Error: research_project.py not found. Use --research to provide pre-computed JSON.")
        sys.exit(1)


def find_screenshot(data):
    """Look for a screenshot in the screenshots directory."""
    screenshots_dir = BASE_DIR / "screenshots"
    if not screenshots_dir.exists():
        return None
    name = data.get("name", "").lower().replace(" ", "-")
    for ext in ["png", "jpg", "jpeg"]:
        path = screenshots_dir / f"{name}.{ext}"
        if path.exists():
            return str(path)
    # Try any screenshot
    for f in screenshots_dir.iterdir():
        if f.suffix.lower() in (".png", ".jpg", ".jpeg"):
            return str(f)
    return None


def generate_video(data, theme_name="midnight", output_path=None, dry_run=False,
                   mode="showcase", repos=None, since=None, screenshot_path=None):
    """
    Main generation entry point. Importable from other modules.

    Args:
        data: Research JSON dict (for showcase/changelog) or None (for comparison)
        theme_name: Theme key from THEMES dict
        output_path: Output MP4 path (default: output/project_video.mp4)
        dry_run: If True, generate PNGs only
        mode: "showcase", "comparison", or "changelog"
        repos: List of research dicts (for comparison mode)
        since: Time period string (for changelog mode)
        screenshot_path: Path to screenshot image

    Returns:
        Path to output file (MP4 or frames directory)
    """
    theme = THEMES.get(theme_name, THEMES["midnight"])

    # Normalize: research outputs "url", scenes expect "repo_url"
    if data and "repo_url" not in data and "url" in data:
        data["repo_url"] = data["url"]

    if output_path is None:
        output_path = OUTPUT_DIR / "project_video.mp4"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Auto-detect screenshot if not provided
    if screenshot_path is None and data is not None:
        screenshot_path = find_screenshot(data)

    # Build scene list based on mode
    if mode == "comparison" and repos:
        scene_list = build_comparison_scenes(repos, theme)
    elif mode == "changelog" and data:
        scene_list = build_changelog_scenes(data, theme, since)
    else:
        scene_list = build_showcase_scenes(data, theme, screenshot_path)

    print(f"\n=== Project Video Generator ===")
    print(f"Mode: {mode} | Theme: {theme_name} | Scenes: {len(scene_list)}\n")

    # Render frames
    print("1. Rendering scene frames...")
    frame_paths = render_frames(scene_list)
    print(f"   Done: {len(frame_paths)} frames in {FRAMES_DIR}\n")

    if dry_run:
        print("Dry run complete. Frames saved to:")
        for p in frame_paths:
            print(f"  {p}")
        return FRAMES_DIR

    # Build FFmpeg scene timing data: (duration, transition, trans_dur)
    ffmpeg_scenes = [(dur, trans, tdur) for (_, dur, trans, tdur) in scene_list]

    print("2. Building FFmpeg command...")
    cmd = build_ffmpeg_cmd(ffmpeg_scenes, frame_paths, output_path)
    print("   Filter chain built\n")

    print("3. Running FFmpeg...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"   FFmpeg FAILED (exit {result.returncode})")
        stderr = result.stderr
        print(stderr[-2000:] if len(stderr) > 2000 else stderr)
        sys.exit(1)

    file_size = output_path.stat().st_size / 1024 / 1024
    print(f"   Output: {output_path}")
    print(f"   Size: {file_size:.1f} MB\n")

    # Quick probe
    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_format", "-show_streams", str(output_path)],
            capture_output=True,
            text=True,
        )
        for line in probe.stdout.splitlines():
            if any(k in line for k in ["duration=", "width=", "height=", "r_frame_rate="]):
                print(f"   {line.strip()}")
    except FileNotFoundError:
        pass  # ffprobe not available

    # Open with system viewer
    try:
        if platform.system() == "Darwin":
            subprocess.Popen(["open", str(output_path)])
        elif platform.system() == "Linux":
            subprocess.Popen(["xdg-open", str(output_path)])
    except Exception:
        pass

    print("\nDone!")
    return output_path


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════


def build_parser():
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate highlight reel videos for software projects."
    )
    subparsers = parser.add_subparsers(dest="command")

    # Default (showcase) arguments on the main parser
    parser.add_argument("--repo", help="GitHub repo URL or local path")
    parser.add_argument("--url", help="Deployed app URL for live screenshots")
    parser.add_argument("--research", help="Path to pre-computed research JSON")
    parser.add_argument(
        "--theme", default="midnight", choices=list(THEMES.keys()),
        help="Color theme (default: midnight)",
    )
    parser.add_argument(
        "--output", help="Output MP4 path (default: output/project_video.mp4)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Generate PNGs only, skip FFmpeg"
    )

    # Compare subcommand
    compare_parser = subparsers.add_parser("compare", help="Compare multiple repos")
    compare_parser.add_argument("repos", nargs="+", help="GitHub repo URLs to compare")
    compare_parser.add_argument(
        "--theme", default="midnight", choices=list(THEMES.keys())
    )
    compare_parser.add_argument("--output", help="Output MP4 path")
    compare_parser.add_argument("--dry-run", action="store_true")

    # Changelog subcommand
    changelog_parser = subparsers.add_parser("changelog", help="Sprint recap video")
    changelog_parser.add_argument("--repo", required=True, help="GitHub repo URL")
    changelog_parser.add_argument("--since", default="last week", help="Time period")
    changelog_parser.add_argument("--url", help="Deployed app URL")
    changelog_parser.add_argument(
        "--theme", default="midnight", choices=list(THEMES.keys())
    )
    changelog_parser.add_argument("--output", help="Output MP4 path")
    changelog_parser.add_argument("--dry-run", action="store_true")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "compare":
        # Comparison mode: research each repo independently
        repos = []
        for repo_url in args.repos:
            print(f"Researching {repo_url}...")
            data = run_research(repo_url)
            repos.append(data)

        generate_video(
            data=None,
            theme_name=args.theme,
            output_path=args.output,
            dry_run=args.dry_run,
            mode="comparison",
            repos=repos,
        )

    elif args.command == "changelog":
        # Changelog mode
        if args.repo:
            data = run_research(args.repo, app_url=getattr(args, "url", None))
        else:
            print("Error: --repo is required for changelog mode.")
            sys.exit(1)

        generate_video(
            data=data,
            theme_name=args.theme,
            output_path=args.output,
            dry_run=args.dry_run,
            mode="changelog",
            since=args.since,
        )

    else:
        # Showcase mode (default)
        if args.research:
            data = load_research(args.research)
        elif args.repo:
            data = run_research(args.repo, app_url=args.url)
        else:
            print("Error: provide --repo or --research.")
            parser.print_help()
            sys.exit(1)

        generate_video(
            data=data,
            theme_name=args.theme,
            output_path=args.output,
            dry_run=args.dry_run,
            mode="showcase",
        )


if __name__ == "__main__":
    main()
