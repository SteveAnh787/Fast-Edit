"""Unified design system inspired by shadcn/ui with a light orange-red palette."""

from __future__ import annotations

from dataclasses import dataclass
from string import Template
from textwrap import dedent
from typing import Dict


class UnifiedTypography:
    """Typography system with Space Grotesk"""
    
    FONT_FAMILY = "'Space Grotesk', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    
    SCALE = {
        # Display - For hero/main titles
        "display-large": {"size": 32, "weight": 400, "line_height": 1.25},
        "display-medium": {"size": 28, "weight": 400, "line_height": 1.29},
        "display-small": {"size": 24, "weight": 400, "line_height": 1.33},
        
        # Headline - For section headers
        "headline-large": {"size": 22, "weight": 500, "line_height": 1.27},
        "headline-medium": {"size": 18, "weight": 500, "line_height": 1.33},
        "headline-small": {"size": 16, "weight": 500, "line_height": 1.50},
        
        # Title - For card titles, tab labels
        "title-large": {"size": 16, "weight": 500, "line_height": 1.50},
        "title-medium": {"size": 14, "weight": 500, "line_height": 1.43},
        "title-small": {"size": 12, "weight": 500, "line_height": 1.33},
        
        # Label - For buttons, form labels
        "label-large": {"size": 12, "weight": 500, "line_height": 1.33},
        "label-medium": {"size": 11, "weight": 500, "line_height": 1.45},
        "label-small": {"size": 10, "weight": 500, "line_height": 1.60},
        
        # Body - For content text
        "body-large": {"size": 14, "weight": 400, "line_height": 1.43},
        "body-medium": {"size": 12, "weight": 400, "line_height": 1.33},
        "body-small": {"size": 11, "weight": 400, "line_height": 1.45},
        
        # Caption - For helper text
        "caption": {"size": 11, "weight": 400, "line_height": 1.45},
        "overline": {"size": 10, "weight": 500, "line_height": 1.60, "letter_spacing": 1.5, "transform": "uppercase"}
    }

@dataclass(frozen=True)
class ThemePalette:
    """Collection of colors for a specific theme."""

    name: str
    surface_dim: str
    surface: str
    surface_bright: str
    surface_container: str
    text_primary: str
    text_secondary: str
    text_muted: str
    outline: str
    outline_variant: str
    primary: str
    primary_alt: str
    accent: str
    highlight: str
    highlight_text: str
    success: str
    warning: str
    error: str
    info: str


class UnifiedStyles:
    """Unified styling system (light-only, shadcn-inspired)."""

    _THEMES: Dict[str, ThemePalette] = {
        "light": ThemePalette(
            name="light",
            surface_dim="#FAFAFA",
            surface="#FFFFFF",
            surface_bright="#FEFEFE",
            surface_container="#F5F5F5",
            text_primary="#1A1A1A",
            text_secondary="#525252",
            text_muted="#A3A3A3",
            outline="#E5E5E5",
            outline_variant="#F5F5F5",
            primary="#F97316",
            primary_alt="#EA580C",
            accent="#FB923C",
            highlight="#F97316",
            highlight_text="#FFFFFF",
            success="#10B981",
            warning="#F59E0B",
            error="#EF4444",
            info="#3B82F6",
        )
    }

    _ACTIVE_THEME = "light"

    @classmethod
    def available_themes(cls) -> Dict[str, ThemePalette]:
        return cls._THEMES

    @classmethod
    def set_theme(cls, mode: str) -> None:
        cls._ACTIVE_THEME = mode if mode in cls._THEMES else "light"

    @classmethod
    def current_theme(cls) -> str:
        return cls._ACTIVE_THEME

    @classmethod
    def palette(cls) -> ThemePalette:
        return cls._THEMES[cls._ACTIVE_THEME]

    @classmethod
    def get_main_stylesheet(cls) -> str:
        palette = cls.palette()
        template = Template(dedent("""
            QWidget {
                background-color: $surface_dim;
                color: $text_primary;
                font-family: $font_family;
                font-size: 13px;
            }

            QLabel { background: transparent; }

            .display-large { font-size: 36px; font-weight: 500; letter-spacing: -0.02em; color: $text_primary; }
            .headline-medium { font-size: 20px; font-weight: 600; color: $text_primary; }
            .headline-small { font-size: 18px; font-weight: 600; color: $text_primary; }
            .title-medium { font-size: 15px; font-weight: 600; color: $text_primary; }
            .body-medium { font-size: 13px; color: $text_secondary; line-height: 1.5; }
            .body-small { font-size: 12px; color: $text_muted; line-height: 1.5; }
            .overline { font-size: 10px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: $text_muted; }

            QPushButton {
                border-radius: 8px;
                font-weight: 500;
                padding: 10px 20px;
                border: none;
                min-height: 40px;
                background-color: $surface;
                color: $text_primary;
                font-size: 13px;
            }
            QPushButton:disabled { background-color: $surface_container; color: $text_muted; opacity: 0.5; }
            QPushButton.btn-primary { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 $primary, stop:1 $primary_alt); color: $highlight_text; font-weight: 600; }
            QPushButton.btn-primary:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 $primary_alt, stop:1 $primary); }
            QPushButton.btn-primary:pressed { background-color: $primary_alt; }
            QPushButton.btn-secondary { background-color: $surface_container; color: $text_primary; border: 1px solid $outline; font-weight: 500; }
            QPushButton.btn-secondary:hover { background-color: $surface_bright; border-color: $outline; }
            QPushButton.btn-outline { background-color: transparent; border: 1.5px solid $outline; color: $text_primary; font-weight: 500; }
            QPushButton.btn-outline:hover { background-color: $surface_container; border-color: $text_secondary; color: $text_primary; }
            QPushButton.btn-ghost { background-color: transparent; color: $text_secondary; padding: 8px 12px; font-weight: 500; }
            QPushButton.btn-ghost:hover { background-color: $surface_container; color: $text_primary; }
            QPushButton.btn-small { min-height: 32px; padding: 6px 14px; font-size: 12px; border-radius: 6px; }
            QPushButton.btn-large { min-height: 48px; padding: 14px 28px; font-size: 14px; font-weight: 600; }

            QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: $surface;
                border: 1.5px solid $outline;
                border-radius: 8px;
                padding: 10px 14px;
                color: $text_primary;
                font-size: 13px;
                min-height: 40px;
                selection-background-color: $primary;
                selection-color: $highlight_text;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: $primary;
                border-width: 2px;
                background-color: $surface;
                outline: none;
            }
            QLineEdit:hover, QTextEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover {
                border-color: $text_secondary;
            }
            QLineEdit::placeholder, QTextEdit::placeholder { color: $text_muted; }
            QComboBox::drop-down { border: none; width: 24px; }
            QComboBox::down-arrow { image: none; width: 0; height: 0; }
            QSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                background: transparent;
                border: none;
                width: 18px;
                padding: 2px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover,
            QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
                background-color: $surface_container;
            }

            .card {
                background-color: $surface;
                border: 1.5px solid $outline;
                border-radius: 12px;
                padding: 24px;
            }
            .card:hover {
                border-color: $text_muted;
                background-color: $surface;
            }
            .card-elevated {
                background-color: $surface;
                border: 1.5px solid $outline;
                border-radius: 12px;
                padding: 24px;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 10px 24px rgba(0, 0, 0, 0.04);
            }

            QTabWidget::pane { border: none; background-color: transparent; margin-top: 8px; }
            QTabBar::tab {
                background-color: transparent;
                color: $text_muted;
                padding: 14px 24px;
                margin-right: 4px;
                border: none;
                border-bottom: 3px solid transparent;
                font-size: 14px;
                font-weight: 600;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                color: $primary;
                border-bottom-color: $primary;
                background-color: transparent;
            }
            QTabBar::tab:hover:!selected {
                color: $text_secondary;
                background-color: $surface_container;
                border-radius: 8px 8px 0 0;
            }

            QListWidget {
                background-color: $surface;
                border: 1.5px solid $outline;
                border-radius: 8px;
                color: $text_primary;
                font-size: 13px;
                padding: 6px;
            }
            QListWidget::item {
                padding: 10px 14px;
                border-radius: 6px;
                margin: 2px 0;
                border: none;
            }
            QListWidget::item:hover {
                background-color: $surface_container;
            }
            QListWidget::item:selected {
                background-color: $primary;
                color: $highlight_text;
                font-weight: 500;
            }

            QScrollBar:vertical {
                background-color: transparent;
                width: 10px;
                border-radius: 5px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background-color: $outline;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: $text_muted;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar:horizontal {
                background-color: transparent;
                height: 10px;
                border-radius: 5px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal {
                background-color: $outline;
                border-radius: 5px;
                min-width: 30px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: $text_muted;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }

            QGroupBox {
                border: 1.5px solid $outline;
                border-radius: 12px;
                background-color: $surface;
                margin-top: 16px;
                padding-top: 24px;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 16px;
                top: 8px;
                padding: 0 8px;
                background-color: $surface;
                color: $text_primary;
            }

            QCheckBox {
                color: $text_secondary;
                font-size: 12px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1.5px solid $outline;
                border-radius: 4px;
                background-color: $surface;
            }
            QCheckBox::indicator:hover {
                border-color: $primary;
            }
            QCheckBox::indicator:checked {
                background-color: $primary;
                border-color: $primary;
                image: none;
            }
            QCheckBox::indicator:checked:hover {
                background-color: $primary_alt;
            }

            .text-success { color: $success; }
            .text-warning { color: $warning; }
            .text-error { color: $error; }
            .text-info { color: $info; }
            .bg-success { background-color: $success; }
            .bg-warning { background-color: $warning; }
            .bg-error { background-color: $error; }
            .bg-info { background-color: $info; }
        """))

        return template.substitute(
            surface_dim=palette.surface_dim,
            text_primary=palette.text_primary,
            font_family=UnifiedTypography.FONT_FAMILY,
            text_secondary=palette.text_secondary,
            text_muted=palette.text_muted,
            surface=palette.surface,
            surface_bright=palette.surface_bright,
            surface_container=palette.surface_container,
            outline=palette.outline,
            outline_variant=palette.outline_variant,
            primary=palette.primary,
            primary_alt=palette.primary_alt,
            accent=palette.accent,
            highlight_text=palette.highlight_text,
            gradient_primary=f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {palette.primary}, stop:1 {palette.primary_alt})",
            gradient_soft=f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {palette.accent}, stop:1 {palette.primary})",
            success=palette.success,
            warning=palette.warning,
            error=palette.error,
            info=palette.info,
        )

    @staticmethod
    def apply_typography(widget, style_name):
        """Apply typography style to widget"""
        widget.setProperty("class", style_name)
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        
    @staticmethod
    def apply_button_style(button, variant="primary", size="medium"):
        """Apply button styling"""
        classes = [f"btn-{variant}"]
        if size != "medium":
            classes.append(f"btn-{size}")
            
        button.setProperty("class", " ".join(classes))
        button.style().unpolish(button)
        button.style().polish(button)
        
    @staticmethod
    def apply_card_style(widget, elevated=False):
        """Apply card styling"""
        class_name = "card-elevated" if elevated else "card"
        widget.setProperty("class", class_name)
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        
    @staticmethod
    def create_icon_label(icon, text="", size="medium"):
        """Create label with icon and text"""
        from PySide6.QtWidgets import QLabel, QHBoxLayout, QWidget
        from PySide6.QtCore import Qt
        
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignCenter)
        
        if size == "small":
            icon_label.setStyleSheet("font-size: 14px;")
        elif size == "large": 
            icon_label.setStyleSheet("font-size: 20px;")
        else:  # medium
            icon_label.setStyleSheet("font-size: 16px;")
            
        layout.addWidget(icon_label)
        
        # Text
        if text:
            text_label = QLabel(text)
            layout.addWidget(text_label)
            
        return container

    @classmethod
    def apply_qpalette(cls, app):
        """Apply Qt palette based on the active theme."""
        from PySide6.QtGui import QColor, QPalette

        palette = cls.palette()
        qt_palette = QPalette()

        qt_palette.setColor(QPalette.Window, QColor(palette.surface_dim))
        qt_palette.setColor(QPalette.WindowText, QColor(palette.text_primary))
        qt_palette.setColor(QPalette.Base, QColor(palette.surface))
        qt_palette.setColor(QPalette.AlternateBase, QColor(palette.surface_bright))
        qt_palette.setColor(QPalette.Text, QColor(palette.text_primary))
        qt_palette.setColor(QPalette.Button, QColor(palette.surface))
        qt_palette.setColor(QPalette.ButtonText, QColor(palette.text_primary))
        qt_palette.setColor(QPalette.PlaceholderText, QColor(palette.text_muted))
        qt_palette.setColor(QPalette.Highlight, QColor(palette.highlight))
        qt_palette.setColor(QPalette.HighlightedText, QColor(palette.highlight_text))
        qt_palette.setColor(QPalette.Link, QColor(palette.primary))

        app.setPalette(qt_palette)

    @classmethod
    def refresh_stylesheet(cls, widget):
        """Apply the global stylesheet to a widget subtree."""
        widget.setStyleSheet(cls.get_main_stylesheet())
