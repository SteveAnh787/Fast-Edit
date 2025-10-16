"""
Automation Tab - Tab tự động hoá với batch rename và subtitle generation
"""

from pathlib import Path
from typing import List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox, QCheckBox,
    QTextEdit, QFileDialog, QMessageBox, QScrollArea
)
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QFont

from src.core.batch_rename import BatchRenamer, RenameResult
from src.core.subtitle_generator import SubtitleGenerator, SubtitleResult
from src.ui.unified_styles import UnifiedStyles


class RenameWorker(QObject):
    finished = Signal(list, str)
    error = Signal(str)

    def __init__(
        self,
        renamer: BatchRenamer,
        directory: str,
        asset_type: str,
        prefix: str,
        start_index: int,
        pad_width: int,
        lowercase_extension: bool,
    ) -> None:
        super().__init__()
        self._renamer = renamer
        self._directory = directory
        self.asset_type = asset_type
        self._prefix = prefix
        self._start_index = start_index
        self._pad_width = pad_width
        self._lowercase_extension = lowercase_extension

    def run(self) -> None:
        try:
            results = self._renamer.rename_files(
                directory=self._directory,
                asset_type=self.asset_type,
                prefix=self._prefix,
                start_index=self._start_index,
                pad_width=self._pad_width,
                separator="_",
                lowercase_extension=self._lowercase_extension,
            )
        except Exception as exc:  # pragma: no cover - filesystem edge cases
            self.error.emit(str(exc))
            return

        self.finished.emit(results, self.asset_type)


class SubtitleWorker(QObject):
    finished = Signal(list, str)
    error = Signal(str)

    def __init__(
        self,
        generator: SubtitleGenerator,
        audio_directory: str,
        subtitle_directory: str,
        model_id: str,
        language: Optional[str],
        translate_to_english: bool,
        threads: Optional[int],
    ) -> None:
        super().__init__()
        self._generator = generator
        self._audio_directory = audio_directory
        self._subtitle_directory = subtitle_directory
        self._model_id = model_id
        self._language = language
        self._translate_to_english = translate_to_english
        self._threads = threads

    def run(self) -> None:
        try:
            results = self._generator.generate_subtitles_batch(
                audio_directory=self._audio_directory,
                subtitle_directory=self._subtitle_directory,
                model_id=self._model_id,
                language=self._language,
                translate_to_english=self._translate_to_english,
                threads=self._threads,
            )
        except Exception as exc:  # pragma: no cover - whisper runtime errors
            self.error.emit(str(exc))
            return

        self.finished.emit(results, self._subtitle_directory)

class AutomationTab(QWidget):
    """Tab chứa các tính năng tự động hoá"""
    
    def __init__(self):
        super().__init__()
        self.batch_renamer = BatchRenamer()
        self.subtitle_generator = SubtitleGenerator()
        self._threads: List[QThread] = []
        self._workers: List[QObject] = []
        self._group_boxes: List[QGroupBox] = []
        self._header_labels: List[QLabel] = []
        self._section_titles: List[QLabel] = []
        self._overline_labels: List[QLabel] = []
        self._caption_labels: List[QLabel] = []
        self._status_labels: List[QLabel] = []
        self._input_widgets: List[QWidget] = []
        self._button_configs: List[tuple] = []
        self._text_panels: List[QTextEdit] = []
        self._checkboxes: List[QCheckBox] = []
        self.init_ui()
        self.refresh_theme()

    # ------------------------------------------------------------------
    # Thread helpers
    # ------------------------------------------------------------------
    def _start_thread(self, worker: QObject, on_finished, on_error) -> None:
        thread = QThread(self)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(on_finished, Qt.QueuedConnection)
        worker.error.connect(on_error, Qt.QueuedConnection)

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

        # Worker deletion handled in worker thread via deleteLater connection.
        
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
        header.setFont(QFont("Space Grotesk", 11, QFont.Bold))
        self._apply_header_label_style(header)
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
        self._apply_group_style(group)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(16)
        
        # Header with asset type selector
        header_layout = QHBoxLayout()
        title = QLabel("Batch Rename")
        title.setFont(QFont("Space Grotesk", 14, QFont.Bold))
        self._apply_section_title_style(title)
        
        self.rename_asset_type = QComboBox()
        self.rename_asset_type.addItems(["Audio", "Image"])
        self.rename_asset_type.currentTextChanged.connect(self._update_rename_defaults)
        self.apply_input_style(self.rename_asset_type)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.rename_asset_type)
        layout.addLayout(header_layout)
        
        # Directory selection
        dir_layout = QVBoxLayout()
        dir_label = QLabel("TARGET DIRECTORY")
        self._apply_overline_style(dir_label)
        
        dir_input_layout = QHBoxLayout()
        self.rename_directory = QLineEdit()
        self.rename_directory.setPlaceholderText("Directory path")
        
        dir_browse_btn = QPushButton("Browse")
        dir_browse_btn.clicked.connect(self.browse_rename_directory)
        
        self.apply_input_style(self.rename_directory)
        self.apply_button_style(dir_browse_btn, "outline", "small")
        
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
        self._apply_overline_style(prefix_label)
        self.rename_prefix = QLineEdit()
        self.rename_prefix.setPlaceholderText("audio")
        self.apply_input_style(self.rename_prefix)
        
        # Start index
        start_label = QLabel("START FROM")
        self._apply_overline_style(start_label)
        self.rename_start_index = QLineEdit()
        self.rename_start_index.setPlaceholderText("1")
        self.apply_input_style(self.rename_start_index)
        
        # Pad width
        pad_label = QLabel("PAD WIDTH")
        self._apply_overline_style(pad_label)
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
        self._apply_checkbox_style(self.rename_lowercase)
        layout.addWidget(self.rename_lowercase)
        
        # Rename button
        self.rename_btn = QPushButton("Rename Now")
        self.rename_btn.clicked.connect(self.start_batch_rename)
        self.apply_button_style(self.rename_btn, "primary")
        layout.addWidget(self.rename_btn)
        
        # Status and results
        self.rename_status = QLabel("")
        self._apply_status_style(self.rename_status)
        layout.addWidget(self.rename_status)
        
        self.rename_results = QTextEdit()
        self.rename_results.setMaximumHeight(120)
        self._apply_text_panel_style(self.rename_results)
        self.rename_results.hide()
        layout.addWidget(self.rename_results)

        self._update_rename_defaults()
        return group
        
    def create_subtitle_generation_widget(self):
        """Create subtitle generation widget"""
        group = QGroupBox()
        self._apply_group_style(group)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(16)
        
        # Header
        title = QLabel("Auto Subtitle Generation")
        title.setFont(QFont("Space Grotesk", 14, QFont.Bold))
        self._apply_section_title_style(title)
        layout.addWidget(title)
        
        # Audio directory
        audio_layout = QVBoxLayout()
        audio_label = QLabel("AUDIO DIRECTORY")
        self._apply_overline_style(audio_label)
        
        audio_input_layout = QHBoxLayout()
        self.audio_directory = QLineEdit()
        self.audio_directory.setPlaceholderText("Path to audio folder (.wav)")
        
        audio_browse_btn = QPushButton("Browse")
        audio_browse_btn.clicked.connect(self.browse_audio_directory)
        
        self.apply_input_style(self.audio_directory)
        self.apply_button_style(audio_browse_btn, "outline", "small")
        
        audio_input_layout.addWidget(self.audio_directory)
        audio_input_layout.addWidget(audio_browse_btn)
        
        audio_layout.addWidget(audio_label)
        audio_layout.addLayout(audio_input_layout)
        layout.addLayout(audio_layout)
        
        # Model selection
        model_layout = QVBoxLayout()
        model_label = QLabel("WHISPER MODEL")
        self._apply_overline_style(model_label)
        
        self.whisper_model = QComboBox()
        for model in self.subtitle_generator.get_available_models():
            label_parts = [model["name"], f"· {model['size_mb']}MB"]
            if model.get("recommended"):
                label_parts.append("(Recommended)")
            if model.get("available"):
                label_parts.append("[Installed]")
            label = " ".join(label_parts)
            self.whisper_model.addItem(label, model["id"])

        # Default to recommended model if available
        recommended_index = next(
            (i for i in range(self.whisper_model.count()) if "Recommended" in self.whisper_model.itemText(i)),
            0,
        )
        self.whisper_model.setCurrentIndex(recommended_index)
        self.apply_input_style(self.whisper_model)
        
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.whisper_model)
        
        info_label = QLabel("Models stored locally, auto-download if not available.")
        self._apply_caption_style(info_label)
        model_layout.addWidget(info_label)
        
        layout.addLayout(model_layout)
        
        # Subtitle directory
        sub_layout = QVBoxLayout()
        sub_label = QLabel("SUBTITLE DIRECTORY")
        self._apply_overline_style(sub_label)
        
        sub_input_layout = QHBoxLayout()
        self.subtitle_directory = QLineEdit()
        self.subtitle_directory.setPlaceholderText("Default: create subtitles folder in audio directory")
        
        sub_browse_btn = QPushButton("Browse")
        sub_browse_btn.clicked.connect(self.browse_subtitle_directory)
        
        self.apply_input_style(self.subtitle_directory)
        self.apply_button_style(sub_browse_btn, "outline", "small")
        
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
        self._apply_overline_style(lang_label)
        self.language = QLineEdit()
        self.language.setPlaceholderText("vi, en, ...")
        self.apply_input_style(self.language)
        
        # Threads
        threads_label = QLabel("THREADS")
        self._apply_overline_style(threads_label)
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
        self._apply_checkbox_style(self.translate_to_english)
        layout.addWidget(self.translate_to_english)
        
        # Generate button
        self.generate_btn = QPushButton("Generate Subtitles")
        self.generate_btn.clicked.connect(self.start_subtitle_generation)
        self.apply_button_style(self.generate_btn, "primary")
        layout.addWidget(self.generate_btn)
        
        # Status and results
        self.subtitle_status = QLabel("")
        self._apply_status_style(self.subtitle_status)
        layout.addWidget(self.subtitle_status)
        
        self.subtitle_results = QTextEdit()
        self.subtitle_results.setMaximumHeight(200)
        self._apply_text_panel_style(self.subtitle_results)
        self.subtitle_results.hide()
        layout.addWidget(self.subtitle_results)
        
        return group
    
    def apply_input_style(self, widget):
        """Apply consistent input styling"""
        from PySide6.QtWidgets import QComboBox, QTextEdit

        palette = UnifiedStyles.palette()
        widget.setStyleSheet(
            f"""
            QLineEdit, QComboBox, QTextEdit {{
                background-color: {palette.surface};
                border: 1.5px solid {palette.outline};
                border-radius: 8px;
                padding: 10px 14px;
                color: {palette.text_primary};
                font-size: 13px;
                min-height: 40px;
                selection-background-color: {palette.primary};
                selection-color: {palette.highlight_text};
            }}
            QLineEdit:hover, QComboBox:hover, QTextEdit:hover {{
                border-color: {palette.text_secondary};
            }}
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus {{
                border-color: {palette.primary};
                border-width: 2px;
                outline: none;
                background-color: {palette.surface};
            }}
            QComboBox::drop-down {{ border: none; width: 24px; }}
            QComboBox::down-arrow {{ image: none; width: 0; height: 0; }}
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
            "preset": "ghost",
        }
        UnifiedStyles.apply_button_style(button, scheme_map.get(color_scheme, color_scheme), size)
        if all(button is not btn for btn, _, __ in self._button_configs):
            self._button_configs.append((button, color_scheme, size))

    def _apply_group_style(self, group: QGroupBox) -> None:
        palette = UnifiedStyles.palette()
        group.setStyleSheet(
            f"""
            QGroupBox {{
                border: 1.5px solid {palette.outline};
                border-radius: 12px;
                background-color: {palette.surface};
                padding: 24px;
                margin-top: 8px;
                font-weight: 600;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 16px;
                top: -8px;
                padding: 0 8px;
                background-color: {palette.surface};
                color: {palette.text_primary};
            }}
        """
        )
        if group not in self._group_boxes:
            self._group_boxes.append(group)

    def _apply_header_label_style(self, label: QLabel) -> None:
        palette = UnifiedStyles.palette()
        label.setStyleSheet(
            f"""
            color: {palette.text_muted};
            text-transform: uppercase;
            letter-spacing: 0.1em;
            font-weight: 700;
            font-size: 11px;
            margin-bottom: 16px;
        """
        )
        if label not in self._header_labels:
            self._header_labels.append(label)

    def _apply_section_title_style(self, label: QLabel) -> None:
        palette = UnifiedStyles.palette()
        label.setStyleSheet(f"color: {palette.text_primary}; font-weight: 600; font-size: 15px; line-height: 1.4;")
        if label not in self._section_titles:
            self._section_titles.append(label)

    def _apply_overline_style(self, label: QLabel) -> None:
        palette = UnifiedStyles.palette()
        label.setStyleSheet(
            f"""
            color: {palette.text_muted};
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 6px;
        """
        )
        if label not in self._overline_labels:
            self._overline_labels.append(label)

    def _apply_caption_style(self, label: QLabel) -> None:
        palette = UnifiedStyles.palette()
        label.setStyleSheet(f"color: {palette.text_secondary}; font-size: 12px; line-height: 1.5;")
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
                background-color: {palette.surface_container};
                border: 1.5px solid {palette.outline};
                border-radius: 8px;
                color: {palette.text_primary};
                font-size: 12px;
                padding: 12px;
                line-height: 1.5;
                font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
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
                font-size: 13px;
                font-weight: 500;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1.5px solid {palette.outline};
                border-radius: 4px;
                background-color: {palette.surface};
            }}
            QCheckBox::indicator:hover {{
                border-color: {palette.primary};
            }}
            QCheckBox::indicator:checked {{
                background-color: {palette.primary};
                border-color: {palette.primary};
            }}
            QCheckBox::indicator:checked:hover {{
                background-color: {palette.primary_alt};
            }}
        """
        )
        if checkbox not in self._checkboxes:
            self._checkboxes.append(checkbox)

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

        for widget in self._input_widgets:
            self.apply_input_style(widget)

        for button, scheme, size in self._button_configs:
            self.apply_button_style(button, scheme, size)
    
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
        directory = self.rename_directory.text().strip()
        if not directory:
            QMessageBox.warning(self, "Batch Rename", "Please select a directory first.")
            return

        if not Path(directory).exists():
            QMessageBox.warning(self, "Batch Rename", "Selected directory does not exist.")
            return

        asset_type = self.rename_asset_type.currentText().lower()
        prefix = "audio" if asset_type == "audio" else "image"
        self.rename_prefix.setText(prefix)

        start_index = self._safe_int(self.rename_start_index.text(), default=1, minimum=1)
        pad_width = self._safe_int(self.rename_pad_width.text(), default=3, minimum=2)
        lowercase_extension = self.rename_lowercase.isChecked()

        self.rename_btn.setEnabled(False)
        self.rename_status.setText("Renaming files…")
        self.rename_results.clear()
        self.rename_results.show()

        worker = RenameWorker(
            self.batch_renamer,
            directory=directory,
            asset_type=asset_type,
            prefix=prefix,
            start_index=start_index,
            pad_width=pad_width,
            lowercase_extension=lowercase_extension,
        )

        self._start_thread(worker, self._handle_rename_finished, self._handle_rename_error)

    def _handle_rename_finished(self, results: List[RenameResult], asset_type: str) -> None:
        self.rename_btn.setEnabled(True)

        if not results:
            self.rename_status.setText("No files matched the selected type.")
            self.rename_results.hide()
            return

        success_results = [result for result in results if result.success]
        failed_results = [result for result in results if not result.success]

        asset_label = "audio" if asset_type == "audio" else "image"
        total = len(results)
        changed_results = [
            result
            for result in success_results
            if result.new_path and Path(result.original_path).name != Path(result.new_path).name
        ]
        renamed_count = len(changed_results)

        if renamed_count == 0 and success_results and not failed_results:
            self.rename_status.setText("Files already match the desired naming format.")
            QMessageBox.information(
                self,
                "Batch Rename",
                "Tất cả các file đã đúng định dạng đặt tên nên không cần đổi tên thêm.",
            )
        else:
            self.rename_status.setText(
                f"Renamed {renamed_count}/{total} {asset_label} files."
            )

        lines: List[str] = []
        for result in results:
            original = Path(result.original_path).name if result.original_path else "<unknown>"
            if result.success and result.new_path:
                target = Path(result.new_path).name
                lines.append(f"{original} → {target}")
            else:
                message = result.error or "Unknown error"
                lines.append(f"{original} ✗ {message}")

        if failed_results:
            QMessageBox.warning(
                self,
                "Batch Rename",
                "Some files could not be renamed. Check the details list for more information.",
            )

        self.rename_results.setPlainText("\n".join(lines))

    def _handle_rename_error(self, message: str) -> None:
        self.rename_btn.setEnabled(True)
        self.rename_status.setText("Rename failed.")
        QMessageBox.critical(self, "Batch Rename", message)

    def start_subtitle_generation(self):
        audio_directory = self.audio_directory.text().strip()
        if not audio_directory:
            QMessageBox.warning(self, "Subtitle Generation", "Please select an audio directory.")
            return

        if not Path(audio_directory).exists():
            QMessageBox.warning(self, "Subtitle Generation", "Audio directory does not exist.")
            return

        subtitle_directory = self.subtitle_directory.text().strip()
        if not subtitle_directory:
            subtitle_directory = str(Path(audio_directory) / "subtitles")
            self.subtitle_directory.setText(subtitle_directory)

        model_id = self.whisper_model.currentData() or "base"
        language = self.language.text().strip() or None
        if language:
            language = language.lower()
        translate = self.translate_to_english.isChecked()
        threads_value = self.thread_count.text().strip()
        threads = self._safe_int(threads_value, default=0, minimum=0) if threads_value else None
        if threads == 0:
            threads = None

        self.generate_btn.setEnabled(False)
        self.subtitle_status.setText("Generating subtitles…")
        self.subtitle_results.clear()
        self.subtitle_results.show()

        worker = SubtitleWorker(
            self.subtitle_generator,
            audio_directory=audio_directory,
            subtitle_directory=subtitle_directory,
            model_id=model_id,
            language=language,
            translate_to_english=translate,
            threads=threads,
        )

        self._start_thread(worker, self._handle_subtitle_finished, self._handle_subtitle_error)

    def _handle_subtitle_finished(self, results: List[SubtitleResult], output_directory: str) -> None:
        self.generate_btn.setEnabled(True)

        if not results:
            self.subtitle_status.setText("No audio files found.")
            self.subtitle_results.hide()
            return

        success_results = [result for result in results if result.success]
        failed_results = [result for result in results if not result.success]

        total = len(results)
        success_count = len(success_results)

        if success_count:
            self.subtitle_status.setText(
                f"Generated {success_count}/{total} subtitle files → {output_directory}"
            )
        else:
            self.subtitle_status.setText("Failed to generate subtitles. See details below.")

        lines: List[str] = []
        for result in results:
            audio_name = Path(result.audio_path).name if result.audio_path else "<unknown>"
            if result.success and result.subtitle_path:
                subtitle_name = Path(result.subtitle_path).name
                lines.append(f"{audio_name} → {subtitle_name}")
            else:
                message = result.error or "Unknown error"
                lines.append(f"{audio_name} ✗ {message}")

        if failed_results:
            QMessageBox.warning(
                self,
                "Subtitle Generation",
                "Some subtitles could not be created. Check the log for details.",
            )

        previews: List[str] = []
        for result in success_results[:3]:
            if result.preview_lines:
                previews.append(
                    f"{Path(result.subtitle_path).name if result.subtitle_path else ''}: "
                    + " | ".join(result.preview_lines[:3])
                )
        if previews:
            lines.extend(["", "Preview:"] + previews)

        self.subtitle_results.setPlainText("\n".join(lines))

    def _handle_subtitle_error(self, message: str) -> None:
        self.generate_btn.setEnabled(True)
        self.subtitle_status.setText("Subtitle generation failed.")
        QMessageBox.critical(self, "Subtitle Generation", message)

    def _update_rename_defaults(self) -> None:
        asset_type = self.rename_asset_type.currentText().lower()
        prefix = "audio" if asset_type == "audio" else "image"
        self.rename_prefix.setText(prefix)
        self.rename_start_index.setText("1")
        self.rename_pad_width.setText("3")
        self.rename_lowercase.setChecked(True)

    @staticmethod
    def _safe_int(value: str, default: int, minimum: int = 0) -> int:
        try:
            numeric = int(value)
        except (TypeError, ValueError):
            return default

        if numeric < minimum:
            return minimum or default
        return numeric
