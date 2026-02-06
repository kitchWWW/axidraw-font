# pen_text_plotter.py
# Minimal vector "font" + helpers to draw text on an AxiDraw using pyaxidraw.

from dual_plotter import DualPlotter
import os


import math

class _RotatingPlotter:
    """Proxy that rotates all moveto/lineto calls around a pivot by angle_deg."""
    def __init__(self, base_ad, angle_deg: float, pivot_x: float, pivot_y: float):
        self._ad = base_ad
        self._cx = float(pivot_x)
        self._cy = float(pivot_y)
        theta = math.radians(angle_deg % 360.0)
        self._cos = math.cos(theta)
        self._sin = math.sin(theta)

    def _apply(self, x: float, y: float) -> tuple[float, float]:
        # Translate to pivot, rotate, translate back.
        dx, dy = x - self._cx, y - self._cy
        X = self._cos * dx - self._sin * dy + self._cx
        Y = self._sin * dx + self._cos * dy + self._cy
        return (X, Y)

    # Only the 2 funcs your drawing code uses need transforming:
    def moveto(self, x: float, y: float) -> None:
        X, Y = self._apply(x, y)
        self._ad.moveto(X, Y)

    def lineto(self, x: float, y: float) -> None:
        X, Y = self._apply(x, y)
        self._ad.lineto(X, Y)

    # Delegate everything else to the underlying plotter (connect, options, etc.)
    def __getattr__(self, name):
        return getattr(self._ad, name)


def draw_wrapped_text_rotated(
    ad,
    *,
    angle_deg: float,
    pivot_x_in: float,
    pivot_y_in: float,
    **wrapped_kwargs,
):
    """
    Wrapper: rotate all drawing by angle_deg around (pivot_x_in, pivot_y_in)
    while reusing your existing draw_wrapped_text implementation.
    """
    rotated_ad = _RotatingPlotter(ad, angle_deg, pivot_x_in, pivot_y_in)
    return draw_wrapped_text(rotated_ad, **wrapped_kwargs)



# --- line counter helpers (replace the old increment_and_get_count + global call) ---
def _read_int_from_file(filename: str) -> int:
    # DELETE THIS IF TESTING FOR REAL
    return 0


    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                s = f.read().strip()
                if s:
                    return int(s)
        except ValueError:
            print(f"Warning: Invalid content in {filename}. Resetting count.")
    return 0

def read_line_count(filename: str = "run_count.txt") -> int:
    """Return the current global 'line index' (how many baseline steps are already used)."""
    return _read_int_from_file(filename)

def increment_line_count(increment_by: int, filename: str = "run_count.txt") -> int:
    """Increase the stored count by `increment_by` and return the new total."""
    current = _read_int_from_file(filename)
    new_val = max(0, current + int(increment_by))
    with open(filename, "w") as f:
        f.write(str(new_val))
    return new_val


# --- A TINY SINGLE-STROKE FONT (normalized 0..1) ---
# Each glyph: {'w': advance_width_in_em, 'strokes': [ [(x,y), (x,y), ...], ... ] }
# Coordinates assume baseline at y=0 and cap height at y=1.
# This is intentionally simple and “boxy” to be plotter-friendly. Extend as you like.

FONT = {
    'a': {'w': 1, 'strokes': [
        [(0, 1), (0.5, 0), (1,1)],
        [(0.25, 0.5), (0.75, 0.5)]
    ]},
    'b': {'w': 1, 'strokes': [
        [(0,0), (0.8, 0), (1,0.2),(1,0.5),(0,0.5)],
        [(0,0),(0,1),(1,1),(1,0.7),(0.8,0.5)]
    ]},
    'c': {'w': 1, 'strokes': [
        [(1,0), (0.5, 0), (0,1),(1,1)]
    ]},
    'd': {'w': 1, 'strokes': [
        [(0,0), (0.8, 0), (1,0.2),(1,1),(0,1)],
        [(0.3,1),(0.3,0)]
    ]},
    'e': {'w': 1, 'strokes': [
        [(1,0), (0,0),(0,1),(1,1)],
        [(0,0.5),(1,0.5)],
    ]},
    'f': {'w': 1, 'strokes': [
        [(1,0), (0.5,0),(0,1)],
        [(0.25,0.5),(1,0.5)],
    ]},
    'g': {'w': 1, 'strokes': [
        [(1,0), (0.5,0),(0,1),(1,1),(1,0.5),(0.75,0.5)],
    ]},
    'h': {'w': 1, 'strokes': [
        [(0, 0), (0, 1.0)],
        [(0, 0.5), (1, 0.5)],
        [(1, 1), (1, 0)],
    ]},
    'i': {'w': 1, 'strokes': [
        [(0, 0), (1, 0)],
        [(1, 1), (0, 1)],
        [(0.5,1),(0.5,0)],
    ]},
    'j': {'w': 1, 'strokes': [
        [(0, 0), (1, 0)],
        [(0.5,0), (1, 0.5),(0,1),(0,0.75)],
    ]},
    'k': {'w': 1, 'strokes': [
        [(0, 0), (0, 1)],
        [(1,0),(0,0.5),(1,1)],
    ]},
    'l': {'w': 1, 'strokes': [
        [(0,0),(0,1),(1,1)],
    ]},
    'm': {'w': 1, 'strokes': [
        [(0,1),(0,0),(0.5,0.5),(1,0),(1,1)],
    ]},
    'n': {'w': 1, 'strokes': [
        [(0,1),(0,0),(1,1),(1,0)],
    ]},
    'o': {'w': 0.6, 'strokes': [
        [(0,0), (0.8, 0), (1,0.2),(1,1),(0,1),(0,0)],
    ]},
    'p': {'w': 0.6, 'strokes': [
        [(0,1),(0,0),(0.8,0),(1,0.2),(1,0.5),(0,0.5)]
    ]},
    'q': {'w': 0.6, 'strokes': [
        [(0,0),(0,1),(0.5,1),(1,0.5),(1,0.2),(0.8,0),(0,0)],
        [(0.5,0.5),(1,1)]
    ]},
    'r': {'w': 0.6, 'strokes': [
        [(0,1),(0,0),(0.8,0),(1,0.2),(1,0.5),(0,0.5),(1,1)]
    ]},
    'w': {'w': 0.8, 'strokes': [
        [(0.05, 1.0), (0.2, 0.0), (0.4, 1.0), (0.6, 0.0), (0.75, 1.0)]
    ]},
    's': {'w': 0.55, 'strokes': [
        [(1,0),(0.5,0),(0.25,0.5),(1,0.5),(1,1),(0,1)]
    ]},
    't': {'w': 1, 'strokes': [
        [(0, 0), (1, 0)],
        [(0.5,0), (0.5, 1)],
    ]},
    'u': {'w': 1, 'strokes': [
        [(0,0),(0,1),(1,1),(1,0)],
    ]},
    'v': {'w': 1, 'strokes': [
        [(0,0),(0.5,1),(1,0)],
    ]},
    'w': {'w': 1, 'strokes': [
        [(0,0),(0.25,1),(0.5,0),(0.75,1),(1,0)],
    ]},
    'x': {'w': 1, 'strokes': [
        [(0,0),(1,1)],
        [(0,1),(1,0)]
    ]},
    'y': {'w': 1, 'strokes': [
        [(0,0),(0.5,0.5),(0.5,1)],
        [(0.5,0.5),(1,0)]
    ]},
    'z': {'w': 1, 'strokes': [
        [(0,0),(1,0),(0,1),(1,1)]
    ]},
    '1': {'w': 1, 'strokes': [
        [(0.25,0.25),(0.5,0),(0.5,1),(0,1)],
        [(0.5,1),(1,1)]
    ]},
    '2': {'w': 1, 'strokes': [
        [(0,0),(0.8,0),(1,0.2),(1,0.5),(0,1),(1,1)]
    ]},
    '3': {'w': 1, 'strokes': [
        [(0,0),(1,0),(1,1),(0,1)],
        [(0,0.5),(1,0.5)]
    ]},
    '4': {'w': 1, 'strokes': [
        [(0,0),(0,0.5),(1,0.5)],
        [(1,1),(1,0)]
    ]},
    '5': {'w': 1, 'strokes': [
        [(0,1),(1,1),(1,0.5),(0,0.5),(0,0),(1,0)]
    ]},
    '6': {'w': 1, 'strokes': [
        [(0,0.5),(0,1),(1,1),(1,0.5),(0,0.5),(0.5,0),(1,0)]
    ]},
    '7': {'w': 1, 'strokes': [
        [(0,1),(1,0),(0,0)]
    ]},
    '8': {'w': 1, 'strokes': [
        [(0,0.5),(0,0),(1,0),(1,0.5),(0,0.5),(0,1),(1,1),(1,0.5)]
    ]},
    '9': {'w': 1, 'strokes': [
        [(1,1),(1,0),(0,0),(0,0.5),(1,0.5)]
    ]},
    '0': {'w': 1, 'strokes': [
        [(0,0),(0,1),(1,1),(1,0),(0,0)],
        [(0,1),(1,0)]
    ]},
    '-': {'w': 1, 'strokes': [
        [(0,0.5),(1,0.5)]
    ]},
    '.': {'w': 1, 'strokes': [
        [(0,1),(0.01,1)]
    ]},
    '!': {'w': 1, 'strokes': [
        [(0,0),(0,0.75)],
        [(0,1),(0.01,1)]
    ]},
    ',': {'w': 1, 'strokes': [
        [(0,1),(0.2,0.8)]
    ]},
    '?': {'w': 1, 'strokes': [
        [(0,0),(0.8,0),(1,0.2),(0.5,0.5),(0.5,0.8)],
        [(0.5,1),(0.51,1)]
    ]},
    '"': {'w': 1, 'strokes': [
        [(0.3,0),(0.3,0.3)],
        [(0.7,0),(0.7,0.3)]
    ]},
    '%': {'w': 1, 'strokes': [
        [(0,0),(0.01,0)],
        [(1,0),(0,1)],
        [(1,1),(0.99,1)]
    ]},
    '#': {'w': 1, 'strokes': [
        [(0.3,0),(0.3,1)],
        [(0.7,0),(0.7,1)],
        [(0,0.35),(1,0.35)],
        [(0,0.65),(1,0.65)]
    ]},
    '+': {'w': 1, 'strokes': [
        [(0,0.5),(1,0.5)],
        [(0.5,0.2),(0.5,0.8)]
    ]},
    'ß': {'w': 1, 'strokes': [
        [(0,1),(0,0),(0.8,0),(1,0.2),(1,0.4),(0,0.5),(1,0.6),(1,0.8),(0.8,1),(0.5,1)]
    ]},
    'é': {'w': 1, 'strokes': [
        [(1,0), (0,0),(0,1),(1,1)],
        [(0,0.5),(1,0.5)],
        [(0.35,-0.15),(0.65,-0.35)]
    ]},
    'í': {'w': 1, 'strokes': [
        [(0, 0), (1, 0)],
        [(1, 1), (0, 1)],
        [(0.5,1),(0.5,0)],
        [(0.35,-0.15),(0.65,-0.35)]
    ]},
    # Space = no strokes, just an advance width
    ' ': {'w': 0.35, 'strokes': []},
}

def draw_polyline(ad, poly, ox, oy, sx, sy):
    """Draw one polyline (list of (x,y) in 0..1 box) scaled & translated to inches."""
    if not poly:
        return
    x0 = ox + poly[0][0] * sx
    y0 = oy + poly[0][1] * sy
    ad.moveto(x0, y0)           # pen up move to start
    for (ux, uy) in poly[1:]:
        ad.lineto(ox + ux * sx, oy + uy * sy)  # pen down line to next point

def draw_glyph(ad, ch, x, y, height_in, tracking_in=0.0):
    """
    Draw a single glyph at baseline origin (x, y), with height = height_in inches.
    Returns the advance (inches) to add to the cursor (width + tracking).
    """
    g = FONT.get(ch, FONT['?'])
    width_em = 0.6 # g['w']
    # Scale X so glyph width is proportional to height for a roughly uniform look:
    sx = width_em * height_in
    sy = height_in

    for stroke in g['strokes']:
        draw_polyline(ad, stroke, x, y, sx, sy)

    return sx + tracking_in  # advance

# --- add this near your FONT dict ---
GLYPH_WIDTH_EM = 0.6  # keep in sync with draw_glyph; single source of truth

def glyph_advance_inches(height_in: float, letter_spacing_em: float) -> float:
    """Advance contributed by a single non-space glyph (width + tracking), in inches."""
    return (GLYPH_WIDTH_EM + letter_spacing_em) * height_in

def space_advance_inches(height_in: float, letter_spacing_em: float, word_spacing_em):
    """
    Advance contributed by a space.
    If custom word spacing is provided (word_spacing_em is not None), mimic draw_text_line behavior:
    use ONLY word_spacing_em * height, no extra tracking.
    Otherwise, treat space as a regular glyph with tracking (like draw_text_line does).
    """
    if word_spacing_em is not None:
        return word_spacing_em * height_in
    else:
        return glyph_advance_inches(height_in, letter_spacing_em)

def measure_word_width_inches(word: str, height_in: float, letter_spacing_em: float) -> float:
    """Width (inches) of a word (no spaces) using the same advance model as draw_text_line."""
    if not word:
        return 0.0
    # Each character advances by the glyph width + tracking
    return len(word) * glyph_advance_inches(height_in, letter_spacing_em)


# --- update draw_glyph to use GLYPH_WIDTH_EM so drawing == measuring ---
def draw_glyph(ad, ch, x, y, height_in, tracking_in=0.0):
    """
    Draw a single glyph at baseline origin (x, y), with height = height_in inches.
    Returns the advance (inches) to add to the cursor (width + tracking).
    """
    g = FONT.get(ch, FONT['?'])
    width_em = GLYPH_WIDTH_EM  # keep consistent with measurement helpers
    sx = width_em * height_in
    sy = height_in

    for stroke in g['strokes']:
        draw_polyline(ad, stroke, x, y, sx, sy)

    return sx + tracking_in  # advance

def draw_text_line(
    ad,
    text,
    origin_x_in,
    baseline_y_in,
    height_in=0.5,
    letter_spacing_em=0.12,
    word_spacing_em=None,
    font_scale: float = 1.0,
):
    """
    Draw a single line of text. 'font_scale' scales the drawn size (glyphs + tracking)
    but does NOT affect external layout decisions elsewhere.
    """
    # Apply scale only to the drawn metrics
    h = height_in * font_scale

    cursor_x = origin_x_in
    for ch in text:
        glyph_key = ch.lower()

        # Custom word spacing: advance only (scaled), no drawing
        if glyph_key == ' ' and word_spacing_em is not None:
            cursor_x += word_spacing_em * h
            continue

        tracking = letter_spacing_em * h
        advance = draw_glyph(ad, glyph_key, cursor_x, baseline_y_in, h, tracking_in=tracking)
        cursor_x += advance


def draw_wrapped_text(
    ad,
    text: str,
    origin_x_in: float,
    baseline_y_in: float,
    height_in: float = 0.6,
    max_width_in: float = 5.0,
    letter_spacing_em: float = 0.12,
    word_spacing_em=None,
    line_spacing_in: float | None = None,
    font_scale: float = 1.0,
):
    """
    Draw text with word wrapping at 'max_width_in' (inches).
    - Wrapping/measurement uses the UNscaled height so line breaks/width stay identical.
    - Drawing uses scaled metrics so the text appears larger/smaller, and line spacing between
      wrapped lines inside this block scales as well.
    - The starting origin (origin_x_in, baseline_y_in) is not scaled.
    """
    # --- measurement setup (UNSCALED to keep wrapping identical) ---
    if line_spacing_in is None:
        line_spacing_in = 1.5 * height_in  # base line spacing before scaling

    words = text.split()
    if not words:
        return

    lines = []
    current_words = []
    current_width = 0.0

    for w in words:
        w_width = measure_word_width_inches(w, height_in, letter_spacing_em)  # unscaled
        add_space = (len(current_words) > 0)
        extra_space_width = (
            space_advance_inches(height_in, letter_spacing_em, word_spacing_em) if add_space else 0.0
        )  # unscaled

        if current_words and (current_width + extra_space_width + w_width) > (max_width_in*0.6):
            lines.append(" ".join(current_words))
            current_words = [w]
            current_width = w_width
        else:
            if add_space:
                current_width += extra_space_width
            current_words.append(w)
            current_width += w_width

    if current_words:
        lines.append(" ".join(current_words))

    # --- drawing with scale applied ---
    y = baseline_y_in
    scaled_line_spacing = line_spacing_in * font_scale

    for line in lines:
        draw_text_line(
            ad,
            text=line,
            origin_x_in=origin_x_in,
            baseline_y_in=y,
            height_in=height_in,            # keep base; scaling handled via font_scale
            letter_spacing_em=letter_spacing_em,
            word_spacing_em=word_spacing_em,
            font_scale=font_scale,
        )
        y += scaled_line_spacing

    return len(lines)  # <-- add this
