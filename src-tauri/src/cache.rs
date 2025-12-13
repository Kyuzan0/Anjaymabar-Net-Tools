//! Cache module for network configuration data
//! Provides thread-safe, TTL-based caching for expensive PowerShell operations

use std::collections::HashMap;
use std::sync::{Mutex, TryLockError};
use std::time::{Duration, Instant};
use serde::{Deserialize, Serialize};
use lazy_static::lazy_static;
use log::{debug, warn, error, info};

use crate::network::IPConfiguration;

/// Default cache TTL: 30 seconds
/// Network config rarely changes, safe to cache for short period
const DEFAULT_TTL_SECS: u64 = 30;

/// Maximum time to wait for cache lock acquisition
/// Prevents indefinite blocking on cache operations
const LOCK_TIMEOUT_MS: u64 = 100;

/// Maximum number of cache entries to prevent memory bloat
const MAX_CACHE_ENTRIES: usize = 50;

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
    #[allow(dead_code)]
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
    #[allow(dead_code)]
    pub fn remaining_ttl_secs(&self) -> u64 {
        let elapsed = self.created_at.elapsed();
        if elapsed > self.ttl {
            0
        } else {
            (self.ttl - elapsed).as_secs()
        }
    }
}

/// Thread-safe network configuration cache
/// Uses Mutex for interior mutability in lazy_static context
pub struct NetworkCache {
    /// Map of adapter_name -> cached config
    configs: Mutex<HashMap<String, CacheEntry<IPConfiguration>>>,
}

impl NetworkCache {
    /// Create a new empty cache
    pub fn new() -> Self {
        Self {
            configs: Mutex::new(HashMap::new()),
        }
    }

    /// Get cached IP configuration for an adapter
    /// Returns None if not cached or expired
    pub fn get_ip_config(&self, adapter_name: &str) -> Option<IPConfiguration> {
        let start_time = Instant::now();
        
        // Try to acquire lock with timeout
        let cache = match self.acquire_lock_with_timeout("get_ip_config") {
            Ok(cache) => cache,
            Err(e) => {
                warn!("Failed to acquire cache lock for get_ip_config: {}", e);
                return None;
            }
        };
        
        let entry = match cache.get(adapter_name) {
            Some(entry) => entry,
            None => {
                debug!("Cache miss for adapter: {}", adapter_name);
                return None;
            }
        };
        
        if entry.is_expired() {
            debug!("Cache entry expired for adapter: {}", adapter_name);
            // Don't return expired data, but don't remove yet
            // (allows stale-while-revalidate pattern)
            None
        } else {
            let elapsed = start_time.elapsed();
            if elapsed.as_millis() > 10 {
                warn!("Slow cache get operation for {}: {}ms", adapter_name, elapsed.as_millis());
            } else {
                debug!("Cache hit for adapter: {} ({}ms)", adapter_name, elapsed.as_millis());
            }
            Some(entry.data.clone())
        }
    }

    /// Get cached config even if expired (for stale fallback)
    pub fn get_ip_config_stale(&self, adapter_name: &str) -> Option<(IPConfiguration, bool)> {
        let start_time = Instant::now();
        
        // Try to acquire lock with timeout
        let cache = match self.acquire_lock_with_timeout("get_ip_config_stale") {
            Ok(cache) => cache,
            Err(e) => {
                warn!("Failed to acquire cache lock for get_ip_config_stale: {}", e);
                return None;
            }
        };
        
        let entry = match cache.get(adapter_name) {
            Some(entry) => entry,
            None => {
                debug!("Cache miss for stale retrieval: {}", adapter_name);
                return None;
            }
        };
        
        let is_expired = entry.is_expired();
        let elapsed = start_time.elapsed();
        
        if elapsed.as_millis() > 10 {
            warn!("Slow stale cache get for {}: {}ms (expired: {})", adapter_name, elapsed.as_millis(), is_expired);
        } else {
            debug!("Stale cache retrieval for {}: {}ms (expired: {})", adapter_name, elapsed.as_millis(), is_expired);
        }
        
        Some((entry.data.clone(), is_expired))
    }

    /// Store IP configuration in cache
    pub fn set_ip_config(&self, adapter_name: &str, config: IPConfiguration) {
        let start_time = Instant::now();
        
        // Try to acquire lock with timeout
        let mut cache = match self.acquire_lock_with_timeout("set_ip_config") {
            Ok(cache) => cache,
            Err(e) => {
                error!("Failed to acquire cache lock for set_ip_config: {}", e);
                return;
            }
        };
        
        // Check cache size limit
        if cache.len() >= MAX_CACHE_ENTRIES {
            warn!("Cache size limit reached ({}), removing oldest entries", MAX_CACHE_ENTRIES);
            self.cleanup_old_entries(&mut cache);
        }
        
        cache.insert(adapter_name.to_string(), CacheEntry::new(config));
        
        let elapsed = start_time.elapsed();
        if elapsed.as_millis() > 10 {
            warn!("Slow cache set operation for {}: {}ms", adapter_name, elapsed.as_millis());
        } else {
            debug!("Cached IP configuration for adapter: {} ({}ms)", adapter_name, elapsed.as_millis());
        }
    }

    /// Store IP configuration with custom TTL
    #[allow(dead_code)]
    pub fn set_ip_config_with_ttl(&self, adapter_name: &str, config: IPConfiguration, ttl_secs: u64) {
        let start_time = Instant::now();
        
        // Try to acquire lock with timeout
        let mut cache = match self.acquire_lock_with_timeout("set_ip_config_with_ttl") {
            Ok(cache) => cache,
            Err(e) => {
                error!("Failed to acquire cache lock for set_ip_config_with_ttl: {}", e);
                return;
            }
        };
        
        // Check cache size limit
        if cache.len() >= MAX_CACHE_ENTRIES {
            warn!("Cache size limit reached ({}), removing oldest entries", MAX_CACHE_ENTRIES);
            self.cleanup_old_entries(&mut cache);
        }
        
        cache.insert(
            adapter_name.to_string(),
            CacheEntry::with_ttl(config, ttl_secs),
        );
        
        let elapsed = start_time.elapsed();
        debug!("Cached IP configuration with TTL {}s for adapter: {} ({}ms)", ttl_secs, adapter_name, elapsed.as_millis());
    }

    /// Invalidate cache for specific adapter
    pub fn invalidate_adapter(&self, adapter_name: &str) {
        let start_time = Instant::now();
        
        // Try to acquire lock with timeout
        let mut cache = match self.acquire_lock_with_timeout("invalidate_adapter") {
            Ok(cache) => cache,
            Err(e) => {
                warn!("Failed to acquire cache lock for invalidate_adapter: {}", e);
                return;
            }
        };
        
        let removed = cache.remove(adapter_name).is_some();
        let elapsed = start_time.elapsed();
        
        if removed {
            info!("Invalidated cache for adapter: {} ({}ms)", adapter_name, elapsed.as_millis());
        } else {
            debug!("Attempted to invalidate non-existent cache entry: {} ({}ms)", adapter_name, elapsed.as_millis());
        }
    }

    /// Invalidate all cached configurations
    pub fn invalidate_all(&self) {
        let start_time = Instant::now();
        
        // Try to acquire lock with timeout
        let mut cache = match self.acquire_lock_with_timeout("invalidate_all") {
            Ok(cache) => cache,
            Err(e) => {
                warn!("Failed to acquire cache lock for invalidate_all: {}", e);
                return;
            }
        };
        
        let count = cache.len();
        cache.clear();
        let elapsed = start_time.elapsed();
        
        info!("Invalidated all cache entries ({} entries) ({}ms)", count, elapsed.as_millis());
    }

    /// Get cache statistics for debugging
    pub fn stats(&self) -> CacheStats {
        let start_time = Instant::now();
        
        // Try to acquire lock with timeout
        let cache = match self.acquire_lock_with_timeout("stats") {
            Ok(cache) => cache,
            Err(e) => {
                warn!("Failed to acquire cache lock for stats: {}", e);
                return CacheStats {
                    cached_configs: 0,
                };
            }
        };
        
        let config_count = cache.len();
        let elapsed = start_time.elapsed();
        
        debug!("Cache stats retrieved: {} entries ({}ms)", config_count, elapsed.as_millis());
        
        CacheStats {
            cached_configs: config_count,
        }
    }
    
    /// Acquire cache lock with timeout to prevent indefinite blocking
    fn acquire_lock_with_timeout(&self, operation: &str) -> Result<std::sync::MutexGuard<'_, HashMap<String, CacheEntry<IPConfiguration>>>, String> {
        let start_time = Instant::now();
        let timeout = Duration::from_millis(LOCK_TIMEOUT_MS);
        
        loop {
            match self.configs.try_lock() {
                Ok(guard) => {
                    let elapsed = start_time.elapsed();
                    if elapsed.as_millis() > 5 {
                        debug!("Cache lock acquired for {} after {}ms", operation, elapsed.as_millis());
                    }
                    return Ok(guard);
                }
                Err(TryLockError::WouldBlock) => {
                    if start_time.elapsed() > timeout {
                        return Err(format!("Timeout acquiring cache lock for {} after {}ms", operation, timeout.as_millis()));
                    }
                    // Sleep for a short time before retrying
                    std::thread::sleep(Duration::from_millis(1));
                }
                Err(TryLockError::Poisoned(_)) => {
                    return Err(format!("Cache lock is poisoned for {}", operation));
                }
            }
        }
    }
    
    /// Clean up old entries to prevent memory bloat
    fn cleanup_old_entries(&self, cache: &mut HashMap<String, CacheEntry<IPConfiguration>>) {
        let mut expired_keys = Vec::new();
        
        // Find expired entries
        for (key, entry) in cache.iter() {
            if entry.is_expired() {
                expired_keys.push(key.clone());
            }
        }
        
        // Remove expired entries
        for key in expired_keys {
            cache.remove(&key);
            debug!("Removed expired cache entry: {}", key);
        }
        
        // If still too many entries, remove the oldest ones
        if cache.len() >= MAX_CACHE_ENTRIES {
            // Collect all entries with their creation times
            let mut entries_with_time: Vec<(String, Instant)> = cache.iter()
                .map(|(key, entry)| (key.clone(), entry.created_at))
                .collect();
            
            // Sort by creation time (oldest first)
            entries_with_time.sort_by_key(|(_, time)| *time);
            
            // Determine how many to remove
            let to_remove = entries_with_time.len() - MAX_CACHE_ENTRIES + 1;
            
            // Collect keys to remove
            let keys_to_remove: Vec<String> = entries_with_time
                .into_iter()
                .take(to_remove)
                .map(|(key, _)| key)
                .collect();
            
            // Remove the oldest entries
            for key in keys_to_remove {
                cache.remove(&key);
                debug!("Removed old cache entry: {}", key);
            }
        }
    }
}

impl Default for NetworkCache {
    fn default() -> Self {
        Self::new()
    }
}

/// Cache statistics for monitoring
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct CacheStats {
    pub cached_configs: usize,
}

// Global singleton cache instance
lazy_static! {
    /// Global network cache accessible from all Tauri commands
    pub static ref NETWORK_CACHE: NetworkCache = NetworkCache::new();
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_test_config() -> IPConfiguration {
        IPConfiguration {
            ip_address: "192.168.1.1".to_string(),
            subnet_mask: "255.255.255.0".to_string(),
            gateway: "192.168.1.254".to_string(),
            primary_dns: "8.8.8.8".to_string(),
            secondary_dns: "8.8.4.4".to_string(),
            dhcp_enabled: false,
        }
    }

    #[test]
    fn test_cache_entry_not_expired_initially() {
        let entry = CacheEntry::new("test".to_string());
        assert!(!entry.is_expired());
    }

    #[test]
    fn test_cache_set_get() {
        let cache = NetworkCache::new();
        let config = create_test_config();

        cache.set_ip_config("eth0", config.clone());
        
        let retrieved = cache.get_ip_config("eth0");
        assert!(retrieved.is_some());
        assert_eq!(retrieved.unwrap().ip_address, "192.168.1.1");
    }

    #[test]
    fn test_cache_invalidate_adapter() {
        let cache = NetworkCache::new();
        let config = create_test_config();

        cache.set_ip_config("eth0", config);
        assert!(cache.get_ip_config("eth0").is_some());
        
        cache.invalidate_adapter("eth0");
        assert!(cache.get_ip_config("eth0").is_none());
    }

    #[test]
    fn test_cache_invalidate_all() {
        let cache = NetworkCache::new();
        let config = create_test_config();

        cache.set_ip_config("eth0", config.clone());
        cache.set_ip_config("eth1", config);
        
        assert_eq!(cache.stats().cached_configs, 2);
        
        cache.invalidate_all();
        assert_eq!(cache.stats().cached_configs, 0);
    }

    #[test]
    fn test_cache_stale_retrieval() {
        let cache = NetworkCache::new();
        let config = create_test_config();

        cache.set_ip_config("eth0", config);
        
        let (retrieved, is_stale) = cache.get_ip_config_stale("eth0").unwrap();
        assert!(!is_stale);
        assert_eq!(retrieved.ip_address, "192.168.1.1");
    }
}