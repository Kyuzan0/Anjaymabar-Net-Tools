"""Firewall Settings Tab for SMB Network Manager."""

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
    QPushButton, QLabel, QTextEdit, QMessageBox
)
from PyQt5.QtCore import Qt

from utils.powershell import run_powershell_command, get_firewall_status


class FirewallTab(QWidget):
    """Tab for Windows Firewall configuration."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Quick Access Group
        access_group = QGroupBox("Quick Access")
        access_layout = QVBoxLayout(access_group)
        
        # Firewall Settings Buttons
        btn_layout = QHBoxLayout()
        
        self.open_firewall_btn = QPushButton("Open Windows Firewall Settings")
        self.open_firewall_btn.clicked.connect(self.open_firewall_settings)
        self.open_firewall_btn.setMinimumHeight(40)
        btn_layout.addWidget(self.open_firewall_btn)
        
        
        access_layout.addLayout(btn_layout)
        
        # Advanced Firewall Button
        self.open_advanced_btn = QPushButton("Open Windows Defender Firewall with Advanced Security")
        self.open_advanced_btn.clicked.connect(self.open_advanced_firewall)
        access_layout.addWidget(self.open_advanced_btn)
        
        layout.addWidget(access_group)
        
        # Firewall Toggle Group
        toggle_group = QGroupBox("Quick Firewall Toggle (All Profiles)")
        toggle_layout = QVBoxLayout(toggle_group)
        
        # Warning Label
        warning_label = QLabel("⚠ Warning: Disabling firewall may expose your system to security risks!")
        warning_label.setStyleSheet("color: orange; font-weight: bold;")
        warning_label.setWordWrap(True)
        toggle_layout.addWidget(warning_label)
        
        # Toggle Buttons
        toggle_btn_layout = QHBoxLayout()
        
        self.enable_all_btn = QPushButton("Enable All Firewall Profiles")
        self.enable_all_btn.clicked.connect(self.enable_all_firewall)
        self.enable_all_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.enable_all_btn.setMinimumHeight(50)
        toggle_btn_layout.addWidget(self.enable_all_btn)
        
        self.disable_all_btn = QPushButton("Disable All Firewall Profiles")
        self.disable_all_btn.clicked.connect(self.disable_all_firewall)
        self.disable_all_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        self.disable_all_btn.setMinimumHeight(50)
        toggle_btn_layout.addWidget(self.disable_all_btn)
        
        toggle_layout.addLayout(toggle_btn_layout)
        
        layout.addWidget(toggle_group)
        
        # Individual Profile Control Group
        profile_group = QGroupBox("Individual Profile Control")
        profile_layout = QVBoxLayout(profile_group)

        
        # Private Profile
        private_layout = QHBoxLayout()
        private_label = QLabel("Private Profile:")
        private_label.setMinimumWidth(100)
        self.enable_private_btn = QPushButton("Enable")
        self.enable_private_btn.clicked.connect(lambda: self.toggle_profile("Private", True))
        self.disable_private_btn = QPushButton("Disable")
        self.disable_private_btn.clicked.connect(lambda: self.toggle_profile("Private", False))
        private_layout.addWidget(private_label)
        private_layout.addWidget(self.enable_private_btn)
        private_layout.addWidget(self.disable_private_btn)
        private_layout.addStretch()
        profile_layout.addLayout(private_layout)
        
        # Public Profile
        public_layout = QHBoxLayout()
        public_label = QLabel("Public Profile:")
        public_label.setMinimumWidth(100)
        self.enable_public_btn = QPushButton("Enable")
        self.enable_public_btn.clicked.connect(lambda: self.toggle_profile("Public", True))
        self.disable_public_btn = QPushButton("Disable")
        self.disable_public_btn.clicked.connect(lambda: self.toggle_profile("Public", False))
        public_layout.addWidget(public_label)
        public_layout.addWidget(self.enable_public_btn)
        public_layout.addWidget(self.disable_public_btn)
        public_layout.addStretch()
        profile_layout.addLayout(public_layout)
        
        # Get Status Button
        self.get_status_btn = QPushButton("Get Firewall Status")
        self.get_status_btn.clicked.connect(self.show_firewall_status)
        profile_layout.addWidget(self.get_status_btn)
        
        layout.addWidget(profile_group)
        
        # Output Group
        output_group = QGroupBox("Command Output")
        output_layout = QVBoxLayout(output_group)
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-weight: bold;")
        output_layout.addWidget(self.status_label)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(120)
        output_layout.addWidget(self.output_text)
        
        # Clear Button
        self.clear_btn = QPushButton("Clear Output")
        self.clear_btn.clicked.connect(self.clear_output)
        output_layout.addWidget(self.clear_btn)
        
        layout.addWidget(output_group)
    
    def update_status(self, message: str, success: bool = True):
        """Update the status label with appropriate styling."""
        if success:
            self.status_label.setStyleSheet("font-weight: bold; color: green;")
        else:
            self.status_label.setStyleSheet("font-weight: bold; color: red;")
        self.status_label.setText(message)
    
    def append_output(self, text: str):
        """Append text to the output area."""
        self.output_text.append(text)
        self.output_text.append("-" * 50)
    
    def clear_output(self):
        """Clear the output text area."""
        self.output_text.clear()
        self.status_label.setText("Ready")
        self.status_label.setStyleSheet("font-weight: bold; color: black;")
    
    def open_firewall_settings(self):
        """Open Windows Firewall control panel."""
        try:
            os.system("control firewall.cpl")
            self.update_status("Opened Firewall Settings", True)
            self.append_output("✓ Opened Windows Firewall Settings (firewall.cpl)")
        except Exception as e:
            self.update_status("Failed to open Firewall Settings", False)
            self.append_output(f"✗ Error: {str(e)}")
    
    def open_advanced_firewall(self):
        """Open Windows Defender Firewall with Advanced Security."""
        try:
            os.system("wf.msc")
            self.update_status("Opened Advanced Firewall", True)
            self.append_output("✓ Opened Windows Defender Firewall with Advanced Security")
        except Exception as e:
            self.update_status("Failed to open Advanced Firewall", False)
            self.append_output(f"✗ Error: {str(e)}")
    
    def enable_all_firewall(self):
        """Enable all firewall profiles."""
        cmd = "Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True"
        success, stdout, stderr = run_powershell_command(cmd)
        
        if success:
            self.update_status("All Firewall Profiles: ENABLED", True)
            self.append_output("✓ All firewall profiles enabled successfully")
        else:
            self.update_status("Failed to enable firewall profiles", False)
            self.append_output(f"✗ Error: {stderr if stderr else 'Unknown error'}")
    
    def disable_all_firewall(self):
        """Disable all firewall profiles after confirmation."""
        reply = QMessageBox.warning(
            self,
            "Security Warning",
            "Are you sure you want to disable ALL firewall profiles?\n\n"
            "This will expose your system to potential security threats!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            cmd = "Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False"
            success, stdout, stderr = run_powershell_command(cmd)
            
            if success:
                self.update_status("All Firewall Profiles: DISABLED", True)
                self.append_output("✓ All firewall profiles disabled")
            else:
                self.update_status("Failed to disable firewall profiles", False)
                self.append_output(f"✗ Error: {stderr if stderr else 'Unknown error'}")
        else:
            self.update_status("Operation cancelled", True)
            self.append_output("ℹ Firewall disable operation cancelled by user")
    
    def toggle_profile(self, profile: str, enable: bool):
        """Toggle a specific firewall profile."""
        state = "True" if enable else "False"
        action = "Enable" if enable else "Disable"
        
        if not enable:
            reply = QMessageBox.warning(
                self,
                "Security Warning",
                f"Are you sure you want to disable the {profile} firewall profile?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                self.update_status("Operation cancelled", True)
                self.append_output(f"ℹ {profile} profile disable cancelled by user")
                return
        
        cmd = f"Set-NetFirewallProfile -Profile {profile} -Enabled {state}"
        success, stdout, stderr = run_powershell_command(cmd)
        
        if success:
            status = "ENABLED" if enable else "DISABLED"
            self.update_status(f"{profile} Profile: {status}", True)
            self.append_output(f"✓ {profile} firewall profile {action.lower()}d successfully")
        else:
            self.update_status(f"Failed to {action.lower()} {profile} profile", False)
            self.append_output(f"✗ Error: {stderr if stderr else 'Unknown error'}")
    
    def show_firewall_status(self):
        """Display current firewall status for all profiles."""
        self.update_status("Fetching Firewall Status...", True)
        success, stdout, stderr = get_firewall_status()
        
        if success:
            self.update_status("Firewall Status Retrieved", True)
            self.append_output("Firewall Profile Status:\n" + stdout)
        else:
            self.update_status("Failed to get Firewall Status", False)
            self.append_output(f"✗ Error: {stderr if stderr else 'Unknown error'}")