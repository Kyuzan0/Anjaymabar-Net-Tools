// Modules
mod admin;
mod cache;
mod diagnostics;
mod file_manager;
mod firewall;
mod network;
mod network_unified;
mod smb;

// Re-export command functions
use admin::*;
use diagnostics::*;
use file_manager::*;
use firewall::*;
use network::*;
use network_unified::*;
use smb::*;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            // SMB Commands
            get_smb_settings,
            set_smb_guest_auth,
            set_smb_client_signature,
            set_smb_server_signature,
            reset_smb_settings,
            restart_smb_service,
            test_smb_connection,
            list_smb_shares,
            map_network_drive,
            unmap_network_drive,
            // Admin Commands
            is_admin,
            request_elevation,
            // Network Commands
            get_network_adapters,
            get_ip_configuration,
            apply_dhcp,
            apply_static_ip,
            run_ipconfig,
            release_ip,
            renew_ip,
            flush_dns,
            display_dns,
            open_network_connections,
            open_network_settings,
            // Network Unified Commands (optimized with caching)
            get_ip_configuration_unified,
            invalidate_adapter_cache,
            invalidate_all_network_cache,
            get_network_cache_stats,
            // Firewall Commands
            get_firewall_status,
            set_firewall_profile,
            enable_all_firewall,
            disable_all_firewall,
            open_firewall_settings,
            open_advanced_firewall,
            // Diagnostic Commands
            run_ping,
            run_tracert,
            run_nslookup,
            run_netstat,
            get_hostname,
            get_network_info,
            check_internet,
            // File Manager Commands
            open_in_file_explorer,
            open_smb_path,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
