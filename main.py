#!/usr/bin/env python3
"""
Windows SMB & Network Manager
Entry point for the application.

This application provides a graphical interface for managing:
- SMB (Server Message Block) configuration
- Network settings and diagnostics
- Windows Firewall settings

Requirements:
- Windows operating system
- Administrator privileges for full functionality
- PyQt5 >= 5.15.0
"""

import sys
import os

# Add the project directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from utils.admin_check import is_admin, run_as_admin
from ui.main_window import MainWindow


def get_icon_path():
    """Get the path to the application icon."""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = sys._MEIPASS
    else:
        # Running as script
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    icon_path = os.path.join(base_path, 'res', 'app_icon.ico')
    
    if os.path.exists(icon_path):
        return icon_path
    
    # Try alternative paths
    alt_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'res', 'app_icon.ico'),
        'res/app_icon.ico',
    ]
    for path in alt_paths:
        if os.path.exists(path):
            return path
    
    return None


def check_platform():
    """Check if running on Windows."""
    if sys.platform != 'win32':
        return False
    return True


def request_elevation():
    """
    Request elevation to administrator privileges.
    Returns True if already admin or elevation was requested.
    Returns False if elevation failed or was denied.
    """
    if is_admin():
        return True
    
    # Ask user if they want to elevate
    app = QApplication(sys.argv)
    reply = QMessageBox.question(
        None,
        "Administrator Privileges Required",
        "This application requires Administrator privileges for full functionality.\n\n"
        "Do you want to restart with Administrator privileges?\n\n"
        "Click 'Yes' to restart as Administrator.\n"
        "Click 'No' to continue with limited functionality.",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.Yes
    )
    
    if reply == QMessageBox.Yes:
        if run_as_admin():
            # Elevation requested, exit current instance
            sys.exit(0)
        else:
            QMessageBox.warning(
                None,
                "Elevation Failed",
                "Failed to request Administrator privileges.\n"
                "The application will continue with limited functionality.",
                QMessageBox.Ok
            )
    
    # User chose No or elevation failed, continue without elevation
    return False


def main():
    """Main entry point for the application."""
    # Check platform
    if not check_platform():
        print("Error: This application only runs on Windows.")
        sys.exit(1)
    
    # Check for admin privileges and optionally request elevation
    if not is_admin():
        # Try to get elevation - this will show a dialog
        request_elevation()
    
    # Create and run the application
    app = QApplication(sys.argv)
    
    # Set application-wide icon
    icon_path = get_icon_path()
    if icon_path:
        app.setWindowIcon(QIcon(icon_path))
    
    # Set application metadata
    app.setApplicationName("Windows SMB & Network Manager")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("SMB Network Manager")
    
    # Use Fusion style for modern look
    app.setStyle("Fusion")
    
    # Enable high DPI scaling
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run the application event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()