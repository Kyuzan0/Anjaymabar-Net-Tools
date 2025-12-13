use serde::{Deserialize, Serialize};
use std::process::Command;
use std::os::windows::process::CommandExt;

const CREATE_NO_WINDOW: u32 = 0x08000000;

/// Network adapter information
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct NetworkAdapter {
    pub name: String,
    pub description: String,
    pub status: String,
    pub mac_address: String,
}

/// IP Configuration for an adapter
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct IPConfiguration {
    pub ip_address: String,
    pub subnet_mask: String,
    pub gateway: String,
    pub primary_dns: String,
    pub secondary_dns: String,
    pub dhcp_enabled: bool,
}

/// Get list of network adapters
#[tauri::command]
pub fn get_network_adapters() -> Result<Vec<NetworkAdapter>, String> {
    let output = Command::new("powershell")
        .creation_flags(CREATE_NO_WINDOW)
        .args([
            "-NoProfile",
            "-Command",
            r#"Get-NetAdapter | Where-Object {
                $_.InterfaceDescription -like '*PCI*' -or
                $_.PnPDeviceID -like '*PCI*' -or
                $_.InterfaceDescription -like '*Ethernet*' -or
                $_.InterfaceDescription -like '*Realtek*' -or
                $_.InterfaceDescription -like '*Intel*' -or
                $_.InterfaceDescription -like '*Killer*' -or
                $_.InterfaceDescription -like '*Qualcomm*' -or
                $_.InterfaceDescription -like '*Broadcom*' -or
                $_.InterfaceDescription -like '*Wi-Fi*' -or
                $_.InterfaceDescription -like '*Wireless*'
            } | Select-Object Name, InterfaceDescription, Status, MacAddress | ConvertTo-Json"#,
        ])
        .output()
        .map_err(|e| format!("Failed to execute PowerShell: {}", e))?;

    if !output.status.success() {
        // Fallback: get all adapters
        return get_all_adapters();
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    if stdout.trim().is_empty() {
        return get_all_adapters();
    }

    parse_adapters_json(&stdout)
}

fn get_all_adapters() -> Result<Vec<NetworkAdapter>, String> {
    let output = Command::new("powershell")
        .creation_flags(CREATE_NO_WINDOW)
        .args([
            "-NoProfile",
            "-Command",
            "Get-NetAdapter | Select-Object Name, InterfaceDescription, Status, MacAddress | ConvertTo-Json",
        ])
        .output()
        .map_err(|e| format!("Failed to execute PowerShell: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    parse_adapters_json(&stdout)
}

fn parse_adapters_json(json_str: &str) -> Result<Vec<NetworkAdapter>, String> {
    let trimmed = json_str.trim();
    if trimmed.is_empty() {
        return Ok(vec![]);
    }

    // Handle single object vs array
    let adapters: Vec<serde_json::Value> = if trimmed.starts_with('[') {
        serde_json::from_str(trimmed).map_err(|e| format!("Failed to parse JSON: {}", e))?
    } else {
        let single: serde_json::Value =
            serde_json::from_str(trimmed).map_err(|e| format!("Failed to parse JSON: {}", e))?;
        vec![single]
    };

    let result: Vec<NetworkAdapter> = adapters
        .iter()
        .map(|a| NetworkAdapter {
            name: a["Name"].as_str().unwrap_or("").to_string(),
            description: a["InterfaceDescription"].as_str().unwrap_or("").to_string(),
            status: a["Status"].as_str().unwrap_or("Unknown").to_string(),
            mac_address: a["MacAddress"].as_str().unwrap_or("").to_string(),
        })
        .collect();

    Ok(result)
}

/// Get IP configuration for a specific adapter
#[tauri::command]
pub fn get_ip_configuration(adapter_name: String) -> Result<IPConfiguration, String> {
    let mut config = IPConfiguration {
        ip_address: String::new(),
        subnet_mask: String::new(),
        gateway: String::new(),
        primary_dns: String::new(),
        secondary_dns: String::new(),
        dhcp_enabled: true,
    };

    // Get IP address
    let cmd = format!(
        r#"Get-NetIPAddress -InterfaceAlias "{}" -AddressFamily IPv4 | Select-Object IPAddress, PrefixLength | ConvertTo-Json"#,
        adapter_name
    );
    if let Ok(output) = Command::new("powershell")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["-NoProfile", "-Command", &cmd])
        .output()
    {
        let stdout = String::from_utf8_lossy(&output.stdout);
        if let Ok(data) = serde_json::from_str::<serde_json::Value>(stdout.trim()) {
            let data = if data.is_array() {
                data.get(0).cloned().unwrap_or(data)
            } else {
                data
            };
            config.ip_address = data["IPAddress"].as_str().unwrap_or("").to_string();
            let prefix = data["PrefixLength"].as_u64().unwrap_or(24) as u8;
            config.subnet_mask = prefix_to_subnet(prefix);
        }
    }

    // Get gateway
    let cmd = format!(
        r#"Get-NetRoute -InterfaceAlias "{}" -DestinationPrefix "0.0.0.0/0" -ErrorAction SilentlyContinue | Select-Object NextHop | ConvertTo-Json"#,
        adapter_name
    );
    if let Ok(output) = Command::new("powershell")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["-NoProfile", "-Command", &cmd])
        .output()
    {
        let stdout = String::from_utf8_lossy(&output.stdout);
        if let Ok(data) = serde_json::from_str::<serde_json::Value>(stdout.trim()) {
            let data = if data.is_array() {
                data.get(0).cloned().unwrap_or(data)
            } else {
                data
            };
            config.gateway = data["NextHop"].as_str().unwrap_or("").to_string();
        }
    }

    // Get DNS servers
    let cmd = format!(
        r#"Get-DnsClientServerAddress -InterfaceAlias "{}" -AddressFamily IPv4 | Select-Object ServerAddresses | ConvertTo-Json"#,
        adapter_name
    );
    if let Ok(output) = Command::new("powershell")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["-NoProfile", "-Command", &cmd])
        .output()
    {
        let stdout = String::from_utf8_lossy(&output.stdout);
        if let Ok(data) = serde_json::from_str::<serde_json::Value>(stdout.trim()) {
            let data = if data.is_array() {
                data.get(0).cloned().unwrap_or(data)
            } else {
                data
            };
            if let Some(servers) = data["ServerAddresses"].as_array() {
                if let Some(primary) = servers.get(0) {
                    config.primary_dns = primary.as_str().unwrap_or("").to_string();
                }
                if let Some(secondary) = servers.get(1) {
                    config.secondary_dns = secondary.as_str().unwrap_or("").to_string();
                }
            }
        }
    }

    // Check DHCP status
    let cmd = format!(
        r#"Get-NetIPInterface -InterfaceAlias "{}" -AddressFamily IPv4 | Select-Object Dhcp | ConvertTo-Json"#,
        adapter_name
    );
    if let Ok(output) = Command::new("powershell")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["-NoProfile", "-Command", &cmd])
        .output()
    {
        let stdout = String::from_utf8_lossy(&output.stdout);
        if let Ok(data) = serde_json::from_str::<serde_json::Value>(stdout.trim()) {
            let dhcp_val = data["Dhcp"].as_u64().unwrap_or(1);
            config.dhcp_enabled = dhcp_val == 1;
        }
    }

    Ok(config)
}

fn prefix_to_subnet(prefix: u8) -> String {
    let mask: u32 = if prefix >= 32 {
        0xFFFFFFFF
    } else {
        0xFFFFFFFF << (32 - prefix)
    };
    format!(
        "{}.{}.{}.{}",
        (mask >> 24) & 0xFF,
        (mask >> 16) & 0xFF,
        (mask >> 8) & 0xFF,
        mask & 0xFF
    )
}

fn subnet_to_prefix(subnet: &str) -> u8 {
    let parts: Vec<&str> = subnet.split('.').collect();
    if parts.len() != 4 {
        return 24;
    }

    let mut binary = String::new();
    for part in parts {
        if let Ok(num) = part.parse::<u8>() {
            binary.push_str(&format!("{:08b}", num));
        }
    }
    binary.chars().filter(|&c| c == '1').count() as u8
}

/// Apply DHCP configuration to adapter
#[tauri::command]
pub fn apply_dhcp(adapter_name: String) -> Result<String, String> {
    // Remove existing static IP
    let cmd = format!(
        r#"Remove-NetIPAddress -InterfaceAlias "{}" -AddressFamily IPv4 -Confirm:$false -ErrorAction SilentlyContinue"#,
        adapter_name
    );
    let _ = Command::new("powershell")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["-NoProfile", "-Command", &cmd])
        .output();

    // Remove existing gateway
    let cmd = format!(
        r#"Remove-NetRoute -InterfaceAlias "{}" -DestinationPrefix "0.0.0.0/0" -Confirm:$false -ErrorAction SilentlyContinue"#,
        adapter_name
    );
    let _ = Command::new("powershell")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["-NoProfile", "-Command", &cmd])
        .output();

    // Enable DHCP
    let cmd = format!(
        r#"Set-NetIPInterface -InterfaceAlias "{}" -Dhcp Enabled"#,
        adapter_name
    );
    let output = Command::new("powershell")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["-NoProfile", "-Command", &cmd])
        .output()
        .map_err(|e| format!("Failed to execute PowerShell: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("Failed to enable DHCP: {}", stderr));
    }

    // Reset DNS
    let cmd = format!(
        r#"Set-DnsClientServerAddress -InterfaceAlias "{}" -ResetServerAddresses"#,
        adapter_name
    );
    let _ = Command::new("powershell")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["-NoProfile", "-Command", &cmd])
        .output();

    Ok(format!("DHCP enabled on {}", adapter_name))
}

/// Apply static IP configuration
#[tauri::command]
pub fn apply_static_ip(
    adapter_name: String,
    ip_address: String,
    subnet_mask: String,
    gateway: String,
    primary_dns: String,
    secondary_dns: String,
) -> Result<String, String> {
    let prefix = subnet_to_prefix(&subnet_mask);

    // Remove existing IP
    let cmd = format!(
        r#"Remove-NetIPAddress -InterfaceAlias "{}" -AddressFamily IPv4 -Confirm:$false -ErrorAction SilentlyContinue"#,
        adapter_name
    );
    let _ = Command::new("powershell")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["-NoProfile", "-Command", &cmd])
        .output();

    // Remove existing gateway
    let cmd = format!(
        r#"Remove-NetRoute -InterfaceAlias "{}" -DestinationPrefix "0.0.0.0/0" -Confirm:$false -ErrorAction SilentlyContinue"#,
        adapter_name
    );
    let _ = Command::new("powershell")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["-NoProfile", "-Command", &cmd])
        .output();

    // Disable DHCP
    let cmd = format!(
        r#"Set-NetIPInterface -InterfaceAlias "{}" -Dhcp Disabled"#,
        adapter_name
    );
    let _ = Command::new("powershell")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["-NoProfile", "-Command", &cmd])
        .output();

    // Set new IP
    let cmd = if !gateway.is_empty() {
        format!(
            r#"New-NetIPAddress -InterfaceAlias "{}" -IPAddress "{}" -PrefixLength {} -DefaultGateway "{}""#,
            adapter_name, ip_address, prefix, gateway
        )
    } else {
        format!(
            r#"New-NetIPAddress -InterfaceAlias "{}" -IPAddress "{}" -PrefixLength {}"#,
            adapter_name, ip_address, prefix
        )
    };

    let output = Command::new("powershell")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["-NoProfile", "-Command", &cmd])
        .output()
        .map_err(|e| format!("Failed to set IP: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("Failed to set IP: {}", stderr));
    }

    // Set DNS
    if !primary_dns.is_empty() {
        let dns_servers = if !secondary_dns.is_empty() {
            format!(r#""{}","{}""#, primary_dns, secondary_dns)
        } else {
            format!(r#""{}""#, primary_dns)
        };

        let cmd = format!(
            r#"Set-DnsClientServerAddress -InterfaceAlias "{}" -ServerAddresses ({})"#,
            adapter_name, dns_servers
        );
        let _ = Command::new("powershell")
            .creation_flags(CREATE_NO_WINDOW)
            .args(["-NoProfile", "-Command", &cmd])
            .output();
    }

    Ok(format!("Static IP {} applied to {}", ip_address, adapter_name))
}

/// Run ipconfig command
#[tauri::command]
pub fn run_ipconfig(all: bool) -> Result<String, String> {
    let args = if all { "/all" } else { "" };
    let output = Command::new("cmd")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["/c", "ipconfig", args])
        .output()
        .map_err(|e| format!("Failed to run ipconfig: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    Ok(stdout.to_string())
}

/// Release IP address
#[tauri::command]
pub fn release_ip() -> Result<String, String> {
    let output = Command::new("cmd")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["/c", "ipconfig", "/release"])
        .output()
        .map_err(|e| format!("Failed to release IP: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    Ok(stdout.to_string())
}

/// Renew IP address
#[tauri::command]
pub fn renew_ip() -> Result<String, String> {
    let output = Command::new("cmd")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["/c", "ipconfig", "/renew"])
        .output()
        .map_err(|e| format!("Failed to renew IP: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    Ok(stdout.to_string())
}

/// Flush DNS cache
#[tauri::command]
pub fn flush_dns() -> Result<String, String> {
    let output = Command::new("cmd")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["/c", "ipconfig", "/flushdns"])
        .output()
        .map_err(|e| format!("Failed to flush DNS: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    Ok(stdout.to_string())
}

/// Display DNS cache
#[tauri::command]
pub fn display_dns() -> Result<String, String> {
    let output = Command::new("cmd")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["/c", "ipconfig", "/displaydns"])
        .output()
        .map_err(|e| format!("Failed to display DNS: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    Ok(stdout.to_string())
}

/// Open network connections
#[tauri::command]
pub fn open_network_connections() -> Result<String, String> {
    Command::new("cmd")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["/c", "ncpa.cpl"])
        .spawn()
        .map_err(|e| format!("Failed to open: {}", e))?;
    Ok("Opened Network Connections".to_string())
}

/// Open network settings
#[tauri::command]
pub fn open_network_settings() -> Result<String, String> {
    Command::new("cmd")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["/c", "start", "ms-settings:network"])
        .spawn()
        .map_err(|e| format!("Failed to open: {}", e))?;
    Ok("Opened Network Settings".to_string())
}
