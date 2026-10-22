"""Animation rendering engine for Android boot animations.
Generates part0 (fade-in entrance) and part1 (looping light sheen sweep)
using vectorized NumPy and OpenCV compositing, with full custom/extended background color support.
"""

from typing import List, Tuple, Generator, Optional
import math
import cv2
import numpy as np


class AnimEngine:
    """Renders Android-style light sheen sweep frames."""

    def __init__(
        self,
        logo_rgba: np.ndarray,
        pos: Tuple[int, int],
        target_size: Tuple[int, int] = (1080, 2400),
        fps: int = 30,
        sweep_duration: float = 1.4,
        pause_duration: float = 0.6,
        intro_duration: float = 0.5,
        beam_angle: float = 25.0,
        beam_width: float = 0.12,
        base_brightness: float = 0.30,
        beam_color: Tuple[int, int, int] = (255, 255, 255),
        halo_color: Optional[Tuple[int, int, int]] = (210, 235, 255),
        bloom_strength: float = 0.35,
        canvas_bg_color: Tuple[int, int, int] = (0, 0, 0)
    ):
        """
        Args:
            logo_rgba: RGBA logo array (uint8).
            pos: (pos_x, pos_y) placement on the target canvas.
            target_size: (width, height) of the screen.
            fps: Playback framerate.
            sweep_duration: Seconds taken for the light beam to cross the logo.
            pause_duration: Seconds to pause between sweep loops.
            intro_duration: Seconds for part0 fade-in.
            beam_angle: Angle of the light beam in degrees.
            beam_width: Relative width of the beam (fraction of logo diagonal).
            base_brightness: Unlit logo brightness (0.0 to 1.0).
            beam_color: RGB color of the specular core.
            halo_color: RGB color of the diffuse ambient sheen.
            bloom_strength: Glow/bloom spilling slightly outside the logo.
            canvas_bg_color: RGB background color for the entire screen (e.g. (9, 45, 73)).
        """
        self.logo_rgba = logo_rgba
        self.pos_x, self.pos_y = pos
        self.screen_w, self.screen_h = target_size
        self.fps = fps
        self.sweep_duration = sweep_duration
        self.pause_duration = pause_duration
        self.intro_duration = intro_duration
        self.beam_angle = beam_angle
        self.beam_width = beam_width
        self.base_brightness = base_brightness
        self.beam_color = np.array(beam_color, dtype=np.float32)
        self.halo_color = np.array(halo_color or beam_color, dtype=np.float32)
        self.bloom_strength = bloom_strength
        self.canvas_bg_color = np.array(canvas_bg_color, dtype=np.float32)
        self.canvas_bg_uint8 = np.clip(self.canvas_bg_color, 0, 255).astype(np.uint8)

        # Calculate frame counts
        self.intro_frames_count = max(5, int(intro_duration * fps))
        self.sweep_frames_count = max(10, int(sweep_duration * fps))
        self.pause_frames_count = max(0, int(pause_duration * fps))
        self.part1_frames_count = self.sweep_frames_count + self.pause_frames_count

        # Precompute coordinate grids and projection coordinates for the logo
        self._precompute_geometry()

    def _precompute_geometry(self):
        h, w = self.logo_rgba.shape[:2]
        self.logo_h, self.logo_w = h, w

        # Alpha channel normalized to 0.0 ~ 1.0
        self.alpha = (self.logo_rgba[..., 3].astype(np.float32) / 255.0)[..., np.newaxis]
        self.rgb = self.logo_rgba[..., :3].astype(np.float32)

        # Coordinate grid
        ys, xs = np.indices((h, w), dtype=np.float32)

        # Projection angle
        rad = math.radians(self.beam_angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        # Projected coordinate along beam direction
        self.u_proj = xs * cos_a + ys * sin_a
        u_min = float(np.min(self.u_proj))
        u_max = float(np.max(self.u_proj))

        # Diagonal / characteristic size
        diag = math.sqrt(w * w + h * h)
        self.sigma_core = max(4.0, diag * self.beam_width * 0.3)
        self.sigma_halo = self.sigma_core * 3.2

        # Start and end positions with margin
        margin = self.sigma_halo * 2.2
        self.u_start = u_min - margin
        self.u_end = u_max + margin

    def render_intro_frame(self, frame_idx: int) -> np.ndarray:
        """Renders a frame for part0 (smooth fade-in of unlit logo from background)."""
        t = (frame_idx + 1) / float(self.intro_frames_count)
        fade = math.sin(t * math.pi * 0.5)

        # The logo smoothly emerges from the canvas background color into its baseline state
        target_logo_rgb = self.rgb * self.base_brightness
        current_logo_rgb = self.canvas_bg_color * (1.0 - fade) + target_logo_rgb * fade

        # Seamless alpha blending onto canvas background color
        logo_patch = self.canvas_bg_color * (1.0 - self.alpha) + current_logo_rgb * self.alpha
        logo_patch = np.clip(logo_patch, 0, 255).astype(np.uint8)

        return self._composite_on_screen(logo_patch)

    def render_part1_frame(self, frame_idx: int) -> np.ndarray:
        """Renders a frame for part1 (sweep animation or trailing pause)."""
        if frame_idx >= self.sweep_frames_count:
            # Pause phase: logo stays at baseline idle brightness
            base_logo = self.rgb * self.base_brightness
            logo_patch = self.canvas_bg_color * (1.0 - self.alpha) + base_logo * self.alpha
            logo_patch = np.clip(logo_patch, 0, 255).astype(np.uint8)
            return self._composite_on_screen(logo_patch)

        # Sweep phase: compute beam center
        t = frame_idx / float(max(1, self.sweep_frames_count - 1))
        # Smooth movement with cubic easing
        t_eased = 3 * t * t - 2 * t * t * t
        center = self.u_start + (self.u_end - self.u_start) * t_eased

        # Distance to center
        dist = np.abs(self.u_proj - center)

        # Intensity profiles
        s_core = np.exp(-0.5 * (dist / self.sigma_core) ** 2)[..., np.newaxis]
        s_halo = np.exp(-0.5 * (dist / self.sigma_halo) ** 2)[..., np.newaxis]

        # Base ambient logo
        base_layer = self.rgb * self.base_brightness

        # Diffuse sheen highlights the logo's own color
        diffuse_layer = self.rgb * (1.0 - self.base_brightness) * s_halo

        # Specular bright core
        specular_layer = self.beam_color * (s_core * 1.35)

        # Combined lit logo
        lit_logo = base_layer + diffuse_layer + specular_layer

        # Optional bloom glow around the logo
        glow_layer = 0.0
        if self.bloom_strength > 0.05 and np.max(s_core) > 0.1:
            glow_mask = (s_core * self.alpha)[..., 0]
            ksize = max(5, int(self.sigma_halo * 0.8) | 1)
            glow_blurred = cv2.GaussianBlur(glow_mask, (ksize, ksize), 0)[..., np.newaxis]
            glow_layer = self.halo_color * (glow_blurred * self.bloom_strength * 0.8)

        # Composite seamlessly onto canvas background color
        # Inside logo (alpha=1): lit_logo
        # Outside logo (alpha=0): canvas_bg_color + glow_layer
        composite = (
            self.canvas_bg_color * (1.0 - self.alpha)
            + lit_logo * self.alpha
            + glow_layer * (1.0 - self.alpha)
        )

        logo_patch = np.clip(composite, 0, 255).astype(np.uint8)
        return self._composite_on_screen(logo_patch)

    def _composite_on_screen(self, logo_patch: np.ndarray) -> np.ndarray:
        """Pastes the rendered logo patch onto the full-screen canvas."""
        canvas = np.full((self.screen_h, self.screen_w, 3), self.canvas_bg_uint8, dtype=np.uint8)

        # Compute valid overlap coordinates
        y1 = max(0, self.pos_y)
        y2 = min(self.screen_h, self.pos_y + self.logo_h)
        x1 = max(0, self.pos_x)
        x2 = min(self.screen_w, self.pos_x + self.logo_w)

        ly1 = max(0, -self.pos_y)
        ly2 = ly1 + (y2 - y1)
        lx1 = max(0, -self.pos_x)
        lx2 = lx1 + (x2 - x1)

        if y2 > y1 and x2 > x1:
            canvas[y1:y2, x1:x2] = logo_patch[ly1:ly2, lx1:lx2]

        return canvas

    def generate_all_part0_frames(self) -> Generator[Tuple[int, np.ndarray], None, None]:
        """Yields (frame_idx, frame_np) for part0."""
        for i in range(self.intro_frames_count):
            yield i, self.render_intro_frame(i)

    def generate_all_part1_frames(self) -> Generator[Tuple[int, np.ndarray], None, None]:
        """Yields (frame_idx, frame_np) for part1."""
        for i in range(self.part1_frames_count):
            yield i, self.render_part1_frame(i)
