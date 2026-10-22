"""GIF exporter module for quick visual preview of the boot animation.
Generates an animated GIF looping part1 (the sheen effect).
"""

from typing import Optional, Callable
import numpy as np
from PIL import Image

from core.anim_engine import AnimEngine


class GifExporter:
    """Exports loop preview as animated GIF."""

    @staticmethod
    def export_preview_gif(
        engine: AnimEngine,
        output_gif_path: str,
        max_dimension: int = 480,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> str:
        """
        Exports part1 (the looping sheen effect) as a downscaled, optimized GIF.

        Args:
            engine: The configured AnimEngine instance.
            output_gif_path: Output path for the .gif file.
            max_dimension: Max width or height for preview size.
            progress_callback: Optional progress reporter.

        Returns:
            The output path.
        """
        frames = []
        total = engine.part1_frames_count

        # Compute scaling factor to downscale full resolution for fast GIF preview
        scale = min(1.0, max_dimension / max(engine.screen_w, engine.screen_h))
        preview_w = max(1, int(engine.screen_w * scale))
        preview_h = max(1, int(engine.screen_h * scale))

        for idx, frame_rgb in engine.generate_all_part1_frames():
            if progress_callback:
                progress_callback(idx + 1, total, f"Generating GIF frame {idx + 1}/{total}")

            img = Image.fromarray(frame_rgb)
            if scale < 1.0:
                img = img.resize((preview_w, preview_h), Image.Resampling.BILINEAR)

            # Convert to adaptive 256-color palette for GIF
            img_paletted = img.convert("P", palette=Image.Palette.ADAPTIVE, colors=128)
            frames.append(img_paletted)

        if not frames:
            raise RuntimeError("No frames generated for GIF export.")

        # Duration per frame in milliseconds
        frame_duration_ms = max(10, int(1000.0 / engine.fps))

        frames[0].save(
            output_gif_path,
            save_all=True,
            append_images=frames[1:],
            duration=frame_duration_ms,
            loop=0,
            optimize=True
        )

        return output_gif_path
