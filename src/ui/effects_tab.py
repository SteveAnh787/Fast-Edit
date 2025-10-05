"""
Effects Tab - Video composition với visual effects và transitions
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox, QCheckBox,
    QTextEdit, QProgressBar, QFileDialog, QMessageBox, QScrollArea,
    QColorDialog, QSlider, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QPalette

from src.core.video_composer import VideoComposer

class EffectsTab(QWidget):
    """Tab ghép & render video với visual effects và transitions"""
    
    def __init__(self):
        super().__init__()
        self.video_composer = VideoComposer()
        
        # Subtitle styling state
        self.font_family = "Arial"
        self.font_size = 48
        self.text_color = "#FFFFFF"
        self.outline_color = "#000000"
        self.outline_width = 2.0
        self.letter_spacing = 0.0
        self.preview_text = "Type content to see preview"
        
        self.init_ui()
        
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
        header.setFont(QFont("Arial", 11, QFont.Bold))  # Use macOS system font
        header.setStyleSheet("""
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 2px;
            font-weight: 600;
            margin-bottom: 12px;
        """)
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
        self.apply_button_style(self.render_individual_btn, "gradient")
        
        # Button 2: Complete video
        self.render_complete_btn = QPushButton("Create Complete Video")
        self.render_complete_btn.clicked.connect(self.start_complete_render)
        self.apply_button_style(self.render_complete_btn, "emerald")
        
        render_buttons_layout.addWidget(self.render_individual_btn)
        render_buttons_layout.addWidget(self.render_complete_btn)
        
        layout.addLayout(render_buttons_layout)
        
        # Status and results
        self.render_status = QLabel("")
        self.render_status.setStyleSheet("color: #10b981; font-size: 12px;")
        layout.addWidget(self.render_status)
        
        self.render_results = QTextEdit()
        self.render_results.setMaximumHeight(200)
        self.render_results.setStyleSheet("""
            QTextEdit {
                background-color: rgba(30, 41, 59, 0.7);
                border: 1px solid #334155;
                border-radius: 8px;
                color: #94a3b8;
                font-size: 10px;
                padding: 8px;
            }
        """)
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
        image_effects_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #334155;
                border-radius: 16px;
                background-color: rgba(30, 41, 59, 0.6);
                padding-top: 20px;
                margin-top: 12px;
            }
        """)
        
        image_layout = QVBoxLayout(image_effects_group)
        image_layout.setSpacing(16)
        
        # Header
        image_title = QLabel("Image Animations")
        image_title.setFont(QFont("Arial", 14, QFont.Bold))
        image_title.setStyleSheet("color: #e2e8f0; margin-bottom: 8px;")
        image_layout.addWidget(image_title)
        
        # Animation type
        animation_label = QLabel("ANIMATION TYPE")
        animation_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;")
        
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
        self.animation_type.setStyleSheet("""
            QComboBox {
                background-color: #1e293b;
                border: 1px solid #475569;
                border-radius: 8px;
                padding: 8px 12px;
                color: #e2e8f0;
                font-size: 12px;
            }
        """)
        
        image_layout.addWidget(animation_label)
        image_layout.addWidget(self.animation_type)
        
        # Animation settings
        settings_grid = QGridLayout()
        settings_grid.setSpacing(12)
        
        # Duration per image
        duration_label = QLabel("DURATION (SEC)")
        duration_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; text-transform: uppercase;")
        self.image_duration = QSpinBox()
        self.image_duration.setRange(1, 30)
        self.image_duration.setValue(5)
        self.image_duration.setStyleSheet("""
            QSpinBox {
                background-color: #1e293b;
                border: 1px solid #475569;
                border-radius: 8px;
                padding: 8px 12px;
                color: #e2e8f0;
                font-size: 12px;
            }
        """)
        
        # Animation intensity
        intensity_label = QLabel("INTENSITY")
        intensity_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; text-transform: uppercase;")
        self.animation_intensity = QComboBox()
        self.animation_intensity.addItems(["Subtle", "Medium", "Strong"])
        self.animation_intensity.setCurrentIndex(1)  # Medium default
        self.animation_intensity.setStyleSheet("""
            QComboBox {
                background-color: #1e293b;
                border: 1px solid #475569;
                border-radius: 8px;
                padding: 8px 12px;
                color: #e2e8f0;
                font-size: 12px;
            }
        """)
        
        settings_grid.addWidget(duration_label, 0, 0)
        settings_grid.addWidget(self.image_duration, 1, 0)
        settings_grid.addWidget(intensity_label, 0, 1)
        settings_grid.addWidget(self.animation_intensity, 1, 1)
        
        image_layout.addLayout(settings_grid)
        
        # Right Panel - Transition Effects
        transition_effects_group = QGroupBox()
        transition_effects_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #334155;
                border-radius: 16px;
                background-color: rgba(30, 41, 59, 0.6);
                padding-top: 20px;
                margin-top: 12px;
            }
        """)
        
        transition_layout = QVBoxLayout(transition_effects_group)
        transition_layout.setSpacing(16)
        
        # Header
        transition_title = QLabel("Transition Effects")
        transition_title.setFont(QFont("Arial", 14, QFont.Bold))
        transition_title.setStyleSheet("color: #e2e8f0; margin-bottom: 8px;")
        transition_layout.addWidget(transition_title)
        
        # Transition type
        trans_type_label = QLabel("TRANSITION TYPE")
        trans_type_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;")
        
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
        self.transition_type.setStyleSheet("""
            QComboBox {
                background-color: #1e293b;
                border: 1px solid #475569;
                border-radius: 8px;
                padding: 8px 12px;
                color: #e2e8f0;
                font-size: 12px;
            }
        """)
        
        transition_layout.addWidget(trans_type_label)
        transition_layout.addWidget(self.transition_type)
        
        # Transition settings
        trans_settings_grid = QGridLayout()
        trans_settings_grid.setSpacing(12)
        
        # Transition duration
        trans_duration_label = QLabel("DURATION (SEC)")
        trans_duration_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; text-transform: uppercase;")
        self.transition_duration = QSpinBox()
        self.transition_duration.setRange(1, 10)
        self.transition_duration.setValue(2)
        self.transition_duration.setStyleSheet("""
            QSpinBox {
                background-color: #1e293b;
                border: 1px solid #475569;
                border-radius: 8px;
                padding: 8px 12px;
                color: #e2e8f0;
                font-size: 12px;
            }
        """)
        
        # Apply to all checkbox
        self.apply_to_all = QCheckBox("Apply to All Images")
        self.apply_to_all.setChecked(True)
        self.apply_to_all.setStyleSheet("""
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
                background-color: #10b981;
                border-color: #059669;
            }
        """)
        
        trans_settings_grid.addWidget(trans_duration_label, 0, 0)
        trans_settings_grid.addWidget(self.transition_duration, 1, 0)
        trans_settings_grid.addWidget(self.apply_to_all, 1, 1)
        
        transition_layout.addLayout(trans_settings_grid)
        
        # Preview button
        preview_btn = QPushButton("Preview Effects")
        preview_btn.clicked.connect(self.preview_effects)
        self.apply_button_style(preview_btn, "indigo")
        transition_layout.addWidget(preview_btn)
        
        # Add to main layout
        main_layout.addWidget(image_effects_group)
        main_layout.addWidget(transition_effects_group)
        
        return container
        
    def create_input_directories_widget(self):
        """Create input directories widget"""
        group = QGroupBox()
        group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #334155;
                border-radius: 16px;
                background-color: rgba(30, 41, 59, 0.6);
                padding-top: 20px;
                margin-top: 12px;
            }
        """)
        
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
        group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #334155;
                border-radius: 16px;
                background-color: rgba(30, 41, 59, 0.6);
                padding-top: 20px;
                margin-top: 12px;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(16)
        
        # Frame rate
        frame_rate_label = QLabel("FRAME RATE")
        frame_rate_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;")
        self.frame_rate = QLineEdit()
        self.frame_rate.setPlaceholderText("30")
        self.frame_rate.setText("30")
        self.apply_input_style(self.frame_rate)
        
        layout.addWidget(frame_rate_label)
        layout.addWidget(self.frame_rate)
        
        # Video codec
        codec_label = QLabel("VIDEO CODEC")
        codec_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;")
        self.video_codec = QComboBox()
        self.video_codec.addItems([
            "H.264 (VideoToolbox)",
            "HEVC H.265 (VideoToolbox)"
        ])
        self.video_codec.setStyleSheet("""
            QComboBox {
                background-color: #1e293b;
                border: 1px solid #475569;
                border-radius: 8px;
                padding: 8px 12px;
                color: #e2e8f0;
                font-size: 12px;
            }
        """)
        
        layout.addWidget(codec_label)
        layout.addWidget(self.video_codec)
        
        # Audio bitrate
        bitrate_label = QLabel("AUDIO BITRATE")
        bitrate_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;")
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
        controls_title.setFont(QFont("Arial", 14, QFont.Bold))
        controls_title.setStyleSheet("color: #e2e8f0; margin-bottom: 8px;")
        controls_layout.addWidget(controls_title)
        
        # Font controls in grid
        font_grid = QGridLayout()
        font_grid.setSpacing(12)
        
        # Font family
        font_label = QLabel("FONT")
        font_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; text-transform: uppercase;")
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Arial", "Helvetica", "Montserrat", "Roboto", "Open Sans", "Arial Black"])
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
        preview_title.setFont(QFont("Arial", 14, QFont.Bold))
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
        label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;")
        
        input_layout = QHBoxLayout()
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        
        browse_btn = QPushButton("Browse")
        self.apply_button_style(browse_btn, "indigo")
        
        self.apply_input_style(line_edit)
        
        input_layout.addWidget(line_edit)
        input_layout.addWidget(browse_btn)
        
        layout.addWidget(label)
        layout.addLayout(input_layout)
        
        return (layout, line_edit, browse_btn)
        
    def apply_input_style(self, widget):
        """Apply consistent input styling"""
        widget.setStyleSheet("""
            QLineEdit {
                background-color: #1e293b;
                border: 1px solid #475569;
                border-radius: 8px;
                padding: 8px 12px;
                color: #e2e8f0;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #4f46e5;
                outline: none;
            }
        """)
        
    def apply_button_style(self, button, color_scheme="indigo"):
        """Apply button styling"""
        if color_scheme == "indigo":
            style = """
                QPushButton {
                    background-color: rgba(79, 70, 229, 0.2);
                    border: 1px solid rgba(79, 70, 229, 0.6);
                    border-radius: 8px;
                    color: #a5b4fc;
                    padding: 8px 12px;
                    font-size: 10px;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    min-height: 32px;
                }
                QPushButton:hover {
                    background-color: rgba(79, 70, 229, 0.3);
                    border-color: #6366f1;
                }
                QPushButton:pressed {
                    background-color: rgba(79, 70, 229, 0.4);
                }
            """
        elif color_scheme == "emerald":
            style = """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 #10b981, stop:1 #059669);
                    border: none;
                    border-radius: 10px;
                    color: white;
                    padding: 14px 28px;
                    font-size: 13px;
                    font-weight: 700;
                    min-height: 44px;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 #059669, stop:1 #047857);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 #047857, stop:1 #065f46);
                }
                QPushButton:disabled {
                    background: #6b7280;
                    color: #9ca3af;
                }
            """
        else:  # gradient
            style = """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 #4f46e5, stop:1 #06b6d4);
                    border: none;
                    border-radius: 10px;
                    color: white;
                    padding: 14px 28px;
                    font-size: 13px;
                    font-weight: 700;
                    min-height: 44px;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 #4338ca, stop:1 #0891b2);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 #3730a3, stop:1 #0e7490);
                }
                QPushButton:disabled {
                    background: #6b7280;
                    color: #9ca3af;
                }
            """
        
        button.setStyleSheet(style)
    
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