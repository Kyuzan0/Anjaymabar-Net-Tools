"""SMB Configuration Tab for SMB Network Manager."""

import subprocess
import json
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QTextEdit, QFrame, QLineEdit,
    QApplication, QFormLayout, QScrollArea, QSizePolicy,
    QMessageBox
)
from PyQt5.QtCore import Qt

from utils.powershell import (
    run_powershell_command, get_smb_client_config, get_smb_server_config,
    set_smb_insecure_guest_auth, get_smb_insecure_guest_auth, log_debug
)
from .toggle_switch import ToggleSwitch
from .loading_overlay import LoadingOverlay


# Default secure SMB configuration values
DEFAULT_SMB_CONFIG = {
    "insecure_guest_logons": False,  # Disabled for security
    "client_require_security_signature": False,  # Disabled for compatibility
    "server_require_security_signature": False,  # Disabled for compatibility
    "last_updated": None
}


class SMBTab(QWidget):
    """Tab for SMB (Server Message Block) configuration settings."""
    
    # Config file path
    CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
    CONFIG_FILE = os.path.join(CONFIG_DIR, 'smb_settings.json')
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._loading = False  # Flag to prevent toggle signals during loading
        self._ensure_config_dir()
        self.setup_ui()
        self.load_current_config()
    
    def _ensure_config_dir(self):
        """Ensure the config directory exists."""
        if not os.path.exists(self.CONFIG_DIR):
            try:
                os.makedirs(self.CONFIG_DIR)
            except OSError as e:
                print(f"Warning: Could not create config directory: {e}")
    
    def _load_saved_settings(self):
        """Load saved settings from JSON file."""
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load settings: {e}")
        return None
    
    def _save_settings(self, insecure_guest: bool, client_sig: bool, server_sig: bool):
        """Save current settings to JSON file."""
        settings = {
            "insecure_guest_logons": insecure_guest,
            "client_require_security_signature": client_sig,
            "server_require_security_signature": server_sig,
            "last_updated": datetime.now().isoformat()
        }
        try:
            self._ensure_config_dir()
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save settings: {e}")
    
    def setup_ui(self):
        """Initialize the UI components."""
        # Main layout with no margins (scroll area handles content)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        # Scroll content widget
        scroll_content = QWidget()
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # SMB Configuration Group
        config_group = self._create_config_group()
        content_layout.addWidget(config_group)
        
        # SMB Connection Test Group
        connection_test_group = self._create_connection_test_group()
        content_layout.addWidget(connection_test_group)
        
        # Add stretch at the end to push content up
        content_layout.addStretch()
        
        # Set scroll content
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        # Create loading overlay (must be created after main layout)
        self.loading_overlay = LoadingOverlay(self)
    
    def _create_config_group(self):
        """Create the SMB Configuration group box."""
        config_group = QGroupBox("SMB Configuration")
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(12)
        config_layout.setContentsMargins(15, 15, 15, 15)
        
        # Insecure Guest Logons Toggle
        guest_frame = QFrame()
        guest_layout = QHBoxLayout(guest_frame)
        guest_layout.setContentsMargins(0, 0, 0, 0)
        guest_layout.setSpacing(10)
        
        guest_label_layout = QVBoxLayout()
        guest_label_layout.setSpacing(2)
        guest_label = QLabel("Insecure Guest Logons")
        guest_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        guest_desc = QLabel("Allow guest access to SMB shares without authentication")
        guest_desc.setStyleSheet("color: #666666; font-size: 10px;")
        guest_desc.setWordWrap(True)
        guest_label_layout.addWidget(guest_label)
        guest_label_layout.addWidget(guest_desc)
        
        self.guest_toggle = ToggleSwitch()
        self.guest_toggle.toggled.connect(self.on_guest_toggle_changed)
        
        guest_layout.addLayout(guest_label_layout, 1)
        guest_layout.addWidget(self.guest_toggle)
        
        config_layout.addWidget(guest_frame)
        
        # Separator 1
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.HLine)
        separator1.setFrameShadow(QFrame.Sunken)
        separator1.setStyleSheet("background-color: #E0E0E0;")
        separator1.setFixedHeight(1)
        config_layout.addWidget(separator1)
        
        # Client Security Signature Toggle
        client_sig_frame = QFrame()
        client_sig_layout = QHBoxLayout(client_sig_frame)
        client_sig_layout.setContentsMargins(0, 0, 0, 0)
        client_sig_layout.setSpacing(10)
        
        client_sig_label_layout = QVBoxLayout()
        client_sig_label_layout.setSpacing(2)
        client_sig_label = QLabel("Client Security Signature Required")
        client_sig_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        client_sig_desc = QLabel("Require SMB packet signing for client connections")
        client_sig_desc.setStyleSheet("color: #666666; font-size: 10px;")
        client_sig_desc.setWordWrap(True)
        client_sig_label_layout.addWidget(client_sig_label)
        client_sig_label_layout.addWidget(client_sig_desc)
        
        self.client_sig_toggle = ToggleSwitch()
        self.client_sig_toggle.toggled.connect(self.on_client_sig_toggle_changed)
        
        client_sig_layout.addLayout(client_sig_label_layout, 1)
        client_sig_layout.addWidget(self.client_sig_toggle)
        
        config_layout.addWidget(client_sig_frame)
        
        # Separator 2
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        separator2.setStyleSheet("background-color: #E0E0E0;")
        separator2.setFixedHeight(1)
        config_layout.addWidget(separator2)
        
        # Server Security Signature Toggle
        server_sig_frame = QFrame()
        server_sig_layout = QHBoxLayout(server_sig_frame)
        server_sig_layout.setContentsMargins(0, 0, 0, 0)
        server_sig_layout.setSpacing(10)
        
        server_sig_label_layout = QVBoxLayout()
        server_sig_label_layout.setSpacing(2)
        server_sig_label = QLabel("Server Security Signature Required")
        server_sig_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        server_sig_desc = QLabel("Require SMB packet signing for server connections")
        server_sig_desc.setStyleSheet("color: #666666; font-size: 10px;")
        server_sig_desc.setWordWrap(True)
        server_sig_label_layout.addWidget(server_sig_label)
        server_sig_label_layout.addWidget(server_sig_desc)
        
        self.server_sig_toggle = ToggleSwitch()
        self.server_sig_toggle.toggled.connect(self.on_server_sig_toggle_changed)
        
        server_sig_layout.addLayout(server_sig_label_layout, 1)
        server_sig_layout.addWidget(self.server_sig_toggle)
        
        config_layout.addWidget(server_sig_frame)
        
        # Separator before buttons
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.HLine)
        separator3.setFrameShadow(QFrame.Sunken)
        separator3.setStyleSheet("background-color: #E0E0E0;")
        separator3.setFixedHeight(1)
        config_layout.addWidget(separator3)
        
        # Action Buttons row
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.refresh_btn = QPushButton("🔄 Refresh Status")
        self.refresh_btn.clicked.connect(self.load_current_config)
        self.refresh_btn.setMinimumHeight(35)
        self.refresh_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button_layout.addWidget(self.refresh_btn)
        
        self.restart_smb_btn = QPushButton("🔃 Restart SMB Service")
        self.restart_smb_btn.clicked.connect(self.restart_smb_service)
        self.restart_smb_btn.setMinimumHeight(35)
        self.restart_smb_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.restart_smb_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:pressed {
                background-color: #E65100;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
        """)
        button_layout.addWidget(self.restart_smb_btn)
        
        self.reset_default_btn = QPushButton("⚙️ Reset to Default")
        self.reset_default_btn.clicked.connect(self.reset_to_default)
        self.reset_default_btn.setMinimumHeight(35)
        self.reset_default_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.reset_default_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
            QPushButton:pressed {
                background-color: #4A148C;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
        """)
        button_layout.addWidget(self.reset_default_btn)
        
        button_layout.addStretch()
        
        config_layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-weight: bold; padding: 5px; color: #666666;")
        config_layout.addWidget(self.status_label)
        
        return config_group
    
    def _create_connection_test_group(self):
        """Create the SMB Connection Test group box."""
        connection_test_group = QGroupBox("SMB Connection Test")
        connection_test_layout = QVBoxLayout(connection_test_group)
        connection_test_layout.setSpacing(10)
        connection_test_layout.setContentsMargins(15, 15, 15, 15)
        
        # Form layout for inputs
        form_layout = QFormLayout()
        form_layout.setSpacing(8)
        form_layout.setHorizontalSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # Server IP/Hostname input
        self.server_ip_input = QLineEdit()
        self.server_ip_input.setPlaceholderText("e.g., 192.168.2.133")
        self.server_ip_input.setMinimumHeight(30)
        form_layout.addRow("Server IP/Hostname:", self.server_ip_input)
        
        # Share Name input (optional)
        self.share_name_input = QLineEdit()
        self.share_name_input.setPlaceholderText("e.g., shared (optional)")
        self.share_name_input.setMinimumHeight(30)
        form_layout.addRow("Share Name:", self.share_name_input)
        
        # Username input (optional)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("(optional)")
        self.username_input.setMinimumHeight(30)
        form_layout.addRow("Username:", self.username_input)
        
        # Password input (optional)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("(optional)")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(30)
        form_layout.addRow("Password:", self.password_input)
        
        connection_test_layout.addLayout(form_layout)
        
        # Test buttons
        test_button_layout = QHBoxLayout()
        test_button_layout.setSpacing(10)
        
        self.test_connection_btn = QPushButton("🔍 Test Connection")
        self.test_connection_btn.clicked.connect(self.test_smb_connection)
        self.test_connection_btn.setMinimumHeight(35)
        self.test_connection_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        test_button_layout.addWidget(self.test_connection_btn)
        
        self.open_explorer_btn = QPushButton("📁 Open in Explorer")
        self.open_explorer_btn.clicked.connect(self.open_in_explorer)
        self.open_explorer_btn.setMinimumHeight(35)
        self.open_explorer_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
            QPushButton:pressed {
                background-color: #1B5E20;
            }
        """)
        test_button_layout.addWidget(self.open_explorer_btn)
        
        test_button_layout.addStretch()
        
        connection_test_layout.addLayout(test_button_layout)
        
        # Connection Result display
        result_label = QLabel("Connection Result:")
        result_label.setStyleSheet("font-weight: bold; margin-top: 5px;")
        connection_test_layout.addWidget(result_label)
        
        self.connection_result_text = QTextEdit()
        self.connection_result_text.setReadOnly(True)
        self.connection_result_text.setMinimumHeight(150)
        self.connection_result_text.setMaximumHeight(200)
        self.connection_result_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.connection_result_text.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #00FF00;
                border: 1px solid #333;
                border-radius: 4px;
                font-family: Consolas, monospace;
                font-size: 11px;
                padding: 8px;
            }
        """)
        self.connection_result_text.setPlaceholderText("Test results will appear here...")
        connection_test_layout.addWidget(self.connection_result_text)
        
        return connection_test_group
    
    def update_status(self, message: str, success: bool = True):
        """Update the status label with appropriate styling."""
        if success:
            self.status_label.setStyleSheet("font-weight: bold; color: #4CAF50; padding: 5px;")
        else:
            self.status_label.setStyleSheet("font-weight: bold; color: #F44336; padding: 5px;")
        self.status_label.setText(message)
    
    def append_output(self, text: str):
        """Append text to the connection result area."""
        current_text = self.connection_result_text.toPlainText()
        if current_text:
            self.connection_result_text.setText(current_text + "\n" + text)
        else:
            self.connection_result_text.setText(text)
    
    def clear_output(self):
        """Clear the output text area."""
        self.connection_result_text.clear()
        self.status_label.setText("Ready")
        self.status_label.setStyleSheet("font-weight: bold; color: #666666; padding: 5px;")
    
    def set_toggles_enabled(self, enabled: bool):
        """Enable or disable all toggle switches."""
        self.guest_toggle.setEnabled(enabled)
        self.client_sig_toggle.setEnabled(enabled)
        self.server_sig_toggle.setEnabled(enabled)
        self.refresh_btn.setEnabled(enabled)
        self.restart_smb_btn.setEnabled(enabled)
        self.reset_default_btn.setEnabled(enabled)
    
    def load_current_config(self):
        """Load current SMB configuration from the system."""
        self._loading = True
        self.set_toggles_enabled(False)
        self.update_status("Loading configuration...", True)
        
        # Try to load saved settings first (for reference)
        saved_settings = self._load_saved_settings()
        
        # Get client configuration - always load from system
        cmd_client = "(Get-SmbClientConfiguration).EnableInsecureGuestLogons"
        success, stdout, stderr = run_powershell_command(cmd_client)
        if success:
            guest_enabled = stdout.strip().lower() == "true"
            self.guest_toggle.setChecked(guest_enabled)
        else:
            # Use default secure value if cannot get from system
            self.guest_toggle.setChecked(DEFAULT_SMB_CONFIG["insecure_guest_logons"])
            self.append_output(f"⚠ Failed to get Guest Logons status: {stderr}")
        
        # Get client security signature
        cmd_client_sig = "(Get-SmbClientConfiguration).RequireSecuritySignature"
        success, stdout, stderr = run_powershell_command(cmd_client_sig)
        if success:
            client_sig_required = stdout.strip().lower() == "true"
            self.client_sig_toggle.setChecked(client_sig_required)
        else:
            # Use default secure value if cannot get from system
            self.client_sig_toggle.setChecked(DEFAULT_SMB_CONFIG["client_require_security_signature"])
            self.append_output(f"⚠ Failed to get Client Security Signature status: {stderr}")
        
        # Get server security signature
        cmd_server_sig = "(Get-SmbServerConfiguration).RequireSecuritySignature"
        success, stdout, stderr = run_powershell_command(cmd_server_sig)
        if success:
            server_sig_required = stdout.strip().lower() == "true"
            self.server_sig_toggle.setChecked(server_sig_required)
        else:
            # Use default secure value if cannot get from system
            self.server_sig_toggle.setChecked(DEFAULT_SMB_CONFIG["server_require_security_signature"])
            self.append_output(f"⚠ Failed to get Server Security Signature status: {stderr}")
        
        self._loading = False
        self.set_toggles_enabled(True)
        self.update_status("Configuration loaded", True)
        self.append_output("✓ Current SMB configuration loaded successfully")
        
        # Save current state to JSON
        self._save_settings(
            self.guest_toggle.isChecked(),
            self.client_sig_toggle.isChecked(),
            self.server_sig_toggle.isChecked()
        )
    
    def on_guest_toggle_changed(self, checked: bool):
        """Handle Insecure Guest Logons toggle change with registry fallback."""
        if self._loading:
            return
        
        # Show loading overlay in center of screen
        self.loading_overlay.show("Applying Guest Logons setting...")
        self.set_toggles_enabled(False)
        QApplication.processEvents()
        
        state = "ENABLED" if checked else "DISABLED"
        
        # Method 1: Try PowerShell cmdlet first
        value = "$true" if checked else "$false"
        cmd = f"Set-SmbClientConfiguration -EnableInsecureGuestLogons {value} -Force -Confirm:$false"
        self.append_output(f"→ Attempting to set Insecure Guest Logons to {state}...")
        
        success, stdout, stderr = run_powershell_command(cmd)
        log_debug(f"PowerShell Set-SmbClientConfiguration result: success={success}, stderr={stderr}")
        
        # Verify the change was actually applied
        verify_cmd = "(Get-SmbClientConfiguration).EnableInsecureGuestLogons"
        verify_success, verify_stdout, verify_stderr = run_powershell_command(verify_cmd)
        
        if verify_success:
            actual_value = verify_stdout.strip().lower() == "true"
            log_debug(f"Verification: expected={checked}, actual={actual_value}")
            
            if actual_value == checked:
                # Success with PowerShell method
                self.update_status(f"Insecure Guest Logons: {state}", True)
                self.append_output(f"✓ Insecure Guest Logons {state.lower()} successfully (PowerShell)")
                self._save_settings(
                    checked,
                    self.client_sig_toggle.isChecked(),
                    self.server_sig_toggle.isChecked()
                )
                self.loading_overlay.hide()
                self.set_toggles_enabled(True)
                return
        
        # Method 2: PowerShell didn't work, try registry fallback
        self.append_output("⚠ PowerShell method didn't apply. Trying registry method...")
        log_debug("Falling back to registry method for AllowInsecureGuestAuth")
        
        reg_success, reg_stdout, reg_stderr = set_smb_insecure_guest_auth(checked)
        
        if reg_success:
            # Verify registry change
            reg_verify_success, reg_actual_value, reg_verify_error = get_smb_insecure_guest_auth()
            
            if reg_verify_success and reg_actual_value == checked:
                self.update_status(f"Insecure Guest Logons: {state}", True)
                self.append_output(f"✓ Insecure Guest Logons {state.lower()} successfully (Registry)")
                self.append_output("ℹ Note: A system restart may be required for changes to take full effect.")
                self._save_settings(
                    checked,
                    self.client_sig_toggle.isChecked(),
                    self.server_sig_toggle.isChecked()
                )
                self.loading_overlay.hide()
                self.set_toggles_enabled(True)
                return
            else:
                # Registry method also failed to verify
                self._loading = True
                self.guest_toggle.setChecked(not checked)
                self._loading = False
                self.update_status("Setting change not applied", False)
                self.append_output(f"✗ Error: Registry method failed to apply. Error: {reg_verify_error}")
                log_debug(f"Registry verification failed: expected={checked}, actual={reg_actual_value}")
        else:
            # Registry method failed
            self._loading = True
            self.guest_toggle.setChecked(not checked)
            self._loading = False
            self.update_status("Setting change not applied - requires admin rights", False)
            error_msg = reg_stderr if reg_stderr else "Access denied or registry key not accessible"
            self.append_output(f"✗ Error: Both methods failed. Registry error: {error_msg}")
            self.append_output("ℹ Make sure the application is running as Administrator.")
            log_debug(f"Registry set failed: {reg_stderr}")
        
        self.loading_overlay.hide()
        self.set_toggles_enabled(True)
    
    def on_client_sig_toggle_changed(self, checked: bool):
        """Handle Client Security Signature toggle change."""
        if self._loading:
            return
        
        # Show loading overlay in center of screen
        self.loading_overlay.show("Applying Client Signature setting...")
        self.set_toggles_enabled(False)
        QApplication.processEvents()
        
        value = "$true" if checked else "$false"
        cmd = f"Set-SmbClientConfiguration -RequireSecuritySignature {value} -Force -Confirm:$false"
        success, stdout, stderr = run_powershell_command(cmd)
        
        if success:
            # Verify the change was actually applied by reading back the value
            verify_cmd = "(Get-SmbClientConfiguration).RequireSecuritySignature"
            verify_success, verify_stdout, verify_stderr = run_powershell_command(verify_cmd)
            
            if verify_success:
                actual_value = verify_stdout.strip().lower() == "true"
                if actual_value == checked:
                    state = "REQUIRED" if checked else "NOT REQUIRED"
                    self.update_status(f"Client Security Signature: {state}", True)
                    self.append_output(f"✓ Client Security Signature set to {state.lower()}")
                    # Save settings after successful change
                    self._save_settings(
                        self.guest_toggle.isChecked(),
                        checked,
                        self.server_sig_toggle.isChecked()
                    )
                else:
                    # Value didn't change - revert toggle
                    self._loading = True
                    self.client_sig_toggle.setChecked(actual_value)
                    self._loading = False
                    self.update_status("Setting change not applied (may require admin rights)", False)
                    self.append_output(f"✗ Error: Setting was not applied. Current value: {actual_value}")
            else:
                # Could not verify, assume success
                state = "REQUIRED" if checked else "NOT REQUIRED"
                self.update_status(f"Client Security Signature: {state}", True)
                self.append_output(f"✓ Client Security Signature set to {state.lower()} (verification skipped)")
                self._save_settings(
                    self.guest_toggle.isChecked(),
                    checked,
                    self.server_sig_toggle.isChecked()
                )
        else:
            # Revert toggle on failure
            self._loading = True
            self.client_sig_toggle.setChecked(not checked)
            self._loading = False
            self.update_status("Failed to change Client Security Signature", False)
            self.append_output(f"✗ Error: {stderr if stderr else 'Unknown error'}")
        
        self.loading_overlay.hide()
        self.set_toggles_enabled(True)
    
    def on_server_sig_toggle_changed(self, checked: bool):
        """Handle Server Security Signature toggle change."""
        if self._loading:
            return
        
        # Show loading overlay in center of screen
        self.loading_overlay.show("Applying Server Signature setting...")
        self.set_toggles_enabled(False)
        QApplication.processEvents()
        
        value = "$true" if checked else "$false"
        cmd = f"Set-SmbServerConfiguration -RequireSecuritySignature {value} -Force -Confirm:$false"
        success, stdout, stderr = run_powershell_command(cmd)
        
        if success:
            # Verify the change was actually applied by reading back the value
            verify_cmd = "(Get-SmbServerConfiguration).RequireSecuritySignature"
            verify_success, verify_stdout, verify_stderr = run_powershell_command(verify_cmd)
            
            if verify_success:
                actual_value = verify_stdout.strip().lower() == "true"
                if actual_value == checked:
                    state = "REQUIRED" if checked else "NOT REQUIRED"
                    self.update_status(f"Server Security Signature: {state}", True)
                    self.append_output(f"✓ Server Security Signature set to {state.lower()}")
                    # Save settings after successful change
                    self._save_settings(
                        self.guest_toggle.isChecked(),
                        self.client_sig_toggle.isChecked(),
                        checked
                    )
                else:
                    # Value didn't change - revert toggle
                    self._loading = True
                    self.server_sig_toggle.setChecked(actual_value)
                    self._loading = False
                    self.update_status("Setting change not applied (may require admin rights)", False)
                    self.append_output(f"✗ Error: Setting was not applied. Current value: {actual_value}")
            else:
                # Could not verify, assume success
                state = "REQUIRED" if checked else "NOT REQUIRED"
                self.update_status(f"Server Security Signature: {state}", True)
                self.append_output(f"✓ Server Security Signature set to {state.lower()} (verification skipped)")
                self._save_settings(
                    self.guest_toggle.isChecked(),
                    self.client_sig_toggle.isChecked(),
                    checked
                )
        else:
            # Revert toggle on failure
            self._loading = True
            self.server_sig_toggle.setChecked(not checked)
            self._loading = False
            self.update_status("Failed to change Server Security Signature", False)
            self.append_output(f"✗ Error: {stderr if stderr else 'Unknown error'}")
        
        self.loading_overlay.hide()
        self.set_toggles_enabled(True)
    
    def reset_to_default(self):
        """Reset all SMB settings to their default values."""
        # Confirm with user
        reply = QMessageBox.question(
            self,
            "Reset to Default",
            "This will reset all SMB settings to their default values:\n\n"
            "• Insecure Guest Logons: DISABLED\n"
            "• Client Security Signature: NOT REQUIRED\n"
            "• Server Security Signature: NOT REQUIRED\n\n"
            "Do you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        self.set_toggles_enabled(False)
        self.update_status("Resetting to default settings...", True)
        self.append_output("⚙️ Resetting SMB settings to default values...")
        QApplication.processEvents()
        
        all_success = True
        
        # Reset Insecure Guest Logons (default: disabled)
        self.append_output("  → Setting Insecure Guest Logons to DISABLED...")
        QApplication.processEvents()
        
        # Use registry method for guest logons
        reg_success, reg_stdout, reg_stderr = set_smb_insecure_guest_auth(False)
        if reg_success:
            self.append_output("  ✓ Insecure Guest Logons set to disabled")
        else:
            all_success = False
            self.append_output(f"  ✗ Failed to set Insecure Guest Logons: {reg_stderr}")
        
        # Reset Client Security Signature (default: not required)
        self.append_output("  → Setting Client Security Signature to NOT REQUIRED...")
        QApplication.processEvents()
        cmd_client = "Set-SmbClientConfiguration -RequireSecuritySignature $false -Force -Confirm:$false"
        success, stdout, stderr = run_powershell_command(cmd_client)
        if success:
            self.append_output("  ✓ Client Security Signature set to not required")
        else:
            all_success = False
            self.append_output(f"  ✗ Failed to set Client Security Signature: {stderr}")
        
        # Reset Server Security Signature (default: not required)
        self.append_output("  → Setting Server Security Signature to NOT REQUIRED...")
        QApplication.processEvents()
        cmd_server = "Set-SmbServerConfiguration -RequireSecuritySignature $false -Force -Confirm:$false"
        success, stdout, stderr = run_powershell_command(cmd_server)
        if success:
            self.append_output("  ✓ Server Security Signature set to not required")
        else:
            all_success = False
            self.append_output(f"  ✗ Failed to set Server Security Signature: {stderr}")
        
        # Reload configuration
        self.append_output("")
        if all_success:
            self.update_status("Settings reset to default successfully", True)
            self.append_output("✓ All settings have been reset to default values")
            self.append_output("ℹ Note: A system restart may be required for all changes to take effect.")
        else:
            self.update_status("Some settings failed to reset", False)
            self.append_output("⚠ Some settings failed to reset - check errors above")
        
        self.set_toggles_enabled(True)
        
        # Reload current config to update toggles
        self.append_output("")
        self.append_output("Reloading SMB configuration...")
        QApplication.processEvents()
        self.load_current_config()
    
    def restart_smb_service(self):
        """Restart SMB Server and Client services."""
        # Confirm with user
        reply = QMessageBox.question(
            self,
            "Restart SMB Services",
            "This will restart the SMB Server (LanmanServer) and SMB Client (LanmanWorkstation) services.\n\n"
            "Active SMB connections may be temporarily interrupted.\n\n"
            "Do you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        self.set_toggles_enabled(False)
        self.update_status("Restarting SMB services...", True)
        self.append_output("🔃 Restarting SMB services...")
        QApplication.processEvents()
        
        results = []
        all_success = True
        
        # Restart SMB Server (LanmanServer)
        self.append_output("  → Restarting SMB Server (LanmanServer)...")
        QApplication.processEvents()
        cmd_server = "Restart-Service LanmanServer -Force"
        success, stdout, stderr = run_powershell_command(cmd_server, timeout=60)
        
        if success:
            results.append("✓ SMB Server (LanmanServer) restarted successfully")
        else:
            all_success = False
            error_msg = stderr if stderr else "Unknown error"
            results.append(f"✗ Failed to restart SMB Server: {error_msg}")
        
        QApplication.processEvents()
        
        # Restart SMB Client (LanmanWorkstation)
        self.append_output("  → Restarting SMB Client (LanmanWorkstation)...")
        QApplication.processEvents()
        cmd_client = "Restart-Service LanmanWorkstation -Force"
        success, stdout, stderr = run_powershell_command(cmd_client, timeout=60)
        
        if success:
            results.append("✓ SMB Client (LanmanWorkstation) restarted successfully")
        else:
            all_success = False
            error_msg = stderr if stderr else "Unknown error"
            results.append(f"✗ Failed to restart SMB Client: {error_msg}")
        
        # Display results
        for result in results:
            self.append_output(result)
        
        if all_success:
            self.update_status("SMB services restarted successfully", True)
            self.append_output("✓ All SMB services restarted successfully")
        else:
            self.update_status("Some SMB services failed to restart", False)
            self.append_output("⚠ Some services failed to restart - check errors above")
        
        self.set_toggles_enabled(True)
        
        # Reload configuration after restart
        self.append_output("Reloading SMB configuration...")
        QApplication.processEvents()
        self.load_current_config()
    
    def test_smb_connection(self):
        """Test SMB connection to the specified server."""
        ip = self.server_ip_input.text().strip()
        share = self.share_name_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not ip:
            self.connection_result_text.setText("❌ Error: Please enter server IP or hostname")
            return
        
        self.connection_result_text.setText(f"Testing connection to \\\\{ip}...")
        QApplication.processEvents()  # Update UI
        
        results = []
        
        # Test 1: Port 445 connectivity using PowerShell
        cmd = f'Test-NetConnection -ComputerName {ip} -Port 445 -WarningAction SilentlyContinue | Select-Object -ExpandProperty TcpTestSucceeded'
        success, stdout, stderr = run_powershell_command(cmd, timeout=15)
        
        if success and "True" in stdout:
            results.append("✓ Port 445 (SMB) is reachable")
        else:
            results.append("✗ Port 445 (SMB) is not reachable")
            # If port is not reachable, still try other tests
        
        QApplication.processEvents()
        
        # Test 2: List available shares using net view
        try:
            result = subprocess.run(
                ['net', 'view', f'\\\\{ip}'],
                capture_output=True,
                text=True,
                timeout=15,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            if result.returncode == 0:
                results.append("✓ SMB service is responding")
                results.append("")
                results.append("Available shares:")
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('-') and not line.startswith('Shared') and not line.startswith('The command'):
                        # Parse share name (first word before spaces)
                        if 'Disk' in line or 'Print' in line or 'IPC' in line:
                            parts = line.split()
                            if parts:
                                share_name = parts[0]
                                share_type = 'Disk' if 'Disk' in line else ('Print' if 'Print' in line else 'IPC')
                                results.append(f"  • {share_name} ({share_type})")
            else:
                error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
                if "Access is denied" in error_msg or "5" in str(result.returncode):
                    results.append("✗ Access denied - authentication may be required")
                elif "network path was not found" in error_msg.lower():
                    results.append("✗ Network path not found - server may be offline")
                else:
                    results.append(f"✗ Cannot list shares: {error_msg}")
        except subprocess.TimeoutExpired:
            results.append("✗ Connection timed out while listing shares")
        except Exception as e:
            results.append(f"✗ Error listing shares: {str(e)}")
        
        QApplication.processEvents()
        
        # Test 3: If credentials provided, test authentication
        if username and password:
            results.append("")
            results.append("Testing authentication...")
            try:
                # Try to connect with credentials
                net_use_cmd = f'net use \\\\{ip}\\IPC$ /user:{username} "{password}"'
                result = subprocess.run(
                    ['cmd', '/c', net_use_cmd],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
                
                if result.returncode == 0:
                    results.append(f"✓ Authentication successful for user '{username}'")
                    # Clean up connection
                    subprocess.run(
                        ['net', 'use', f'\\\\{ip}\\IPC$', '/delete', '/y'],
                        capture_output=True,
                        timeout=5,
                        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                    )
                else:
                    error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
                    results.append(f"✗ Authentication failed: {error_msg}")
            except subprocess.TimeoutExpired:
                results.append("✗ Authentication timed out")
            except Exception as e:
                results.append(f"✗ Authentication error: {str(e)}")
        
        # Test 4: If share specified, test specific share access
        if share:
            results.append("")
            results.append(f"Testing share access: \\\\{ip}\\{share}")
            share_path = f'\\\\{ip}\\{share}'
            
            try:
                # Test if we can access the share
                cmd = f'Test-Path -Path "{share_path}"'
                success, stdout, stderr = run_powershell_command(cmd, timeout=10)
                
                if success and "True" in stdout:
                    results.append(f"✓ Share '{share}' is accessible")
                else:
                    results.append(f"✗ Share '{share}' is not accessible or does not exist")
            except Exception as e:
                results.append(f"✗ Error testing share: {str(e)}")
        
        self.connection_result_text.setText('\n'.join(results))
    
    def open_in_explorer(self):
        """Open the SMB share in Windows Explorer."""
        ip = self.server_ip_input.text().strip()
        share = self.share_name_input.text().strip()
        
        if not ip:
            self.connection_result_text.setText("❌ Error: Please enter server IP or hostname")
            return
        
        # Build the path
        if share:
            path = f'\\\\{ip}\\{share}'
        else:
            path = f'\\\\{ip}'
        
        try:
            subprocess.Popen(['explorer', path])
            self.connection_result_text.setText(f"Opening {path} in Windows Explorer...")
        except Exception as e:
            self.connection_result_text.setText(f"❌ Error opening explorer: {str(e)}")