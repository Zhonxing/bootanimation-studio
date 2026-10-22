"""Automated unit and integration tests for bootanimation generation engine."""

import os
import tempfile
import unittest
import zipfile
import numpy as np
from PIL import Image

from core.image_processor import ImageProcessor
from core.anim_engine import AnimEngine
from core.zip_builder import ZipBuilder
from core.gif_exporter import GifExporter


class TestBootAnimationEngine(unittest.TestCase):
    """Test suite for core bootanimation generation and validation."""

    def setUp(self):
        self.test_logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "sample_logo.png")
        self.target_size = (720, 1280)  # Use smaller size for rapid test execution

    def test_image_processor_loading(self):
        """Test loading, resizing and centering."""
        logo_np, pos, screen_size, detected_bg = ImageProcessor.load_and_prepare(
            self.test_logo_path,
            target_size=self.target_size,
            bg_mode="auto"
        )
        self.assertIsInstance(logo_np, np.ndarray)
        self.assertEqual(logo_np.shape[2], 4)  # Must be RGBA
        self.assertGreater(logo_np.shape[0], 0)
        self.assertGreater(logo_np.shape[1], 0)
        self.assertEqual(len(detected_bg), 3)

        # Check positioning inside target bounds
        pos_x, pos_y = pos
        self.assertGreaterEqual(pos_x, 0)
        self.assertGreaterEqual(pos_y, 0)
        self.assertLess(pos_x + logo_np.shape[1], self.target_size[0] + 1)
        self.assertLess(pos_y + logo_np.shape[0], self.target_size[1] + 1)

    def test_anim_engine_frame_generation(self):
        """Test frame generation for part0 and part1."""
        logo_np, pos, screen_size, detected_bg = ImageProcessor.load_and_prepare(
            self.test_logo_path,
            target_size=self.target_size
        )

        engine = AnimEngine(
            logo_rgba=logo_np,
            pos=pos,
            target_size=self.target_size,
            fps=30,
            sweep_duration=1.0,
            pause_duration=0.3,
            intro_duration=0.3,
            canvas_bg_color=(9, 45, 73)
        )

        self.assertGreater(engine.intro_frames_count, 0)
        self.assertGreater(engine.part1_frames_count, 0)

        # Test single frame render
        p0_f0 = engine.render_intro_frame(0)
        self.assertEqual(p0_f0.shape, (self.target_size[1], self.target_size[0], 3))

        p1_f0 = engine.render_part1_frame(0)
        self.assertEqual(p1_f0.shape, (self.target_size[1], self.target_size[0], 3))

    def test_zip_builder_and_android_compliance(self):
        """Test that generated zip strictly satisfies Android bootanim rules."""
        logo_np, pos, screen_size, detected_bg = ImageProcessor.load_and_prepare(
            self.test_logo_path,
            target_size=(360, 640),
            scale_ratio=0.5
        )

        engine = AnimEngine(
            logo_rgba=logo_np,
            pos=pos,
            target_size=(360, 640),
            fps=30,
            sweep_duration=0.5,
            pause_duration=0.2,
            intro_duration=0.2,
            canvas_bg_color=(9, 45, 73)
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "bootanimation.zip")
            ZipBuilder.build_bootanimation_zip(engine, zip_path)

            self.assertTrue(os.path.exists(zip_path))
            self.assertGreater(os.path.getsize(zip_path), 0)

            # Strict verification
            verification = ZipBuilder.verify_zip(zip_path)
            self.assertTrue(verification["is_valid"], f"Verification failed: {verification['errors']}")
            self.assertEqual(verification["info"]["resolution"], (360, 640))
            self.assertEqual(verification["info"]["fps"], 30)
            self.assertGreater(verification["info"]["part0_frames"], 0)
            self.assertGreater(verification["info"]["part1_frames"], 0)

            # Direct inspection of desc.txt binary content
            with zipfile.ZipFile(zip_path, "r") as zf:
                desc_bytes = zf.read("desc.txt")
                self.assertNotIn(b"\r\n", desc_bytes, "desc.txt must not contain CRLF")
                self.assertTrue(desc_bytes.endswith(b"\n"), "desc.txt must end with LF")
                desc_str = desc_bytes.decode('utf-8')
                self.assertIn("#092d49", desc_str)

                # Verify all entries are ZIP_STORED (compression method 0)
                for entry in zf.infolist():
                    self.assertEqual(
                        entry.compress_type,
                        zipfile.ZIP_STORED,
                        f"Entry {entry.filename} is not stored (compression != 0)"
                    )

    def test_gif_exporter(self):
        """Test preview GIF generation."""
        logo_np, pos, screen_size, detected_bg = ImageProcessor.load_and_prepare(
            self.test_logo_path,
            target_size=(360, 640),
            scale_ratio=0.5
        )

        engine = AnimEngine(
            logo_rgba=logo_np,
            pos=pos,
            target_size=(360, 640),
            fps=30,
            sweep_duration=0.4,
            pause_duration=0.1,
            intro_duration=0.2
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            gif_path = os.path.join(tmpdir, "preview.gif")
            GifExporter.export_preview_gif(engine, gif_path, max_dimension=200)

            self.assertTrue(os.path.exists(gif_path))
            self.assertGreater(os.path.getsize(gif_path), 0)


if __name__ == "__main__":
    unittest.main()
