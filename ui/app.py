"""Main application window for Android BootAnimation Generator.
Built with CustomTkinter for a sleek, modern desktop experience.
Supports full Chinese & English (中/英) localization, 1:1 original image ratio,
automatic image-matching resolution, full-screen background extension, and smart border matting.
"""

from typing import Optional, Tuple, Dict, Any
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

    I18N = {
        "zh": {
            "window_title": "Android BootAnimation 一键生成器",
            "left_panel_label": "⚙️ 参数配置与素材设置",
            "lang_label": "界面语言 / Language:",
            "sec1_title": "1. 选择 Logo 图片",
            "path_placeholder": "请选择图片 (支持 PNG/JPG 等)",
            "browse_btn": "浏览...",
            "sample_android_btn": "✨ Android 示例",
            "sample_blue_btn": "🌌 深海蓝主题示例",
            "matting_mode_label": "Logo 抠图去底方式:",
            "matting_modes": [
                "自动检测 (推荐)",
                "智能吸色去底 (以边缘色抠图)",
                "保持原样 (透明 PNG)",
                "智能去黑底 (纯黑背景)",
                "智能去白底 (纯白背景)",
                "亮度转透明 (灰度图)"
            ],
            "sec2_title": "2. 全屏底色设置 (方案 B 沉浸式延展)",
            "screen_bg_modes": [
                "自动延展图片底色 (无缝沉浸)",
                "经典纯黑 (#000000)",
                "自定义颜色"
            ],
            "current_bg_text": "当前底色: {}",
            "apply_color_btn": "应用颜色",
            "sec3_title": "3. Logo 画面比例",
            "ratio_badge_text": "✓ 保留原图原始比例 (1:1 像素映射，不虚化、不放大拉伸)",
            "sec4_title": "4. 屏幕分辨率与帧率",
            "target_res_label": "目标输出分辨率:",
            "match_image_size": "跟随图片原图尺寸 ({})",
            "match_image_default": "跟随图片原图尺寸 (自动识别)",
            "manual_res_option": "手动输入自定义尺寸...",
            "effective_res_badge": "🎯 实际输出尺寸: {} x {}",
            "custom_w_placeholder": "宽 W",
            "custom_h_placeholder": "高 H",
            "apply_size_btn": "应用尺寸",
            "fps_label": "播放帧率 (FPS):",
            "sec5_title": "5. 光影扫光质感微调",
            "angle_label": "光束倾角: {}°",
            "width_label": "光束宽度: {:.2f}",
            "speed_label": "扫光速度: {:.1f} 秒/次",
            "pause_label": "循环间隔停顿: {:.1f} 秒",
            "bright_label": "未扫光底色亮度: {}%",
            "color_preset_label": "光影色彩方案:",
            "color_presets": [
                "经典冷白",
                "原生冰蓝",
                "安卓经典绿",
                "流金璀璨"
            ],
            "right_title": "📱 动效实时预览 (Android Sheen)",
            "right_sub": "所见即所得：保留原图 1:1 比例与排版，全屏无缝底色延展",
            "export_zip_btn": "⚡ 一键生成并导出 bootanimation.zip",
            "export_gif_btn": "🎞 导出预览 GIF 动图 (用于分享预览)",
            "open_folder_btn": "📂 打开导出目录",
            "status_ready": "准备就绪",
            "dlg_select_image": "选择 Logo 图片",
            "dlg_save_zip": "保存 bootanimation.zip",
            "dlg_save_gif": "保存预览 GIF",
            "dlg_export_success_title": "导出成功",
            "dlg_export_fail_title": "导出失败",
            "zip_success_msg": "bootanimation.zip 已成功生成！\n\n分辨率: {} x {} ({} FPS)\n全屏底色: {} (无缝沉浸)\n保存路径: {}\n\n已通过 Android AOSP 规范验证（0% 压缩率，LF 换行）。",
            "gif_success_msg": "预览动图已成功导出至:\n{}",
            "status_success_zip": "✅ 生成成功！尺寸 {}x{} 底色 {}",
            "status_success_gif": "✅ 预览 GIF 已保存！"
        },
        "en": {
            "window_title": "Android BootAnimation Studio",
            "left_panel_label": "⚙️ Configuration & Media Settings",
            "lang_label": "Language / 界面语言:",
            "sec1_title": "1. Select Logo Image",
            "path_placeholder": "Select image (PNG/JPG/WebP supported)",
            "browse_btn": "Browse...",
            "sample_android_btn": "✨ Android Sample",
            "sample_blue_btn": "🌌 Deep Blue Sample",
            "matting_mode_label": "Logo Matting & Alpha Extraction:",
            "matting_modes": [
                "Auto Detect (Recommended)",
                "Smart Border Chroma Key",
                "Keep As-Is (Transparent PNG)",
                "Remove Black Background",
                "Remove White Background",
                "Luminance to Alpha"
            ],
            "sec2_title": "2. Screen Background (Plan B Extension)",
            "screen_bg_modes": [
                "Auto Extend Image Border Color (Seamless)",
                "Classic Pure Black (#000000)",
                "Custom Color"
            ],
            "current_bg_text": "Current BG: {}",
            "apply_color_btn": "Apply Color",
            "sec3_title": "3. Logo Screen Proportion",
            "ratio_badge_text": "✓ 1:1 Original Proportions (Native pixels, zero distortion/stretching)",
            "sec4_title": "4. Screen Resolution & Framerate",
            "target_res_label": "Target Resolution:",
            "match_image_size": "Match Image Original Size ({})",
            "match_image_default": "Match Image Original Size (Auto)",
            "manual_res_option": "Manual Custom Dimensions...",
            "effective_res_badge": "🎯 Effective Resolution: {} x {}",
            "custom_w_placeholder": "Width W",
            "custom_h_placeholder": "Height H",
            "apply_size_btn": "Apply Size",
            "fps_label": "Framerate (FPS):",
            "sec5_title": "5. Light Sheen Fine-Tuning",
            "angle_label": "Beam Angle: {}°",
            "width_label": "Beam Width: {:.2f}",
            "speed_label": "Sweep Speed: {:.1f} s/cycle",
            "pause_label": "Loop Pause: {:.1f} s",
            "bright_label": "Base Ambient Brightness: {}%",
            "color_preset_label": "Color Palette Preset:",
            "color_presets": [
                "Classic Silver-White",
                "Native Ice Blue",
                "Classic Android Green",
                "Gleaming Gold"
            ],
            "right_title": "📱 Real-Time Preview (Android Sheen)",
            "right_sub": "WYSIWYG: 1:1 original proportions, seamless full-screen background",
            "export_zip_btn": "⚡ One-Click Export bootanimation.zip",
            "export_gif_btn": "🎞 Export Preview GIF (For Quick Sharing)",
            "open_folder_btn": "📂 Open Output Folder",
            "status_ready": "Ready",
            "dlg_select_image": "Select Logo Image",
            "dlg_save_zip": "Save bootanimation.zip",
            "dlg_save_gif": "Save Preview GIF",
            "dlg_export_success_title": "Export Succeeded",
            "dlg_export_fail_title": "Export Failed",
            "zip_success_msg": "bootanimation.zip generated successfully!\n\nResolution: {} x {} ({} FPS)\nBackground: {} (Seamless)\nSaved to: {}\n\nComplies with Android AOSP specification (0% STORED, LF line ends).",
            "gif_success_msg": "Preview GIF saved successfully to:\n{}",
            "status_success_zip": "✅ Exported! Size {}x{} BG {}",
            "status_success_gif": "✅ Preview GIF saved successfully!"
        }
    }

    STANDARD_PRESETS = {
        "1080 x 2400 (现代手机 20:9)": (1080, 2400),
        "1080 x 1920 (经典手机 16:9)": (1080, 1920),
        "720 x 1280 (高清 720P)": (720, 1280),
        "1440 x 3200 (2K 超清)": (1440, 3200),
        "1920 x 1080 (车机 / 平板横屏)": (1920, 1080),
        "1280 x 800 (平板 / 工控屏)": (1280, 800)
    }

    STANDARD_PRESETS_EN = {
        "1080 x 2400 (Modern Phone 20:9)": (1080, 2400),
        "1080 x 1920 (Classic Phone 16:9)": (1080, 1920),
        "720 x 1280 (HD 720P)": (720, 1280),
        "1440 x 3200 (2K QHD)": (1440, 3200),
        "1920 x 1080 (Automotive / Tablet)": (1920, 1080),
        "1280 x 800 (Tablet / Industrial)": (1280, 800)
    }

    COLOR_PRESETS = {
        "经典冷白": ((255, 255, 255), (220, 235, 255)),
        "原生冰蓝": ((210, 240, 255), (140, 200, 255)),
        "安卓经典绿": ((164, 198, 57), (130, 215, 80)),
        "流金璀璨": ((255, 215, 80), (255, 180, 50)),
        "Classic Silver-White": ((255, 255, 255), (220, 235, 255)),
        "Native Ice Blue": ((210, 240, 255), (140, 200, 255)),
        "Classic Android Green": ((164, 198, 57), (130, 215, 80)),
        "Gleaming Gold": ((255, 215, 80), (255, 180, 50))
    }

    BG_MODE_MAP = {
        "自动检测 (推荐)": "auto",
        "智能吸色去底 (以边缘色抠图)": "smart_border",
        "保持原样 (透明 PNG)": "keep",
        "智能去黑底 (纯黑背景)": "remove_black",
        "智能去白底 (纯白背景)": "remove_white",
        "亮度转透明 (灰度图)": "luminance",
        "Auto Detect (Recommended)": "auto",
        "Smart Border Chroma Key": "smart_border",
        "Keep As-Is (Transparent PNG)": "keep",
        "Remove Black Background": "remove_black",
        "Remove White Background": "remove_white",
        "Luminance to Alpha": "luminance"
    }

    def __init__(self):
        super().__init__()

        self.current_lang = "zh"
        self.title(self.I18N[self.current_lang]["window_title"])
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

    def _t(self, key: str) -> str:
        return self.I18N[self.current_lang].get(key, key)

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Left Column (Settings & Controls)
        self.left_scroll = ctk.CTkScrollableFrame(self, label_text=self._t("left_panel_label"), corner_radius=10)
        self.left_scroll.grid(row=0, column=0, sticky="nsew", padx=(15, 8), pady=15)

        # Right Column (Preview & Export)
        self.right_frame = ctk.CTkFrame(self, corner_radius=10)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 15), pady=15)

        self._build_left_panel()
        self._build_right_panel()

    def _build_left_panel(self):
        parent = self.left_scroll

        # --- Top Language Switch Row ---
        lang_row = ctk.CTkFrame(parent, fg_color="transparent")
        lang_row.pack(fill="x", pady=(0, 10))

        self.lang_label = ctk.CTkLabel(lang_row, text=self._t("lang_label"), font=("Segoe UI", 12))
        self.lang_label.pack(side="left")

        self.lang_seg = ctk.CTkSegmentedButton(
            lang_row,
            values=["中文", "English"],
            command=self._on_language_change,
            width=140,
            height=26
        )
        self.lang_seg.set("中文")
        self.lang_seg.pack(side="right")

        # --- Section 1: Logo Input ---
        self.sec1_label = ctk.CTkLabel(parent, text=self._t("sec1_title"), font=("Segoe UI", 14, "bold"))
        self.sec1_label.pack(anchor="w", pady=(5, 6))

        file_row = ctk.CTkFrame(parent, fg_color="transparent")
        file_row.pack(fill="x", pady=(0, 6))

        self.path_entry = ctk.CTkEntry(file_row, placeholder_text=self._t("path_placeholder"), height=32)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.browse_btn = ctk.CTkButton(file_row, text=self._t("browse_btn"), width=70, height=32, command=self._on_browse_file)
        self.browse_btn.pack(side="right")

        sample_row = ctk.CTkFrame(parent, fg_color="transparent")
        sample_row.pack(fill="x", pady=(0, 8))

        self.sample_btn = ctk.CTkButton(
            sample_row,
            text=self._t("sample_android_btn"),
            height=28,
            fg_color="#2b3b28",
            hover_color="#3b5237",
            command=self._load_default_sample
        )
        self.sample_btn.pack(side="left", padx=(0, 6))

        self.sample_blue_btn = ctk.CTkButton(
            sample_row,
            text=self._t("sample_blue_btn"),
            height=28,
            fg_color="#1e293b",
            hover_color="#334155",
            command=self._load_blue_sample
        )
        self.sample_blue_btn.pack(side="left")

        # Background matting mode
        self.bg_label = ctk.CTkLabel(parent, text=self._t("matting_mode_label"), font=("Segoe UI", 12))
        self.bg_label.pack(anchor="w", pady=(0, 2))

        self.bg_mode_var = ctk.StringVar(value=self._t("matting_modes")[0])
        self.bg_mode_menu = ctk.CTkOptionMenu(
            parent,
            variable=self.bg_mode_var,
            values=self._t("matting_modes"),
            command=lambda _: self._trigger_preview_update()
        )
        self.bg_mode_menu.pack(fill="x", pady=(0, 10))

        # --- Section 2: Screen Background Extension (方案 B) ---
        self.sec2_label = ctk.CTkLabel(parent, text=self._t("sec2_title"), font=("Segoe UI", 14, "bold"))
        self.sec2_label.pack(anchor="w", pady=(5, 6))

        self.screen_bg_var = ctk.StringVar(value=self._t("screen_bg_modes")[0])
        self.screen_bg_menu = ctk.CTkOptionMenu(
            parent,
            variable=self.screen_bg_var,
            values=self._t("screen_bg_modes"),
            command=self._on_screen_bg_mode_change
        )
        self.screen_bg_menu.pack(fill="x", pady=(0, 6))

        # Custom / Active color badge row
        self.color_badge_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.color_badge_frame.pack(fill="x", pady=(0, 10))

        self.bg_preview_badge = ctk.CTkLabel(
            self.color_badge_frame,
            text=self._t("current_bg_text").format("#000000"),
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
            text=self._t("apply_color_btn"),
            width=70,
            height=26,
            command=self._on_apply_custom_color
        )

        # --- Section 3: Logo Proportion Setting (保留原图比例) ---
        self.sec3_label = ctk.CTkLabel(parent, text=self._t("sec3_title"), font=("Segoe UI", 14, "bold"))
        self.sec3_label.pack(anchor="w", pady=(5, 6))

        self.ratio_badge = ctk.CTkLabel(
            parent,
            text=self._t("ratio_badge_text"),
            font=("Segoe UI", 11, "bold"),
            fg_color="#064E3B",
            text_color="#6EE7B7",
            corner_radius=6,
            height=30
        )
        self.ratio_badge.pack(fill="x", pady=(0, 15))

        # --- Section 4: Screen Resolution & FPS ---
        self.sec4_label = ctk.CTkLabel(parent, text=self._t("sec4_title"), font=("Segoe UI", 14, "bold"))
        self.sec4_label.pack(anchor="w", pady=(5, 6))

        self.res_label = ctk.CTkLabel(parent, text=self._t("target_res_label"), font=("Segoe UI", 12))
        self.res_label.pack(anchor="w", pady=(0, 2))

        # Dedicated Resolution Container
        self.res_container = ctk.CTkFrame(parent, fg_color="transparent")
        self.res_container.pack(fill="x", pady=(0, 6))

        self.res_var = ctk.StringVar(value=self._t("match_image_default"))
        self.res_menu = ctk.CTkOptionMenu(
            self.res_container,
            variable=self.res_var,
            values=[self._t("match_image_default")] + list(self.STANDARD_PRESETS.keys()) + [self._t("manual_res_option")],
            command=self._on_preset_change
        )
        self.res_menu.pack(fill="x", pady=(0, 4))

        # Info badge showing the actual effective resolution
        self.res_badge = ctk.CTkLabel(
            self.res_container,
            text=self._t("effective_res_badge").format(1080, 2400),
            font=("Segoe UI", 11),
            text_color="#10B981"
        )
        self.res_badge.pack(anchor="w", pady=(0, 6))

        # Custom resolution inputs
        self.custom_res_frame = ctk.CTkFrame(self.res_container, fg_color="transparent")
        self.custom_w_entry = ctk.CTkEntry(self.custom_res_frame, placeholder_text=self._t("custom_w_placeholder"), width=80)
        self.custom_w_entry.pack(side="left", padx=(0, 4))
        self.custom_w_entry.insert(0, "1080")

        x_label = ctk.CTkLabel(self.custom_res_frame, text="x")
        x_label.pack(side="left", padx=4)

        self.custom_h_entry = ctk.CTkEntry(self.custom_res_frame, placeholder_text=self._t("custom_h_placeholder"), width=80)
        self.custom_h_entry.pack(side="left", padx=(4, 8))
        self.custom_h_entry.insert(0, "2400")

        self.apply_custom_btn = ctk.CTkButton(
            self.custom_res_frame, text=self._t("apply_size_btn"), width=70,
            command=self._trigger_preview_update
        )
        self.apply_custom_btn.pack(side="left")

        # FPS Selection
        self.fps_label = ctk.CTkLabel(parent, text=self._t("fps_label"), font=("Segoe UI", 12))
        self.fps_label.pack(anchor="w", pady=(8, 2))

        self.fps_var = ctk.StringVar(value="30 FPS")
        self.fps_seg = ctk.CTkSegmentedButton(
            parent, values=["30 FPS", "60 FPS"],
            variable=self.fps_var,
            command=lambda _: self._trigger_preview_update()
        )
        self.fps_seg.pack(fill="x", pady=(0, 15))

        # --- Section 5: Light Sheen Tuning ---
        self.sec5_label = ctk.CTkLabel(parent, text=self._t("sec5_title"), font=("Segoe UI", 14, "bold"))
        self.sec5_label.pack(anchor="w", pady=(5, 6))

        # Beam Angle
        self.angle_label = ctk.CTkLabel(parent, text=self._t("angle_label").format(25), font=("Segoe UI", 12))
        self.angle_label.pack(anchor="w", pady=(0, 2))
        self.angle_slider = ctk.CTkSlider(parent, from_=0, to=45, number_of_steps=45, command=self._on_angle_change)
        self.angle_slider.set(25)
        self.angle_slider.pack(fill="x", pady=(0, 10))

        # Beam Width
        self.width_label = ctk.CTkLabel(parent, text=self._t("width_label").format(0.12), font=("Segoe UI", 12))
        self.width_label.pack(anchor="w", pady=(0, 2))
        self.width_slider = ctk.CTkSlider(parent, from_=0.05, to=0.30, number_of_steps=25, command=self._on_width_change)
        self.width_slider.set(0.12)
        self.width_slider.pack(fill="x", pady=(0, 10))

        # Sweep Duration
        self.speed_label = ctk.CTkLabel(parent, text=self._t("speed_label").format(1.4), font=("Segoe UI", 12))
        self.speed_label.pack(anchor="w", pady=(0, 2))
        self.speed_slider = ctk.CTkSlider(parent, from_=0.8, to=3.0, number_of_steps=22, command=self._on_speed_change)
        self.speed_slider.set(1.4)
        self.speed_slider.pack(fill="x", pady=(0, 10))

        # Pause Duration
        self.pause_label = ctk.CTkLabel(parent, text=self._t("pause_label").format(0.6), font=("Segoe UI", 12))
        self.pause_label.pack(anchor="w", pady=(0, 2))
        self.pause_slider = ctk.CTkSlider(parent, from_=0.0, to=2.0, number_of_steps=20, command=self._on_pause_change)
        self.pause_slider.set(0.6)
        self.pause_slider.pack(fill="x", pady=(0, 10))

        # Base brightness
        self.bright_label = ctk.CTkLabel(parent, text=self._t("bright_label").format(45), font=("Segoe UI", 12))
        self.bright_label.pack(anchor="w", pady=(0, 2))
        self.bright_slider = ctk.CTkSlider(parent, from_=0.10, to=0.80, number_of_steps=35, command=self._on_bright_change)
        self.bright_slider.set(0.45)
        self.bright_slider.pack(fill="x", pady=(0, 10))

        # Color preset
        self.color_label = ctk.CTkLabel(parent, text=self._t("color_preset_label"), font=("Segoe UI", 12))
        self.color_label.pack(anchor="w", pady=(0, 2))

        self.color_var = ctk.StringVar(value=self._t("color_presets")[0])
        self.color_menu = ctk.CTkOptionMenu(
            parent,
            variable=self.color_var,
            values=self._t("color_presets"),
            command=lambda _: self._trigger_preview_update()
        )
        self.color_menu.pack(fill="x", pady=(0, 15))

    def _build_right_panel(self):
        parent = self.right_frame

        # Title
        self.right_title = ctk.CTkLabel(parent, text=self._t("right_title"), font=("Segoe UI", 16, "bold"))
        self.right_title.pack(anchor="w", padx=15, pady=(12, 4))

        self.right_sub = ctk.CTkLabel(parent, text=self._t("right_sub"), font=("Segoe UI", 11), text_color="#888888")
        self.right_sub.pack(anchor="w", padx=15, pady=(0, 8))

        # Preview Widget
        self.preview_canvas = PreviewCanvas(parent, preview_width=300, preview_height=420)
        self.preview_canvas.pack(pady=4)

        # Export Buttons & Progress Area
        export_box = ctk.CTkFrame(parent, fg_color="transparent")
        export_box.pack(fill="x", padx=15, pady=(10, 15))

        self.export_zip_btn = ctk.CTkButton(
            export_box,
            text=self._t("export_zip_btn"),
            height=40,
            font=("Segoe UI", 14, "bold"),
            command=self._on_export_zip
        )
        self.export_zip_btn.pack(fill="x", pady=(0, 8))

        self.export_gif_btn = ctk.CTkButton(
            export_box,
            text=self._t("export_gif_btn"),
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
        self.status_label = ctk.CTkLabel(export_box, text=self._t("status_ready"), font=("Segoe UI", 11), text_color="#AAAAAA")
        self.status_label.pack(anchor="w")

        # Open folder button
        self.open_dir_btn = ctk.CTkButton(
            export_box,
            text=self._t("open_folder_btn"),
            height=28,
            fg_color="#222222",
            hover_color="#333333",
            command=self._on_open_folder
        )
        self.open_dir_btn.pack(fill="x", pady=(6, 0))
        self.open_dir_btn.pack_forget()

    # --- Language Switching ---

    def _on_language_change(self, value):
        self.current_lang = "zh" if value == "中文" else "en"
        self._apply_translations()

    def _apply_translations(self):
        t = self.I18N[self.current_lang]
        self.title(t["window_title"])
        self.left_scroll.configure(label_text=t["left_panel_label"])
        self.lang_label.configure(text=t["lang_label"])

        self.sec1_label.configure(text=t["sec1_title"])
        self.path_entry.configure(placeholder_text=t["path_placeholder"])
        self.browse_btn.configure(text=t["browse_btn"])
        self.sample_btn.configure(text=t["sample_android_btn"])
        self.sample_blue_btn.configure(text=t["sample_blue_btn"])
        self.bg_label.configure(text=t["matting_mode_label"])

        # Update matting modes menu
        cur_bg_mode_idx = 0
        self.bg_mode_menu.configure(values=t["matting_modes"])
        self.bg_mode_var.set(t["matting_modes"][0])

        self.sec2_label.configure(text=t["sec2_title"])
        self.screen_bg_menu.configure(values=t["screen_bg_modes"])
        if "纯黑" in self.screen_bg_var.get() or "Pure Black" in self.screen_bg_var.get():
            self.screen_bg_var.set(t["screen_bg_modes"][1])
        elif "自定义" in self.screen_bg_var.get() or "Custom" in self.screen_bg_var.get():
            self.screen_bg_var.set(t["screen_bg_modes"][2])
        else:
            self.screen_bg_var.set(t["screen_bg_modes"][0])

        self.custom_hex_btn.configure(text=t["apply_color_btn"])
        self.sec3_label.configure(text=t["sec3_title"])
        self.ratio_badge.configure(text=t["ratio_badge_text"])

        self.sec4_label.configure(text=t["sec4_title"])
        self.res_label.configure(text=t["target_res_label"])

        # Update resolution presets
        presets_dict = self.STANDARD_PRESETS if self.current_lang == "zh" else self.STANDARD_PRESETS_EN
        auto_text = t["match_image_size"].format(f"{self.image_orig_size[0]} x {self.image_orig_size[1]}")
        menu_values = [auto_text] + list(presets_dict.keys()) + [t["manual_res_option"]]
        self.res_menu.configure(values=menu_values)
        if "手动" in self.res_var.get() or "Manual" in self.res_var.get():
            self.res_var.set(t["manual_res_option"])
        elif any(k in self.res_var.get() for k in presets_dict.keys()):
            pass
        else:
            self.res_var.set(auto_text)

        self.custom_w_entry.configure(placeholder_text=t["custom_w_placeholder"])
        self.custom_h_entry.configure(placeholder_text=t["custom_h_placeholder"])
        self.apply_custom_btn.configure(text=t["apply_size_btn"])
        self.fps_label.configure(text=t["fps_label"])

        self.sec5_label.configure(text=t["sec5_title"])
        self.angle_label.configure(text=t["angle_label"].format(int(self.angle_slider.get())))
        self.width_label.configure(text=t["width_label"].format(self.width_slider.get()))
        self.speed_label.configure(text=t["speed_label"].format(self.speed_slider.get()))
        self.pause_label.configure(text=t["pause_label"].format(self.pause_slider.get()))
        self.bright_label.configure(text=t["bright_label"].format(int(self.bright_slider.get() * 100)))

        self.color_label.configure(text=t["color_preset_label"])
        self.color_menu.configure(values=t["color_presets"])
        self.color_var.set(t["color_presets"][0])

        self.right_title.configure(text=t["right_title"])
        self.right_sub.configure(text=t["right_sub"])
        self.export_zip_btn.configure(text=t["export_zip_btn"])
        self.export_gif_btn.configure(text=t["export_gif_btn"])
        self.open_dir_btn.configure(text=t["open_folder_btn"])
        if "准备" in self.status_label.cget("text") or "Ready" in self.status_label.cget("text"):
            self.status_label.configure(text=t["status_ready"])

        self._update_bg_badge()
        self._update_res_badge()
        self.preview_canvas.set_language(self.current_lang)

    # --- Callbacks ---

    def _on_angle_change(self, val):
        self.angle_label.configure(text=self._t("angle_label").format(int(val)))
        self._trigger_preview_update()

    def _on_width_change(self, val):
        self.width_label.configure(text=self._t("width_label").format(val))
        self._trigger_preview_update()

    def _on_speed_change(self, val):
        self.speed_label.configure(text=self._t("speed_label").format(val))
        self._trigger_preview_update()

    def _on_pause_change(self, val):
        self.pause_label.configure(text=self._t("pause_label").format(val))
        self._trigger_preview_update()

    def _on_bright_change(self, val):
        self.bright_label.configure(text=self._t("bright_label").format(int(val * 100)))
        self._trigger_preview_update()

    def _on_preset_change(self, choice):
        if "手动" in choice or "Manual" in choice:
            self.custom_res_frame.pack(fill="x", pady=(4, 6))
        else:
            self.custom_res_frame.pack_forget()
        self._update_res_badge()
        self._trigger_preview_update()

    def _update_res_badge(self):
        w, h = self._get_target_resolution()
        self.res_badge.configure(text=self._t("effective_res_badge").format(w, h))

    def _on_screen_bg_mode_change(self, choice):
        if "自定义" in choice or "Custom" in choice:
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
        self.bg_preview_badge.configure(
            text=self._t("current_bg_text").format(hex_str),
            fg_color=hex_str,
            text_color=txt_color
        )

    def _on_browse_file(self):
        file_path = filedialog.askopenfilename(
            title=self._t("dlg_select_image"),
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.webp *.bmp"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self._load_image_file(file_path)

    def _load_image_file(self, file_path: str):
        self.current_image_path = file_path
        self.path_entry.delete(0, "end")
        self.path_entry.insert(0, file_path)

        try:
            with Image.open(file_path) as img:
                self.image_orig_size = img.size
                self.detected_bg_color = ImageProcessor.detect_border_color(np.array(img.convert("RGBA")))
        except Exception:
            self.image_orig_size = (1080, 2400)
            self.detected_bg_color = (0, 0, 0)

        t = self.I18N[self.current_lang]
        presets_dict = self.STANDARD_PRESETS if self.current_lang == "zh" else self.STANDARD_PRESETS_EN
        auto_text = t["match_image_size"].format(f"{self.image_orig_size[0]} x {self.image_orig_size[1]}")
        menu_values = [auto_text] + list(presets_dict.keys()) + [t["manual_res_option"]]
        self.res_menu.configure(values=menu_values)

        self.res_var.set(auto_text)
        self.custom_res_frame.pack_forget()
        self._update_res_badge()
        self._update_bg_badge()
        self._trigger_preview_update()

    def _load_default_sample(self):
        sample_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "sample_logo.png"))
        if os.path.exists(sample_path):
            black_option = self._t("screen_bg_modes")[1]
            self.screen_bg_var.set(black_option)
            self._on_screen_bg_mode_change(black_option)
            self._load_image_file(sample_path)

    def _load_blue_sample(self):
        sample_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "blue_sample_logo.png"))
        if os.path.exists(sample_path):
            auto_option = self._t("screen_bg_modes")[0]
            self.screen_bg_var.set(auto_option)
            self._on_screen_bg_mode_change(auto_option)
            self._load_image_file(sample_path)

    def _get_canvas_bg_color(self) -> Tuple[int, int, int]:
        mode = self.screen_bg_var.get()
        if "纯黑" in mode or "Pure Black" in mode:
            return (0, 0, 0)
        elif "自动" in mode or "Auto" in mode:
            return self.detected_bg_color
        elif "自定义" in mode or "Custom" in mode:
            hex_val = self.custom_hex_entry.get().strip().lstrip("#")
            if len(hex_val) == 6:
                try:
                    return (int(hex_val[0:2], 16), int(hex_val[2:4], 16), int(hex_val[4:6], 16))
                except ValueError:
                    pass
        return self.detected_bg_color

    def _get_target_resolution(self) -> Tuple[int, int]:
        choice = self.res_var.get()
        if "跟随图片" in choice or "Match Image" in choice:
            return self.image_orig_size

        size = self.STANDARD_PRESETS.get(choice) or self.STANDARD_PRESETS_EN.get(choice)
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
        bg_mode = self.BG_MODE_MAP.get(self.bg_mode_var.get(), "auto")
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
            self.status_label.configure(text=f"Preview error: {e}", text_color="#FF6B6B")

    # --- Export Handlers ---

    def _on_export_zip(self):
        if self.is_busy:
            return

        save_path = filedialog.asksaveasfilename(
            title=self._t("dlg_save_zip"),
            defaultextension=".zip",
            initialfile="bootanimation.zip",
            filetypes=[("Zip files", "*.zip")]
        )
        if not save_path:
            return

        self.last_export_path = save_path
        self._set_busy(True)

        def worker():
            try:
                engine = self._create_engine(for_preview=False)
                if not engine:
                    raise ValueError("Please select a valid image first.")

                def progress_cb(cur, total, msg):
                    ratio = cur / max(1, total)
                    self.after(0, lambda: self._update_progress(ratio, msg))

                ZipBuilder.build_bootanimation_zip(engine, save_path, progress_callback=progress_cb)
                verify_res = ZipBuilder.verify_zip(save_path)

                def on_done():
                    self._set_busy(False)
                    self.prog_bar.set(1.0)
                    t = self.I18N[self.current_lang]
                    if verify_res["is_valid"]:
                        bg_hex = "#{:02X}{:02X}{:02X}".format(*engine.canvas_bg_uint8)
                        self.status_label.configure(
                            text=t["status_success_zip"].format(engine.screen_w, engine.screen_h, bg_hex),
                            text_color="#4ADE80"
                        )
                        self.open_dir_btn.pack(fill="x", pady=(6, 0))
                        messagebox.showinfo(
                            t["dlg_export_success_title"],
                            t["zip_success_msg"].format(
                                engine.screen_w, engine.screen_h, engine.fps, bg_hex, save_path
                            )
                        )
                    else:
                        self.status_label.configure(
                            text=f"Warning: {verify_res['errors']}",
                            text_color="#FBBF24"
                        )

                self.after(0, on_done)

            except Exception as e:
                def on_err(err_msg):
                    self._set_busy(False)
                    t = self.I18N[self.current_lang]
                    self.status_label.configure(text=f"Error: {err_msg}", text_color="#F87171")
                    messagebox.showerror(t["dlg_export_fail_title"], str(err_msg))

                self.after(0, lambda: on_err(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_export_gif(self):
        if self.is_busy:
            return

        save_path = filedialog.asksaveasfilename(
            title=self._t("dlg_save_gif"),
            defaultextension=".gif",
            initialfile="preview.gif",
            filetypes=[("GIF files", "*.gif")]
        )
        if not save_path:
            return

        self.last_export_path = save_path
        self._set_busy(True)

        def worker():
            try:
                engine = self._create_engine(for_preview=False)
                if not engine:
                    raise ValueError("Please select a valid image first.")

                def progress_cb(cur, total, msg):
                    ratio = cur / max(1, total)
                    self.after(0, lambda: self._update_progress(ratio, msg))

                GifExporter.export_preview_gif(engine, save_path, progress_callback=progress_cb)

                def on_done():
                    self._set_busy(False)
                    self.prog_bar.set(1.0)
                    t = self.I18N[self.current_lang]
                    self.status_label.configure(text=t["status_success_gif"], text_color="#4ADE80")
                    self.open_dir_btn.pack(fill="x", pady=(6, 0))
                    messagebox.showinfo(
                        t["dlg_export_success_title"],
                        t["gif_success_msg"].format(save_path)
                    )

                self.after(0, on_done)

            except Exception as e:
                def on_err(err_msg):
                    self._set_busy(False)
                    t = self.I18N[self.current_lang]
                    self.status_label.configure(text=f"GIF error: {err_msg}", text_color="#F87171")
                    messagebox.showerror(t["dlg_export_fail_title"], str(err_msg))

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
            messagebox.showinfo("Notice", "File or directory does not exist.")


def run_app():
    app = BootAnimationApp()
    app.mainloop()


if __name__ == "__main__":
    run_app()
