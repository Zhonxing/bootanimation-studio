"""Main application window for Android BootAnimation Generator.
Built with CustomTkinter for a sleek, modern desktop experience.
Preserves 1:1 original image proportions, automatic image-matching resolution,
full-screen background color extension, and smart border matting.
"""

from typing import Optional, Tuple
import os
import threading
from tkinter import filedialog, messagebox
import customtkinter as ctk
import numpy as np
from PIL import Image

from core.image_processor import ImageProcessor
from core.anim_engine import AnimEngine
from core.zip_builder import ZipBuilder
from core.gif_exporter import GifExporter
from ui.preview_canvas import PreviewCanvas


class BootAnimationApp(ctk.CTk):
    """Main Application GUI."""

    STANDARD_PRESETS = {
        "1080 x 2400 (现代手机 20:9)": (1080, 2400),
        "1080 x 1920 (经典手机 16:9)": (1080, 1920),
        "720 x 1280 (高清 720P)": (720, 1280),
        "1440 x 3200 (2K 超清)": (1440, 3200),
        "1920 x 1080 (车机 / 平板横屏)": (1920, 1080),
        "1280 x 800 (平板 / 工控屏)": (1280, 800)
    }

    COLOR_PRESETS = {
        "经典冷白": ((255, 255, 255), (220, 235, 255)),
        "原生冰蓝": ((210, 240, 255), (140, 200, 255)),
        "安卓经典绿": ((164, 198, 57), (130, 215, 80)),
        "流金璀璨": ((255, 215, 80), (255, 180, 50))
    }

    BG_MODES = {
        "自动检测 (推荐)": "auto",
        "智能吸色去底 (以边缘色抠图)": "smart_border",
        "保持原样 (透明 PNG)": "keep",
        "智能去黑底 (纯黑背景)": "remove_black",
        "智能去白底 (纯白背景)": "remove_white",
        "亮度转透明 (灰度图)": "luminance"
    }

    SCREEN_BG_OPTIONS = [
        "自动延展图片底色 (无缝沉浸)",
        "经典纯黑 (#000000)",
        "自定义颜色"
    ]

    def __init__(self):
        super().__init__()

        # Window settings
        self.title("Android BootAnimation 一键生成器")
        self.geometry("1020x780")
        self.minsize(960, 720)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("green")

        self.current_image_path: Optional[str] = None
        self.last_export_path: Optional[str] = None
        self.detected_bg_color: Tuple[int, int, int] = (0, 0, 0)
        self.image_orig_size: Tuple[int, int] = (1080, 2400)
        self.is_busy = False

        self._build_ui()
        self._load_default_sample()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Left Column (Settings & Controls)
        self.left_scroll = ctk.CTkScrollableFrame(self, label_text="⚙️ 参数配置与素材设置", corner_radius=10)
        self.left_scroll.grid(row=0, column=0, sticky="nsew", padx=(15, 8), pady=15)

        # Right Column (Preview & Export)
        self.right_frame = ctk.CTkFrame(self, corner_radius=10)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 15), pady=15)

        self._build_left_panel()
        self._build_right_panel()

    def _build_left_panel(self):
        parent = self.left_scroll

        # --- Section 1: Logo Input ---
        sec1 = ctk.CTkLabel(parent, text="1. 选择 Logo 图片", font=("Segoe UI", 14, "bold"))
        sec1.pack(anchor="w", pady=(5, 6))

        file_row = ctk.CTkFrame(parent, fg_color="transparent")
        file_row.pack(fill="x", pady=(0, 6))

        self.path_entry = ctk.CTkEntry(file_row, placeholder_text="请选择图片 (支持 PNG/JPG 等)", height=32)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.browse_btn = ctk.CTkButton(file_row, text="浏览...", width=70, height=32, command=self._on_browse_file)
        self.browse_btn.pack(side="right")

        sample_row = ctk.CTkFrame(parent, fg_color="transparent")
        sample_row.pack(fill="x", pady=(0, 8))

        self.sample_btn = ctk.CTkButton(
            sample_row,
            text="✨ Android 示例",
            height=28,
            fg_color="#2b3b28",
            hover_color="#3b5237",
            command=self._load_default_sample
        )
        self.sample_btn.pack(side="left", padx=(0, 6))

        self.sample_blue_btn = ctk.CTkButton(
            sample_row,
            text="🌌 深海蓝主题示例",
            height=28,
            fg_color="#1e293b",
            hover_color="#334155",
            command=self._load_blue_sample
        )
        self.sample_blue_btn.pack(side="left")

        # Background matting mode
        bg_label = ctk.CTkLabel(parent, text="Logo 抠图去底方式:", font=("Segoe UI", 12))
        bg_label.pack(anchor="w", pady=(0, 2))

        self.bg_mode_var = ctk.StringVar(value="自动检测 (推荐)")
        self.bg_mode_menu = ctk.CTkOptionMenu(
            parent,
            variable=self.bg_mode_var,
            values=list(self.BG_MODES.keys()),
            command=lambda _: self._trigger_preview_update()
        )
        self.bg_mode_menu.pack(fill="x", pady=(0, 10))

        # --- Section 2: Screen Background Extension (方案 B) ---
        sec_bg = ctk.CTkLabel(parent, text="2. 全屏底色设置 (方案 B 沉浸式延展)", font=("Segoe UI", 14, "bold"))
        sec_bg.pack(anchor="w", pady=(5, 6))

        self.screen_bg_var = ctk.StringVar(value="自动延展图片底色 (无缝沉浸)")
        self.screen_bg_menu = ctk.CTkOptionMenu(
            parent,
            variable=self.screen_bg_var,
            values=self.SCREEN_BG_OPTIONS,
            command=self._on_screen_bg_mode_change
        )
        self.screen_bg_menu.pack(fill="x", pady=(0, 6))

        # Custom / Active color badge row
        self.color_badge_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.color_badge_frame.pack(fill="x", pady=(0, 10))

        self.bg_preview_badge = ctk.CTkLabel(
            self.color_badge_frame,
            text="当前底色: #000000",
            font=("Segoe UI", 11, "bold"),
            fg_color="#000000",
            text_color="#FFFFFF",
            corner_radius=6,
            height=26,
            width=160
        )
        self.bg_preview_badge.pack(side="left", padx=(0, 8))

        self.custom_hex_entry = ctk.CTkEntry(
            self.color_badge_frame,
            placeholder_text="#092D49",
            width=90,
            height=26
        )
        self.custom_hex_btn = ctk.CTkButton(
            self.color_badge_frame,
            text="应用颜色",
            width=70,
            height=26,
            command=self._on_apply_custom_color
        )

        # --- Section 3: Logo Proportion Setting (保留原图比例) ---
        sec_scale = ctk.CTkLabel(parent, text="3. Logo 画面比例", font=("Segoe UI", 14, "bold"))
        sec_scale.pack(anchor="w", pady=(5, 6))

        self.ratio_badge = ctk.CTkLabel(
            parent,
            text="✓ 保留原图原始比例 (1:1 像素映射，不虚化、不放大拉伸)",
            font=("Segoe UI", 11, "bold"),
            fg_color="#064E3B",
            text_color="#6EE7B7",
            corner_radius=6,
            height=30
        )
        self.ratio_badge.pack(fill="x", pady=(0, 15))

        # --- Section 4: Screen Resolution & FPS ---
        sec4 = ctk.CTkLabel(parent, text="4. 屏幕分辨率与帧率", font=("Segoe UI", 14, "bold"))
        sec4.pack(anchor="w", pady=(5, 6))

        res_label = ctk.CTkLabel(parent, text="目标输出分辨率:", font=("Segoe UI", 12))
        res_label.pack(anchor="w", pady=(0, 2))

        # Dedicated Resolution Container
        self.res_container = ctk.CTkFrame(parent, fg_color="transparent")
        self.res_container.pack(fill="x", pady=(0, 6))

        self.res_var = ctk.StringVar(value="跟随图片原图尺寸 (自动识别)")
        self.res_menu = ctk.CTkOptionMenu(
            self.res_container,
            variable=self.res_var,
            values=["跟随图片原图尺寸 (自动识别)"] + list(self.STANDARD_PRESETS.keys()) + ["手动输入自定义尺寸..."],
            command=self._on_preset_change
        )
        self.res_menu.pack(fill="x", pady=(0, 4))

        # Info badge showing the actual effective resolution
        self.res_badge = ctk.CTkLabel(
            self.res_container,
            text="🎯 实际输出尺寸: 1080 x 2400",
            font=("Segoe UI", 11),
            text_color="#10B981"
        )
        self.res_badge.pack(anchor="w", pady=(0, 6))

        # Custom resolution inputs
        self.custom_res_frame = ctk.CTkFrame(self.res_container, fg_color="transparent")
        self.custom_w_entry = ctk.CTkEntry(self.custom_res_frame, placeholder_text="宽 W", width=80)
        self.custom_w_entry.pack(side="left", padx=(0, 4))
        self.custom_w_entry.insert(0, "1080")

        x_label = ctk.CTkLabel(self.custom_res_frame, text="x")
        x_label.pack(side="left", padx=4)

        self.custom_h_entry = ctk.CTkEntry(self.custom_res_frame, placeholder_text="高 H", width=80)
        self.custom_h_entry.pack(side="left", padx=(4, 8))
        self.custom_h_entry.insert(0, "2400")

        self.apply_custom_btn = ctk.CTkButton(
            self.custom_res_frame, text="应用尺寸", width=70,
            command=self._trigger_preview_update
        )
        self.apply_custom_btn.pack(side="left")

        # FPS Selection
        fps_label = ctk.CTkLabel(parent, text="播放帧率 (FPS):", font=("Segoe UI", 12))
        fps_label.pack(anchor="w", pady=(8, 2))

        self.fps_var = ctk.StringVar(value="30 FPS")
        self.fps_seg = ctk.CTkSegmentedButton(
            parent, values=["30 FPS", "60 FPS"],
            variable=self.fps_var,
            command=lambda _: self._trigger_preview_update()
        )
        self.fps_seg.pack(fill="x", pady=(0, 15))

        # --- Section 5: Light Sheen Tuning ---
        sec5 = ctk.CTkLabel(parent, text="5. 光影扫光质感微调", font=("Segoe UI", 14, "bold"))
        sec5.pack(anchor="w", pady=(5, 6))

        # Beam Angle
        self.angle_label = ctk.CTkLabel(parent, text="光束倾角: 25°", font=("Segoe UI", 12))
        self.angle_label.pack(anchor="w", pady=(0, 2))
        self.angle_slider = ctk.CTkSlider(parent, from_=0, to=45, number_of_steps=45, command=self._on_angle_change)
        self.angle_slider.set(25)
        self.angle_slider.pack(fill="x", pady=(0, 10))

        # Beam Width
        self.width_label = ctk.CTkLabel(parent, text="光束宽度: 0.12", font=("Segoe UI", 12))
        self.width_label.pack(anchor="w", pady=(0, 2))
        self.width_slider = ctk.CTkSlider(parent, from_=0.05, to=0.30, number_of_steps=25, command=self._on_width_change)
        self.width_slider.set(0.12)
        self.width_slider.pack(fill="x", pady=(0, 10))

        # Sweep Duration
        self.speed_label = ctk.CTkLabel(parent, text="扫光速度: 1.4 秒/次", font=("Segoe UI", 12))
        self.speed_label.pack(anchor="w", pady=(0, 2))
        self.speed_slider = ctk.CTkSlider(parent, from_=0.8, to=3.0, number_of_steps=22, command=self._on_speed_change)
        self.speed_slider.set(1.4)
        self.speed_slider.pack(fill="x", pady=(0, 10))

        # Pause Duration
        self.pause_label = ctk.CTkLabel(parent, text="循环间隔停顿: 0.6 秒", font=("Segoe UI", 12))
        self.pause_label.pack(anchor="w", pady=(0, 2))
        self.pause_slider = ctk.CTkSlider(parent, from_=0.0, to=2.0, number_of_steps=20, command=self._on_pause_change)
        self.pause_slider.set(0.6)
        self.pause_slider.pack(fill="x", pady=(0, 10))

        # Base brightness
        self.bright_label = ctk.CTkLabel(parent, text="未扫光底色亮度: 45%", font=("Segoe UI", 12))
        self.bright_label.pack(anchor="w", pady=(0, 2))
        self.bright_slider = ctk.CTkSlider(parent, from_=0.10, to=0.80, number_of_steps=35, command=self._on_bright_change)
        self.bright_slider.set(0.45)
        self.bright_slider.pack(fill="x", pady=(0, 10))

        # Color preset
        color_label = ctk.CTkLabel(parent, text="光影色彩方案:", font=("Segoe UI", 12))
        color_label.pack(anchor="w", pady=(0, 2))

        self.color_var = ctk.StringVar(value="经典冷白")
        self.color_menu = ctk.CTkOptionMenu(
            parent,
            variable=self.color_var,
            values=list(self.COLOR_PRESETS.keys()),
            command=lambda _: self._trigger_preview_update()
        )
        self.color_menu.pack(fill="x", pady=(0, 15))

    def _build_right_panel(self):
        parent = self.right_frame

        # Title
        title_label = ctk.CTkLabel(parent, text="📱 动效实时预览 (Android Sheen)", font=("Segoe UI", 16, "bold"))
        title_label.pack(anchor="w", padx=15, pady=(12, 4))

        sub_label = ctk.CTkLabel(parent, text="所见即所得：保留原图 1:1 比例与排版，全屏无缝底色延展", font=("Segoe UI", 11), text_color="#888888")
        sub_label.pack(anchor="w", padx=15, pady=(0, 8))

        # Preview Widget
        self.preview_canvas = PreviewCanvas(parent, preview_width=300, preview_height=420)
        self.preview_canvas.pack(pady=4)

        # Export Buttons & Progress Area
        export_box = ctk.CTkFrame(parent, fg_color="transparent")
        export_box.pack(fill="x", padx=15, pady=(10, 15))

        self.export_zip_btn = ctk.CTkButton(
            export_box,
            text="⚡ 一键生成并导出 bootanimation.zip",
            height=40,
            font=("Segoe UI", 14, "bold"),
            command=self._on_export_zip
        )
        self.export_zip_btn.pack(fill="x", pady=(0, 8))

        self.export_gif_btn = ctk.CTkButton(
            export_box,
            text="🎞 导出预览 GIF 动图 (用于分享预览)",
            height=32,
            fg_color="#334155",
            hover_color="#475569",
            command=self._on_export_gif
        )
        self.export_gif_btn.pack(fill="x", pady=(0, 10))

        # Progress bar
        self.prog_bar = ctk.CTkProgressBar(export_box)
        self.prog_bar.set(0.0)
        self.prog_bar.pack(fill="x", pady=(0, 6))

        # Status label
        self.status_label = ctk.CTkLabel(export_box, text="准备就绪", font=("Segoe UI", 11), text_color="#AAAAAA")
        self.status_label.pack(anchor="w")

        # Open folder button
        self.open_dir_btn = ctk.CTkButton(
            export_box,
            text="📂 打开导出目录",
            height=28,
            fg_color="#222222",
            hover_color="#333333",
            command=self._on_open_folder
        )
        self.open_dir_btn.pack(fill="x", pady=(6, 0))
        self.open_dir_btn.pack_forget()

    # --- Callbacks ---

    def _on_angle_change(self, val):
        self.angle_label.configure(text=f"光束倾角: {int(val)}°")
        self._trigger_preview_update()

    def _on_width_change(self, val):
        self.width_label.configure(text=f"光束宽度: {val:.2f}")
        self._trigger_preview_update()

    def _on_speed_change(self, val):
        self.speed_label.configure(text=f"扫光速度: {val:.1f} 秒/次")
        self._trigger_preview_update()

    def _on_pause_change(self, val):
        self.pause_label.configure(text=f"循环间隔停顿: {val:.1f} 秒")
        self._trigger_preview_update()

    def _on_bright_change(self, val):
        self.bright_label.configure(text=f"未扫光底色亮度: {int(val * 100)}%")
        self._trigger_preview_update()

    def _on_preset_change(self, choice):
        if "手动输入" in choice:
            self.custom_res_frame.pack(fill="x", pady=(4, 6))
        else:
            self.custom_res_frame.pack_forget()
        self._update_res_badge()
        self._trigger_preview_update()

    def _update_res_badge(self):
        w, h = self._get_target_resolution()
        self.res_badge.configure(text=f"🎯 实际输出尺寸: {w} x {h}")

    def _on_screen_bg_mode_change(self, choice):
        if choice == "自定义颜色":
            self.custom_hex_entry.pack(side="left", padx=(0, 6))
            self.custom_hex_btn.pack(side="left")
        else:
            self.custom_hex_entry.pack_forget()
            self.custom_hex_btn.pack_forget()
        self._update_bg_badge()
        self._trigger_preview_update()

    def _on_apply_custom_color(self):
        self._update_bg_badge()
        self._trigger_preview_update()

    def _update_bg_badge(self):
        color = self._get_canvas_bg_color()
        hex_str = "#{:02X}{:02X}{:02X}".format(*color)
        lum = 0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]
        txt_color = "#000000" if lum > 140 else "#FFFFFF"
        self.bg_preview_badge.configure(text=f"当前底色: {hex_str}", fg_color=hex_str, text_color=txt_color)

    def _on_browse_file(self):
        file_path = filedialog.askopenfilename(
            title="选择 Logo 图片",
            filetypes=[
                ("图片文件", "*.png *.jpg *.jpeg *.webp *.bmp"),
                ("所有文件", "*.*")
            ]
        )
        if file_path:
            self._load_image_file(file_path)

    def _load_image_file(self, file_path: str):
        self.current_image_path = file_path
        self.path_entry.delete(0, "end")
        self.path_entry.insert(0, file_path)

        # Update image dimensions and border color
        try:
            with Image.open(file_path) as img:
                self.image_orig_size = img.size
                self.detected_bg_color = ImageProcessor.detect_border_color(np.array(img.convert("RGBA")))
        except Exception:
            self.image_orig_size = (1080, 2400)
            self.detected_bg_color = (0, 0, 0)

        # Update resolution options with detected image size
        auto_text = f"跟随图片原图尺寸 ({self.image_orig_size[0]} x {self.image_orig_size[1]})"
        menu_values = [auto_text] + list(self.STANDARD_PRESETS.keys()) + ["手动输入自定义尺寸..."]
        self.res_menu.configure(values=menu_values)

        # Default to following the image size!
        self.res_var.set(auto_text)
        self.custom_res_frame.pack_forget()
        self._update_res_badge()

        # Update background color badge
        self._update_bg_badge()
        self._trigger_preview_update()

    def _load_default_sample(self):
        sample_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "sample_logo.png"))
        if os.path.exists(sample_path):
            self.screen_bg_var.set("经典纯黑 (#000000)")
            self._on_screen_bg_mode_change("经典纯黑 (#000000)")
            self._load_image_file(sample_path)

    def _load_blue_sample(self):
        sample_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "blue_sample_logo.png"))
        if os.path.exists(sample_path):
            self.screen_bg_var.set("自动延展图片底色 (无缝沉浸)")
            self._on_screen_bg_mode_change("自动延展图片底色 (无缝沉浸)")
            self._load_image_file(sample_path)

    def _get_canvas_bg_color(self) -> Tuple[int, int, int]:
        mode = self.screen_bg_var.get()
        if mode == "经典纯黑 (#000000)":
            return (0, 0, 0)
        elif mode == "自动延展图片底色 (无缝沉浸)":
            return self.detected_bg_color
        elif mode == "自定义颜色":
            hex_val = self.custom_hex_entry.get().strip().lstrip("#")
            if len(hex_val) == 6:
                try:
                    return (int(hex_val[0:2], 16), int(hex_val[2:4], 16), int(hex_val[4:6], 16))
                except ValueError:
                    pass
        return self.detected_bg_color

    def _get_target_resolution(self) -> Tuple[int, int]:
        choice = self.res_var.get()
        if "跟随图片" in choice:
            return self.image_orig_size

        size = self.STANDARD_PRESETS.get(choice)
        if size is not None:
            return size

        try:
            w = int(self.custom_w_entry.get().strip())
            h = int(self.custom_h_entry.get().strip())
            return max(10, w), max(10, h)
        except Exception:
            return self.image_orig_size

    def _create_engine(self, for_preview: bool = False) -> Optional[AnimEngine]:
        if not self.current_image_path or not os.path.exists(self.current_image_path):
            return None

        target_size = self._get_target_resolution()
        fps = 30 if "30" in self.fps_var.get() else 60
        bg_mode = self.BG_MODES.get(self.bg_mode_var.get(), "auto")
        canvas_bg = self._get_canvas_bg_color()

        beam_angle = float(self.angle_slider.get())
        beam_width = float(self.width_slider.get())
        sweep_duration = float(self.speed_slider.get())
        pause_duration = float(self.pause_slider.get())
        base_brightness = float(self.bright_slider.get())

        color_scheme = self.COLOR_PRESETS.get(self.color_var.get(), ((255, 255, 255), (220, 235, 255)))
        beam_color, halo_color = color_scheme

        if for_preview:
            max_p_dim = 400
            scale = min(1.0, max_p_dim / max(target_size[0], target_size[1]))
            p_size = (max(10, int(target_size[0] * scale)), max(10, int(target_size[1] * scale)))

            logo_np, pos, _, _ = ImageProcessor.load_and_prepare(
                self.current_image_path,
                target_size=p_size,
                bg_mode=bg_mode
            )

            engine = AnimEngine(
                logo_rgba=logo_np,
                pos=pos,
                target_size=p_size,
                fps=fps,
                sweep_duration=sweep_duration,
                pause_duration=pause_duration,
                intro_duration=0.4,
                beam_angle=beam_angle,
                beam_width=beam_width,
                base_brightness=base_brightness,
                beam_color=beam_color,
                halo_color=halo_color,
                canvas_bg_color=canvas_bg
            )
            return engine

        else:
            logo_np, pos, _, _ = ImageProcessor.load_and_prepare(
                self.current_image_path,
                target_size=target_size,
                bg_mode=bg_mode
            )

            engine = AnimEngine(
                logo_rgba=logo_np,
                pos=pos,
                target_size=target_size,
                fps=fps,
                sweep_duration=sweep_duration,
                pause_duration=pause_duration,
                intro_duration=0.5,
                beam_angle=beam_angle,
                beam_width=beam_width,
                base_brightness=base_brightness,
                beam_color=beam_color,
                halo_color=halo_color,
                canvas_bg_color=canvas_bg
            )
            return engine

    def _trigger_preview_update(self):
        try:
            self._update_res_badge()
            preview_engine = self._create_engine(for_preview=True)
            if preview_engine:
                self.preview_canvas.update_animation(preview_engine)
        except Exception as e:
            self.status_label.configure(text=f"预览加载失败: {e}", text_color="#FF6B6B")

    # --- Export Handlers ---

    def _on_export_zip(self):
        if self.is_busy:
            return

        save_path = filedialog.asksaveasfilename(
            title="保存 bootanimation.zip",
            defaultextension=".zip",
            initialfile="bootanimation.zip",
            filetypes=[("Zip 文件", "*.zip")]
        )
        if not save_path:
            return

        self.last_export_path = save_path
        self._set_busy(True)

        def worker():
            try:
                engine = self._create_engine(for_preview=False)
                if not engine:
                    raise ValueError("请先选择有效的 Logo 图片。")

                def progress_cb(cur, total, msg):
                    ratio = cur / max(1, total)
                    self.after(0, lambda: self._update_progress(ratio, msg))

                ZipBuilder.build_bootanimation_zip(engine, save_path, progress_callback=progress_cb)
                verify_res = ZipBuilder.verify_zip(save_path)

                def on_done():
                    self._set_busy(False)
                    self.prog_bar.set(1.0)
                    if verify_res["is_valid"]:
                        bg_hex = "#{:02X}{:02X}{:02X}".format(*engine.canvas_bg_uint8)
                        self.status_label.configure(
                            text=f"✅ 生成成功！尺寸 {engine.screen_w}x{engine.screen_h} 底色 {bg_hex}",
                            text_color="#4ADE80"
                        )
                        self.open_dir_btn.pack(fill="x", pady=(6, 0))
                        messagebox.showinfo(
                            "导出成功",
                            f"bootanimation.zip 已成功生成！\n\n"
                            f"分辨率: {engine.screen_w} x {engine.screen_h} ({engine.fps} FPS)\n"
                            f"全屏底色: {bg_hex} (无缝沉浸)\n"
                            f"保存路径: {save_path}\n\n"
                            "已通过 Android AOSP 规范验证（0% 压缩率，LF 换行）。"
                        )
                    else:
                        self.status_label.configure(
                            text=f"⚠️ 生成完成，但验证异常: {verify_res['errors']}",
                            text_color="#FBBF24"
                        )

                self.after(0, on_done)

            except Exception as e:
                def on_err(err_msg):
                    self._set_busy(False)
                    self.status_label.configure(text=f"❌ 导出失败: {err_msg}", text_color="#F87171")
                    messagebox.showerror("导出失败", f"生成 bootanimation.zip 时发生错误:\n{err_msg}")

                self.after(0, lambda: on_err(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_export_gif(self):
        if self.is_busy:
            return

        save_path = filedialog.asksaveasfilename(
            title="保存预览 GIF",
            defaultextension=".gif",
            initialfile="preview.gif",
            filetypes=[("GIF 文件", "*.gif")]
        )
        if not save_path:
            return

        self.last_export_path = save_path
        self._set_busy(True)

        def worker():
            try:
                engine = self._create_engine(for_preview=False)
                if not engine:
                    raise ValueError("请先选择有效的 Logo 图片。")

                def progress_cb(cur, total, msg):
                    ratio = cur / max(1, total)
                    self.after(0, lambda: self._update_progress(ratio, msg))

                GifExporter.export_preview_gif(engine, save_path, progress_callback=progress_cb)

                def on_done():
                    self._set_busy(False)
                    self.prog_bar.set(1.0)
                    self.status_label.configure(text="✅ 预览 GIF 已保存！", text_color="#4ADE80")
                    self.open_dir_btn.pack(fill="x", pady=(6, 0))
                    messagebox.showinfo("导出成功", f"预览动图已成功导出至:\n{save_path}")

                self.after(0, on_done)

            except Exception as e:
                def on_err(err_msg):
                    self._set_busy(False)
                    self.status_label.configure(text=f"❌ GIF 导出失败: {err_msg}", text_color="#F87171")
                    messagebox.showerror("导出失败", f"导出 GIF 失败:\n{err_msg}")

                self.after(0, lambda: on_err(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _update_progress(self, ratio: float, msg: str):
        self.prog_bar.set(ratio)
        self.status_label.configure(text=msg, text_color="#AAAAAA")

    def _set_busy(self, busy: bool):
        self.is_busy = busy
        state = "disabled" if busy else "normal"
        self.export_zip_btn.configure(state=state)
        self.export_gif_btn.configure(state=state)
        self.browse_btn.configure(state=state)
        self.sample_btn.configure(state=state)
        self.sample_blue_btn.configure(state=state)

    def _on_open_folder(self):
        if self.last_export_path and os.path.exists(self.last_export_path):
            folder = os.path.dirname(os.path.abspath(self.last_export_path))
            os.startfile(folder)
        else:
            messagebox.showinfo("提示", "文件或目录不存在。")


def run_app():
    app = BootAnimationApp()
    app.mainloop()


if __name__ == "__main__":
    run_app()
