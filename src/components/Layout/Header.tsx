import { useState, useEffect } from 'react';
import { CheckCircle, AlertTriangle, Loader2, Wifi, WifiOff } from 'lucide-react';
import { checkInternet } from '../../lib/tauri';

interface HeaderProps {
    isAdmin: boolean;
    checking?: boolean;
}

export function Header({ isAdmin, checking }: HeaderProps) {
    const [hasInternet, setHasInternet] = useState<boolean | null>(null);

    useEffect(() => {
        checkInternetStatus();
        // Check every 30 seconds
        const interval = setInterval(checkInternetStatus, 30000);
        return () => clearInterval(interval);
    }, []);

    const checkInternetStatus = async () => {
        try {
            const status = await checkInternet();
            setHasInternet(status);
        } catch {
            setHasInternet(false);
        }
    };

    return (
        <header className="h-14 px-6 flex items-center justify-between border-b border-white/10 bg-white/5 backdrop-blur-xl">
            <div className="flex items-center gap-3">
                {/* Admin Status */}
                {checking ? (
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-500/20 text-gray-400 rounded-lg text-sm">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Checking...</span>
                    </div>
                ) : isAdmin ? (
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-green-500/20 text-green-400 rounded-lg text-sm">
                        <CheckCircle className="w-4 h-4" />
                        <span>Administrator</span>
                    </div>
                ) : (
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-500/20 text-amber-400 rounded-lg text-sm">
                        <AlertTriangle className="w-4 h-4" />
                        <span>Limited Permissions</span>
                    </div>
                )}

                {/* Internet Status */}
                {hasInternet !== null && (
                    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm ${hasInternet
                            ? 'bg-green-500/20 text-green-400'
                            : 'bg-red-500/20 text-red-400'
                        }`}>
                        {hasInternet ? (
                            <>
                                <Wifi className="w-4 h-4" />
                                <span>Online</span>
                            </>
                        ) : (
                            <>
                                <WifiOff className="w-4 h-4" />
                                <span>Offline</span>
                            </>
                        )}
                    </div>
                )}
            </div>

            <div className="flex items-center gap-4">
                <span className="text-sm text-gray-400">Anjaymabar Net Tools v2.0</span>
            </div>
        </header>
    );
}
