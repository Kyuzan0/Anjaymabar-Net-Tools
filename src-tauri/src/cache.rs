//! Cache module for network configuration data
//! Provides thread-safe, TTL-based caching for expensive PowerShell operations

use std::collections::HashMap;
use std::sync::Mutex;
use std::time::{Duration, Instant};
use serde::{Deserialize, Serialize};
use lazy_static::lazy_static;

use crate::network::IPConfiguration;

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
    pub fn get_ip_config_stale(&self, adapter_name: &str) -> Option<(IPConfiguration, bool)> {
        let cache = self.configs.lock().ok()?;
        let entry = cache.get(adapter_name)?;
        Some((entry.data.clone(), entry.is_expired()))
    }

    /// Store IP configuration in cache
    pub fn set_ip_config(&self, adapter_name: &str, config: IPConfiguration) {
        if let Ok(mut cache) = self.configs.lock() {
            cache.insert(adapter_name.to_string(), CacheEntry::new(config));
        }
    }

    /// Store IP configuration with custom TTL
    pub fn set_ip_config_with_ttl(&self, adapter_name: &str, config: IPConfiguration, ttl_secs: u64) {
        if let Ok(mut cache) = self.configs.lock() {
            cache.insert(
                adapter_name.to_string(),
                CacheEntry::with_ttl(config, ttl_secs),
            );
        }
    }

    /// Invalidate cache for specific adapter
    pub fn invalidate_adapter(&self, adapter_name: &str) {
        if let Ok(mut cache) = self.configs.lock() {
            cache.remove(adapter_name);
        }
    }

    /// Invalidate all cached configurations
    pub fn invalidate_all(&self) {
        if let Ok(mut cache) = self.configs.lock() {
            cache.clear();
        }
    }

    /// Get cache statistics for debugging
    pub fn stats(&self) -> CacheStats {
        let config_count = self.configs.lock().map(|c| c.len()).unwrap_or(0);
        
        CacheStats {
            cached_configs: config_count,
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