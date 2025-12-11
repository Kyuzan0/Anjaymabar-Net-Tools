"""Main Window for SMB Network Manager."""

import sys
import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget,
    QLabel, QStatusBar, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from utils.admin_check import is_admin, get_admin_status_message
from .smb_tab import SMBTab
from .network_tab import NetworkTab
from .firewall_tab import FirewallTab


class MainWindow(QMainWindow):
    """Main application window with tabbed interface."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Anjaymabar Net Tools")
        self.setMinimumSize(800, 600)
        self.set_window_icon()
        self.setup_ui()
        self.check_admin_status()
    
    def set_window_icon(self):
        """Set the window icon for title bar and taskbar."""
        # Get the path to the icon file
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            base_path = sys._MEIPASS
        else:
            # Running as script
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        icon_path = os.path.join(base_path, 'res', 'app_icon.ico')
        
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            # Try alternative paths
            alt_paths = [
                os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'res', 'app_icon.ico'),
                'res/app_icon.ico',
                '../res/app_icon.ico'
            ]
            for path in alt_paths:
                if os.path.exists(path):
                    self.setWindowIcon(QIcon(path))
                    break
    
    def setup_ui(self):
        """Initialize the UI components."""
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main Layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Admin Status Banner
        self.admin_banner = QLabel()
        self.admin_banner.setAlignment(Qt.AlignCenter)
        self.admin_banner.setMinimumHeight(30)
        main_layout.addWidget(self.admin_banner)
        
        # Tab Widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(False)
        
        # Create and add tabs
        self.smb_tab = SMBTab()
        self.network_tab = NetworkTab()
        self.firewall_tab = FirewallTab()
        
        self.tab_widget.addTab(self.smb_tab, "🔗 SMB Conf")
        self.tab_widget.addTab(self.network_tab, "🌐 Network Settings")
        self.tab_widget.addTab(self.firewall_tab, "🛡️ Firewall Settings")
        
        main_layout.addWidget(self.tab_widget)
        
        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Apply Styles
        self.apply_styles()
    
    def check_admin_status(self):
        """Check and display admin status."""
        if is_admin():
            self.admin_banner.setStyleSheet(
                "background-color: #4CAF50; color: white; "
                "font-weight: bold; padding: 5px; border-radius: 3px;"
            )
            self.admin_banner.setText("✓ Running with Administrator Privileges")
            self.status_bar.showMessage("Administrator mode - All features available")
        else:
            self.admin_banner.setStyleSheet(
                "background-color: #FF9800; color: white; "
                "font-weight: bold; padding: 5px; border-radius: 3px;"
            )
            self.admin_banner.setText(
                "⚠ Not running as Administrator - Some features may not work. "
                "Please restart as Administrator for full functionality."
            )
            self.status_bar.showMessage("Limited mode - Restart as Administrator for full access")
            
            # Show warning dialog
            QMessageBox.warning(
                self,
                "Administrator Privileges Required",
                "This application is not running with Administrator privileges.\n\n"
                "Some features (like changing SMB settings, firewall settings, etc.) "
                "will not work properly.\n\n"
                "Please close this application and run it as Administrator.",
                QMessageBox.Ok
            )
    
    def apply_styles(self):
        """Apply modern styling to the application."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            
            QTabWidget::pane {
                border: 1px solid #ddd;
                background-color: white;
                border-radius: 5px;
            }
            
            QTabWidget::tab-bar {
                alignment: left;
            }
            
            QTabBar::tab {
                background-color: #e0e0e0;
                color: #333;
                padding: 6px 10px;      /* ukurannya mengecil */
                min-width: 0px;         /* TAB mengikuti panjang teks */
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-weight: bold;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #2196F3;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #f0f0f0;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #2196F3;
            }
            
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            
            QPushButton:hover {
                background-color: #1976D2;
            }
            
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
            }
            
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
                background-color: #fafafa;
                font-family: Consolas, monospace;
            }
            
            QLabel {
                color: #333;
            }
            
            QStatusBar {
                background-color: #e0e0e0;
                color: #333;
            }
        """)
    
    def closeEvent(self, event):
        """Handle window close event."""
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Are you sure you want to exit?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()