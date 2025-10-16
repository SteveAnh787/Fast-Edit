from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt
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

from .unified_styles import UnifiedStyles


@dataclass
class ProjectRecord:
    id: str
    name: str
    description: str
    created_at: str
    updated_at: str
    directories: Dict[str, str] = field(default_factory=lambda: {"audio": "", "image": "", "subtitle": "", "output": ""})
    resources: Dict[str, int] = field(default_factory=lambda: {"audio": 0, "image": 0, "subtitle": 0})
    history: List[Dict[str, str]] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)
    file_path: Optional[Path] = None

    @classmethod
    def new(cls) -> "ProjectRecord":
        now = datetime.now().isoformat()
        record = cls(
            id=str(uuid.uuid4()),
            name="Untitled Project",
            description="",
            created_at=now,
            updated_at=now,
        )
        record.push_history("Project created")
        return record

    def push_history(self, message: str) -> None:
        self.history.insert(0, {"timestamp": datetime.now().isoformat(), "event": message})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "directories": self.directories,
            "resources": self.resources,
            "history": self.history,
            "settings": self.settings,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], source: Optional[Path] = None) -> "ProjectRecord":
        # Backward compatibility for legacy project files.
        directories = data.get("directories") or {
            "audio": data.get("audio_directory", ""),
            "image": data.get("image_directory", ""),
            "subtitle": data.get("subtitle_directory", ""),
            "output": data.get("output_directory", ""),
        }
        resources = data.get("resources") or {"audio": 0, "image": 0, "subtitle": 0}
        history = data.get("history") or []

        record = cls(
            id=data.get("id", data.get("name", str(uuid.uuid4()))),
            name=data.get("name", "Untitled Project"),
            description=data.get("description", ""),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            directories=directories,
            resources=resources,
            history=history,
            settings=data.get("settings", {}),
            file_path=source,
        )
        return record


class ProjectTab(QWidget):
    """Project management workspace inspired by shadcn/ui."""

    def __init__(self) -> None:
        super().__init__()
        self.projects_directory = self._get_projects_directory()
        self.projects: List[ProjectRecord] = []
        self.current_project: ProjectRecord = ProjectRecord.new()
        self.unsaved_changes = False

        self._build_ui()
        self._load_projects()
        self._bind_project(self.current_project)

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        UnifiedStyles.refresh_stylesheet(self)

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(24, 20, 24, 24)
        root_layout.setSpacing(20)

        left_panel = self._build_project_list_panel()
        right_panel = self._build_project_detail_panel()

        root_layout.addWidget(left_panel, 0)
        root_layout.addWidget(right_panel, 1)

    def _build_project_list_panel(self) -> QWidget:
        container = QFrame()
        UnifiedStyles.apply_card_style(container)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("Projects")
        UnifiedStyles.apply_typography(title, "headline-small")
        layout.addWidget(title)

        subtitle = QLabel("Create and manage your video projects before editing.")
        UnifiedStyles.apply_typography(subtitle, "body-small")
        layout.addWidget(subtitle)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search projects")
        self.search_input.textChanged.connect(self._filter_project_list)
        layout.addWidget(self.search_input)

        self.project_list = QListWidget()
        self.project_list.setSelectionMode(QListWidget.SingleSelection)
        self.project_list.itemSelectionChanged.connect(self._on_project_selection_changed)
        layout.addWidget(self.project_list, 1)

        self.create_project_btn = QPushButton("New Project")
        self.create_project_btn.clicked.connect(self._create_project_flow)
        UnifiedStyles.apply_button_style(self.create_project_btn, "primary")
        layout.addWidget(self.create_project_btn)

        return container

    def _build_project_detail_panel(self) -> QWidget:
        outer = QFrame()
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(16)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        self.header_card = self._build_info_card()
        self.directories_card = self._build_directories_card()
        self.resources_card = self._build_resources_card()
        self.history_card = self._build_history_card()
        self.action_bar = self._build_action_bar()

        content_layout.addWidget(self.header_card)
        content_layout.addWidget(self.directories_card)
        content_layout.addWidget(self.resources_card)
        content_layout.addWidget(self.history_card)
        content_layout.addWidget(self.action_bar)
        content_layout.addStretch()

        scroll.setWidget(content)
        outer_layout.addWidget(scroll)
        return outer

    def _build_info_card(self) -> QFrame:
        card = QFrame()
        UnifiedStyles.apply_card_style(card, elevated=True)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(26, 26, 26, 26)
        layout.setSpacing(18)

        self.project_name_edit = QLineEdit()
        self.project_name_edit.setPlaceholderText("Project name")
        self.project_name_edit.textChanged.connect(self._on_project_name_changed)

        self.project_description_edit = QTextEdit()
        self.project_description_edit.setPlaceholderText("Project description, goals, or notes")
        self.project_description_edit.textChanged.connect(self._on_project_description_changed)
        self.project_description_edit.setMinimumHeight(80)

        meta_row = QHBoxLayout()
        meta_row.setSpacing(24)

        self.created_label = QLabel()
        UnifiedStyles.apply_typography(self.created_label, "body-small")

        self.updated_label = QLabel()
        UnifiedStyles.apply_typography(self.updated_label, "body-small")

        self.status_badge = QLabel()
        UnifiedStyles.apply_typography(self.status_badge, "overline")
        self.status_badge.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        meta_row.addWidget(self.created_label)
        meta_row.addWidget(self.updated_label)
        meta_row.addStretch()
        meta_row.addWidget(self.status_badge)

        layout.addWidget(self.project_name_edit)
        layout.addWidget(self.project_description_edit)
        layout.addLayout(meta_row)

        return card

    def _build_directories_card(self) -> QFrame:
        card = QFrame()
        UnifiedStyles.apply_card_style(card)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QLabel("Project resources")
        UnifiedStyles.apply_typography(header, "headline-small")
        layout.addWidget(header)

        helper = QLabel("Tell the editor where to find your media. These folders are used across all tabs.")
        UnifiedStyles.apply_typography(helper, "body-small")
        layout.addWidget(helper)

        grid = QGridLayout()
        grid.setSpacing(12)
        layout.addLayout(grid)

        self.directory_inputs: Dict[str, QLineEdit] = {}

        self._add_directory_field(grid, 0, "Audio folder", "audio", self._browse_audio_directory)
        self._add_directory_field(grid, 1, "Image folder", "image", self._browse_image_directory)
        self._add_directory_field(grid, 2, "Subtitle folder", "subtitle", self._browse_subtitle_directory)
        self._add_directory_field(grid, 3, "Output folder", "output", self._browse_output_directory)

        return card

    def _add_directory_field(self, grid: QGridLayout, row: int, label: str, key: str, handler) -> None:
        caption = QLabel(label)
        UnifiedStyles.apply_typography(caption, "label-small")
        grid.addWidget(caption, row, 0)

        field_layout = QHBoxLayout()
        field_layout.setSpacing(8)

        line_edit = QLineEdit()
        line_edit.setPlaceholderText("Select a folder…")
        line_edit.textChanged.connect(lambda value, slot_key=key: self._on_directory_changed(slot_key, value))
        field_layout.addWidget(line_edit, 1)

        browse_btn = QPushButton("Browse")
        UnifiedStyles.apply_button_style(browse_btn, "outline", "small")
        browse_btn.clicked.connect(handler)
        field_layout.addWidget(browse_btn)

        grid.addLayout(field_layout, row, 1)
        self.directory_inputs[key] = line_edit

    def _build_resources_card(self) -> QFrame:
        card = QFrame()
        UnifiedStyles.apply_card_style(card)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header_row = QHBoxLayout()
        title = QLabel("Resource overview")
        UnifiedStyles.apply_typography(title, "headline-small")
        header_row.addWidget(title)
        header_row.addStretch()

        self.refresh_resources_btn = QPushButton("Refresh counts")
        UnifiedStyles.apply_button_style(self.refresh_resources_btn, "secondary", "small")
        self.refresh_resources_btn.clicked.connect(self._refresh_resource_summary)
        header_row.addWidget(self.refresh_resources_btn)
        layout.addLayout(header_row)

        grid = QGridLayout()
        grid.setSpacing(20)
        layout.addLayout(grid)

        self.resource_labels: Dict[str, QLabel] = {}
        resource_titles = {
            "audio": "Audio files",
            "image": "Image files",
            "subtitle": "Subtitle files",
        }
        for index, (key, caption) in enumerate(resource_titles.items()):
            card_container = QFrame()
            UnifiedStyles.apply_card_style(card_container)
            inner = QVBoxLayout(card_container)
            inner.setContentsMargins(16, 16, 16, 16)
            inner.setSpacing(6)

            caption_label = QLabel(caption)
            UnifiedStyles.apply_typography(caption_label, "label-small")
            value_label = QLabel("0")
            UnifiedStyles.apply_typography(value_label, "headline-medium")

            inner.addWidget(caption_label)
            inner.addWidget(value_label)
            inner.addStretch()

            grid.addWidget(card_container, 0, index)
            self.resource_labels[key] = value_label

        return card

    def _build_history_card(self) -> QFrame:
        card = QFrame()
        UnifiedStyles.apply_card_style(card)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title_row = QHBoxLayout()
        title = QLabel("Activity history")
        UnifiedStyles.apply_typography(title, "headline-small")
        title_row.addWidget(title)
        title_row.addStretch()

        self.clear_history_btn = QPushButton("Clear history")
        UnifiedStyles.apply_button_style(self.clear_history_btn, "ghost", "small")
        self.clear_history_btn.clicked.connect(self._clear_history)
        title_row.addWidget(self.clear_history_btn)

        layout.addLayout(title_row)

        self.history_list = QListWidget()
        layout.addWidget(self.history_list, 1)

        return card

    def _build_action_bar(self) -> QFrame:
        frame = QFrame()
        UnifiedStyles.apply_card_style(frame)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        self.save_btn = QPushButton("Save project")
        UnifiedStyles.apply_button_style(self.save_btn, "primary")
        self.save_btn.clicked.connect(self._save_current_project)
        layout.addWidget(self.save_btn)

        self.duplicate_btn = QPushButton("Duplicate")
        UnifiedStyles.apply_button_style(self.duplicate_btn, "secondary")
        self.duplicate_btn.clicked.connect(self._duplicate_project)
        layout.addWidget(self.duplicate_btn)

        self.delete_btn = QPushButton("Delete")
        UnifiedStyles.apply_button_style(self.delete_btn, "outline")
        self.delete_btn.clicked.connect(self._delete_project)
        layout.addWidget(self.delete_btn)

        layout.addStretch()

        self.open_media_btn = QPushButton("Open media folders")
        UnifiedStyles.apply_button_style(self.open_media_btn, "ghost")
        self.open_media_btn.clicked.connect(self._open_media_folders)
        layout.addWidget(self.open_media_btn)

        return frame

    # ------------------------------------------------------------------
    # Project loading and binding
    # ------------------------------------------------------------------
    def _get_projects_directory(self) -> Path:
        base = Path.home() / ".vibe-render" / "projects"
        base.mkdir(parents=True, exist_ok=True)
        return base

    def _load_projects(self) -> None:
        self.projects = []
        for path in sorted(self.projects_directory.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                with path.open("r", encoding="utf-8") as handle:
                    data = json.load(handle)
                record = ProjectRecord.from_dict(data, source=path)
                self.projects.append(record)
            except Exception:
                continue

        self._populate_project_list()

    def _populate_project_list(self, query: str = "") -> None:
        self.project_list.blockSignals(True)
        self.project_list.clear()

        normalized = query.lower().strip()
        for record in self.projects:
            if normalized and normalized not in record.name.lower():
                continue
            item = QListWidgetItem(record.name)
            subtitle = datetime.fromisoformat(record.updated_at).strftime("%d %b %Y • %H:%M")
            item.setToolTip(f"Last edited {subtitle}")
            item.setData(Qt.UserRole, record.id)
            self.project_list.addItem(item)

        if self.project_list.count() == 0:
            empty = QListWidgetItem("No projects found")
            empty.setFlags(Qt.NoItemFlags)
            self.project_list.addItem(empty)

        self.project_list.blockSignals(False)

    def _filter_project_list(self, text: str) -> None:
        self._populate_project_list(text)

    def _on_project_selection_changed(self) -> None:
        if not self.project_list.selectedItems():
            return
        selected = self.project_list.selectedItems()[0]
        project_id = selected.data(Qt.UserRole)
        record = self._get_project_by_id(project_id)
        if record:
            self._bind_project(record)

    def _get_project_by_id(self, project_id: str) -> Optional[ProjectRecord]:
        for record in self.projects:
            if record.id == project_id:
                return record
        return None

    def _bind_project(self, project: ProjectRecord) -> None:
        self.current_project = project
        self.unsaved_changes = False

        self.project_name_edit.blockSignals(True)
        self.project_description_edit.blockSignals(True)

        self.project_name_edit.setText(project.name)
        self.project_description_edit.setPlainText(project.description)

        for key, field in self.directory_inputs.items():
            field.blockSignals(True)
            field.setText(project.directories.get(key, ""))
            field.blockSignals(False)

        self._update_metadata_labels()
        self._update_resource_labels()
        self._populate_history()
        self._update_save_button_state()

        self.project_name_edit.blockSignals(False)
        self.project_description_edit.blockSignals(False)

    def _update_metadata_labels(self) -> None:
        created = datetime.fromisoformat(self.current_project.created_at).strftime("%d %b %Y • %H:%M")
        updated = datetime.fromisoformat(self.current_project.updated_at).strftime("%d %b %Y • %H:%M")
        self.created_label.setText(f"Created {created}")
        self.updated_label.setText(f"Last updated {updated}")
        status = "Unsaved changes" if self.unsaved_changes else "Up to date"
        self.status_badge.setText(status.upper())

    def _populate_history(self) -> None:
        self.history_list.clear()
        if not self.current_project.history:
            placeholder = QListWidgetItem("History is empty")
            placeholder.setFlags(Qt.NoItemFlags)
            self.history_list.addItem(placeholder)
            return

        for entry in self.current_project.history:
            stamp = datetime.fromisoformat(entry["timestamp"]).strftime("%d %b %Y • %H:%M")
            item = QListWidgetItem(f"{stamp} – {entry['event']}")
            self.history_list.addItem(item)

    def _update_resource_labels(self) -> None:
        for key, label in self.resource_labels.items():
            label.setText(str(self.current_project.resources.get(key, 0)))

    def _update_save_button_state(self) -> None:
        self.save_btn.setEnabled(self.unsaved_changes)
        self.delete_btn.setEnabled(self.current_project.file_path is not None)
        self.duplicate_btn.setEnabled(self.current_project.file_path is not None)

    # ------------------------------------------------------------------
    # Events & mutations
    # ------------------------------------------------------------------
    def _on_project_name_changed(self, value: str) -> None:
        self.current_project.name = value or "Untitled Project"
        self.unsaved_changes = True
        self._update_metadata_labels()

    def _on_project_description_changed(self) -> None:
        self.current_project.description = self.project_description_edit.toPlainText()
        self.unsaved_changes = True
        self._update_metadata_labels()

    def _on_directory_changed(self, key: str, value: str) -> None:
        self.current_project.directories[key] = value
        self.unsaved_changes = True
        self.current_project.push_history(f"Updated {key} directory")
        self._populate_history()
        self._update_metadata_labels()

    def _refresh_resource_summary(self) -> None:
        counts = {"audio": 0, "image": 0, "subtitle": 0}
        audio_suffixes = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"}
        image_suffixes = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
        subtitle_suffixes = {".srt", ".vtt"}

        for key, directory in self.current_project.directories.items():
            if not directory:
                continue
            path = Path(directory)
            if not path.exists():
                continue
            try:
                for item in path.iterdir():
                    if item.is_file():
                        suffix = item.suffix.lower()
                        if suffix in audio_suffixes:
                            counts["audio"] += 1
                        if suffix in image_suffixes:
                            counts["image"] += 1
                        if suffix in subtitle_suffixes:
                            counts["subtitle"] += 1
            except Exception:
                continue

        self.current_project.resources = counts
        self.current_project.push_history("Refreshed resource counts")
        self.unsaved_changes = True
        self._update_resource_labels()
        self._populate_history()
        self._update_metadata_labels()

    def _clear_history(self) -> None:
        self.current_project.history.clear()
        self.current_project.push_history("History cleared")
        self.unsaved_changes = True
        self._populate_history()
        self._update_metadata_labels()

    # ------------------------------------------------------------------
    # Buttons
    # ------------------------------------------------------------------
    def _create_project_flow(self) -> None:
        if self.unsaved_changes and not self._confirm_discard_changes():
            return
        record = ProjectRecord.new()
        self.projects.insert(0, record)
        self._populate_project_list(self.search_input.text())
        self.project_list.clearSelection()
        self._bind_project(record)
        self.current_project.push_history("Project initialised")
        self._populate_history()
        self._update_save_button_state()

    def _save_current_project(self) -> None:
        if not self.current_project.name.strip():
            QMessageBox.warning(self, "Save project", "Please enter a project name before saving.")
            return

        self.current_project.updated_at = datetime.now().isoformat()
        payload = self.current_project.to_dict()

        target_path = self.current_project.file_path
        if target_path is None:
            target_path = self.projects_directory / f"{self.current_project.id}.json"
            self.current_project.file_path = target_path

        try:
            with target_path.open("w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2)
        except Exception as exc:
            QMessageBox.critical(self, "Save project", f"Failed to save project:\n{exc}")
            return

        self.current_project.push_history("Project saved")
        self.unsaved_changes = False
        self._populate_history()
        self._update_metadata_labels()
        self._update_save_button_state()
        self._load_projects()

    def _duplicate_project(self) -> None:
        clone = ProjectRecord.from_dict(self.current_project.to_dict())
        clone.id = str(uuid.uuid4())
        clone.name = f"{clone.name} Copy"
        clone.created_at = datetime.now().isoformat()
        clone.updated_at = clone.created_at
        clone.history = []
        clone.push_history("Duplicated from existing project")
        clone.file_path = None
        self.projects.insert(0, clone)
        self._populate_project_list(self.search_input.text())
        self.project_list.clearSelection()
        self._bind_project(clone)
        self.unsaved_changes = True
        self._update_save_button_state()

    def _delete_project(self) -> None:
        if not self.current_project.file_path or not self.current_project.file_path.exists():
            QMessageBox.warning(self, "Delete project", "Save the project before deleting it.")
            return
        confirm = QMessageBox.question(
            self,
            "Delete project",
            "This will permanently remove the saved project record. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return
        try:
            self.current_project.file_path.unlink()
        except Exception as exc:
            QMessageBox.critical(self, "Delete project", f"Failed to delete project:\n{exc}")
            return
        self.projects = [p for p in self.projects if p.id != self.current_project.id]
        self._populate_project_list(self.search_input.text())
        self._create_project_flow()

    def _open_media_folders(self) -> None:
        directories = [path for path in self.current_project.directories.values() if path]
        if not directories:
            QMessageBox.information(self, "Open folders", "No media folders configured.")
            return
        for directory in directories:
            QFileDialog.getOpenFileName(self, "Folder preview", directory)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _browse_audio_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select audio directory")
        if directory:
            self.directory_inputs["audio"].setText(directory)

    def _browse_image_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select image directory")
        if directory:
            self.directory_inputs["image"].setText(directory)

    def _browse_subtitle_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select subtitle directory")
        if directory:
            self.directory_inputs["subtitle"].setText(directory)

    def _browse_output_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select output directory")
        if directory:
            self.directory_inputs["output"].setText(directory)

    def _confirm_discard_changes(self) -> bool:
        if not self.unsaved_changes:
            return True
        response = QMessageBox.question(
            self,
            "Discard changes",
            "You have unsaved changes. Discard them?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return response == QMessageBox.Yes

    def closeEvent(self, event) -> None:  # type: ignore[override]
        if not self._confirm_discard_changes():
            event.ignore()
            return
        super().closeEvent(event)

    def refresh_stylesheet(self) -> None:
        UnifiedStyles.refresh_stylesheet(self)
