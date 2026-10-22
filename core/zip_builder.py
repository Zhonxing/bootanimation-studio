"""Android bootanimation.zip packaging engine.
Strictly adheres to Android AOSP bootanim specifications:
- Zero compression (ZIP_STORED)
- desc.txt formatted with Unix LF line breaks and trailing newline
- Optional #RRGGBB background color integration
- Sequentially numbered PNG frames in part0/ and part1/
"""

from typing import Callable, Optional
import io
import zipfile
import cv2
import numpy as np

from core.anim_engine import AnimEngine


class ZipBuilder:
    """Builds compliant Android bootanimation.zip archives."""

    @staticmethod
    def build_bootanimation_zip(
        engine: AnimEngine,
        output_zip_path: str,
        pause_frames_after_part1: int = 0,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> str:
        """
        Renders all frames from the engine and packages them into a valid bootanimation.zip.

        Args:
            engine: The configured AnimEngine instance.
            output_zip_path: Destination path for .zip file.
            pause_frames_after_part1: Trailing pause frames defined in desc.txt for part1.
            progress_callback: Optional callable(current_frame, total_frames, status_msg).

        Returns:
            The output file path.
        """
        total_frames = engine.intro_frames_count + engine.part1_frames_count
        current_frame = 0

        # Construct desc.txt content with strict Unix LF line endings
        r, g, b = engine.canvas_bg_uint8
        hex_bg = f"#{r:02x}{g:02x}{b:02x}"
        if (r, g, b) != (0, 0, 0):
            p0_line = f"p 1 0 part0 {hex_bg}"
            p1_line = f"p 0 {pause_frames_after_part1} part1 {hex_bg}"
        else:
            p0_line = "p 1 0 part0"
            p1_line = f"p 0 {pause_frames_after_part1} part1"

        desc_lines = [
            f"{engine.screen_w} {engine.screen_h} {engine.fps}",
            p0_line,
            p1_line,
            ""  # ensures trailing newline
        ]
        desc_content = "\n".join(desc_lines).encode("utf-8")

        # Create zip with zero compression (ZIP_STORED)
        with zipfile.ZipFile(output_zip_path, mode="w", compression=zipfile.ZIP_STORED) as zf:
            # Write desc.txt
            zf.writestr("desc.txt", desc_content)

            # Write part0 frames
            for idx, frame_rgb in engine.generate_all_part0_frames():
                current_frame += 1
                if progress_callback:
                    progress_callback(current_frame, total_frames, f"Rendering part0: frame {idx + 1}/{engine.intro_frames_count}")

                frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
                success, png_bytes = cv2.imencode(".png", frame_bgr)
                if not success:
                    raise RuntimeError(f"Failed to encode PNG for part0 frame {idx}")

                arcname = f"part0/{idx:05d}.png"
                zf.writestr(arcname, png_bytes.tobytes())

            # Write part1 frames
            for idx, frame_rgb in engine.generate_all_part1_frames():
                current_frame += 1
                if progress_callback:
                    progress_callback(current_frame, total_frames, f"Rendering part1: frame {idx + 1}/{engine.part1_frames_count}")

                frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
                success, png_bytes = cv2.imencode(".png", frame_bgr)
                if not success:
                    raise RuntimeError(f"Failed to encode PNG for part1 frame {idx}")

                arcname = f"part1/{idx:05d}.png"
                zf.writestr(arcname, png_bytes.tobytes())

        if progress_callback:
            progress_callback(total_frames, total_frames, "Export completed successfully!")

        return output_zip_path

    @staticmethod
    def verify_zip(zip_path: str) -> dict:
        """
        Validates an existing bootanimation.zip archive for Android compliance.
        Checks:
        1. desc.txt existence, Unix line endings, non-empty, and format.
        2. Zero compression (compression method == zipfile.ZIP_STORED).
        3. Frame folders part0 and part1.
        """
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "info": {}
        }

        with zipfile.ZipFile(zip_path, "r") as zf:
            infolist = zf.infolist()

            # Check compression method
            for info in infolist:
                if info.compress_type != zipfile.ZIP_STORED:
                    result["is_valid"] = False
                    result["errors"].append(
                        f"Entry '{info.filename}' is compressed (type={info.compress_type}). "
                        "Android requires ZIP_STORED (0% compression)."
                    )

            # Check desc.txt
            if "desc.txt" not in zf.namelist():
                result["is_valid"] = False
                result["errors"].append("desc.txt is missing from root of archive.")
                return result

            desc_bytes = zf.read("desc.txt")
            if b"\r\n" in desc_bytes:
                result["is_valid"] = False
                result["errors"].append("desc.txt contains Windows CRLF line breaks. Must use Unix LF.")

            desc_text = desc_bytes.decode("utf-8", errors="ignore")
            lines = [line.strip() for line in desc_text.split("\n") if line.strip()]

            if not lines:
                result["is_valid"] = False
                result["errors"].append("desc.txt is empty.")
                return result

            header = lines[0].split()
            if len(header) < 3:
                result["is_valid"] = False
                result["errors"].append(f"Invalid desc.txt header: '{lines[0]}'. Expected 'width height fps'.")
            else:
                try:
                    w, h, fps = int(header[0]), int(header[1]), int(header[2])
                    result["info"]["resolution"] = (w, h)
                    result["info"]["fps"] = fps
                except ValueError:
                    result["is_valid"] = False
                    result["errors"].append(f"Header dimensions/fps not integers: '{lines[0]}'")

            part0_count = sum(1 for name in zf.namelist() if name.startswith("part0/") and name.endswith(".png"))
            part1_count = sum(1 for name in zf.namelist() if name.startswith("part1/") and name.endswith(".png"))

            result["info"]["part0_frames"] = part0_count
            result["info"]["part1_frames"] = part1_count

            if part0_count == 0:
                result["warnings"].append("part0 contains no PNG frames.")
            if part1_count == 0:
                result["warnings"].append("part1 contains no PNG frames.")

        return result
