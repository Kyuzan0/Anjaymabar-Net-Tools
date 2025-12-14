import { invoke } from '@tauri-apps/api/core';

// ============== SMB Types & Commands ==============

export interface SMBSettings {
    guest_auth_enabled: boolean;
    client_signature_required: boolean;
    server_signature_required: boolean;
}

export async function getSMBSettings(): Promise<SMBSettings> {
    return await invoke<SMBSettings>('get_smb_settings');
}

export async function setSMBGuestAuth(enabled: boolean): Promise<string> {
    return await invoke<string>('set_smb_guest_auth', { enabled });
}

export async function setSMBClientSignature(enabled: boolean): Promise<string> {
    return await invoke<string>('set_smb_client_signature', { enabled });
}

export async function setSMBServerSignature(enabled: boolean): Promise<string> {
    return await invoke<string>('set_smb_server_signature', { enabled });
}

export async function resetSMBSettings(): Promise<string> {
    return await invoke<string>('reset_smb_settings');
}

export async function restartSMBService(): Promise<string> {
    return await invoke<string>('restart_smb_service');
}

export async function openAdvancedSharing(): Promise<string> {
    return await invoke<string>('open_advanced_sharing');
}

export interface SmbShare {
    name: string;
    path: string;
    description: string;
}

export async function testSMBConnection(host: string): Promise<string> {
    return await invoke('test_smb_connection', { host });
}

export async function listSMBShares(host: string, username?: string, password?: string): Promise<SmbShare[]> {
    return await invoke('list_smb_shares', { host, username, password });
}

export async function mapNetworkDrive(driveLetter: string, path: string, username?: string, password?: string): Promise<string> {
    return await invoke('map_network_drive', { drive_letter: driveLetter, path, username, password });
}

export async function unmapNetworkDrive(driveLetter: string): Promise<string> {
    return await invoke('unmap_network_drive', { drive_letter: driveLetter });
}

// ============== Admin Commands ==============

export async function isAdmin(): Promise<boolean> {
    return await invoke<boolean>('is_admin');
}

export async function requestElevation(): Promise<string> {
    return await invoke<string>('request_elevation');
}

// ============== Network Types & Commands ==============

export interface NetworkAdapter {
    name: string;
    description: string;
    status: string;
    mac_address: string;
}

export interface IPConfiguration {
    ip_address: string;
    subnet_mask: string;
    gateway: string;
    primary_dns: string;
    secondary_dns: string;
    dhcp_enabled: boolean;
}

export async function getNetworkAdapters(): Promise<NetworkAdapter[]> {
    return await invoke<NetworkAdapter[]>('get_network_adapters');
}

export async function getIPConfiguration(adapterName: string): Promise<IPConfiguration> {
    return await invoke<IPConfiguration>('get_ip_configuration', { adapterName });
}

export async function applyDHCP(adapterName: string): Promise<string> {
    return await invoke<string>('apply_dhcp', { adapterName });
}

export async function applyStaticIP(
    adapterName: string,
    ipAddress: string,
    subnetMask: string,
    gateway: string,
    primaryDns: string,
    secondaryDns: string
): Promise<string> {
    return await invoke<string>('apply_static_ip', {
        adapterName,
        ipAddress,
        subnetMask,
        gateway,
        primaryDns,
        secondaryDns,
    });
}

export async function runIpconfig(all: boolean = false): Promise<string> {
    return await invoke<string>('run_ipconfig', { all });
}

export async function releaseIP(): Promise<string> {
    return await invoke<string>('release_ip');
}

export async function renewIP(): Promise<string> {
    return await invoke<string>('renew_ip');
}

export async function flushDNS(): Promise<string> {
    return await invoke<string>('flush_dns');
}

export async function displayDNS(): Promise<string> {
    return await invoke<string>('display_dns');
}

export async function openNetworkConnections(): Promise<string> {
    return await invoke<string>('open_network_connections');
}

export async function openNetworkSettings(): Promise<string> {
    return await invoke<string>('open_network_settings');
}

// ============== Firewall Types & Commands ==============

export interface FirewallStatus {
    domain: boolean;
    private: boolean;
    public: boolean;
}

export async function getFirewallStatus(): Promise<FirewallStatus> {
    return await invoke<FirewallStatus>('get_firewall_status');
}

export async function setFirewallProfile(profile: string, enabled: boolean): Promise<string> {
    return await invoke<string>('set_firewall_profile', { profile, enabled });
}

export async function enableAllFirewall(): Promise<string> {
    return await invoke<string>('enable_all_firewall');
}

export async function disableAllFirewall(): Promise<string> {
    return await invoke<string>('disable_all_firewall');
}

export async function openFirewallSettings(): Promise<string> {
    return await invoke<string>('open_firewall_settings');
}

export async function openAdvancedFirewall(): Promise<string> {
    return await invoke<string>('open_advanced_firewall');
}

// ============== Diagnostic Commands ==============

export async function runPing(host: string, count: number = 4): Promise<string> {
    return await invoke<string>('run_ping', { host, count });
}

export async function runTracert(host: string): Promise<string> {
    return await invoke<string>('run_tracert', { host });
}

export async function runNslookup(host: string): Promise<string> {
    return await invoke<string>('run_nslookup', { host });
}

export async function runNetstat(option: string = 'all'): Promise<string> {
    return await invoke<string>('run_netstat', { option });
}

export async function getHostname(): Promise<string> {
    return await invoke<string>('get_hostname');
}

export async function getNetworkInfo(): Promise<string> {
    return await invoke<string>('get_network_info');
}

export async function checkInternet(): Promise<boolean> {
    return await invoke<boolean>('check_internet');
}

// ============== File Manager Commands ==============

export async function openInFileExplorer(paths: string[]): Promise<void> {
    return await invoke<void>('open_in_file_explorer', { paths });
}

export async function openSmbPath(server: string, share?: string): Promise<void> {
    return await invoke<void>('open_smb_path', { server, share });
}

// ============== Optimized Network Commands ==============

/**
 * Get IP configuration using the unified/optimized Tauri command
 * This combines all 4 PowerShell queries into a single call with caching
 *
 * @param adapterName - Name of the network adapter
 * @returns IP configuration for the adapter
 */
export async function getIPConfigurationUnified(adapterName: string): Promise<IPConfiguration> {
    return await invoke<IPConfiguration>('get_ip_configuration_unified', { adapterName });
}

/**
 * Invalidate the Rust-side cache for a specific adapter
 * Call this after applying configuration changes
 *
 * @param adapterName - Name of the adapter to invalidate cache for
 */
export async function invalidateAdapterCache(adapterName: string): Promise<void> {
    return await invoke<void>('invalidate_adapter_cache', { adapterName });
}

/**
 * Invalidate all network-related caches on the Rust side
 * Call this for a full refresh
 */
export async function invalidateAllNetworkCache(): Promise<void> {
    return await invoke<void>('invalidate_all_network_cache');
}

/**
 * Cache statistics for debugging/monitoring
 */
export interface CacheStats {
    cached_configs: number;
    has_adapter_list: boolean;
}

/**
 * Get cache statistics from Rust backend
 * Useful for debugging and monitoring cache effectiveness
 */
export async function getCacheStats(): Promise<CacheStats> {
    return await invoke<CacheStats>('get_cache_stats');
}
