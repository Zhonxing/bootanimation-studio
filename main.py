"""Android BootAnimation Generator - Entry Point.
Supports both GUI mode (default) and CLI mode.
"""

import sys
import os
import argparse

# Ensure current directory is on python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_cli(args):
    """Executes bootanimation generation via Command Line Interface."""
    from core.image_processor import ImageProcessor
    from core.anim_engine import AnimEngine
    from core.zip_builder import ZipBuilder
    from core.gif_exporter import GifExporter

    if not os.path.exists(args.image):
        print(f"Error: Image file not found: {args.image}", file=sys.stderr)
        sys.exit(1)

    try:
        w, h = map(int, args.res.lower().split("x"))
    except ValueError:
        print(f"Error: Invalid resolution format '{args.res}'. Expected e.g. 1080x2400", file=sys.stderr)
        sys.exit(1)

    print(f"Processing image '{args.image}' for resolution {w}x{h} at {args.fps} FPS...")
    logo_np, pos, _, detected_bg = ImageProcessor.load_and_prepare(
        args.image,
        target_size=(w, h),
        scale_ratio=args.scale,
        bg_mode=args.bg_mode
    )

    # Determine canvas background color
    if args.canvas_bg.lower() == "auto":
        canvas_bg = detected_bg
    elif args.canvas_bg.startswith("#") and len(args.canvas_bg) == 7:
        hex_str = args.canvas_bg.lstrip("#")
        canvas_bg = (int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))
    else:
        canvas_bg = (0, 0, 0)

    print(f"Canvas background color: #{canvas_bg[0]:02X}{canvas_bg[1]:02X}{canvas_bg[2]:02X}")

    color_map = {
        "white": ((255, 255, 255), (220, 235, 255)),
        "cyan": ((210, 240, 255), (140, 200, 255)),
        "green": ((164, 198, 57), (130, 215, 80)),
        "gold": ((255, 215, 80), (255, 180, 50))
    }
    beam_color, halo_color = color_map.get(args.color.lower(), ((255, 255, 255), (220, 235, 255)))

    engine = AnimEngine(
        logo_rgba=logo_np,
        pos=pos,
        target_size=(w, h),
        fps=args.fps,
        sweep_duration=args.speed,
        pause_duration=args.pause,
        intro_duration=0.5,
        beam_angle=args.angle,
        beam_width=args.width,
        base_brightness=args.base_brightness,
        beam_color=beam_color,
        halo_color=halo_color,
        canvas_bg_color=canvas_bg
    )

    print(f"Frames: part0={engine.intro_frames_count}, part1={engine.part1_frames_count}")
    print(f"Building Android bootanimation.zip: {args.output}")

    def progress(cur, total, msg):
        percent = int(cur / max(1, total) * 100)
        sys.stdout.write(f"\r[{percent}%] {msg}")
        sys.stdout.flush()

    ZipBuilder.build_bootanimation_zip(engine, args.output, progress_callback=progress)
    print("\nVerifying compliance with Android AOSP specification...")
    verify_res = ZipBuilder.verify_zip(args.output)
    if verify_res["is_valid"]:
        print(f"[SUCCESS] bootanimation.zip created and verified: {os.path.abspath(args.output)}")
    else:
        print(f"[WARNING] Verification issues: {verify_res['errors']}", file=sys.stderr)

    if args.gif:
        print(f"Generating preview GIF: {args.gif}")
        GifExporter.export_preview_gif(engine, args.gif, progress_callback=progress)
        print(f"\n[SUCCESS] Preview GIF created: {os.path.abspath(args.gif)}")


def main():
    parser = argparse.ArgumentParser(description="Android BootAnimation Generator (Android 原生光影扫光效果)")
    parser.add_argument("--cli", action="store_true", help="Run in command-line mode without GUI")
    parser.add_argument("-i", "--image", type=str, help="Path to input logo image (PNG/JPG)")
    parser.add_argument("-o", "--output", type=str, default="bootanimation.zip", help="Output zip filename")
    parser.add_argument("--res", type=str, default="1080x2400", help="Screen resolution WxH, e.g. 1080x2400")
    parser.add_argument("--fps", type=int, default=30, choices=[30, 60], help="Playback framerate")
    parser.add_argument("--scale", type=float, default=0.6, help="Logo scale relative to screen width/height")
    parser.add_argument("--bg-mode", type=str, default="auto", choices=["auto", "keep", "remove_black", "remove_white", "luminance"], help="Background handling mode")
    parser.add_argument("--speed", type=float, default=1.4, help="Sweep duration in seconds")
    parser.add_argument("--pause", type=float, default=0.6, help="Pause duration between sweeps in seconds")
    parser.add_argument("--angle", type=float, default=25.0, help="Light beam tilt angle (degrees)")
    parser.add_argument("--width", type=float, default=0.12, help="Light beam relative width")
    parser.add_argument("--base-brightness", type=float, default=0.45, help="Baseline unlit logo brightness")
    parser.add_argument("--canvas-bg", type=str, default="auto", help="Canvas background color: 'auto' (extend image border color), or hex e.g. '#000000'")
    parser.add_argument("--color", type=str, default="white", choices=["white", "cyan", "green", "gold"], help="Light sheen color preset")
    parser.add_argument("--gif", type=str, help="Optional output path to also export preview animated GIF")

    args = parser.parse_args()

    # If --cli or --image is passed, run in CLI mode; otherwise launch GUI
    if args.cli or args.image:
        if not args.image:
            print("Error: --image is required when using --cli mode.", file=sys.stderr)
            sys.exit(1)
        run_cli(args)
    else:
        from ui.app import run_app
        run_app()


if __name__ == "__main__":
    main()
