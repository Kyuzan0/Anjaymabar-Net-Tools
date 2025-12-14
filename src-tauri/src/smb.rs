use std::process::Command;
use std::os::windows::process::CommandExt;
use winreg::enums::*;
use winreg::RegKey;

const CREATE_NO_WINDOW: u32 = 0x08000000;

#[derive(serde::Serialize)]
pub struct SMBSettings {
    pub guest_auth_enabled: bool,
    pub client_signature_required: bool,
    pub server_signature_required: bool,
}

#[tauri::command]
pub fn get_smb_settings() -> Result<SMBSettings, String> {
    let hklm = RegKey::predef(HKEY_LOCAL_MACHINE);
    
    // Check Guest Auth
    let lanman_workstation = hklm
        .open_subkey("SYSTEM\\CurrentControlSet\\Services\\LanmanWorkstation\\Parameters")
        .map_err(|e| e.to_string())?;
    let guest_auth: u32 = lanman_workstation
        .get_value("AllowInsecureGuestAuth")
        .unwrap_or(0);

    // Check Client Signature (RequireSecuritySignature)
    let client_signature: u32 = lanman_workstation
        .get_value("RequireSecuritySignature")
        .unwrap_or(0);

    // Check Server Signature (RequireSecuritySignature)
    let lanman_server = hklm
        .open_subkey("SYSTEM\\CurrentControlSet\\Services\\LanmanServer\\Parameters")
        .map_err(|e| e.to_string())?;
    let server_signature: u32 = lanman_server
        .get_value("RequireSecuritySignature")
        .unwrap_or(0);

    Ok(SMBSettings {
        guest_auth_enabled: guest_auth == 1,
        client_signature_required: client_signature == 1,
        server_signature_required: server_signature == 1,
    })
}

#[tauri::command]
pub fn set_smb_guest_auth(enabled: bool) -> Result<String, String> {
    let value = if enabled { 1u32 } else { 0u32 };
    let hklm = RegKey::predef(HKEY_LOCAL_MACHINE);
    let key = hklm
        .open_subkey_with_flags(
            "SYSTEM\\CurrentControlSet\\Services\\LanmanWorkstation\\Parameters",
            KEY_WRITE,
        )
        .map_err(|e| format!("Failed to open registry key: {}", e))?;

    key.set_value("AllowInsecureGuestAuth", &value)
        .map_err(|e| format!("Failed to write registry value: {}", e))?;

    Ok(format!("Guest Auth set to {}", enabled))
}

#[tauri::command]
pub fn set_smb_client_signature(enabled: bool) -> Result<String, String> {
    let value = if enabled { 1u32 } else { 0u32 };
    let hklm = RegKey::predef(HKEY_LOCAL_MACHINE);
    let key = hklm
        .open_subkey_with_flags(
            "SYSTEM\\CurrentControlSet\\Services\\LanmanWorkstation\\Parameters",
            KEY_WRITE,
        )
        .map_err(|e| format!("Failed to open registry key: {}", e))?;

    key.set_value("RequireSecuritySignature", &value)
        .map_err(|e| format!("Failed to write registry value: {}", e))?;

    Ok(format!("Client Signature set to {}", enabled))
}

#[tauri::command]
pub fn set_smb_server_signature(enabled: bool) -> Result<String, String> {
    let value = if enabled { 1u32 } else { 0u32 };
    let hklm = RegKey::predef(HKEY_LOCAL_MACHINE);
    let key = hklm
        .open_subkey_with_flags(
            "SYSTEM\\CurrentControlSet\\Services\\LanmanServer\\Parameters",
            KEY_WRITE,
        )
        .map_err(|e| format!("Failed to open registry key: {}", e))?;

    key.set_value("RequireSecuritySignature", &value)
        .map_err(|e| format!("Failed to write registry value: {}", e))?;

    Ok(format!("Server Signature set to {}", enabled))
}

#[tauri::command]
pub fn reset_smb_settings() -> Result<String, String> {
    // 1. Disable Guest Auth (Secure default)
    set_smb_guest_auth(false)?;
    
    // 2. Enable Client Signature (Secure default)
    set_smb_client_signature(true)?;
    
    // 3. Enable Server Signature (Secure default)
    set_smb_server_signature(true)?;

    Ok("All SMB settings reset to secure defaults".to_string())
}

#[tauri::command]
pub fn restart_smb_service() -> Result<String, String> {
    let output = Command::new("powershell")
        .creation_flags(CREATE_NO_WINDOW)
        .args([
            "-NoProfile",
            "-Command",
            "Restart-Service LanmanWorkstation -Force; Restart-Service LanmanServer -Force",
        ])
        .output()
        .map_err(|e| format!("Failed to execute PowerShell: {}", e))?;

    if output.status.success() {
        Ok("SMB Services restarted successfully".to_string())
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(format!("Failed to restart services: {}", stderr))
    }
}

#[derive(serde::Serialize)]
pub struct SmbShare {
    pub name: String,
    pub path: String,
    pub description: String,
}

#[tauri::command]
pub fn test_smb_connection(host: String) -> Result<String, String> {
    // Simple ping check first
    let output = Command::new("ping")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["-n", "1", "-w", "2000", &host])
        .output()
        .map_err(|e| format!("Failed to execute ping: {}", e))?;

    if !output.status.success() {
        return Err(format!("Host {} is unreachable", host));
    }

    // Check port 445 (SMB) using PowerShell
    let cmd = format!(
        "Test-NetConnection -ComputerName {} -Port 445 -InformationLevel Quiet",
        host
    );
    
    let output = Command::new("powershell")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["-NoProfile", "-Command", &cmd])
        .output()
        .map_err(|e| format!("Failed to execute PowerShell: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    if stdout.trim().to_lowercase() == "true" {
        Ok(format!("Successfully connected to SMB on {}", host))
    } else {
        Err(format!("SMB port (445) on {} is closed or blocked", host))
    }
}

#[tauri::command]
pub fn list_smb_shares(host: String, _username: Option<String>, _password: Option<String>) -> Result<Vec<SmbShare>, String> {
    // Note: net view doesn't support credentials directly in args
    // For authenticated access, use 'net use' first to establish connection
    // TODO: Implement credential handling via net use before net view

    // Use net view
    let output = Command::new("net")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["view", &format!("\\\\{}", host)])
        .output()
        .map_err(|e| format!("Failed to execute net view: {}", e))?;

    // Note: 'net view' output parsing is tricky and locale-dependent.
    // For a robust solution, we might need WMI or PowerShell Get-SmbShare (but that works locally).
    // For remote listing without domain, 'net view' is standard but requires parsing.
    
    // Alternative: PowerShell Get-SmbShare -CimSession (requires WinRM)
    // Fallback: Just return raw output for now or simple parsing
    
    let stdout = String::from_utf8_lossy(&output.stdout);
    if !output.status.success() {
        return Err(stdout.to_string());
    }

    // Parse net view output - format is column-based:
    // "Share name       Type    Used as  Comment"
    // "ShareName        Disk             Description here"
    // The share name column is typically up to the "Type" column (Disk/Print/IPC)
    let mut shares = Vec::new();
    let mut found_separator = false;
    
    for line in stdout.lines() {
        let trimmed = line.trim();
        
        // Skip empty lines and header lines
        if trimmed.is_empty() ||
           trimmed.starts_with("Shared resources") ||
           trimmed.starts_with("Share name") ||
           trimmed.contains("command completed") {
            continue;
        }
        
        // Look for the separator line (------) to know data starts after it
        if trimmed.starts_with("---") || trimmed.starts_with("───") {
            found_separator = true;
            continue;
        }
        
        // Only parse lines after the separator
        if !found_separator {
            continue;
        }
        
        // net view output format: "ShareName       Disk           Comment text here"
        // The "Disk" (or "Print", "IPC") keyword marks the type column
        // Share name is everything before the type keyword
        
        // Find the type column (Disk, Print, IPC) which indicates end of share name
        let type_patterns = ["  Disk", "  Print", "  IPC"];
        let mut share_name = String::new();
        let mut description = String::new();
        
        for pattern in &type_patterns {
            if let Some(pos) = line.find(pattern) {
                // Share name is everything before the type, trimmed
                share_name = line[..pos].trim().to_string();
                // Description is after the type (skip "Disk" + spaces)
                let after_type = &line[pos + pattern.len()..];
                description = after_type.trim().to_string();
                break;
            }
        }
        
        // If no type pattern found, try splitting by multiple spaces (fallback)
        if share_name.is_empty() && !trimmed.is_empty() {
            // Use regex-like splitting: split by 2+ spaces
            let parts: Vec<&str> = trimmed.split("  ")
                .filter(|s| !s.is_empty())
                .collect();
            if !parts.is_empty() {
                share_name = parts[0].trim().to_string();
                if parts.len() > 2 {
                    description = parts[2..].join(" ").trim().to_string();
                }
            }
        }
        
        if !share_name.is_empty() {
            shares.push(SmbShare {
                name: share_name.clone(),
                path: format!("\\\\{}\\{}", host, share_name),
                description,
            });
        }
    }

    Ok(shares)
}

#[tauri::command]
pub fn map_network_drive(drive_letter: String, path: String, username: Option<String>, password: Option<String>) -> Result<String, String> {
    let mut args = vec!["use".to_string(), drive_letter.clone(), path.clone()];
    
    // Handle credentials
    // Note: passing password in args is visible in process list, but for local tool it's acceptable-ish.
    // Better way is using WNetAddConnection2 API via FFI, but that's complex.
    if let (Some(u), Some(p)) = (username, password) {
        args.push(p);
        args.push(format!("/user:{}", u));
    }

    let args_refs: Vec<&str> = args.iter().map(|s| s.as_str()).collect();
    let output = Command::new("net")
        .creation_flags(CREATE_NO_WINDOW)
        .args(&args_refs)
        .output()
        .map_err(|e| format!("Failed to map drive: {}", e))?;

    if output.status.success() {
        Ok(format!("Mapped {} to {}", drive_letter, path))
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(stderr.to_string())
    }
}

#[tauri::command]
pub fn unmap_network_drive(drive_letter: String) -> Result<String, String> {
    let output = Command::new("net")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["use", &drive_letter, "/delete", "/y"])
        .output()
        .map_err(|e| format!("Failed to unmap drive: {}", e))?;

    if output.status.success() {
        Ok(format!("Unmapped {}", drive_letter))
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(stderr.to_string())
    }
}

/// Open Advanced Sharing Settings
#[tauri::command]
pub fn open_advanced_sharing() -> Result<String, String> {
    Command::new("cmd")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["/c", "control", "/name", "Microsoft.NetworkAndSharingCenter", "/page", "Advanced"])
        .spawn()
        .map_err(|e| format!("Failed to open Advanced Sharing Settings: {}", e))?;
    Ok("Opened Advanced Sharing Settings".to_string())
}
