import { motion } from 'framer-motion';
import { Library, Globe, Shield } from 'lucide-react';

export type TabType = 'smb' | 'network' | 'firewall';

interface SidebarProps {
    activeTab: TabType;
    onTabChange: (tab: TabType) => void;
}

const menuItems: { id: TabType; label: string; icon: React.ElementType }[] = [
    { id: 'smb', label: 'SMB Settings', icon: Library },
    { id: 'network', label: 'Network Settings', icon: Globe },
    { id: 'firewall', label: 'Firewall Settings', icon: Shield },
];

export function Sidebar({ activeTab, onTabChange }: SidebarProps) {
    return (
        <aside className="w-64 h-screen bg-white/5 backdrop-blur-xl border-r border-white/10 p-4 flex flex-col">
            {/* App Title */}
            <div className="mb-8 px-4">
                <h1 className="text-xl font-bold text-white">Anjaymabar</h1>
                <p className="text-sm text-gray-400">Net Tools</p>
            </div>

            {/* Navigation */}
            <nav className="flex-1 space-y-2">
                {menuItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = activeTab === item.id;

                    return (
                        <motion.button
                            key={item.id}
                            onClick={() => onTabChange(item.id)}
                            className={`sidebar-item w-full ${isActive ? 'active' : ''}`}
                            whileHover={{ x: 4 }}
                            whileTap={{ scale: 0.98 }}
                        >
                            <Icon className={`w-5 h-5 ${isActive ? 'text-primary' : ''}`} />
                            <span>{item.label}</span>
                        </motion.button>
                    );
                })}
            </nav>

            {/* Footer */}
            <div className="mt-auto pt-4 border-t border-white/10">
                <p className="text-xs text-gray-500 text-center">v2.0.0 - Tauri</p>
            </div>
        </aside>
    );
}
