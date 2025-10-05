"""
Unified Design System - Typography, Icons và Styling thống nhất
"""

class MaterialIcons:
    """Google Material Icons collection"""
    
    # Navigation & Actions
    HOME = "🏠"
    SETTINGS = "⚙️"
    SEARCH = "🔍"
    ADD = "➕"
    EDIT = "✏️"
    DELETE = "🗑️"
    SAVE = "💾"
    LOAD = "📂"
    EXPORT = "📤"
    IMPORT = "📥"
    
    # Project & Files
    PROJECT = "📁"
    FOLDER = "📂"
    FILE = "📄"
    AUDIO = "🎵"
    VIDEO = "🎬"
    IMAGE = "🖼️"
    SUBTITLE = "💬"
    
    # Media & Content
    PLAY = "▶️"
    PAUSE = "⏸️"
    STOP = "⏹️"
    RECORD = "⏺️"
    VOLUME = "🔊"
    CAMERA = "📷"
    
    # Status & Feedback
    SUCCESS = "✅"
    WARNING = "⚠️"
    ERROR = "❌"
    INFO = "ℹ️"
    LOADING = "⏳"
    
    # Tools & Features
    MAGIC_WAND = "🪄"
    TARGET = "🎯"
    SCAN = "🔎"
    VALIDATE = "✔️"
    PATTERN = "🧩"
    AUTOMATION = "🤖"
    EFFECT = "✨"
    RENDER = "🎞️"
    
    # UI Elements
    MENU = "☰"
    CLOSE = "✖️"
    EXPAND = "🔽"
    COLLAPSE = "🔼"
    REFRESH = "🔄"
    CLEAR = "🧹"

class UnifiedTypography:
    """Typography system với Google Fonts style"""
    
    FONT_FAMILY = "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    
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

class ModernColors:
    """Modern color palette với dark theme focus"""
    
    # Surface colors
    SURFACE_DIM = "#111827"           # Main background
    SURFACE = "#1f2937"               # Cards, elevated elements  
    SURFACE_BRIGHT = "#374151"        # Hover states
    SURFACE_CONTAINER = "#4b5563"     # Containers
    
    # On-surface (text on backgrounds)
    ON_SURFACE = "#f9fafb"           # Primary text
    ON_SURFACE_VARIANT = "#d1d5db"   # Secondary text
    OUTLINE = "#6b7280"              # Borders, dividers
    OUTLINE_VARIANT = "#4b5563"      # Subtle borders
    
    # Primary colors (Brand)
    PRIMARY = "#6366f1"              # Main brand color
    ON_PRIMARY = "#ffffff"           # Text on primary
    PRIMARY_CONTAINER = "#4f46e5"    # Primary button hover
    
    # Secondary colors
    SECONDARY = "#10b981"            # Success/positive actions
    ON_SECONDARY = "#ffffff"
    SECONDARY_CONTAINER = "#059669"
    
    # Tertiary colors  
    TERTIARY = "#8b5cf6"            # Accent color
    ON_TERTIARY = "#ffffff"
    TERTIARY_CONTAINER = "#7c3aed"
    
    # Semantic colors
    ERROR = "#ef4444"
    ON_ERROR = "#ffffff" 
    WARNING = "#f59e0b"
    ON_WARNING = "#ffffff"
    INFO = "#06b6d4"
    ON_INFO = "#ffffff"
    SUCCESS = "#10b981"
    ON_SUCCESS = "#ffffff"

class UnifiedStyles:
    """Unified styling system"""
    
    @staticmethod
    def get_main_stylesheet():
        return f"""
        /* === GLOBAL RESET === */
        QWidget {{
            background-color: {ModernColors.SURFACE_DIM};
            color: {ModernColors.ON_SURFACE};
            font-family: {UnifiedTypography.FONT_FAMILY};
            font-size: 12px;
        }}
        
        /* === TYPOGRAPHY CLASSES === */
        .display-large {{ font-size: 32px; font-weight: 400; line-height: 1.25; color: {ModernColors.ON_SURFACE}; }}
        .display-medium {{ font-size: 28px; font-weight: 400; line-height: 1.29; color: {ModernColors.ON_SURFACE}; }}
        .display-small {{ font-size: 24px; font-weight: 400; line-height: 1.33; color: {ModernColors.ON_SURFACE}; }}
        
        .headline-large {{ font-size: 22px; font-weight: 500; line-height: 1.27; color: {ModernColors.ON_SURFACE}; }}
        .headline-medium {{ font-size: 18px; font-weight: 500; line-height: 1.33; color: {ModernColors.ON_SURFACE}; }}
        .headline-small {{ font-size: 16px; font-weight: 500; line-height: 1.50; color: {ModernColors.ON_SURFACE}; }}
        
        .title-large {{ font-size: 16px; font-weight: 500; line-height: 1.50; color: {ModernColors.ON_SURFACE}; }}
        .title-medium {{ font-size: 14px; font-weight: 500; line-height: 1.43; color: {ModernColors.ON_SURFACE}; }}
        .title-small {{ font-size: 12px; font-weight: 500; line-height: 1.33; color: {ModernColors.ON_SURFACE}; }}
        
        .body-large {{ font-size: 14px; font-weight: 400; line-height: 1.43; color: {ModernColors.ON_SURFACE_VARIANT}; }}
        .body-medium {{ font-size: 12px; font-weight: 400; line-height: 1.33; color: {ModernColors.ON_SURFACE_VARIANT}; }}
        .body-small {{ font-size: 11px; font-weight: 400; line-height: 1.45; color: {ModernColors.ON_SURFACE_VARIANT}; }}
        
        .label-large {{ font-size: 12px; font-weight: 500; line-height: 1.33; }}
        .label-medium {{ font-size: 11px; font-weight: 500; line-height: 1.45; }}
        .label-small {{ font-size: 10px; font-weight: 500; line-height: 1.60; }}
        
        .caption {{ font-size: 11px; font-weight: 400; line-height: 1.45; color: {ModernColors.OUTLINE}; }}
        .overline {{ 
            font-size: 10px; 
            font-weight: 500; 
            line-height: 1.60; 
            letter-spacing: 1.5px;
            text-transform: uppercase;
            color: {ModernColors.OUTLINE};
        }}
        
        /* === BUTTONS === */
        QPushButton {{
            border: none;
            border-radius: 12px;
            font-weight: 500;
            font-size: 12px;
            min-height: 40px;
            padding: 10px 24px;
            color: {ModernColors.ON_PRIMARY};
        }}
        
        QPushButton.btn-primary {{
            background-color: {ModernColors.PRIMARY};
            color: {ModernColors.ON_PRIMARY};
        }}
        QPushButton.btn-primary:hover {{
            background-color: {ModernColors.PRIMARY_CONTAINER};
        }}
        QPushButton.btn-primary:pressed {{
            background-color: #3730a3;
        }}
        
        QPushButton.btn-secondary {{
            background-color: {ModernColors.SECONDARY};
            color: {ModernColors.ON_SECONDARY};
        }}
        QPushButton.btn-secondary:hover {{
            background-color: {ModernColors.SECONDARY_CONTAINER};
        }}
        
        QPushButton.btn-tertiary {{
            background-color: {ModernColors.TERTIARY};
            color: {ModernColors.ON_TERTIARY};
        }}
        QPushButton.btn-tertiary:hover {{
            background-color: {ModernColors.TERTIARY_CONTAINER};
        }}
        
        QPushButton.btn-outline {{
            background-color: transparent;
            border: 1px solid {ModernColors.OUTLINE};
            color: {ModernColors.ON_SURFACE};
        }}
        QPushButton.btn-outline:hover {{
            background-color: {ModernColors.SURFACE_BRIGHT};
            border-color: {ModernColors.PRIMARY};
        }}
        
        QPushButton.btn-small {{
            min-height: 32px;
            padding: 6px 16px;
            font-size: 11px;
        }}
        
        QPushButton.btn-large {{
            min-height: 48px;
            padding: 14px 32px;
            font-size: 14px;
        }}
        
        /* === INPUTS === */
        QLineEdit, QTextEdit, QComboBox {{
            background-color: {ModernColors.SURFACE};
            border: 1px solid {ModernColors.OUTLINE_VARIANT};
            border-radius: 8px;
            padding: 12px 16px;
            color: {ModernColors.ON_SURFACE};
            font-size: 12px;
            min-height: 40px;
        }}
        
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
            border-color: {ModernColors.PRIMARY};
            background-color: {ModernColors.SURFACE_BRIGHT};
            outline: none;
        }}
        
        QLineEdit::placeholder {{
            color: {ModernColors.OUTLINE};
        }}
        
        /* === CARDS === */
        .card {{
            background-color: {ModernColors.SURFACE};
            border: 1px solid {ModernColors.OUTLINE_VARIANT};
            border-radius: 16px;
            padding: 24px;
        }}
        
        .card:hover {{
            border-color: {ModernColors.OUTLINE};
            background-color: {ModernColors.SURFACE_BRIGHT};
        }}
        
        .card-elevated {{
            background-color: {ModernColors.SURFACE};
            border: 1px solid {ModernColors.OUTLINE_VARIANT};
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        
        /* === TABS === */
        QTabWidget::pane {{
            border: none;
            background-color: transparent;
        }}
        
        QTabBar::tab {{
            background-color: transparent;
            color: {ModernColors.OUTLINE};
            padding: 16px 24px;
            margin-right: 4px;
            border-bottom: 2px solid transparent;
            font-size: 14px;
            font-weight: 500;
            min-width: 120px;
        }}
        
        QTabBar::tab:selected {{
            color: {ModernColors.PRIMARY};
            border-bottom-color: {ModernColors.PRIMARY};
            background-color: {ModernColors.SURFACE};
        }}
        
        QTabBar::tab:hover:!selected {{
            color: {ModernColors.ON_SURFACE_VARIANT};
            background-color: {ModernColors.SURFACE_BRIGHT};
        }}
        
        /* === LISTS === */
        QListWidget {{
            background-color: {ModernColors.SURFACE};
            border: 1px solid {ModernColors.OUTLINE_VARIANT};
            border-radius: 12px;
            color: {ModernColors.ON_SURFACE};
            font-size: 12px;
            padding: 8px;
        }}
        
        QListWidget::item {{
            padding: 12px 16px;
            border-radius: 8px;
            margin: 2px 0;
            border: none;
        }}
        
        QListWidget::item:hover {{
            background-color: {ModernColors.SURFACE_BRIGHT};
        }}
        
        QListWidget::item:selected {{
            background-color: {ModernColors.PRIMARY};
            color: {ModernColors.ON_PRIMARY};
        }}
        
        /* === SCROLLBARS === */
        QScrollBar:vertical {{
            background-color: {ModernColors.SURFACE};
            width: 12px;
            border-radius: 6px;
            margin: 0;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {ModernColors.OUTLINE_VARIANT};
            border-radius: 6px;
            min-height: 20px;
            margin: 2px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {ModernColors.OUTLINE};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        /* === STATUS COLORS === */
        .text-success {{ color: {ModernColors.SUCCESS}; }}
        .text-warning {{ color: {ModernColors.WARNING}; }}
        .text-error {{ color: {ModernColors.ERROR}; }}
        .text-info {{ color: {ModernColors.INFO}; }}
        
        .bg-success {{ background-color: {ModernColors.SUCCESS}; }}
        .bg-warning {{ background-color: {ModernColors.WARNING}; }}
        .bg-error {{ background-color: {ModernColors.ERROR}; }}
        .bg-info {{ background-color: {ModernColors.INFO}; }}
        """
    
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