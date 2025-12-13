use std::process::Command;
use std::os::windows::process::CommandExt;

const CREATE_NO_WINDOW: u32 = 0x08000000;

/// Run ping command
#[tauri::command]
pub fn run_ping(host: String, count: u32) -> Result<String, String> {
    let count_str = count.to_string();
    let output = Command::new("ping")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["-n", &count_str, &host])
        .output()
        .map_err(|e| format!("Failed to run ping: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);

    if !stdout.is_empty() {
        Ok(stdout.to_string())
    } else {
        Err(stderr.to_string())
    }
}

/// Run tracert command
#[tauri::command]
pub fn run_tracert(host: String) -> Result<String, String> {
    let output = Command::new("tracert")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["-d", &host])
        .output()
        .map_err(|e| format!("Failed to run tracert: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    Ok(stdout.to_string())
}

/// Run nslookup command
#[tauri::command]
pub fn run_nslookup(host: String) -> Result<String, String> {
    let output = Command::new("nslookup")
        .creation_flags(CREATE_NO_WINDOW)
        .arg(&host)
        .output()
        .map_err(|e| format!("Failed to run nslookup: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    Ok(stdout.to_string())
}

/// Run netstat command
#[tauri::command]
pub fn run_netstat(option: String) -> Result<String, String> {
    let args: Vec<&str> = match option.as_str() {
        "all" => vec!["-a", "-n"],
        "listening" => vec!["-a", "-n", "-p", "TCP"],
        "stats" => vec!["-s"],
        "routes" => vec!["-r"],
        _ => vec!["-a"],
    };

    let output = Command::new("netstat")
        .creation_flags(CREATE_NO_WINDOW)
        .args(&args)
        .output()
        .map_err(|e| format!("Failed to run netstat: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    Ok(stdout.to_string())
}

/// Get hostname
#[tauri::command]
pub fn get_hostname() -> Result<String, String> {
    let output = Command::new("hostname")
        .creation_flags(CREATE_NO_WINDOW)
        .output()
        .map_err(|e| format!("Failed to get hostname: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    Ok(stdout.trim().to_string())
}

/// Get system network info
#[tauri::command]
pub fn get_network_info() -> Result<String, String> {
    let output = Command::new("powershell")
        .creation_flags(CREATE_NO_WINDOW)
        .args([
            "-NoProfile",
            "-Command",
            r#"
            $info = @{}
            $info['Hostname'] = $env:COMPUTERNAME
            $info['Username'] = $env:USERNAME
            $info['Domain'] = (Get-WmiObject Win32_ComputerSystem).Domain
            $info | ConvertTo-Json
            "#,
        ])
        .output()
        .map_err(|e| format!("Failed to get network info: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    Ok(stdout.to_string())
}

/// Check internet connectivity
#[tauri::command]
pub fn check_internet() -> Result<bool, String> {
    let output = Command::new("ping")
        .creation_flags(CREATE_NO_WINDOW)
        .args(["-n", "1", "-w", "3000", "8.8.8.8"])
        .output()
        .map_err(|e| format!("Failed to check internet: {}", e))?;

    Ok(output.status.success())
}
