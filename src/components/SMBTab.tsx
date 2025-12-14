import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Shield, AlertTriangle, RefreshCw, RotateCcw, Loader2, Folder, FolderOpen, ChevronUp, Settings } from 'lucide-react';
import toast from 'react-hot-toast';
import { Card } from './UI/Card';
import { ToggleSwitch } from './UI/ToggleSwitch';
import { Button } from './UI/Button';
import {
    getSMBSettings,
    setSMBGuestAuth,
    setSMBClientSignature,
    setSMBServerSignature,
    resetSMBSettings,
    restartSMBService,
    testSMBConnection,
    listSMBShares,
    openSmbPath,
    openAdvancedSharing,
    type SMBSettings,
    type SmbShare
} from '../lib/tauri';

// IP/Hostname validation function
const isValidIpOrHostname = (value: string): boolean => {
    const trimmed = value.trim();
    if (!trimmed) return false;

    // Check if it looks like an IP (contains only numbers and dots)
    const looksLikeIp = /^[\d.]+$/.test(trimmed);

    if (looksLikeIp) {
        // Must be a complete IPv4: exactly 4 octets separated by 3 dots
        const ipv4Regex = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/;
        const match = trimmed.match(ipv4Regex);
        if (!match) return false; // Incomplete IP like "192.16" fails here

        // Verify each octet is 0-255
        const octets = [match[1], match[2], match[3], match[4]].map(Number);
        return octets.every(o => o >= 0 && o <= 255);
    }

    // Valid hostname check (must start with a letter, not a number)
    // This prevents "192.16" from being treated as a hostname
    const hostnameRegex = /^[a-zA-Z][a-zA-Z0-9-]*(\.[a-zA-Z][a-zA-Z0-9-]*)*$/;
    return hostnameRegex.test(trimmed);
};

// Get validation error message for IP/hostname
const getValidationError = (value: string): string | null => {
    const trimmed = value.trim();
    if (!trimmed) return 'Please enter a hostname or IP address';

    // Check if it looks like an incomplete IP (ends with dot or has incomplete octets)
    if (/^\d+\.$/.test(trimmed) || /^\d+\.\d+\.$/.test(trimmed) || /^\d+\.\d+\.\d+\.$/.test(trimmed)) {
        return `Host "${trimmed}" is unreachable - incomplete IP address`;
    }

    // Check if it looks like an IP but invalid format
    if (/^[\d.]+$/.test(trimmed)) {
        const parts = trimmed.split('.');
        if (parts.length !== 4) {
            return `Host "${trimmed}" is unreachable - invalid IP format (expected xxx.xxx.xxx.xxx)`;
        }
        const invalidOctet = parts.find(p => {
            const num = Number(p);
            return isNaN(num) || num < 0 || num > 255;
        });
        if (invalidOctet !== undefined) {
            return `Host "${trimmed}" is unreachable - IP octet out of range (0-255)`;
        }
    }

    // General invalid format
    if (!isValidIpOrHostname(trimmed)) {
        return `Host "${trimmed}" is unreachable - invalid hostname or IP format`;
    }

    return null;
};

export function SMBTab() {
    const [settings, setSettings] = useState<SMBSettings | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState<string | null>(null);
    const [restarting, setRestarting] = useState(false);

    // Connection Test State
    const [testHost, setTestHost] = useState('');
    const [testUser, setTestUser] = useState('');
    const [testPass, setTestPass] = useState('');
    const [testing, setTesting] = useState(false);
    const [shares, setShares] = useState<SmbShare[]>([]);
    const [listingShares, setListingShares] = useState(false);
    const [openingShare, setOpeningShare] = useState<string | null>(null);

    // Connection test success tracking
    const [connectionTested, setConnectionTested] = useState(false);

    // Open in Explorer State
    const [openingExplorer, setOpeningExplorer] = useState(false);

    // Derived validation state
    const isHostValid = isValidIpOrHostname(testHost);
    const validationError = getValidationError(testHost);

    // Load settings on mount
    useEffect(() => {
        loadSettings();
    }, []);

    const loadSettings = async () => {
        try {
            setLoading(true);
            const data = await getSMBSettings();
            setSettings(data);
        } catch (error) {
            console.error('Failed to load settings:', error);
            toast.error(`Failed to load settings: ${error}`);
        } finally {
            setLoading(false);
        }
    };

    const handleGuestAuthToggle = async (enabled: boolean) => {
        if (!settings) return;

        try {
            setSaving('guestAuth');
            const message = await setSMBGuestAuth(enabled);
            setSettings(prev => prev ? { ...prev, guest_auth_enabled: enabled } : null);
            toast.success(message);
        } catch (error) {
            toast.error(`${error}`);
        } finally {
            setSaving(null);
        }
    };

    const handleClientSignatureToggle = async (enabled: boolean) => {
        if (!settings) return;

        try {
            setSaving('clientSig');
            const message = await setSMBClientSignature(enabled);
            setSettings(prev => prev ? { ...prev, client_signature_required: enabled } : null);
            toast.success(message);
        } catch (error) {
            toast.error(`${error}`);
        } finally {
            setSaving(null);
        }
    };

    const handleServerSignatureToggle = async (enabled: boolean) => {
        if (!settings) return;

        try {
            setSaving('serverSig');
            const message = await setSMBServerSignature(enabled);
            setSettings(prev => prev ? { ...prev, server_signature_required: enabled } : null);
            toast.success(message);
        } catch (error) {
            toast.error(`${error}`);
        } finally {
            setSaving(null);
        }
    };

    const handleReset = async () => {
        try {
            setSaving('reset');
            const message = await resetSMBSettings();
            await loadSettings(); // Reload settings
            toast.success(message);
        } catch (error) {
            toast.error(`${error}`);
        } finally {
            setSaving(null);
        }
    };

    const handleRestart = async () => {
        if (!confirm('Restart SMB services? This may disconnect active network shares.')) {
            return;
        }

        try {
            setRestarting(true);
            const message = await restartSMBService();
            toast.success(message);
        } catch (error) {
            toast.error(`${error}`);
        } finally {
            setRestarting(false);
        }
    };

    const handleTestConnection = async () => {
        if (!testHost) {
            toast.error('Please enter a Hostname or IP');
            return;
        }

        // Validate format before testing
        if (!isHostValid) {
            toast.error(validationError || 'Invalid hostname or IP format');
            return;
        }

        try {
            setTesting(true);
            setConnectionTested(false);
            const msg = await testSMBConnection(testHost);
            setConnectionTested(true);
            toast.success(msg);
        } catch (error) {
            setConnectionTested(false);
            toast.error(`${error}`);
        } finally {
            setTesting(false);
        }
    };

    // Reset connection tested state when host changes
    const handleHostChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setTestHost(e.target.value);
        setConnectionTested(false);
    };

    const handleListShares = async () => {
        // If shares are already visible, hide them (toggle behavior)
        if (shares.length > 0) {
            setShares([]);
            return;
        }

        if (!testHost) {
            toast.error('Please enter a Hostname or IP');
            return;
        }

        try {
            setListingShares(true);
            const data = await listSMBShares(testHost, testUser || undefined, testPass || undefined);
            setShares(data);
            if (data.length === 0) {
                toast('No shares found or access denied', { icon: 'ℹ️' });
            }
        } catch (error) {
            toast.error(`${error}`);
            setShares([]);
        } finally {
            setListingShares(false);
        }
    };

    const handleOpenInExplorer = async () => {
        if (!testHost.trim()) {
            toast.error('Please enter a hostname or IP address');
            return;
        }

        // Check for valid format
        if (!isHostValid) {
            toast.error(validationError || `Host "${testHost.trim()}" is unreachable - invalid format`);
            return;
        }

        try {
            setOpeningExplorer(true);
            await openSmbPath(testHost.trim(), undefined);
            toast.success(`Opened \\\\${testHost.trim()} in Explorer`);
        } catch (error) {
            toast.error(`${error}`);
        } finally {
            setOpeningExplorer(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <Loader2 className="w-8 h-8 text-primary animate-spin" />
                <span className="ml-3 text-gray-400">Loading SMB settings...</span>
            </div>
        );
    }

    if (!settings) {
        return (
            <div className="flex flex-col items-center justify-center h-full text-gray-400">
                <AlertTriangle className="w-16 h-16 mb-4" />
                <p>Failed to load SMB settings</p>
                <Button variant="secondary" onClick={loadSettings} className="mt-4">
                    Retry
                </Button>
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
                    <Shield className="w-8 h-8 text-primary" />
                    <h2 className="text-2xl font-bold text-white">SMB Configuration</h2>
                </div>
                <Button
                    variant="secondary"
                    onClick={() => openAdvancedSharing()}
                    title="Open Windows Advanced Sharing Settings"
                >
                    <Settings className="w-4 h-4" />
                    Advanced Sharing
                </Button>
            </div>

            {/* Settings Card */}
            <Card title="Security Settings">
                <div className="space-y-4">
                    {/* Guest Auth Toggle */}
                    <div className="setting-row">
                        <div className="setting-info">
                            <div className="flex items-center gap-2">
                                <span className="setting-title">Insecure Guest Logons</span>
                                {settings.guest_auth_enabled && (
                                    <AlertTriangle className="w-5 h-5 text-amber-500" />
                                )}
                            </div>
                            <p className="setting-description">
                                Allow guest authentication for SMB shares (not recommended for security)
                            </p>
                        </div>
                        <ToggleSwitch
                            checked={settings.guest_auth_enabled}
                            onChange={handleGuestAuthToggle}
                            disabled={saving === 'guestAuth'}
                        />
                    </div>

                    <div className="border-t border-white/10" />

                    {/* Client Signature Toggle */}
                    <div className="setting-row">
                        <div className="setting-info">
                            <span className="setting-title">Client Security Signature</span>
                            <p className="setting-description">
                                Require digital signature for SMB client connections
                            </p>
                        </div>
                        <ToggleSwitch
                            checked={settings.client_signature_required}
                            onChange={handleClientSignatureToggle}
                            disabled={saving === 'clientSig'}
                        />
                    </div>

                    <div className="border-t border-white/10" />

                    {/* Server Signature Toggle */}
                    <div className="setting-row">
                        <div className="setting-info">
                            <span className="setting-title">Server Security Signature</span>
                            <p className="setting-description">
                                Require digital signature for SMB server connections
                            </p>
                        </div>
                        <ToggleSwitch
                            checked={settings.server_signature_required}
                            onChange={handleServerSignatureToggle}
                            disabled={saving === 'serverSig'}
                        />
                    </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-3 mt-6">
                    <Button
                        variant="primary"
                        onClick={handleReset}
                        disabled={saving === 'reset'}
                        icon={saving === 'reset' ? <Loader2 className="w-4 h-4 animate-spin" /> : <RotateCcw className="w-4 h-4" />}
                    >
                        Reset to Default
                    </Button>
                    <Button
                        variant="secondary"
                        onClick={handleRestart}
                        disabled={restarting}
                        icon={restarting ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                    >
                        Restart SMB Service
                    </Button>
                </div>
            </Card>

            {/* Connection Test & Mapping */}
            <Card title="Connection & Mapping">
                <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="md:col-span-2">
                            <label className="block text-sm text-gray-400 mb-1">Hostname / IP</label>
                            <input
                                type="text"
                                value={testHost}
                                onChange={handleHostChange}
                                placeholder="192.168.1.10"
                                className={`input-field ${testHost && !isHostValid ? 'border-red-500/50 focus:border-red-500' : ''}`}
                            />
                            {testHost && !isHostValid && (
                                <p className="text-xs text-red-400 mt-1">{validationError}</p>
                            )}
                            {testHost && isHostValid && connectionTested && (
                                <p className="text-xs text-green-400 mt-1">✓ Connection tested successfully</p>
                            )}
                        </div>
                        <div className="flex items-end">
                            <Button
                                variant="primary"
                                onClick={handleTestConnection}
                                loading={testing}
                                className="w-full"
                            >
                                Test Connection
                            </Button>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm text-gray-400 mb-1">Username (Optional)</label>
                            <input
                                type="text"
                                value={testUser}
                                onChange={(e) => setTestUser(e.target.value)}
                                placeholder="user"
                                className="input-field"
                            />
                        </div>
                        <div>
                            <label className="block text-sm text-gray-400 mb-1">Password (Optional)</label>
                            <input
                                type="password"
                                value={testPass}
                                onChange={(e) => setTestPass(e.target.value)}
                                placeholder="password"
                                className="input-field"
                            />
                        </div>
                    </div>

                    <div className="flex flex-wrap gap-2 justify-end">
                        <Button
                            variant="secondary"
                            onClick={handleListShares}
                            loading={listingShares}
                            icon={shares.length > 0 ? <ChevronUp className="w-4 h-4" /> : <Folder className="w-4 h-4" />}
                        >
                            {shares.length > 0 ? 'Hide Shares' : 'List Shares'}
                        </Button>
                        <Button
                            variant="secondary"
                            onClick={handleOpenInExplorer}
                            loading={openingExplorer}
                            disabled={!testHost.trim() || !isHostValid}
                            icon={<FolderOpen className="w-4 h-4" />}
                            title={
                                !testHost.trim()
                                    ? "Enter a hostname or IP first"
                                    : !isHostValid
                                        ? validationError || "Invalid hostname or IP format"
                                        : connectionTested
                                            ? "Open in Windows Explorer (connection verified)"
                                            : "Open in Windows Explorer"
                            }
                            className={(!testHost.trim() || !isHostValid) ? 'opacity-50 cursor-not-allowed' : ''}
                        >
                            Open in Explorer
                        </Button>
                    </div>

                    {/* Shares List */}
                    {shares.length > 0 && (
                        <div className="mt-4 p-4 bg-black/20 rounded-xl border border-white/5">
                            <h4 className="text-sm font-semibold text-gray-300 mb-2">Available Shares:</h4>
                            <ul className="space-y-2">
                                {shares.map((share, idx) => (
                                    <li key={idx} className="flex items-center justify-between p-2 bg-white/5 rounded-lg hover:bg-white/10">
                                        <div className="flex items-center gap-3">
                                            <Folder className="w-4 h-4 text-primary" />
                                            <div>
                                                <div className="text-sm font-medium text-white">{share.name}</div>
                                                <div className="text-xs text-gray-400">{share.path}</div>
                                            </div>
                                        </div>
                                        <Button
                                            variant="secondary"
                                            className="py-1! px-3! text-xs!"
                                            icon={openingShare === share.name ? <Loader2 className="w-3 h-3 animate-spin" /> : <FolderOpen className="w-3 h-3" />}
                                            disabled={openingShare === share.name}
                                            onClick={async (e) => {
                                                e.stopPropagation();
                                                try {
                                                    setOpeningShare(share.name);
                                                    await openSmbPath(testHost, share.name);
                                                    toast.success(`Opened \\\\${testHost}\\${share.name} in Explorer`);
                                                } catch (error) {
                                                    toast.error(`${error}`);
                                                } finally {
                                                    setOpeningShare(null);
                                                }
                                            }}
                                        >
                                            Open
                                        </Button>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                </div>
            </Card>

            {/* Info Card */}
            <Card className="bg-blue-500/10! border-blue-500/30!">
                <div className="flex items-start gap-3">
                    <Shield className="w-5 h-5 text-blue-400 mt-0.5" />
                    <div>
                        <p className="text-sm text-blue-200">
                            <strong>Note:</strong> Changes to SMB settings take effect immediately.
                            Some changes may require restarting SMB services or reconnecting to network shares.
                        </p>
                    </div>
                </div>
            </Card>
        </motion.div>
    );
}
