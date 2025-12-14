/**
 * Network Loading Benchmark Utility
 * 
 * Measures performance of:
 * - Fresh fetch (no cache)
 * - Cache hit (from memory)
 * - localStorage load
 * - Prefetch effectiveness
 */

import { invoke } from '@tauri-apps/api/core';
import { type IPConfiguration } from './tauri';
import { networkCacheStore } from '../hooks/useNetworkCache';

// Storage key for benchmark results
const BENCHMARK_STORAGE_KEY = 'network_benchmark_results';

export interface BenchmarkResult {
    testName: string;
    duration: number; // in milliseconds
    timestamp: number;
    success: boolean;
    details?: string;
}

export interface BenchmarkSummary {
    results: BenchmarkResult[];
    averages: {
        freshFetch: number;
        cacheHit: number;
        localStorageLoad: number;
    };
    improvement: {
        cacheVsFresh: string;
        localStorageVsFresh: string;
    };
    runAt: string;
}

/**
 * High-precision timer using performance.now()
 */
function now(): number {
    return performance.now();
}

/**
 * Format duration for display
 */
function formatDuration(ms: number): string {
    if (ms < 1) {
        return `${(ms * 1000).toFixed(2)}μs`;
    }
    return `${ms.toFixed(2)}ms`;
}

/**
 * Run a single timed test
 */
async function runTimedTest<T>(
    testName: string,
    testFn: () => Promise<T> | T
): Promise<BenchmarkResult> {
    const start = now();
    let success = true;
    let details: string | undefined;

    try {
        await testFn();
    } catch (error) {
        success = false;
        details = error instanceof Error ? error.message : String(error);
    }

    const duration = now() - start;

    return {
        testName,
        duration,
        timestamp: Date.now(),
        success,
        details,
    };
}

/**
 * Test fresh fetch (bypassing all caches)
 */
async function benchmarkFreshFetch(adapterName: string): Promise<BenchmarkResult> {
    // Clear caches first
    networkCacheStore.invalidateAll();

    // Also invalidate Rust-side cache
    try {
        await invoke('invalidate_adapter_cache', { adapterName });
    } catch {
        // Ignore if command doesn't exist
    }

    return runTimedTest('Fresh Fetch (No Cache)', async () => {
        const config = await invoke<IPConfiguration>('get_ip_configuration_unified', {
            adapterName,
        });
        return config;
    });
}

/**
 * Test cache hit (from memory)
 */
async function benchmarkCacheHit(adapterName: string): Promise<BenchmarkResult> {
    // First, ensure data is in cache
    const config = await invoke<IPConfiguration>('get_ip_configuration_unified', {
        adapterName,
    });
    networkCacheStore.setCachedIPConfig(adapterName, config);

    // Now test cache hit speed
    return runTimedTest('Cache Hit (Memory)', () => {
        return networkCacheStore.getCachedIPConfig(adapterName);
    });
}

/**
 * Test localStorage load speed
 */
async function benchmarkLocalStorageLoad(): Promise<BenchmarkResult> {
    return runTimedTest('LocalStorage Load', () => {
        const stored = localStorage.getItem('network_cache_v1');
        if (stored) {
            return JSON.parse(stored);
        }
        return null;
    });
}

/**
 * Test adapter switching with prefetch
 */
async function benchmarkPrefetchSwitch(
    _fromAdapter: string,
    toAdapter: string
): Promise<{ withPrefetch: BenchmarkResult; withoutPrefetch: BenchmarkResult }> {
    // Test WITHOUT prefetch
    networkCacheStore.invalidateAll();
    try {
        await invoke('invalidate_all_network_cache');
    } catch {
        // Ignore
    }

    const withoutPrefetch = await runTimedTest('Switch WITHOUT Prefetch', async () => {
        const config = await invoke<IPConfiguration>('get_ip_configuration_unified', {
            adapterName: toAdapter,
        });
        return config;
    });

    // Test WITH prefetch (simulate prefetch then switch)
    networkCacheStore.invalidateAll();

    // Prefetch first
    const prefetchConfig = await invoke<IPConfiguration>('get_ip_configuration_unified', {
        adapterName: toAdapter,
    });
    networkCacheStore.setCachedIPConfig(toAdapter, prefetchConfig);

    // Now measure the "switch" which should be instant from cache
    const withPrefetch = await runTimedTest('Switch WITH Prefetch', () => {
        return networkCacheStore.getCachedIPConfig(toAdapter);
    });

    return { withPrefetch, withoutPrefetch };
}

/**
 * Run full benchmark suite
 */
export async function runFullBenchmark(adapterName: string, secondAdapter?: string): Promise<BenchmarkSummary> {
    console.log('🚀 Starting Network Loading Benchmark...\n');

    const results: BenchmarkResult[] = [];

    // 1. Fresh Fetch Test (run 3 times for average)
    console.log('📊 Testing Fresh Fetch...');
    const freshFetchResults: number[] = [];
    for (let i = 0; i < 3; i++) {
        const result = await benchmarkFreshFetch(adapterName);
        results.push({ ...result, testName: `${result.testName} #${i + 1}` });
        freshFetchResults.push(result.duration);
        console.log(`   Run ${i + 1}: ${formatDuration(result.duration)}`);
    }

    // 2. Cache Hit Test (run 5 times for average)
    console.log('\n📊 Testing Cache Hit...');
    const cacheHitResults: number[] = [];
    for (let i = 0; i < 5; i++) {
        const result = await benchmarkCacheHit(adapterName);
        results.push({ ...result, testName: `${result.testName} #${i + 1}` });
        cacheHitResults.push(result.duration);
        console.log(`   Run ${i + 1}: ${formatDuration(result.duration)}`);
    }

    // 3. LocalStorage Load Test
    console.log('\n📊 Testing LocalStorage Load...');
    const localStorageResults: number[] = [];
    for (let i = 0; i < 5; i++) {
        const result = await benchmarkLocalStorageLoad();
        results.push({ ...result, testName: `${result.testName} #${i + 1}` });
        localStorageResults.push(result.duration);
        console.log(`   Run ${i + 1}: ${formatDuration(result.duration)}`);
    }

    // 4. Prefetch Switch Test (if second adapter provided)
    if (secondAdapter) {
        console.log('\n📊 Testing Prefetch Switch...');
        const { withPrefetch, withoutPrefetch } = await benchmarkPrefetchSwitch(
            adapterName,
            secondAdapter
        );
        results.push(withPrefetch);
        results.push(withoutPrefetch);
        console.log(`   Without Prefetch: ${formatDuration(withoutPrefetch.duration)}`);
        console.log(`   With Prefetch: ${formatDuration(withPrefetch.duration)}`);
    }

    // Calculate averages
    const avgFreshFetch = freshFetchResults.reduce((a, b) => a + b, 0) / freshFetchResults.length;
    const avgCacheHit = cacheHitResults.reduce((a, b) => a + b, 0) / cacheHitResults.length;
    const avgLocalStorage = localStorageResults.reduce((a, b) => a + b, 0) / localStorageResults.length;

    // Calculate improvement percentages
    const cacheImprovement = ((avgFreshFetch - avgCacheHit) / avgFreshFetch * 100).toFixed(1);
    const localStorageImprovement = ((avgFreshFetch - avgLocalStorage) / avgFreshFetch * 100).toFixed(1);

    const summary: BenchmarkSummary = {
        results,
        averages: {
            freshFetch: avgFreshFetch,
            cacheHit: avgCacheHit,
            localStorageLoad: avgLocalStorage,
        },
        improvement: {
            cacheVsFresh: `${cacheImprovement}% faster`,
            localStorageVsFresh: `${localStorageImprovement}% faster`,
        },
        runAt: new Date().toISOString(),
    };

    // Log summary
    console.log('\n' + '='.repeat(50));
    console.log('📈 BENCHMARK SUMMARY');
    console.log('='.repeat(50));
    console.log(`\n⏱️  Average Times:`);
    console.log(`   Fresh Fetch:     ${formatDuration(avgFreshFetch)}`);
    console.log(`   Cache Hit:       ${formatDuration(avgCacheHit)}`);
    console.log(`   LocalStorage:    ${formatDuration(avgLocalStorage)}`);
    console.log(`\n🚀 Improvements:`);
    console.log(`   Cache vs Fresh:       ${summary.improvement.cacheVsFresh}`);
    console.log(`   LocalStorage vs Fresh: ${summary.improvement.localStorageVsFresh}`);
    console.log('='.repeat(50));

    // Save to localStorage for future reference
    localStorage.setItem(BENCHMARK_STORAGE_KEY, JSON.stringify(summary));

    return summary;
}

/**
 * Get last benchmark results
 */
export function getLastBenchmarkResults(): BenchmarkSummary | null {
    const stored = localStorage.getItem(BENCHMARK_STORAGE_KEY);
    if (stored) {
        return JSON.parse(stored);
    }
    return null;
}

/**
 * Quick benchmark (single run each)
 */
export async function runQuickBenchmark(adapterName: string): Promise<{
    freshFetch: string;
    cacheHit: string;
    speedup: string;
}> {
    // Fresh fetch
    const freshResult = await benchmarkFreshFetch(adapterName);

    // Cache hit
    const cacheResult = await benchmarkCacheHit(adapterName);

    const speedup = (freshResult.duration / cacheResult.duration).toFixed(0);

    return {
        freshFetch: formatDuration(freshResult.duration),
        cacheHit: formatDuration(cacheResult.duration),
        speedup: `${speedup}x faster`,
    };
}

// Export for use in browser console
if (typeof window !== 'undefined') {
    (window as any).networkBenchmark = {
        runFull: runFullBenchmark,
        runQuick: runQuickBenchmark,
        getLastResults: getLastBenchmarkResults,
    };
}

export default {
    runFullBenchmark,
    runQuickBenchmark,
    getLastBenchmarkResults,
};
