/**
 * Client-side network configuration cache hook
 * Provides React-side caching for IP configurations
 * 
 * Features:
 * - Map-based storage (adapter name -> config)
 * - TTL validation with stale data fallback
 * - Automatic cleanup of expired entries
 * - Singleton pattern via module scope
 * - React 18 compatible with useSyncExternalStore
 * - LocalStorage persistence for faster initial loads
 */

import { useCallback, useMemo, useSyncExternalStore } from 'react';
import { type IPConfiguration } from '../lib/tauri';

// Default TTL: 30 seconds (matches Rust cache)
const DEFAULT_TTL_MS = 30000;

// Cache cleanup interval: 60 seconds
const CLEANUP_INTERVAL_MS = 60000;

// LocalStorage key for persistent cache
const STORAGE_KEY = 'network_cache_v1';

// Maximum age for persistent cache: 5 minutes (after this, data is considered too stale)
const MAX_PERSISTENT_AGE_MS = 5 * 60 * 1000;

/**
 * Cache entry structure with timestamp for TTL validation
 */
export interface CacheEntry<T> {
    data: T;
    timestamp: number;
    ttl: number;
}

/**
 * Structure for persisted cache data in localStorage
 */
interface PersistedCacheData {
    configs: Record<string, { data: IPConfiguration; timestamp: number; ttl: number }>;
    adapters: { data: Array<{ name: string; description: string; status: string; mac_address: string }>; timestamp: number; ttl: number } | null;
    savedAt: number;
}

/**
 * Singleton cache store (module-scoped)
 * Uses a simple observer pattern for React integration
 */
class NetworkCacheStore {
    private cache = new Map<string, CacheEntry<IPConfiguration>>();
    private adapterCache: CacheEntry<Array<{ name: string; description: string; status: string; mac_address: string }>> | null = null;
    private listeners = new Set<() => void>();
    private cleanupInterval: ReturnType<typeof setInterval> | null = null;
    private version = 0; // For snapshot comparison

    constructor() {
        // Load from localStorage on init
        this.loadFromStorage();
        // Start cleanup interval
        this.startCleanup();
    }

    /**
     * Load cache data from localStorage
     */
    private loadFromStorage(): void {
        if (typeof window === 'undefined') return;

        try {
            const stored = localStorage.getItem(STORAGE_KEY);
            if (!stored) return;

            const data: PersistedCacheData = JSON.parse(stored);
            const now = Date.now();

            // Check if persistent cache is too old
            if (now - data.savedAt > MAX_PERSISTENT_AGE_MS) {
                console.log('[NetworkCache] Persistent cache expired, clearing');
                localStorage.removeItem(STORAGE_KEY);
                return;
            }

            // Load IP configs
            if (data.configs) {
                for (const [key, entry] of Object.entries(data.configs)) {
                    // Adjust timestamp to be relative to now for fresh TTL check
                    const adjustedEntry: CacheEntry<IPConfiguration> = {
                        data: entry.data,
                        timestamp: entry.timestamp,
                        ttl: entry.ttl,
                    };
                    this.cache.set(key, adjustedEntry);
                }
            }

            // Load adapters
            if (data.adapters) {
                this.adapterCache = {
                    data: data.adapters.data,
                    timestamp: data.adapters.timestamp,
                    ttl: data.adapters.ttl,
                };
            }

            console.log(`[NetworkCache] Loaded ${this.cache.size} configs from localStorage`);
        } catch (error) {
            console.warn('[NetworkCache] Failed to load from localStorage:', error);
            localStorage.removeItem(STORAGE_KEY);
        }
    }

    /**
     * Save cache data to localStorage
     */
    private saveToStorage(): void {
        if (typeof window === 'undefined') return;

        try {
            const configs: Record<string, { data: IPConfiguration; timestamp: number; ttl: number }> = {};

            for (const [key, entry] of this.cache.entries()) {
                configs[key] = {
                    data: entry.data,
                    timestamp: entry.timestamp,
                    ttl: entry.ttl,
                };
            }

            const data: PersistedCacheData = {
                configs,
                adapters: this.adapterCache ? {
                    data: this.adapterCache.data,
                    timestamp: this.adapterCache.timestamp,
                    ttl: this.adapterCache.ttl,
                } : null,
                savedAt: Date.now(),
            };

            localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
        } catch (error) {
            console.warn('[NetworkCache] Failed to save to localStorage:', error);
        }
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
            if (now > entry.timestamp + entry.ttl) {
                this.cache.delete(key);
                hasChanges = true;
            }
        }

        // Check adapter cache
        if (this.adapterCache && now > this.adapterCache.timestamp + this.adapterCache.ttl) {
            this.adapterCache = null;
            hasChanges = true;
        }

        if (hasChanges) {
            this.version++;
            this.notifyListeners();
            this.saveToStorage();
        }
    }

    /**
     * Notify all subscribed listeners of cache changes
     */
    private notifyListeners(): void {
        this.listeners.forEach(listener => listener());
    }

    /**
     * Check if entry is expired
     */
    private isExpired(entry: CacheEntry<unknown>): boolean {
        return Date.now() > entry.timestamp + entry.ttl;
    }

    /**
     * Get cached IP configuration for adapter (returns null if not found or expired)
     */
    getCachedIPConfig(adapterName: string): IPConfiguration | null {
        const entry = this.cache.get(adapterName);

        if (!entry) return null;

        if (this.isExpired(entry)) {
            // Entry expired, but don't delete yet (stale-while-revalidate)
            return null;
        }

        return entry.data;
    }

    /**
     * Get cached IP config with stale status (for fallback display)
     * Returns [data, isStale] tuple
     */
    getCachedIPConfigWithStale(adapterName: string): [IPConfiguration | null, boolean] {
        const entry = this.cache.get(adapterName);

        if (!entry) return [null, false];

        const isStale = this.isExpired(entry);

        return [entry.data, isStale];
    }

    /**
     * Store IP configuration in cache
     */
    setCachedIPConfig(adapterName: string, data: IPConfiguration, ttl: number = DEFAULT_TTL_MS): void {
        const entry: CacheEntry<IPConfiguration> = {
            data,
            timestamp: Date.now(),
            ttl,
        };

        this.cache.set(adapterName, entry);
        this.version++;
        this.notifyListeners();
        this.saveToStorage();
    }

    /**
     * Get cached adapter list
     */
    getCachedAdapters(): Array<{ name: string; description: string; status: string; mac_address: string }> | null {
        if (!this.adapterCache) return null;

        if (this.isExpired(this.adapterCache)) {
            return null;
        }

        return this.adapterCache.data;
    }

    /**
     * Store adapter list in cache
     */
    setCachedAdapters(adapters: Array<{ name: string; description: string; status: string; mac_address: string }>, ttl: number = DEFAULT_TTL_MS): void {
        this.adapterCache = {
            data: adapters,
            timestamp: Date.now(),
            ttl,
        };
        this.version++;
        this.notifyListeners();
        this.saveToStorage();
    }

    /**
     * Invalidate (remove) cache entry for specific adapter
     */
    invalidateAdapter(adapterName: string): void {
        if (this.cache.has(adapterName)) {
            this.cache.delete(adapterName);
            this.version++;
            this.notifyListeners();
            this.saveToStorage();
        }
    }

    /**
     * Clear all cache entries
     */
    invalidateAll(): void {
        this.cache.clear();
        this.adapterCache = null;
        this.version++;
        this.notifyListeners();
        // Also clear localStorage
        if (typeof window !== 'undefined') {
            localStorage.removeItem(STORAGE_KEY);
        }
    }

    /**
     * Get cache size (number of IP config entries)
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
     * Returns version number for efficient comparison
     */
    getSnapshot(): number {
        return this.version;
    }

    /**
     * Cleanup on unmount
     */
    destroy(): void {
        if (this.cleanupInterval) {
            clearInterval(this.cleanupInterval);
        }
        this.cache.clear();
        this.adapterCache = null;
        this.listeners.clear();
    }
}

// Global singleton instance
export const networkCacheStore = new NetworkCacheStore();

/**
 * Hook for accessing the network configuration cache
 * Uses useSyncExternalStore for React 18 concurrent mode support
 * 
 * @example
 * ```tsx
 * const cache = useNetworkCache();
 * 
 * // Check cache before fetching
 * const cached = cache.getCachedIPConfig(adapterName);
 * if (cached) {
 *   setFormData(cached);
 *   return;
 * }
 * 
 * // After fetching, update cache
 * const data = await fetchConfig(adapterName);
 * cache.setCachedIPConfig(adapterName, data);
 * ```
 */
export function useNetworkCache() {
    // Use useSyncExternalStore for proper React 18 concurrent mode support
    const cacheVersion = useSyncExternalStore(
        useCallback((callback) => networkCacheStore.subscribe(callback), []),
        useCallback(() => networkCacheStore.getSnapshot(), []),
        useCallback(() => networkCacheStore.getSnapshot(), []) // Server snapshot
    );

    // Memoized cache operations - re-created when version changes
    const operations = useMemo(() => ({
        /**
         * Get cached IP config (null if not found or expired)
         */
        getCachedIPConfig: (adapterName: string): IPConfiguration | null => {
            return networkCacheStore.getCachedIPConfig(adapterName);
        },

        /**
         * Get cached IP config with stale status
         */
        getCachedIPConfigWithStale: (adapterName: string): [IPConfiguration | null, boolean] => {
            return networkCacheStore.getCachedIPConfigWithStale(adapterName);
        },

        /**
         * Store IP config in cache
         */
        setCachedIPConfig: (adapterName: string, data: IPConfiguration, ttl?: number): void => {
            networkCacheStore.setCachedIPConfig(adapterName, data, ttl);
        },

        /**
         * Get cached adapter list
         */
        getCachedAdapters: (): Array<{ name: string; description: string; status: string; mac_address: string }> | null => {
            return networkCacheStore.getCachedAdapters();
        },

        /**
         * Store adapter list in cache
         */
        setCachedAdapters: (adapters: Array<{ name: string; description: string; status: string; mac_address: string }>, ttl?: number): void => {
            networkCacheStore.setCachedAdapters(adapters, ttl);
        },

        /**
         * Invalidate cache for specific adapter
         */
        invalidateAdapter: (adapterName: string): void => {
            networkCacheStore.invalidateAdapter(adapterName);
        },

        /**
         * Clear entire cache
         */
        invalidateAll: (): void => {
            networkCacheStore.invalidateAll();
        },

        /**
         * Get cache size
         */
        size: networkCacheStore.size,

        /**
         * Get cached adapter names
         */
        keys: networkCacheStore.keys,

        /**
         * Cache version for dependency tracking
         */
        version: cacheVersion,
    }), [cacheVersion]);

    return operations;
}

// Export direct store functions for non-hook usage
export const getCachedIPConfig = (adapterName: string) => networkCacheStore.getCachedIPConfig(adapterName);
export const setCachedIPConfig = (adapterName: string, data: IPConfiguration, ttl?: number) => networkCacheStore.setCachedIPConfig(adapterName, data, ttl);
export const getCachedAdapters = () => networkCacheStore.getCachedAdapters();
export const setCachedAdapters = (adapters: Array<{ name: string; description: string; status: string; mac_address: string }>, ttl?: number) => networkCacheStore.setCachedAdapters(adapters, ttl);
export const invalidateAdapter = (adapterName: string) => networkCacheStore.invalidateAdapter(adapterName);
export const invalidateAll = () => networkCacheStore.invalidateAll();

export default useNetworkCache;