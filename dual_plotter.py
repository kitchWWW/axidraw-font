# dual_plotter.py
# Wrapper that routes AxiDraw commands to either the real device or a 100 DPI PNG,
# and (in offline mode) also emits a replay script out########.py that will send
# the same sequence of commands to a real AxiDraw.

from __future__ import annotations
from typing import Tuple, Optional, List, Dict
import os
import time
import math

TIMESTAMP_FOR_SESSION = str(round(time.time() * 1000))

try:
    from PIL import Image, ImageDraw  # pip install pillow
except ImportError as e:
    raise SystemExit("This wrapper needs Pillow. Install with: pip install pillow") from e

try:
    from pyaxidraw import axidraw
except ImportError:
    axidraw = None  # Only needed when use_device=True


class _Options:
    """Lightweight placeholder for AxiDraw .options in image mode."""
    def __init__(self):
        # Expose the common attrs you set; values are ignored in image mode.
        self.pen_pos_down = 70
        self.pen_pos_up = 20
        self.speed_pendown = 25
        self.speed_penup = 60
        self.accel = 30


class DualPlotter:
    """
    A minimal wrapper that mimics the AxiDraw interface.

    If use_device=True, forwards to a real AxiDraw.
    If use_device=False, records lines to a 100 DPI PNG
    AND writes a replay script out########.py that can drive a real AxiDraw.

    Coordinates are in inches, same as AxiDraw.
    """

    # --- Color name constants (for convenience) -----------------------------  # ### NEW
    BLACK   = "BLACK"                                                          # ### NEW
    RED     = "RED"                                                            # ### NEW
    ORANGE  = "ORANGE"                                                         # ### NEW
    YELLOW  = "YELLOW"                                                         # ### NEW
    GREEN   = "GREEN"                                                          # ### NEW
    CYAN    = "CYAN"                                                           # ### NEW
    BLUE    = "BLUE"                                                           # ### NEW
    PURPLE  = "PURPLE"                                                         # ### NEW
    MAGENTA = "MAGENTA"                                                        # ### NEW
    GREY = "GREY"                                                        # ### NEW

    # Name -> RGB map (image mode only)                                        # ### NEW
    _COLOR_TABLE: Dict[str, Tuple[int, int, int]] = {                          # ### NEW
        "BLACK":   (0, 0, 0),                                                  # ### NEW
        "RED":     (220, 20, 60),   # crimson-ish                               ### NEW
        "ORANGE":  (255, 165, 0),                                              # ### NEW
        "YELLOW":  (255, 215, 0),   # goldenrod-ish                             ### NEW
        "GREEN":   (34, 139, 34),                                              # ### NEW
        "CYAN":    (0, 180, 180),                                              # ### NEW
        "BLUE":    (30, 144, 255),                                             # ### NEW
        "PURPLE":  (128, 0, 128),                                              # ### NEW
        "MAGENTA": (255, 0, 255),                                              # ### NEW
        "GREY": (200, 200, 200),                                              # ### NEW
        # Add more if you like...                                              # ### NEW
    }                                                                          # ### NEW

    def __init__(
        self,
        use_device: bool,
        *,
        out_path: str = "zout/z" + TIMESTAMP_FOR_SESSION + ".png",
        dpi: int = 100,
        page_bbox_inches: Tuple[float, float, float, float] = (0.0, 0.0, 11.69, 8.27),
        line_px: int = 1,
    ):
        """
        page_bbox_inches: (xmin, ymin, xmax, ymax) in inches for the PNG canvas.
        """
        self.use_device = use_device
        self.out_path = out_path
        self.dpi = int(dpi)
        self.line_px = int(line_px)
        self._pos: Optional[Tuple[float, float]] = None  # current (x, y) in inches

        # Distance tracking (in inches)
        self._pen_distance_in = 0.0     # all travel: moveto + lineto
        self._drawn_length_in = 0.0     # only pen-down segments (lineto)

        # BBox & pixel size
        self.xmin, self.ymin, self.xmax, self.ymax = page_bbox_inches
        w_in = max(0.0, self.xmax - self.xmin)
        h_in = max(0.0, self.ymax - self.ymin)
        self.W = max(1, int(round(w_in * self.dpi)))
        self.H = max(1, int(round(h_in * self.dpi)))

        # Options
        self.options = _Options()

        # --- Stroke color state (for image mode) -----------------------------  # ### NEW
        self._stroke_color_name: str = self.BLACK                               # ### NEW
        self._stroke_rgb: Tuple[int, int, int] = self._COLOR_TABLE[self.BLACK]  # ### NEW

        if self.use_device:
            if axidraw is None:
                raise RuntimeError("pyaxidraw not available but use_device=True was requested.")
            self._dev = axidraw.AxiDraw()
            self._apply_options()
        else:
            # Image mode: RGB white background; draw colored lines.             # ### CHANGED (RGB)
            self._img = Image.new("RGB", (self.W, self.H), (255, 255, 255))     # ### CHANGED
            self._draw = ImageDraw.Draw(self._img, "RGB")                       # ### CHANGED

            # --- Offline replay recording state ---
            self._called_interactive: bool = False
            self._command_log: List[Tuple[str, object, object]] = []  # kind,x,y or ("color", name, None)  ### CHANGED
            self._options_snapshot: Optional[Dict[str, float]] = None
            # Separate timestamped name for the replay script
            self._py_out_path: str = f"zout/z{TIMESTAMP_FOR_SESSION}.py"

    # --- Helpers -------------------------------------------------------------

    def _apply_options(self):
        # Apply current self.options to the real device
        self._dev.options.pen_pos_down = float(self.options.pen_pos_down)
        self._dev.options.pen_pos_up = float(self.options.pen_pos_up)
        self._dev.options.speed_pendown = float(self.options.speed_pendown)
        self._dev.options.speed_penup = float(self.options.speed_penup)
        self._dev.options.accel = float(self.options.accel)

    def _snapshot_current_options(self) -> Dict[str, float]:
        return dict(
            pen_pos_down=float(self.options.pen_pos_down),
            pen_pos_up=float(self.options.pen_pos_up),
            speed_pendown=float(self.options.speed_pendown),
            speed_penup=float(self.options.speed_penup),
            accel=float(self.options.accel),
        )

    def _to_px(self, x_in: float, y_in: float) -> Tuple[int, int]:
        """Convert inches to image pixel coords. Y is flipped so +Y is 'up' like AxiDraw."""
        px = int(round((x_in - self.xmin) * self.dpi))
        py = int(round((self.ymax - y_in) * self.dpi))
        return px, py

    @staticmethod
    def _segment_len(a: Tuple[float, float], b: Tuple[float, float]) -> float:
        """Euclidean distance in inches between two (x, y) points."""
        return math.hypot(b[0] - a[0], b[1] - a[1])

    # ### NEW: normalize a color name and fetch RGB (image mode only)
    def _rgb_for_name(self, color_like: str) -> Tuple[int, int, int]:
        """Map a user string to an RGB tuple; fallback to black for unknown names."""
        if not isinstance(color_like, str):
            return self._COLOR_TABLE[self.BLACK]
        name = color_like.strip().upper()
        return self._COLOR_TABLE.get(name, self._COLOR_TABLE[self.BLACK])

    # --- Replay script writer (offline mode) ---------------------------------

    def _write_replay_script(self):
        # Ensure we have some options captured; default to final values
        if self._options_snapshot is None:
            self._options_snapshot = self._snapshot_current_options()

        opts = self._options_snapshot
        lines: List[str] = []
        lines.append("# Auto-generated by DualPlotter (offline recorder)")
        lines.append("# Replays the captured drawing on a real AxiDraw.")
        lines.append("from pyaxidraw import axidraw")
        lines.append("")
        lines.append("def main():")
        lines.append("    ad = axidraw.AxiDraw()")
        lines.append("    ad.interactive()")
        lines.append("    # Apply recorded options")
        lines.append(f"    ad.options.pen_pos_down = {opts['pen_pos_down']}")
        lines.append(f"    ad.options.pen_pos_up = {opts['pen_pos_up']}")
        lines.append(f"    ad.options.speed_pendown = {opts['speed_pendown']}")
        lines.append(f"    ad.options.speed_penup = {opts['speed_penup']}")
        lines.append(f"    ad.options.accel = {opts['accel']}")
        lines.append("")
        lines.append("    if not ad.connect():")
        lines.append('        print(\"Could not connect to AxiDraw.\")')
        lines.append("        return")
        lines.append("")
        if not self._command_log:
            lines.append("    # (No movements were recorded.)")
        else:
            lines.append("    # Replay recorded moves (inches) and color changes:")
            # Inject moveto if first command is a lineto (keep behavior consistent)
            cmds = list(self._command_log)

            if cmds and cmds[0][0] == "lineto":
                _, x, y = cmds[0]
                lines.append(f"    ad.moveto({round(float(x),3)!r}, {round(float(y),3)!r})  # inserted to ensure valid start")
                cmds = cmds[1:]

            for kind, a, b in cmds:
                if kind == "moveto":
                    x, y = float(a), float(b)
                    lines.append(f"    ad.moveto({round(x,3)!r}, {round(y,3)!r})")
                elif kind == "lineto":
                    x, y = float(a), float(b)
                    lines.append(f"    ad.lineto({round(x,3)!r}, {round(y,3)!r})")
                elif kind == "color":
                    color_name = str(a)
                    lines.append("    # --- Color change requested ---")
                    lines.append("    ad.moveto(0.0, 0.0)")
                    # Prompt user to change pen/ink and wait for Enter
                    safe = color_name.replace("'", "\\'")  # basic quote safety
                    lines.append(f"    input('Please change the color to {safe}! Press Enter to continue...')")
                else:
                    # Unknown event kind; ignore gracefully
                    lines.append(f"    # (Unrecognized event skipped: {kind})")

        lines.append("")
        lines.append("    ad.disconnect()")
        lines.append("")
        lines.append("if __name__ == \"__main__\":")
        lines.append("    main()")
        content = "\n".join(lines)

        with open(self._py_out_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"[Image mode] Wrote AxiDraw replay script: {self._py_out_path}")

    # --- Public API (mirrors AxiDraw you use) --------------------------------

    def interactive(self):
        if self.use_device:
            ret = self._dev.interactive()
            self._apply_options()
            return ret
        # offline: record that interactive was called (for completeness)
        self._called_interactive = True

    def connect(self) -> bool:
        if self.use_device:
            return self._dev.connect()
        # Offline: snapshot options at the time the user decided to "connect".
        if self._options_snapshot is None:
            self._options_snapshot = self._snapshot_current_options()
        return True  # always "connected" in image mode

    def moveto(self, x: float, y: float):
        x, y = float(x), float(y)

        # Distance tracking for pen-up travel
        if self._pos is not None:
            self._pen_distance_in += self._segment_len(self._pos, (x, y))
        self._pos = (x, y)

        if self.use_device:
            return self._dev.moveto(x, y)

        # Record offline command
        self._command_log.append(("moveto", x, y))
        # (no drawing in image mode for moveto)

    def lineto(self, x: float, y: float):
        x, y = float(x), float(y)

        if self._pos is None:
            # If lineto is called first, mirror device behavior: jump to start
            self._pos = (x, y)
            if self.use_device:
                return self._dev.lineto(x, y)
            # Offline: record as a lineto; we'll insert a moveto in the replay file.
            self._command_log.append(("lineto", x, y))
            return

        seg_len = self._segment_len(self._pos, (x, y))
        self._pen_distance_in += seg_len
        self._drawn_length_in += seg_len

        if self.use_device:
            result = self._dev.lineto(x, y)
        else:
            # Render to image (current stroke color)
            p0 = self._to_px(*self._pos)
            p1 = self._to_px(x, y)
            self._draw.line([p0, p1], fill=self._stroke_rgb, width=self.line_px)  # ### CHANGED
            # Record offline command
            self._command_log.append(("lineto", x, y))
            result = None

        self._pos = (x, y)
        return result

    # ### NEW: confirmColorChange API
    def confirmColorChange(self, new_color: str):
        """
        Change pen color.

        - Device mode: move pen (pen-up) to (0,0), prompt the user to change ink,
          and wait for Enter to continue.
        - Image mode: switch the stroke color (fallback to black for unknown names)
          and record a color-change event so the replay script will pause similarly.
        """
        # Always move the (logical) head to (0,0) first
        self.moveto(0.0, 0.0)

        # Cache the text we will display to the user (use the argument verbatim)
        display_name = str(new_color)

        if self.use_device:
            # Prompt & wait in device mode
            try:
                input(f"Please change the color to {display_name}! Press Enter to continue...")
            except KeyboardInterrupt:
                print("Color change canceled by user (KeyboardInterrupt).")
            return

        # Image mode: set stroke color immediately (fallback to black for unknown)
        rgb = self._rgb_for_name(display_name)
        self._stroke_color_name = display_name
        self._stroke_rgb = rgb

        # Record a color-change event so the replay script reproduces the prompt
        self._command_log.append(("color", display_name, None))

    def outlinePage(self, do_dots=False):
        self.moveto(self.xmin, self.ymin)
        if do_dots:
            self.lineto(self.xmin, self.ymin)
        self.moveto(self.xmin, self.ymax)
        if do_dots:
            self.lineto(self.xmin, self.ymax)
        self.moveto(self.xmax, self.ymax)
        if do_dots:
            self.lineto(self.xmax, self.ymax)
        self.moveto(self.xmax, self.ymin)
        if do_dots:
            self.lineto(self.xmax, self.ymin)
        self.moveto(self.xmin, self.ymin)

    def disconnect(self):
        if self.use_device:
            return self._dev.disconnect()

        # Save PNG with proper DPI metadata
        flipped_img = self._img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        flipped_img.save(self.out_path, dpi=(self.dpi, self.dpi))
        try:
            # macOS preview convenience; ignore errors on other OSes
            os.system(f"open {self.out_path}")
        except Exception:
            pass

        # Emit replay script
        self._write_replay_script()

        # Print metrics (image mode only)
        print(f"[Image mode] Saved preview PNG: {self.out_path}")
        print(f"[Image mode] Total travel distance (pen-up + pen-down): {self._pen_distance_in:.3f} in")
        print(f"[Image mode] Total drawn length (pen-down only):       {self._drawn_length_in:.3f} in")
