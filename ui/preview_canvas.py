"""Realtime animation preview widget for the CustomTkinter UI.
Renders and loops the light sweep frames in real-time.
"""

from typing import Optional, List, Tuple
import numpy as np
from PIL import Image
import customtkinter as ctk

from core.anim_engine import AnimEngine


class PreviewCanvas(ctk.CTkFrame):
    """Interactive preview canvas displaying looping animation frames."""

    def __init__(self, master, preview_width: int = 280, preview_height: int = 480, **kwargs):
        super().__init__(master, **kwargs)
        self.preview_w = preview_width
        self.preview_h = preview_height

        self.frames_cache: List[ctk.CTkImage] = []
        self.current_frame_idx = 0
        self.is_playing = True
        self.anim_job: Optional[str] = None
        self.fps = 30

        # UI Elements
        self.canvas_label = ctk.CTkLabel(
            self,
            text="暂无预览\n请导入图片",
            font=("Segoe UI", 14),
            text_color="#888888",
            width=self.preview_w,
            height=self.preview_h,
            fg_color="#0A0A0A",
            corner_radius=10
        )
        self.canvas_label.pack(pady=8, padx=8)

        # Control row
        self.controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.controls_frame.pack(fill="x", padx=10, pady=(0, 6))

        self.play_pause_btn = ctk.CTkButton(
            self.controls_frame,
            text="⏸ 暂停",
            width=80,
            height=28,
            command=self.toggle_play_pause
        )
        self.play_pause_btn.pack(side="left", padx=(0, 6))

        self.restart_btn = ctk.CTkButton(
            self.controls_frame,
            text="⏮ 重播",
            width=70,
            height=28,
            fg_color="#333333",
            hover_color="#444444",
            command=self.restart_playback
        )
        self.restart_btn.pack(side="left", padx=(0, 6))

        self.info_label = ctk.CTkLabel(
            self.controls_frame,
            text="帧: 0/0",
            font=("Segoe UI", 11),
            text_color="#AAAAAA"
        )
        self.info_label.pack(side="right")

    def update_animation(self, engine: AnimEngine):
        """Pre-renders a lightweight sequence of frames for the preview canvas."""
        self.stop_playback()
        self.frames_cache.clear()

        self.fps = engine.fps

        # Compute aspect ratio fit for preview window
        screen_w, screen_h = engine.screen_w, engine.screen_h
        scale = min(self.preview_w / screen_w, self.preview_h / screen_h)
        display_w = max(1, int(screen_w * scale))
        display_h = max(1, int(screen_h * scale))

        # We preview part1 (the continuous sheen loop)
        for idx, frame_rgb in engine.generate_all_part1_frames():
            img = Image.fromarray(frame_rgb)
            img_resized = img.resize((display_w, display_h), Image.Resampling.BILINEAR)

            # Center inside preview area with sleek black device bezel
            bg = Image.new("RGB", (self.preview_w, self.preview_h), (12, 12, 12))
            offset_x = (self.preview_w - display_w) // 2
            offset_y = (self.preview_h - display_h) // 2
            bg.paste(img_resized, (offset_x, offset_y))

            ctk_img = ctk.CTkImage(light_image=bg, dark_image=bg, size=(self.preview_w, self.preview_h))
            self.frames_cache.append(ctk_img)

        self.current_frame_idx = 0
        if self.frames_cache:
            self.canvas_label.configure(image=self.frames_cache[0], text="")
            self.is_playing = True
            self.play_pause_btn.configure(text="⏸ 暂停")
            self._schedule_next_frame()

    def _schedule_next_frame(self):
        if not self.is_playing or not self.frames_cache:
            return

        interval_ms = max(15, int(1000.0 / self.fps))
        self.anim_job = self.after(interval_ms, self._step_frame)

    def _step_frame(self):
        if not self.frames_cache:
            return

        self.current_frame_idx = (self.current_frame_idx + 1) % len(self.frames_cache)
        self.canvas_label.configure(image=self.frames_cache[self.current_frame_idx])
        self.info_label.configure(text=f"帧: {self.current_frame_idx + 1}/{len(self.frames_cache)}")

        if self.is_playing:
            self._schedule_next_frame()

    def toggle_play_pause(self):
        if self.is_playing:
            self.stop_playback()
            self.play_pause_btn.configure(text="▶ 播放")
        else:
            self.is_playing = True
            self.play_pause_btn.configure(text="⏸ 暂停")
            self._schedule_next_frame()

    def restart_playback(self):
        self.current_frame_idx = 0
        if self.frames_cache:
            self.canvas_label.configure(image=self.frames_cache[0])
            self.info_label.configure(text=f"帧: 1/{len(self.frames_cache)}")
        if not self.is_playing:
            self.toggle_play_pause()

    def stop_playback(self):
        self.is_playing = False
        if self.anim_job is not None:
            self.after_cancel(self.anim_job)
            self.anim_job = None
