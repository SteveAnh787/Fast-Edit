"""
Composer Tab - Tab ghép & render với video composition và subtitle styling
"""

from pathlib import Path
import subprocess
from typing import Dict, List, Tuple, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
    QTextEdit, QFileDialog, QMessageBox, QScrollArea,
    QColorDialog, QSlider, QFrame, QDialog, QProgressBar, QDialogButtonBox
)
from PySide6.QtCore import Qt, QThread, Signal, QObject, QEvent
from PySide6.QtGui import QFont, QColor
from PySide6.QtGui import QDesktopServices

from src.core.video_composer import (
    VideoComposer,
    RenderOptions,
    SubtitleStyle,
    AnimationSettings,
    TransitionSettings,
    RenderBatchResult,
)
from src.core.filter_presets import audio_presets_list, video_presets_list, FilterPreset


class RenderWorker(QObject):
    """Background worker that drives the VideoComposer."""

    finished = Signal(object, str)
    error = Signal(str)
    progress = Signal(str, float, str)

    def __init__(
        self,
        audio_directory: str,
        image_directory: str,
        output_directory: str,
        subtitle_directory: Optional[str],
        options: RenderOptions,
        mode: str,
        create_individual: bool,
        create_combined: bool,
    ) -> None:
        super().__init__()
        self._audio_directory = audio_directory
        self._image_directory = image_directory
        self._output_directory = output_directory
        self._subtitle_directory = subtitle_directory
        self._options = options
        self._mode = mode
        self._create_individual = create_individual
        self._create_combined = create_combined

    def _progress_callback(self, stage: str, ratio: float, message: Optional[str]) -> None:
        self.progress.emit(stage, ratio, message or "")

    def run(self) -> None:
        composer = VideoComposer()
        try:
            result = composer.render_project(
                audio_directory=self._audio_directory,
                image_directory=self._image_directory,
                output_directory=self._output_directory,
                subtitle_directory=self._subtitle_directory,
                options=self._options,
                create_individual=self._create_individual,
                create_combined=self._create_combined,
                progress_callback=self._progress_callback,
            )
        except Exception as exc:  # pragma: no cover - runtime execution branch
            self.error.emit(str(exc))
            return

        self.finished.emit(result, self._mode)
from src.ui.unified_styles import UnifiedStyles

class ComposerTab(QWidget):
    """Tab ghép & render video với subtitle styling"""
    
    def __init__(self):
        super().__init__()
        self.setObjectName("ComposerTabRoot")
        self.video_composer = VideoComposer()
        
        # Subtitle styling state
        self.font_family = "Space Grotesk"
        self.font_size = 48
        self.text_color = "#FFFFFF"
        self.outline_color = "#000000"
        self.outline_width = 2.0
        self.letter_spacing = 0.0
        self.preview_text = "Type content to see preview"
        
        self._group_boxes: List[QGroupBox] = []
        self._header_labels: List[QLabel] = []
        self._section_titles: List[QLabel] = []
        self._overline_labels: List[QLabel] = []
        self._caption_labels: List[QLabel] = []
        self._status_labels: List[QLabel] = []
        self._text_panels: List[QTextEdit] = []
        self._input_widgets: List[QWidget] = []
        self._button_configs: List[tuple] = []
        self._checkboxes: List[QCheckBox] = []
        self._color_buttons: List[QPushButton] = []
        self._info_frames: List[QFrame] = []
        self.video_filter_checkboxes: List[QCheckBox] = []
        self.audio_filter_checkboxes: List[QCheckBox] = []
        self._threads: List[QThread] = []
        self._workers: List[QObject] = []
        self._active_mode: Optional[str] = None
        self._progress_dialog: Optional[ProgressDialog] = None
        self._last_output_dir: Optional[Path] = None

        self.init_ui()
        self.refresh_theme()
        
    def init_ui(self):
        """Initialize composer tab UI"""
        # Main layout with scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        content_widget = QWidget()
        scroll.setWidget(content_widget)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
        
        # Content layout
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(24)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Header
        header = QLabel("CONTENT COMPOSITION & RENDER")
        header.setFont(QFont("Space Grotesk", 11, QFont.Bold))
        self._apply_header_label_style(header)
        layout.addWidget(header)
        
        # Main content grid - directories and settings
        directories_grid = QGridLayout()
        directories_grid.setSpacing(24)
        
        # Left column - Input directories
        input_dirs_widget = self.create_input_directories_widget()
        directories_grid.addWidget(input_dirs_widget, 0, 0)
        
        # Right column - Output settings
        output_settings_widget = self.create_output_settings_widget()
        directories_grid.addWidget(output_settings_widget, 0, 1)

        layout.addLayout(directories_grid)

        # Logo settings section
        logo_section = self.create_logo_settings_widget()
        layout.addWidget(logo_section)

        motion_widget = self.create_motion_settings_widget()
        layout.addWidget(motion_widget)

        effects_widget = self.create_effects_settings_widget()
        layout.addWidget(effects_widget)

        # Subtitle styling section
        subtitle_section = self.create_subtitle_styling_section()
        layout.addWidget(subtitle_section)
        
        # Two render buttons with English text
        render_buttons_layout = QHBoxLayout()
        render_buttons_layout.setSpacing(16)
        
        # Button 1: Individual videos
        self.render_individual_btn = QPushButton("Create Individual Videos")
        self.render_individual_btn.clicked.connect(self.start_individual_render)
        self.apply_button_style(self.render_individual_btn, "primary", "large")
        
        # Button 2: Complete video
        self.render_complete_btn = QPushButton("Create Complete Video")
        self.render_complete_btn.clicked.connect(self.start_complete_render)
        self.apply_button_style(self.render_complete_btn, "primary", "large")
        
        render_buttons_layout.addWidget(self.render_individual_btn)
        render_buttons_layout.addWidget(self.render_complete_btn)
        
        layout.addLayout(render_buttons_layout)
        
        # Status and results
        self.render_status = QLabel("")
        self._apply_status_style(self.render_status)
        layout.addWidget(self.render_status)
        
        self.render_results = QTextEdit()
        self.render_results.setMaximumHeight(200)
        self._apply_text_panel_style(self.render_results)
        self.render_results.hide()
        layout.addWidget(self.render_results)
        
        layout.addStretch()
        
    def create_input_directories_widget(self):
        """Create input directories widget"""
        group = QGroupBox()
        self._apply_group_style(group)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(16)

        # Audio directory
        audio_layout = self.create_directory_input("AUDIO DIRECTORY", "Path to audio folder")
        self.audio_directory = audio_layout[1]
        audio_browse_btn = audio_layout[2]
        audio_browse_btn.clicked.connect(self.browse_audio_directory)
        layout.addLayout(audio_layout[0])
        
        # Image directory  
        image_layout = self.create_directory_input("IMAGE DIRECTORY", "Path to image folder")
        self.image_directory = image_layout[1]
        image_browse_btn = image_layout[2]
        image_browse_btn.clicked.connect(self.browse_image_directory)
        layout.addLayout(image_layout[0])
        
        # Subtitle directory (optional)
        subtitle_layout = self.create_directory_input("SUBTITLE DIRECTORY (OPTIONAL)", "Path to subtitle .srt folder")
        self.subtitle_directory = subtitle_layout[1]
        subtitle_browse_btn = subtitle_layout[2]
        subtitle_browse_btn.clicked.connect(self.browse_subtitle_directory)
        layout.addLayout(subtitle_layout[0])
        
        # Background Music directory (optional)
        music_layout = self.create_directory_input("BACKGROUND MUSIC DIRECTORY (OPTIONAL)", "Path to background music folder")
        self.music_directory = music_layout[1]
        music_browse_btn = music_layout[2]
        music_browse_btn.clicked.connect(self.browse_music_directory)
        layout.addLayout(music_layout[0])
        
        # Output directory
        output_layout = self.create_directory_input("OUTPUT DIRECTORY", "Path to save videos (.mp4)")
        self.output_directory = output_layout[1]
        output_browse_btn = output_layout[2]
        output_browse_btn.clicked.connect(self.browse_output_directory)
        layout.addLayout(output_layout[0])

        sync_label = QLabel("SYNC MODE")
        self._apply_overline_style(sync_label)
        self.sync_mode_combo = QComboBox()
        self.sync_mode_combo.addItem("Standard pairing (1:1 files)", "standard")
        self.sync_mode_combo.addItem("Sync Audio • distribute visuals evenly", "sync_audio")
        self.sync_mode_combo.addItem("Sync Images • reuse visuals to cover audio", "sync_images")
        self.apply_input_style(self.sync_mode_combo)
        layout.addWidget(sync_label)
        layout.addWidget(self.sync_mode_combo)
        
        return group
        
    def create_output_settings_widget(self):
        """Create output settings widget"""
        group = QGroupBox()
        self._apply_group_style(group)

        layout = QVBoxLayout(group)
        layout.setSpacing(16)

        # Frame rate
        frame_rate_label = QLabel("FRAME RATE")
        self._apply_overline_style(frame_rate_label)
        self.frame_rate = QLineEdit()
        self.frame_rate.setPlaceholderText("30")
        self.frame_rate.setText("30")
        self.apply_input_style(self.frame_rate)

        layout.addWidget(frame_rate_label)
        layout.addWidget(self.frame_rate)

        # Video codec
        codec_label = QLabel("VIDEO CODEC")
        self._apply_overline_style(codec_label)
        self.video_codec = QComboBox()
        self.video_codec.addItems([
            "H.264 (VideoToolbox)",
            "HEVC H.265 (VideoToolbox)"
        ])
        self.apply_input_style(self.video_codec)

        layout.addWidget(codec_label)
        layout.addWidget(self.video_codec)

        # Audio bitrate
        bitrate_label = QLabel("AUDIO BITRATE")
        self._apply_overline_style(bitrate_label)
        self.audio_bitrate = QLineEdit()
        self.audio_bitrate.setPlaceholderText("192k")
        self.audio_bitrate.setText("192k")
        self.apply_input_style(self.audio_bitrate)

        layout.addWidget(bitrate_label)
        layout.addWidget(self.audio_bitrate)

        # Video bitrate
        video_bitrate_label = QLabel("VIDEO BITRATE")
        self._apply_overline_style(video_bitrate_label)
        self.video_bitrate = QLineEdit()
        self.video_bitrate.setPlaceholderText("8000k")
        self.video_bitrate.setText("8000k")
        self.apply_input_style(self.video_bitrate)

        layout.addWidget(video_bitrate_label)
        layout.addWidget(self.video_bitrate)

        # Resolution
        resolution_label = QLabel("OUTPUT RESOLUTION")
        self._apply_overline_style(resolution_label)
        resolution_layout = QHBoxLayout()
        self.resolution_width = QSpinBox()
        self.resolution_width.setRange(640, 4096)
        self.resolution_width.setValue(1920)
        self.apply_input_style(self.resolution_width)
        multiply_label = QLabel("×")
        self._apply_caption_style(multiply_label)
        self.resolution_height = QSpinBox()
        self.resolution_height.setRange(360, 2160)
        self.resolution_height.setValue(1080)
        self.apply_input_style(self.resolution_height)
        resolution_layout.addWidget(self.resolution_width)
        resolution_layout.addWidget(multiply_label)
        resolution_layout.addWidget(self.resolution_height)

        layout.addWidget(resolution_label)
        layout.addLayout(resolution_layout)

        # Burn subtitles checkbox - SET DEFAULT TO CHECKED
        self.burn_subtitles = QCheckBox("Burn subtitles directly into video")
        self.burn_subtitles.setChecked(True)  # Default checked
        self._apply_checkbox_style(self.burn_subtitles)
        layout.addWidget(self.burn_subtitles)

        # Hardware acceleration
        self.use_hardware_checkbox = QCheckBox("Hardware acceleration (VideoToolbox)")
        self.use_hardware_checkbox.setChecked(True)
        self._apply_checkbox_style(self.use_hardware_checkbox)
        layout.addWidget(self.use_hardware_checkbox)

        # Info box
        info_frame = QFrame()
        self._apply_info_frame_style(info_frame)

        info_layout = QVBoxLayout(info_frame)
        info_text = QLabel("""Images will be looped until audio ends. If "Burn subtitles" is enabled, subtitles will be rendered directly into the video frame, otherwise they will be embedded as soft subtitles.""")
        info_text.setWordWrap(True)
        self._apply_caption_style(info_text)
        
        req_text = QLabel("Requires ffmpeg and ffprobe installed in PATH.")
        self._apply_caption_style(req_text)
        
        info_layout.addWidget(info_text)
        info_layout.addWidget(req_text)

        layout.addWidget(info_frame)

        return group

    def create_logo_settings_widget(self):
        """Create logo settings widget with comprehensive controls"""
        group = QGroupBox()
        self._apply_group_style(group)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(16)
        
        # Header
        logo_title = QLabel("Logo & Overlay Settings")
        logo_title.setFont(QFont("Space Grotesk", 14, QFont.Bold))
        self._apply_section_title_style(logo_title)
        layout.addWidget(logo_title)
        
        # Logo file input
        logo_file_layout = self.create_file_input("LOGO FILE (OPTIONAL)", "Select logo image file (.png, .jpg, .svg)")
        self.logo_file = logo_file_layout[1]
        logo_browse_btn = logo_file_layout[2]
        logo_browse_btn.clicked.connect(self.browse_logo_file)
        layout.addLayout(logo_file_layout[0])
        
        # Logo settings grid
        logo_grid = QGridLayout()
        logo_grid.setSpacing(12)
        
        # Logo size
        size_label = QLabel("SIZE (%)")
        self._apply_overline_style(size_label)
        self.logo_size = QSpinBox()
        self.logo_size.setRange(5, 200)
        self.logo_size.setValue(15)
        self.logo_size.setSuffix("%")
        self.apply_input_style(self.logo_size)
        
        # Logo opacity - SET DEFAULT TO 100%
        opacity_label = QLabel("OPACITY (%)")
        self._apply_overline_style(opacity_label)
        self.logo_opacity = QSpinBox()
        self.logo_opacity.setRange(0, 100)
        self.logo_opacity.setValue(100)  # Changed from 80 to 100
        self.logo_opacity.setSuffix("%")
        self.apply_input_style(self.logo_opacity)
        
        logo_grid.addWidget(size_label, 0, 0)
        logo_grid.addWidget(self.logo_size, 1, 0)
        logo_grid.addWidget(opacity_label, 0, 1)
        logo_grid.addWidget(self.logo_opacity, 1, 1)
        
        layout.addLayout(logo_grid)
        
        # Position controls
        position_grid = QGridLayout()
        position_grid.setSpacing(12)
        
        # X Position
        x_label = QLabel("X POSITION")
        self._apply_overline_style(x_label)
        self.logo_x = QSpinBox()
        self.logo_x.setRange(-500, 2000)
        self.logo_x.setValue(50)
        self.apply_input_style(self.logo_x)
        
        # Y Position
        y_label = QLabel("Y POSITION")
        self._apply_overline_style(y_label)
        self.logo_y = QSpinBox()
        self.logo_y.setRange(-500, 2000)
        self.logo_y.setValue(50)
        self.apply_input_style(self.logo_y)
        
        position_grid.addWidget(x_label, 0, 0)
        position_grid.addWidget(self.logo_x, 1, 0)
        position_grid.addWidget(y_label, 0, 1)
        position_grid.addWidget(self.logo_y, 1, 1)
        
        layout.addLayout(position_grid)
        
        # Position presets
        preset_label = QLabel("POSITION PRESETS")
        self._apply_overline_style(preset_label)
        layout.addWidget(preset_label)
        
        preset_layout = QHBoxLayout()
        
        # Position preset buttons
        positions = [
            ("Top Left", (50, 50)),
            ("Top Right", (1820, 50)),
            ("Bottom Left", (50, 980)),
            ("Bottom Right", (1820, 980)),
            ("Center", (960, 540))
        ]
        
        for text, (x, y) in positions:
            btn = QPushButton(text)
            btn.clicked.connect(lambda checked, x=x, y=y: self.set_logo_position(x, y))
            self.apply_button_style(btn, "preset")
            preset_layout.addWidget(btn)
        
        layout.addLayout(preset_layout)
        
        # Advanced options
        advanced_layout = QHBoxLayout()
        
        # Remove background checkbox
        self.remove_background = QCheckBox("Remove background (PNG transparency)")
        self._apply_checkbox_style(self.remove_background)
        advanced_layout.addWidget(self.remove_background)
        
        # Enable logo checkbox - SET DEFAULT TO CHECKED
        self.enable_logo = QCheckBox("Enable logo overlay")
        self.enable_logo.setChecked(True)  # Default checked
        self._apply_checkbox_style(self.enable_logo)
        advanced_layout.addWidget(self.enable_logo)
        
        layout.addLayout(advanced_layout)
        
        # Info box
        info_frame = QFrame()
        self._apply_info_frame_style(info_frame)
        
        info_layout = QVBoxLayout(info_frame)
        info_text = QLabel("Logo will be overlaid on all video frames. Position coordinates are relative to 1920x1080 output. Use PNG files for transparency support.")
        info_text.setWordWrap(True)
        self._apply_caption_style(info_text)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_frame)

        return group

    def create_effects_settings_widget(self):
        """UI for selecting reusable FFmpeg filters and audio effects."""
        group = QGroupBox()
        self._apply_group_style(group)

        layout = QHBoxLayout(group)
        layout.setSpacing(24)

        video_layout = QVBoxLayout()
        video_title = QLabel("VIDEO FILTERS")
        self._apply_overline_style(video_title)
        video_layout.addWidget(video_title)

        for category, presets in self._group_presets_by_category(video_presets_list()):
            section_label = QLabel(category.upper())
            self._apply_section_title_style(section_label)
            video_layout.addWidget(section_label)
            for preset in presets:
                checkbox = QCheckBox(preset.name)
                checkbox.setToolTip(preset.description)
                checkbox.setProperty("filter_id", preset.id)
                self._apply_checkbox_style(checkbox)
                video_layout.addWidget(checkbox)
                self.video_filter_checkboxes.append(checkbox)

        video_layout.addStretch()

        audio_layout = QVBoxLayout()
        audio_title = QLabel("AUDIO EFFECTS")
        self._apply_overline_style(audio_title)
        audio_layout.addWidget(audio_title)

        for category, presets in self._group_presets_by_category(audio_presets_list()):
            section_label = QLabel(category.upper())
            self._apply_section_title_style(section_label)
            audio_layout.addWidget(section_label)
            for preset in presets:
                checkbox = QCheckBox(preset.name)
                checkbox.setToolTip(preset.description)
                checkbox.setProperty("filter_id", preset.id)
                self._apply_checkbox_style(checkbox)
                audio_layout.addWidget(checkbox)
                self.audio_filter_checkboxes.append(checkbox)

        audio_layout.addStretch()

        layout.addLayout(video_layout)
        layout.addLayout(audio_layout)
        layout.setStretch(0, 1)
        layout.setStretch(1, 1)

        return group

    def _group_presets_by_category(self, presets: List[FilterPreset]) -> List[Tuple[str, List[FilterPreset]]]:
        grouped: Dict[str, List[FilterPreset]] = {}
        for preset in presets:
            grouped.setdefault(preset.category, []).append(preset)
        return list(grouped.items())

    def create_motion_settings_widget(self):
        """Animation and transition configuration."""
        group = QGroupBox()
        self._apply_group_style(group)

        layout = QGridLayout(group)
        layout.setSpacing(12)

        # Animation type
        animation_label = QLabel("ANIMATION")
        self._apply_overline_style(animation_label)
        self.animation_type_combo = QComboBox()
        animation_items = [
            ("None", "none"),
            ("Zoom In", "zoom_in"),
            ("Zoom Out", "zoom_out"),
            ("Ken Burns (Zoom + Pan)", "ken_burns"),
            ("Pan Left", "pan_left"),
            ("Pan Right", "pan_right"),
            ("Pan Up", "pan_up"),
            ("Pan Down", "pan_down"),
        ]
        for text, value in animation_items:
            self.animation_type_combo.addItem(text, value)
        self.apply_input_style(self.animation_type_combo)

        # Animation intensity
        intensity_label = QLabel("ANIMATION INTENSITY")
        self._apply_overline_style(intensity_label)
        self.animation_intensity_combo = QComboBox()
        intensity_items = [
            ("Subtle", "subtle"),
            ("Medium", "medium"),
            ("Strong", "strong"),
        ]
        for text, value in intensity_items:
            self.animation_intensity_combo.addItem(text, value)
        self.animation_intensity_combo.setCurrentIndex(1)
        self.apply_input_style(self.animation_intensity_combo)

        # Transition type
        transition_label = QLabel("TRANSITION")
        self._apply_overline_style(transition_label)
        self.transition_type_combo = QComboBox()
        transition_items = [
            ("None", "none"),
            ("Fade", "fade"),
            ("Dissolve", "dissolve"),
            ("Crossfade", "crossfade"),
            ("Wipe Left", "wipe_left"),
            ("Wipe Right", "wipe_right"),
            ("Wipe Up", "wipe_up"),
            ("Wipe Down", "wipe_down"),
            ("Slide Left", "slide_left"),
            ("Slide Right", "slide_right"),
            ("Slide Up", "slide_up"),
            ("Slide Down", "slide_down"),
            ("Smooth Left", "smooth_left"),
            ("Smooth Right", "smooth_right"),
            ("Fade to White", "fade_white"),
            ("Blur Fade", "blur"),
            ("Circle Open", "circle_open"),
            ("Circle Close", "circle_close"),
            ("Pixelize", "pixelize"),
            ("Radial", "radial"),
        ]
        for text, value in transition_items:
            self.transition_type_combo.addItem(text, value)
        self.apply_input_style(self.transition_type_combo)

        # Transition duration
        transition_duration_label = QLabel("TRANSITION DURATION (s)")
        self._apply_overline_style(transition_duration_label)
        self.transition_duration_spin = QDoubleSpinBox()
        self.transition_duration_spin.setDecimals(2)
        self.transition_duration_spin.setRange(0.2, 5.0)
        self.transition_duration_spin.setSingleStep(0.2)
        self.transition_duration_spin.setValue(1.0)
        self.apply_input_style(self.transition_duration_spin)

        layout.addWidget(animation_label, 0, 0)
        layout.addWidget(self.animation_type_combo, 1, 0)
        layout.addWidget(intensity_label, 0, 1)
        layout.addWidget(self.animation_intensity_combo, 1, 1)
        layout.addWidget(transition_label, 2, 0)
        layout.addWidget(self.transition_type_combo, 3, 0)
        layout.addWidget(transition_duration_label, 2, 1)
        layout.addWidget(self.transition_duration_spin, 3, 1)

        return group
        
    def create_subtitle_styling_section(self):
        """Create subtitle styling section with new layout"""
        # Main container
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
            }
        """)
        
        main_layout = QHBoxLayout(container)
        main_layout.setSpacing(24)
        
        # Left Panel - Controls
        controls_group = QGroupBox()
        self._apply_group_style(controls_group)
        
        controls_layout = QVBoxLayout(controls_group)
        controls_layout.setSpacing(16)
        
        # Header
        controls_title = QLabel("Subtitle Styling (Burn-in)")
        controls_title.setFont(QFont("Space Grotesk", 14, QFont.Bold))
        self._apply_section_title_style(controls_title)
        controls_layout.addWidget(controls_title)

        # Preview text input - moved to top
        preview_label = QLabel("SAMPLE CONTENT")
        self._apply_overline_style(preview_label)
        
        self.preview_text_input = QLineEdit()
        self.preview_text_input.setPlaceholderText("Type subtitle content to preview...")
        self.preview_text_input.textChanged.connect(self.update_preview_text)
        self.apply_input_style(self.preview_text_input)
        
        controls_layout.addWidget(preview_label)
        controls_layout.addWidget(self.preview_text_input)
        
        # Font controls in grid
        font_grid = QGridLayout()
        font_grid.setSpacing(12)
        
        # Font family
        font_label = QLabel("FONT")
        self._apply_overline_style(font_label)
        self.font_combo = QComboBox()
        self.font_combo.addItems(
            [
                "Space Grotesk",
                "Montserrat",
                "Roboto",
                "Open Sans",
                "Arial",
                "Helvetica",
                "Arial Black",
            ]
        )
        self.font_combo.currentTextChanged.connect(self.update_font_family)
        self.apply_input_style(self.font_combo)
        
        # Font size
        size_label = QLabel("SIZE")
        self._apply_overline_style(size_label)
        self.font_size_input = QSpinBox()
        self.font_size_input.setRange(12, 120)
        self.font_size_input.setValue(48)
        self.font_size_input.valueChanged.connect(self.update_font_size)
        self.apply_input_style(self.font_size_input)
        
        font_grid.addWidget(font_label, 0, 0)
        font_grid.addWidget(self.font_combo, 1, 0)
        font_grid.addWidget(size_label, 0, 1)
        font_grid.addWidget(self.font_size_input, 1, 1)
        
        controls_layout.addLayout(font_grid)
        
        # Color controls - better layout
        color_grid = QGridLayout()
        color_grid.setSpacing(12)
        
        # Text color
        text_color_label = QLabel("TEXT COLOR")
        self._apply_overline_style(text_color_label)
        
        text_color_layout = QHBoxLayout()
        self.text_color_btn = QPushButton()
        self.text_color_btn.setFixedSize(48, 40)
        self._apply_color_button_style(self.text_color_btn, self.text_color)
        self.text_color_btn.clicked.connect(self.choose_text_color)
        
        self.text_color_input = QLineEdit(self.text_color)
        self.text_color_input.textChanged.connect(self.update_text_color)
        self.apply_input_style(self.text_color_input)
        
        text_color_layout.addWidget(self.text_color_btn)
        text_color_layout.addWidget(self.text_color_input)
        
        # Outline color
        outline_color_label = QLabel("OUTLINE COLOR")
        self._apply_overline_style(outline_color_label)
        
        outline_color_layout = QHBoxLayout()
        self.outline_color_btn = QPushButton()
        self.outline_color_btn.setFixedSize(48, 40)
        self._apply_color_button_style(self.outline_color_btn, self.outline_color)
        self.outline_color_btn.clicked.connect(self.choose_outline_color)
        
        self.outline_color_input = QLineEdit(self.outline_color)
        self.outline_color_input.textChanged.connect(self.update_outline_color)
        self.apply_input_style(self.outline_color_input)
        
        outline_color_layout.addWidget(self.outline_color_btn)
        outline_color_layout.addWidget(self.outline_color_input)
        
        color_grid.addWidget(text_color_label, 0, 0)
        color_grid.addLayout(text_color_layout, 1, 0)
        color_grid.addWidget(outline_color_label, 0, 1)
        color_grid.addLayout(outline_color_layout, 1, 1)
        
        controls_layout.addLayout(color_grid)
        
        # Advanced controls
        advanced_grid = QGridLayout()
        advanced_grid.setSpacing(12)
        
        # Outline width
        width_label = QLabel("OUTLINE WIDTH")
        self._apply_overline_style(width_label)
        self.outline_width_input = QSpinBox()
        self.outline_width_input.setRange(0, 10)
        self.outline_width_input.setValue(2)
        self.outline_width_input.valueChanged.connect(self.update_outline_width)
        self.apply_input_style(self.outline_width_input)
        
        # Letter spacing
        spacing_label = QLabel("LETTER SPACING")
        self._apply_overline_style(spacing_label)
        self.letter_spacing_input = QSpinBox()
        self.letter_spacing_input.setRange(-5, 10)
        self.letter_spacing_input.setValue(0)
        self.letter_spacing_input.valueChanged.connect(self.update_letter_spacing)
        self.apply_input_style(self.letter_spacing_input)
        
        advanced_grid.addWidget(width_label, 0, 0)
        advanced_grid.addWidget(self.outline_width_input, 1, 0)
        advanced_grid.addWidget(spacing_label, 0, 1)
        advanced_grid.addWidget(self.letter_spacing_input, 1, 1)
        
        controls_layout.addLayout(advanced_grid)
        
        # Subtitle position controls
        position_grid = QGridLayout()
        position_grid.setSpacing(12)
        
        # Margin from bottom
        margin_label = QLabel("MARGIN FROM BOTTOM (PX)")
        self._apply_overline_style(margin_label)
        self.margin_bottom_input = QSpinBox()
        self.margin_bottom_input.setRange(0, 300)
        self.margin_bottom_input.setValue(60)
        self.margin_bottom_input.valueChanged.connect(self.update_margin_bottom)
        self.apply_input_style(self.margin_bottom_input)
        
        # Alignment
        alignment_label = QLabel("ALIGNMENT")
        self._apply_overline_style(alignment_label)
        self.alignment_combo = QComboBox()
        self.alignment_combo.addItems(["Left", "Center", "Right"])
        self.alignment_combo.setCurrentIndex(1)  # Default to Center
        self.alignment_combo.currentIndexChanged.connect(self.update_alignment)
        self.apply_input_style(self.alignment_combo)
        
        position_grid.addWidget(margin_label, 0, 0)
        position_grid.addWidget(self.margin_bottom_input, 1, 0)
        position_grid.addWidget(alignment_label, 0, 1)
        position_grid.addWidget(self.alignment_combo, 1, 1)
        
        controls_layout.addLayout(position_grid)
        
        # Right Panel - Preview
        preview_group = QGroupBox()
        self._apply_group_style(preview_group)
        
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setSpacing(16)
        
        # Preview header
        preview_title = QLabel("Preview")
        preview_title.setFont(QFont("Space Grotesk", 14, QFont.Bold))
        self._apply_section_title_style(preview_title)
        preview_layout.addWidget(preview_title)

        # Preview area
        self.preview_frame = QFrame()
        self.preview_frame.setMinimumHeight(320)
        self._apply_preview_frame_style()
        
        preview_frame_layout = QVBoxLayout(self.preview_frame)
        preview_frame_layout.setAlignment(Qt.AlignCenter)
        
        self.preview_label = QLabel(self.preview_text)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setWordWrap(True)
        self.update_preview_style()
        
        preview_frame_layout.addWidget(self.preview_label)
        preview_layout.addWidget(self.preview_frame)
        
        # Quick preset buttons
        preset_layout = QHBoxLayout()
        
        preset_vi_btn = QPushButton("Tiếng Việt")
        preset_vi_btn.clicked.connect(lambda: self.set_preview_text("Xin chào! Đây là phụ đề mẫu."))
        self.apply_button_style(preset_vi_btn, "preset", "small")
        
        preset_en_btn = QPushButton("English")
        preset_en_btn.clicked.connect(lambda: self.set_preview_text("Hello! This is a sample subtitle."))
        self.apply_button_style(preset_en_btn, "preset", "small")
        
        preset_clear_btn = QPushButton("Clear")
        preset_clear_btn.clicked.connect(lambda: self.set_preview_text(""))
        self.apply_button_style(preset_clear_btn, "preset", "small")
        
        preset_layout.addWidget(preset_vi_btn)
        preset_layout.addWidget(preset_en_btn)
        preset_layout.addWidget(preset_clear_btn)
        preset_layout.addStretch()
        
        preview_layout.addLayout(preset_layout)
        
        # Add to main layout
        main_layout.addWidget(controls_group)
        main_layout.addWidget(preview_group)
        
        return container
        
    def create_directory_input(self, label_text, placeholder):
        """Create a directory input layout"""
        layout = QVBoxLayout()
        layout.setSpacing(8)

        label = QLabel(label_text)
        self._apply_overline_style(label)

        input_layout = QHBoxLayout()
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)

        browse_btn = QPushButton("Browse")
        self.apply_button_style(browse_btn, "outline", "small")

        self.apply_input_style(line_edit)
        
        input_layout.addWidget(line_edit)
        input_layout.addWidget(browse_btn)
        
        layout.addWidget(label)
        layout.addLayout(input_layout)
        
        return (layout, line_edit, browse_btn)

    def create_file_input(self, label_text, placeholder):
        """Create a file input layout for logo selection"""
        layout = QVBoxLayout()
        layout.setSpacing(8)

        label = QLabel(label_text)
        self._apply_overline_style(label)

        input_layout = QHBoxLayout()
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)

        browse_btn = QPushButton("Browse")
        self.apply_button_style(browse_btn, "outline", "small")

        self.apply_input_style(line_edit)
        
        input_layout.addWidget(line_edit)
        input_layout.addWidget(browse_btn)
        
        layout.addWidget(label)
        layout.addLayout(input_layout)
        
        return (layout, line_edit, browse_btn)

    def browse_logo_file(self):
        """Browse for logo file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Logo File", 
            "", 
            "Image Files (*.png *.jpg *.jpeg *.svg *.bmp *.gif)"
        )
        if file_path:
            self.logo_file.setText(file_path)

    def set_logo_position(self, x: int, y: int):
        """Set logo position from preset buttons"""
        self.logo_x.setValue(x)
        self.logo_y.setValue(y)

    # ------------------------------------------------------------------
    # Render helpers
    # ------------------------------------------------------------------
    def _collect_render_inputs(self) -> Optional[Tuple[str, str, Optional[str], str]]:
        audio_dir = self.audio_directory.text().strip()
        image_dir = self.image_directory.text().strip()
        output_dir = self.output_directory.text().strip()
        subtitle_dir = self.subtitle_directory.text().strip()

        if not audio_dir or not image_dir or not output_dir:
            QMessageBox.warning(self, "Compose & Render", "Please select audio, image and output directories.")
            return None

        if not subtitle_dir:
            default_sub_dir = Path(audio_dir) / "subtitles"
            subtitle_dir = str(default_sub_dir) if default_sub_dir.exists() else None

        return audio_dir, image_dir, subtitle_dir, output_dir

    def _collect_render_options(self) -> RenderOptions:
        try:
            frame_rate = float(self.frame_rate.text().strip() or 30.0)
        except ValueError:
            frame_rate = 30.0

        audio_bitrate = self.audio_bitrate.text().strip() or "192k"
        video_bitrate = self.video_bitrate.text().strip() or "8000k"
        video_codec = "hevc" if "HEVC" in self.video_codec.currentText() else "h264"

        subtitle_style = SubtitleStyle(
            font_name=self.font_combo.currentText(),
            font_size=self.font_size_input.value(),
            primary_color=self.text_color_input.text().strip() or self.text_color,
            outline_color=self.outline_color_input.text().strip() or self.outline_color,
            outline_width=float(self.outline_width_input.value()),
            letter_spacing=float(self.letter_spacing_input.value()),
            margin_bottom=self.margin_bottom_input.value(),
            alignment=self.alignment_combo.currentIndex() + 1,  # Convert to ASS alignment (1, 2, 3)
        )

        animation = AnimationSettings(
            type=self.animation_type_combo.currentData() or "none",
            intensity=self.animation_intensity_combo.currentData() or "medium",
        )

        transition = TransitionSettings(
            type=self.transition_type_combo.currentData() or "none",
            duration=float(self.transition_duration_spin.value()),
        )

        video_filters = [
            str(cb.property("filter_id"))
            for cb in self.video_filter_checkboxes
            if cb.isChecked() and cb.property("filter_id")
        ]
        audio_filters = [
            str(cb.property("filter_id"))
            for cb in self.audio_filter_checkboxes
            if cb.isChecked() and cb.property("filter_id")
        ]

        resolution = (self.resolution_width.value(), self.resolution_height.value())

        # Collect background music directory
        music_dir = self.music_directory.text().strip() or None
        
        # Collect logo settings
        logo_file = self.logo_file.text().strip() or None
        logo_enabled = self.enable_logo.isChecked() and bool(logo_file)

        sync_mode_value = "standard"
        if hasattr(self, "sync_mode_combo") and self.sync_mode_combo:
            sync_mode_value = self.sync_mode_combo.currentData() or "standard"

        return RenderOptions(
            frame_rate=frame_rate,
            resolution=resolution,
            video_codec=video_codec,
            video_bitrate=video_bitrate,
            audio_bitrate=audio_bitrate,
            burn_subtitles=self.burn_subtitles.isChecked(),
            subtitle_style=subtitle_style,
            animation=animation,
            transition=transition,
            use_hardware_acceleration=self.use_hardware_checkbox.isChecked(),
            video_filters=video_filters,
            audio_filters=audio_filters,
            sync_mode=sync_mode_value,
            # Background music
            background_music_directory=music_dir,
            # Logo settings
            logo_file=logo_file,
            logo_enabled=logo_enabled,
            logo_size=self.logo_size.value(),
            logo_opacity=self.logo_opacity.value(),
            logo_x=self.logo_x.value(),
            logo_y=self.logo_y.value(),
            logo_remove_background=self.remove_background.isChecked(),
        )

    def _prompt_combined_filename(self, suggestion: str) -> Optional[str]:
        dialog = QDialog(self)
        dialog.setWindowTitle("Name Final Video")
        dialog.setModal(True)
        dialog.setFixedSize(360, 150)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        label = QLabel("Enter a name for the combined video:")
        layout.addWidget(label)

        line_edit = QLineEdit()
        line_edit.setText(suggestion)
        layout.addWidget(line_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)

        accepted = {'result': None}

        def accept():
            text = line_edit.text().strip()
            if not text:
                QMessageBox.warning(dialog, "Name Required", "Please enter a file name.")
                return
            accepted['result'] = text
            dialog.accept()

        def reject():
            dialog.reject()

        buttons.accepted.connect(accept)
        buttons.rejected.connect(reject)

        dialog.exec()
        return accepted['result']

    def _start_thread(self, worker: QObject) -> None:
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.error.connect(worker.deleteLater)
        thread.finished.connect(lambda: self._finalize_thread(thread, worker))
        thread.finished.connect(thread.deleteLater)
        thread.start()
        self._threads.append(thread)
        self._workers.append(worker)

    def _finalize_thread(self, thread: QThread, worker: QObject) -> None:
        if thread in self._threads:
            self._threads.remove(thread)
        if worker in self._workers:
            self._workers.remove(worker)
        # Worker deleted via deleteLater connection once thread stops.

    def _handle_render_progress(self, stage: str, ratio: float, message: str) -> None:
        if message:
            percent = max(0, min(int(ratio * 100), 100))
            status_text = f"{message} ({percent}%)"
            self.render_status.setText(status_text)
            if self._progress_dialog:
                self._progress_dialog.update_status(status_text, ratio)

    def _handle_render_finished(self, result: RenderBatchResult, mode: str) -> None:
        self._close_progress_dialog()
        if not isinstance(result, RenderBatchResult):
            self.render_status.setText("Render hoàn tất.")
            self.render_individual_btn.setEnabled(True)
            self.render_complete_btn.setEnabled(True)
            return

        self.render_individual_btn.setEnabled(True)
        self.render_complete_btn.setEnabled(True)

        if mode == "combined" and result.combined:
            status = "Hoàn thành video tổng hợp."
        elif mode == "individual":
            status = "Hoàn thành tạo các video từng cảnh."
        else:
            status = "Render hoàn tất."
        self.render_status.setText(status)

        lines: List[str] = []
        if result.scenes:
            lines.append("✅ Scene clips:")
            for item in result.scenes:
                prefix = "📁" if item.success else "⚠️"
                name = Path(item.output_path).name if item.output_path else "(failed)"
                duration = f"{item.duration:.2f}s" if item.duration else "--"
                if item.success:
                    lines.append(f"{prefix} {name} • {duration}")
                else:
                    lines.append(f"{prefix} {name} — {item.error}")
            lines.append("")

        if result.combined:
            if result.combined.success:
                name = Path(result.combined.output_path).name
                lines.append(f"🎬 Combined video: {name} • {result.combined.duration:.2f}s")
            else:
                lines.append(f"⚠️ Combined video failed: {result.combined.error}")

        if not lines:
            lines.append("Không có video nào được tạo.")

        self.render_results.setPlainText("\n".join(lines))
        self.render_results.show()

        if self._last_output_dir:
            dialog = CompletionDialog(status, self._last_output_dir, self)
            dialog.exec()

    def _handle_render_error(self, message: str) -> None:
        self._close_progress_dialog()
        self.render_individual_btn.setEnabled(True)
        self.render_complete_btn.setEnabled(True)
        self.render_status.setText("Render thất bại.")
        QMessageBox.critical(self, "Compose & Render", message)

    def _open_progress_dialog(self, message: str) -> None:
        self._close_progress_dialog()
        dialog = ProgressDialog(self)
        dialog.update_status(message, 0.0)
        dialog.cancel_button.setEnabled(False)
        dialog.show()
        self._progress_dialog = dialog

    def _close_progress_dialog(self) -> None:
        if self._progress_dialog:
            self._progress_dialog.close()
            self._progress_dialog = None
    def apply_input_style(self, widget):
        """Apply consistent input styling"""
        palette = UnifiedStyles.palette()
        widget.setStyleSheet(
            f"""
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
                background-color: {palette.surface};
                border: 1px solid {palette.outline_variant};
                border-radius: 8px;
                padding: 8px 12px;
                color: {palette.text_primary};
                font-size: 12px;
            }}
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
                border-color: {palette.primary};
                background-color: {palette.surface_bright};
                outline: none;
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox::down-arrow {{ width: 0px; height: 0px; }}
            QSpinBox::up-button,
            QSpinBox::down-button,
            QDoubleSpinBox::up-button,
            QDoubleSpinBox::down-button {{
                background: transparent;
                border: none;
                width: 14px;
            }}
        """
        )

        if widget not in self._input_widgets:
            self._input_widgets.append(widget)

        if isinstance(widget, (QComboBox, QSpinBox, QDoubleSpinBox)):
            self._disable_wheel_event(widget)

    def _disable_wheel_event(self, widget: QWidget) -> None:
        """Ignore wheel events unless the user is actively interacting."""
        widget.setFocusPolicy(Qt.StrongFocus)
        widget.installEventFilter(self)

    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        blocked_types = (QComboBox, QSpinBox, QDoubleSpinBox)

        if event.type() == QEvent.Type.Wheel and isinstance(source, blocked_types):
            if isinstance(source, QComboBox):
                view = source.view()
                if view and view.isVisible():
                    return super().eventFilter(source, event)

            event.ignore()
            return True

        return super().eventFilter(source, event)

    def apply_button_style(self, button, color_scheme="primary", size="medium"):
        scheme_map = {
            "indigo": "secondary",
            "preset": "ghost",
            "gradient": "primary",
            "emerald": "primary",
            "outline": "outline",
        }
        UnifiedStyles.apply_button_style(button, scheme_map.get(color_scheme, color_scheme), size)
        if all(button is not btn for btn, _, __ in self._button_configs):
            self._button_configs.append((button, color_scheme, size))

    def _apply_group_style(self, group: QGroupBox) -> None:
        palette = UnifiedStyles.palette()
        group.setStyleSheet(
            f"""
            QGroupBox {{
                border: 1px solid {palette.outline_variant};
                border-radius: 16px;
                background-color: {palette.surface};
                padding-top: 20px;
                margin-top: 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                top: 10px;
                padding: 0 4px;
            }}
        """
        )
        if group not in self._group_boxes:
            self._group_boxes.append(group)

    def _apply_header_label_style(self, label: QLabel) -> None:
        palette = UnifiedStyles.palette()
        label.setStyleSheet(
            f"""
            color: {palette.text_secondary};
            text-transform: uppercase;
            letter-spacing: 2px;
            font-weight: 600;
            margin-bottom: 12px;
        """
        )
        if label not in self._header_labels:
            self._header_labels.append(label)

    def _apply_section_title_style(self, label: QLabel) -> None:
        palette = UnifiedStyles.palette()
        label.setStyleSheet(f"color: {palette.text_primary}; font-weight: 600;")
        if label not in self._section_titles:
            self._section_titles.append(label)

    def _apply_overline_style(self, label: QLabel) -> None:
        palette = UnifiedStyles.palette()
        label.setStyleSheet(
            f"""
            color: {palette.text_muted};
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        """
        )
        if label not in self._overline_labels:
            self._overline_labels.append(label)

    def _apply_caption_style(self, label: QLabel) -> None:
        palette = UnifiedStyles.palette()
        label.setStyleSheet(f"color: {palette.text_secondary}; font-size: 10px;")
        if label not in self._caption_labels:
            self._caption_labels.append(label)

    def _apply_status_style(self, label: QLabel) -> None:
        palette = UnifiedStyles.palette()
        label.setStyleSheet(f"color: {palette.primary_alt}; font-size: 12px;")
        if label not in self._status_labels:
            self._status_labels.append(label)

    def _apply_text_panel_style(self, panel: QTextEdit) -> None:
        palette = UnifiedStyles.palette()
        panel.setStyleSheet(
            f"""
            QTextEdit {{
                background-color: {palette.surface};
                border: 1px solid {palette.outline_variant};
                border-radius: 8px;
                color: {palette.text_secondary};
                font-size: 10px;
                padding: 8px;
            }}
        """
        )
        if panel not in self._text_panels:
            self._text_panels.append(panel)

    def _apply_checkbox_style(self, checkbox: QCheckBox) -> None:
        palette = UnifiedStyles.palette()
        checkbox.setStyleSheet(
            f"""
            QCheckBox {{
                color: {palette.text_secondary};
                font-size: 10px;
                text-transform: uppercase;
                font-weight: 600;
                letter-spacing: 1px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {palette.outline_variant};
                border-radius: 3px;
                background-color: {palette.surface};
            }}
            QCheckBox::indicator:checked {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {palette.primary}, stop:1 {palette.primary_alt});
                border-color: {palette.primary};
            }}
        """
        )
        if checkbox not in self._checkboxes:
            self._checkboxes.append(checkbox)

    def _apply_color_button_style(self, button: QPushButton, color: str) -> None:
        palette = UnifiedStyles.palette()
        button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {color};
                border: 1px solid {palette.outline_variant};
                border-radius: 6px;
            }}
        """
        )
        if button not in self._color_buttons:
            self._color_buttons.append(button)

    def _apply_preview_frame_style(self) -> None:
        palette = UnifiedStyles.palette()
        self.preview_frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {palette.surface_dim};
                border: 1px solid {palette.outline_variant};
                border-radius: 12px;
            }}
        """
        )

    def _apply_info_frame_style(self, frame: QFrame) -> None:
        palette = UnifiedStyles.palette()
        frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {palette.surface};
                border: 1px solid {palette.outline_variant};
                border-radius: 8px;
                padding: 12px;
            }}
        """
        )
        if frame not in self._info_frames:
            self._info_frames.append(frame)

    def refresh_theme(self) -> None:
        """Reapply palette-driven styles when theme changes."""
        UnifiedStyles.refresh_stylesheet(self)
        for group in self._group_boxes:
            self._apply_group_style(group)

        for label in self._header_labels:
            self._apply_header_label_style(label)

        for label in self._section_titles:
            self._apply_section_title_style(label)

        for label in self._overline_labels:
            self._apply_overline_style(label)

        for label in self._caption_labels:
            self._apply_caption_style(label)

        for label in self._status_labels:
            self._apply_status_style(label)

        for panel in self._text_panels:
            self._apply_text_panel_style(panel)

        for checkbox in self._checkboxes:
            self._apply_checkbox_style(checkbox)

        for frame in self._info_frames:
            self._apply_info_frame_style(frame)

        if hasattr(self, "preview_frame"):
            self._apply_preview_frame_style()
        if hasattr(self, "text_color_btn"):
            self._apply_color_button_style(self.text_color_btn, self.text_color)
        if hasattr(self, "outline_color_btn"):
            self._apply_color_button_style(self.outline_color_btn, self.outline_color)

        for widget in self._input_widgets:
            self.apply_input_style(widget)

        for button, scheme, size in self._button_configs:
            self.apply_button_style(button, scheme, size)

    # Preview and styling methods
    def update_preview_text(self, text):
        """Update preview text"""
        self.preview_text = text or "Type content to see preview"
        self.preview_label.setText(self.preview_text)
        
    def set_preview_text(self, text):
        """Set preview text from preset buttons"""
        self.preview_text_input.setText(text)
        
    def update_font_family(self, font):
        """Update font family"""
        self.font_family = font
        self.update_preview_style()
        
    def update_font_size(self, size):
        """Update font size"""
        self.font_size = size
        self.update_preview_style()
        
    def update_text_color(self, color):
        """Update text color"""
        self.text_color = color
        self._apply_color_button_style(self.text_color_btn, color)
        self.update_preview_style()
        
    def update_outline_color(self, color):
        """Update outline color"""
        self.outline_color = color
        self._apply_color_button_style(self.outline_color_btn, color)
        self.update_preview_style()
        
    def update_outline_width(self, width):
        """Update outline width"""
        self.outline_width = float(width)
        self.update_preview_style()
        
    def update_letter_spacing(self, spacing):
        """Update letter spacing"""
        self.letter_spacing = float(spacing)
        self.update_preview_style()
        
    def update_margin_bottom(self, margin):
        """Update subtitle margin from bottom"""
        self.margin_bottom = int(margin)
        
    def update_alignment(self, index):
        """Update subtitle alignment"""
        # 0=Left, 1=Center, 2=Right -> ASS alignment values 1, 2, 3
        self.alignment = index + 1
        
    def update_preview_style(self):
        """Update preview label style"""
        # Build text shadow for outline effect
        shadow_parts = []
        if self.outline_width > 0:
            offsets = [-self.outline_width, 0, self.outline_width]
            for x in offsets:
                for y in offsets:
                    if x == 0 and y == 0:
                        continue
                    shadow_parts.append(f"{x}px {y}px 0px {self.outline_color}")
        
        text_shadow = ", ".join(shadow_parts) if shadow_parts else "none"
        
        style = f"""
            QLabel {{
                font-family: {self.font_family};
                font-size: {self.font_size}px;
                color: {self.text_color};
                text-align: center;
                line-height: 1.2;
                letter-spacing: {self.letter_spacing}px;
            }}
        """
        
        self.preview_label.setStyleSheet(style)
        
    def choose_text_color(self):
        """Open color dialog for text color"""
        color = QColorDialog.getColor(QColor(self.text_color), self)
        if color.isValid():
            self.text_color = color.name()
            self.text_color_input.setText(self.text_color)
            self.update_text_color(self.text_color)
            
    def choose_outline_color(self):
        """Open color dialog for outline color"""
        color = QColorDialog.getColor(QColor(self.outline_color), self)
        if color.isValid():
            self.outline_color = color.name()
            self.outline_color_input.setText(self.outline_color)
            self.update_outline_color(self.outline_color)
    
    # Event handlers
    def browse_audio_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Audio Directory")
        if directory:
            self.audio_directory.setText(directory)
            
    def browse_image_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Image Directory")
        if directory:
            self.image_directory.setText(directory)
            
    def browse_subtitle_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Subtitle Directory")
        if directory:
            self.subtitle_directory.setText(directory)
            
    def browse_output_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_directory.setText(directory)
    
    def browse_music_directory(self):
        """Browse for background music directory"""
        directory = QFileDialog.getExistingDirectory(self, "Select Background Music Directory")
        if directory:
            self.music_directory.setText(directory)
    
    def start_individual_render(self):
        """Start individual video render (1 audio + 1 image + 1 subtitle = 1 video)"""
        inputs = self._collect_render_inputs()
        if not inputs:
            return

        audio_dir, image_dir, subtitle_dir, output_dir = inputs
        options = self._collect_render_options()

        self._active_mode = "individual"
        self._last_output_dir = Path(output_dir)
        self.render_status.setText("Đang tạo các video cho từng cảnh…")
        self.render_results.clear()
        self.render_results.hide()
        self.render_individual_btn.setEnabled(False)
        self.render_complete_btn.setEnabled(False)

        self._open_progress_dialog("Rendering individual clips…")

        worker = RenderWorker(
            audio_directory=audio_dir,
            image_directory=image_dir,
            output_directory=output_dir,
            subtitle_directory=subtitle_dir,
            options=options,
            mode="individual",
            create_individual=True,
            create_combined=False,
        )
        worker.progress.connect(self._handle_render_progress, Qt.QueuedConnection)
        worker.finished.connect(self._handle_render_finished, Qt.QueuedConnection)
        worker.error.connect(self._handle_render_error, Qt.QueuedConnection)
        self._start_thread(worker)

    def start_complete_render(self):
        """Start complete video render (create individual videos then concatenate them)"""
        inputs = self._collect_render_inputs()
        if not inputs:
            return

        audio_dir, image_dir, subtitle_dir, output_dir = inputs
        options = self._collect_render_options()

        out_base = Path(output_dir).name or "output"
        suggestion = f"{out_base}_final.mp4"

        filename = self._prompt_combined_filename(suggestion)
        if not filename:
            return
        if not filename.lower().endswith(".mp4"):
            filename += ".mp4"
        options.combined_filename = filename

        self._active_mode = "combined"
        self._last_output_dir = Path(output_dir)
        self.render_status.setText("Đang dựng video hoàn chỉnh…")
        self.render_results.clear()
        self.render_results.hide()
        self.render_individual_btn.setEnabled(False)
        self.render_complete_btn.setEnabled(False)

        self._open_progress_dialog("Rendering complete video…")

        worker = RenderWorker(
            audio_directory=audio_dir,
            image_directory=image_dir,
            output_directory=output_dir,
            subtitle_directory=subtitle_dir,
            options=options,
            mode="combined",
            create_individual=False,
            create_combined=True,
        )
        worker.progress.connect(self._handle_render_progress, Qt.QueuedConnection)
        worker.finished.connect(self._handle_render_finished, Qt.QueuedConnection)
        worker.error.connect(self._handle_render_error, Qt.QueuedConnection)
        self._start_thread(worker)
class ProgressDialog(QDialog):
    """Simple modal dialog showing rendering progress."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Rendering")
        self.setModal(True)
        self.setFixedSize(360, 160)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.message_label = QLabel("Preparing…")
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button, alignment=Qt.AlignRight)

        self._cancel_requested = False

    def update_status(self, message: str, ratio: float) -> None:
        if message:
            self.message_label.setText(message)
        percent = max(0, min(int(ratio * 100), 100))
        self.progress_bar.setValue(percent)

    def cancel_requested(self) -> bool:
        return self._cancel_requested

    def reject(self) -> None:  # pragma: no cover - GUI interaction
        self._cancel_requested = True
        super().reject()


class CompletionDialog(QDialog):
    """Dialog presented after render completes."""

    def __init__(self, message: str, output_dir: Path, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Render Completed")
        self.setModal(True)
        self.setFixedSize(380, 160)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        label = QLabel(message)
        label.setWordWrap(True)
        layout.addWidget(label)
        
        self.open_button = QPushButton("Open Folder")
        self.open_button.clicked.connect(lambda: self._open_dir(output_dir))
        layout.addWidget(self.open_button, alignment=Qt.AlignRight)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button, alignment=Qt.AlignRight)

    def _open_dir(self, directory: Path) -> None:
        if directory.exists():
            subprocess.Popen(["open", str(directory)])
