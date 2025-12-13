import { useState, useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import { AnimatePresence, motion } from 'framer-motion';
import { Sidebar, TabType } from './components/Layout/Sidebar';
import { Header } from './components/Layout/Header';
import { SMBTab } from './components/SMBTab';
import { NetworkTab } from './components/NetworkTab';
import { FirewallTab } from './components/FirewallTab';
import { isAdmin } from './lib/tauri';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState<TabType>('smb');
  const [adminStatus, setAdminStatus] = useState<boolean>(false);
  const [checkingAdmin, setCheckingAdmin] = useState(true);

  useEffect(() => {
    checkAdminStatus();
  }, []);

  const checkAdminStatus = async () => {
    try {
      setCheckingAdmin(true);
      const status = await isAdmin();
      setAdminStatus(status);
    } catch (error) {
      console.error('Failed to check admin status:', error);
      setAdminStatus(false);
    } finally {
      setCheckingAdmin(false);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: 'rgba(30, 41, 59, 0.95)',
            backdropFilter: 'blur(20px)',
            color: 'white',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '12px',
          },
          success: {
            iconTheme: { primary: '#22c55e', secondary: 'white' },
          },
          error: {
            iconTheme: { primary: '#ef4444', secondary: 'white' },
          },
          duration: 4000,
        }}
      />

      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

      <div className="flex-1 flex flex-col overflow-hidden">
        <Header isAdmin={adminStatus} checking={checkingAdmin} />

        <main className="flex-1 overflow-y-auto">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
              className="h-full"
            >
              {activeTab === 'smb' && <SMBTab />}
              {activeTab === 'network' && <NetworkTab />}
              {activeTab === 'firewall' && <FirewallTab />}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}

export default App;
