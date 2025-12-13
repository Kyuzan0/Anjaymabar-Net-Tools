use serde::{Deserialize, Serialize};
use std::process::Command;
use std::os::windows::process::CommandExt;

const CREATE_NO_WINDOW: u32 = 0x08000000;

/// Firewall profile status (reserved for future use)
#[allow(dead_code)]
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct FirewallProfile {
    pub name: String,
    pub enabled: bool,
}

/// All firewall profiles status
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct FirewallStatus {
    pub domain: bool,
    pub private: bool,
    pub public: bool,
}

/// Get firewall status for all profiles
#[tauri::command]
pub fn get_firewall_status() -> Result<FirewallStatus, String> {
    let output = Command::new("powershell")
        .creation_flags(CREATE_NO_WINDOW)
        .args([
            "-NoProfile",
            "-Command",
            "Get-NetFirewallProfile | Select-Object Name, Enabled | ConvertTo-Json",
        ])
        .output()
        .map_err(|e| format!("Failed to execute PowerShell: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    let trimmed = stdout.trim();

    if trimmed.is_empty() {
        return Err("No firewall profile data returned".to_string());
    }

    // Parse JSON
    let profiles: Vec<serde_json::Value> = if trimmed.starts_with('[') {
        serde_json::from_str(trimmed).map_err(|e| format!("Failed to parse JSON: {}", e))?
    } else {
        let single: serde_json::Value =
            serde_json::from_str(trimmed).map_err(|e| format!("Failed to parse JSON: {}", e))?;
        vec![single]
    };

    let mut status = FirewallStatus {
        domain: false,
        private: false,
        public: false,
    };

    for profile in profiles {
        let name = profile["Name"].as_str().unwrap_or("").to_lowercase();
        let enabled = profile["Enabled"].as_bool().unwrap_or(false); // PowerShell returns boolean for Enabled property in JSON
        
        // Handle case where Enabled might be returned as integer 1/0 or string "True"/"False" depending on PS version
        let is_enabled = if profile["Enabled"].is_boolean() {
             profile["Enabled"].as_bool().unwrap_or(false)
        } else if profile["Enabled"].is_number() {
             profile["Enabled"].as_i64().unwrap_or(0) == 1
        } else {
             enabled
        };

        match name.as_str() {
            "domain" => status.domain = is_enabled,
            "private" => status.private = is_enabled,
            "public" => status.public = is_enabled,
            _ => {}
        }
    }

    Ok(status)
}

/// Enable or disable a specific firewall profile
#[tauri::command]
pub fn set_firewall_profile(profile: String, enabled: bool) -> Result<String, String> {
    let state = if enabled { "True" } else { "False" };
    let cmd = format!(
        "Set-NetFirewallProfile -Profile {} -Enabled {}",
        profile, state
    );

    let output = Command::new("powershell")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["-NoProfile", "-Command", &cmd])
        .output()
        .map_err(|e| format!("Failed to execute PowerShell: {}", e))?;

    if output.status.success() {
        let action = if enabled { "enabled" } else { "disabled" };
        Ok(format!("{} profile {}", profile, action))
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(format!("Failed to set {} profile: {}", profile, stderr))
    }
}

/// Enable all firewall profiles
#[tauri::command]
pub fn enable_all_firewall() -> Result<String, String> {
    let cmd = "Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True";

    let output = Command::new("powershell")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["-NoProfile", "-Command", cmd])
        .output()
        .map_err(|e| format!("Failed to execute PowerShell: {}", e))?;

    if output.status.success() {
        Ok("All firewall profiles enabled".to_string())
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(format!("Failed to enable all profiles: {}", stderr))
    }
}

/// Disable all firewall profiles
#[tauri::command]
pub fn disable_all_firewall() -> Result<String, String> {
    let cmd = "Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False";

    let output = Command::new("powershell")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["-NoProfile", "-Command", cmd])
        .output()
        .map_err(|e| format!("Failed to execute PowerShell: {}", e))?;

    if output.status.success() {
        Ok("All firewall profiles disabled".to_string())
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(format!("Failed to disable all profiles: {}", stderr))
    }
}

/// Open Windows Firewall settings
#[tauri::command]
pub fn open_firewall_settings() -> Result<String, String> {
    Command::new("cmd")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["/c", "control", "firewall.cpl"])
        .spawn()
        .map_err(|e| format!("Failed to open: {}", e))?;
    Ok("Opened Firewall Settings".to_string())
}

/// Open Advanced Firewall settings
#[tauri::command]
pub fn open_advanced_firewall() -> Result<String, String> {
    Command::new("cmd")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["/c", "wf.msc"])
        .spawn()
        .map_err(|e| format!("Failed to open: {}", e))?;
    Ok("Opened Advanced Firewall".to_string())
}
