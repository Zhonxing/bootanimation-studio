"""Image preprocessing and normalization module for boot animation generation.
Preserves 1:1 original image proportions, aspect ratio and layout.
"""

from typing import Tuple, Optional
import numpy as np
from PIL import Image


class ImageProcessor:
    """Preprocesses input images for boot animation rendering."""

    @staticmethod
    def detect_border_color(img_np: np.ndarray) -> Tuple[int, int, int]:
        """
        Samples the perimeter and corners of the image to detect
        the dominant background color.
        """
        h, w = img_np.shape[:2]
        corners = [
            img_np[0, 0, :3],
            img_np[0, -1, :3],
            img_np[-1, 0, :3],
            img_np[-1, -1, :3]
        ]
        top = img_np[0, :, :3]
        bottom = img_np[-1, :, :3]
        left = img_np[:, 0, :3]
        right = img_np[:, -1, :3]

        border_samples = np.vstack([corners, top[::10], bottom[::10], left[::10], right[::10]])
        median_color = np.median(border_samples, axis=0).astype(int)
        return int(median_color[0]), int(median_color[1]), int(median_color[2])

    @staticmethod
    def load_and_prepare(
        image_input,
        target_size: Tuple[int, int] = (1080, 2400),
        scale_ratio: Optional[float] = None,  # Kept for API compatibility, ignored when preserving original ratio
        bg_mode: str = "auto",
        threshold: float = 22.0
    ) -> Tuple[np.ndarray, Tuple[int, int], Tuple[int, int], Tuple[int, int, int]]:
        """
        Loads and prepares the logo for the target screen, strictly preserving original proportions.

        Args:
            image_input: File path (str) or PIL.Image.Image.
            target_size: (width, height) of the screen.
            scale_ratio: Ignored to preserve original 1:1 image proportion.
            bg_mode: Background handling strategy.
            threshold: Color tolerance for background removal.

        Returns:
            processed_logo: RGBA numpy array of the logo patch.
            (pos_x, pos_y): Placement coordinates on the target screen.
            target_size: (width, height) of the target screen.
            detected_bg_color: (R, G, B) sampled from the image borders.
        """
        if isinstance(image_input, str):
            img = Image.open(image_input)
        elif isinstance(image_input, Image.Image):
            img = image_input.copy()
        else:
            raise ValueError(f"Unsupported image input type: {type(image_input)}")

        img = img.convert("RGBA")
        img_np = np.array(img, dtype=np.uint8)
        orig_h, orig_w = img_np.shape[:2]

        # Detect the border/background color from the original image
        detected_bg_color = ImageProcessor.detect_border_color(img_np)

        # Handle background extraction
        img_np = ImageProcessor.process_transparency(img_np, bg_mode, threshold, detected_bg_color)

        # Find visible logo pixels
        alpha = img_np[..., 3]
        visible_y, visible_x = np.where(alpha > 5)
        if len(visible_y) == 0 or len(visible_x) == 0:
            return np.zeros((10, 10, 4), dtype=np.uint8), (0, 0), target_size, detected_bg_color

        ymin, ymax = np.min(visible_y), np.max(visible_y)
        xmin, xmax = np.min(visible_x), np.max(visible_x)
        patch = img_np[ymin:ymax+1, xmin:xmax+1]
        patch_h, patch_w = patch.shape[:2]

        screen_w, screen_h = target_size

        # If target size matches original image size, preserve exact original pixel position!
        if screen_w == orig_w and screen_h == orig_h:
            return patch, (xmin, ymin), target_size, detected_bg_color

        # If target size is different (e.g. putting a 1024x512 image into a 1080x2400 phone screen):
        # Maintain 1:1 original proportion (downscale only if larger than target screen)
        scale = min(1.0, screen_w / orig_w, screen_h / orig_h)
        if scale < 1.0:
            new_w = max(1, int(patch_w * scale))
            new_h = max(1, int(patch_h * scale))
            resized_patch = np.array(
                Image.fromarray(patch).resize((new_w, new_h), Image.Resampling.LANCZOS),
                dtype=np.uint8
            )
            pos_x = (screen_w - new_w) // 2
            pos_y = (screen_h - new_h) // 2
            return resized_patch, (pos_x, pos_y), target_size, detected_bg_color
        else:
            # 1:1 pixel mapping, centered on target canvas
            pos_x = (screen_w - patch_w) // 2
            pos_y = (screen_h - patch_h) // 2
            return patch, (pos_x, pos_y), target_size, detected_bg_color

    @staticmethod
    def process_transparency(
        img_np: np.ndarray,
        mode: str,
        threshold: float = 22.0,
        detected_bg: Optional[Tuple[int, int, int]] = None
    ) -> np.ndarray:
        """Applies transparency based on the selected mode."""
        r, g, b, a = img_np[..., 0], img_np[..., 1], img_np[..., 2], img_np[..., 3]
        out = img_np.copy()

        has_alpha_variation = np.any(a < 250)

        if mode == "keep":
            return out

        if detected_bg is None:
            detected_bg = ImageProcessor.detect_border_color(img_np)

        if mode == "auto":
            # If already has transparent pixels, respect them
            if has_alpha_variation:
                return out
            # Solid image: use smart border matting
            mode = "smart_border"

        if mode == "smart_border":
            target_rgb = np.array(detected_bg, dtype=float)
            dist = np.linalg.norm(img_np[..., :3].astype(float) - target_rgb, axis=-1)
            feather = 15.0
            alpha_mask = np.clip((dist - threshold) / feather * 255.0, 0, 255).astype(np.uint8)
            out[..., 3] = np.minimum(a, alpha_mask)

        elif mode == "remove_black":
            dist = np.sqrt(r.astype(float)**2 + g.astype(float)**2 + b.astype(float)**2)
            alpha_mask = np.clip((dist - threshold) / (threshold * 1.5 + 1e-5) * 255, 0, 255).astype(np.uint8)
            out[..., 3] = np.minimum(a, alpha_mask)

        elif mode == "remove_white":
            dist = np.sqrt((255.0 - r)**2 + (255.0 - g)**2 + (255.0 - b)**2)
            alpha_mask = np.clip((dist - threshold) / (threshold * 1.5 + 1e-5) * 255, 0, 255).astype(np.uint8)
            out[..., 3] = np.minimum(a, alpha_mask)

        elif mode == "luminance":
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            out[..., 3] = np.clip(lum, 0, 255).astype(np.uint8)

        return out
