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
import math
import platform
import random
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ── Config ───────────────────────────────────────────────────────────────────

W, H = 1920, 1080
FPS = 30

BASE_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = Path(__file__).parent
FRAMES_DIR = BASE_DIR / "output" / "frames"
OUTPUT_DIR = BASE_DIR / "output"

# ── Layout constants (all relative to W/H for easy resizing) ────────────────

MARGIN = 120                    # outer margin from edges
PANEL_RADIUS = 16               # rounded corner radius for floating panels
PANEL_OPACITY = 0.06            # panel fill opacity over background
ACCENT_BAR_W = 5                # width of vertical accent bars
PROGRESS_DOT_Y = H - 60        # y position of progress dots
PROGRESS_DOT_R = 4              # radius of active progress dot
PROGRESS_DOT_SPACING = 20       # spacing between progress dots
GLOW_DEFAULT_RADIUS = 600       # default radial glow radius
GLOW_DEFAULT_INTENSITY = 0.15   # default glow intensity

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
        "bg": "#080810",
        "bg_alt": "#0C0C1A",
        "bg_dark": "#050508",
        "white": "#F0F0FF",
        "muted": "#9090B0",
        "very_muted": "#505070",
        "accents": ["#E8976C", "#F0B86A", "#C084FC", "#60A5FA", "#4ECDC4", "#FF6B9D"],
        "glow": "#E8976C",       # warm amber glow
        "glow_alt": "#C084FC",   # secondary violet glow
    },
    "aurora": {
        "bg": "#060D18",
        "bg_alt": "#0A1425",
        "bg_dark": "#040810",
        "white": "#E8F0FF",
        "muted": "#7A9CC6",
        "very_muted": "#4A6A8A",
        "accents": ["#00D4AA", "#4ECDC4", "#FF6B9D", "#C084FC", "#FCD34D", "#60A5FA"],
        "glow": "#00D4AA",
        "glow_alt": "#4ECDC4",
    },
    "ember": {
        "bg": "#100808",
        "bg_alt": "#180C0C",
        "bg_dark": "#0A0505",
        "white": "#FFF0E8",
        "muted": "#C69A88",
        "very_muted": "#8A6A5A",
        "accents": ["#FF6B35", "#FF4444", "#FFB347", "#E85D75", "#C084FC", "#4ECDC4"],
        "glow": "#FF6B35",
        "glow_alt": "#FFB347",
    },
    "mono": {
        "bg": "#0A0A0A",
        "bg_alt": "#121212",
        "bg_dark": "#060606",
        "white": "#EEEEEE",
        "muted": "#888888",
        "very_muted": "#555555",
        "accents": ["#FFFFFF", "#CCCCCC", "#AAAAAA", "#999999", "#777777", "#DDDDDD"],
        "glow": "#444444",
        "glow_alt": "#333333",
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


def radial_glow_bg(theme, glow_pos=(0.8, 0.3), glow_radius=600, intensity=0.15,
                   secondary_pos=None, secondary_radius=400, secondary_intensity=0.08):
    """Create a dark background with soft radial glow light sources.

    This is the signature cinematic look — deep dark base with warm light
    bleeding in from off-center positions, like sunrise through a window.
    """
    img = gradient_bg(theme["bg"], theme["bg_alt"])
    pixels = img.load()
    bg_rgb = hex_to_rgb(theme["bg"])
    glow_rgb = hex_to_rgb(theme.get("glow", theme["accents"][0]))
    gx, gy = int(glow_pos[0] * W), int(glow_pos[1] * H)

    for y in range(H):
        for x in range(W):
            dist = math.sqrt((x - gx) ** 2 + (y - gy) ** 2)
            if dist < glow_radius * 1.5:
                falloff = max(0.0, 1.0 - (dist / glow_radius) ** 1.8)
                alpha = falloff * intensity
                r, g, b = pixels[x, y]
                pixels[x, y] = (
                    min(255, int(r + (glow_rgb[0] - r) * alpha)),
                    min(255, int(g + (glow_rgb[1] - g) * alpha)),
                    min(255, int(b + (glow_rgb[2] - b) * alpha)),
                )

    # Optional secondary glow (cooler accent from opposite side)
    if secondary_pos:
        glow2_rgb = hex_to_rgb(theme.get("glow_alt", theme["accents"][1]))
        gx2, gy2 = int(secondary_pos[0] * W), int(secondary_pos[1] * H)
        for y in range(H):
            for x in range(W):
                dist = math.sqrt((x - gx2) ** 2 + (y - gy2) ** 2)
                if dist < secondary_radius * 1.5:
                    falloff = max(0.0, 1.0 - (dist / secondary_radius) ** 1.8)
                    alpha = falloff * secondary_intensity
                    r, g, b = pixels[x, y]
                    pixels[x, y] = (
                        min(255, int(r + (glow2_rgb[0] - r) * alpha)),
                        min(255, int(g + (glow2_rgb[1] - g) * alpha)),
                        min(255, int(b + (glow2_rgb[2] - b) * alpha)),
                    )
    return img


def draw_floating_panel(draw, x, y, w, h, theme, accent=None, opacity=None):
    """Draw a floating semi-transparent card panel with subtle border.

    Creates depth by drawing a filled rectangle with a thin border.
    The panel sits on top of the glow background, creating layered depth.
    """
    if opacity is None:
        opacity = PANEL_OPACITY
    bg_rgb = hex_to_rgb(theme["bg_alt"])
    fill = tuple(min(255, int(c + 255 * opacity)) for c in bg_rgb)
    draw.rounded_rectangle([x, y, x + w, y + h], radius=PANEL_RADIUS, fill=fill)
    border_color = hex_to_rgb(accent if accent else theme["very_muted"])
    border_top = tuple(min(255, c + 30) for c in border_color)
    draw.rounded_rectangle([x, y, x + w, y + h], radius=PANEL_RADIUS, outline=border_top)


def draw_progress_dots(draw, current, total, theme, y=None):
    """Draw small progress indicator dots at the bottom of the frame."""
    if y is None:
        y = PROGRESS_DOT_Y
    total_width = (total - 1) * PROGRESS_DOT_SPACING
    start_x = (W - total_width) // 2
    for i in range(total):
        cx = start_x + i * PROGRESS_DOT_SPACING
        if i == current:
            color = hex_to_rgb(theme.get("glow", theme["accents"][0]))
            draw.ellipse([cx - PROGRESS_DOT_R, y - PROGRESS_DOT_R,
                          cx + PROGRESS_DOT_R, y + PROGRESS_DOT_R], fill=color)
        else:
            color = hex_to_rgb(theme["very_muted"])
            draw.ellipse([cx - 2, y - 2, cx + 2, y + 2], fill=color)


# ── Extra mode effects (animated) ───────────────────────────────────────────
# "Spicy" visual effects — default ON. Each animated effect takes an image,
# theme, and `t` (0.0–1.0 progress through the scene) so particles drift,
# wisps rise, and the video feels alive rather than frozen.

EFFECT_FPS = 10  # frames per second for animated effects (keeps render fast)


def _generate_spark_particles(count, seed):
    """Pre-generate spark positions/properties so they're consistent across frames."""
    rng = random.Random(seed or 101)
    particles = []
    for _ in range(count):
        if rng.random() < 0.6:
            x = rng.choice([rng.randint(0, W // 5), rng.randint(W * 4 // 5, W)])
        else:
            x = rng.randint(0, W)
        y = rng.randint(0, H)
        size = rng.uniform(1, 3.5)
        brightness = rng.uniform(0.4, 1.0)
        drift_speed = rng.uniform(15, 60)  # pixels per second upward
        twinkle_phase = rng.uniform(0, math.pi * 2)
        twinkle_speed = rng.uniform(2, 5)
        particles.append((x, y, size, brightness, drift_speed, twinkle_phase, twinkle_speed))
    return particles


def fx_sparks(img, theme, t=0.0, count=40, seed=None, _particles=None):
    """Animated particle sparks — drift upward and twinkle over time.

    The seed controls both positions AND visual character: different seeds
    produce sparks that cluster in different regions, use different accent
    colors, and drift at different speeds — so each scene feels unique.
    """
    if _particles is None:
        _particles = _generate_spark_particles(count, seed)

    draw = ImageDraw.Draw(img)

    # Pick spark color from theme accents based on seed — each scene gets
    # a different color temperature instead of always using the glow color.
    rng_color = random.Random(seed or 0)
    accent_idx = rng_color.randint(0, len(theme["accents"]) - 1)
    spark_rgb = hex_to_rgb(theme["accents"][accent_idx])
    white = (255, 255, 255)
    duration = 5.0

    for (bx, by, size, brightness, drift_speed, twinkle_phase, twinkle_speed) in _particles:
        time_s = t * duration
        y = (by - drift_speed * time_s) % H
        x = bx + math.sin(time_s * 0.8 + twinkle_phase) * 5

        twinkle = 0.5 + 0.5 * math.sin(time_s * twinkle_speed + twinkle_phase)
        cur_brightness = brightness * (0.3 + 0.7 * twinkle)

        color = tuple(int(spark_rgb[i] + (white[i] - spark_rgb[i]) * cur_brightness) for i in range(3))

        # Halo for larger sparks
        if size > 2 and cur_brightness > 0.5:
            halo_r = size * 2.5
            for hy in range(max(0, int(y - halo_r)), min(H, int(y + halo_r))):
                for hx in range(max(0, int(x - halo_r)), min(W, int(x + halo_r))):
                    dist = math.sqrt((hx - x) ** 2 + (hy - y) ** 2)
                    if dist < halo_r:
                        alpha = max(0, (1 - dist / halo_r) ** 2) * 0.12 * cur_brightness
                        r, g, b = img.getpixel((hx, hy))
                        img.putpixel((hx, hy), (
                            min(255, int(r + color[0] * alpha)),
                            min(255, int(g + color[1] * alpha)),
                            min(255, int(b + color[2] * alpha)),
                        ))

        cur_size = size * (0.6 + 0.4 * twinkle)
        ix, iy = int(x), int(y)
        if 0 < ix < W - 1 and 0 < iy < H - 1:
            draw.ellipse([ix - cur_size, iy - cur_size, ix + cur_size, iy + cur_size], fill=color)

    return img


def _generate_wisp_params(count, seed):
    """Pre-generate wisp positions so they're consistent across frames."""
    rng = random.Random(seed or 202)
    wisps = []
    for _ in range(count):
        cx = rng.randint(W // 6, W * 5 // 6)
        base_y = rng.randint(H * 2 // 3, H - 50)
        wisp_h = rng.randint(150, 350)
        wisp_w = rng.randint(30, 70)
        intensity = rng.uniform(0.04, 0.09)
        phase = rng.uniform(0, math.pi * 2)
        wisps.append((cx, base_y, wisp_h, wisp_w, intensity, phase))
    return wisps


def fx_heat_wisps(img, theme, t=0.0, count=5, seed=None, _wisps=None):
    """Animated heat wisps — rise slowly and sway over time."""
    if _wisps is None:
        _wisps = _generate_wisp_params(count, seed)

    pixels = img.load()
    glow_rgb = hex_to_rgb(theme.get("glow", theme["accents"][0]))
    duration = 5.0
    time_s = t * duration

    for (cx, base_y, wisp_h, wisp_w, intensity, phase) in _wisps:
        # Wisps rise over time
        rise_offset = int(time_s * 20)  # 20 px/sec upward
        # Intensity pulses gently
        pulse = 0.7 + 0.3 * math.sin(time_s * 1.5 + phase)

        for dy in range(0, wisp_h, 2):  # step by 2 for speed
            y = base_y - dy - rise_offset
            if y < 0 or y >= H:
                continue
            falloff = (1 - dy / wisp_h) ** 1.5
            spread = int(wisp_w * (1 + dy / wisp_h * 0.5))
            # Wobble shifts over time
            wobble = int(math.sin(dy * 0.05 + time_s * 2 + phase) * 18)

            for dx in range(-spread, spread, 2):  # step by 2 for speed
                x = cx + dx + wobble
                if 0 <= x < W:
                    dist_norm = abs(dx) / max(spread, 1)
                    alpha = falloff * (1 - dist_norm ** 2) * intensity * pulse
                    if alpha > 0.005:
                        r, g, b = pixels[x, y]
                        pixels[x, y] = (
                            min(255, int(r + glow_rgb[0] * alpha)),
                            min(255, int(g + glow_rgb[1] * alpha)),
                            min(255, int(b + glow_rgb[2] * alpha * 0.5)),
                        )
    return img


def fx_laser_streaks(img, theme, t=0.0, count=3, seed=None):
    """Soft light beams that sweep slowly — like stage lighting or god rays.

    Much softer than actual lasers: wide, low-opacity, with gentle falloff.
    Different accent colors per beam based on seed.
    """
    rng = random.Random(seed or 303)
    duration = 5.0
    time_s = t * duration

    for i in range(count):
        color_hex = theme["accents"][rng.randint(0, len(theme["accents"]) - 1)]
        color_rgb = hex_to_rgb(color_hex)

        # Beams sweep slowly: different speeds and directions per beam
        sweep = int(time_s * 40 * (0.5 + i * 0.5))
        x1 = rng.randint(-200, W + 200) + sweep
        y1 = rng.choice([rng.randint(-100, 0), rng.randint(H, H + 100)])
        x2 = rng.randint(-200, W + 200) + sweep
        y2 = H - y1 + rng.randint(-200, 200)

        # Draw as multiple progressively wider, dimmer lines for a soft glow
        pixels = img.load()
        # Calculate line direction for perpendicular spread
        dx = x2 - x1
        dy = y2 - y1
        line_len = max(1, math.sqrt(dx * dx + dy * dy))
        # Normal direction (perpendicular to line)
        nx = -dy / line_len
        ny = dx / line_len

        beam_width = 25  # pixels of soft spread
        steps = 100  # points along the line
        for step in range(steps):
            frac = step / steps
            cx = int(x1 + dx * frac)
            cy = int(y1 + dy * frac)

            for offset in range(-beam_width, beam_width + 1, 2):
                px = int(cx + nx * offset)
                py = int(cy + ny * offset)
                if 0 <= px < W and 0 <= py < H:
                    # Gaussian-ish falloff from center of beam
                    falloff = math.exp(-(offset * offset) / (2 * (beam_width * 0.4) ** 2))
                    alpha = falloff * 0.04  # very low opacity
                    r, g, b = pixels[px, py]
                    pixels[px, py] = (
                        min(255, int(r + color_rgb[0] * alpha)),
                        min(255, int(g + color_rgb[1] * alpha)),
                        min(255, int(b + color_rgb[2] * alpha)),
                    )

    return img


def fx_scanlines(img, theme, t=0.0, spacing=4, opacity=0.06):
    """Subtle horizontal scanlines — static texture, slight scroll over time."""
    y_offset = int(t * spacing * 2) % spacing  # subtle scroll
    for y in range(y_offset, H, spacing):
        for x in range(0, W, 3):
            if 0 <= x < W and 0 <= y < H:
                r, g, b = img.getpixel((x, y))
                img.putpixel((x, y), (
                    int(r * (1 - opacity)),
                    int(g * (1 - opacity)),
                    int(b * (1 - opacity)),
                ))
    return img


# ── Effect arc ──────────────────────────────────────────────────────────────
# The video tells a visual story through its effects:
#
#   Opening  →  calm  →  building  →  climax  →  finale
#   (warm)     (cool)    (energy)    (peak)     (everything)
#
# Each scene gets a "mood" based on its position. The mood determines
# which effects appear AND how they're parameterized (color, count, speed).
# Simple: 5 moods, mapped by position. No randomness.

_FX_FUNCS = {
    "sparks": fx_sparks,
    "heat_wisps": fx_heat_wisps,
    "laser_streaks": fx_laser_streaks,
    "scanlines": fx_scanlines,
}

# The five moods and what they look like
_MOODS = {
    "opening":  {"fx": ["sparks", "heat_wisps"],  "spark_count": 45, "wisp_count": 5, "accent_idx": 0},
    "calm":     {"fx": ["sparks"],                 "spark_count": 20, "wisp_count": 0, "accent_idx": 1},
    "texture":  {"fx": ["scanlines", "sparks"],    "spark_count": 15, "wisp_count": 0, "accent_idx": 2},
    "energy":   {"fx": ["laser_streaks", "sparks"],"spark_count": 25, "wisp_count": 0, "accent_idx": 3},
    "warmth":   {"fx": ["heat_wisps", "sparks"],   "spark_count": 30, "wisp_count": 4, "accent_idx": 4},
    "finale":   {"fx": ["sparks", "heat_wisps", "laser_streaks"], "spark_count": 50, "wisp_count": 6, "accent_idx": 0},
}


def plan_fx_arc(total_scenes):
    """Plan the full effects arc for a video.

    Returns a list of mood names, one per scene. The arc always starts
    with 'opening', ends with 'finale', and distributes the middle moods
    so they cycle without repeating neighbors.

    This is the whole coordination algorithm — simple and predictable.
    """
    if total_scenes <= 2:
        return ["opening"] + ["finale"] * (total_scenes - 1)

    arc = ["opening"]

    # Middle moods cycle through these in order, creating variety
    middle_cycle = ["calm", "texture", "energy", "warmth"]
    for i in range(1, total_scenes - 1):
        arc.append(middle_cycle[(i - 1) % len(middle_cycle)])

    arc.append("finale")
    return arc


def apply_extra_fx(img, theme, scene_kind, scene_idx, t=0.0,
                   total_scenes=1):
    """Apply effects for this scene based on the planned arc."""
    arc = plan_fx_arc(total_scenes)
    mood_name = arc[scene_idx] if scene_idx < len(arc) else "calm"
    mood = _MOODS[mood_name]

    for name in mood["fx"]:
        fx_func = _FX_FUNCS.get(name)
        if not fx_func:
            continue

        # Each scene uses a different accent color — the mood picks the offset
        # and the scene_idx shifts it further so even same-mood scenes differ
        seed = (scene_idx * 137 + mood["accent_idx"] * 31) % 10000

        if name == "sparks":
            img = fx_func(img, theme, t=t, seed=seed, count=mood["spark_count"])
        elif name == "heat_wisps":
            img = fx_func(img, theme, t=t, seed=seed, count=mood["wisp_count"])
        elif name == "laser_streaks":
            img = fx_func(img, theme, t=t, seed=seed, count=2)
        elif name == "scanlines":
            img = fx_func(img, theme, t=t)

    return img


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


def add_grain(img, intensity=6):
    """Add subtle film grain for a premium feel. Uses numpy-style random for speed."""
    pixels = img.load()
    # Sample fewer points but spread them — gives natural grain texture
    rng = random.Random(42)  # deterministic for consistent frames
    for y in range(0, H, 2):
        for x in range(0, W, 2):
            noise = rng.randint(-intensity, intensity)
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


def scene_title(data, theme, scene_idx=0, total_scenes=1):
    """Title card: cinematic glow bg, project name, description, repo URL."""
    img = radial_glow_bg(theme, glow_pos=(0.5, 0.35), glow_radius=700, intensity=0.18,
                         secondary_pos=(0.15, 0.85), secondary_radius=400, secondary_intensity=0.06)
    draw = ImageDraw.Draw(img)

    name = data.get("name", "Project")
    description = data.get("description", "")
    repo_url = data.get("repo_url", "")
    a = accent(theme, 0)

    # Project name — large, centered, warm
    draw_text_centered(draw, 340, name.upper(), font("bold", 78), theme["white"])

    # Accent-colored thin rule
    rule_w = min(len(name) * 35, 600)
    rule_x = (W - rule_w) // 2
    draw.rectangle([rule_x, 440, rule_x + rule_w, 442], fill=hex_to_rgb(a))

    if description:
        lines = wrap_text(description, font("light", 30), W - 500, draw)
        for i, line in enumerate(lines[:2]):
            draw_text_centered(
                draw, 475 + i * 44, line, font("light", 30), theme["muted"]
            )

    if repo_url:
        display_url = repo_url.replace("https://", "").replace("http://", "")
        draw_text_centered(
            draw, 620, display_url, font("regular", 20), theme["very_muted"]
        )

    draw_progress_dots(draw, scene_idx, total_scenes, theme)
    return img


def scene_context(data, theme, scene_idx=0, total_scenes=1):
    """Context card: project overview from README summary with floating panel."""
    img = radial_glow_bg(theme, glow_pos=(0.2, 0.4), glow_radius=500, intensity=0.12,
                         secondary_pos=(0.9, 0.8), secondary_radius=350, secondary_intensity=0.05)
    draw = ImageDraw.Draw(img)

    a = accent(theme, 0)

    # Floating panel
    panel_x, panel_y = 120, 160
    panel_w, panel_h = W - 240, 700
    draw_floating_panel(draw, panel_x, panel_y, panel_w, panel_h, theme, accent=a)

    # Accent bar inside panel
    draw_accent_bar(draw, a, x=panel_x + 30, y_start=panel_y + 30, y_end=panel_y + panel_h - 30)

    draw.text(
        (panel_x + 60, panel_y + 40), "THE PROJECT",
        font=font("bold", 44), fill=hex_to_rgb(a)
    )

    summary = data.get("readme_summary") or data.get("description") or "No summary available."
    lines = wrap_text(summary, font("light", 28), panel_w - 120, draw)
    for i, line in enumerate(lines[:8]):
        draw.text(
            (panel_x + 60, panel_y + 120 + i * 48), line,
            font=font("light", 28), fill=hex_to_rgb(theme["muted"])
        )

    draw_progress_dots(draw, scene_idx, total_scenes, theme)
    return img


def scene_tech_stack(data, theme, scene_idx=0, total_scenes=1):
    """Tech stack card: languages with glowing bars, deps in a floating panel."""
    img = radial_glow_bg(theme, glow_pos=(0.3, 0.5), glow_radius=500, intensity=0.10,
                         secondary_pos=(0.85, 0.3), secondary_radius=350, secondary_intensity=0.06)
    draw = ImageDraw.Draw(img)

    a = accent(theme, 1)
    languages = data.get("languages", {})
    tech_stack = data.get("tech_stack", [])

    # Left panel: Languages
    lp_x, lp_y = 100, 140
    lp_w = 820
    lp_h = 780
    draw_floating_panel(draw, lp_x, lp_y, lp_w, lp_h, theme, accent=a)

    draw.text(
        (lp_x + 40, lp_y + 30), "LANGUAGES",
        font=font("bold", 20), fill=hex_to_rgb(theme["very_muted"])
    )

    if languages:
        sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
        primary = sorted_langs[0][0]
        draw.text(
            (lp_x + 40, lp_y + 70), primary,
            font=font("bold", 56), fill=hex_to_rgb(theme["white"])
        )

        # Language bars — full width, glowing
        y = lp_y + 170
        max_bar_w = lp_w - 80
        for i, (lang, pct) in enumerate(sorted_langs[:6]):
            color = accent(theme, i)
            color_rgb = hex_to_rgb(color)
            pct_val = float(pct) if isinstance(pct, (int, float)) else 0
            bar_w = max(4, int(max_bar_w * (pct_val / 100.0)))

            # Language name + percentage
            draw.text(
                (lp_x + 40, y), lang,
                font=font("regular", 24), fill=hex_to_rgb(theme["white"])
            )
            pct_text = f"{pct_val:.0f}%"
            pct_bbox = draw.textbbox((0, 0), pct_text, font=font("regular", 24))
            draw.text(
                (lp_x + lp_w - 40 - (pct_bbox[2] - pct_bbox[0]), y), pct_text,
                font=font("regular", 24), fill=hex_to_rgb(theme["muted"])
            )

            # Bar track
            bar_y = y + 38
            bar_h = 8
            draw.rounded_rectangle(
                [lp_x + 40, bar_y, lp_x + 40 + max_bar_w, bar_y + bar_h],
                radius=4, fill=hex_to_rgb(theme["bg_dark"])
            )
            # Filled bar
            if bar_w > 8:
                draw.rounded_rectangle(
                    [lp_x + 40, bar_y, lp_x + 40 + bar_w, bar_y + bar_h],
                    radius=4, fill=color_rgb
                )

            y += 80
    else:
        draw.text(
            (lp_x + 40, lp_y + 80), "No language data",
            font=font("light", 28), fill=hex_to_rgb(theme["very_muted"])
        )

    # Right panel: Tech stack / dependencies
    if tech_stack:
        rp_x = 960
        rp_y = 140
        rp_w = 860
        rp_h = 780
        draw_floating_panel(draw, rp_x, rp_y, rp_w, rp_h, theme, accent=theme["accents"][2])

        draw.text(
            (rp_x + 40, rp_y + 30), "STACK",
            font=font("bold", 20), fill=hex_to_rgb(theme["very_muted"])
        )

        for i, item in enumerate(tech_stack[:12]):
            color = accent(theme, i + 2)
            iy = rp_y + 80 + i * 52
            # Colored dot
            draw.ellipse(
                [rp_x + 40, iy + 10, rp_x + 52, iy + 22], fill=hex_to_rgb(color)
            )
            draw.text(
                (rp_x + 65, iy),
                str(item),
                font=font("regular", 26),
                fill=hex_to_rgb(theme["white"]),
            )

    draw_progress_dots(draw, scene_idx, total_scenes, theme)
    return img


def scene_architecture(data, theme, screenshot_path=None, scene_idx=0, total_scenes=1):
    """Architecture card: directory tree in floating panel, file count."""
    img = radial_glow_bg(theme, glow_pos=(0.7, 0.4), glow_radius=450, intensity=0.10)
    draw = ImageDraw.Draw(img)

    a = accent(theme, 2)
    tree = data.get("tree_summary", "")
    total_files = data.get("total_files", 0)

    has_shot = screenshot_path and Path(screenshot_path).exists()

    # Parse tree into lines
    if tree:
        lines = [s.strip() for s in tree.replace(", ", "\n").strip().split("\n") if s.strip()]
    else:
        lines = []

    # Panel
    panel_w = 850 if has_shot else W - 240
    panel_x = 120
    panel_y = 140
    panel_h = 780
    draw_floating_panel(draw, panel_x, panel_y, panel_w, panel_h, theme, accent=a)

    draw.text(
        (panel_x + 40, panel_y + 30), "ARCHITECTURE",
        font=font("bold", 20), fill=hex_to_rgb(theme["very_muted"])
    )

    if total_files:
        draw.text(
            (panel_x + 40, panel_y + 65),
            f"{total_files} files",
            font=font("bold", 48), fill=hex_to_rgb(theme["white"])
        )

    # Directory listing with tree-style formatting
    y = panel_y + 150
    max_chars = 45 if has_shot else 70
    for i, line in enumerate(lines[:14]):
        # Add tree prefix character
        prefix = "\u251c\u2500 " if i < len(lines) - 1 else "\u2514\u2500 "
        display = prefix + line[:max_chars]
        color = accent(theme, i) if "files)" in line else theme["muted"]
        draw.text(
            (panel_x + 40, y + i * 38), display,
            font=font("regular", 22), fill=hex_to_rgb(color)
        )

    if has_shot:
        img = add_screenshot_inset(img, screenshot_path, a)

    draw_progress_dots(draw, scene_idx, total_scenes, theme)
    return img


def scene_feature(data, theme, feature_text, index, screenshot_path=None, scene_idx=0, total_scenes=1):
    """Feature card: floating panel with accent glow, feature text prominent."""
    a = accent(theme, index)

    # Vary the glow position per feature for visual rhythm
    glow_positions = [(0.2, 0.4), (0.8, 0.3), (0.3, 0.7), (0.7, 0.6)]
    gp = glow_positions[index % len(glow_positions)]

    img = radial_glow_bg(theme, glow_pos=gp, glow_radius=500, intensity=0.12)
    draw = ImageDraw.Draw(img)

    has_shot = screenshot_path and Path(screenshot_path).exists()

    # Panel
    panel_w = 850 if has_shot else W - 240
    panel_x = 120
    panel_y = 200
    panel_h = 600
    draw_floating_panel(draw, panel_x, panel_y, panel_w, panel_h, theme, accent=a)

    # Accent bar inside panel
    draw_accent_bar(draw, a, x=panel_x + 25, y_start=panel_y + 25, y_end=panel_y + panel_h - 25)

    # Feature number
    draw.text(
        (panel_x + 55, panel_y + 35),
        f"FEATURE {index + 1:02d}",
        font=font("bold", 18), fill=hex_to_rgb(theme["very_muted"])
    )

    # Feature text — large and prominent
    max_w = panel_w - 100 if not has_shot else panel_w - 80
    lines = wrap_text(feature_text, font("bold", 38), max_w, draw)
    for i, line in enumerate(lines[:4]):
        draw.text(
            (panel_x + 55, panel_y + 80 + i * 58), line,
            font=font("bold", 38), fill=hex_to_rgb(theme["white"])
        )

    if has_shot:
        img = add_screenshot_inset(img, screenshot_path, a)

    draw_progress_dots(draw, scene_idx, total_scenes, theme)
    return img


def scene_demo(data, theme, screenshot_path, scene_idx=0, total_scenes=1):
    """Demo card: large centered screenshot with cinematic frame."""
    img = radial_glow_bg(theme, glow_pos=(0.5, 0.5), glow_radius=700, intensity=0.15,
                         secondary_pos=(0.1, 0.2), secondary_radius=300, secondary_intensity=0.05)
    draw = ImageDraw.Draw(img)

    a = accent(theme, 3)
    draw_text_centered(draw, 100, "LIVE DEMO", font("bold", 40), a)

    img = add_screenshot_inset(img, screenshot_path, a, large=True)

    url = data.get("homepage", data.get("repo_url", ""))
    if url:
        display_url = url.replace("https://", "").replace("http://", "")
        draw_text_centered(
            draw, 980, display_url, font("regular", 22), theme["very_muted"]
        )

    draw_progress_dots(draw, scene_idx, total_scenes, theme)
    return img


def scene_stats(data, theme, scene_idx=0, total_scenes=1):
    """Stats card: 2x3 grid of oversized numbers in floating panels."""
    img = radial_glow_bg(theme, glow_pos=(0.5, 0.5), glow_radius=600, intensity=0.12,
                         secondary_pos=(0.9, 0.1), secondary_radius=300, secondary_intensity=0.06)
    draw = ImageDraw.Draw(img)

    a = accent(theme, 4)
    draw_text_centered(draw, 80, "BY THE NUMBERS", font("bold", 20), theme["very_muted"])

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

    # 3x2 grid of mini floating panels
    cols, rows = 3, 2
    cell_w = 500
    cell_h = 340
    gap = 40
    grid_w = cols * cell_w + (cols - 1) * gap
    grid_h = rows * cell_h + (rows - 1) * gap
    start_x = (W - grid_w) // 2
    start_y = (H - grid_h) // 2 + 20

    for i, (value, label) in enumerate(stats):
        col = i % cols
        row = i // cols
        px = start_x + col * (cell_w + gap)
        py = start_y + row * (cell_h + gap)

        stat_accent = accent(theme, i)
        draw_floating_panel(draw, px, py, cell_w, cell_h, theme, accent=stat_accent)

        # Large value — centered in panel
        bbox = draw.textbbox((0, 0), value, font=font("bold", 64))
        vw = bbox[2] - bbox[0]
        vh = bbox[3] - bbox[1]
        draw.text(
            (px + (cell_w - vw) // 2, py + (cell_h - vh) // 2 - 20),
            value, font=font("bold", 64), fill=hex_to_rgb(theme["white"])
        )

        # Label below value
        bbox = draw.textbbox((0, 0), label, font=font("regular", 16))
        lw = bbox[2] - bbox[0]
        draw.text(
            (px + (cell_w - lw) // 2, py + cell_h - 50),
            label, font=font("regular", 16), fill=hex_to_rgb(theme["very_muted"])
        )

    draw_progress_dots(draw, scene_idx, total_scenes, theme)
    return img


def scene_highlights(data, theme, scene_idx=0, total_scenes=1):
    """Highlights card: recent activity as a visual timeline.

    Shows recent commits or PRs as a horizontal timeline with accent dots
    and short messages. A unique "montage within montage" feel.
    """
    img = radial_glow_bg(theme, glow_pos=(0.5, 0.6), glow_radius=500, intensity=0.10,
                         secondary_pos=(0.8, 0.2), secondary_radius=350, secondary_intensity=0.06)
    draw = ImageDraw.Draw(img)

    a = accent(theme, 5 % len(theme["accents"]))
    draw_text_centered(draw, 80, "RECENT ACTIVITY", font("bold", 20), theme["very_muted"])

    # Gather activity items — prefer PRs, fall back to commits
    prs = data.get("recent_prs", [])
    commits = data.get("recent_commits", [])
    items = []
    for pr in prs[:6]:
        items.append({"label": f"PR #{pr.get('number', '?')}", "text": pr.get("title", ""), "date": pr.get("merged_at", "")})
    if len(items) < 3:
        for c in commits[:6 - len(items)]:
            items.append({"label": c.get("sha", "")[:7], "text": c.get("message", ""), "date": c.get("date", "")})

    if not items:
        # Fallback: show creation date and description
        draw_text_centered(draw, H // 2 - 40, data.get("name", "Project"), font("bold", 56), theme["white"])
        created = data.get("created_at")
        if created:
            draw_text_centered(draw, H // 2 + 40, f"Created {created}", font("light", 26), theme["muted"])
        draw_progress_dots(draw, scene_idx, total_scenes, theme)
        return img

    # Draw items as stacked cards with a vertical timeline line
    panel_x = MARGIN + 60
    panel_w = W - MARGIN * 2 - 120
    timeline_x = panel_x + 15

    # Vertical timeline line
    y_start = 150
    y_end = min(y_start + len(items) * 120 + 40, H - 100)
    draw.rectangle([timeline_x, y_start, timeline_x + 2, y_end], fill=hex_to_rgb(theme["very_muted"]))

    for i, item in enumerate(items[:6]):
        color = accent(theme, i)
        y = y_start + 20 + i * 120

        # Timeline dot
        dot_r = 8
        draw.ellipse([timeline_x - dot_r + 1, y + 10 - dot_r,
                       timeline_x + dot_r + 1, y + 10 + dot_r], fill=hex_to_rgb(color))

        # Mini floating card
        card_x = timeline_x + 30
        card_w = panel_w - 60
        card_h = 90
        draw_floating_panel(draw, card_x, y - 10, card_w, card_h, theme, accent=color, opacity=0.04)

        # Label (PR number or commit sha)
        draw.text(
            (card_x + 20, y), item["label"],
            font=font("bold", 18), fill=hex_to_rgb(color)
        )

        # Date on the right
        if item["date"]:
            date_text = item["date"][:10]
            dbbox = draw.textbbox((0, 0), date_text, font=font("regular", 16))
            draw.text(
                (card_x + card_w - 20 - (dbbox[2] - dbbox[0]), y + 2), date_text,
                font=font("regular", 16), fill=hex_to_rgb(theme["very_muted"])
            )

        # Message text — truncated
        msg = item["text"][:80] + ("..." if len(item["text"]) > 80 else "")
        draw.text(
            (card_x + 20, y + 30), msg,
            font=font("regular", 22), fill=hex_to_rgb(theme["muted"])
        )

    draw_progress_dots(draw, scene_idx, total_scenes, theme)
    return img


def scene_closing(data, theme, scene_idx=0, total_scenes=1):
    """Closing card: project name with warm glow, repo URL, install command."""
    img = radial_glow_bg(theme, glow_pos=(0.5, 0.4), glow_radius=700, intensity=0.20,
                         secondary_pos=(0.2, 0.8), secondary_radius=400, secondary_intensity=0.08)
    draw = ImageDraw.Draw(img)

    name = data.get("name", "Project")
    description = data.get("description", "")
    repo_url = data.get("repo_url", "")
    install_cmd = data.get("install_command", "")
    a = accent(theme, 0)

    draw_text_centered(draw, 310, name.upper(), font("bold", 72), theme["white"])

    # Warm accent rule
    rule_w = min(len(name) * 30, 500)
    rule_x = (W - rule_w) // 2
    draw.rectangle([rule_x, 405, rule_x + rule_w, 407], fill=hex_to_rgb(a))

    if description:
        lines = wrap_text(description, font("light", 28), W - 500, draw)
        for i, line in enumerate(lines[:2]):
            draw_text_centered(
                draw, 435 + i * 42, line, font("light", 28), theme["muted"]
            )

    if repo_url:
        display = repo_url.replace("https://", "").replace("http://", "")
        draw_text_centered(
            draw, 570, display, font("regular", 22), theme["very_muted"]
        )

    if install_cmd:
        # Install command in a small floating panel
        cmd_text = f"$ {install_cmd}"
        cmd_bbox = draw.textbbox((0, 0), cmd_text, font=font("regular", 22))
        cmd_w = cmd_bbox[2] - cmd_bbox[0] + 60
        cmd_x = (W - cmd_w) // 2
        draw_floating_panel(draw, cmd_x, 625, cmd_w, 50, theme, accent=a)
        draw_text_centered(draw, 637, cmd_text, font("regular", 22), theme["muted"])

    draw_progress_dots(draw, scene_idx, total_scenes, theme)
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


def render_frames(scene_list, extra=True, theme=None):
    """
    Render animated frame sequences for each scene.

    When extra mode is ON, each scene gets multiple frames at EFFECT_FPS
    so effects animate (sparks drift, wisps rise). When OFF, falls back
    to a single static frame per scene (looped by FFmpeg).

    Returns: list of dicts with 'path' (file or pattern), 'animated' (bool),
             'fps' (int), for each scene.
    """
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    scene_outputs = []

    for i, scene_tuple in enumerate(scene_list):
        if len(scene_tuple) >= 5:
            image_fn, duration, _, _, scene_kind = scene_tuple[:5]
        else:
            image_fn = scene_tuple[0]
            duration = scene_tuple[1]
            scene_kind = "title"

        # Render the base scene image (static content)
        print(f"  Rendering scene {i + 1:02d} ({scene_kind})...")
        base_img = image_fn()
        base_img = add_grain(base_img)

        if extra and theme:
            # Animated: generate multiple frames
            scene_dir = FRAMES_DIR / f"scene_{i + 1:02d}"
            scene_dir.mkdir(parents=True, exist_ok=True)
            num_frames = max(2, int(duration * EFFECT_FPS))

            for f_idx in range(num_frames):
                t = f_idx / max(num_frames - 1, 1)
                frame = base_img.copy()
                frame = apply_extra_fx(frame, theme, scene_kind, i, t=t,
                                      total_scenes=len(scene_list))
                frame.save(scene_dir / f"frame_{f_idx:04d}.png", "PNG")

            scene_outputs.append({
                "path": str(scene_dir / "frame_%04d.png"),
                "animated": True,
                "fps": EFFECT_FPS,
            })
            print(f"    {num_frames} frames at {EFFECT_FPS}fps")
        else:
            # Static: single PNG
            path = FRAMES_DIR / f"scene_{i + 1:02d}.png"
            base_img.save(path, "PNG")
            scene_outputs.append({
                "path": str(path),
                "animated": False,
                "fps": FPS,
            })

    return scene_outputs


def encode_scene_clips(scenes, scene_outputs):
    """Encode each scene's frame sequence into a short MP4 clip.

    This ensures each clip has a proper constant frame rate that FFmpeg's
    xfade filter can work with. Returns list of clip paths.
    """
    clip_paths = []
    for i, (dur, _, _) in enumerate(scenes):
        out = scene_outputs[i]
        clip_path = FRAMES_DIR / f"clip_{i + 1:02d}.mp4"

        if out["animated"]:
            cmd = [
                "ffmpeg", "-y",
                "-framerate", str(out["fps"]),
                "-i", out["path"],
                "-vf", f"fps={FPS},format=yuv420p",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "12",
                "-t", str(dur),
                str(clip_path),
            ]
        else:
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-t", str(dur),
                "-i", out["path"],
                "-vf", f"fps={FPS},format=yuv420p",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "12",
                str(clip_path),
            ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"   Warning: clip {i+1} encoding failed: {result.stderr[-500:]}")
        clip_paths.append(clip_path)

    return clip_paths


def build_ffmpeg_cmd(scenes, clip_paths, output_path):
    """
    Build FFmpeg command with chained xfade transitions.

    Takes pre-encoded MP4 clips (constant frame rate) as inputs.

    scenes: list of (duration_secs, transition_type, transition_duration)
    clip_paths: list of Path objects for scene MP4 clips
    """
    n = len(scenes)
    inputs = []
    for i in range(n):
        inputs.extend(["-i", str(clip_paths[i])])

    # Build xfade chain
    filters = []
    cumulative = scenes[0][0]

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

    Skips scenes with no meaningful data (empty tech stack, no features).
    Passes scene index and total count for progress dots.

    Returns: list of (image_fn, duration, transition_type, transition_duration)
    """
    # First pass: collect scene specs, then we know total count
    scene_specs = []

    # Title — always included (5s — let the glow breathe)
    scene_specs.append(("title", 5.0, "fadeblack", 0.6))

    # Context — always included (6s — time to read)
    scene_specs.append(("context", 6.0, "fadeblack", 0.5))

    # Tech stack — only if we have language or stack data (5s)
    has_lang = bool(data.get("languages"))
    has_stack = bool(data.get("tech_stack"))
    if has_lang or has_stack:
        scene_specs.append(("tech_stack", 5.0, "fadeblack", 0.5))

    # Architecture — only if tree has meaningful depth (3+ lines) (5s)
    tree = data.get("tree_summary", "")
    tree_lines = [l for l in tree.split("\n") if l.strip()] if tree else []
    if len(tree_lines) >= 3:
        scene_specs.append(("architecture", 5.0, "slideleft", 0.4))

    # Features — only if 2+ (5s each)
    features = data.get("features", [])
    for i, feat in enumerate(features[:4]):
        if len(features) >= 2:
            scene_specs.append((f"feature_{i}", 5.0, "slideleft", 0.4))

    # Demo — only if screenshot (5s)
    if screenshot_path and Path(screenshot_path).exists():
        scene_specs.append(("demo", 5.0, "fadeblack", 0.5))

    # Highlights — a unique "montage within montage" scene showing recent activity (5s)
    scene_specs.append(("highlights", 5.0, "fadeblack", 0.6))

    # Stats — always (5s)
    scene_specs.append(("stats", 5.0, "fadeblack", 0.5))

    # Closing — always, no outgoing transition (5s)
    scene_specs.append(("closing", 5.0, None, 0))

    total = len(scene_specs)

    # Second pass: build actual scene callables with index/total
    # Each entry is a 5-tuple: (image_fn, duration, transition, trans_dur, scene_kind)
    scenes = []
    for idx, (kind, dur, trans, tdur) in enumerate(scene_specs):
        base_kind = kind.split("_")[0] if kind.startswith("feature_") else kind

        if kind == "title":
            scenes.append((lambda i=idx, t=total: scene_title(data, theme, i, t), dur, trans, tdur, "title"))
        elif kind == "context":
            scenes.append((lambda i=idx, t=total: scene_context(data, theme, i, t), dur, trans, tdur, "context"))
        elif kind == "tech_stack":
            scenes.append((lambda i=idx, t=total: scene_tech_stack(data, theme, i, t), dur, trans, tdur, "tech_stack"))
        elif kind == "architecture":
            scenes.append((lambda i=idx, t=total: scene_architecture(data, theme, screenshot_path, i, t), dur, trans, tdur, "architecture"))
        elif kind.startswith("feature_"):
            fi = int(kind.split("_")[1])
            ft = features[fi] if isinstance(features[fi], str) else str(features[fi])
            scenes.append((lambda ft=ft, fi=fi, i=idx, t=total: scene_feature(data, theme, ft, fi, None, i, t), dur, trans, tdur, "feature"))
        elif kind == "demo":
            scenes.append((lambda i=idx, t=total: scene_demo(data, theme, screenshot_path, i, t), dur, trans, tdur, "demo"))
        elif kind == "highlights":
            scenes.append((lambda i=idx, t=total: scene_highlights(data, theme, i, t), dur, trans, tdur, "highlights"))
        elif kind == "stats":
            scenes.append((lambda i=idx, t=total: scene_stats(data, theme, i, t), dur, trans, tdur, "stats"))
        elif kind == "closing":
            scenes.append((lambda i=idx, t=total: scene_closing(data, theme, i, t), dur, trans, tdur, "closing"))

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
                   mode="showcase", repos=None, since=None, screenshot_path=None,
                   extra=True):
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

    extra_label = "ON" if extra else "off"
    print(f"\n=== Project Video Generator ===")
    print(f"Mode: {mode} | Theme: {theme_name} | Extra: {extra_label} | Scenes: {len(scene_list)}\n")

    # Render frames
    print("1. Rendering scene frames...")
    scene_outputs = render_frames(scene_list, extra=extra, theme=theme)
    print(f"   Done: {len(scene_outputs)} scenes rendered to {FRAMES_DIR}\n")

    if dry_run:
        print("Dry run complete. Scenes saved to:")
        for out in scene_outputs:
            print(f"  {out['path']}  {'(animated)' if out['animated'] else '(static)'}")
        return FRAMES_DIR

    # Build FFmpeg scene timing data: (duration, transition, trans_dur)
    ffmpeg_scenes = [(s[1], s[2], s[3]) for s in scene_list]

    print("2. Encoding scene clips...")
    clip_paths = encode_scene_clips(ffmpeg_scenes, scene_outputs)
    print(f"   {len(clip_paths)} clips encoded\n")

    print("3. Building FFmpeg xfade chain...")
    cmd = build_ffmpeg_cmd(ffmpeg_scenes, clip_paths, output_path)
    print("   Filter chain built\n")

    print("4. Assembling final video...")
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
    parser.add_argument(
        "--no-extra", action="store_true",
        help="Disable extra visual effects (sparks, lasers, fog, etc.)"
    )

    # Compare subcommand
    compare_parser = subparsers.add_parser("compare", help="Compare multiple repos")
    compare_parser.add_argument("repos", nargs="+", help="GitHub repo URLs to compare")
    compare_parser.add_argument(
        "--theme", default="midnight", choices=list(THEMES.keys())
    )
    compare_parser.add_argument("--output", help="Output MP4 path")
    compare_parser.add_argument("--dry-run", action="store_true")
    compare_parser.add_argument("--no-extra", action="store_true")

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
    changelog_parser.add_argument("--no-extra", action="store_true")

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
            extra=not args.no_extra,
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
            extra=not args.no_extra,
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
            extra=not args.no_extra,
        )


if __name__ == "__main__":
    main()
