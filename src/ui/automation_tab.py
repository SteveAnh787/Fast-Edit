"""
Automation Tab - Tab tự động hoá với batch rename và subtitle generation
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox, QCheckBox,
    QTextEdit, QProgressBar, QFileDialog, QMessageBox, QScrollArea
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont

from src.core.batch_rename import BatchRenamer
from src.core.subtitle_generator import SubtitleGenerator

class AutomationTab(QWidget):
    """Tab chứa các tính năng tự động hoá"""
    
    def __init__(self):
        super().__init__()
        self.batch_renamer = BatchRenamer()
        self.subtitle_generator = SubtitleGenerator()
        self.init_ui()
        
    def init_ui(self):
        """Initialize automation tab UI"""
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
        header = QLabel("PROCESS AUTOMATION")
        header.setFont(QFont("Arial", 11, QFont.Bold))  # Use macOS system font
        header.setStyleSheet("""
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 2px;
            font-weight: 600;
            margin-bottom: 12px;
        """)
        layout.addWidget(header)
        
        # Two column grid for main content
        grid_layout = QGridLayout()
        grid_layout.setSpacing(24)
        
        # Left column - Batch Rename
        rename_widget = self.create_batch_rename_widget()
        grid_layout.addWidget(rename_widget, 0, 0)
        
        # Right column - Subtitle Generation
        subtitle_widget = self.create_subtitle_generation_widget()
        grid_layout.addWidget(subtitle_widget, 0, 1)
        
        layout.addLayout(grid_layout)
        layout.addStretch()
        
    def create_batch_rename_widget(self):
        """Create batch rename widget"""
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
        
        # Header with asset type selector
        header_layout = QHBoxLayout()
        title = QLabel("Batch Rename")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setStyleSheet("color: #e2e8f0;")
        
        self.rename_asset_type = QComboBox()
        self.rename_asset_type.addItems(["Audio", "Image"])
        self.rename_asset_type.setStyleSheet("""
            QComboBox {
                background-color: #1e293b;
                border: 1px solid #475569;
                border-radius: 6px;
                padding: 4px 8px;
                color: #e2e8f0;
                font-size: 10px;
                text-transform: uppercase;
                font-weight: 600;
                letter-spacing: 1px;
            }
        """)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.rename_asset_type)
        layout.addLayout(header_layout)
        
        # Directory selection
        dir_layout = QVBoxLayout()
        dir_label = QLabel("TARGET DIRECTORY")
        dir_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;")
        
        dir_input_layout = QHBoxLayout()
        self.rename_directory = QLineEdit()
        self.rename_directory.setPlaceholderText("Directory path")
        
        dir_browse_btn = QPushButton("Browse")
        dir_browse_btn.clicked.connect(self.browse_rename_directory)
        
        self.apply_input_style(self.rename_directory)
        self.apply_button_style(dir_browse_btn, "indigo")
        
        dir_input_layout.addWidget(self.rename_directory)
        dir_input_layout.addWidget(dir_browse_btn)
        
        dir_layout.addWidget(dir_label)
        dir_layout.addLayout(dir_input_layout)
        layout.addLayout(dir_layout)
        
        # Rename options in grid
        options_grid = QGridLayout()
        options_grid.setSpacing(12)
        
        # Prefix
        prefix_label = QLabel("PREFIX")
        prefix_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; text-transform: uppercase;")
        self.rename_prefix = QLineEdit()
        self.rename_prefix.setPlaceholderText("audio")
        self.apply_input_style(self.rename_prefix)
        
        # Start index
        start_label = QLabel("START FROM")
        start_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; text-transform: uppercase;")
        self.rename_start_index = QLineEdit()
        self.rename_start_index.setPlaceholderText("1")
        self.apply_input_style(self.rename_start_index)
        
        # Pad width
        pad_label = QLabel("PAD WIDTH")
        pad_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; text-transform: uppercase;")
        self.rename_pad_width = QLineEdit()
        self.rename_pad_width.setPlaceholderText("3")
        self.apply_input_style(self.rename_pad_width)
        
        options_grid.addWidget(prefix_label, 0, 0)
        options_grid.addWidget(self.rename_prefix, 1, 0)
        options_grid.addWidget(start_label, 0, 1)
        options_grid.addWidget(self.rename_start_index, 1, 1)
        options_grid.addWidget(pad_label, 0, 2)
        options_grid.addWidget(self.rename_pad_width, 1, 2)
        
        layout.addLayout(options_grid)
        
        # Lowercase checkbox
        self.rename_lowercase = QCheckBox("Auto lowercase file extensions")
        self.rename_lowercase.setChecked(True)
        self.rename_lowercase.setStyleSheet("""
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
        layout.addWidget(self.rename_lowercase)
        
        # Rename button
        self.rename_btn = QPushButton("Rename Now")
        self.rename_btn.clicked.connect(self.start_batch_rename)
        self.apply_button_style(self.rename_btn, "gradient")
        layout.addWidget(self.rename_btn)
        
        # Status and results
        self.rename_status = QLabel("")
        self.rename_status.setStyleSheet("color: #10b981; font-size: 12px;")
        layout.addWidget(self.rename_status)
        
        self.rename_results = QTextEdit()
        self.rename_results.setMaximumHeight(120)
        self.rename_results.setStyleSheet("""
            QTextEdit {
                background-color: rgba(30, 41, 59, 0.7);
                border: 1px solid #334155;
                border-radius: 8px;
                color: #94a3b8;
                font-size: 10px;
                padding: 8px;
            }
        """)
        self.rename_results.hide()
        layout.addWidget(self.rename_results)
        
        return group
        
    def create_subtitle_generation_widget(self):
        """Create subtitle generation widget"""
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
        
        # Header
        title = QLabel("Auto Subtitle Generation")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setStyleSheet("color: #e2e8f0;")
        layout.addWidget(title)
        
        # Audio directory
        audio_layout = QVBoxLayout()
        audio_label = QLabel("AUDIO DIRECTORY")
        audio_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;")
        
        audio_input_layout = QHBoxLayout()
        self.audio_directory = QLineEdit()
        self.audio_directory.setPlaceholderText("Path to audio folder (.wav)")
        
        audio_browse_btn = QPushButton("Browse")
        audio_browse_btn.clicked.connect(self.browse_audio_directory)
        
        self.apply_input_style(self.audio_directory)
        self.apply_button_style(audio_browse_btn, "indigo")
        
        audio_input_layout.addWidget(self.audio_directory)
        audio_input_layout.addWidget(audio_browse_btn)
        
        audio_layout.addWidget(audio_label)
        audio_layout.addLayout(audio_input_layout)
        layout.addLayout(audio_layout)
        
        # Model selection
        model_layout = QVBoxLayout()
        model_label = QLabel("WHISPER MODEL")
        model_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;")
        
        self.whisper_model = QComboBox()
        self.whisper_model.addItems([
            "ggml-tiny-en - Whisper Tiny (English) · 75MB",
            "ggml-base - Whisper Base · 142MB (Recommended)",
            "ggml-small-en - Whisper Small (English) · 465MB",
            "ggml-medium - Whisper Medium · 1.5GB"
        ])
        self.whisper_model.setCurrentIndex(1)  # Base model default
        self.whisper_model.setStyleSheet("""
            QComboBox {
                background-color: #1e293b;
                border: 1px solid #475569;
                border-radius: 8px;
                padding: 8px 12px;
                color: #e2e8f0;
                font-size: 12px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
        """)
        
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.whisper_model)
        
        info_label = QLabel("Models stored locally, auto-download if not available.")
        info_label.setStyleSheet("color: #94a3b8; font-size: 10px;")
        model_layout.addWidget(info_label)
        
        layout.addLayout(model_layout)
        
        # Subtitle directory
        sub_layout = QVBoxLayout()
        sub_label = QLabel("SUBTITLE DIRECTORY")
        sub_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;")
        
        sub_input_layout = QHBoxLayout()
        self.subtitle_directory = QLineEdit()
        self.subtitle_directory.setPlaceholderText("Default: create subtitles folder in audio directory")
        
        sub_browse_btn = QPushButton("Browse")
        sub_browse_btn.clicked.connect(self.browse_subtitle_directory)
        
        self.apply_input_style(self.subtitle_directory)
        self.apply_button_style(sub_browse_btn, "indigo")
        
        sub_input_layout.addWidget(self.subtitle_directory)
        sub_input_layout.addWidget(sub_browse_btn)
        
        sub_layout.addWidget(sub_label)
        sub_layout.addLayout(sub_input_layout)
        layout.addLayout(sub_layout)
        
        # Options grid
        options_grid = QGridLayout()
        options_grid.setSpacing(12)
        
        # Language
        lang_label = QLabel("LANGUAGE")
        lang_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; text-transform: uppercase;")
        self.language = QLineEdit()
        self.language.setPlaceholderText("vi, en, ...")
        self.apply_input_style(self.language)
        
        # Threads
        threads_label = QLabel("THREADS")
        threads_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; text-transform: uppercase;")
        self.thread_count = QLineEdit()
        self.thread_count.setPlaceholderText("Auto")
        self.apply_input_style(self.thread_count)
        
        options_grid.addWidget(lang_label, 0, 0)
        options_grid.addWidget(self.language, 1, 0)
        options_grid.addWidget(threads_label, 0, 1)
        options_grid.addWidget(self.thread_count, 1, 1)
        
        layout.addLayout(options_grid)
        
        # Translate checkbox
        self.translate_to_english = QCheckBox("Translate to English")
        self.translate_to_english.setStyleSheet("""
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
        layout.addWidget(self.translate_to_english)
        
        # Generate button
        self.generate_btn = QPushButton("Generate Subtitles")
        self.generate_btn.clicked.connect(self.start_subtitle_generation)
        self.apply_button_style(self.generate_btn, "emerald")
        layout.addWidget(self.generate_btn)
        
        # Status and results
        self.subtitle_status = QLabel("")
        self.subtitle_status.setStyleSheet("color: #10b981; font-size: 12px;")
        layout.addWidget(self.subtitle_status)
        
        self.subtitle_results = QTextEdit()
        self.subtitle_results.setMaximumHeight(200)
        self.subtitle_results.setStyleSheet("""
            QTextEdit {
                background-color: rgba(30, 41, 59, 0.7);
                border: 1px solid #334155;
                border-radius: 8px;
                color: #94a3b8;
                font-size: 10px;
                padding: 8px;
            }
        """)
        self.subtitle_results.hide()
        layout.addWidget(self.subtitle_results)
        
        return group
    
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
                    padding: 12px 20px;
                    font-size: 12px;
                    font-weight: 700;
                    min-height: 40px;
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
                    padding: 12px 20px;
                    font-size: 12px;
                    font-weight: 700;
                    min-height: 40px;
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
    
    # Event handlers
    def browse_rename_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory to Rename")
        if directory:
            self.rename_directory.setText(directory)
            
    def browse_audio_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Audio Directory")
        if directory:
            self.audio_directory.setText(directory)
            if not self.subtitle_directory.text():
                self.subtitle_directory.setText(f"{directory}/subtitles")
                
    def browse_subtitle_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Subtitle Directory")
        if directory:
            self.subtitle_directory.setText(directory)
    
    def start_batch_rename(self):
        """Start batch rename operation"""
        if not self.rename_directory.text():
            QMessageBox.warning(self, "Error", "Please select a directory first.")
            return
            
        # TODO: Implement batch rename logic
        self.rename_status.setText("Renaming files...")
        self.rename_btn.setEnabled(False)
        
        # Simulate processing
        QTimer.singleShot(2000, self.finish_batch_rename)
        
    def finish_batch_rename(self):
        """Finish batch rename operation"""
        self.rename_status.setText("Processed 15 files — renamed 12")
        self.rename_btn.setEnabled(True)
        self.rename_results.setText("audio_001.wav → audio_001.wav\naudio_002.wav → audio_002.wav\n...")
        self.rename_results.show()
        
    def start_subtitle_generation(self):
        """Start subtitle generation"""
        if not self.audio_directory.text():
            QMessageBox.warning(self, "Error", "Please select audio directory.")
            return
            
        # TODO: Implement subtitle generation logic
        self.subtitle_status.setText("Processing...")
        self.generate_btn.setEnabled(False)
        
        # Simulate processing
        QTimer.singleShot(3000, self.finish_subtitle_generation)
        
    def finish_subtitle_generation(self):
        """Finish subtitle generation"""
        self.subtitle_status.setText("Generated subtitles for 8 audio files.")
        self.generate_btn.setEnabled(True)
        self.subtitle_results.setText("audio_001.wav → audio_001.srt\naudio_002.wav → audio_002.srt\n...")
        self.subtitle_results.show()