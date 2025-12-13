use std::path::Path;
#[cfg(not(target_os = "windows"))]
use std::process::Command;

/// Opens files or folders in the native file explorer
/// 
/// For Windows: Uses explorer.exe /select,<path> for files or explorer.exe <path> for folders
/// For macOS: Uses open -R <path> for files or open <path> for folders  
/// For Linux: Uses xdg-open <parent_path> or file manager specific commands
#[tauri::command]
pub async fn open_in_file_explorer(paths: Vec<String>) -> Result<(), String> {
    if paths.is_empty() {
        return Err("No paths provided".to_string());
    }

    for path_str in paths {
        let path = Path::new(&path_str);
        
        // Check if path exists
        if !path.exists() {
            return Err(format!("Path does not exist: {}", path_str));
        }

        #[cfg(target_os = "windows")]
        {
            open_in_explorer_windows(&path_str, path.is_dir())?;
        }

        #[cfg(target_os = "macos")]
        {
            open_in_explorer_macos(&path_str, path.is_dir())?;
        }

        #[cfg(target_os = "linux")]
        {
            open_in_explorer_linux(&path_str, path.is_dir())?;
        }
    }

    Ok(())
}

#[cfg(target_os = "windows")]
fn open_in_explorer_windows(path: &str, is_dir: bool) -> Result<(), String> {
    use std::os::windows::process::CommandExt;
    use std::process::Command;
    
    let result = if is_dir {
        // For directories, quote the path to handle spaces
        let quoted_path = format!("\"{}\"", path);
        Command::new("explorer.exe")
            .raw_arg(&quoted_path)
            .spawn()
    } else {
        // For files, use /select, with quoted path to handle spaces
        // Format: explorer.exe /select,"C:\path with spaces\file.txt"
        let select_arg = format!("/select,\"{}\"", path);
        Command::new("explorer.exe")
            .raw_arg(&select_arg)
            .spawn()
    };

    match result {
        Ok(_) => Ok(()),
        Err(e) => Err(format!("Failed to open file explorer: {}", e)),
    }
}

#[cfg(target_os = "macos")]
fn open_in_explorer_macos(path: &str, is_dir: bool) -> Result<(), String> {
    let result = if is_dir {
        // For directories, just open the folder
        Command::new("open")
            .arg(path)
            .spawn()
    } else {
        // For files, use -R to reveal the file in Finder
        Command::new("open")
            .arg("-R")
            .arg(path)
            .spawn()
    };

    match result {
        Ok(_) => Ok(()),
        Err(e) => Err(format!("Failed to open Finder: {}", e)),
    }
}

#[cfg(target_os = "linux")]
fn open_in_explorer_linux(path: &str, is_dir: bool) -> Result<(), String> {
    let target_path = if is_dir {
        path.to_string()
    } else {
        // For files, get the parent directory
        Path::new(path)
            .parent()
            .map(|p| p.to_string_lossy().to_string())
            .unwrap_or_else(|| path.to_string())
    };

    // Try xdg-open first (works on most Linux distros)
    let result = Command::new("xdg-open")
        .arg(&target_path)
        .spawn();

    match result {
        Ok(_) => Ok(()),
        Err(_) => {
            // Fallback to nautilus (GNOME file manager)
            let fallback = Command::new("nautilus")
                .arg(&target_path)
                .spawn();
            
            match fallback {
                Ok(_) => Ok(()),
                Err(e) => Err(format!("Failed to open file manager: {}", e)),
            }
        }
    }
}

/// Opens an SMB path in Windows Explorer
///
/// Constructs a UNC path from server and optional share name, then opens it in Explorer.
/// Example: open_smb_path("192.168.2.133", Some("shared")) opens \\192.168.2.133\shared
#[tauri::command]
pub async fn open_smb_path(server: String, share: Option<String>) -> Result<(), String> {
    if server.is_empty() {
        return Err("Server address is required".to_string());
    }

    // Build UNC path: \\server\share or \\server
    let unc_path = match share {
        Some(s) if !s.is_empty() => format!("\\\\{}\\{}", server, s),
        _ => format!("\\\\{}", server),
    };

    #[cfg(target_os = "windows")]
    {
        use std::os::windows::process::CommandExt;
        
        // For paths with spaces, explorer.exe needs the path wrapped in quotes
        // Using raw_arg to prevent Rust from adding extra escaping
        let quoted_path = format!("\"{}\"", unc_path);
        
        let result = std::process::Command::new("explorer.exe")
            .raw_arg(&quoted_path)
            .spawn();

        match result {
            Ok(_) => Ok(()),
            Err(e) => Err(format!("Failed to open file explorer: {}", e)),
        }
    }

    #[cfg(not(target_os = "windows"))]
    {
        Err("SMB path opening is only supported on Windows".to_string())
    }
}