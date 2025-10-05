from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .unified_styles import ModernColors, MaterialIcons, UnifiedStyles


class ProjectTab(QWidget):
    """Project management tab with responsive layout and unified styling."""

    def __init__(self) -> None:
        super().__init__()
        self._init_scaling()

        self.current_project: Dict[str, object] = {
            "name": "",
            "created": "",
            "modified": "",
            "audio_directory": "",
            "image_directory": "",
            "subtitle_directory": "",
            "output_directory": "",
            "pattern": "",
            "assets": [],
            "settings": {},
        }

        self.projects_directory = self._get_projects_directory()

        self._build_widgets()
        self.load_recent_projects()
        self.update_project_info()
        self.refresh_stylesheet()

    # ------------------------------------------------------------------
    # Styling helpers
    # ------------------------------------------------------------------
    def _init_scaling(self) -> None:
        """Initialise scaling factors based on the current screen DPI."""
        screen = self.screen() or QGuiApplication.primaryScreen()
        dpi = 96.0
        if screen is not None:
            try:
                dpi = screen.logicalDotsPerInch() or dpi
            except AttributeError:
                pass
        self.dpi_scale = max(0.85, min(1.45, dpi / 96.0))
        self.responsive_breakpoint = 1080

    def sp(self, value: int) -> int:
        """Scale pixel-based spacing values."""
        return max(1, int(round(value * self.dpi_scale)))

    def fp(self, value: int) -> int:
        """Scale font sizes with sensible floor."""
        return max(10, int(round(value * self.dpi_scale)))

    def refresh_stylesheet(self) -> None:
        base_styles = UnifiedStyles.get_main_stylesheet()
        self.setStyleSheet(base_styles + self._build_local_stylesheet())

    def _build_local_stylesheet(self) -> str:
        return f"""
        QFrame#HeaderFrame {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {ModernColors.PRIMARY}, stop:1 {ModernColors.TERTIARY});
            border-bottom: 1px solid {ModernColors.OUTLINE_VARIANT};
        }}

        QLabel#HeaderTitle {{
            color: {ModernColors.ON_PRIMARY};
            font-size: {self.fp(18)}px;
            font-weight: 600;
            background: transparent;
        }}

        QLabel#HeaderSubtitle {{
            color: {ModernColors.ON_PRIMARY};
            font-size: {self.fp(12)}px;
            opacity: 0.8;
            background: transparent;
        }}

        QLabel#HeaderInfo {{
            color: {ModernColors.ON_PRIMARY};
            background-color: rgba(15, 23, 42, 0.45);
            padding: {self.sp(6)}px {self.sp(12)}px;
            border-radius: {self.sp(12)}px;
            font-size: {self.fp(11)}px;
        }}

        QFrame#InfoFrame {{
            background-color: rgba(15, 23, 42, 0.55);
            border: 1px solid {ModernColors.OUTLINE_VARIANT};
            border-radius: {self.sp(12)}px;
        }}

        QLabel#StatusLabel {{
            color: {ModernColors.SECONDARY};
            font-weight: 600;
            font-size: {self.fp(12)}px;
        }}

        QLabel#DetailsLabel {{
            color: {ModernColors.ON_SURFACE_VARIANT};
            font-size: {self.fp(11)}px;
        }}

        QListWidget#RecentProjectsList {{
            min-height: {self.sp(220)}px;
        }}

        QTextEdit#AssetsPreview {{
            min-height: {self.sp(140)}px;
        }}

        QFrame#ActionsBar {{
            background-color: rgba(15, 23, 42, 0.55);
            border: 1px solid {ModernColors.OUTLINE_VARIANT};
            border-radius: {self.sp(16)}px;
        }}
        """

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_widgets(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(self.sp(16))
        main_layout.setContentsMargins(self.sp(24), self.sp(20), self.sp(24), self.sp(24))

        header = self._create_header_section()
        main_layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)

        content_widget = QWidget()
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll, 1)

        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(self.sp(20))
        content_layout.setContentsMargins(0, 0, 0, 0)

        self.cards_layout = QGridLayout()
        self.cards_layout.setSpacing(self.sp(20))
        content_layout.addLayout(self.cards_layout)

        self.project_card = self._create_project_management_card()
        self.recent_card = self._create_recent_projects_card()
        self.directories_card = self._create_directories_card()
        self.pattern_card = self._create_pattern_matching_card()

        self.card_widgets: List[QWidget] = [
            self.project_card,
            self.recent_card,
            self.directories_card,
            self.pattern_card,
        ]
        self.update_cards_layout(self.width() or self.responsive_breakpoint + 1)

        actions_bar = self._create_actions_bar()
        content_layout.addWidget(actions_bar)
        content_layout.addStretch()

    def _create_header_section(self) -> QFrame:
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")

        layout = QHBoxLayout(header_frame)
        layout.setContentsMargins(self.sp(24), self.sp(16), self.sp(24), self.sp(16))
        layout.setSpacing(self.sp(12))

        title_layout = QVBoxLayout()
        title_layout.setSpacing(self.sp(4))

        title = QLabel(f"{MaterialIcons.PROJECT} Project Management")
        title.setObjectName("HeaderTitle")
        title_layout.addWidget(title)

        subtitle = QLabel("Create, organise, and manage your video projects")
        subtitle.setObjectName("HeaderSubtitle")
        title_layout.addWidget(subtitle)
        title_layout.addStretch()

        layout.addLayout(title_layout)
        layout.addStretch()

        self.header_project_info = QLabel("No project loaded")
        self.header_project_info.setObjectName("HeaderInfo")
        self.header_project_info.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.header_project_info)

        return header_frame

    def _create_project_management_card(self) -> QFrame:
        card = self._create_card()
        layout = card.layout()  # type: ignore[assignment]

        title = QLabel(f"{MaterialIcons.PROJECT} Current Project")
        UnifiedStyles.apply_typography(title, "title-medium")
        title.setStyleSheet("font-weight: 600; margin-bottom: 8px; background: transparent;")
        layout.addWidget(title)

        name_label = QLabel("Project name")
        UnifiedStyles.apply_typography(name_label, "label-small")
        name_label.setStyleSheet("background: transparent; color: #94a3b8; margin-bottom: 4px;")
        layout.addWidget(name_label)

        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText("Enter project name")
        self.project_name_input.textChanged.connect(self.update_project_name)
        self.project_name_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 1px solid #334155;
                border-radius: 8px;
                background-color: #1e293b;
                color: #e2e8f0;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #4f46e5;
                background-color: #0f172a;
            }
        """)
        layout.addWidget(self.project_name_input)

        info_frame = QFrame()
        info_frame.setObjectName("InfoFrame")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(self.sp(12), self.sp(12), self.sp(12), self.sp(12))
        info_layout.setSpacing(self.sp(4))

        self.project_status = QLabel("Ready to create a new project")
        self.project_status.setObjectName("StatusLabel")
        info_layout.addWidget(self.project_status)

        self.project_details = QLabel("No project details available")
        self.project_details.setObjectName("DetailsLabel")
        self.project_details.setWordWrap(True)
        info_layout.addWidget(self.project_details)

        layout.addWidget(info_frame)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(self.sp(12))

        self.new_project_btn = QPushButton(f"{MaterialIcons.ADD} New")
        UnifiedStyles.apply_button_style(self.new_project_btn, "secondary")
        self.new_project_btn.clicked.connect(self.new_project)
        buttons_layout.addWidget(self.new_project_btn)

        self.save_project_btn = QPushButton(f"{MaterialIcons.SAVE} Save")
        UnifiedStyles.apply_button_style(self.save_project_btn, "primary")
        self.save_project_btn.clicked.connect(self.save_project)
        buttons_layout.addWidget(self.save_project_btn)

        self.load_project_btn = QPushButton(f"{MaterialIcons.LOAD} Load")
        UnifiedStyles.apply_button_style(self.load_project_btn, "outline")
        self.load_project_btn.clicked.connect(self.load_project)
        buttons_layout.addWidget(self.load_project_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        return card

    def _create_recent_projects_card(self) -> QFrame:
        card = self._create_card()
        layout = card.layout()  # type: ignore[assignment]

        title = QLabel(f"{MaterialIcons.FILE} Recent Projects")
        UnifiedStyles.apply_typography(title, "title-medium")
        title.setStyleSheet("font-weight: 600; margin-bottom: 8px; background: transparent;")
        layout.addWidget(title)

        description = QLabel("Double-click to load a saved project")
        UnifiedStyles.apply_typography(description, "body-small")
        description.setStyleSheet("background: transparent; color: #64748b; margin-bottom: 8px;")
        layout.addWidget(description)

        self.recent_projects_list = QListWidget()
        self.recent_projects_list.setObjectName("RecentProjectsList")
        self.recent_projects_list.itemDoubleClicked.connect(self.load_selected_recent_project)
        layout.addWidget(self.recent_projects_list)

        return card

    def _create_directories_card(self) -> QFrame:
        card = self._create_card()
        layout = card.layout()  # type: ignore[assignment]

        title = QLabel(f"{MaterialIcons.FOLDER} Project Directories")
        UnifiedStyles.apply_typography(title, "title-medium")
        title.setStyleSheet("font-weight: 600; margin-bottom: 12px; background: transparent;")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(self.sp(12))
        layout.addLayout(grid)

        self.audio_dir_input = self._create_directory_row(
            grid,
            row=0,
            label="Audio files",
            placeholder="Select folder containing audio files",
            browse_slot=self.browse_audio_directory,
            on_change=self.update_audio_directory,
        )

        self.image_dir_input = self._create_directory_row(
            grid,
            row=1,
            label="Image files",
            placeholder="Select folder containing image files",
            browse_slot=self.browse_image_directory,
            on_change=self.update_image_directory,
        )

        self.subtitle_dir_input = self._create_directory_row(
            grid,
            row=2,
            label="Subtitles (optional)",
            placeholder="Select folder containing subtitle files",
            browse_slot=self.browse_subtitle_directory,
            on_change=self.update_subtitle_directory,
        )

        self.output_dir_input = self._create_directory_row(
            grid,
            row=3,
            label="Output",
            placeholder="Select folder for rendered videos",
            browse_slot=self.browse_output_directory,
            on_change=self.update_output_directory,
        )

        return card

    def _create_pattern_matching_card(self) -> QFrame:
        card = self._create_card()
        layout = card.layout()  # type: ignore[assignment]

        title = QLabel(f"{MaterialIcons.PATTERN} Smart Pattern Matching")
        UnifiedStyles.apply_typography(title, "title-medium")
        title.setStyleSheet("font-weight: 600; margin-bottom: 8px; background: transparent;")
        layout.addWidget(title)

        description = QLabel("Enter a base filename to detect related assets (e.g. 'audio', 'scene01').")
        UnifiedStyles.apply_typography(description, "body-small")
        description.setWordWrap(True)
        description.setStyleSheet("background: transparent; color: #64748b; margin-bottom: 12px;")
        layout.addWidget(description)

        input_layout = QHBoxLayout()
        input_layout.setSpacing(self.sp(12))

        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText("e.g. audio, scene01, shot_01")
        self.pattern_input.textChanged.connect(self.update_pattern)
        self.pattern_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 1px solid #334155;
                border-radius: 8px;
                background-color: #1e293b;
                color: #e2e8f0;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #4f46e5;
                background-color: #0f172a;
            }
        """)
        input_layout.addWidget(self.pattern_input)

        self.apply_pattern_btn = QPushButton(f"{MaterialIcons.MAGIC_WAND} Apply")
        UnifiedStyles.apply_button_style(self.apply_pattern_btn, "tertiary")
        self.apply_pattern_btn.clicked.connect(self.apply_pattern)
        input_layout.addWidget(self.apply_pattern_btn)

        layout.addLayout(input_layout)

        helper = QLabel("Detected assets will appear below once a pattern has been applied.")
        UnifiedStyles.apply_typography(helper, "caption")
        helper.setStyleSheet("background: transparent; color: #64748b;")
        layout.addWidget(helper)

        self.assets_preview = QTextEdit()
        self.assets_preview.setReadOnly(True)
        self.assets_preview.setObjectName("AssetsPreview")
        layout.addWidget(self.assets_preview)

        return card

    def _create_actions_bar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("ActionsBar")

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(self.sp(18), self.sp(12), self.sp(18), self.sp(12))
        layout.setSpacing(self.sp(16))

        text_block = QVBoxLayout()
        text_block.setSpacing(self.sp(2))

        title = QLabel(f"{MaterialIcons.MAGIC_WAND} Quick Actions")
        UnifiedStyles.apply_typography(title, "title-small")
        title.setStyleSheet("font-weight: 600; color: #e2e8f0;")
        text_block.addWidget(title)

        subtitle = QLabel("Validate configuration, scan assets, or export settings")
        UnifiedStyles.apply_typography(subtitle, "body-small")
        subtitle.setStyleSheet("background: transparent; color: #64748b;")
        text_block.addWidget(subtitle)
        text_block.addStretch()

        layout.addLayout(text_block)
        layout.addStretch()

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(self.sp(12))

        self.scan_assets_btn = QPushButton(f"{MaterialIcons.SCAN} Scan Assets")
        UnifiedStyles.apply_button_style(self.scan_assets_btn, "primary")
        self.scan_assets_btn.clicked.connect(self.scan_all_assets)
        buttons_layout.addWidget(self.scan_assets_btn)

        self.validate_project_btn = QPushButton(f"{MaterialIcons.VALIDATE} Validate")
        UnifiedStyles.apply_button_style(self.validate_project_btn, "secondary")
        self.validate_project_btn.clicked.connect(self.validate_project)
        buttons_layout.addWidget(self.validate_project_btn)

        self.export_config_btn = QPushButton(f"{MaterialIcons.EXPORT} Export Config")
        UnifiedStyles.apply_button_style(self.export_config_btn, "outline")
        self.export_config_btn.clicked.connect(self.export_project_config)
        buttons_layout.addWidget(self.export_config_btn)

        layout.addLayout(buttons_layout)
        return frame

    def _create_card(self) -> QFrame:
        card = QFrame()
        UnifiedStyles.apply_card_style(card)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(self.sp(20), self.sp(20), self.sp(20), self.sp(20))
        layout.setSpacing(self.sp(16))
        return card

    def _create_directory_row(
        self,
        grid: QGridLayout,
        row: int,
        label: str,
        placeholder: str,
        browse_slot,
        on_change,
    ) -> QLineEdit:
        caption = QLabel(label)
        UnifiedStyles.apply_typography(caption, "label-small")
        caption.setAlignment(Qt.AlignCenter)  # Căn giữa text
        caption.setStyleSheet("background: transparent; padding: 8px;")  # Bỏ background
        grid.addWidget(caption, row, 0, 1, 1)

        input_layout = QHBoxLayout()
        input_layout.setSpacing(self.sp(8))

        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        line_edit.textChanged.connect(on_change)
        input_layout.addWidget(line_edit, 1)

        browse_btn = QPushButton(f"{MaterialIcons.FOLDER} Browse")
        UnifiedStyles.apply_button_style(browse_btn, "outline", "small")
        browse_btn.clicked.connect(browse_slot)
        input_layout.addWidget(browse_btn)

        grid.addLayout(input_layout, row, 1, 1, 1)
        return line_edit

    # ------------------------------------------------------------------
    # Layout responsiveness
    # ------------------------------------------------------------------
    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self.update_cards_layout(event.size().width())

    def update_cards_layout(self, available_width: int) -> None:
        if not hasattr(self, "cards_layout"):
            return

        for widget in self.card_widgets:
            self.cards_layout.removeWidget(widget)

        columns = 1 if available_width < self.responsive_breakpoint else 2
        for index, widget in enumerate(self.card_widgets):
            row = index // columns
            column = index % columns
            self.cards_layout.addWidget(widget, row, column)

        self.cards_layout.setColumnStretch(0, 1)
        self.cards_layout.setColumnStretch(1, 1 if columns > 1 else 0)

    # ------------------------------------------------------------------
    # Project state helpers
    # ------------------------------------------------------------------
    def _get_projects_directory(self) -> Path:
        projects_dir = Path.home() / ".vibe_render_tool" / "projects"
        projects_dir.mkdir(parents=True, exist_ok=True)
        return projects_dir

    def new_project(self) -> None:
        timestamp = datetime.now().isoformat()
        self.current_project = {
            "name": "Untitled Project",
            "created": timestamp,
            "modified": timestamp,
            "audio_directory": "",
            "image_directory": "",
            "subtitle_directory": "",
            "output_directory": "",
            "pattern": "",
            "assets": [],
            "settings": {},
        }
        self.project_name_input.setText(self.current_project["name"])  # type: ignore[arg-type]
        self.pattern_input.clear()
        self.assets_preview.clear()
        self.audio_dir_input.clear()
        self.image_dir_input.clear()
        self.subtitle_dir_input.clear()
        self.output_dir_input.clear()
        self.update_project_info()
        QMessageBox.information(self, "New Project", "A fresh project has been created.")

    def save_project(self) -> None:
        name = self.current_project.get("name", "").strip()  # type: ignore[help-by-default]
        if not name:
            QMessageBox.warning(self, "Save Project", "Please enter a project name before saving.")
            return

        self.current_project["modified"] = datetime.now().isoformat()

        filename = f"{name}.json"
        filepath = self.projects_directory / filename
        try:
            with filepath.open("w", encoding="utf-8") as handle:
                json.dump(self.current_project, handle, indent=2)
        except Exception as exc:  # pragma: no cover - user notified
            QMessageBox.critical(self, "Save Project", f"Failed to save project:\n{exc}")
            return

        QMessageBox.information(self, "Save Project", f"Project saved to {filepath}")
        self.load_recent_projects()
        self.update_project_info()

    def load_project(self) -> None:
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Load Project",
            str(self.projects_directory),
            "Project files (*.json)",
        )
        if not filepath:
            return

        try:
            with open(filepath, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception as exc:  # pragma: no cover - user notified
            QMessageBox.critical(self, "Load Project", f"Failed to load project:\n{exc}")
            return

        self.current_project = {
            **{
                "name": "",
                "created": "",
                "modified": "",
                "audio_directory": "",
                "image_directory": "",
                "subtitle_directory": "",
                "output_directory": "",
                "pattern": "",
                "assets": [],
                "settings": {},
            },
            **data,
        }

        self.project_name_input.setText(self.current_project.get("name", ""))
        self.audio_dir_input.setText(self.current_project.get("audio_directory", ""))
        self.image_dir_input.setText(self.current_project.get("image_directory", ""))
        self.subtitle_dir_input.setText(self.current_project.get("subtitle_directory", ""))
        self.output_dir_input.setText(self.current_project.get("output_directory", ""))
        self.pattern_input.setText(self.current_project.get("pattern", ""))
        self.update_assets_preview()
        self.update_project_info()
        self.load_recent_projects()

    def load_selected_recent_project(self, item: QListWidgetItem) -> None:
        filepath = item.data(Qt.UserRole)
        if filepath:
            self._load_project_from_path(Path(filepath))

    def _load_project_from_path(self, path: Path) -> None:
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception as exc:  # pragma: no cover - user notified
            QMessageBox.critical(self, "Load Project", f"Failed to load project:\n{exc}")
            return

        self.current_project.update(data)
        self.project_name_input.setText(self.current_project.get("name", ""))
        self.audio_dir_input.setText(self.current_project.get("audio_directory", ""))
        self.image_dir_input.setText(self.current_project.get("image_directory", ""))
        self.subtitle_dir_input.setText(self.current_project.get("subtitle_directory", ""))
        self.output_dir_input.setText(self.current_project.get("output_directory", ""))
        self.pattern_input.setText(self.current_project.get("pattern", ""))
        self.update_assets_preview()
        self.update_project_info()

    def load_recent_projects(self) -> None:
        self.recent_projects_list.clear()
        if not self.projects_directory.exists():
            return

        project_files = sorted(
            self.projects_directory.glob("*.json"),
            key=lambda file: file.stat().st_mtime,
            reverse=True,
        )

        if not project_files:
            placeholder = QListWidgetItem("No saved projects yet")
            placeholder.setFlags(Qt.NoItemFlags)
            self.recent_projects_list.addItem(placeholder)
            return

        for path in project_files[:12]:
            item = QListWidgetItem(path.stem)
            item.setToolTip(str(path))
            item.setData(Qt.UserRole, str(path))
            self.recent_projects_list.addItem(item)

    def update_project_name(self, name: str) -> None:
        self.current_project["name"] = name
        self.update_project_info()

    def update_audio_directory(self, value: str) -> None:
        self.current_project["audio_directory"] = value

    def update_image_directory(self, value: str) -> None:
        self.current_project["image_directory"] = value

    def update_subtitle_directory(self, value: str) -> None:
        self.current_project["subtitle_directory"] = value

    def update_output_directory(self, value: str) -> None:
        self.current_project["output_directory"] = value

    def update_pattern(self, value: str) -> None:
        self.current_project["pattern"] = value

    def browse_audio_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select Audio Directory")
        if directory:
            self.audio_dir_input.setText(directory)

    def browse_image_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select Image Directory")
        if directory:
            self.image_dir_input.setText(directory)

    def browse_subtitle_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select Subtitle Directory")
        if directory:
            self.subtitle_dir_input.setText(directory)

    def browse_output_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_dir_input.setText(directory)

    # ------------------------------------------------------------------
    # Pattern matching & validation
    # ------------------------------------------------------------------
    def apply_pattern(self) -> None:
        pattern = self.pattern_input.text().strip()
        if not pattern:
            QMessageBox.warning(self, "Pattern Matching", "Please enter a pattern first.")
            return

        assets = self.detect_pattern_assets(pattern)
        self.current_project["pattern"] = pattern
        self.current_project["assets"] = [str(path) for path in assets]
        self.update_assets_preview()

        if assets:
            QMessageBox.information(
                self,
                "Pattern Matching",
                f"Found {len(assets)} assets matching '{pattern}'.",
            )
        else:
            QMessageBox.information(
                self,
                "Pattern Matching",
                "No files matched the provided pattern. Try another keyword.",
            )
        self.update_project_info()

    def detect_pattern_assets(self, pattern: str) -> List[Path]:
        pattern_lower = pattern.lower()
        matches: List[Path] = []
        directories = [
            self.current_project.get("audio_directory", ""),
            self.current_project.get("image_directory", ""),
            self.current_project.get("subtitle_directory", ""),
        ]
        for directory in directories:
            if not directory:
                continue
            dir_path = Path(directory)
            if not dir_path.exists():
                continue
            for entry in dir_path.iterdir():
                if entry.is_file() and pattern_lower in entry.stem.lower():
                    matches.append(entry)
        return matches

    def update_assets_preview(self) -> None:
        assets = self.current_project.get("assets", [])
        if assets:
            preview_lines = []
            for asset in assets[:25]:
                preview_lines.append(Path(asset).name if isinstance(asset, str) else str(asset))
            if len(assets) > 25:
                preview_lines.append(f"… +{len(assets) - 25} more")
            self.assets_preview.setPlainText("\n".join(preview_lines))
        else:
            self.assets_preview.clear()

    def scan_all_assets(self) -> None:
        audio_dir = self.current_project.get("audio_directory", "")
        image_dir = self.current_project.get("image_directory", "")
        if not audio_dir and not image_dir:
            QMessageBox.warning(
                self,
                "Scan Assets",
                "Please select at least one directory (audio or image) before scanning.",
            )
            return

        candidate_patterns = ["audio", "image", "video", "scene", "shot", "take", "file"]
        best_pattern = ""
        best_matches: List[Path] = []

        for pattern in candidate_patterns:
            matches = self.detect_pattern_assets(pattern)
            if len(matches) > len(best_matches):
                best_pattern = pattern
                best_matches = matches

        if best_pattern:
            self.pattern_input.setText(best_pattern)
            self.current_project["pattern"] = best_pattern
            self.current_project["assets"] = [str(path) for path in best_matches]
            self.update_assets_preview()
            self.update_project_info()
            QMessageBox.information(
                self,
                "Scan Assets",
                f"Auto-detected pattern '{best_pattern}' with {len(best_matches)} assets.",
            )
        else:
            QMessageBox.information(
                self,
                "Scan Assets",
                "No common patterns found. Try entering a pattern manually.",
            )

    def validate_project(self) -> None:
        issues: List[str] = []
        name = self.current_project.get("name", "").strip()
        if not name:
            issues.append("• Project name is empty")

        audio_dir = self.current_project.get("audio_directory", "").strip()
        if not audio_dir:
            issues.append("• Audio directory not set")
        elif not Path(audio_dir).exists():
            issues.append("• Audio directory does not exist")

        image_dir = self.current_project.get("image_directory", "").strip()
        if not image_dir:
            issues.append("• Image directory not set")
        elif not Path(image_dir).exists():
            issues.append("• Image directory does not exist")

        output_dir = self.current_project.get("output_directory", "").strip()
        if not output_dir:
            issues.append("• Output directory not set")
        elif not Path(output_dir).exists():
            issues.append("• Output directory does not exist")

        assets = self.current_project.get("assets", [])
        if not assets:
            issues.append("• No assets detected. Apply or scan for a pattern.")

        if issues:
            QMessageBox.warning(self, "Validation", "Project issues detected:\n\n" + "\n".join(issues))
        else:
            QMessageBox.information(self, "Validation", "Project configuration looks good!")

    def export_project_config(self) -> None:
        name = self.current_project.get("name", "").strip() or "project"
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Project Config",
            f"{name}_config.json",
            "JSON files (*.json)",
        )
        if not filepath:
            return

        try:
            with open(filepath, "w", encoding="utf-8") as handle:
                json.dump(self.current_project, handle, indent=2)
        except Exception as exc:  # pragma: no cover - user notified
            QMessageBox.critical(self, "Export", f"Failed to export configuration:\n{exc}")
            return

        QMessageBox.information(self, "Export", f"Configuration exported to:\n{filepath}")

    # ------------------------------------------------------------------
    # Presentation helpers
    # ------------------------------------------------------------------
    def update_project_info(self) -> None:
        name = self.current_project.get("name", "").strip() or "Unnamed project"
        created = self.current_project.get("created", "")
        modified = self.current_project.get("modified", "")
        assets = self.current_project.get("assets", [])

        def _format(timestamp: str) -> str:
            if not timestamp:
                return "n/a"
            if "T" in timestamp:
                try:
                    return datetime.fromisoformat(timestamp).strftime("%d %b %Y %H:%M")
                except ValueError:
                    return timestamp
            return timestamp

        created_text = _format(created)
        modified_text = _format(modified)

        self.project_status.setText(f"Active project: {name}")
        details_lines = [
            f"Created: {created_text}",
            f"Last saved: {modified_text}",
            f"Assets detected: {len(assets)}",
        ]
        self.project_details.setText("\n".join(details_lines))
        self.header_project_info.setText(f"{name} • {len(assets)} assets")

