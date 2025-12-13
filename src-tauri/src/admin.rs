use std::process::Command;
#[cfg(windows)]
use std::os::windows::process::CommandExt;

#[cfg(windows)]
const CREATE_NO_WINDOW: u32 = 0x08000000;

/// Check if the application is running with administrator privileges
#[tauri::command]
pub fn is_admin() -> bool {
    #[cfg(windows)]
    {
        // Use PowerShell to check admin status
        let output = Command::new("powershell")
            .creation_flags(CREATE_NO_WINDOW)
            .args([
                "-NoProfile",
                "-Command",
                "([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)"
            ])
            .output();

        match output {
            Ok(o) => {
                let result = String::from_utf8_lossy(&o.stdout);
                result.trim().eq_ignore_ascii_case("true")
            }
            Err(_) => false,
        }
    }

    #[cfg(not(windows))]
    {
        false
    }
}

/// Request elevation (restart as admin)
#[tauri::command]
pub fn request_elevation() -> Result<String, String> {
    #[cfg(windows)]
    {
        let exe_path = std::env::current_exe()
            .map_err(|e| format!("Failed to get executable path: {}", e))?;

        let output = Command::new("powershell")
            .creation_flags(CREATE_NO_WINDOW)
            .args([
                "-NoProfile",
                "-Command",
                &format!(
                    "Start-Process -FilePath '{}' -Verb RunAs",
                    exe_path.display()
                ),
            ])
            .output()
            .map_err(|e| format!("Failed to request elevation: {}", e))?;

        if output.status.success() {
            // Exit current instance
            std::process::exit(0);
        } else {
            let error = String::from_utf8_lossy(&output.stderr);
            Err(format!("Elevation request failed: {}", error))
        }
    }

    #[cfg(not(windows))]
    {
        Err("This feature is only available on Windows".to_string())
    }
}
