/**
 * Benchmark Panel Component
 * 
 * Displays network loading performance benchmarks
 * Can be toggled on demand to run and visualize results
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BarChart3, Play, Clock, Zap, Database, HardDrive, X, RefreshCw } from 'lucide-react';
import { Button } from './Button';
import { runFullBenchmark, runQuickBenchmark, getLastBenchmarkResults, type BenchmarkSummary } from '../../lib/benchmark';
import { useNetworkAdapters } from '../../hooks/useNetworkData';

interface BenchmarkPanelProps {
    isOpen: boolean;
    onClose: () => void;
}

export function BenchmarkPanel({ isOpen, onClose }: BenchmarkPanelProps) {
    const [isRunning, setIsRunning] = useState(false);
    const [results, setResults] = useState<BenchmarkSummary | null>(null);
    const [quickResults, setQuickResults] = useState<{
        freshFetch: string;
        cacheHit: string;
        speedup: string;
    } | null>(null);
    const { adapters } = useNetworkAdapters();

    // Load last results on mount
    useEffect(() => {
        const lastResults = getLastBenchmarkResults();
        if (lastResults) {
            setResults(lastResults);
        }
    }, []);

    const handleRunQuickBenchmark = async () => {
        if (adapters.length === 0) return;

        setIsRunning(true);
        try {
            const result = await runQuickBenchmark(adapters[0].name);
            setQuickResults(result);
        } catch (error) {
            console.error('Benchmark failed:', error);
        } finally {
            setIsRunning(false);
        }
    };

    const handleRunFullBenchmark = async () => {
        if (adapters.length === 0) return;

        setIsRunning(true);
        try {
            const secondAdapter = adapters.length > 1 ? adapters[1].name : undefined;
            const result = await runFullBenchmark(adapters[0].name, secondAdapter);
            setResults(result);
        } catch (error) {
            console.error('Benchmark failed:', error);
        } finally {
            setIsRunning(false);
        }
    };

    const formatTime = (ms: number): string => {
        if (ms < 1) {
            return `${(ms * 1000).toFixed(1)}μs`;
        }
        if (ms < 1000) {
            return `${ms.toFixed(1)}ms`;
        }
        return `${(ms / 1000).toFixed(2)}s`;
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                    onClick={onClose}
                >
                    <motion.div
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0.9, opacity: 0 }}
                        className="bg-slate-900 border border-white/10 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden"
                        onClick={(e) => e.stopPropagation()}
                    >
                        {/* Header */}
                        <div className="flex items-center justify-between p-4 border-b border-white/10">
                            <div className="flex items-center gap-3">
                                <BarChart3 className="w-6 h-6 text-primary" />
                                <h2 className="text-xl font-bold text-white">Network Loading Benchmark</h2>
                            </div>
                            <button
                                onClick={onClose}
                                className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                            >
                                <X className="w-5 h-5 text-gray-400" />
                            </button>
                        </div>

                        {/* Content */}
                        <div className="p-4 space-y-4 overflow-y-auto max-h-[60vh]">
                            {/* Quick Benchmark */}
                            <div className="bg-white/5 rounded-xl p-4">
                                <div className="flex items-center justify-between mb-3">
                                    <h3 className="text-white font-semibold flex items-center gap-2">
                                        <Zap className="w-4 h-4 text-yellow-400" />
                                        Quick Benchmark
                                    </h3>
                                    <Button
                                        variant="secondary"
                                        onClick={handleRunQuickBenchmark}
                                        loading={isRunning}
                                        className="text-sm"
                                    >
                                        <Play className="w-4 h-4" />
                                        Run
                                    </Button>
                                </div>

                                {quickResults && (
                                    <div className="grid grid-cols-3 gap-3 mt-3">
                                        <div className="bg-red-500/10 rounded-lg p-3 text-center">
                                            <Clock className="w-5 h-5 text-red-400 mx-auto mb-1" />
                                            <div className="text-xs text-gray-400">Fresh Fetch</div>
                                            <div className="text-lg font-bold text-red-400">{quickResults.freshFetch}</div>
                                        </div>
                                        <div className="bg-green-500/10 rounded-lg p-3 text-center">
                                            <Database className="w-5 h-5 text-green-400 mx-auto mb-1" />
                                            <div className="text-xs text-gray-400">Cache Hit</div>
                                            <div className="text-lg font-bold text-green-400">{quickResults.cacheHit}</div>
                                        </div>
                                        <div className="bg-primary/10 rounded-lg p-3 text-center">
                                            <Zap className="w-5 h-5 text-primary mx-auto mb-1" />
                                            <div className="text-xs text-gray-400">Speedup</div>
                                            <div className="text-lg font-bold text-primary">{quickResults.speedup}</div>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Full Benchmark */}
                            <div className="bg-white/5 rounded-xl p-4">
                                <div className="flex items-center justify-between mb-3">
                                    <h3 className="text-white font-semibold flex items-center gap-2">
                                        <BarChart3 className="w-4 h-4 text-blue-400" />
                                        Full Benchmark
                                    </h3>
                                    <Button
                                        variant="secondary"
                                        onClick={handleRunFullBenchmark}
                                        loading={isRunning}
                                        className="text-sm"
                                    >
                                        <RefreshCw className="w-4 h-4" />
                                        Run Full Test
                                    </Button>
                                </div>

                                {results && (
                                    <div className="space-y-4 mt-3">
                                        {/* Averages */}
                                        <div className="grid grid-cols-3 gap-3">
                                            <div className="bg-red-500/10 rounded-lg p-3">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <Clock className="w-4 h-4 text-red-400" />
                                                    <span className="text-xs text-gray-400">Fresh Fetch</span>
                                                </div>
                                                <div className="text-xl font-bold text-red-400">
                                                    {formatTime(results.averages.freshFetch)}
                                                </div>
                                                <div className="text-xs text-gray-500">avg of 3 runs</div>
                                            </div>
                                            <div className="bg-green-500/10 rounded-lg p-3">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <Database className="w-4 h-4 text-green-400" />
                                                    <span className="text-xs text-gray-400">Cache Hit</span>
                                                </div>
                                                <div className="text-xl font-bold text-green-400">
                                                    {formatTime(results.averages.cacheHit)}
                                                </div>
                                                <div className="text-xs text-gray-500">avg of 5 runs</div>
                                            </div>
                                            <div className="bg-blue-500/10 rounded-lg p-3">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <HardDrive className="w-4 h-4 text-blue-400" />
                                                    <span className="text-xs text-gray-400">LocalStorage</span>
                                                </div>
                                                <div className="text-xl font-bold text-blue-400">
                                                    {formatTime(results.averages.localStorageLoad)}
                                                </div>
                                                <div className="text-xs text-gray-500">avg of 5 runs</div>
                                            </div>
                                        </div>

                                        {/* Improvements */}
                                        <div className="bg-gradient-to-r from-green-500/20 to-blue-500/20 rounded-lg p-4">
                                            <h4 className="text-white font-semibold mb-3 flex items-center gap-2">
                                                <Zap className="w-4 h-4 text-yellow-400" />
                                                Performance Improvements
                                            </h4>
                                            <div className="space-y-2">
                                                <div className="flex justify-between items-center">
                                                    <span className="text-gray-300">Cache vs Fresh Fetch:</span>
                                                    <span className="text-green-400 font-bold">{results.improvement.cacheVsFresh}</span>
                                                </div>
                                                <div className="flex justify-between items-center">
                                                    <span className="text-gray-300">LocalStorage vs Fresh:</span>
                                                    <span className="text-blue-400 font-bold">{results.improvement.localStorageVsFresh}</span>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Visual Bar Chart */}
                                        <div className="space-y-2">
                                            <h4 className="text-sm text-gray-400">Comparison (lower is better)</h4>
                                            <div className="space-y-2">
                                                {/* Fresh Fetch Bar */}
                                                <div className="flex items-center gap-2">
                                                    <span className="text-xs text-gray-400 w-20">Fresh</span>
                                                    <div className="flex-1 h-6 bg-white/5 rounded overflow-hidden">
                                                        <motion.div
                                                            initial={{ width: 0 }}
                                                            animate={{ width: '100%' }}
                                                            className="h-full bg-red-500/50"
                                                        />
                                                    </div>
                                                    <span className="text-xs text-gray-400 w-16 text-right">
                                                        {formatTime(results.averages.freshFetch)}
                                                    </span>
                                                </div>
                                                {/* Cache Hit Bar */}
                                                <div className="flex items-center gap-2">
                                                    <span className="text-xs text-gray-400 w-20">Cache</span>
                                                    <div className="flex-1 h-6 bg-white/5 rounded overflow-hidden">
                                                        <motion.div
                                                            initial={{ width: 0 }}
                                                            animate={{
                                                                width: `${Math.max(1, (results.averages.cacheHit / results.averages.freshFetch) * 100)}%`
                                                            }}
                                                            className="h-full bg-green-500/50"
                                                        />
                                                    </div>
                                                    <span className="text-xs text-gray-400 w-16 text-right">
                                                        {formatTime(results.averages.cacheHit)}
                                                    </span>
                                                </div>
                                                {/* LocalStorage Bar */}
                                                <div className="flex items-center gap-2">
                                                    <span className="text-xs text-gray-400 w-20">Storage</span>
                                                    <div className="flex-1 h-6 bg-white/5 rounded overflow-hidden">
                                                        <motion.div
                                                            initial={{ width: 0 }}
                                                            animate={{
                                                                width: `${Math.max(1, (results.averages.localStorageLoad / results.averages.freshFetch) * 100)}%`
                                                            }}
                                                            className="h-full bg-blue-500/50"
                                                        />
                                                    </div>
                                                    <span className="text-xs text-gray-400 w-16 text-right">
                                                        {formatTime(results.averages.localStorageLoad)}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Last Run */}
                                        <div className="text-xs text-gray-500 text-center">
                                            Last run: {new Date(results.runAt).toLocaleString()}
                                        </div>
                                    </div>
                                )}

                                {!results && !isRunning && (
                                    <div className="text-center text-gray-500 py-8">
                                        <BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-30" />
                                        <p>Click "Run Full Test" to see detailed performance metrics</p>
                                    </div>
                                )}

                                {isRunning && (
                                    <div className="text-center py-8">
                                        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                                        <p className="text-gray-400">Running benchmark...</p>
                                        <p className="text-xs text-gray-500">Check console for progress</p>
                                    </div>
                                )}
                            </div>

                            {/* Info */}
                            <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-4">
                                <h4 className="text-yellow-400 font-semibold mb-2">💡 What does this measure?</h4>
                                <ul className="text-sm text-gray-300 space-y-1">
                                    <li><strong>Fresh Fetch:</strong> Time to fetch from Rust/PowerShell (no cache)</li>
                                    <li><strong>Cache Hit:</strong> Time to retrieve from in-memory cache</li>
                                    <li><strong>LocalStorage:</strong> Time to load from persistent storage</li>
                                </ul>
                            </div>
                        </div>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}

export default BenchmarkPanel;
