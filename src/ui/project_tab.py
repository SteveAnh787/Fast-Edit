"""
Project Tab - Quản lý dự án và workspace
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit, QListWidget,
    QListWidgetItem, QFileDialog, QMessageBox, QScrollArea, QFrame,
    QSplitter, QCheckBox, QSpinBox, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap, QIcon

class ProjectTab(QWidget):
    """Tab quản lý dự án và workspace"""
    
    def __init__(self):
        super().__init__()
        
        self.setStyleSheet("""
            QWidget {
                background-color: #1e293b;
                color: #e2e8f0;
                font-size: 32px;
            }
            
            QPushButton {
                background-color: #4f46e5;
                color: white;
                border: none;
                padding: 16px 32px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 36px;
                min-height: 20px;
            }
            
            QPushButton:hover {
                background-color: #6366f1;
                transform: translateY(-1px);
            }
            
            QPushButton:pressed {
                background-color: #3730a3;
            }
            
            QLabel {
                color: #e2e8f0;
                font-size: 36px;
                padding: 8px;
            }
            
            QScrollArea {
                border: 1px solid #334155;
                border-radius: 8px;
                background-color: #0f172a;
            }
        """)
        
        # Project state
        self.current_project = {
            "name": "",
            "created": "",
            "modified": "",
            "audio_directory": "",
            "image_directory": "",
            "subtitle_directory": "",
            "output_directory": "",
            "pattern": "",
            "assets": [],
            "settings": {}
        }
        
        self.projects_directory = self._get_projects_directory()
        self.init_ui()
        self.load_recent_projects()
        
    def init_ui(self):
        """Initialize project tab UI"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header section
        header_frame = self.create_header_section()
        main_layout.addWidget(header_frame)
        
        # Content area with scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: rgba(30, 41, 59, 0.5);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(100, 116, 139, 0.8);
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(148, 163, 184, 0.8);
            }
        """)
        
        content_widget = QWidget()
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        # Content layout
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(24, 24, 24, 24)
        
        # Main grid layout for cards
        cards_layout = QGridLayout()
        cards_layout.setSpacing(20)
        
        # Row 1: Project management cards
        project_card = self.create_project_management_card()
        recent_card = self.create_recent_projects_card()
        
        cards_layout.addWidget(project_card, 0, 0)
        cards_layout.addWidget(recent_card, 0, 1)
        
        # Row 2: Directories and pattern matching
        directories_card = self.create_directories_card()
        pattern_card = self.create_pattern_matching_card()
        
        cards_layout.addWidget(directories_card, 1, 0)
        cards_layout.addWidget(pattern_card, 1, 1)
        
        # Set column stretch
        cards_layout.setColumnStretch(0, 1)
        cards_layout.setColumnStretch(1, 1)
        
        content_layout.addLayout(cards_layout)
        
        # Bottom actions bar
        actions_bar = self.create_actions_bar()
        content_layout.addWidget(actions_bar)
        
        content_layout.addStretch()
        
    def create_header_section(self):
        """Create header section"""
        header_frame = QFrame()
        header_frame.setFixedHeight(80)
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(79, 70, 229, 0.1),
                    stop:1 rgba(6, 182, 212, 0.1));
                border-bottom: 1px solid rgba(100, 116, 139, 0.2);
            }
        """)
        
        layout = QHBoxLayout(header_frame)
        layout.setContentsMargins(24, 0, 24, 0)
        
        # Left side - Title and description
        left_layout = QVBoxLayout()
        left_layout.setSpacing(4)
        
        title = QLabel("Project Management")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setStyleSheet("color: #f1f5f9; font-weight: 700;")
        
        subtitle = QLabel("Create, organize and manage your video projects")
        subtitle.setStyleSheet("color: #94a3b8; font-size: 12px;")
        
        left_layout.addWidget(title)
        left_layout.addWidget(subtitle)
        left_layout.addStretch()
        
        layout.addLayout(left_layout)
        layout.addStretch()
        
        # Right side - Quick project info
        self.header_project_info = QLabel("No project loaded")
        self.header_project_info.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.header_project_info.setStyleSheet("""
            color: #cbd5e1;
            font-size: 11px;
            font-weight: 500;
            background-color: rgba(30, 41, 59, 0.5);
            padding: 8px 12px;
            border-radius: 6px;
        """)
        
        layout.addWidget(self.header_project_info)
        
        return header_frame
        
    def create_project_management_card(self):
        """Create project management card"""
        card = self.create_card("Current Project", "📁")
        layout = card.layout()
        
        # Project name input
        name_layout = QVBoxLayout()
        name_layout.setSpacing(8)
        
        name_label = QLabel("PROJECT NAME")
        name_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;")
        
        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText("Enter project name...")
        self.project_name_input.textChanged.connect(self.update_project_name)
        self.apply_modern_input_style(self.project_name_input)
        
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.project_name_input)
        
        layout.addLayout(name_layout)
        
        # Project info display
        self.project_info_display = QFrame()
        self.project_info_display.setStyleSheet("""
            QFrame {
                background-color: rgba(15, 23, 42, 0.6);
                border: 1px solid rgba(100, 116, 139, 0.3);
                border-radius: 8px;
                padding: 12px;
            }
        """)
        
        info_layout = QVBoxLayout(self.project_info_display)
        info_layout.setSpacing(4)
        
        self.project_status = QLabel("Ready to create new project")
        self.project_status.setStyleSheet("color: #10b981; font-size: 11px; font-weight: 500;")
        
        self.project_details = QLabel("No project details")
        self.project_details.setStyleSheet("color: #94a3b8; font-size: 10px;")
        self.project_details.setWordWrap(True)
        
        info_layout.addWidget(self.project_status)
        info_layout.addWidget(self.project_details)
        
        layout.addWidget(self.project_info_display)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        
        self.new_project_btn = QPushButton("New")
        self.new_project_btn.clicked.connect(self.new_project)
        self.apply_modern_button_style(self.new_project_btn, "success")
        
        self.save_project_btn = QPushButton("Save")
        self.save_project_btn.clicked.connect(self.save_project)
        self.apply_modern_button_style(self.save_project_btn, "primary")
        
        self.load_project_btn = QPushButton("Load")
        self.load_project_btn.clicked.connect(self.load_project)
        self.apply_modern_button_style(self.load_project_btn, "secondary")
        
        buttons_layout.addWidget(self.new_project_btn)
        buttons_layout.addWidget(self.save_project_btn)
        buttons_layout.addWidget(self.load_project_btn)
        
        layout.addLayout(buttons_layout)
        
        return card
        
    def create_recent_projects_card(self):
        """Create recent projects card"""
        card = self.create_card("Recent Projects", "📋")
        layout = card.layout()
        
        # Recent projects list
        self.recent_projects_list = QListWidget()
        self.recent_projects_list.setMaximumHeight(200)
        self.recent_projects_list.setStyleSheet("""
            QListWidget {
                background-color: rgba(15, 23, 42, 0.6);
                border: 1px solid rgba(100, 116, 139, 0.3);
                border-radius: 8px;
                color: #e2e8f0;
                font-size: 11px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 12px;
                border-radius: 6px;
                margin: 2px;
                border: none;
            }
            QListWidget::item:hover {
                background-color: rgba(79, 70, 229, 0.15);
            }
            QListWidget::item:selected {
                background-color: rgba(79, 70, 229, 0.3);
                color: #f1f5f9;
            }
        """)
        self.recent_projects_list.itemDoubleClicked.connect(self.load_recent_project)
        
        layout.addWidget(self.recent_projects_list)
        
        # Quick load info
        info_label = QLabel("Double-click to load project")
        info_label.setStyleSheet("color: #64748b; font-size: 10px; text-align: center; margin-top: 8px;")
        info_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(info_label)
        
        return card
        
    def create_directories_card(self):
        """Create directories configuration card"""
        card = self.create_card("Project Directories", "📂")
        layout = card.layout()
        
        # Directory inputs
        dirs_data = [
            ("AUDIO", "audio_dir_input", "Select folder containing audio files", self.browse_audio_directory),
            ("IMAGES", "image_dir_input", "Select folder containing image files", self.browse_image_directory),
            ("SUBTITLES", "subtitle_dir_input", "Select folder for subtitle files (optional)", self.browse_subtitle_directory),
            ("OUTPUT", "output_dir_input", "Select folder to save rendered videos", self.browse_output_directory)
        ]
        
        for label_text, attr_name, placeholder, browse_func in dirs_data:
            dir_layout = self.create_directory_input_compact(label_text, placeholder, browse_func)
            setattr(self, attr_name, dir_layout[1])
            
            # Connect text change events
            if attr_name == "audio_dir_input":
                dir_layout[1].textChanged.connect(self.update_audio_directory)
            elif attr_name == "image_dir_input":
                dir_layout[1].textChanged.connect(self.update_image_directory)
            elif attr_name == "subtitle_dir_input":
                dir_layout[1].textChanged.connect(self.update_subtitle_directory)
            elif attr_name == "output_dir_input":
                dir_layout[1].textChanged.connect(self.update_output_directory)
                
            layout.addLayout(dir_layout[0])
            
        return card
        
    def create_pattern_matching_card(self):
        """Create pattern matching card"""
        card = self.create_card("Smart Pattern Matching", "🎯")
        layout = card.layout()
        
        # Pattern input
        pattern_layout = QVBoxLayout()
        pattern_layout.setSpacing(8)
        
        pattern_label = QLabel("FILE PATTERN")
        pattern_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;")
        
        pattern_input_layout = QHBoxLayout()
        pattern_input_layout.setSpacing(8)
        
        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText("e.g., audio, video, content...")
        self.pattern_input.textChanged.connect(self.update_pattern)
        self.apply_modern_input_style(self.pattern_input)
        
        self.apply_pattern_btn = QPushButton("Apply")
        self.apply_pattern_btn.clicked.connect(self.apply_pattern)
        self.apply_modern_button_style(self.apply_pattern_btn, "accent")
        self.apply_pattern_btn.setFixedWidth(80)
        
        pattern_input_layout.addWidget(self.pattern_input)
        pattern_input_layout.addWidget(self.apply_pattern_btn)
        
        pattern_layout.addWidget(pattern_label)
        pattern_layout.addLayout(pattern_input_layout)
        
        layout.addLayout(pattern_layout)
        
        # Pattern info
        pattern_info = QLabel("Enter base filename to auto-detect numbered files\n(e.g., 'audio' finds audio_001.mp3, audio_002.mp3...)")
        pattern_info.setStyleSheet("color: #64748b; font-size: 10px; line-height: 1.4;")
        pattern_info.setWordWrap(True)
        
        layout.addWidget(pattern_info)
        
        # Assets preview
        self.assets_preview = QTextEdit()
        self.assets_preview.setMaximumHeight(120)
        self.assets_preview.setPlaceholderText("Detected assets will appear here...")
        self.assets_preview.setStyleSheet("""
            QTextEdit {
                background-color: rgba(15, 23, 42, 0.6);
                border: 1px solid rgba(100, 116, 139, 0.3);
                border-radius: 8px;
                color: #94a3b8;
                font-size: 10px;
                padding: 12px;
                font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
            }
        """)
        
        layout.addWidget(self.assets_preview)
        
        return card
        
    def create_actions_bar(self):
        """Create bottom actions bar"""
        actions_frame = QFrame()
        actions_frame.setFixedHeight(60)
        actions_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 41, 59, 0.4);
                border: 1px solid rgba(100, 116, 139, 0.2);
                border-radius: 12px;
            }
        """)
        
        layout = QHBoxLayout(actions_frame)
        layout.setContentsMargins(16, 0, 16, 0)
        
        # Left side - Action description
        desc_layout = QVBoxLayout()
        desc_layout.setSpacing(2)
        
        title = QLabel("Quick Actions")
        title.setFont(QFont("Arial", 11, QFont.Bold))
        title.setStyleSheet("color: #f1f5f9;")
        
        subtitle = QLabel("Batch operations and project validation")
        subtitle.setStyleSheet("color: #94a3b8; font-size: 10px;")
        
        desc_layout.addWidget(title)
        desc_layout.addWidget(subtitle)
        desc_layout.addStretch()
        
        layout.addLayout(desc_layout)
        layout.addStretch()
        
        # Right side - Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        
        self.scan_assets_btn = QPushButton("Scan Assets")
        self.scan_assets_btn.clicked.connect(self.scan_all_assets)
        self.apply_modern_button_style(self.scan_assets_btn, "info")
        
        self.validate_project_btn = QPushButton("Validate")
        self.validate_project_btn.clicked.connect(self.validate_project)
        self.apply_modern_button_style(self.validate_project_btn, "warning")
        
        self.export_config_btn = QPushButton("Export")
        self.export_config_btn.clicked.connect(self.export_project_config)
        self.apply_modern_button_style(self.export_config_btn, "secondary")
        
        buttons_layout.addWidget(self.scan_assets_btn)
        buttons_layout.addWidget(self.validate_project_btn)
        buttons_layout.addWidget(self.export_config_btn)
        
        layout.addLayout(buttons_layout)
        
        return actions_frame
        
    def create_card(self, title: str, icon: str = "") -> QFrame:
        """Create a modern card widget"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 41, 59, 0.6);
                border: 1px solid rgba(100, 116, 139, 0.3);
                border-radius: 16px;
                padding: 0px;
            }
            QFrame:hover {
                border-color: rgba(100, 116, 139, 0.5);
                background-color: rgba(30, 41, 59, 0.7);
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Card header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        if icon:
            icon_label = QLabel(icon)
            icon_label.setFont(QFont("Arial", 14))
            icon_label.setFixedSize(20, 20)
            icon_label.setAlignment(Qt.AlignCenter)
            header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 13, QFont.Bold))
        title_label.setStyleSheet("color: #f1f5f9; font-weight: 600;")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        return card
        
    def create_directory_input_compact(self, label_text, placeholder, browse_func):
        """Create compact directory input"""
        layout = QVBoxLayout()
        layout.setSpacing(6)
        
        label = QLabel(label_text)
        label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;")
        
        input_layout = QHBoxLayout()
        input_layout.setSpacing(6)
        
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        self.apply_modern_input_style(line_edit)
        
        browse_btn = QPushButton("📁")
        browse_btn.clicked.connect(browse_func)
        browse_btn.setFixedSize(32, 32)
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(100, 116, 139, 0.2);
                border: 1px solid rgba(100, 116, 139, 0.4);
                border-radius: 6px;
                color: #cbd5e1;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(100, 116, 139, 0.3);
                border-color: rgba(148, 163, 184, 0.6);
            }
            QPushButton:pressed {
                background-color: rgba(100, 116, 139, 0.4);
            }
        """)
        
        input_layout.addWidget(line_edit)
        input_layout.addWidget(browse_btn)
        
        layout.addWidget(label)
        layout.addLayout(input_layout)
        
        return (layout, line_edit, browse_btn)
        
    def apply_modern_input_style(self, widget):
        """Apply modern input styling"""
        widget.setStyleSheet("""
            QLineEdit {
                background-color: rgba(15, 23, 42, 0.6);
                border: 1px solid rgba(100, 116, 139, 0.3);
                border-radius: 8px;
                padding: 8px 12px;
                color: #f1f5f9;
                font-size: 11px;
                selection-background-color: rgba(79, 70, 229, 0.3);
            }
            QLineEdit:focus {
                border-color: rgba(79, 70, 229, 0.6);
                background-color: rgba(15, 23, 42, 0.8);
                outline: none;
            }
            QLineEdit::placeholder {
                color: rgba(148, 163, 184, 0.6);
            }
        """)
        
    def apply_modern_button_style(self, button, style_type="primary"):
        """Apply modern button styling"""
        styles = {
            "primary": """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(79, 70, 229, 0.8),
                        stop:1 rgba(99, 102, 241, 0.8));
                    border: none;
                    border-radius: 8px;
                    color: white;
                    padding: 8px 16px;
                    font-size: 11px;
                    font-weight: 600;
                    min-height: 32px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(67, 56, 202, 0.9),
                        stop:1 rgba(79, 70, 229, 0.9));
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(55, 48, 163, 1.0),
                        stop:1 rgba(67, 56, 202, 1.0));
                }
            """,
            "success": """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(16, 185, 129, 0.8),
                        stop:1 rgba(5, 150, 105, 0.8));
                    border: none;
                    border-radius: 8px;
                    color: white;
                    padding: 8px 16px;
                    font-size: 11px;
                    font-weight: 600;
                    min-height: 32px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(5, 150, 105, 0.9),
                        stop:1 rgba(4, 120, 87, 0.9));
                }
            """,
            "secondary": """
                QPushButton {
                    background-color: rgba(100, 116, 139, 0.2);
                    border: 1px solid rgba(100, 116, 139, 0.4);
                    border-radius: 8px;
                    color: #cbd5e1;
                    padding: 8px 16px;
                    font-size: 11px;
                    font-weight: 500;
                    min-height: 32px;
                }
                QPushButton:hover {
                    background-color: rgba(100, 116, 139, 0.3);
                    border-color: rgba(148, 163, 184, 0.6);
                }
            """,
            "accent": """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(139, 92, 246, 0.8),
                        stop:1 rgba(124, 58, 237, 0.8));
                    border: none;
                    border-radius: 8px;
                    color: white;
                    padding: 8px 16px;
                    font-size: 11px;
                    font-weight: 600;
                    min-height: 32px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(124, 58, 237, 0.9),
                        stop:1 rgba(109, 40, 217, 0.9));
                }
            """,
            "info": """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(6, 182, 212, 0.8),
                        stop:1 rgba(8, 145, 178, 0.8));
                    border: none;
                    border-radius: 8px;
                    color: white;
                    padding: 8px 16px;
                    font-size: 11px;
                    font-weight: 600;
                    min-height: 32px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(8, 145, 178, 0.9),
                        stop:1 rgba(14, 116, 144, 0.9));
                }
            """,
            "warning": """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(245, 158, 11, 0.8),
                        stop:1 rgba(217, 119, 6, 0.8));
                    border: none;
                    border-radius: 8px;
                    color: white;
                    padding: 8px 16px;
                    font-size: 11px;
                    font-weight: 600;
                    min-height: 32px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(217, 119, 6, 0.9),
                        stop:1 rgba(180, 83, 9, 0.9));
                }
            """
        }
        
        button.setStyleSheet(styles.get(style_type, styles["primary"]))

    # Project management methods
    def _get_projects_directory(self) -> Path:
        """Get projects directory"""
        projects_dir = Path.home() / ".vibe_render_tool" / "projects"
        projects_dir.mkdir(parents=True, exist_ok=True)
        return projects_dir
        
    def new_project(self):
        """Create new project"""
        self.current_project = {
            "name": "Untitled Project",
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat(),
            "audio_directory": "",
            "image_directory": "",
            "subtitle_directory": "",
            "output_directory": "",
            "pattern": "",
            "assets": [],
            "settings": {}
        }
        
        self.project_name_input.setText(self.current_project["name"])
        self.update_project_info()
        self.clear_directories()
        
        QMessageBox.information(self, "New Project", "New project created successfully!")
        
    def save_project(self):
        """Save current project"""
        if not self.current_project["name"]:
            QMessageBox.warning(self, "Save Error", "Please enter a project name first.")
            return
            
        filename = f"{self.current_project['name']}.json"
        filepath = self.projects_directory / filename
        
        self.current_project["modified"] = datetime.now().isoformat()
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.current_project, f, indent=2, ensure_ascii=False)
                
            QMessageBox.information(self, "Project Saved", f"Project saved as '{filename}'")
            self.load_recent_projects()
            
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save project: {str(e)}")
            
    def load_project(self):
        """Load existing project"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Load Project",
            str(self.projects_directory),
            "Project files (*.json)"
        )
        
        if filepath:
            self.load_project_from_file(filepath)
            
    def load_project_from_file(self, filepath: str):
        """Load project from file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.current_project = json.load(f)
                
            # Update UI
            self.project_name_input.setText(self.current_project.get("name", ""))
            self.audio_dir_input.setText(self.current_project.get("audio_directory", ""))
            self.image_dir_input.setText(self.current_project.get("image_directory", ""))
            self.subtitle_dir_input.setText(self.current_project.get("subtitle_directory", ""))
            self.output_dir_input.setText(self.current_project.get("output_directory", ""))
            self.pattern_input.setText(self.current_project.get("pattern", ""))
            
            self.update_project_info()
            self.update_assets_preview()
            
            QMessageBox.information(self, "Project Loaded", f"Project '{self.current_project['name']}' loaded successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load project: {str(e)}")
            
    def load_recent_projects(self):
        """Load recent projects list"""
        self.recent_projects_list.clear()
        
        try:
            project_files = list(self.projects_directory.glob("*.json"))
            project_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for project_file in project_files[:8]:  # Show last 8 projects
                try:
                    with open(project_file, 'r', encoding='utf-8') as f:
                        project_data = json.load(f)
                        
                    name = project_data.get("name", project_file.stem)
                    modified = project_data.get("modified", "")
                    
                    if modified:
                        try:
                            mod_date = datetime.fromisoformat(modified)
                            mod_str = mod_date.strftime("%m/%d %H:%M")
                        except:
                            mod_str = "Unknown"
                    else:
                        mod_str = "Unknown"
                        
                    item_text = f"{name}\n{mod_str} • {project_file.name}"
                    
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, str(project_file))
                    self.recent_projects_list.addItem(item)
                    
                except:
                    continue
                    
        except Exception as e:
            print(f"Error loading recent projects: {e}")
            
    def load_recent_project(self, item):
        """Load recent project from list"""
        filepath = item.data(Qt.UserRole)
        if filepath:
            self.load_project_from_file(filepath)
            
    # Directory management methods
    def update_project_name(self, name):
        """Update project name"""
        self.current_project["name"] = name
        self.update_project_info()
        
    def update_audio_directory(self, directory):
        """Update audio directory"""
        self.current_project["audio_directory"] = directory
        self.update_project_info()
        
    def update_image_directory(self, directory):
        """Update image directory"""
        self.current_project["image_directory"] = directory
        self.update_project_info()
        
    def update_subtitle_directory(self, directory):
        """Update subtitle directory"""
        self.current_project["subtitle_directory"] = directory
        
    def update_output_directory(self, directory):
        """Update output directory"""
        self.current_project["output_directory"] = directory
        
    def update_pattern(self, pattern):
        """Update file pattern"""
        self.current_project["pattern"] = pattern
        
    def browse_audio_directory(self):
        """Browse for audio directory"""
        directory = QFileDialog.getExistingDirectory(self, "Select Audio Directory")
        if directory:
            self.audio_dir_input.setText(directory)
            
    def browse_image_directory(self):
        """Browse for image directory"""
        directory = QFileDialog.getExistingDirectory(self, "Select Image Directory")
        if directory:
            self.image_dir_input.setText(directory)
            
    def browse_subtitle_directory(self):
        """Browse for subtitle directory"""
        directory = QFileDialog.getExistingDirectory(self, "Select Subtitle Directory")
        if directory:
            self.subtitle_dir_input.setText(directory)
            
    def browse_output_directory(self):
        """Browse for output directory"""
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_dir_input.setText(directory)
            
    def clear_directories(self):
        """Clear all directory inputs"""
        self.audio_dir_input.clear()
        self.image_dir_input.clear()
        self.subtitle_dir_input.clear()
        self.output_dir_input.clear()
        self.pattern_input.clear()
        self.assets_preview.clear()
        
    # Pattern matching methods
    def apply_pattern(self):
        """Apply pattern to detect assets"""
        pattern = self.pattern_input.text().strip()
        if not pattern:
            QMessageBox.warning(self, "Pattern Error", "Please enter a file pattern.")
            return
            
        audio_dir = self.audio_dir_input.text().strip()
        image_dir = self.image_dir_input.text().strip()
        
        if not audio_dir or not image_dir:
            QMessageBox.warning(self, "Directory Error", "Please select audio and image directories first.")
            return
            
        # Detect matching files
        assets = self.detect_pattern_assets(pattern, audio_dir, image_dir)
        self.current_project["assets"] = assets
        self.update_assets_preview()
        
        if assets:
                    assets.append({
                        "audio": str(audio_file),
                        "image": str(image_file),
                        "subtitle": "",  # Will be filled later
                        "base_name": base_name
                    })
                    
        except Exception as e:
            print(f"Error detecting assets: {e}")
            
        return assets
        
    def update_assets_preview(self):
        """Update assets preview"""
        assets = self.current_project.get("assets", [])
        
        if not assets:
            self.assets_preview.setPlainText("No assets detected. Use pattern matching to find files.")
            return
            
        preview_text = f"📁 DETECTED ASSETS ({len(assets)} groups):\n\n"
        
        for i, asset in enumerate(assets[:8], 1):  # Show first 8
            audio_name = Path(asset["audio"]).name
            image_name = Path(asset["image"]).name
            preview_text += f"{i:2d}. {audio_name} + {image_name}\n"
            
        if len(assets) > 8:
            preview_text += f"\n... and {len(assets) - 8} more assets"
            
        self.assets_preview.setPlainText(preview_text)
        
    def update_project_info(self):
        """Update project info display"""
        if self.current_project["name"]:
            assets_count = len(self.current_project.get("assets", []))
            
            # Update status
            if assets_count > 0:
                self.project_status.setText(f"✅ Project ready • {assets_count} assets")
                self.project_status.setStyleSheet("color: #10b981; font-size: 11px; font-weight: 500;")
            else:
                self.project_status.setText("⚠️ No assets detected")
                self.project_status.setStyleSheet("color: #f59e0b; font-size: 11px; font-weight: 500;")
            
            # Update details
            created = self.current_project.get("created", "")
            if created:
                try:
                    created_date = datetime.fromisoformat(created)
                    created_str = created_date.strftime("%Y-%m-%d %H:%M")
                except:
                    created_str = "Unknown"
            else:
                created_str = "Unknown"
                
            audio_dir = self.current_project.get("audio_directory", "")
            audio_info = f"Audio: {Path(audio_dir).name}" if audio_dir else "Audio: Not set"
            
            image_dir = self.current_project.get("image_directory", "")
            image_info = f"Images: {Path(image_dir).name}" if image_dir else "Images: Not set"
                
            details_text = f"Created: {created_str}\n{audio_info} • {image_info}"
            self.project_details.setText(details_text)
            
            # Update header info
            self.header_project_info.setText(f"{self.current_project['name']} • {assets_count} assets")
        else:
            self.project_status.setText("Ready to create new project")
            self.project_status.setStyleSheet("color: #10b981; font-size: 11px; font-weight: 500;")
            self.project_details.setText("No project details")
            self.header_project_info.setText("No project loaded")
            
    # Quick actions
    def scan_all_assets(self):
        """Scan all directories for assets"""
        audio_dir = self.audio_dir_input.text().strip()
        image_dir = self.image_dir_input.text().strip()
        
        if not audio_dir or not image_dir:
            QMessageBox.warning(self, "Scan Error", "Please select audio and image directories first.")
            return
            
        # Auto-detect common patterns
        patterns = ["audio", "video", "content", "track", "file", "item"]
        best_pattern = None
        best_count = 0
        
        for pattern in patterns:
            assets = self.detect_pattern_assets(pattern, audio_dir, image_dir)
            if len(assets) > best_count:
                best_count = len(assets)
                best_pattern = pattern
                
        if best_pattern and best_count > 0:
            self.pattern_input.setText(best_pattern)
            self.current_project["assets"] = self.detect_pattern_assets(best_pattern, audio_dir, image_dir)
            self.update_assets_preview()
            self.update_project_info()
            QMessageBox.information(self, "Scan Complete", f"Auto-detected pattern '{best_pattern}' with {best_count} assets!")
        else:
            QMessageBox.information(self, "Scan Complete", "No common patterns found. Try manual pattern entry.")
            
    def validate_project(self):
        """Validate project configuration"""
        issues = []
        
        if not self.current_project["name"]:
            issues.append("• Project name is empty")
            
        if not self.current_project["audio_directory"]:
            issues.append("• Audio directory not set")
        elif not Path(self.current_project["audio_directory"]).exists():
            issues.append("• Audio directory does not exist")
            
        if not self.current_project["image_directory"]:
            issues.append("• Image directory not set")
        elif not Path(self.current_project["image_directory"]).exists():
            issues.append("• Image directory does not exist")
            
        if not self.current_project["output_directory"]:
            issues.append("• Output directory not set")
            
        assets = self.current_project.get("assets", [])
        if not assets:
            issues.append("• No assets detected (try pattern matching)")
            
        if issues:
            issues_text = "Project validation issues:\n\n" + "\n".join(issues)
            QMessageBox.warning(self, "Validation Issues", issues_text)
        else:
            QMessageBox.information(self, "Validation Success", "✅ Project configuration is valid!")
            
    def export_project_config(self):
        """Export project configuration"""
        if not self.current_project["name"]:
            QMessageBox.warning(self, "Export Error", "Please create or load a project first.")
            return
            
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Project Config",
            f"{self.current_project['name']}_config.json",
            "JSON files (*.json)"
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(self.current_project, f, indent=2, ensure_ascii=False)
                    
                QMessageBox.information(self, "Export Success", f"Configuration exported to:\n{filepath}")
                
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export: {str(e)}")

class ProjectCard(QFrame):
    def __init__(self, name="", description="", parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: #f9f9f9;
                margin: 5px;
                padding: 10px;
            }
            QFrame:hover {
                background-color: #f0f0f0;
                border: 1px solid #bbb;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Project name
        name_label = QLabel(name or "Untitled Project")
        name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(name_label)
        
        # Project description
        desc_label = QLabel(description or "No description")
        desc_label.setStyleSheet("color: #666; font-size: 12px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        open_btn = QPushButton("Open")
        open_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        
        edit_btn = QPushButton("Edit")
        edit_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; }")
        
        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
        
        button_layout.addWidget(open_btn)
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(delete_btn)
        
        layout.addLayout(button_layout)