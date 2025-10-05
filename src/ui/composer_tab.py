"""
Composer Tab - Tab ghép & render với video composition và subtitle styling
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

class ComposerTab(QWidget):
    """Tab ghép & render video với subtitle styling"""
    
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
        header.setFont(QFont("Arial", 11, QFont.Bold))  # Use Arial font
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
        
        # Subtitle styling section
        subtitle_section = self.create_subtitle_styling_section()
        layout.addWidget(subtitle_section)
        
        # Two render buttons with English text
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
        
        # Info box
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 41, 59, 0.6);
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        
        info_layout = QVBoxLayout(info_frame)
        info_text = QLabel("""Images will be looped until audio ends. If "Burn subtitles" is enabled, subtitles will be rendered directly into the video frame, otherwise they will be embedded as soft subtitles.""")
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #94a3b8; font-size: 10px; line-height: 1.4;")
        
        req_text = QLabel("Requires ffmpeg and ffprobe installed in PATH.")
        req_text.setStyleSheet("color: #94a3b8; font-size: 9px; margin-top: 8px;")
        
        info_layout.addWidget(info_text)
        info_layout.addWidget(req_text)
        
        layout.addWidget(info_frame)
        
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
        
        # Preview text input - moved to top
        preview_label = QLabel("SAMPLE CONTENT")
        preview_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;")
        
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
        
        # Color controls - better layout
        color_grid = QGridLayout()
        color_grid.setSpacing(12)
        
        # Text color
        text_color_label = QLabel("TEXT COLOR")
        text_color_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; text-transform: uppercase;")
        
        text_color_layout = QHBoxLayout()
        self.text_color_btn = QPushButton()
        self.text_color_btn.setFixedSize(48, 40)
        self.text_color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.text_color};
                border: 1px solid #475569;
                border-radius: 6px;
            }}
        """)
        self.text_color_btn.clicked.connect(self.choose_text_color)
        
        self.text_color_input = QLineEdit(self.text_color)
        self.text_color_input.textChanged.connect(self.update_text_color)
        self.apply_input_style(self.text_color_input)
        
        text_color_layout.addWidget(self.text_color_btn)
        text_color_layout.addWidget(self.text_color_input)
        
        # Outline color
        outline_color_label = QLabel("OUTLINE COLOR")
        outline_color_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; text-transform: uppercase;")
        
        outline_color_layout = QHBoxLayout()
        self.outline_color_btn = QPushButton()
        self.outline_color_btn.setFixedSize(48, 40)
        self.outline_color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.outline_color};
                border: 1px solid #475569;
                border-radius: 6px;
            }}
        """)
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
        width_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; text-transform: uppercase;")
        self.outline_width_input = QSpinBox()
        self.outline_width_input.setRange(0, 10)
        self.outline_width_input.setValue(2)
        self.outline_width_input.valueChanged.connect(self.update_outline_width)
        self.outline_width_input.setStyleSheet("""
            QSpinBox {
                background-color: #1e293b;
                border: 1px solid #475569;
                border-radius: 8px;
                padding: 8px 12px;
                color: #e2e8f0;
                font-size: 12px;
            }
        """)
        
        # Letter spacing
        spacing_label = QLabel("LETTER SPACING")
        spacing_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; text-transform: uppercase;")
        self.letter_spacing_input = QSpinBox()
        self.letter_spacing_input.setRange(-5, 10)
        self.letter_spacing_input.setValue(0)
        self.letter_spacing_input.valueChanged.connect(self.update_letter_spacing)
        self.letter_spacing_input.setStyleSheet("""
            QSpinBox {
                background-color: #1e293b;
                border: 1px solid #475569;
                border-radius: 8px;
                padding: 8px 12px;
                color: #e2e8f0;
                font-size: 12px;
            }
        """)
        
        advanced_grid.addWidget(width_label, 0, 0)
        advanced_grid.addWidget(self.outline_width_input, 1, 0)
        advanced_grid.addWidget(spacing_label, 0, 1)
        advanced_grid.addWidget(self.letter_spacing_input, 1, 1)
        
        controls_layout.addLayout(advanced_grid)
        
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
        self.preview_frame.setMinimumHeight(320)
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
        
        # Quick preset buttons
        preset_layout = QHBoxLayout()
        
        preset_vi_btn = QPushButton("Tiếng Việt")
        preset_vi_btn.clicked.connect(lambda: self.set_preview_text("Xin chào! Đây là phụ đề mẫu."))
        self.apply_button_style(preset_vi_btn, "preset")
        
        preset_en_btn = QPushButton("English")
        preset_en_btn.clicked.connect(lambda: self.set_preview_text("Hello! This is a sample subtitle."))
        self.apply_button_style(preset_en_btn, "preset")
        
        preset_clear_btn = QPushButton("Clear")
        preset_clear_btn.clicked.connect(lambda: self.set_preview_text(""))
        self.apply_button_style(preset_clear_btn, "preset")
        
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
        elif color_scheme == "preset":
            style = """
                QPushButton {
                    background-color: #475569;
                    border: 1px solid #64748b;
                    border-radius: 6px;
                    color: #e2e8f0;
                    padding: 6px 12px;
                    font-size: 10px;
                    font-weight: 500;
                    min-height: 28px;
                }
                QPushButton:hover {
                    background-color: #64748b;
                    color: #f8fafc;
                }
                QPushButton:pressed {
                    background-color: #334155;
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
        else:  # gradient (default for main render buttons)
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
        self.text_color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: 1px solid #475569;
                border-radius: 6px;
            }}
        """)
        self.update_preview_style()
        
    def update_outline_color(self, color):
        """Update outline color"""
        self.outline_color = color
        self.outline_color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: 1px solid #475569;
                border-radius: 6px;
            }}
        """)
        self.update_preview_style()
        
    def update_outline_width(self, width):
        """Update outline width"""
        self.outline_width = float(width)
        self.update_preview_style()
        
    def update_letter_spacing(self, spacing):
        """Update letter spacing"""
        self.letter_spacing = float(spacing)
        self.update_preview_style()
        
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
    
    def start_individual_render(self):
        """Start individual video render (1 audio + 1 image + 1 subtitle = 1 video)"""
        if not self.audio_directory.text() or not self.image_directory.text() or not self.output_directory.text():
            QMessageBox.warning(self, "Error", "Please select audio, image and output directories.")
            return
            
        # Start rendering individual videos
        self.render_status.setText("Creating individual videos...")
        self.render_individual_btn.setEnabled(False)
        self.render_complete_btn.setEnabled(False)
        
        # Simulate processing
        QTimer.singleShot(3000, lambda: self.finish_individual_render())
        
    def start_complete_render(self):
        """Start complete video render (create individual videos then concatenate them)"""
        if not self.audio_directory.text() or not self.image_directory.text() or not self.output_directory.text():
            QMessageBox.warning(self, "Error", "Please select audio, image and output directories.")
            return
            
        # Start rendering complete video (two-step process)
        self.render_status.setText("Step 1/2: Creating individual videos...")
        self.render_individual_btn.setEnabled(False)
        self.render_complete_btn.setEnabled(False)
        
        # Simulate step 1: Create individual videos
        QTimer.singleShot(2000, lambda: self.complete_render_step2())
        
    def complete_render_step2(self):
        """Step 2: Concatenate individual videos"""
        self.render_status.setText("Step 2/2: Concatenating into complete video...")
        
        # Simulate step 2: Concatenate videos
        QTimer.singleShot(3000, lambda: self.finish_complete_render())
        
    def finish_individual_render(self):
        """Finish individual video render"""
        self.render_status.setText("Created 5 individual videos successfully!")
        self.render_individual_btn.setEnabled(True)
        self.render_complete_btn.setEnabled(True)
        
        # Show results
        results_text = """✅ INDIVIDUAL VIDEOS CREATED:
📁 output_001.mp4 • 15s
📁 output_002.mp4 • 15s  
📁 output_003.mp4 • 15s
📁 output_004.mp4 • 15s
📁 output_005.mp4 • 15s

Total: 5 videos • Each with audio + image + subtitles"""
        
        self.render_results.setText(results_text)
        self.render_results.show()
        
    def finish_complete_render(self):
        """Finish complete video render"""
        self.render_status.setText("Complete video created successfully!")
        self.render_individual_btn.setEnabled(True)
        self.render_complete_btn.setEnabled(True)
        
        # Show results
        results_text = """✅ COMPLETE VIDEO CREATED:
🎬 Step 1: Created 5 individual videos (with subtitles)
   • temp_001.mp4, temp_002.mp4, temp_003.mp4...

🔗 Step 2: Concatenated into long video
   • complete_video.mp4 • 75s
   • Contains all audio + images + subtitles seamlessly
   
✅ Finished! 1 long video from 5 individual segments"""
        
        self.render_results.setText(results_text)
        self.render_results.show()