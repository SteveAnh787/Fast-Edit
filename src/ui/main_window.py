"""
Main Window - Cửa sổ chính của ứng dụng Vibe Render Tool
"""

from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QStatusBar
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

from src.ui.automation_tab import AutomationTab
from src.ui.composer_tab import ComposerTab
from src.ui.effects_tab import EffectsTab
from src.ui.project_tab import ProjectTab

class MainWindow(QMainWindow):
    """Main application window with tabs"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        # Window properties
        self.setWindowTitle("Vibe Render Tool")
        self.setMinimumSize(QSize(1200, 800))
        self.resize(QSize(1400, 900))
        
        # Central widget with tabs
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main layout
        layout = QVBoxLayout(self.central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.setup_tab_widget()
        
        # Add tabs
        self.project_tab = ProjectTab()
        self.automation_tab = AutomationTab()
        self.composer_tab = ComposerTab()
        self.effects_tab = EffectsTab()
        
        self.tab_widget.addTab(self.project_tab, "Project Management")
        self.tab_widget.addTab(self.automation_tab, "Automation")
        self.tab_widget.addTab(self.composer_tab, "Compose & Render")
        self.tab_widget.addTab(self.effects_tab, "Visual Effects")
        
        layout.addWidget(self.tab_widget)
        
        # Status bar
        self.setup_status_bar()
        
        # Apply custom styling
        self.apply_styles()
        
    def setup_tab_widget(self):
        """Setup tab widget styling"""
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setTabsClosable(False)
        self.tab_widget.setMovable(False)
        
    def setup_status_bar(self):
        """Setup status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status message
        self.status_bar.showMessage("Ready - Vibe Render Tool v2.0.0")
        
    def apply_styles(self):
        """Apply custom CSS styles"""
        style = """
        QMainWindow {
            background-color: #0f172a;
            color: #e2e8f0;
            font-size: 32px;
        }
        
        QTabWidget::pane {
            border: 1px solid #334155;
            background-color: #1e293b;
            border-radius: 8px;
        }
        
        QTabWidget::tab-bar {
            left: 0px;
        }
        
        QTabBar::tab {
            background-color: #334155;
            color: #94a3b8;
            padding: 16px 32px;
            margin-right: 2px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            font-weight: 600;
            font-size: 44px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        QTabBar::tab:selected {
            background-color: #4f46e5;
            color: white;
            border-bottom: 2px solid #6366f1;
        }
        
        QTabBar::tab:hover:!selected {
            background-color: #475569;
            color: #e2e8f0;
        }
        
        QStatusBar {
            background-color: #1e293b;
            color: #94a3b8;
            border-top: 1px solid #334155;
            font-size: 40px;
        }
        
        QStatusBar::item {
            border: none;
        }
        """
        
        self.setStyleSheet(style)
        
    def update_status(self, message: str):
        """Update status bar message"""
        self.status_bar.showMessage(message)