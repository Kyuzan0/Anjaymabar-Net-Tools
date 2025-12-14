# 🌐 Anjaymabar Net Tools

A modern Windows network management application built with **Tauri 2**, **React 19**, and **Rust**. Provides a beautiful, fast GUI for managing SMB settings, network configuration, and Windows firewall.

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Platform](https://img.shields.io/badge/platform-Windows-0078D6?logo=windows)
![Tauri](https://img.shields.io/badge/Tauri-2.0-FFC131?logo=tauri)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)
![Rust](https://img.shields.io/badge/Rust-Backend-orange?logo=rust)

## ✨ Features

### 🛡️ SMB Configuration
- **Insecure Guest Logons** - Toggle guest authentication for SMB shares
- **Client/Server Security Signature** - Manage SMB signing requirements
- **Reset to Defaults** - One-click secure defaults restoration
- **Restart SMB Service** - Restart LanmanWorkstation & LanmanServer
- **Advanced Sharing Settings** - Quick access to Windows sharing settings
- **Connection Testing** - Test SMB connectivity to remote hosts
- **Share Browser** - List and open SMB shares on remote hosts

### 🌐 Network Settings
- **Adapter Selection** - View and manage physical network adapters
- **DHCP/Static IP** - Switch between automatic and manual IP configuration
- **IP Configuration** - Set IP address, subnet mask, gateway, and DNS servers
- **Quick Commands** - ipconfig, release/renew IP, flush/display DNS
- **External Tools** - Quick access to ncpa.cpl and Windows Settings

### 🔥 Firewall Management
- **Profile Status** - View Domain, Private, and Public firewall status
- **Toggle Profiles** - Enable/disable individual firewall profiles
- **Quick Actions** - Enable all or disable all profiles
- **Advanced Firewall** - Open Windows Firewall with Advanced Security

### ⚡ Performance Optimizations
- **Multi-layer Caching** - React-side + Rust-side cache with TTL
- **LocalStorage Persistence** - Cache survives app restarts (5 min TTL)
- **Prefetch on Hover** - Adapter configs preloaded when dropdown focused
- **Debounced Requests** - 150ms debounce prevents rapid API calls
- **Skeleton Loading** - Beautiful loading states during data fetch
- **Benchmark Tool** - Built-in performance measurement utility

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 19, TypeScript, Tailwind CSS 4 |
| **Animation** | Framer Motion |
| **Icons** | Lucide React |
| **Backend** | Rust, Tauri 2.0 |
| **System API** | PowerShell, Windows Registry (winreg) |
| **Build** | Vite 7 |

## 📁 Project Structure

```
smb_network_manager/
├── src/                        # React Frontend
│   ├── components/
│   │   ├── NetworkTab.tsx      # Network configuration UI
│   │   ├── SMBTab.tsx          # SMB settings UI
│   │   ├── FirewallTab.tsx     # Firewall management UI
│   │   ├── Layout/             # Sidebar, Header components
│   │   └── UI/                 # Reusable UI components
│   │       ├── Button.tsx
│   │       ├── Card.tsx
│   │       ├── ToggleSwitch.tsx
│   │       ├── Skeleton.tsx
│   │       ├── NetworkConfigSkeleton.tsx
│   │       └── BenchmarkPanel.tsx
│   ├── hooks/
│   │   ├── useNetworkData.ts   # Optimized network data fetching
│   │   └── useNetworkCache.ts  # Client-side cache with persistence
│   ├── lib/
│   │   ├── tauri.ts            # Tauri command wrappers
│   │   └── benchmark.ts        # Performance benchmarking utility
│   ├── App.tsx
│   ├── App.css
│   └── main.tsx
├── src-tauri/                  # Rust Backend
│   ├── src/
│   │   ├── lib.rs              # Tauri app setup & command registration
│   │   ├── smb.rs              # SMB registry & service management
│   │   ├── network.rs          # Network adapter & IP configuration
│   │   ├── network_unified.rs  # Optimized network commands with caching
│   │   ├── firewall.rs         # Windows Firewall management
│   │   ├── cache.rs            # Rust-side TTL cache
│   │   ├── admin.rs            # Admin privilege handling
│   │   ├── diagnostics.rs      # Ping, tracert, nslookup, netstat
│   │   └── file_manager.rs     # File explorer integration
│   ├── Cargo.toml
│   └── tauri.conf.json
├── package.json
├── tailwind.config.js
├── vite.config.ts
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- **Node.js** 18+ 
- **Rust** 1.70+
- **Windows 10/11** (required for Windows-specific features)

### Installation

```bash
# Clone the repository
git clone https://github.com/Kyuzan0/Anjaymabar-Net-Tools.git
cd smb_network_manager

# Install dependencies
npm install

# Run in development mode
npm run tauri dev

# Build for production
npm run tauri build
```

### Running with Administrator Privileges

Most features require **Administrator privileges** to modify system settings. The app will work in read-only mode without elevation, but cannot apply changes.

## 📊 Performance Benchmarks

The app includes a built-in benchmark tool accessible from the Network tab:

| Operation | Typical Time |
|-----------|-------------|
| Fresh Fetch (PowerShell) | ~100-200ms |
| Cache Hit (Memory) | ~0.01-0.05ms |
| LocalStorage Load | ~0.1-0.5ms |

**Cache provides ~99.9% speed improvement** over fresh fetches!

To run benchmarks:
1. Open Network tab
2. Click the 📊 (chart) icon in the header
3. Click "Run" for quick test or "Run Full Test" for comprehensive analysis

Or via browser console:
```javascript
await networkBenchmark.runQuick('Ethernet')
await networkBenchmark.runFull('Ethernet', 'Wi-Fi')
```

## ⚙️ Configuration

### Cache Settings

Located in `src/hooks/useNetworkCache.ts`:
```typescript
const DEFAULT_TTL_MS = 30000;        // Memory cache TTL: 30 seconds
const MAX_PERSISTENT_AGE_MS = 300000; // LocalStorage TTL: 5 minutes
```

Located in `src-tauri/src/cache.rs`:
```rust
const DEFAULT_TTL_SECS: u64 = 30;    // Rust-side cache TTL
const MAX_CACHE_ENTRIES: usize = 50;  // Maximum cached adapters
```

## 🔧 Available Tauri Commands

### SMB Commands
- `get_smb_settings` - Read current SMB configuration
- `set_smb_guest_auth` - Toggle insecure guest logons
- `set_smb_client_signature` - Toggle client signing
- `set_smb_server_signature` - Toggle server signing
- `reset_smb_settings` - Reset to secure defaults
- `restart_smb_service` - Restart SMB services
- `test_smb_connection` - Test SMB port connectivity
- `list_smb_shares` - List shares on remote host
- `open_advanced_sharing` - Open Windows sharing settings

### Network Commands
- `get_network_adapters` - List physical network adapters
- `get_ip_configuration` - Get IP config for adapter
- `get_ip_configuration_unified` - Optimized cached version
- `apply_dhcp` - Enable DHCP on adapter
- `apply_static_ip` - Set static IP configuration
- `run_ipconfig` - Execute ipconfig command
- `release_ip` / `renew_ip` - DHCP operations
- `flush_dns` / `display_dns` - DNS cache operations

### Firewall Commands
- `get_firewall_status` - Get all profile statuses
- `set_firewall_profile` - Toggle specific profile
- `enable_all_firewall` / `disable_all_firewall` - Batch operations
- `open_firewall_settings` - Open Windows Firewall UI

## 📝 License

MIT License - feel free to use this project for any purpose.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

**Made with ❤️ using Tauri, React, and Rust**
