/**
 * Custom hook for fetching network adapter configuration with optimizations:
 * - 150ms debouncing (prevents rapid consecutive calls)
 * - AbortController (cancels in-flight requests when adapter changes)
 * - Cache-first strategy with fallback
 * - Loading states for skeleton UI integration
 * - Error handling with retry capability
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { type IPConfiguration, type NetworkAdapter } from '../lib/tauri';
import { useNetworkCache, networkCacheStore } from './useNetworkCache';

// Debounce delay in milliseconds
const DEBOUNCE_MS = 150;

/**
 * Load state type for better UI control
 */
export type LoadState = 'idle' | 'loading' | 'error';

/**
 * State interface for useNetworkData hook
 */
interface UseNetworkDataState {
    /** List of available network adapters */
    adapters: NetworkAdapter[];
    /** Current IP configuration data */
    currentConfig: IPConfiguration | null;
    /** Loading state for UI feedback */
    loadState: LoadState;
    /** Error message if fetch failed */
    error: string | null;
    /** Currently selected adapter name */
    selectedAdapter: string;
    /** Whether adapters are loading */
    adaptersLoading: boolean;
}

/**
 * Return type for useNetworkData hook
 */
interface UseNetworkDataReturn extends UseNetworkDataState {
    /** Select a new adapter (with debouncing) */
    selectAdapter: (adapterName: string) => void;
    /** Refresh adapter list */
    refreshAdapters: () => Promise<void>;
    /** Force invalidate cache and reload current adapter config */
    invalidateCache: () => void;
    /** Manually refetch current config without debounce */
    refetchConfig: () => Promise<void>;
}

/**
 * Hook for fetching network configuration with debouncing and caching
 * 
 * @returns State object with data, loading states, and utility functions
 * 
 * @example
 * ```tsx
 * const { 
 *   adapters, 
 *   currentConfig, 
 *   loadState, 
 *   selectedAdapter,
 *   selectAdapter,
 *   refreshAdapters,
 *   invalidateCache
 * } = useNetworkData();
 * 
 * if (loadState === 'loading') return <NetworkConfigSkeleton />;
 * if (loadState === 'error') return <ErrorDisplay onRetry={refetchConfig} />;
 * if (!currentConfig) return null;
 * 
 * return <IPConfigForm initialData={currentConfig} />;
 * ```
 */
export function useNetworkData(): UseNetworkDataReturn {
    const [state, setState] = useState<UseNetworkDataState>({
        adapters: [],
        currentConfig: null,
        loadState: 'idle',
        error: null,
        selectedAdapter: '',
        adaptersLoading: true,
    });

    const cache = useNetworkCache();

    // Refs for managing async operations
    const abortControllerRef = useRef<AbortController | null>(null);
    const debounceTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const isMountedRef = useRef(true);

    // Track the current adapter to detect stale responses
    const currentAdapterRef = useRef<string>('');

    /**
     * Fetch IP configuration for adapter (internal, no debounce)
     */
    const fetchIPConfig = useCallback(async (adapterName: string, skipCache = false) => {
        if (!adapterName) return;

        // Cancel any existing request
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }

        // Create new abort controller
        abortControllerRef.current = new AbortController();

        // Check cache first (unless skipCache is true)
        if (!skipCache) {
            const cachedConfig = cache.getCachedIPConfig(adapterName);
            if (cachedConfig) {
                if (isMountedRef.current && currentAdapterRef.current === adapterName) {
                    setState(prev => ({
                        ...prev,
                        currentConfig: cachedConfig,
                        loadState: 'idle',
                        error: null,
                    }));
                }
                return;
            }
        }

        // Set loading state
        setState(prev => ({
            ...prev,
            loadState: 'loading',
            error: null,
        }));

        try {
            // Try the optimized unified command first
            let config: IPConfiguration;
            try {
                config = await invoke<IPConfiguration>('get_ip_configuration_unified', {
                    adapterName: adapterName,
                });
            } catch {
                // Fallback to original command if unified fails
                config = await invoke<IPConfiguration>('get_ip_configuration', {
                    adapterName: adapterName,
                });
            }

            // Check if component is still mounted and this is still the current request
            if (!isMountedRef.current || currentAdapterRef.current !== adapterName) {
                return;
            }

            // Update cache
            cache.setCachedIPConfig(adapterName, config);

            setState(prev => ({
                ...prev,
                currentConfig: config,
                loadState: 'idle',
                error: null,
            }));
        } catch (error) {
            // Ignore abort errors
            if (error instanceof Error && error.name === 'AbortError') {
                return;
            }

            if (!isMountedRef.current || currentAdapterRef.current !== adapterName) {
                return;
            }

            // Try to get stale cache for fallback
            const [staleConfig] = cache.getCachedIPConfigWithStale(adapterName);
            
            setState(prev => ({
                ...prev,
                currentConfig: staleConfig, // May be null or stale data
                loadState: 'error',
                error: error instanceof Error ? error.message : String(error),
            }));
        }
    }, [cache]);

    /**
     * Debounced adapter selection
     */
    const selectAdapter = useCallback((adapterName: string) => {
        // Update selected adapter immediately for UI feedback
        currentAdapterRef.current = adapterName;
        setState(prev => ({
            ...prev,
            selectedAdapter: adapterName,
            loadState: 'loading', // Set loading immediately for responsive feel
        }));

        // Clear any existing debounce timeout
        if (debounceTimeoutRef.current) {
            clearTimeout(debounceTimeoutRef.current);
        }

        // Cancel any in-flight request
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }

        // Schedule the actual fetch with debounce
        debounceTimeoutRef.current = setTimeout(() => {
            fetchIPConfig(adapterName);
        }, DEBOUNCE_MS);
    }, [fetchIPConfig]);

    /**
     * Fetch network adapters list
     */
    const refreshAdapters = useCallback(async () => {
        setState(prev => ({ ...prev, adaptersLoading: true }));

        try {
            // Check cache first
            const cachedAdapters = cache.getCachedAdapters();
            if (cachedAdapters && cachedAdapters.length > 0) {
                setState(prev => ({
                    ...prev,
                    adapters: cachedAdapters,
                    adaptersLoading: false,
                    // Set first adapter if none selected
                    selectedAdapter: prev.selectedAdapter || cachedAdapters[0].name,
                }));
                
                // Trigger config load for selected adapter
                if (!state.selectedAdapter && cachedAdapters.length > 0) {
                    currentAdapterRef.current = cachedAdapters[0].name;
                    fetchIPConfig(cachedAdapters[0].name);
                }
                return;
            }

            const adapters = await invoke<NetworkAdapter[]>('get_network_adapters');

            if (!isMountedRef.current) return;

            // Update cache
            cache.setCachedAdapters(adapters);

            setState(prev => ({
                ...prev,
                adapters,
                adaptersLoading: false,
                // Set first adapter if none selected
                selectedAdapter: prev.selectedAdapter || (adapters.length > 0 ? adapters[0].name : ''),
            }));

            // Load config for first adapter if none selected
            if (!state.selectedAdapter && adapters.length > 0) {
                currentAdapterRef.current = adapters[0].name;
                fetchIPConfig(adapters[0].name);
            }
        } catch (error) {
            if (!isMountedRef.current) return;

            setState(prev => ({
                ...prev,
                adaptersLoading: false,
                error: error instanceof Error ? error.message : String(error),
            }));
        }
    }, [cache, fetchIPConfig, state.selectedAdapter]);

    /**
     * Force invalidate cache and reload
     */
    const invalidateCache = useCallback(() => {
        // Clear React-side cache
        cache.invalidateAll();

        // Clear Rust-side cache via Tauri command
        invoke('invalidate_all_network_cache').catch(console.error);

        // Reload current adapter config
        if (state.selectedAdapter) {
            fetchIPConfig(state.selectedAdapter, true);
        }
    }, [cache, state.selectedAdapter, fetchIPConfig]);

    /**
     * Refetch current config without debounce
     */
    const refetchConfig = useCallback(async () => {
        if (state.selectedAdapter) {
            await fetchIPConfig(state.selectedAdapter, true);
        }
    }, [state.selectedAdapter, fetchIPConfig]);

    /**
     * Effect: Load adapters on mount
     */
    useEffect(() => {
        refreshAdapters();
    }, [refreshAdapters]);

    /**
     * Effect: Load config when selected adapter changes (from external source)
     */
    useEffect(() => {
        if (state.selectedAdapter && state.selectedAdapter !== currentAdapterRef.current) {
            currentAdapterRef.current = state.selectedAdapter;
            fetchIPConfig(state.selectedAdapter);
        }
    }, [state.selectedAdapter, fetchIPConfig]);

    /**
     * Effect: Track component mount state and cleanup
     */
    useEffect(() => {
        isMountedRef.current = true;
        
        return () => {
            isMountedRef.current = false;
            
            // Cleanup timeouts
            if (debounceTimeoutRef.current) {
                clearTimeout(debounceTimeoutRef.current);
            }
            
            // Cancel any in-flight requests
            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
            }
        };
    }, []);

    return {
        ...state,
        selectAdapter,
        refreshAdapters,
        invalidateCache,
        refetchConfig,
    };
}

/**
 * Simpler hook for fetching just the network adapters list
 * Used when you only need the adapter list without IP config
 */
export function useNetworkAdapters() {
    const [adapters, setAdapters] = useState<NetworkAdapter[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchAdapters = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            // Check cache first
            const cached = networkCacheStore.getCachedAdapters();
            if (cached && cached.length > 0) {
                setAdapters(cached);
                setLoading(false);
                return;
            }

            const data = await invoke<NetworkAdapter[]>('get_network_adapters');
            networkCacheStore.setCachedAdapters(data);
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

export default useNetworkData;