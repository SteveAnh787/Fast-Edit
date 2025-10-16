"""
Main Window - Cửa sổ chính của ứng dụng Vibe Render Tool
"""

from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QStatusBar
from PySide6.QtCore import QSize

from src.ui.automation_tab import AutomationTab
from src.ui.composer_tab import ComposerTab
from src.ui.project_tab import ProjectTab
from src.ui.unified_styles import UnifiedStyles

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
        
        self.tab_widget.addTab(self.project_tab, "Projects")
        self.tab_widget.addTab(self.automation_tab, "Automation")
        self.tab_widget.addTab(self.composer_tab, "Compose & Render")
        
        layout.addWidget(self.tab_widget)
        
        # Status bar
        self.setup_status_bar()
        self._apply_global_styles()
        
    def setup_tab_widget(self):
        """Setup tab widget styling"""
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setTabsClosable(False)
        self.tab_widget.setMovable(False)
        
    def setup_status_bar(self):
        """Setup status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.status_bar.showMessage("Ready – Vibe Render Tool v2.0.0")

    def _apply_global_styles(self) -> None:
        app = QApplication.instance()
        if app:
            UnifiedStyles.apply_qpalette(app)
        self.setStyleSheet(UnifiedStyles.get_main_stylesheet())

        if hasattr(self.project_tab, "refresh_stylesheet"):
            self.project_tab.refresh_stylesheet()
        if hasattr(self.automation_tab, "refresh_theme"):
            self.automation_tab.refresh_theme()
        if hasattr(self.composer_tab, "refresh_theme"):
            self.composer_tab.refresh_theme()

    def update_status(self, message: str):
        """Update status bar message"""
        self.status_bar.showMessage(message)
