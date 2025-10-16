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
            surface_dim="#F7F8FA",
            surface="#FFFFFF",
            surface_bright="#FFF7F1",
            surface_container="#FFF1E9",
            text_primary="#2F1E16",
            text_secondary="#6B463B",
            text_muted="#9E7768",
            outline="#F3C3B2",
            outline_variant="#F8D6C6",
            primary="#F97316",
            primary_alt="#EF4444",
            accent="#FB923C",
            highlight="#F97316",
            highlight_text="#FFFFFF",
            success="#22C55E",
            warning="#F97316",
            error="#EF4444",
            info="#FACC15",
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
                font-size: 12px;
            }

            QLabel { background: transparent; }

            .display-large { font-size: 36px; font-weight: 500; letter-spacing: -0.02em; color: $text_primary; }
            .headline-medium { font-size: 20px; font-weight: 600; color: $text_primary; }
            .headline-small { font-size: 18px; font-weight: 600; color: $text_primary; }
            .title-medium { font-size: 15px; font-weight: 600; color: $text_primary; }
            .body-medium { font-size: 13px; color: $text_secondary; }
            .body-small { font-size: 12px; color: $text_muted; }
            .overline { font-size: 10px; font-weight: 600; letter-spacing: 0.16em; text-transform: uppercase; color: $text_muted; }

            QPushButton {
                border-radius: 10px;
                font-weight: 600;
                padding: 10px 22px;
                border: none;
                min-height: 40px;
                background-color: $surface;
                color: $text_primary;
            }
            QPushButton:disabled { background-color: $surface_bright; color: $text_muted; }
            QPushButton.btn-primary { background: $gradient_primary; color: $highlight_text; }
            QPushButton.btn-primary:hover { background: $gradient_soft; }
            QPushButton.btn-primary:pressed { background-color: $primary_alt; }
            QPushButton.btn-secondary { background-color: $surface_bright; color: $text_primary; }
            QPushButton.btn-secondary:hover { background-color: $surface_container; }
            QPushButton.btn-outline { background-color: transparent; border: 1px solid $outline; color: $text_primary; }
            QPushButton.btn-outline:hover { background-color: $surface_bright; border-color: $primary; }
            QPushButton.btn-ghost { background-color: transparent; color: $text_secondary; }
            QPushButton.btn-ghost:hover { background-color: $surface_bright; color: $text_primary; }
            QPushButton.btn-small { min-height: 32px; padding: 6px 16px; font-size: 11px; }
            QPushButton.btn-large { min-height: 48px; padding: 14px 32px; font-size: 14px; }

            QLineEdit, QTextEdit, QComboBox {
                background-color: $surface;
                border: 1px solid $outline_variant;
                border-radius: 10px;
                padding: 12px 16px;
                color: $text_primary;
                font-size: 12px;
                min-height: 40px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus { border-color: $primary; background-color: $surface_bright; outline: none; }
            QLineEdit::placeholder { color: $text_muted; }

            .card { background-color: $surface; border: 1px solid rgba(249, 203, 185, 0.6); border-radius: 18px; padding: 28px; }
            .card:hover { border-color: $outline; background-color: $surface_bright; }
            .card-elevated { background-color: $surface; border: 1px solid rgba(249, 203, 185, 0.75); border-radius: 20px; padding: 28px; box-shadow: 0 24px 55px -32px rgba(239, 68, 68, 0.35); }

            QTabWidget::pane { border: none; background-color: transparent; }
            QTabBar::tab { background-color: transparent; color: $text_muted; padding: 16px 20px; margin-right: 6px; border-bottom: 2px solid transparent; font-size: 14px; font-weight: 600; min-width: 120px; }
            QTabBar::tab:selected { color: $primary; border-bottom-color: $primary; background-color: $surface; }
            QTabBar::tab:hover:!selected { color: $text_secondary; background-color: $surface_bright; }

            QListWidget { background-color: $surface; border: 1px solid $outline_variant; border-radius: 14px; color: $text_primary; font-size: 12px; padding: 10px; }
            QListWidget::item { padding: 12px 16px; border-radius: 10px; margin: 2px 0; border: none; }
            QListWidget::item:hover { background-color: $surface_bright; }
            QListWidget::item:selected { background-color: $primary; color: $highlight_text; }

            QScrollBar:vertical { background-color: $surface; width: 12px; border-radius: 6px; margin: 0; }
            QScrollBar::handle:vertical { background-color: $outline_variant; border-radius: 6px; min-height: 20px; margin: 2px; }
            QScrollBar::handle:vertical:hover { background-color: $outline; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }

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
