use std::env;
use std::fs;
use std::path::Path;

fn main() {
    // Enable detailed build output for debugging
    unsafe { env::set_var("RUST_LOG", "debug"); }
    
    // Embed Windows manifest for Administrator privileges
    #[cfg(windows)]
    {
        println!("cargo:warning=Building for Windows platform");
        
        // Validate Windows build environment
        if let Err(e) = validate_windows_environment() {
            eprintln!("Build error: Windows environment validation failed: {}", e);
            std::process::exit(1);
        }
        
        // Check if manifest file exists
        let manifest_path = Path::new("app.manifest");
        if !manifest_path.exists() {
            eprintln!("Build error: Windows manifest file not found at: {:?}", manifest_path);
            std::process::exit(1);
        }
        
        // Read and validate manifest content
        let manifest_content = match fs::read_to_string(manifest_path) {
            Ok(content) => {
                println!("cargo:warning=Successfully loaded Windows manifest ({} bytes)", content.len());
                content
            }
            Err(e) => {
                eprintln!("Build error: Failed to read Windows manifest: {}", e);
                std::process::exit(1);
            }
        };
        
        // Validate manifest XML structure (basic check)
        if !manifest_content.contains("<assembly") || !manifest_content.contains("</assembly>") {
            eprintln!("Build error: Invalid manifest file format - missing assembly tags");
            std::process::exit(1);
        }
        
        let mut windows = tauri_build::WindowsAttributes::new();
        windows = windows.app_manifest(&manifest_content);
        
        println!("cargo:warning=Configuring Tauri build with Windows attributes");
        
        // Replace .expect() with proper error handling
        match tauri_build::try_build(
            tauri_build::Attributes::new()
                .windows_attributes(windows)
        ) {
            Ok(_) => {
                println!("cargo:warning=Tauri build configuration completed successfully");
            }
            Err(e) => {
                eprintln!("Build error: Failed to configure Tauri build: {}", e);
                eprintln!("Build error: This might be due to missing dependencies or invalid configuration");
                eprintln!("Build error: Please ensure all required tools are installed and the manifest is valid");
                std::process::exit(1);
            }
        }
    }
    
    #[cfg(not(windows))]
    {
        println!("cargo:warning=Building for non-Windows platform");
        match tauri_build::build() {
            Ok(_) => {
                println!("cargo:warning=Tauri build configuration completed successfully");
            }
            Err(e) => {
                eprintln!("Build error: Failed to configure Tauri build: {}", e);
                std::process::exit(1);
            }
        }
    }
}

#[cfg(windows)]
fn validate_windows_environment() -> Result<(), String> {
    // Check for Windows-specific build requirements
    println!("cargo:warning=Validating Windows build environment");
    
    // Check if we're actually on Windows
    if !cfg!(target_os = "windows") {
        return Err("Not building on Windows target".to_string());
    }
    
    // Check for common Windows build tools
    let required_tools = vec!["cargo", "rustc"];
    
    for tool in required_tools {
        match std::process::Command::new(tool).arg("--version").output() {
            Ok(output) => {
                let version = String::from_utf8_lossy(&output.stdout);
                println!("cargo:warning=Found {} version: {}", tool, version.trim());
            }
            Err(e) => {
                return Err(format!("Required tool '{}' not found: {}", tool, e));
            }
        }
    }
    
    // Check for Windows SDK (basic check)
    match std::process::Command::new("cmd").args(&["/C", "where", "rc.exe"]).output() {
        Ok(output) if output.status.success() => {
            println!("cargo:warning=Windows SDK tools found");
        }
        _ => {
            println!("cargo:warning=Windows SDK tools not found in PATH - this might cause issues");
        }
    }
    
    Ok(())
}
