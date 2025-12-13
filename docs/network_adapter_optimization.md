
# Network Adapter Loading Performance Optimization

## Technical Solution Document

**Version:** 1.0  
**Date:** December 2024  
**Project:** Anjaymabar Net Tools (AM Net Tools)  
**Target:** Rust + Tauri + React Architecture

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current Bottlenecks Analysis](#2-current-bottlenecks-analysis)
3. [Implementation Code Examples](#3-implementation-code-examples)
4. [Performance Benchmarks](#4-performance-benchmarks)
5. [Edge Cases & Error Handling](#5-edge-cases--error-handling)
6. [Implementation Checklist](#6-implementation-checklist)
7. [File Changes Summary](#7-file-changes-summary)

---

## 1. Executive Summary

### Problem Statement

The current network adapter configuration loading experiences significant latency (550-1500ms) when switching between adapters. This creates a poor user experience with noticeable UI freezes and slow responsiveness.

### Current Performance

| Metric | Value | Issue |
|--------|-------|-------|
| Adapter switch latency | 550-1500ms | Unacceptable UX |
| PowerShell calls per load | 4 sequential | Blocking main thread |
| Cache implementation | None | Redundant calls |
| Debouncing | None | Rapid switches cause queue |

### Target Performance

| Metric | Target Value | Improvement |
|--------|--------------|-------------|
| Perceived latency | <150ms | 70-90% faster |
| Cache hit response | <10ms | 99%+ faster |
| PowerShell calls | 1 unified | 75% reduction |
| Memory overhead | <5MB cache | Minimal impact |

### Key Optimizations

1. **Combined PowerShell Scripts** - Single script fetching ALL data (IP, Gateway, DNS, DHCP status)
2. **Rust-side Caching** - `lazy_static!` singleton with TTL-based invalidation
3. **React-side Caching** - Map-based storage with stale data fallback
4. **Debouncing** - 150ms delay on adapter selection changes
5. **Skeleton UI** - Immediate visual feedback during loading

---

## 2. Current Bottlenecks Analysis

### 2.1 Rust Backend (`network.rs`)

**File:** [`am_net_tools/src-tauri/src/network.rs`](../am_net_tools/src-tauri/src/network.rs)

#### Current Issue: 4 Sequential PowerShell Calls

```rust
// Lines 107-209: get_ip_configuration() function
// Problem: Each section spawns a new PowerShell process

// Call 1: Get IP Address (lines 120-140)
let cmd = format!(r#"Get-NetIPAddress -InterfaceAlias "{}" ..."#);

// Call 2: Get Gateway (lines 143-161)  
let cmd = format!(r#"Get-NetRoute -InterfaceAlias "{}" ..."#);

// Call 3: Get DNS Servers (lines 164-189)
let cmd = format!(r#"Get-DnsClientServerAddress -InterfaceAlias "{}" ..."#);

// Call 4: Check DHCP Status (lines 192-206)
let cmd = format!(r#"Get-NetIPInterface -InterfaceAlias "{}" ..."#);
```

**Impact:**
- Each `Command::new("powershell")` spawns a new process (~100-200ms overhead)
- Sequential execution = 4 × (100-200ms) = 400-800ms minimum
- No caching = same calls repeated on every adapter switch

### 2.2 React Frontend (`NetworkTab.tsx`)

**File:** [`am_net_tools/src/components/NetworkTab.tsx`](../am_net_tools/src/components/NetworkTab.tsx)

#### Current Issue: Auto-load on Every Selection

```typescript
// Lines 49-53: useEffect triggers on every selection change
useEffect(() => {
    if (selectedAdapter) {
        loadIPConfig(selectedAdapter);  // No debouncing!
    }
}, [selectedAdapter]);
```

**Problems:**
- No debouncing: rapid clicks = multiple queued requests
- No caching: switching back to same adapter = full reload
- Loading state blocks entire card (not skeleton)

### 2.3 Python Legacy Comparison (`network_tab.py`)

**File:** [`ui/network_tab.py`](../ui/network_tab.py)

The Python version has similar issues but shows the expected behavior:

```python
# Lines 386-482: load_current_adapter_ip()
# Same 4 sequential PowerShell calls
# BUT: Uses QApplication.processEvents() for UI responsiveness
```

**Key Insight:** Python version also suffers from the same bottlenecks, confirming this is an architectural issue, not platform-specific.

---

## 3. Implementation Code Examples

### 3.A Rust Cache Module (`cache.rs`)

**New file:** `am_net_tools/src-tauri/src/cache.rs`

```rust
//! Cache module for network configuration data
//! Provides thread-safe, TTL-based caching for expensive PowerShell operations

use std::collections::HashMap;
use std::sync::Mutex;
use std::time::{Duration, Instant};
use serde::{Deserialize, Serialize};
use lazy_static::lazy_static;

/// Default cache TTL: 30 seconds
/// Network config rarely changes, safe to cache for short period
const DEFAULT_TTL_SECS: u64 = 30;

/// Cache entry with timestamp for TTL validation
#[derive(Debug, Clone)]
pub struct CacheEntry<T: Clone> {
    /// Cached data
    pub data: T,
    /// When this entry was created
    pub created_at: Instant,
    /// Time-to-live duration
    pub ttl: Duration,
}

impl<T: Clone> CacheEntry<T> {
    /// Create a new cache entry with default TTL
    pub fn new(data: T) -> Self {
        Self {
            data,
            created_at: Instant::now(),
            ttl: Duration::from_secs(DEFAULT_TTL_SECS),
        }
    }

    /// Create a new cache entry with custom TTL
    pub fn with_ttl(data: T, ttl_secs: u64) -> Self {
        Self {
            data,
            created_at: Instant::now(),
            ttl: Duration::from_secs(ttl_secs),
        }
    }

    /// Check if this entry has expired
    pub fn is_expired(&self) -> bool {
        self.created_at.elapsed() > self.ttl
    }

    /// Get remaining TTL in seconds (0 if expired)
    pub fn remaining_ttl_secs(&self) -> u64 {
        let elapsed = self.created_at.elapsed();
        if elapsed > self.ttl {
            0
        } else {
            (self.ttl - elapsed).as_secs()
        }
    }
}

/// Unified IP configuration data (matches all 4 PS queries)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CachedIPConfig {
    pub ip_address: String,
    pub prefix_length: u8,
    pub subnet_mask: String,
    pub gateway: String,
    pub primary_dns: String,
    pub secondary_dns: String,
    pub dhcp_enabled: bool,
}

/// Thread-safe network configuration cache
/// Uses Mutex for interior mutability in lazy_static context
pub struct NetworkCache {
    /// Map of adapter_name -> cached config
    configs: Mutex<HashMap<String, CacheEntry<CachedIPConfig>>>,
    /// Map of adapter_name -> cached adapters list
    adapters: Mutex<Option<CacheEntry<Vec<super::network::NetworkAdapter>>>>,
}

impl NetworkCache {
    /// Create a new empty cache
    pub fn new() -> Self {
        Self {
            configs: Mutex::new(HashMap::new()),
            adapters: Mutex::new(None),
        }
    }

    /// Get cached IP configuration for an adapter
    /// Returns None if not cached or expired
    pub fn get_config(&self, adapter_name: &str) -> Option<CachedIPConfig> {
        let cache = self.configs.lock().ok()?;
        let entry = cache.get(adapter_name)?;
        
        if entry.is_expired() {
            // Don't return expired data, but don't remove yet
            // (allows stale-while-revalidate pattern)
            None
        } else {
            Some(entry.data.clone())
        }
    }

    /// Get cached config even if expired (for stale fallback)
    pub fn get_config_stale(&self, adapter_name: &str) -> Option<(CachedIPConfig, bool)> {
        let cache = self.configs.lock().ok()?;
        let entry = cache.get(adapter_name)?;
        Some((entry.data.clone(), entry.is_expired()))
    }

    /// Store IP configuration in cache
    pub fn set_config(&self, adapter_name: &str, config: CachedIPConfig) {
        if let Ok(mut cache) = self.configs.lock() {
            cache.insert(adapter_name.to_string(), CacheEntry::new(config));
        }
    }

    /// Store IP configuration with custom TTL
    pub fn set_config_with_ttl(&self, adapter_name: &str, config: CachedIPConfig, ttl_secs: u64) {
        if let Ok(mut cache) = self.configs.lock() {
            cache.insert(
                adapter_name.to_string(),
                CacheEntry::with_ttl(config, ttl_secs),
            );
        }
    }

    /// Invalidate cache for specific adapter
    pub fn invalidate_config(&self, adapter_name: &str) {
        if let Ok(mut cache) = self.configs.lock() {
            cache.remove(adapter_name);
        }
    }

    /// Invalidate all cached configurations
    pub fn invalidate_all_configs(&self) {
        if let Ok(mut cache) = self.configs.lock() {
            cache.clear();
        }
    }

    /// Get cached adapter list
    pub fn get_adapters(&self) -> Option<Vec<super::network::NetworkAdapter>> {
        let cache = self.adapters.lock().ok()?;
        let entry = cache.as_ref()?;
        
        if entry.is_expired() {
            None
        } else {
            Some(entry.data.clone())
        }
    }

    /// Store adapter list in cache
    pub fn set_adapters(&self, adapters: Vec<super::network::NetworkAdapter>) {
        if let Ok(mut cache) = self.adapters.lock() {
            *cache = Some(CacheEntry::new(adapters));
        }
    }

    /// Get cache statistics for debugging
    pub fn stats(&self) -> CacheStats {
        let config_count = self.configs.lock().map(|c| c.len()).unwrap_or(0);
        let has_adapters = self.adapters.lock().map(|a| a.is_some()).unwrap_or(false);
        
        CacheStats {
            cached_configs: config_count,
            has_adapter_list: has_adapters,
        }
    }
}

/// Cache statistics for monitoring
#[derive(Debug, Serialize)]
pub struct CacheStats {
    pub cached_configs: usize,
    pub has_adapter_list: bool,
}

// Global singleton cache instance
lazy_static! {
    /// Global network cache accessible from all Tauri commands
    pub static ref NETWORK_CACHE: NetworkCache = NetworkCache::new();
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cache_entry_expiration() {
        let entry = CacheEntry::with_ttl("test", 1);
        assert!(!entry.is_expired());
        
        std::thread::sleep(Duration::from_millis(1100));
        assert!(entry.is_expired());
    }

    #[test]
    fn test_cache_set_get() {
        let cache = NetworkCache::new();
        let config = CachedIPConfig {
            ip_address: "192.168.1.1".to_string(),
            prefix_length: 24,
            subnet_mask: "255.255.255.0".to_string(),
            gateway: "192.168.1.254".to_string(),
            primary_dns: "8.8.8.8".to_string(),
            secondary_dns: "8.8.4.4".to_string(),
            dhcp_enabled: false,
        };

        cache.set_config("eth0", config.clone());
        
        let retrieved = cache.get_config("eth0");
        assert!(retrieved.is_some());
        assert_eq!(retrieved.unwrap().ip_address, "192.168.1.1");
    }
}
```

### 3.B Unified PowerShell Query (`network_unified.rs`)

**New file:** `am_net_tools/src-tauri/src/network_unified.rs`

```rust
//! Unified network configuration query
//! Combines all 4 PowerShell queries into a single script for efficiency

use serde::{Deserialize, Serialize};
use std::os::windows::process::CommandExt;
use std::process::Command;

use crate::cache::{CachedIPConfig, NETWORK_CACHE};
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

/// Get IP configuration using unified query with caching
/// 
/// # Flow:
/// 1. Check cache for valid entry
/// 2. If cache hit, return immediately
/// 3. If cache miss, run unified PS script
/// 4. Parse response and update cache
/// 5. Return configuration
#[tauri::command]
pub async fn get_ip_configuration_cached(adapter_name: String) -> Result<IPConfiguration, String> {
    // Step 1: Check cache first (fast path)
    if let Some(cached) = NETWORK_CACHE.get_config(&adapter_name) {
        log::debug!("Cache hit for adapter: {}", adapter_name);
        return Ok(IPConfiguration {
            ip_address: cached.ip_address,
            subnet_mask: cached.subnet_mask,
            gateway: cached.gateway,
            primary_dns: cached.primary_dns,
            secondary_dns: cached.secondary_dns,
            dhcp_enabled: cached.dhcp_enabled,
        });
    }

    log::debug!("Cache miss for adapter: {}, fetching...", adapter_name);

    // Step 2: Run unified PowerShell script
    let output = tokio::task::spawn_blocking(move || {
        Command::new("powershell")
            .creation_flags(CREATE_NO_WINDOW)
            .args([
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy", "Bypass",
                "-Command",
                &format!(
                    r#"& {{ {} }} -AdapterName '{}'"#,
                    UNIFIED_PS_SCRIPT,
                    adapter_name.replace("'", "''") // Escape single quotes
                ),
            ])
            .output()
    })
    .await
    .map_err(|e| format!("Task join error: {}", e))?
    .map_err(|e| format!("Failed to execute PowerShell: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("PowerShell error: {}", stderr));
    }

    // Step 3: Parse JSON response
    let stdout = String::from_utf8_lossy(&output.stdout);
    let response: UnifiedPSResponse = serde_json::from_str(stdout.trim())
        .map_err(|e| format!("Failed to parse response: {} (raw: {})", e, stdout))?;

    // Check for PowerShell-level errors
    if let Some(error) = response.error {
        return Err(format!("PowerShell script error: {}", error));
    }

    // Step 4: Convert and cache the result
    let subnet_mask = prefix_to_subnet(response.prefix_length);
    
    let cached_config = CachedIPConfig {
        ip_address: response.ip_address.clone(),
        prefix_length: response.prefix_length,
        subnet_mask: subnet_mask.clone(),
        gateway: response.gateway.clone(),
        primary_dns: response.primary_dns.clone(),
        secondary_dns: response.secondary_dns.clone(),
        dhcp_enabled: response.dhcp_enabled,
    };

    // Store in cache with adapter name from outer scope (we moved it earlier)
    // Need to capture adapter_name before the blocking task
    // Note: adapter_name is moved into the closure, so we need to clone it first
    // This is handled in the actual implementation by cloning before the spawn_blocking
    
    let config = IPConfiguration {
        ip_address: cached_config.ip_address.clone(),
        subnet_mask: cached_config.subnet_mask.clone(),
        gateway: cached_config.gateway.clone(),
        primary_dns: cached_config.primary_dns.clone(),
        secondary_dns: cached_config.secondary_dns.clone(),
        dhcp_enabled: cached_config.dhcp_enabled,
    };

    Ok(config)
}

/// Invalidate cache for adapter (call after applying changes)
#[tauri::command]
pub fn invalidate_adapter_cache(adapter_name: String) {
    NETWORK_CACHE.invalidate_config(&adapter_name);
    log::info!("Cache invalidated for adapter: {}", adapter_name);
}

/// Invalidate all cached network configurations
#[tauri::command]
pub fn invalidate_all_network_cache() {
    NETWORK_CACHE.invalidate_all_configs();
    log::info!("All network cache invalidated");
}

/// Get cache statistics (for debugging/monitoring)
#[tauri::command]
pub fn get_cache_stats() -> crate::cache::CacheStats {
    NETWORK_CACHE.stats()
}

// ============================================================================
// Corrected version with proper adapter_name handling
// ============================================================================

/// Optimized version that properly handles adapter_name lifetime
#[tauri::command]
pub async fn get_ip_configuration_optimized(adapter_name: String) -> Result<IPConfiguration, String> {
    // Step 1: Check cache first
    if let Some(cached) = NETWORK_CACHE.get_config(&adapter_name) {
        return Ok(IPConfiguration {
            ip_address: cached.ip_address,
            subnet_mask: cached.subnet_mask,
            gateway: cached.gateway,
            primary_dns: cached.primary_dns,
            secondary_dns: cached.secondary_dns,
            dhcp_enabled: cached.dhcp_enabled,
        });
    }

    // Clone adapter_name for use after spawn_blocking
    let adapter_name_for_cache = adapter_name.clone();

    // Step 2: Run unified PowerShell script
    let output = tokio::task::spawn_blocking(move || {
        Command::new("powershell")
            .creation_flags(CREATE_NO_WINDOW)
            .args([
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy", "Bypass",
                "-Command",
                &format!(
                    r#"& {{ {} }} -AdapterName '{}'"#,
                    UNIFIED_PS_SCRIPT,
                    adapter_name.replace("'", "''")
                ),
            ])
            .output()
    })
    .await
    .map_err(|e| format!("Task join error: {}", e))?
    .map_err(|e| format!("Failed to execute PowerShell: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("PowerShell error: {}", stderr));
    }

    // Step 3: Parse response
    let stdout = String::from_utf8_lossy(&output.stdout);
    let response: UnifiedPSResponse = serde_json::from_str(stdout.trim())
        .map_err(|e| format!("Parse error: {}", e))?;

    if let Some(error) = response.error {
        return Err(error);
    }

    // Step 4: Build result
    let subnet_mask = prefix_to_subnet(response.prefix_length);

    let cached_config = CachedIPConfig {
        ip_address: response.ip_address,
        prefix_length: response.prefix_length,
        subnet_mask: subnet_mask.clone(),
        gateway: response.gateway,
        primary_dns: response.primary_dns,
        secondary_dns: response.secondary_dns,
        dhcp_enabled: response.dhcp_enabled,
    };

    // Step 5: Update cache
    NETWORK_CACHE.set_config(&adapter_name_for_cache, cached_config.clone());

    Ok(IPConfiguration {
        ip_address: cached_config.ip_address,
        subnet_mask: cached_config.subnet_mask,
        gateway: cached_config.gateway,
        primary_dns: cached_config.primary_dns,
        secondary_dns: cached_config.secondary_dns,
        dhcp_enabled: cached_config.dhcp_enabled,
    })
}
```

### 3.C React Custom Hook (`useNetworkData.ts`)

**New file:** `am_net_tools/src/hooks/useNetworkData.ts`

```typescript
/**
 * Custom hook for fetching network adapter configuration with optimizations:
 * - Debouncing (prevents rapid consecutive calls)
 * - Abort controller (cancels in-flight requests when adapter changes)
 * - Loading states (for skeleton UI integration)
 * - Error handling with retry capability
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { type IPConfiguration } from '../lib/tauri';

// Debounce delay in milliseconds
const DEBOUNCE_MS = 150;

interface UseNetworkDataState {
    /** Current IP configuration data */
    data: IPConfiguration | null;
    /** Whether data is currently loading */
    loading: boolean;
    /** Error message if fetch failed */
    error: string | null;
    /** Whether we're showing stale (cached) data */
    isStale: boolean;
    /** Timestamp of last successful fetch */
    lastUpdated: Date | null;
}

interface UseNetworkDataReturn extends UseNetworkDataState {
    /** Manually trigger a refetch */
    refetch: () => void;
    /** Clear current data and error state */
    reset: () => void;
}

/**
 * Hook for fetching network configuration with debouncing and caching
 * 
 * @param adapterName - Name of the network adapter to fetch config for
 * @returns State object with data, loading, error, and utility functions
 * 
 * @example
 * ```tsx
 * const { data, loading, error, refetch } = useNetworkData(selectedAdapter);
 * 
 * if (loading) return <NetworkConfigSkeleton />;
 * if (error) return <ErrorDisplay message={error} onRetry={refetch} />;
 * if (!data) return null;
 * 
 * return <IPConfigForm initialData={data} />;
 * ```
 */
export function useNetworkData(adapterName: string | null): UseNetworkDataReturn {
    const [state, setState] = useState<UseNetworkDataState>({
        data: null,
        loading: false,
        error: null,
        isStale: false,
        lastUpdated: null,
    });

    // Refs for managing async operations
    const abortControllerRef = useRef<AbortController | null>(null);
    const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    const isMountedRef = useRef(true);

    // Track the current adapter to detect changes
    const currentAdapterRef = useRef<string | null>(null);

    /**
     * Internal fetch function (no debouncing)
     */
    const fetchData = useCallback(async (adapter: string) => {
        // Cancel any existing request
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }

        // Create new abort controller
        abortControllerRef.current = new AbortController();

        setState(prev => ({
            ...prev,
            loading: true,
            error: null,
        }));

        try {
            // Use the optimized cached version
            const config = await invoke<IPConfiguration>('get_ip_configuration_optimized', {
                adapterName: adapter,
            });

            // Check if component is still mounted and this is still the current request
            if (!isMountedRef.current || currentAdapterRef.current !== adapter) {
                return;
            }

            setState({
                data: config,
                loading: false,
                error: null,
                isStale: false,
                lastUpdated: new Date(),
            });
        } catch (error) {
            // Ignore abort errors
            if (error instanceof Error && error.name === 'AbortError') {
                return;
            }

            if (!isMountedRef.current || currentAdapterRef.current !== adapter) {
                return;
            }

            setState(prev => ({
                ...prev,
                loading: false,
                error: error instanceof Error ? error.message : String(error),
            }));
        }
    }, []);

    /**
     * Debounced fetch function
     */
    const debouncedFetch = useCallback((adapter: string) => {
        // Clear any existing debounce timeout
        if (debounceTimeoutRef.current) {
            clearTimeout(debounceTimeoutRef.current);
        }

        // Set loading state immediately for better UX
        setState(prev => ({
            ...prev,
            loading: true,
        }));

        // Schedule the actual fetch
        debounceTimeoutRef.current = setTimeout(() => {
            fetchData(adapter);
        }, DEBOUNCE_MS);
    }, [fetchData]);

    /**
     * Effect: Fetch data when adapter changes
     */
    useEffect(() => {
        currentAdapterRef.current = adapterName;

        if (!adapterName) {
            // Reset state when no adapter selected
            setState({
                data: null,
                loading: false,
                error: null,
                isStale: false,
                lastUpdated: null,
            });
            return;
        }

        debouncedFetch(adapterName);

        // Cleanup function
        return () => {
            if (debounceTimeoutRef.current) {
                clearTimeout(debounceTimeoutRef.current);
            }
            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
            }
        };
    }, [adapterName, debouncedFetch]);

    /**
     * Effect: Track component mount state
     */
    useEffect(() => {
        isMountedRef.current = true;
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    /**
     * Manual refetch function
     */
    const refetch = useCallback(() => {
        if (adapterName) {
            fetchData(adapterName);
        }
    }, [adapterName, fetchData]);

    /**
     * Reset function to clear state
     */
    const reset = useCallback(() => {
        setState({
            data: null,
            loading: false,
            error: null,
            isStale: false,
            lastUpdated: null,
        });
    }, []);

    return {
        ...state,
        refetch,
        reset,
    };
}

/**
 * Hook for fetching network adapters list
 * Simpler than useNetworkData since adapter list changes rarely
 */
export function useNetworkAdapters() {
    const [adapters, setAdapters] = useState<Array<{
        name: string;
        description: string;
        status: string;
        mac_address: string;
    }>>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchAdapters = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            const data = await invoke<typeof adapters>('get_network_adapters');
            setAdapters(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : String(err));
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchAdapters();
    }, [fetchAdapters]);

    return {
        adapters,
        loading,
        error,
        refetch: fetchAdapters,
    };
}
```

### 3.D Network Cache Hook (`useNetworkCache.ts`)

**New file:** `am_net_tools/src/hooks/useNetworkCache.ts`

```typescript
/**
 * Client-side network configuration cache hook
 * Provides React-side caching for IP configurations
 * 
 * Features:
 * - Map-based storage (adapter name -> config)
 * - TTL validation with stale data fallback
 * - Automatic cleanup of expired entries
 * - Singleton pattern via module scope
 */

import { useCallback, useMemo, useRef, useSyncExternalStore } from 'react';
import { type IPConfiguration } from '../lib/tauri';

// Cache TTL in milliseconds (30 seconds, matches Rust cache)
const CACHE_TTL_MS = 30 * 1000;

// Cache cleanup interval (run every 60 seconds)
const CLEANUP_INTERVAL_MS = 60 * 1000;

interface CacheEntry {
    data: IPConfiguration;
    timestamp: number;
    expiresAt: number;
}

/**
 * Singleton cache store (module-scoped)
 * Uses a simple observer pattern for React integration
 */
class NetworkCacheStore {
    private cache = new Map<string, CacheEntry>();
    private listeners = new Set<() => void>();
    private cleanupInterval: NodeJS.Timeout | null = null;

    constructor() {
        // Start cleanup interval
        this.startCleanup();
    }

    /**
     * Start periodic cleanup of expired entries
     */
    private startCleanup(): void {
        if (typeof window === 'undefined') return;
        
        this.cleanupInterval = setInterval(() => {
            this.removeExpired();
        }, CLEANUP_INTERVAL_MS);
    }

    /**
     * Remove all expired entries from cache
     */
    private removeExpired(): void {
        const now = Date.now();
        let hasChanges = false;

        for (const [key, entry] of this.cache.entries()) {
            if (now > entry.expiresAt) {
                this.cache.delete(key);
                hasChanges = true;
            }
        }

        if (hasChanges) {
            this.notifyListeners();
        }
    }

    /**
     * Notify all subscribed listeners of cache changes
     */
    private notifyListeners(): void {
        this.listeners.forEach(listener => listener());
    }

    /**
     * Get cache entry for adapter (returns null if not found or expired)
     */
    get(adapterName: string): IPConfiguration | null {
        const entry = this.cache.get(adapterName);
        
        if (!entry) return null;
        
        const now = Date.now();
        if (now > entry.expiresAt) {
            // Entry expired, but don't delete yet (stale-while-revalidate)
            return null;
        }

        return entry.data;
    }

    /**
     * Get stale cache entry (for fallback display)
     * Returns [data, isStale] tuple
     */
    getWithStaleStatus(adapterName: string): [IPConfiguration | null, boolean] {
        const entry = this.cache.get(adapterName);
        
        if (!entry) return [null, false];
        
        const now = Date.now();
        const isStale = now > entry.expiresAt;

        return [entry.data, isStale];
    }

    /**
     * Store configuration in cache
     */
    set(adapterName: string, data: IPConfiguration, ttlMs: number = CACHE_TTL_MS): void {
        const now = Date.now();
        
        this.cache.set(adapterName, {
            data,
            timestamp: now,
            expiresAt: now + ttlMs,
        });

        this.notifyListeners();
    }

    /**
     * Invalidate (remove) cache entry for adapter
     */
    invalidate(adapterName: string): void {
        if (this.cache.has(adapterName)) {
            this.cache.delete(adapterName);
            this.notifyListeners();
        }
    }

    /**
     * Clear all cache entries
     */
    clear(): void {
        this.cache.clear();
        this.notifyListeners();
    }

    /**
     * Get cache size (number of entries)
     */
    get size(): number {
        return this.cache.size;
    }

    /**
     * Get all cached adapter names
     */
    get keys(): string[] {
        return Array.from(this.cache.keys());
    }

    /**
     * Subscribe to cache changes (for React integration)
     */
    subscribe(listener: () => void): () => void {
        this.listeners.add(listener);
        return () => this.listeners.delete(listener);
    }

    /**
     * Get snapshot for useSyncExternalStore
     */
    getSnapshot(): Map<string, CacheEntry> {
        return this.cache;
    }

    /**
     * Cleanup on unmount
     */
    destroy(): void {
        if (this.cleanupInterval) {
            clearInterval(this.cleanupInterval);
        }
        this.cache.clear();
        this.listeners.clear();
    }
}

// Singleton instance
const cacheStore = new NetworkCacheStore();

/**
 * Hook for accessing the network configuration cache
 * 
 * @example
 * ```tsx
 * const cache = useNetworkCache();
 * 
 * // Check cache before fetching
 * const cached = cache.get(adapterName);
 * if (cached) {
 *   setFormData(cached);
 *   return;
 * }
 * 
 * // After fetching, update cache
 * const data = await fetchConfig(adapterName);
 * cache.set(adapterName, data);
 * ```
 */
export function useNetworkCache() {
    // Use useSyncExternalStore for proper React 18 concurrent mode support
    const cacheSnapshot = useSyncExternalStore(
        useCallback((callback) => cacheStore.subscribe(callback), []),
        useCallback(() => cacheStore.getSnapshot(), []),
        useCallback(() => cacheStore.getSnapshot(), [])
    );

    // Memoized cache operations
    const operations = useMemo(() => ({
        /**
         * Get cached config (null if not found or expired)
         */
        get: (adapterName: string): IPConfiguration | null => {
            return cacheStore.get(adapterName);
        },

        /**
         * Get cached config with stale status
         */
        getWithStaleStatus: (adapterName: string): [IPConfiguration | null, boolean] => {
            return cacheStore.getWithStaleStatus(adapterName);
        },

        /**
         * Store config in cache
         */
        set: (adapterName: string, data: IPConfiguration): void => {
            cacheStore.set(adapterName, data);
        },

        /**
         * Store config with custom TTL
         */
        setWithTTL: (adapterName: string, data: IPConfiguration, ttlMs: number): void => {
            cacheStore.set(adapterName, data, ttlMs);
        },

        /**
         * Invalidate cache for adapter
         */
        invalidate: (adapterName: string): void => {
            cacheStore.invalidate(adapterName);
        },

        /**
         * Clear entire cache
         */
        clear: (): void => {
            cacheStore.clear();
        },

        /**
         * Get cache size
         */
        size: cacheStore.size,

        /**
         * Get cached adapter names
         */
        keys: cacheStore.keys,
    }), [cacheSnapshot]);

    return operations;
}

/**
 * Hook for getting a specific adapter's cached config with reactivity
 * Re-renders when that specific entry changes
 */
export function useCachedConfig(adapterName: string | null) {
    const cache = useNetworkCache();
    const previousDataRef = useRef<IPConfiguration | null>(null);

    const data = useMemo(() => {
        if (!adapterName) return null;
        return cache.get(adapterName);
    }, [adapterName, cache]);

    // Track if data changed
    const hasChanged = data !== previousDataRef.current;
    previousDataRef.current = data;

    return {
        data,
        isStale: adapterName ? cache.getWithStaleStatus(adapterName)[1] : false,
        hasChanged,
    };
}
```

### 3.E Skeleton Component (`NetworkConfigSkeleton.tsx`)

**New file:** `am_net_tools/src/components/NetworkConfigSkeleton.tsx`

```typescript
/**
 * Skeleton loading component for Network Configuration form
 * Matches the exact layout of the IP Configuration card for seamless loading states
 */

import { motion } from 'framer-motion';

/**
 * Base skeleton block with shimmer animation
 */
function SkeletonBlock({
    width = '100%',
    height = 20,
    className = '',
    rounded = 'md',
}: {
    width?: string | number;
    height?: string | number;
    className?: string;
    rounded?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
}) {
    const roundedClasses = {
        sm: 'rounded-sm',
        md: 'rounded-md',
        lg: 'rounded-lg',
        xl: 'rounded-xl',
        full: 'rounded-full',
    };

    return (
        <div
            className={`bg-white/10 animate-pulse ${roundedClasses[rounded]} ${className}`}
            style={{
                width: typeof width === 'number' ? `${width}px` : width,
                height: typeof height === 'number' ? `${height}px` : height,
            }}
        />
    );
}

/**
 * Skeleton for a form input field (label + input)
 */
function InputSkeleton({ labelWidth = 100 }: { labelWidth?: number }) {
    return (
        <div className="space-y-1">
            <SkeletonBlock width={labelWidth} height={14} />
            <SkeletonBlock height={44} rounded="xl" />
        </div>
    );
}

/**
 * Main Network Configuration Skeleton
 * Matches the IP Configuration card layout exactly
 */
export function NetworkConfigSkeleton() {
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="space-y-6"
        >
            {/* DHCP / Static Toggle Skeleton */}
            <div className="flex gap-4 mb-6">
                <div className="flex items-center gap-2">
                    <SkeletonBlock width={16} height={16} rounded="full" />
                    <SkeletonBlock width={130} height={16} />
                </div>
                <div className="flex items-center gap-2">
                    <SkeletonBlock width={16} height={16} rounded="full" />
                    <SkeletonBlock width={120} height={16} />
                </div>
            </div>

            {/* Form Fields Skeleton */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* IP Address */}
                <InputSkeleton labelWidth={80} />
                
                {/* Subnet Mask */}
                <InputSkeleton labelWidth={90} />
                
                {/* Default Gateway */}
                <InputSkeleton labelWidth={110} />
                
                {/* Primary DNS */}
                <InputSkeleton labelWidth={85} />
                
                {/* Secondary DNS */}
                <InputSkeleton labelWidth={100} />
            </div>

            {/* Apply Button Skeleton */}
            <div className="mt-6">
                <SkeletonBlock width={180} height={44} rounded="xl" />
            </div>
        </motion.div>
    );
}

/**
 * Inline skeleton for adapter dropdown loading
 */
export function AdapterSelectSkeleton() {
    return (
        <div className="flex gap-2">
            <SkeletonBlock height={48} className="flex-1" rounded="xl" />
            <SkeletonBlock width={48} height={48} rounded="xl" />
        </div>
    );
}

/**
 * Full page skeleton for initial load
 */
export function NetworkPageSkeleton() {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-6 space-y-6"
        >
            {/* Header Skeleton */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <SkeletonBlock width={32} height={32} rounded="lg" />
                    <SkeletonBlock width={180} height={28} />
                </div>
                <div className="flex gap-2">
                    <SkeletonBlock width={100} height={40} rounded="xl" />
                    <SkeletonBlock width={90} height={40} rounded="xl" />
                </div>
            </div>

            {/* Adapter Selection Skeleton */}
            <div className="glass-card">
                <div className="flex flex-col gap-2">
                    <SkeletonBlock width={130} height={18} />
                    <AdapterSelectSkeleton />
                </div>
            </div>

            {/* IP Configuration Skeleton */}
            <div className="glass-card">
                <SkeletonBlock width={140} height={20} className="mb-4" />
                <NetworkConfigSkeleton />
            </div>

            {/* Quick Commands Skeleton */}
            <div className="glass-card">
                <SkeletonBlock width={110} height={20} className="mb-4" />
                <div className="flex flex-wrap gap-3">
                    {[100, 120, 95, 90, 100, 115].map((width, i) => (
                        <SkeletonBlock key={i} width={width} height={40} rounded="xl" />
                    ))}
                </div>
            </div>
        </motion.div>
    );
}

/**
 * Overlay skeleton for config loading (shows on top of existing content)
 * Used when switching adapters to show loading without removing current data
 */
export function ConfigLoadingOverlay() {
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.1 }}
            className="absolute inset-0 bg-black/40 backdrop-blur-[1px] flex items-center justify-center z-10 rounded-xl"
        >
            <div className="flex flex-col items-center gap-3">
                {/* Animated spinner */}
                <div className="w-8 h-8 border-2 border-white/20 border-t-primary rounded-full animate-spin" />
                <span className="text-sm text-gray-300">Loading configuration...</span>
            </div>
        </motion.div>
    );
}
```

### 3.F Updated NetworkTab.tsx (Key Changes)

**Modifications to:** `am_net_tools/src/components/NetworkTab.tsx`

```typescript
/**
 * Updated NetworkTab with performance optimizations:
 * 1. Uses useNetworkData hook with debouncing
 * 2. Integrates skeleton loading UI
 * 3. Invalidates cache after applying changes
 * 
 * Key changes from original are marked with: // CHANGE:
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Globe, RefreshCw, Loader2, ExternalLink, Terminal,
    Wifi, WifiOff, ArrowDownUp, Trash2
} from 'lucide-react';
import toast from 'react-hot-toast';
import { Card } from './UI/Card';
import { Button } from './UI/Button';
// CHANGE: Import optimized hooks
import { useNetworkData, useNetworkAdapters } from '../hooks/useNetworkData';
import { useNetworkCache } from '../hooks/useNetworkCache';
// CHANGE: Import skeleton components
import { NetworkConfigSkeleton, ConfigLoadingOverlay } from './NetworkConfigSkeleton';
import {
    applyDHCP,
    applyStaticIP,
    runIpconfig,
    releaseIP,
    renewIP,
    flushDNS,
    displayDNS,
    openNetworkConnections,
    openNetworkSettings,
} from '../lib/tauri';
import { invoke } from '@tauri-apps/api/core';

export function NetworkTab() {
    // CHANGE: Use optimized adapter hook
    const { adapters, loading: adaptersLoading, refetch: refetchAdapters } = useNetworkAdapters();
    
    const [selectedAdapter, setSelectedAdapter] = useState<string>('');
    const [output, setOutput] = useState('');
    const [isDHCP, setIsDHCP] = useState(true);
    const [saving, setSaving] = useState(false);

    // CHANGE: Use optimized data hook with debouncing
    const { 
        data: ipConfig, 
        loading: configLoading, 
        error: configError,
        refetch: refetchConfig 
    } = useNetworkData(selectedAdapter || null);

    // CHANGE: Get cache operations for invalidation
    const cache = useNetworkCache();

    // Form state for static IP
    const [formData, setFormData] = useState({
        ip_address: '',
        subnet_mask: '255.255.255.0',
        gateway: '',
        primary_dns: '8.8.8.8',
        secondary_dns: '8.8.4.4',
    });

    // CHANGE: Set initial adapter only once when list loads
    useEffect(() => {
        if (adapters.length > 0 && !selectedAdapter) {
            setSelectedAdapter(adapters[0].name);
        }
    }, [adapters, selectedAdapter]);

    // CHANGE: Update form when config loads (with null check)
    useEffect(() => {
        if (ipConfig) {
            setIsDHCP(ipConfig.dhcp_enabled);
            setFormData({
                ip_address: ipConfig.ip_address || '',
                subnet_mask: ipConfig.subnet_mask || '255.255.255.0',
                gateway: ipConfig.gateway || '',
                primary_dns: ipConfig.primary_dns || '8.8.8.8',
                secondary_dns: ipConfig.secondary_dns || '8.8.4.4',
            });
        }
    }, [ipConfig]);

    // CHANGE: Show error toast when config fails
    useEffect(() => {
        if (configError) {
            toast.error(`Failed to load config: ${configError}`);
        }
    }, [configError]);

    const handleApplyConfig = async () => {
        if (!selectedAdapter) {
            toast.error('Please select a network adapter');
            return;
        }

        try {
            setSaving(true);
            
            if (isDHCP) {
                const msg = await applyDHCP(selectedAdapter);
                toast.success(msg);
            } else {
                if (!formData.ip_address) {
                    toast.error('IP Address is required');
                    return;
                }
                const msg = await applyStaticIP(
                    selectedAdapter,
                    formData.ip_address,
                    formData.subnet_mask,
                    formData.gateway,
                    formData.primary_dns,
                    formData.secondary_dns
                );
                toast.success(msg);
            }

            // CHANGE: Invalidate both caches after applying changes
            cache.invalidate(selectedAdapter);
            await invoke('invalidate_adapter_cache', { adapterName: selectedAdapter });
            
            // CHANGE: Refetch to get new config
            refetchConfig();
            
        } catch (error) {
            toast.error(`${error}`);
        } finally {
            setSaving(false);
        }
    };

    const runCommand = async (cmd: 'ipconfig' | 'ipconfig_all' | 'release' | 'renew' | 'flush' | 'dns') => {
        try {
            let result = '';
            switch (cmd) {
                case 'ipconfig':
                    result = await runIpconfig(false);
                    break;
                case 'ipconfig_all':
                    result = await runIpconfig(true);
                    break;
                case 'release':
                    result = await releaseIP();
                    toast.success('IP Released');
                    // CHANGE: Invalidate cache after IP release
                    cache.clear();
                    break;
                case 'renew':
                    result = await renewIP();
                    toast.success('IP Renewed');
                    // CHANGE: Invalidate cache after IP renew
                    cache.clear();
                    refetchConfig();
                    break;
                case 'flush':
                    result = await flushDNS();
                    toast.success('DNS Cache Flushed');
                    break;
                case 'dns':
                    result = await displayDNS();
                    break;
            }
            setOutput(result);
        } catch (error) {
            toast.error(`${error}`);
        }
    };

    // CHANGE: Use skeleton for initial page load
    if (adaptersLoading) {
        return (
            <div className="flex items-center justify-center h-full">
                <Loader2 className="w-8 h-8 text-primary animate-spin" />
                <span className="ml-3 text-gray-400">Loading network adapters...</span>
            </div>
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-6 space-y-6 overflow-y-auto"
        >
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <Globe className="w-8 h-8 text-primary" />
                    <h2 className="text-2xl font-bold text-white">Network Settings</h2>
                </div>
                <div className="flex gap-2">
                    <Button variant="secondary" onClick={() => openNetworkConnections()}>
                        <ExternalLink className="w-4 h-4" />
                        ncpa.cpl
                    </Button>
                    <Button variant="secondary" onClick={() => openNetworkSettings()}>
                        <ExternalLink className="w-4 h-4" />
                        Settings
                    </Button>
                </div>
            </div>

            {/* Adapter Selection */}
            <Card>
                <div className="flex flex-col gap-2">
                    <label className="text-white font-semibold">
                        Network Adapter:
                    </label>
                    <div className="flex gap-2">
                        <select
                            value={selectedAdapter}
                            onChange={(e) => setSelectedAdapter(e.target.value)}
                            className="flex-1 px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-primary truncate pr-8"
                            style={{ textOverflow: 'ellipsis' }}
                        >
                            {adapters.map((adapter) => (
                                <option key={adapter.name} value={adapter.name} className="bg-slate-800">
                                    {adapter.status === 'Up' ? '🟢' : '🔴'} {adapter.name} - {adapter.description}
                                </option>
                            ))}
                        </select>
                        <Button variant="secondary" onClick={refetchAdapters}>
                            <RefreshCw className="w-4 h-4" />
                        </Button>
                    </div>
                </div>
            </Card>

            {/* IP Configuration */}
            <Card title="IP Configuration" className="relative overflow-hidden">
                {/* CHANGE: Use AnimatePresence for smooth skeleton transitions */}
                <AnimatePresence mode="wait">
                    {configLoading ? (
                        <ConfigLoadingOverlay key="loading" />
                    ) : null}
                </AnimatePresence>

                {/* CHANGE: Show skeleton only on initial load, not refreshes */}
                {!ipConfig && configLoading ? (
                    <NetworkConfigSkeleton />
                ) : (
                    <>
                        {/* DHCP / Static Toggle */}
                        <div className="flex gap-4 mb-6">
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                    type="radio"
                                    checked={isDHCP}
                                    onChange={() => setIsDHCP(true)}
                                    className="w-4 h-4 text-primary"
                                />
                                <span className="text-white">DHCP (Automatic)</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                    type="radio"
                                    checked={!isDHCP}
                                    onChange={() => setIsDHCP(false)}
                                    className="w-4 h-4 text-primary"
                                />
                                <span className="text-white">Static IP (Manual)</span>
                            </label>
                        </div>

                        {/* Static IP Form */}
                        <div className={`space-y-4 ${isDHCP ? 'opacity-50 pointer-events-none' : ''}`}>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm text-gray-400 mb-1">IP Address</label>
                                    <input
                                        type="text"
                                        value={formData.ip_address}
                                        onChange={(e) => setFormData({ ...formData, ip_address: e.target.value })}
                                        placeholder="192.168.1.100"
                                        className="input-field w-full"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-400 mb-1">Subnet Mask</label>
                                    <input
                                        type="text"
                                        value={formData.subnet_mask}
                                        onChange={(e) => setFormData({ ...formData, subnet_mask: e.target.value })}
                                        placeholder="255.255.255.0"
                                        className="input-field w-full"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-400 mb-1">Default Gateway</label>
                                    <input
                                        type="text"
                                        value={formData.gateway}
                                        onChange={(e) => setFormData({ ...formData, gateway: e.target.value })}
                                        placeholder="192.168.1.1"
                                        className="input-field w-full"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-400 mb-1">Primary DNS</label>
                                    <input
                                        type="text"
                                        value={formData.primary_dns}
                                        onChange={(e) => setFormData({ ...formData, primary_dns: e.target.value })}
                                        placeholder="8.8.8.8"
                                        className="input-field w-full"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-400 mb-1">Secondary DNS</label>
                                    <input
                                        type="text"
                                        value={formData.secondary_dns}
                                        onChange={(e) => setFormData({ ...formData, secondary_dns: e.target.value })}
                                        placeholder="8.8.4.4"
                                        className="input-field w-full"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Apply Button */}
                        <div className="mt-6">
                            <Button variant="primary" onClick={handleApplyConfig} loading={saving}>
                                Apply Configuration
                            </Button>
                        </div>
                    </>
                )}
            </Card>

            {/* Quick Commands */}
            <Card title="IP Commands">
                <div className="flex flex-wrap gap-3">
                    <Button variant="secondary" onClick={() => runCommand('ipconfig')}>
                        <Terminal className="w-4 h-4" />
                        ipconfig
                    </Button>
                    <Button variant="secondary" onClick={() => runCommand('ipconfig_all')}>
                        <Terminal className="w-4 h-4" />
                        ipconfig /all
                    </Button>
                    <Button variant="secondary" onClick={() => runCommand('release')}>
                        <WifiOff className="w-4 h-4" />
                        Release IP
                    </Button>
                    <Button variant="secondary" onClick={() => runCommand('renew')}>
                        <Wifi className="w-4 h-4" />
                        Renew IP
                    </Button>
                    <Button variant="secondary" onClick={() => runCommand('flush')}>
                        <Trash2 className="w-4 h-4" />
                        Flush DNS
                    </Button>
                    <Button variant="secondary" onClick={() => runCommand('dns')}>
                        <ArrowDownUp className="w-4 h-4" />
                        Display DNS
                    </Button>
                </div>
            </Card>

            {/* Command Output */}
            {output && (
                <Card title="Command Output">
                    <div className="relative">
                        <pre className="p-4 bg-black/30 rounded-xl text-green-400 text-sm font-mono max-h-64 overflow-auto whitespace-pre-wrap scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-transparent">
                            {output}
                        </pre>
                        <button
                            onClick={() => setOutput('')}
                            className="absolute top-2 right-2 px-2 py-1 text-xs bg-white/10 rounded hover:bg-white/20"
                        >
                            Clear
                        </button>
                    </div>
                </Card>
            )}
        </motion.div>
    );
}
```

---

## 4. Performance Benchmarks

### 4.1 Expected Performance Improvements

| Scenario | Current (ms) | After P0 (ms) | After All (ms) | Improvement |
|----------|--------------|---------------|----------------|-------------|
| First adapter load | 550-1500 | 150-300 | 150-300 | **60-80%** |
| Cache hit | 550-1500 | 0-10 | 0-10 | **99%+** |
| Rapid switching (5×) | 2750-7500 | 150-450 | 150-300 | **95%+** |
| Page reload | 550-1500 | 150-300 | 150-300 | **60-80%** |
| After applying changes | 550-1500 | 150-300 | 150-300 | **60-80%** |

### 4.2 Latency Breakdown (Before Optimization)

```
┌─────────────────────────────────────────────────────────────────┐
│ Current: get_ip_configuration() - 550-1500ms total             │
├─────────────────────────────────────────────────────────────────┤
│ [===== Get IP Address =====] 100-300ms (PowerShell spawn)      │
│ [===== Get Gateway ========] 100-300ms (PowerShell spawn)      │
│ [===== Get DNS ============] 100-300ms (PowerShell spawn)      │
│ [===== Get DHCP Status ====] 100-300ms (PowerShell spawn)      │
│ [= JSON Parsing =] 50ms                                        │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 Latency Breakdown (After Optimization)

```
┌─────────────────────────────────────────────────────────────────┐
│ Optimized: get_ip_configuration_optimized() - 150-300ms        │
├─────────────────────────────────────────────────────────────────┤
│ [= Cache Check =] 0-5ms                                        │
│ [========= Unified PowerShell Script =========] 100-250ms      │
│ [= JSON Parsing + Cache Update =] 10-20ms                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Cache Hit Path - <10ms                                          │
├─────────────────────────────────────────────────────────────────┤
│ [= Cache Check =] 0-5ms                                        │
│ [= Return Cached =] 0-5ms                                      │
└─────────────────────────────────────────────────────────────────┘
```

### 4.4 Memory Impact

| Component | Memory Usage | Notes |
|-----------|--------------|-------|
| Rust NetworkCache | ~1-2 KB per adapter | Minimal overhead |
| React cache (Map) | ~0.5-1 KB per adapter | In-memory only |
| Total for 5 adapters | ~10-15 KB | Negligible |

---

## 5. Edge Cases & Error Handling

### 5.1 PowerShell Execution Failure

**Scenario:** PowerShell fails to execute or times out.

**Handling Strategy:**
```rust
// In network_unified.rs
match output.status.success() {
    true => parse_response(output.stdout),
    false => {
        // Log error for debugging
        log::error!("PowerShell failed: {}", String::from_utf8_lossy(&output.stderr));
        
        // Try to return stale cache data if available
        if let Some((stale_data, _)) = NETWORK_CACHE.get_config_stale(&adapter_name) {
            log::warn!("Returning stale cache for {}", adapter_name);
            return Ok(stale_data.into());
        }
        
        // No cache, return error
        Err("PowerShell execution failed".into())
    }
}
```

**React Side:**
```typescript
// In useNetworkData.ts
const { data, error, loading } = useNetworkData(adapter);

// Show stale data with warning badge
if (error && cache.getWithStaleStatus(adapter)[0]) {
    return (
        <div className="relative">
            <StaleBadge />
            <ConfigForm data={cache.get(adapter)!} disabled />
        </div>
    );
}
```

### 5.2 Cache Corruption / Stale Data

**Scenario:** Cached data becomes invalid (e.g., IP changed externally).

**Handling Strategy:**
- TTL-based expiration (30 seconds default)
- Force refresh button available to users
- Invalidate cache after any `apply*` operation

```typescript
// Force refresh pattern
<Button onClick={() => {
    cache.invalidate(selectedAdapter);
    invoke('invalidate_adapter_cache', { adapterName: selectedAdapter });
    refetchConfig();
}}>
    <RefreshCw className="w-4 h-4" />
    Force Refresh
</Button>
```

### 5.3 Network Adapter Disappearing

**Scenario:** USB adapter unplugged or adapter disabled mid-operation.

**Handling Strategy:**
```rust
// PowerShell handles this gracefully with -ErrorAction SilentlyContinue
// Returns empty/null values instead of throwing

// React should handle null/empty values
if (!ipConfig || !ipConfig.ip_address) {
    return (
        <EmptyState
            icon={<WifiOff />}
            title="No Configuration"
            description="This adapter has no IP configuration or is disconnected."
        />
    );
}
```

### 5.4 Admin Privilege Issues

**Scenario:** User tries to apply changes without admin rights.

**Handling Strategy:**
```rust
// In apply_dhcp / apply_static_ip
if !output.status.success() {
    let stderr = String::from_utf8_lossy(&output.stderr);
    
    // Detect admin error
    if stderr.contains("Access is denied") || stderr.contains("Administrator") {
        return Err("Administrator privileges required. Please run as Administrator.".into());
    }
    
    return Err(format!("Operation failed: {}", stderr));
}
```

### 5.5 Graceful Degradation Levels

| Level | Condition | Behavior |
|-------|-----------|----------|
| L0 | Everything works | Normal operation with caching |
| L1 | Cache miss, fetch succeeds | Show skeleton → load data |
| L2 | Cache hit (stale) | Show stale badge, background refresh |
| L3 | Fetch fails, stale cache exists | Show stale data with error toast |
| L4 | Fetch fails, no cache | Show error state with retry button |

---

## 6. Implementation Checklist

### Priority 0 (Critical) - Day 1-2

- [ ] **P0.1: Create Rust cache module** (4 hours)
  - File: `src-tauri/src/cache.rs`
  - Add `lazy_static` to Cargo.toml
  - Implement `CacheEntry<T>`, `NetworkCache`, `NETWORK_CACHE`
  - Unit tests for TTL expiration

- [ ] **P0.2: Create unified PowerShell command** (4 hours)
  - File: `src-tauri/src/network_unified.rs`
  - Implement `get_ip_configuration_optimized`
  - Add cache integration
  - Register commands in `lib.rs`

- [ ] **P0.3: Add cache invalidation commands** (2 hours)
  - Implement `invalidate_adapter_cache`
  - Implement `invalidate_all_network_cache`
  - Call invalidation after `apply_dhcp` / `apply_static_ip`

### Priority 1 (High) - Day 3

- [ ] **P1.1: Create React skeleton components** (2 hours)
  - File: `src/components/NetworkConfigSkeleton.tsx`
  - Match exact layout of IP Configuration card
  - Add AnimatePresence for smooth transitions

- [ ] **P1.2: Implement debouncing hook** (3 hours)
  - File: `src/hooks/useNetworkData.ts`
  - 150ms debounce on adapter selection
  - AbortController for request cancellation
  - Loading state management

- [ ] **P1.3: Update NetworkTab.tsx** (3 hours)
  - Integrate `useNetworkData` hook
  - Replace loading overlay with skeleton
  - Add cache invalidation on apply

### Priority 2 (Medium) - Day 4

- [ ] **P2.1: Implement React-side cache** (3 hours)
  - File: `src/hooks/useNetworkCache.ts`
  - Map-based storage with TTL
  - useSyncExternalStore for reactivity
  - Stale-while-revalidate pattern

- [ ] **P2.2: Add force refresh button** (1 hour)
  - Clear both caches on click
  - Show loading indicator

- [ ] **P2.3: Error state improvements** (2 hours)
  - Stale data badge component
  - Retry button for failed fetches
  - Toast notifications for errors

### Priority 3 (Low) - Day 5

- [ ] **P3.1: Add cache statistics** (1 hour)
  - Debug panel showing cache status
  - Only in development mode

- [ ] **P3.2: Performance monitoring** (2 hours)
  - Log timing for cache hits vs misses
  - Console output in dev mode

- [ ] **P3.3: Documentation** (1 hour)
  - Update README with new architecture
  - Add inline code comments

---

## 7. File Changes Summary

### New Files to Create

| File Path | Description | Priority |
|-----------|-------------|----------|
| `src-tauri/src/cache.rs` | Rust-side cache implementation | P0 |
| `src-tauri/src/network_unified.rs` | Unified PowerShell query | P0 |
| `src/hooks/useNetworkData.ts` | Debounced data fetching hook | P1 |
| `src/hooks/useNetworkCache.ts` | React-side cache hook | P2 |
| `src/components/NetworkConfigSkeleton.tsx` | Skeleton loading components | P1 |

### Files to Modify

| File Path | Changes Required | Priority |
|-----------|------------------|----------|
| `src-tauri/Cargo.toml` | Add `lazy_static = "1.4"` dependency | P0 |
| `src-tauri/src/lib.rs` | Register new commands | P0 |
| `src-tauri/src/network.rs` | Add cache invalidation calls | P0 |
| `src/components/NetworkTab.tsx` | Integrate hooks, skeletons | P1 |
| `src/lib/tauri.ts` | Add new command type exports | P1 |

### Cargo.toml Addition

```toml
[dependencies]
# ... existing dependencies ...
lazy_static = "1.4"
log = "0.4"
```

### lib.rs Command Registration

```rust
// In src-tauri/src/lib.rs, add to invoke_handler:

mod cache;
mod network_unified;

.invoke_handler(tauri::generate_handler![
    // ... existing commands ...
    network_unified::get_ip_configuration_optimized,
    network_unified::invalidate_adapter_cache,
    network_unified::invalidate_all_network_cache,
    network_unified::get_cache_stats,
])
```

### tauri.ts Type Additions

```typescript
// In src/lib/tauri.ts, add:

export async function getIPConfigurationOptimized(adapterName: string): Promise<IPConfiguration> {
    return invoke<IPConfiguration>('get_ip_configuration_optimized', { adapterName });
}

export async function invalidateAdapterCache(adapterName: string): Promise<void> {
    return invoke<void>('invalidate_adapter_cache', { adapterName });
}

export async function invalidateAllNetworkCache(): Promise<void> {
    return invoke<void>('invalidate_all_network_cache');
}

export interface CacheStats {
    cached_configs: number;
    has_adapter_list: boolean;
}

export async function getCacheStats(): Promise<CacheStats> {
    return invoke<CacheStats>('get_cache_stats');
}
```

---

## Appendix A: Testing Guide

### Manual Testing Checklist

1. **First Load Performance**
   - [ ] Time from page load to data display
   - [ ] Skeleton shows immediately
   - [ ] No UI freeze during load

2. **Cache Hit Behavior**
   - [ ] Switch adapter, switch back → instant load
   - [ ] Verify no PowerShell process spawns on cache hit

3. **Debouncing**
   - [ ] Rapidly click through adapters
   - [ ] Only last adapter should load
   - [ ] No queued requests

4. **Cache Invalidation**
   - [ ] Apply config → cache cleared
   - [ ] Force refresh button works
   - [ ] Stale data badge appears correctly

5. **Error Handling**
   - [ ] Unplug adapter mid-load → graceful error
   - [ ] No admin rights → clear error message
   - [ ] Network disconnected → shows cached data

### Automated Testing

```rust
// In cache.rs tests
#[test]
fn test_cache_expiration() {
    let cache = NetworkCache::new();
    let config = create_test_config();
    
    cache.set_config_with_ttl("test", config.clone(), 1);
    assert!(cache.get_config("test").is_some());
    
    std::thread::sleep(Duration::from_secs(2));
    assert!(cache.get_config("test").is_none());
    
    // But stale should still return
    let (stale, is_stale) = cache.get_config_stale("test").unwrap();
    assert!(is_stale);
}
```

---

## Appendix B: Rollback Plan

If issues arise with the new caching system:

1. **Quick Disable**: Set cache TTL to 0
   ```rust
   const DEFAULT_TTL_SECS: u64 = 0; // Effectively disables cache
   ```

2. **Full Rollback**: Revert to original `get_ip_configuration`
   ```typescript
   // In NetworkTab.tsx, change back to:
   const config = await getIPConfiguration(adapterName);
   ```

3. **Partial Rollback**: Keep unified PS script, remove cache
   - Remove cache checks from `get_ip_configuration_optimized`
   - Keep single PowerShell call benefit

---

## Appendix C: Future Optimizations

### Phase 2 Improvements (Post-Launch)

1. **WebSocket Real-time Updates**
   - Push notifications when adapter state changes
   - No polling required

2. **Background Prefetching**
   - Prefetch all adapters' config on app start
   - User sees instant load for any adapter

3. **Persistent Cache**
   - Store cache to disk for app restart
   - Faster initial load on app start

4. **Rust-native Network APIs**
   - Replace PowerShell with direct Windows API calls
   - Even faster than unified PS script

---

**Document End**

*Last Updated: December 2024*
*Author: Engineering Team*
*Review Status: Ready for Implementation*