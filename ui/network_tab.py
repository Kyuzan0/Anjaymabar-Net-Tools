"""Network Settings Tab for SMB Network Manager."""

import os
import re
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QTextEdit, QComboBox, QLineEdit,
    QRadioButton, QButtonGroup, QFormLayout, QFrame,
    QScrollArea, QSizePolicy, QApplication, QMessageBox
)
from PyQt5.QtCore import Qt

from utils.powershell import run_cmd_command, run_powershell_command


class NetworkTab(QWidget):
    """Tab for network configuration and diagnostics."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.network_adapters = {}  # Store adapter info: {display_name: interface_alias}
        self.setup_ui()
        self.refresh_network_adapters()
    
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
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # Quick Access Group
        access_group = QGroupBox("Quick Access")
        access_layout = QVBoxLayout(access_group)
        
        # Network Connections Button
        network_btn_layout = QHBoxLayout()
        self.open_network_btn = QPushButton("Open Network Connections (ncpa.cpl)")
        self.open_network_btn.clicked.connect(self.open_network_connections)
        self.open_network_btn.setMinimumHeight(40)
        network_btn_layout.addWidget(self.open_network_btn)
        access_layout.addLayout(network_btn_layout)
        
        # Additional Quick Access Buttons
        quick_btns_layout = QHBoxLayout()
        
        self.open_adapter_btn = QPushButton("Network & Internet Settings")
        self.open_adapter_btn.clicked.connect(self.open_network_settings)
        quick_btns_layout.addWidget(self.open_adapter_btn)
        
        self.open_sharing_btn = QPushButton("Advanced Sharing Settings")
        self.open_sharing_btn.clicked.connect(self.open_sharing_settings)
        quick_btns_layout.addWidget(self.open_sharing_btn)
        
        access_layout.addLayout(quick_btns_layout)
        content_layout.addWidget(access_group)
        
        # IP Configuration Settings Group (NEW)
        ip_config_group = self._create_ip_config_group()
        content_layout.addWidget(ip_config_group)
        
        # IP Commands Group
        ip_group = QGroupBox("IP Commands")
        ip_layout = QVBoxLayout(ip_group)
        
        # Buttons Row
        btn_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh IP Config")
        self.refresh_btn.clicked.connect(self.refresh_ipconfig)
        btn_layout.addWidget(self.refresh_btn)
        
        self.refresh_all_btn = QPushButton("Refresh IP Config (All)")
        self.refresh_all_btn.clicked.connect(self.refresh_ipconfig_all)
        btn_layout.addWidget(self.refresh_all_btn)
        
        self.release_btn = QPushButton("Release IP")
        self.release_btn.clicked.connect(self.release_ip)
        btn_layout.addWidget(self.release_btn)
        
        self.renew_btn = QPushButton("Renew IP")
        self.renew_btn.clicked.connect(self.renew_ip)
        btn_layout.addWidget(self.renew_btn)
        
        ip_layout.addLayout(btn_layout)
        
        # DNS Buttons Row
        dns_layout = QHBoxLayout()
        
        self.flush_dns_btn = QPushButton("Flush DNS Cache")
        self.flush_dns_btn.clicked.connect(self.flush_dns)
        dns_layout.addWidget(self.flush_dns_btn)
        
        self.display_dns_btn = QPushButton("Display DNS Cache")
        self.display_dns_btn.clicked.connect(self.display_dns)
        dns_layout.addWidget(self.display_dns_btn)
        
        ip_layout.addLayout(dns_layout)
        
        content_layout.addWidget(ip_group)
        
        # Output Group
        output_group = QGroupBox("Command Output")
        output_layout = QVBoxLayout(output_group)
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-weight: bold;")
        output_layout.addWidget(self.status_label)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(200)
        self.output_text.setFontFamily("Consolas")
        output_layout.addWidget(self.output_text)
        
        # Clear Button
        self.clear_btn = QPushButton("Clear Output")
        self.clear_btn.clicked.connect(self.clear_output)
        output_layout.addWidget(self.clear_btn)
        
        content_layout.addWidget(output_group)
        
        # Add stretch at the end
        content_layout.addStretch()
        
        # Set scroll content
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
    
    def _create_ip_config_group(self):
        """Create the IP Configuration settings group box."""
        ip_config_group = QGroupBox("IP Configuration")
        ip_config_layout = QVBoxLayout(ip_config_group)
        ip_config_layout.setSpacing(10)
        ip_config_layout.setContentsMargins(15, 15, 15, 15)
        
        # Network Adapter Selection
        adapter_layout = QHBoxLayout()
        adapter_label = QLabel("Network Adapter:")
        adapter_label.setMinimumWidth(120)
        self.adapter_combo = QComboBox()
        self.adapter_combo.setMinimumHeight(30)
        self.adapter_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.adapter_combo.currentIndexChanged.connect(self.on_adapter_changed)
        
        self.refresh_adapters_btn = QPushButton("🔄")
        self.refresh_adapters_btn.setFixedSize(35, 30)
        self.refresh_adapters_btn.setToolTip("Refresh network adapters")
        self.refresh_adapters_btn.clicked.connect(self.refresh_network_adapters)
        
        adapter_layout.addWidget(adapter_label)
        adapter_layout.addWidget(self.adapter_combo)
        adapter_layout.addWidget(self.refresh_adapters_btn)
        ip_config_layout.addLayout(adapter_layout)
        
        # DHCP / Static IP Radio Buttons
        ip_type_layout = QHBoxLayout()
        ip_type_label = QLabel("IP Assignment:")
        ip_type_label.setMinimumWidth(120)
        
        self.dhcp_radio = QRadioButton("DHCP (Automatic)")
        self.static_radio = QRadioButton("Static IP (Manual)")
        self.dhcp_radio.setChecked(True)
        
        self.ip_type_group = QButtonGroup()
        self.ip_type_group.addButton(self.dhcp_radio, 0)
        self.ip_type_group.addButton(self.static_radio, 1)
        self.ip_type_group.buttonClicked.connect(self.on_ip_type_changed)
        
        ip_type_layout.addWidget(ip_type_label)
        ip_type_layout.addWidget(self.dhcp_radio)
        ip_type_layout.addWidget(self.static_radio)
        ip_type_layout.addStretch()
        ip_config_layout.addLayout(ip_type_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #E0E0E0;")
        separator.setFixedHeight(1)
        ip_config_layout.addWidget(separator)
        
        # Static IP Configuration Form
        self.static_ip_frame = QFrame()
        static_form_layout = QFormLayout(self.static_ip_frame)
        static_form_layout.setSpacing(8)
        static_form_layout.setHorizontalSpacing(15)
        static_form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # IP Address
        self.ip_address_input = QLineEdit()
        self.ip_address_input.setPlaceholderText("192.168.1.100")
        self.ip_address_input.setMinimumHeight(28)
        static_form_layout.addRow("IP Address:", self.ip_address_input)
        
        # Subnet Mask
        self.subnet_mask_input = QLineEdit()
        self.subnet_mask_input.setPlaceholderText("255.255.255.0")
        self.subnet_mask_input.setMinimumHeight(28)
        static_form_layout.addRow("Subnet Mask:", self.subnet_mask_input)
        
        # Default Gateway
        self.gateway_input = QLineEdit()
        self.gateway_input.setPlaceholderText("192.168.1.1")
        self.gateway_input.setMinimumHeight(28)
        static_form_layout.addRow("Default Gateway:", self.gateway_input)
        
        # Primary DNS
        self.primary_dns_input = QLineEdit()
        self.primary_dns_input.setPlaceholderText("8.8.8.8")
        self.primary_dns_input.setMinimumHeight(28)
        static_form_layout.addRow("Primary DNS:", self.primary_dns_input)
        
        # Secondary DNS
        self.secondary_dns_input = QLineEdit()
        self.secondary_dns_input.setPlaceholderText("8.8.4.4 (optional)")
        self.secondary_dns_input.setMinimumHeight(28)
        static_form_layout.addRow("Secondary DNS:", self.secondary_dns_input)
        
        self.static_ip_frame.setEnabled(False)  # Disabled by default (DHCP selected)
        ip_config_layout.addWidget(self.static_ip_frame)
        
        # Apply Button
        apply_btn_layout = QHBoxLayout()
        
        self.apply_ip_btn = QPushButton("📝 Apply IP Configuration")
        self.apply_ip_btn.setMinimumHeight(40)
        self.apply_ip_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
            QPushButton:pressed {
                background-color: #1B5E20;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
        """)
        self.apply_ip_btn.clicked.connect(self.apply_ip_configuration)
        
        self.load_current_ip_btn = QPushButton("📥 Load Current IP")
        self.load_current_ip_btn.setMinimumHeight(40)
        self.load_current_ip_btn.clicked.connect(self.load_current_adapter_ip)
        
        apply_btn_layout.addWidget(self.apply_ip_btn)
        apply_btn_layout.addWidget(self.load_current_ip_btn)
        apply_btn_layout.addStretch()
        
        ip_config_layout.addLayout(apply_btn_layout)
        
        return ip_config_group
    
    def refresh_network_adapters(self):
        """Refresh the list of PCIe network adapters."""
        self.adapter_combo.clear()
        self.network_adapters.clear()
        
        self.update_status("Detecting network adapters...", True)
        QApplication.processEvents()
        
        # PowerShell command to get PCIe network adapters
        cmd = """Get-NetAdapter | Where-Object {
            $_.InterfaceDescription -like '*PCI*' -or
            $_.PnPDeviceID -like '*PCI*' -or
            $_.InterfaceDescription -like '*Ethernet*' -or
            $_.InterfaceDescription -like '*Realtek*' -or
            $_.InterfaceDescription -like '*Intel*' -or
            $_.InterfaceDescription -like '*Killer*' -or
            $_.InterfaceDescription -like '*Qualcomm*' -or
            $_.InterfaceDescription -like '*Broadcom*'
        } | Select-Object Name, InterfaceDescription, Status, MacAddress | ConvertTo-Json"""
        
        success, stdout, stderr = run_powershell_command(cmd)
        
        if success and stdout.strip():
            try:
                import json
                # Handle both single object and array
                adapters_data = json.loads(stdout)
                if isinstance(adapters_data, dict):
                    adapters_data = [adapters_data]
                
                for adapter in adapters_data:
                    name = adapter.get('Name', '')
                    desc = adapter.get('InterfaceDescription', '')
                    status = adapter.get('Status', '')
                    mac = adapter.get('MacAddress', '')
                    
                    # Create display name with status
                    status_icon = "🟢" if status == "Up" else "🔴"
                    display_name = f"{status_icon} {name} - {desc}"
                    
                    self.network_adapters[display_name] = {
                        'name': name,
                        'description': desc,
                        'status': status,
                        'mac': mac
                    }
                    self.adapter_combo.addItem(display_name)
                
                self.update_status(f"Found {len(adapters_data)} network adapter(s)", True)
                self.append_output(f"✓ Detected {len(adapters_data)} PCIe/Ethernet network adapter(s)")
                
            except (json.JSONDecodeError, KeyError) as e:
                self.update_status("Error parsing adapter data", False)
                self.append_output(f"✗ Error parsing adapter data: {e}")
                # Fallback: try to get all adapters
                self._get_all_adapters_fallback()
        else:
            self.update_status("No PCIe adapters found, loading all adapters", True)
            self._get_all_adapters_fallback()
    
    def _get_all_adapters_fallback(self):
        """Fallback method to get all network adapters."""
        cmd = "Get-NetAdapter | Select-Object Name, InterfaceDescription, Status | ConvertTo-Json"
        success, stdout, stderr = run_powershell_command(cmd)
        
        if success and stdout.strip():
            try:
                import json
                adapters_data = json.loads(stdout)
                if isinstance(adapters_data, dict):
                    adapters_data = [adapters_data]
                
                for adapter in adapters_data:
                    name = adapter.get('Name', '')
                    desc = adapter.get('InterfaceDescription', '')
                    status = adapter.get('Status', '')
                    
                    status_icon = "🟢" if status == "Up" else "🔴"
                    display_name = f"{status_icon} {name} - {desc}"
                    
                    self.network_adapters[display_name] = {
                        'name': name,
                        'description': desc,
                        'status': status,
                        'mac': ''
                    }
                    self.adapter_combo.addItem(display_name)
                
                self.append_output(f"✓ Loaded {len(adapters_data)} network adapter(s) (fallback)")
                
            except Exception as e:
                self.append_output(f"✗ Error in fallback adapter detection: {e}")
    
    def on_adapter_changed(self, index):
        """Handle adapter selection change."""
        if index >= 0:
            display_name = self.adapter_combo.currentText()
            if display_name in self.network_adapters:
                adapter_info = self.network_adapters[display_name]
                self.append_output(f"Selected adapter: {adapter_info['name']} ({adapter_info['description']})")
    
    def on_ip_type_changed(self, button):
        """Handle DHCP/Static IP radio button change."""
        is_static = self.static_radio.isChecked()
        self.static_ip_frame.setEnabled(is_static)
        
        if is_static:
            self.append_output("Static IP mode selected - enter IP configuration manually")
        else:
            self.append_output("DHCP mode selected - IP will be assigned automatically")
    
    def load_current_adapter_ip(self):
        """Load current IP configuration for selected adapter."""
        display_name = self.adapter_combo.currentText()
        if not display_name or display_name not in self.network_adapters:
            self.update_status("Please select a network adapter", False)
            return
        
        adapter_info = self.network_adapters[display_name]
        interface_alias = adapter_info['name']
        
        self.update_status(f"Loading IP configuration for {interface_alias}...", True)
        QApplication.processEvents()
        
        # Get IP address info
        cmd = f'Get-NetIPAddress -InterfaceAlias "{interface_alias}" -AddressFamily IPv4 | Select-Object IPAddress, PrefixLength | ConvertTo-Json'
        success, stdout, stderr = run_powershell_command(cmd)
        
        if success and stdout.strip():
            try:
                import json
                ip_data = json.loads(stdout)
                if isinstance(ip_data, list):
                    ip_data = ip_data[0] if ip_data else {}
                
                ip_address = ip_data.get('IPAddress', '')
                prefix_length = ip_data.get('PrefixLength', 24)
                
                # Convert prefix length to subnet mask
                subnet_mask = self._prefix_to_subnet(prefix_length)
                
                self.ip_address_input.setText(ip_address)
                self.subnet_mask_input.setText(subnet_mask)
                
            except Exception as e:
                self.append_output(f"⚠ Error parsing IP address: {e}")
        
        # Get default gateway
        cmd = f'Get-NetRoute -InterfaceAlias "{interface_alias}" -DestinationPrefix "0.0.0.0/0" | Select-Object NextHop | ConvertTo-Json'
        success, stdout, stderr = run_powershell_command(cmd)
        
        if success and stdout.strip():
            try:
                import json
                gateway_data = json.loads(stdout)
                if isinstance(gateway_data, list):
                    gateway_data = gateway_data[0] if gateway_data else {}
                gateway = gateway_data.get('NextHop', '')
                self.gateway_input.setText(gateway)
            except Exception:
                pass
        
        # Get DNS servers
        cmd = f'Get-DnsClientServerAddress -InterfaceAlias "{interface_alias}" -AddressFamily IPv4 | Select-Object ServerAddresses | ConvertTo-Json'
        success, stdout, stderr = run_powershell_command(cmd)
        
        if success and stdout.strip():
            try:
                import json
                dns_data = json.loads(stdout)
                if isinstance(dns_data, list):
                    dns_data = dns_data[0] if dns_data else {}
                dns_servers = dns_data.get('ServerAddresses', [])
                
                if dns_servers and len(dns_servers) > 0:
                    self.primary_dns_input.setText(dns_servers[0])
                if dns_servers and len(dns_servers) > 1:
                    self.secondary_dns_input.setText(dns_servers[1])
                    
            except Exception:
                pass
        
        # Check if DHCP is enabled
        cmd = f'Get-NetIPInterface -InterfaceAlias "{interface_alias}" -AddressFamily IPv4 | Select-Object Dhcp | ConvertTo-Json'
        success, stdout, stderr = run_powershell_command(cmd)
        
        if success and stdout.strip():
            try:
                import json
                dhcp_data = json.loads(stdout)
                if isinstance(dhcp_data, list):
                    dhcp_data = dhcp_data[0] if dhcp_data else {}
                dhcp_enabled = dhcp_data.get('Dhcp', '') == 'Enabled'
                
                if dhcp_enabled:
                    self.dhcp_radio.setChecked(True)
                    self.static_ip_frame.setEnabled(False)
                else:
                    self.static_radio.setChecked(True)
                    self.static_ip_frame.setEnabled(True)
                    
            except Exception:
                pass
        
        self.update_status(f"Loaded IP configuration for {interface_alias}", True)
        self.append_output(f"✓ Current IP configuration loaded for {interface_alias}")
    
    def _prefix_to_subnet(self, prefix_length):
        """Convert CIDR prefix length to subnet mask."""
        try:
            prefix = int(prefix_length)
            mask = (0xffffffff >> (32 - prefix)) << (32 - prefix)
            return f"{(mask >> 24) & 0xff}.{(mask >> 16) & 0xff}.{(mask >> 8) & 0xff}.{mask & 0xff}"
        except (ValueError, TypeError):
            return "255.255.255.0"
    
    def _subnet_to_prefix(self, subnet_mask):
        """Convert subnet mask to CIDR prefix length."""
        try:
            parts = subnet_mask.split('.')
            if len(parts) != 4:
                return 24
            binary = ''.join([bin(int(x)).lstrip('0b').zfill(8) for x in parts])
            return binary.count('1')
        except (ValueError, AttributeError):
            return 24
    
    def _validate_ip(self, ip_str):
        """Validate IP address format."""
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, ip_str):
            return False
        parts = ip_str.split('.')
        return all(0 <= int(part) <= 255 for part in parts)
    
    def apply_ip_configuration(self):
        """Apply IP configuration to selected adapter."""
        display_name = self.adapter_combo.currentText()
        if not display_name or display_name not in self.network_adapters:
            QMessageBox.warning(self, "Warning", "Please select a network adapter.")
            return
        
        adapter_info = self.network_adapters[display_name]
        interface_alias = adapter_info['name']
        
        is_dhcp = self.dhcp_radio.isChecked()
        
        if is_dhcp:
            # Apply DHCP configuration
            reply = QMessageBox.question(
                self,
                "Apply DHCP Configuration",
                f"This will set the adapter '{interface_alias}' to obtain IP address automatically via DHCP.\n\n"
                "Do you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            self.update_status("Applying DHCP configuration...", True)
            self.append_output(f"🔄 Setting {interface_alias} to DHCP mode...")
            QApplication.processEvents()
            
            # Remove existing static IP
            cmd = f'Remove-NetIPAddress -InterfaceAlias "{interface_alias}" -AddressFamily IPv4 -Confirm:$false -ErrorAction SilentlyContinue'
            run_powershell_command(cmd)
            
            # Remove existing gateway
            cmd = f'Remove-NetRoute -InterfaceAlias "{interface_alias}" -DestinationPrefix "0.0.0.0/0" -Confirm:$false -ErrorAction SilentlyContinue'
            run_powershell_command(cmd)
            
            # Enable DHCP
            cmd = f'Set-NetIPInterface -InterfaceAlias "{interface_alias}" -Dhcp Enabled'
            success, stdout, stderr = run_powershell_command(cmd)
            
            if not success:
                self.update_status("Failed to enable DHCP", False)
                self.append_output(f"✗ Error enabling DHCP: {stderr}")
                return
            
            # Reset DNS to automatic
            cmd = f'Set-DnsClientServerAddress -InterfaceAlias "{interface_alias}" -ResetServerAddresses'
            success, stdout, stderr = run_powershell_command(cmd)
            
            if success:
                self.update_status("DHCP configuration applied successfully", True)
                self.append_output(f"✓ DHCP configuration applied to {interface_alias}")
                self.append_output("  IP address will be obtained automatically")
            else:
                self.update_status("DHCP applied, DNS reset failed", False)
                self.append_output(f"⚠ DHCP enabled but DNS reset failed: {stderr}")
                
        else:
            # Apply Static IP configuration
            ip_address = self.ip_address_input.text().strip()
            subnet_mask = self.subnet_mask_input.text().strip()
            gateway = self.gateway_input.text().strip()
            primary_dns = self.primary_dns_input.text().strip()
            secondary_dns = self.secondary_dns_input.text().strip()
            
            # Validation
            if not ip_address:
                QMessageBox.warning(self, "Validation Error", "IP Address is required.")
                return
            
            if not self._validate_ip(ip_address):
                QMessageBox.warning(self, "Validation Error", "Invalid IP Address format.")
                return
            
            if not subnet_mask:
                subnet_mask = "255.255.255.0"
            elif not self._validate_ip(subnet_mask):
                QMessageBox.warning(self, "Validation Error", "Invalid Subnet Mask format.")
                return
            
            if gateway and not self._validate_ip(gateway):
                QMessageBox.warning(self, "Validation Error", "Invalid Gateway format.")
                return
            
            if primary_dns and not self._validate_ip(primary_dns):
                QMessageBox.warning(self, "Validation Error", "Invalid Primary DNS format.")
                return
            
            if secondary_dns and not self._validate_ip(secondary_dns):
                QMessageBox.warning(self, "Validation Error", "Invalid Secondary DNS format.")
                return
            
            prefix_length = self._subnet_to_prefix(subnet_mask)
            
            # Confirm with user
            config_summary = f"IP Address: {ip_address}/{prefix_length}\nSubnet Mask: {subnet_mask}"
            if gateway:
                config_summary += f"\nDefault Gateway: {gateway}"
            if primary_dns:
                config_summary += f"\nPrimary DNS: {primary_dns}"
            if secondary_dns:
                config_summary += f"\nSecondary DNS: {secondary_dns}"
            
            reply = QMessageBox.question(
                self,
                "Apply Static IP Configuration",
                f"This will set the following IP configuration on '{interface_alias}':\n\n{config_summary}\n\n"
                "Do you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            self.update_status("Applying static IP configuration...", True)
            self.append_output(f"🔄 Setting static IP on {interface_alias}...")
            QApplication.processEvents()
            
            # Remove existing IP configuration
            cmd = f'Remove-NetIPAddress -InterfaceAlias "{interface_alias}" -AddressFamily IPv4 -Confirm:$false -ErrorAction SilentlyContinue'
            run_powershell_command(cmd)
            
            # Remove existing gateway
            cmd = f'Remove-NetRoute -InterfaceAlias "{interface_alias}" -DestinationPrefix "0.0.0.0/0" -Confirm:$false -ErrorAction SilentlyContinue'
            run_powershell_command(cmd)
            
            # Disable DHCP
            cmd = f'Set-NetIPInterface -InterfaceAlias "{interface_alias}" -Dhcp Disabled'
            run_powershell_command(cmd)
            
            QApplication.processEvents()
            
            # Set new IP address
            if gateway:
                cmd = f'New-NetIPAddress -InterfaceAlias "{interface_alias}" -IPAddress "{ip_address}" -PrefixLength {prefix_length} -DefaultGateway "{gateway}"'
            else:
                cmd = f'New-NetIPAddress -InterfaceAlias "{interface_alias}" -IPAddress "{ip_address}" -PrefixLength {prefix_length}'
            
            success, stdout, stderr = run_powershell_command(cmd, timeout=30)
            
            if not success:
                self.update_status("Failed to set IP address", False)
                self.append_output(f"✗ Error setting IP address: {stderr}")
                return
            
            self.append_output(f"  ✓ IP Address set: {ip_address}/{prefix_length}")
            if gateway:
                self.append_output(f"  ✓ Default Gateway set: {gateway}")
            
            QApplication.processEvents()
            
            # Set DNS servers
            if primary_dns:
                if secondary_dns:
                    dns_servers = f'"{primary_dns}","{secondary_dns}"'
                else:
                    dns_servers = f'"{primary_dns}"'
                
                cmd = f'Set-DnsClientServerAddress -InterfaceAlias "{interface_alias}" -ServerAddresses ({dns_servers})'
                success, stdout, stderr = run_powershell_command(cmd)
                
                if success:
                    self.append_output(f"  ✓ DNS servers set: {primary_dns}" + (f", {secondary_dns}" if secondary_dns else ""))
                else:
                    self.append_output(f"  ⚠ Failed to set DNS: {stderr}")
            
            self.update_status("Static IP configuration applied successfully", True)
            self.append_output(f"✓ Static IP configuration applied to {interface_alias}")
    
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
        self.output_text.append("-" * 60)
    
    def clear_output(self):
        """Clear the output text area."""
        self.output_text.clear()
        self.status_label.setText("Ready")
        self.status_label.setStyleSheet("font-weight: bold; color: black;")
    
    def open_network_connections(self):
        """Open the Network Connections control panel."""
        try:
            os.system("ncpa.cpl")
            self.update_status("Opened Network Connections", True)
            self.append_output("✓ Opened Network Connections (ncpa.cpl)")
        except Exception as e:
            self.update_status("Failed to open Network Connections", False)
            self.append_output(f"✗ Error: {str(e)}")
    
    def open_network_settings(self):
        """Open Windows Network & Internet Settings."""
        try:
            os.system("start ms-settings:network")
            self.update_status("Opened Network & Internet Settings", True)
            self.append_output("✓ Opened Network & Internet Settings")
        except Exception as e:
            self.update_status("Failed to open Network Settings", False)
            self.append_output(f"✗ Error: {str(e)}")
    
    def open_sharing_settings(self):
        """Open Advanced Sharing Settings."""
        try:
            os.system("control /name Microsoft.NetworkAndSharingCenter /page Advanced")
            self.update_status("Opened Advanced Sharing Settings", True)
            self.append_output("✓ Opened Advanced Sharing Settings")
        except Exception as e:
            self.update_status("Failed to open Sharing Settings", False)
            self.append_output(f"✗ Error: {str(e)}")
    
    def refresh_ipconfig(self):
        """Display basic IP configuration."""
        self.update_status("Fetching IP Configuration...", True)
        success, stdout, stderr = run_cmd_command("ipconfig")
        
        if success:
            self.update_status("IP Configuration Retrieved", True)
            self.append_output("IP Configuration:\n" + stdout)
        else:
            self.update_status("Failed to get IP Configuration", False)
            self.append_output(f"✗ Error: {stderr if stderr else 'Unknown error'}")
    
    def refresh_ipconfig_all(self):
        """Display detailed IP configuration."""
        self.update_status("Fetching Detailed IP Configuration...", True)
        success, stdout, stderr = run_cmd_command("ipconfig /all")
        
        if success:
            self.update_status("Detailed IP Configuration Retrieved", True)
            self.append_output("Detailed IP Configuration:\n" + stdout)
        else:
            self.update_status("Failed to get IP Configuration", False)
            self.append_output(f"✗ Error: {stderr if stderr else 'Unknown error'}")
    
    def release_ip(self):
        """Release the current IP address."""
        self.update_status("Releasing IP Address...", True)
        success, stdout, stderr = run_cmd_command("ipconfig /release")
        
        if success:
            self.update_status("IP Address Released", True)
            self.append_output("✓ IP Address Released\n" + stdout)
        else:
            self.update_status("Failed to release IP Address", False)
            self.append_output(f"✗ Error: {stderr if stderr else stdout}")
    
    def renew_ip(self):
        """Renew the IP address."""
        self.update_status("Renewing IP Address...", True)
        success, stdout, stderr = run_cmd_command("ipconfig /renew")
        
        if success:
            self.update_status("IP Address Renewed", True)
            self.append_output("✓ IP Address Renewed\n" + stdout)
        else:
            self.update_status("Failed to renew IP Address", False)
            self.append_output(f"✗ Error: {stderr if stderr else stdout}")
    
    def flush_dns(self):
        """Flush the DNS resolver cache."""
        self.update_status("Flushing DNS Cache...", True)
        success, stdout, stderr = run_cmd_command("ipconfig /flushdns")
        
        if success:
            self.update_status("DNS Cache Flushed", True)
            self.append_output("✓ DNS Cache Flushed\n" + stdout)
        else:
            self.update_status("Failed to flush DNS Cache", False)
            self.append_output(f"✗ Error: {stderr if stderr else 'Unknown error'}")
    
    def display_dns(self):
        """Display the DNS resolver cache."""
        self.update_status("Fetching DNS Cache...", True)
        success, stdout, stderr = run_cmd_command("ipconfig /displaydns")
        
        if success:
            self.update_status("DNS Cache Retrieved", True)
            self.append_output("DNS Cache:\n" + stdout)
        else:
            self.update_status("Failed to get DNS Cache", False)
            self.append_output(f"✗ Error: {stderr if stderr else 'Unknown error'}")