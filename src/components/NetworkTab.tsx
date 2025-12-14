/**
 * NetworkTab Component
 * 
 * Refactored with P1 optimizations:
 * - Uses useNetworkData hook with 150ms debouncing
 * - Shows NetworkConfigSkeleton during loading
 * - Integrates with cache for faster adapter switching
 * - Invalidates cache after apply operations
 * - Includes Force Refresh button
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Globe, RefreshCw, Loader2, ExternalLink, Terminal,
    Wifi, WifiOff, ArrowDownUp, Trash2, RotateCcw, BarChart3
} from 'lucide-react';
import toast from 'react-hot-toast';
import { Card } from './UI/Card';
import { Button } from './UI/Button';
import { NetworkConfigSkeleton, ConfigLoadingOverlay } from './UI/NetworkConfigSkeleton';
import { BenchmarkPanel } from './UI/BenchmarkPanel';
import { useNetworkData } from '../hooks/useNetworkData';
import { useNetworkCache } from '../hooks/useNetworkCache';
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
    invalidateAdapterCache,
} from '../lib/tauri';

export function NetworkTab() {
    // Use the optimized data hook with debouncing and caching
    const {
        adapters,
        currentConfig,
        loadState,
        error: configError,
        selectedAdapter,
        adaptersLoading,
        selectAdapter,
        refreshAdapters,
        invalidateCache,
        refetchConfig,
        prefetchAdapter,
    } = useNetworkData();

    // Get cache for manual invalidation
    const cache = useNetworkCache();

    const [output, setOutput] = useState('');
    const [isDHCP, setIsDHCP] = useState(true);
    const [saving, setSaving] = useState(false);
    const [showBenchmark, setShowBenchmark] = useState(false);

    // Form state for static IP
    const [formData, setFormData] = useState({
        ip_address: '',
        subnet_mask: '255.255.255.0',
        gateway: '',
        primary_dns: '8.8.8.8',
        secondary_dns: '8.8.4.4',
    });

    // Update form when config loads
    useEffect(() => {
        if (currentConfig) {
            setIsDHCP(currentConfig.dhcp_enabled);
            setFormData({
                ip_address: currentConfig.ip_address || '',
                subnet_mask: currentConfig.subnet_mask || '255.255.255.0',
                gateway: currentConfig.gateway || '',
                primary_dns: currentConfig.primary_dns || '8.8.8.8',
                secondary_dns: currentConfig.secondary_dns || '8.8.4.4',
            });
        }
    }, [currentConfig]);

    // Show error toast when config fails
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

            // Invalidate both React-side and Rust-side cache after applying changes
            cache.invalidateAdapter(selectedAdapter);
            await invalidateAdapterCache(selectedAdapter);

            // Refetch to get new config
            await refetchConfig();

        } catch (error) {
            toast.error(`${error}`);
        } finally {
            setSaving(false);
        }
    };

    const handleForceRefresh = async () => {
        // Invalidate all caches and reload
        invalidateCache();
        toast.success('Cache cleared, refreshing...');
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
                    // Invalidate cache after IP release
                    cache.invalidateAll();
                    break;
                case 'renew':
                    result = await renewIP();
                    toast.success('IP Renewed');
                    // Invalidate cache after IP renew and reload
                    cache.invalidateAll();
                    await refetchConfig();
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

    // Show loading state for initial adapter load
    if (adaptersLoading) {
        return (
            <div className="flex items-center justify-center h-full">
                <Loader2 className="w-8 h-8 text-primary animate-spin" />
                <span className="ml-3 text-gray-400">Loading network adapters...</span>
            </div>
        );
    }

    return (
        <>
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
                        <Button variant="secondary" onClick={() => setShowBenchmark(true)} title="Run performance benchmark">
                            <BarChart3 className="w-4 h-4" />
                        </Button>
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
                                onChange={(e) => selectAdapter(e.target.value)}
                                onFocus={() => {
                                    // Prefetch all adapters when dropdown is focused
                                    adapters.forEach(adapter => {
                                        if (adapter.name !== selectedAdapter) {
                                            prefetchAdapter(adapter.name);
                                        }
                                    });
                                }}
                                className="flex-1 px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-primary truncate pr-8"
                                style={{ textOverflow: 'ellipsis' }}
                            >
                                {adapters.map((adapter) => (
                                    <option key={adapter.name} value={adapter.name} className="bg-slate-800">
                                        {adapter.status === 'Up' ? '🟢' : '🔴'} {adapter.name} - {adapter.description}
                                    </option>
                                ))}
                            </select>
                            <Button variant="secondary" onClick={refreshAdapters} title="Refresh adapter list">
                                <RefreshCw className="w-4 h-4" />
                            </Button>
                            <Button variant="secondary" onClick={handleForceRefresh} title="Force refresh (clear cache)">
                                <RotateCcw className="w-4 h-4" />
                            </Button>
                        </div>
                    </div>
                </Card>

                {/* IP Configuration */}
                <Card title="IP Configuration" className="relative overflow-hidden">
                    {/* Loading overlay for adapter switching */}
                    <AnimatePresence mode="wait">
                        {loadState === 'loading' && currentConfig && (
                            <ConfigLoadingOverlay key="loading-overlay" />
                        )}
                    </AnimatePresence>

                    {/* Show skeleton only on initial load (no cached data) */}
                    {loadState === 'loading' && !currentConfig ? (
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

            {/* Benchmark Panel */}
            <BenchmarkPanel
                isOpen={showBenchmark}
                onClose={() => setShowBenchmark(false)}
            />
        </>
    );
}
