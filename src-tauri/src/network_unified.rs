//! Unified network configuration query
//! Combines all 4 PowerShell queries into a single script for efficiency

use serde::{Deserialize, Serialize};
use std::os::windows::process::CommandExt;
use std::process::Command;

use crate::cache::NETWORK_CACHE;
use crate::network::IPConfiguration;

const CREATE_NO_WINDOW: u32 = 0x08000000;

/// Unified PowerShell script that fetches all network config in one call
/// This reduces 4 process spawns to 1, saving ~300-600ms
const UNIFIED_PS_SCRIPT: &str = r#"
param([string]$AdapterName)

$result = @{
    ip_address = ""
    prefix_length = 24
    gateway = ""
    primary_dns = ""
    secondary_dns = ""
    dhcp_enabled = $true
    error = $null
}

try {
    # Get IP Address and Prefix Length
    $ipInfo = Get-NetIPAddress -InterfaceAlias $AdapterName -AddressFamily IPv4 -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($ipInfo) {
        $result.ip_address = $ipInfo.IPAddress
        $result.prefix_length = $ipInfo.PrefixLength
    }

    # Get Default Gateway
    $route = Get-NetRoute -InterfaceAlias $AdapterName -DestinationPrefix "0.0.0.0/0" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($route) {
        $result.gateway = $route.NextHop
    }

    # Get DNS Servers
    $dns = Get-DnsClientServerAddress -InterfaceAlias $AdapterName -AddressFamily IPv4 -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($dns -and $dns.ServerAddresses) {
        if ($dns.ServerAddresses.Count -gt 0) {
            $result.primary_dns = $dns.ServerAddresses[0]
        }
        if ($dns.ServerAddresses.Count -gt 1) {
            $result.secondary_dns = $dns.ServerAddresses[1]
        }
    }

    # Get DHCP Status
    $interface = Get-NetIPInterface -InterfaceAlias $AdapterName -AddressFamily IPv4 -ErrorAction SilentlyContinue
    if ($interface) {
        $result.dhcp_enabled = ($interface.Dhcp -eq 'Enabled') -or ($interface.Dhcp -eq 1)
    }
}
catch {
    $result.error = $_.Exception.Message
}

$result | ConvertTo-Json -Compress
"#;

/// Response structure from unified PowerShell script
#[derive(Debug, Deserialize)]
struct UnifiedPSResponse {
    ip_address: String,
    prefix_length: u8,
    gateway: String,
    primary_dns: String,
    secondary_dns: String,
    dhcp_enabled: bool,
    error: Option<String>,
}

/// Convert CIDR prefix length to dotted-decimal subnet mask
/// 
/// # Examples
/// - prefix 24 -> "255.255.255.0"
/// - prefix 16 -> "255.255.0.0"
/// - prefix 8 -> "255.0.0.0"
fn prefix_to_subnet(prefix: u8) -> String {
    let mask: u32 = if prefix >= 32 {
        0xFFFFFFFF
    } else if prefix == 0 {
        0
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

/// Get IP configuration using unified query with caching
/// 
/// # Flow:
/// 1. Check cache for valid entry
/// 2. If cache hit, return immediately
/// 3. If cache miss, run unified PS script
/// 4. Parse response and update cache
/// 5. Return configuration
#[tauri::command]
pub fn get_ip_configuration_unified(adapter_name: String) -> Result<IPConfiguration, String> {
    // Step 1: Check cache first (fast path)
    if let Some(cached) = NETWORK_CACHE.get_ip_config(&adapter_name) {
        return Ok(cached);
    }

    // Step 2: Run unified PowerShell script
    let ps_command = format!(
        r#"& {{ {} }} -AdapterName '{}'"#,
        UNIFIED_PS_SCRIPT,
        adapter_name.replace("'", "''") // Escape single quotes
    );

    let output = Command::new("powershell")
        .creation_flags(CREATE_NO_WINDOW)
        .args([
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy", "Bypass",
            "-Command",
            &ps_command,
        ])
        .output()
        .map_err(|e| format!("Failed to execute PowerShell: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        
        // Try to return stale cache data if available
        if let Some((stale_data, _)) = NETWORK_CACHE.get_ip_config_stale(&adapter_name) {
            return Ok(stale_data);
        }
        
        return Err(format!("PowerShell error: {}", stderr));
    }

    // Step 3: Parse JSON response
    let stdout = String::from_utf8_lossy(&output.stdout);
    let trimmed = stdout.trim();
    
    if trimmed.is_empty() {
        return Err("Empty response from PowerShell".to_string());
    }

    let response: UnifiedPSResponse = serde_json::from_str(trimmed)
        .map_err(|e| format!("Failed to parse response: {} (raw: {})", e, trimmed))?;

    // Check for PowerShell-level errors
    if let Some(error) = response.error {
        if !error.is_empty() {
            return Err(format!("PowerShell script error: {}", error));
        }
    }

    // Step 4: Build and cache the result
    let subnet_mask = prefix_to_subnet(response.prefix_length);
    
    let config = IPConfiguration {
        ip_address: response.ip_address,
        subnet_mask,
        gateway: response.gateway,
        primary_dns: response.primary_dns,
        secondary_dns: response.secondary_dns,
        dhcp_enabled: response.dhcp_enabled,
    };

    // Step 5: Update cache
    NETWORK_CACHE.set_ip_config(&adapter_name, config.clone());

    Ok(config)
}

/// Invalidate cache for adapter (call after applying changes)
#[tauri::command]
pub fn invalidate_adapter_cache(adapter_name: String) {
    NETWORK_CACHE.invalidate_adapter(&adapter_name);
}

/// Invalidate all cached network configurations
#[tauri::command]
pub fn invalidate_all_network_cache() {
    NETWORK_CACHE.invalidate_all();
}

/// Get cache statistics (for debugging/monitoring)
#[tauri::command]
pub fn get_network_cache_stats() -> crate::cache::CacheStats {
    NETWORK_CACHE.stats()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_prefix_to_subnet_24() {
        assert_eq!(prefix_to_subnet(24), "255.255.255.0");
    }

    #[test]
    fn test_prefix_to_subnet_16() {
        assert_eq!(prefix_to_subnet(16), "255.255.0.0");
    }

    #[test]
    fn test_prefix_to_subnet_8() {
        assert_eq!(prefix_to_subnet(8), "255.0.0.0");
    }

    #[test]
    fn test_prefix_to_subnet_32() {
        assert_eq!(prefix_to_subnet(32), "255.255.255.255");
    }

    #[test]
    fn test_prefix_to_subnet_0() {
        assert_eq!(prefix_to_subnet(0), "0.0.0.0");
    }

    #[test]
    fn test_prefix_to_subnet_25() {
        assert_eq!(prefix_to_subnet(25), "255.255.255.128");
    }

    #[test]
    fn test_prefix_to_subnet_30() {
        assert_eq!(prefix_to_subnet(30), "255.255.255.252");
    }
}