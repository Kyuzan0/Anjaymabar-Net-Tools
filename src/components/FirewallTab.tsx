import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
    Shield, ShieldCheck, ShieldOff, ExternalLink, Loader2,
    AlertTriangle, RefreshCw
} from 'lucide-react';
import toast from 'react-hot-toast';
import { Card } from './UI/Card';
import { Button } from './UI/Button';
import { ToggleSwitch } from './UI/ToggleSwitch';
import {
    getFirewallStatus,
    setFirewallProfile,
    enableAllFirewall,
    disableAllFirewall,
    openFirewallSettings,
    openAdvancedFirewall,
    type FirewallStatus,
} from '../lib/tauri';

export function FirewallTab() {
    const [status, setStatus] = useState<FirewallStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState<string | null>(null);

    useEffect(() => {
        loadStatus();
    }, []);

    const loadStatus = async () => {
        try {
            setLoading(true);
            const data = await getFirewallStatus();
            setStatus(data);
        } catch (error) {
            toast.error(`Failed to load firewall status: ${error}`);
        } finally {
            setLoading(false);
        }
    };

    const handleProfileToggle = async (profile: 'Domain' | 'Private' | 'Public', enabled: boolean) => {
        if (!enabled) {
            const confirm = window.confirm(
                `Are you sure you want to disable the ${profile} firewall profile?\n\nThis may expose your system to security threats.`
            );
            if (!confirm) return;
        }

        try {
            setSaving(profile);
            const msg = await setFirewallProfile(profile, enabled);
            setStatus((prev) => {
                if (!prev) return prev;
                return {
                    ...prev,
                    [profile.toLowerCase()]: enabled,
                };
            });
            toast.success(msg);
        } catch (error) {
            toast.error(`${error}`);
        } finally {
            setSaving(null);
        }
    };

    const handleEnableAll = async () => {
        try {
            setSaving('all');
            const msg = await enableAllFirewall();
            setStatus({ domain: true, private: true, public: true });
            toast.success(msg);
        } catch (error) {
            toast.error(`${error}`);
        } finally {
            setSaving(null);
        }
    };

    const handleDisableAll = async () => {
        const confirm = window.confirm(
            'Are you sure you want to disable ALL firewall profiles?\n\n⚠️ This will expose your system to potential security threats!'
        );
        if (!confirm) return;

        try {
            setSaving('all');
            const msg = await disableAllFirewall();
            setStatus({ domain: false, private: false, public: false });
            toast.success(msg);
        } catch (error) {
            toast.error(`${error}`);
        } finally {
            setSaving(null);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <Loader2 className="w-8 h-8 text-primary animate-spin" />
                <span className="ml-3 text-gray-400">Loading firewall status...</span>
            </div>
        );
    }

    const allEnabled = status?.domain && status?.private && status?.public;
    const allDisabled = !status?.domain && !status?.private && !status?.public;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-6 space-y-6"
        >
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <Shield className="w-8 h-8 text-primary" />
                    <h2 className="text-2xl font-bold text-white">Firewall Settings</h2>
                </div>
                <div className="flex gap-2">
                    <Button variant="secondary" onClick={() => openFirewallSettings()}>
                        <ExternalLink className="w-4 h-4" />
                        firewall.cpl
                    </Button>
                    <Button variant="secondary" onClick={() => openAdvancedFirewall()}>
                        <ExternalLink className="w-4 h-4" />
                        Advanced
                    </Button>
                </div>
            </div>

            {/* Quick Toggle */}
            <Card>
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                        {allEnabled ? (
                            <ShieldCheck className="w-6 h-6 text-green-500" />
                        ) : allDisabled ? (
                            <ShieldOff className="w-6 h-6 text-red-500" />
                        ) : (
                            <AlertTriangle className="w-6 h-6 text-amber-500" />
                        )}
                        <span className="text-lg font-semibold text-white">
                            Quick Toggle (All Profiles)
                        </span>
                    </div>
                    <Button variant="secondary" onClick={loadStatus}>
                        <RefreshCw className="w-4 h-4" />
                    </Button>
                </div>

                <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl mb-4">
                    <div className="flex items-center gap-2 text-amber-400">
                        <AlertTriangle className="w-5 h-5" />
                        <span className="text-sm font-semibold">
                            Warning: Disabling firewall may expose your system to security risks!
                        </span>
                    </div>
                </div>

                <div className="flex gap-4">
                    <Button
                        variant="primary"
                        onClick={handleEnableAll}
                        loading={saving === 'all'}
                        className="!bg-green-600 hover:!bg-green-700 flex-1"
                    >
                        <ShieldCheck className="w-5 h-5" />
                        Enable All Profiles
                    </Button>
                    <Button
                        variant="secondary"
                        onClick={handleDisableAll}
                        loading={saving === 'all'}
                        className="!bg-red-600/20 !border-red-500/30 hover:!bg-red-600/40 flex-1"
                    >
                        <ShieldOff className="w-5 h-5" />
                        Disable All Profiles
                    </Button>
                </div>
            </Card>

            {/* Individual Profiles */}
            <Card title="Individual Profile Control">
                <div className="space-y-4">
                    {/* Domain Profile */}
                    <div className="setting-row">
                        <div className="setting-info">
                            <div className="flex items-center gap-2">
                                <span className="setting-title">Domain Profile</span>
                                {status?.domain ? (
                                    <span className="px-2 py-0.5 text-xs bg-green-500/20 text-green-400 rounded-full">
                                        Enabled
                                    </span>
                                ) : (
                                    <span className="px-2 py-0.5 text-xs bg-red-500/20 text-red-400 rounded-full">
                                        Disabled
                                    </span>
                                )}
                            </div>
                            <p className="setting-description">
                                Used when your computer is connected to a corporate domain network
                            </p>
                        </div>
                        <ToggleSwitch
                            checked={status?.domain ?? false}
                            onChange={(enabled) => handleProfileToggle('Domain', enabled)}
                            disabled={saving === 'Domain'}
                        />
                    </div>

                    <div className="border-t border-white/10" />

                    {/* Private Profile */}
                    <div className="setting-row">
                        <div className="setting-info">
                            <div className="flex items-center gap-2">
                                <span className="setting-title">Private Profile</span>
                                {status?.private ? (
                                    <span className="px-2 py-0.5 text-xs bg-green-500/20 text-green-400 rounded-full">
                                        Enabled
                                    </span>
                                ) : (
                                    <span className="px-2 py-0.5 text-xs bg-red-500/20 text-red-400 rounded-full">
                                        Disabled
                                    </span>
                                )}
                            </div>
                            <p className="setting-description">
                                Used when connected to a trusted private network (home, work)
                            </p>
                        </div>
                        <ToggleSwitch
                            checked={status?.private ?? false}
                            onChange={(enabled) => handleProfileToggle('Private', enabled)}
                            disabled={saving === 'Private'}
                        />
                    </div>

                    <div className="border-t border-white/10" />

                    {/* Public Profile */}
                    <div className="setting-row">
                        <div className="setting-info">
                            <div className="flex items-center gap-2">
                                <span className="setting-title">Public Profile</span>
                                {status?.public ? (
                                    <span className="px-2 py-0.5 text-xs bg-green-500/20 text-green-400 rounded-full">
                                        Enabled
                                    </span>
                                ) : (
                                    <span className="px-2 py-0.5 text-xs bg-red-500/20 text-red-400 rounded-full">
                                        Disabled
                                    </span>
                                )}
                            </div>
                            <p className="setting-description">
                                Used when connected to public networks (cafes, airports, hotels)
                            </p>
                        </div>
                        <ToggleSwitch
                            checked={status?.public ?? false}
                            onChange={(enabled) => handleProfileToggle('Public', enabled)}
                            disabled={saving === 'Public'}
                        />
                    </div>
                </div>
            </Card>

            {/* Info Card */}
            <Card className="bg-blue-500/10! border-blue-500/30!">
                <div className="flex items-start gap-3">
                    <Shield className="w-5 h-5 text-blue-400 mt-0.5" />
                    <div>
                        <p className="text-sm text-blue-200">
                            <strong>Tip:</strong> Keep all firewall profiles enabled for maximum security.
                            Only disable specific profiles if you understand the security implications.
                        </p>
                    </div>
                </div>
            </Card>
        </motion.div>
    );
}
