#!/usr/bin/env python3
"""
Vibe Render Tool - Python Version
High-performance desktop tool for batch-generating subtitle-rich video content
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor, QFont

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from ui.main_window import MainWindow

def setup_dark_theme(app: QApplication):
    """Setup dark theme for the application"""
    app.setStyle('Fusion')
    
    # Create dark palette
    palette = QPalette()
    
    # Window colors
    palette.setColor(QPalette.Window, QColor(15, 23, 42))  # slate-950
    palette.setColor(QPalette.WindowText, QColor(226, 232, 240))  # slate-200
    
    # Base colors (input fields)
    palette.setColor(QPalette.Base, QColor(30, 41, 59))  # slate-800
    palette.setColor(QPalette.AlternateBase, QColor(51, 65, 85))  # slate-700
    
    # Text colors
    palette.setColor(QPalette.Text, QColor(226, 232, 240))  # slate-200
    palette.setColor(QPalette.BrightText, QColor(255, 255, 255))
    
    # Button colors
    palette.setColor(QPalette.Button, QColor(51, 65, 85))  # slate-700
    palette.setColor(QPalette.ButtonText, QColor(226, 232, 240))  # slate-200
    
    # Highlight colors
    palette.setColor(QPalette.Highlight, QColor(79, 70, 229))  # indigo-600
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    
    app.setPalette(palette)

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Vibe Render Tool")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Vibe Coding")
    
    # Setup theme and fonts
    setup_dark_theme(app)
    
    # Set default font
    font = QFont("Arial", 10)
    app.setFont(font)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()