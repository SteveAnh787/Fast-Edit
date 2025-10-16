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

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("Vibe Render Tool")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Vibe Coding")

    # Setup theme with Fusion style
    app.setStyle('Fusion')

    # Set default font
    font = QFont("Inter", 13)
    font.setStyleHint(QFont.SansSerif)
    app.setFont(font)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()