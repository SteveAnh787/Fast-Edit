"""
Effects Tab - Video composition với visual effects và transitions
"""

from typing import List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
    QTextEdit, QProgressBar, QFileDialog, QMessageBox, QScrollArea,
    QColorDialog, QSlider, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QPalette

from src.core.video_composer import VideoComposer
from src.ui.unified_styles import UnifiedStyles

class EffectsTab(QWidget):
    """Tab ghép & render video với visual effects và transitions"""
    
    def __init__(self):
        super().__init__()
        self.setObjectName("EffectsTabRoot")
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

        self.init_ui()
        self.refresh_theme()
        
    def init_ui(self):
        """Initialize effects tab UI"""
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
        header = QLabel("VISUAL EFFECTS & COMPOSITION")
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
        
        # Visual Effects section - NEW
        effects_section = self.create_visual_effects_section()
        layout.addWidget(effects_section)
        
        # Subtitle styling section
        subtitle_section = self.create_subtitle_styling_section()
        layout.addWidget(subtitle_section)
        
        # Two render buttons
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
        
    def create_visual_effects_section(self):
        """Create visual effects section - NEW"""
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
        
        # Left Panel - Image Effects
        image_effects_group = QGroupBox()
        self._apply_group_style(image_effects_group)
        
        image_layout = QVBoxLayout(image_effects_group)
        image_layout.setSpacing(16)
        
        # Header
        image_title = QLabel("Image Animations")
        image_title.setFont(QFont("Space Grotesk", 14, QFont.Bold))
        self._apply_section_title_style(image_title)
        image_layout.addWidget(image_title)
        
        # Animation type
        animation_label = QLabel("ANIMATION TYPE")
        self._apply_overline_style(animation_label)
        
        self.animation_type = QComboBox()
        self.animation_type.addItems([
            "None",
            "Zoom In", 
            "Zoom Out",
            "Ken Burns (Zoom + Pan)",
            "Pan Left",
            "Pan Right", 
            "Pan Up",
            "Pan Down",
            "Fade In",
            "Fade Out"
        ])
        self.apply_input_style(self.animation_type)
        
        image_layout.addWidget(animation_label)
        image_layout.addWidget(self.animation_type)
        
        # Animation settings
        settings_grid = QGridLayout()
        settings_grid.setSpacing(12)
        
        # Duration per image
        duration_label = QLabel("DURATION (SEC)")
        self._apply_overline_style(duration_label)
        self.image_duration = QSpinBox()
        self.image_duration.setRange(1, 30)
        self.image_duration.setValue(5)
        self.apply_input_style(self.image_duration)
        
        # Animation intensity
        intensity_label = QLabel("INTENSITY")
        self._apply_overline_style(intensity_label)
        self.animation_intensity = QComboBox()
        self.animation_intensity.addItems(["Subtle", "Medium", "Strong"])
        self.animation_intensity.setCurrentIndex(1)  # Medium default
        self.apply_input_style(self.animation_intensity)
        
        settings_grid.addWidget(duration_label, 0, 0)
        settings_grid.addWidget(self.image_duration, 1, 0)
        settings_grid.addWidget(intensity_label, 0, 1)
        settings_grid.addWidget(self.animation_intensity, 1, 1)
        
        image_layout.addLayout(settings_grid)
        
        # Right Panel - Transition Effects
        transition_effects_group = QGroupBox()
        self._apply_group_style(transition_effects_group)
        
        transition_layout = QVBoxLayout(transition_effects_group)
        transition_layout.setSpacing(16)
        
        # Header
        transition_title = QLabel("Transition Effects")
        transition_title.setFont(QFont("Space Grotesk", 14, QFont.Bold))
        self._apply_section_title_style(transition_title)
        transition_layout.addWidget(transition_title)
        
        # Transition type
        trans_type_label = QLabel("TRANSITION TYPE")
        self._apply_overline_style(trans_type_label)
        
        self.transition_type = QComboBox()
        self.transition_type.addItems([
            "None",
            "Fade",
            "Dissolve", 
            "Crossfade",
            "Wipe Left",
            "Wipe Right",
            "Wipe Up", 
            "Wipe Down",
            "Slide Left",
            "Slide Right",
            "Blur Transition"
        ])
        self.apply_input_style(self.transition_type)
        
        transition_layout.addWidget(trans_type_label)
        transition_layout.addWidget(self.transition_type)
        
        # Transition settings
        trans_settings_grid = QGridLayout()
        trans_settings_grid.setSpacing(12)
        
        # Transition duration
        trans_duration_label = QLabel("DURATION (SEC)")
        self._apply_overline_style(trans_duration_label)
        self.transition_duration = QSpinBox()
        self.transition_duration.setRange(1, 10)
        self.transition_duration.setValue(2)
        self.apply_input_style(self.transition_duration)

        # Apply to all checkbox
        self.apply_to_all = QCheckBox("Apply to All Images")
        self.apply_to_all.setChecked(True)
        self._apply_checkbox_style(self.apply_to_all)
        
        trans_settings_grid.addWidget(trans_duration_label, 0, 0)
        trans_settings_grid.addWidget(self.transition_duration, 1, 0)
        trans_settings_grid.addWidget(self.apply_to_all, 1, 1)
        
        transition_layout.addLayout(trans_settings_grid)
        
        # Preview button
        preview_btn = QPushButton("Preview Effects")
        preview_btn.clicked.connect(self.preview_effects)
        self.apply_button_style(preview_btn, "secondary")
        transition_layout.addWidget(preview_btn)
        
        # Add to main layout
        main_layout.addWidget(image_effects_group)
        main_layout.addWidget(transition_effects_group)
        
        return container
        
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

        # Output directory
        output_layout = self.create_directory_input("OUTPUT DIRECTORY", "Path to save videos (.mp4)")
        self.output_directory = output_layout[1]
        output_browse_btn = output_layout[2]
        output_browse_btn.clicked.connect(self.browse_output_directory)
        layout.addLayout(output_layout[0])
        
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
        
        # Burn subtitles checkbox
        self.burn_subtitles = QCheckBox("Burn subtitles directly into video")
        self.burn_subtitles.setStyleSheet("""
            QCheckBox {
                color: #94a3b8;
                font-size: 10px;
                text-transform: uppercase;
                font-weight: 600;
                letter-spacing: 1px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #475569;
                border-radius: 3px;
                background-color: #1e293b;
            }
            QCheckBox::indicator:checked {
                background-color: #4f46e5;
                border-color: #6366f1;
            }
        """)
        layout.addWidget(self.burn_subtitles)
        
        return group
        
    def create_subtitle_styling_section(self):
        """Create subtitle styling section"""
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
        controls_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #334155;
                border-radius: 16px;
                background-color: rgba(30, 41, 59, 0.6);
                padding-top: 20px;
                margin-top: 12px;
            }
        """)
        
        controls_layout = QVBoxLayout(controls_group)
        controls_layout.setSpacing(16)
        
        # Header
        controls_title = QLabel("Subtitle Styling (Burn-in)")
        controls_title.setFont(QFont("Space Grotesk", 14, QFont.Bold))
        controls_title.setStyleSheet("color: #e2e8f0; margin-bottom: 8px;")
        controls_layout.addWidget(controls_title)
        
        # Font controls in grid
        font_grid = QGridLayout()
        font_grid.setSpacing(12)
        
        # Font family
        font_label = QLabel("FONT")
        font_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; text-transform: uppercase;")
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
        self.font_combo.setStyleSheet("""
            QComboBox {
                background-color: #1e293b;
                border: 1px solid #475569;
                border-radius: 8px;
                padding: 8px 12px;
                color: #e2e8f0;
                font-size: 12px;
            }
        """)
        
        # Font size
        size_label = QLabel("SIZE")
        size_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; text-transform: uppercase;")
        self.font_size_input = QSpinBox()
        self.font_size_input.setRange(12, 120)
        self.font_size_input.setValue(48)
        self.font_size_input.valueChanged.connect(self.update_font_size)
        self.font_size_input.setStyleSheet("""
            QSpinBox {
                background-color: #1e293b;
                border: 1px solid #475569;
                border-radius: 8px;
                padding: 8px 12px;
                color: #e2e8f0;
                font-size: 12px;
            }
        """)
        
        font_grid.addWidget(font_label, 0, 0)
        font_grid.addWidget(self.font_combo, 1, 0)
        font_grid.addWidget(size_label, 0, 1)
        font_grid.addWidget(self.font_size_input, 1, 1)
        
        controls_layout.addLayout(font_grid)
        
        # Right Panel - Preview
        preview_group = QGroupBox()
        preview_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #334155;
                border-radius: 16px;
                background-color: rgba(30, 41, 59, 0.6);
                padding-top: 20px;
                margin-top: 12px;
            }
        """)
        
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setSpacing(16)
        
        # Preview header
        preview_title = QLabel("Preview")
        preview_title.setFont(QFont("Space Grotesk", 14, QFont.Bold))
        preview_title.setStyleSheet("color: #e2e8f0; margin-bottom: 8px;")
        preview_layout.addWidget(preview_title)
        
        # Preview area
        self.preview_frame = QFrame()
        self.preview_frame.setMinimumHeight(200)
        self.preview_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 0.95);
                border: 1px solid #475569;
                border-radius: 12px;
            }
        """)
        
        preview_frame_layout = QVBoxLayout(self.preview_frame)
        preview_frame_layout.setAlignment(Qt.AlignCenter)
        
        self.preview_label = QLabel(self.preview_text)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setWordWrap(True)
        self.update_preview_style()
        
        preview_frame_layout.addWidget(self.preview_label)
        preview_layout.addWidget(self.preview_frame)
        
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

    def apply_button_style(self, button, color_scheme="primary", size="medium"):
        scheme_map = {
            "indigo": "secondary",
            "emerald": "primary",
            "gradient": "primary",
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

    
    # Subtitle styling methods
    def update_font_family(self, font):
        """Update font family"""
        self.font_family = font
        self.update_preview_style()
        
    def update_font_size(self, size):
        """Update font size"""
        self.font_size = size
        self.update_preview_style()
        
    def update_preview_style(self):
        """Update preview label style"""
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
    
    def start_individual_render(self):
        """Start individual video render with effects"""
        if not self.audio_directory.text() or not self.image_directory.text() or not self.output_directory.text():
            QMessageBox.warning(self, "Error", "Please select audio, image and output directories.")
            return
            
        animation = self.animation_type.currentText()
        transition = self.transition_type.currentText()
        
        self.render_status.setText(f"Creating individual videos with {animation} + {transition}...")
        self.render_individual_btn.setEnabled(False)
        self.render_complete_btn.setEnabled(False)
        
        # Simulate processing
        QTimer.singleShot(4000, lambda: self.finish_individual_render())
        
    def start_complete_render(self):
        """Start complete video render with effects"""
        if not self.audio_directory.text() or not self.image_directory.text() or not self.output_directory.text():
            QMessageBox.warning(self, "Error", "Please select audio, image and output directories.")
            return
            
        animation = self.animation_type.currentText()
        transition = self.transition_type.currentText()
        
        self.render_status.setText(f"Step 1/2: Creating individual videos with {animation}...")
        self.render_individual_btn.setEnabled(False)
        self.render_complete_btn.setEnabled(False)
        
        # Simulate step 1: Create individual videos
        QTimer.singleShot(3000, lambda: self.complete_render_step2())
        
    def complete_render_step2(self):
        """Step 2: Concatenate individual videos with transitions"""
        transition = self.transition_type.currentText()
        self.render_status.setText(f"Step 2/2: Adding {transition} transitions and concatenating...")
        
        # Simulate step 2: Concatenate videos
        QTimer.singleShot(4000, lambda: self.finish_complete_render())
        
    def finish_individual_render(self):
        """Finish individual video render with effects"""
        animation = self.animation_type.currentText()
        transition = self.transition_type.currentText()
        
        self.render_status.setText("Created 5 videos with visual effects!")
        self.render_individual_btn.setEnabled(True)
        self.render_complete_btn.setEnabled(True)
        
        # Show results
        results_text = f"""✅ VIDEOS WITH EFFECTS CREATED:
🎬 Animation: {animation} ({self.image_duration.value()}s duration)
🔄 Transition: {transition} ({self.transition_duration.value()}s duration)
📁 output_001.mp4 • 15s with effects
📁 output_002.mp4 • 15s with effects  
📁 output_003.mp4 • 15s with effects
📁 output_004.mp4 • 15s with effects
📁 output_005.mp4 • 15s with effects

Total: 5 videos • Each with visual effects + subtitles"""
        
        self.render_results.setText(results_text)
        self.render_results.show()
        
    def finish_complete_render(self):
        """Finish complete video render with effects"""
        animation = self.animation_type.currentText()
        transition = self.transition_type.currentText()
        
        self.render_status.setText("Complete video with effects created!")
        self.render_individual_btn.setEnabled(True)
        self.render_complete_btn.setEnabled(True)
        
        # Show results
        results_text = f"""✅ COMPLETE VIDEO WITH EFFECTS:
🎬 Step 1: Created 5 videos with {animation} animation
   • Each image: {self.image_duration.value()}s with smooth effects

🔗 Step 2: Added {transition} transitions ({self.transition_duration.value()}s each)
   • complete_video_effects.mp4 • 85s total
   • Seamless transitions between all segments
   
✅ Professional video with cinematic effects completed!"""
        
        self.render_results.setText(results_text)
        self.render_results.show()
        
    def preview_effects(self):
        """Preview visual effects"""
        animation = self.animation_type.currentText()
        transition = self.transition_type.currentText()
        
        self.render_status.setText(f"Previewing: {animation} + {transition} transition...")
        
        # Simulate preview
        QTimer.singleShot(2000, lambda: self.finish_preview())
        
    def finish_preview(self):
        """Finish preview"""
        self.render_status.setText("Preview completed! Ready for rendering.")
        
        preview_text = """✅ EFFECTS PREVIEW:
🎬 Animation: Zoom In (Medium intensity, 5s per image)
🔄 Transition: Fade (2s duration)
📊 Applied to all images
⚡ Estimated render time: 2-3 minutes

Ready to create videos with effects!"""
        
        self.render_results.setText(preview_text)
        self.render_results.show()
