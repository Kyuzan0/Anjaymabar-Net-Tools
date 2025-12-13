# 🎯 Refactor Planning: Python PyQt5 → Rust + Tauri

## 📋 Executive Summary

**Project:** Anjaymabar Net Tools (SMB Network Manager)  
**Current:** Python 3 + PyQt5 (~35 MB)  
**Target:** Rust + Tauri + React (~8-12 MB)  
**Estimated Timeline:** 14 hari (2 weeks)  
**Development Tools:** VS Code + Antigravity (NO Visual Studio!)  
**Risk Level:** Medium  
**Expected Benefits:**
- ✅ Size reduction: 65-75% (35 MB → 8-12 MB)
- ✅ Modern UI: WinUI 3 style replicated dengan web tech
- ✅ VS Code native development
- ✅ Faster startup time
- ✅ Lower memory footprint
- ✅ Single .exe output

---

## 🏆 ACTUAL RESULTS (As of 2025-12-13)

| Metric | Target | Achieved | Status |
|--------|--------|----------|--------|
| **Binary Size** | 8-12 MB | **8.72 MB** | ✅ ACHIEVED |
| **Size Reduction** | 65-75% | **75%** | ✅ EXCEEDED |
| **SMB Settings** | 3 toggles working | ✅ All 3 implemented | ✅ DONE |
| **Network Settings** | Adapter/IP config | ✅ Full implementation | ✅ DONE |
| **Firewall Settings** | Profile toggles | ✅ All 3 profiles | ✅ DONE |
| **Diagnostics** | ping/tracert/etc | ✅ 7 commands | ✅ DONE |
| **Admin Check** | Working | ✅ Via PowerShell | ✅ DONE |
| **Registry Access** | Working | ✅ winreg crate | ✅ DONE |
| **UI Framework** | React + Tailwind | ✅ Fully styled | ✅ DONE |
| **Installers** | NSIS/MSI | ✅ Both generated | ✅ DONE |

---

## 📊 Implementation Progress

### ✅ Day 1-2: COMPLETED (2025-12-13)

#### Environment Setup
- [x] Rust 1.92.0 installed (via winget)
- [x] Node.js v24.8.0 verified
- [x] MSVC Build Tools 2022 installed
- [x] VS Code extensions configured

#### Project Creation
- [x] Tauri project created: `am_net_tools/`
- [x] React + TypeScript + Vite template
- [x] Dependencies installed:
  - tailwindcss v4 + @tailwindcss/postcss
  - framer-motion
  - lucide-react  
  - react-hot-toast
- [x] Tailwind configured with custom theme

#### UI Components Created
- [x] `Layout/Sidebar.tsx` - Navigation sidebar
- [x] `Layout/Header.tsx` - Admin status header
- [x] `UI/ToggleSwitch.tsx` - Animated toggle
- [x] `UI/Card.tsx` - Glassmorphism card
- [x] `UI/Button.tsx` - Primary/secondary variants
- [x] `SMBTab.tsx` - Full implementation with Rust backend
- [x] `NetworkTab.tsx` - Placeholder
- [x] `FirewallTab.tsx` - Placeholder

#### Rust Backend Created
- [x] `src-tauri/src/smb.rs`:
  - `get_smb_settings()` - Read Registry
  - `set_smb_guest_auth()` - AllowInsecureGuestAuth
  - `set_smb_client_signature()` - Client signature
  - `set_smb_server_signature()` - Server signature
  - `reset_smb_settings()` - Reset defaults
  - `restart_smb_service()` - Via PowerShell
- [x] `src-tauri/src/admin.rs`:
  - `is_admin()` - Check privileges
  - `request_elevation()` - UAC request

#### Frontend Integration
- [x] `src/lib/tauri.ts` - API wrapper
- [x] SMBTab connected to Rust backend
- [x] Toast notifications working
- [x] Loading states implemented
- [x] Error handling complete

#### Build Results
- [x] Dev build working: `npm run tauri dev`
- [x] Release build successful: `npm run tauri build`
- [x] **Final .exe size: 8.61 MB** ✅
- [x] NSIS installer generated
- [x] MSI installer generated

### ✅ Day 3-4: COMPLETED (2025-12-13)

#### Network Module (`src-tauri/src/network.rs`)
- [x] `get_network_adapters()` - List PCIe/Ethernet adapters
- [x] `get_ip_configuration()` - Get IP, subnet, gateway, DNS
- [x] `apply_dhcp()` - Enable DHCP on adapter
- [x] `apply_static_ip()` - Set static IP config
- [x] `run_ipconfig()` - Run ipconfig command
- [x] `release_ip()` - Release IP address
- [x] `renew_ip()` - Renew IP address
- [x] `flush_dns()` - Flush DNS cache
- [x] `display_dns()` - Display DNS cache
- [x] `open_network_connections()` - Open ncpa.cpl
- [x] `open_network_settings()` - Open ms-settings:network

#### Firewall Module (`src-tauri/src/firewall.rs`)
- [x] `get_firewall_status()` - Get Domain/Private/Public status
- [x] `set_firewall_profile()` - Enable/disable specific profile
- [x] `enable_all_firewall()` - Enable all profiles
- [x] `disable_all_firewall()` - Disable all profiles
- [x] `open_firewall_settings()` - Open firewall.cpl
- [x] `open_advanced_firewall()` - Open wf.msc

#### NetworkTab.tsx - Full Implementation
- [x] Adapter dropdown with status icons (🟢/🔴)
- [x] DHCP/Static radio buttons
- [x] IP configuration form (IP, Subnet, Gateway, DNS)
- [x] Apply configuration button
- [x] Quick commands (ipconfig, release, renew, flush DNS)
- [x] Command output display with clear button

#### FirewallTab.tsx - Full Implementation
- [x] Enable/Disable All buttons with security warning
- [x] Individual profile toggles (Domain, Private, Public)
- [x] Status badges (Enabled/Disabled)
- [x] Quick access buttons (firewall.cpl, wf.msc)
- [x] Security warning banners

### ✅ Day 5-6: COMPLETED (2025-12-13)

#### Diagnostics Module (`src-tauri/src/diagnostics.rs`)
- [x] `run_ping()` - Ping host with count
- [x] `run_tracert()` - Trace route to host
- [x] `run_nslookup()` - DNS lookup
- [x] `run_netstat()` - Connection statistics
- [x] `get_hostname()` - Get computer name
- [x] `get_network_info()` - System network info
- [x] `check_internet()` - Check internet connectivity

#### IP Validation (`src/lib/validators.ts`)
- [x] `isValidIPv4()` - Validate IPv4 format
- [x] `isValidSubnetMask()` - Validate subnet mask
- [x] `prefixToSubnet()` - CIDR to subnet conversion
- [x] `subnetToPrefix()` - Subnet to CIDR conversion
- [x] `getIPClass()` - Get IP class (A/B/C/D/E)
- [x] `isPrivateIP()` - Check if private IP
- [x] `validateIPForm()` - Complete form validation

#### UI Enhancements
- [x] Enhanced App.css with better styling
- [x] Custom animations (fadeIn, pulse, spin)
- [x] Improved scrollbar styling
- [x] Better button hover effects
- [x] Radio button custom styling
- [x] Header with Internet status indicator (Online/Offline)
- [x] Auto-refresh internet status every 30 seconds

#### Build Results
- [x] **Final .exe size: 8.72 MB** ✅
- [x] **Total Rust Commands: 32**
- [x] **React Components: 10+**

### ⏳ Day 7+: REMAINING

- [ ] UI polish and final animations
- [ ] Windows 10/11 compatibility testing
- [ ] Edge cases and error handling review
- [ ] Final performance optimization
- [ ] README.md documentation
- [ ] Screenshot/demo recording
- [ ] Release v2.0.0 tag

---

## �🎨 Target Design Specification

**Design Goal:** Replicate WinUI 3 Fluent Design mockup menggunakan web technologies

### Visual Design (From WinUI 3 Mockup)
- **Theme:** Dark mode with gradient background (mimic Mica)
- **Layout:** Left sidebar navigation (replicate NavigationView)
- **Accent Color:** #2196F3 (Blue) - consistent dengan mockup
- **Typography:** Segoe UI Variable Display / Inter
- **S pacing:** 24px main padding, 16px between sections
- **Card Style:** Glassmorphism (backdrop-filter: blur) - replicate Acrylic
- **Shadows:** Subtle depth dengan modern CSS shadows
- **Animations:** Framer Motion - smooth like Fluent Design

### Navigation Structure (Same as Mockup)
```
Anjaymabar Net Tools
├── 🔗 SMB Settings (Library icon)
├── 🌐 Network Settings (Globe icon)
└── 🛡️ Firewall Settings (Shield icon)
```

### Components per Page
- **SMB Settings:**
  - 3 custom toggle switches (Insecure Guest, Client Signature, Server Signature)
  - 2 action buttons (Reset to Default, Restart SMB Service)
  - Status notifications (toast/modal)

- **Network Settings:**
  - Adapter selector dropdown
  - DHCP/Static radio group
  - IP configuration inputs (IP, Subnet, Gateway, DNS)
  - Quick action buttons
  - Output text area dengan scroll

- **Firewall Settings:**
  - Enable/Disable all profiles button
  - 3 profile toggles (Domain, Private, Public)
  - Quick access buttons
  - Status display area

---

## 📊 Migration Mapping

### Python → Rust/React Code Mapping

| Python File | Tauri Equivalent | Lines | Type |
|-------------|------------------|-------|------|
| `main.py` (146) | `src-tauri/src/main.rs` | ~100 | Rust |
| `ui/main_window.py` (232) | `src/App.tsx` + `Layout.tsx` | ~150 | React/TS |
| `ui/smb_tab.py` (978) | `src/components/SMBTab.tsx` + `smb.rs` | ~300 + 150 | React + Rust |
| `ui/network_tab.py` (803) | `src/components/NetworkTab.tsx` + `network.rs` | ~400 + 200 | React + Rust |
| `ui/firewall_tab.py` (251) | `src/components/FirewallTab.tsx` + `firewall.rs` | ~150 + 100 | React + Rust |
| `ui/toggle_switch.py` (75) | `src/components/ToggleSwitch.tsx` | ~80 | React |
| `ui/loading_overlay.py` (45) | `src/components/LoadingSpinner.tsx` | ~40 | React |
| `utils/powershell.py` (318) | `src-tauri/src/powershell.rs` | ~150 | Rust |
| `utils/admin_check.py` (186) | `src-tauri/src/admin.rs` | ~80 | Rust |
| **Total** | | **~1,850 lines** | |

**Benefit:** ~2,800 lines (Python) → ~1,850 lines (Rust +React/TS) = **34% code reduction**

---

## 🏗️ Tauri Project Structure

```
smb-network-manager/
├── src-tauri/                       # Rust backend
│   ├── src/
│   │   ├── main.rs                  # Tauri entry point + app setup
│   │   ├── smb.rs                   # SMB operations (Registry access)
│   │   ├── network.rs               # Network config (PowerShell)
│   │   ├── firewall.rs              # Firewall operations
│   │   ├── powershell.rs            # PowerShell execution utility
│   │   ├── admin.rs                 # Admin privilege check
│   │   └── lib.rs                   # Shared utilities
│   ├── Cargo.toml                   # Rust dependencies
│   ├── tauri.conf.json              # Tauri configuration
│   ├── build.rs                     # Build script
│   └── icons/                       # App icons
│       └── icon.ico
│
├── src/                             # React frontend
│   ├── App.tsx                      # Main app component + routing
│   ├── main.tsx                     # React entry point
│   │
│   ├── components/                  # UI Components
│   │   ├── Layout/
│   │   │   ├── Sidebar.tsx          # Navigation sidebar
│   │   │   └── Header.tsx           # App header bar
│   │   │
│   │   ├── UI/
│   │   │   ├── ToggleSwitch.tsx     # Custom toggle component
│   │   │   ├── Button.tsx           # Styled button
│   │   │   ├── Card.tsx             # Glass card container
│   │   │   ├── Input.tsx            # Styled input field
│   │   │   └── LoadingSpinner.tsx   # Loading indicator
│   │   │
│   │   ├── SMBTab.tsx               # SMB settings page
│   │   ├── NetworkTab.tsx           # Network settings page
│   │   └── FirewallTab.tsx          # Firewall settings page
│   │
│   ├── hooks/                       # Custom React hooks
│   │   ├── useTauriCommand.ts       # Hook for Tauri commands
│   │   └── useToast.ts              # Toast notification hook
│   │
│   ├── lib/                         # Utilities
│   │   ├── tauri.ts                 # Tauri command wrappers
│   │   └── validators.ts            # IP validation, etc.
│   │
│   ├── styles/
│   │   └── globals.css              # Tailwind base + custom styles
│   │
│   └── types/
│       ├── smb.ts                   # SMB types
│       ├── network.ts               # Network types
│       └── firewall.ts              # Firewall types
│
├── public/                          # Static assets
│   └── vite.svg
│
├── package.json                     # Node dependencies
├── vite.config.ts                   # Vite configuration
├── tailwind.config.js               # Tailwind configuration
├── tsconfig.json                    # TypeScript configuration
└── README.md

```

---

## 📅 Implementation Timeline (14 Days)

### **Week 1: Foundation & Backend**

#### **Day 1-2: Environment Setup & Project Init** ✅ COMPLETED
- [x] Install Rust (rustup.rs) → **v1.92.0 installed**
- [x] Install Node.js 20+ LTS → **v24.8.0 available**
- [x] Install VS Code extensions:
  - rust-analyzer ✅
  - Tauri ✅
  - ES7+ React/Redux/React-Native snippets ✅
  - Tailwind CSS IntelliSense ✅
- [x] Create Tauri project: `npm create tauri-app@latest` → **am_net_tools/ created**
  - Choose: React + TypeScript + Vite ✅
- [x] Setup Tailwind CSS: `npm install -D tailwindcss@next` → **v4 + @tailwindcss/postcss**
- [x] Install dependencies:
  - `npm install framer-motion lucide-react react-hot-toast` ✅
- [x] Configure `tauri.conf.json` (app name, window size, etc.) ✅
- [x] Import app icon to `src-tauri/icons/` ✅
- [x] **Deliverable:** Working Tauri hello world ✅

#### **Day 3: React App Structure & Basic Layout** ✅ COMPLETED (ahead of schedule!)
- [x] Create folder structure (components/, hooks/, lib/, types/) ✅
- [x] Setup Tailwind config dengan theme colors (#2196F3 accent) ✅
- [x] Create `Layout` components:
  - `Sidebar.tsx` - Navigation sidebar (replicate NavigationView) ✅
  - `Header.tsx` - App header dengan admin status banner ✅
- [x] Implement basic routing (SMB, Network, Firewall tabs) ✅
- [x] Create base UI components:
  - `Card.tsx` - Glassmorphism card ✅
  - `Button.tsx` - Styled button ✅
  - `ToggleSwitch.tsx` - Custom toggle ✅
- [x] Apply dark theme gradient background ✅
- [x] **Deliverable:** UI shell dengan navigation ✅

#### **Day 4-5: Rust Backend (Tauri Commands)** ✅ COMPLETED (ahead of schedule!)
- [x] Create `src-tauri/src/admin.rs`:
  - Windows UAC check function ✅
  - Elevation request function ✅
- [x] Create `src-tauri/src/smb.rs`:
  - Read Registry SMB settings (Guest Auth, Client Sig, Server Sig) ✅
  - Write Registry SMB settings ✅
  - Reset to defaults ✅
  - Restart SMB service (via PowerShell) ✅
- [x] Expose Tauri commands:
  - `#[tauri::command] fn get_smb_settings() -> Result<SMBSettings, String>` ✅
  - `#[tauri::command] fn set_smb_guest_auth(enabled: bool) -> Result<(), String>` ✅
  - `#[tauri::command] fn restart_smb_service() -> Result<(), String>` ✅
- [x] Test dari frontend (use `invoke` from @tauri-apps/api) ✅
- [x] **Deliverable:** Working Rust backend dengan SMB operations ✅

---

### **Week 2: UI Implementation & Polish**

#### **Day 6-7: SMB Page (High Priority)** 🔗
- [ ] Create `src/components/SMBTab.tsx`
- [ ] Implement UI matching mockup:
  - 3 toggle switches with labels + descriptions
  - Card layout dengan glassmorphism
  - Button group (Reset, Restart)
- [ ] Create TypeScript types (`types/smb.ts`)
- [ ] Implement Tauri command calls:
  - Load current settings on mount
  - Toggle handlers calling Rust backend
  - Reset button logic
  - Restart service with confirmation
- [ ] Add Framer Motion animations (fade in, transitions)
- [ ] Implement toast notifications (react-hot-toast)
- [ ] Error handling dengan user-friendly messages
- [ ] Save/load settings state
- [ ] **Deliverable:** Fully working SMB Settings page

#### **Day 8-9: Network Page (High Priority)** 🌐
- [ ] Create `src-tauri/src/network.rs`:
  - Get network adapters (PowerShell: Get-NetAdapter)
  - Get IP configuration
  - Set static IP / DHCP
  - Execute ipconfig, flush DNS, etc.
- [ ] Create `src/components/NetworkTab.tsx`
- [ ] Implement UI:
  - Adapter dropdown (select element)
  - DHCP/Static radio buttons
  - IP/Subnet/Gateway/DNS input fields
  - Apply button
- [ ] Implement quick action buttons:
  - ipconfig
  - ipconfig /all
  - Release IP
  - Renew IP
  - Flush DNS
  - Display DNS cache
- [ ] Add output text area dengan scrolling
- [ ] IP address validation (lib/validators.ts)
- [ ] **Deliverable:** Fully working Network Settings page

#### **Day 10: Firewall Page (Medium Priority)** 🛡️
- [ ] Create `src-tauri/src/firewall.rs`:
  - Get firewall profile status
  - Enable/disable firewall profiles
  - Get firewall rule count
- [ ] Create `src/components/FirewallTab.tsx`
- [ ] Implement UI:
  - 3 profile toggles (Domain, Private, Public)
  - Enable/Disable All buttons
  - Status display cards
- [ ] Add confirmation dialogs untuk disable operations
- [ ] Quick access shortcuts (open Firewall settings)
- [ ] **Deliverable:** Fully working Firewall Settings page

#### **Day 11: Styling & Animations** 🎨
- [ ] Polish all pages dengan consistent styling
- [ ] Apply glassmorphism effects to all cards
- [ ] Add Framer Motion animations:
  - Page transitions (fade in/out)
  - Toggle switch animations
  - Button hover/press animations
  - Loading spinners
- [ ] Implement responsive layouts (though desktop-only)
- [ ] Add smooth scrolling
- [ ] Polish color scheme, shadows, spacing
- [ ] Review against WinUI 3 mockup (95%+ match)
- [ ] **Deliverable:** Polished UI matching mockup

#### **Day 12: Testing & Bug Fixes** 🐛
- [ ] Manual testing all features
- [ ] Test admin vs non-admin scenarios
- [ ] Test on Windows 10 1809+ and Windows 11
- [ ] Test dengan different resolutions
- [ ] Fix any bugs found
- [ ] Performance testing (startup time, memory usage)
- [ ] WebView2 DevTools debugging
- [ ] **Deliverable:** Stable build

#### **Day 13: Build Optimization** ⚡
- [ ] Optimize Tauri bundle:
  - Enable `tauri.bundle.active = true`
  - Configure `tauri.bundle.targets = ["nsis"]` for installer
  - Set compression: `lzma`
- [ ] Optimize Rust build:
  - `cargo build --release` with optimizations
  - Strip debug symbols
- [ ] Treeshake unused code (Vite + Rollup)
- [ ] Optimize images/assets
- [ ] Measure final .exe size (target: 8-12 MB)
- [ ] **Deliverable:** Optimized 8-12 MB executable

#### **Day 14: Documentation & Finalization** 📝
- [ ] Update README.md dengan Tauri instructions
- [ ] Create build documentation
- [ ] Create user guide (markdown)
- [ ] Screenshot app untuk documentation
- [ ] Create installer (NSIS) optional
- [ ] Final testing
- [ ] Git commit & tag release (v2.0.0)
- [ ] **Deliverable:** Production-ready release

---

## 🔧 Technical Implementation Details

### 1. Tauri Configuration (tauri.conf.json)

```json
{
  "build": {
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build",
    "devPath": "http://localhost:1420",
    "distDir": "../dist"
  },
  "package": {
    "productName": "Anjaymabar Net Tools",
    "version": "2.0.0"
  },
  "tauri": {
    "allowlist": {
      "all": false,
      "shell": {
        "all": false,
        "open": true
      },
      "window": {
        "all": false,
        "close": true,
        "hide": true,
        "show": true,
        "maximize": true,
        "minimize": true,
        "setTitle": true
      }
    },
    "bundle": {
      "active": true,
      "targets": ["nsis"],
      "identifier": "com.anjaymabar.nettools",
      "icon": [
        "icons/icon.ico"
      ],
      "windows": {
        "certificateThumbprint": null,
        "digestAlgorithm": "sha256",
        "timestampUrl": ""
      }
    },
    "security": {
      "csp": null
    },
    "windows": [
      {
        "fullscreen": false,
        "height": 600,
        "resizable": true,
        "title": "Anjaymabar Net Tools",
        "width": 900,
        "minWidth": 800,
        "minHeight": 600,
        "decorations": true,
        "transparent": false
      }
    ]
  }
}
```

### 2. Rust Backend - SMB Operations (smb.rs)

```rust
use serde::{Deserialize, Serialize};
use winreg::enums::*;
use winreg::RegKey;

#[derive(Debug, Serialize, Deserialize)]
pub struct SMBSettings {
    pub guest_auth_enabled: bool,
    pub client_signature_required: bool,
    pub server_signature_required: bool,
}

const SMB_REG_PATH: &str = r"SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters";

#[tauri::command]
pub fn get_smb_settings() -> Result<SMBSettings, String> {
    let hklm = RegKey::predef(HKEY_LOCAL_MACHINE);
    let smb_key = hklm
        .open_subkey(SMB_REG_PATH)
        .map_err(|e| format!("Failed to open registry key: {}", e))?;

    let guest_auth: u32 = smb_key
        .get_value("AllowInsecureGuestAuth")
        .unwrap_or(0);

    // TODO: Get client & server signature settings
    
    Ok(SMBSettings {
        guest_auth_enabled: guest_auth == 1,
        client_signature_required: false,
        server_signature_required: false,
    })
}

#[tauri::command]
pub fn set_smb_guest_auth(enabled: bool) -> Result<(), String> {
    let hklm = RegKey::predef(HKEY_LOCAL_MACHINE);
    let smb_key = hklm
        .open_subkey_with_flags(SMB_REG_PATH, KEY_WRITE)
        .map_err(|e| format!("Failed to open registry key: {}", e))?;

    let value: u32 = if enabled { 1 } else { 0 };
    smb_key
        .set_value("AllowInsecureGuestAuth", &value)
        .map_err(|e| format!("Failed to set registry value: {}", e))?;

    Ok(())
}

#[tauri::command]
pub async fn restart_smb_service() -> Result<String, String> {
    use std::process::Command;

    let output = Command::new("powershell")
        .args(&[
            "-NoProfile",
            "-Command",
            "Restart-Service -Name LanmanWorkstation -Force",
        ])
        .output()
        .map_err(|e| format!("Failed to execute PowerShell: {}", e))?;

    if output.status.success() {
        Ok("SMB service restarted successfully".to_string())
    } else {
        let error = String::from_utf8_lossy(&output.stderr);
        Err(format!("Failed to restart service: {}", error))
    }
}
```

### 3. React Frontend - SMB Tab (SMBTab.tsx)

```typescript
import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { motion } from 'framer-motion';
import { toast } from 'react-hot-toast';
import { Shield, AlertTriangle, RefreshCw } from 'lucide-react';
import { Card } from './UI/Card';
import { ToggleSwitch } from './UI/ToggleSwitch';
import { Button } from './UI/Button';

interface SMBSettings {
  guest_auth_enabled: boolean;
  client_signature_required: boolean;
  server_signature_required: boolean;
}

export function SMBTab() {
  const [settings, setSettings] = useState<SMBSettings | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const data = await invoke<SMBSettings>('get_smb_settings');
      setSettings(data);
    } catch (error) {
      toast.error(`Failed to load settings: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  const handleGuestAuthToggle = async (enabled: boolean) => {
    try {
      await invoke('set_smb_guest_auth', { enabled });
      setSettings(prev => prev ? { ...prev, guest_auth_enabled: enabled } : null);
      toast.success('Guest authentication updated');
    } catch (error) {
      toast.error(`Failed to update: ${error}`);
    }
  };

  const handleRestart = async () => {
    if (!confirm('Restart SMB service? This may disconnect active shares.')) {
      return;
    }

    try {
      const result = await invoke<string>('restart_smb_service');
      toast.success(result);
    } catch (error) {
      toast.error(`Failed to restart: ${error}`);
    }
  };

  if (loading || !settings) {
    return <div className="flex items-center justify-center h-full">Loading...</div>;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-6 space-y-6"
    >
      {/* Header */}
      <div className="flex items-center gap-3">
        <Shield className="w-8 h-8 text-blue-500" />
        <h2 className="text-2xl font-bold text-white">SMB Configuration</h2>
      </div>

      {/* Settings Card */}
      <Card className="space-y-4">
        {/* Guest Auth Toggle */}
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-semibold text-white">
                Insecure Guest Logons
              </h3>
              {settings.guest_auth_enabled && (
                <AlertTriangle className="w-5 h-5 text-amber-500" />
              )}
            </div>
            <p className="text-sm text-gray-400 mt-1">
              Allow guest authentication for SMB shares (not recommended)
            </p>
          </div>

          <ToggleSwitch
            checked={settings.guest_auth_enabled}
            onChange={handleGuestAuthToggle}
          />
        </div>

        <div className="border-t border-white/10" />

        {/* Client Signature Toggle */}
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-white">
              Client Security Signature
            </h3>
            <p className="text-sm text-gray-400 mt-1">
              Require security signature for SMB client connections
            </p>
          </div>

          <ToggleSwitch
            checked={settings.client_signature_required}
            onChange={() => {/* TODO */}}
          />
        </div>

        <div className="border-t border-white/10" />

        {/* Server Signature Toggle */}
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-white">
              Server Security Signature
            </h3>
            <p className="text-sm text-gray-400 mt-1">
              Require security signature for SMB server connections
            </p>
          </div>

          <ToggleSwitch
            checked={settings.server_signature_required}
            onChange={() => {/* TODO */}}
          />
        </div>
      </Card>

      {/* Action Buttons */}
      <div className="flex gap-3">
        <Button variant="primary" onClick={() => {/* Reset logic */}}>
          Reset to Default
        </Button>
        <Button
          variant="secondary"
          onClick={handleRestart}
          icon={<RefreshCw className="w-4 h-4" />}
        >
          Restart SMB Service
        </Button>
      </div>
    </motion.div>
  );
}
```

### 4. Custom Components - Toggle Switch (ToggleSwitch.tsx)

```typescript
import { motion } from 'framer-motion';

interface ToggleSwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
}

export function ToggleSwitch({ checked, onChange, disabled }: ToggleSwitchProps) {
  return (
    <button
      onClick={() => !disabled && onChange(!checked)}
      disabled={disabled}
      className={`
        relative w-14 h-8 rounded-full transition-colors duration-200
        ${checked ? 'bg-blue-500' : 'bg-gray-600'}
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
      `}
    >
      <motion.div
        className="absolute top-1 left-1 w-6 h-6 bg-white rounded-full shadow-lg"
        animate={{ x: checked ? 24 : 0 }}
        transition={{ type: 'spring', stiffness: 500, damping: 30 }}
      />
    </button>
  );
}
```

### 5. Tailwind Configuration (tailwind.config.js)

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#2196F3', // Blue accent (from WinUI 3 mockup)
        'glass-bg': 'rgba(255, 255, 255, 0.05)',
        'glass-border': 'rgba(255, 255, 255, 0.1)',
      },
      fontFamily: {
        sans: ['Segoe UI Variable Display', 'Inter', 'sans-serif'],
      },
      backdropBlur: {
        'glass': '20px',
      },
      boxShadow: {
        'glass': '0 8px 32px rgba(0, 0, 0, 0.3)',
        'glow': '0 0 20px rgba(33, 150, 243, 0.3)',
      },
    },
  },
  plugins: [],
}
```

### 6. Global Styles (globals.css)

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 min-h-screen;
    @apply text-white font-sans antialiased;
  }
}

@layer components {
  .glass-card {
    @apply bg-white/5 backdrop-blur-xl border border-white/10;
    @apply rounded-2xl shadow-glass;
  }

  .btn-primary {
    @apply px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-600;
    @apply text-white rounded-xl font-semibold;
    @apply hover:from-blue-600 hover:to-blue-700;
    @apply transition-all duration-200 shadow-lg shadow-blue-500/25;
    @apply active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed;
  }

  .btn-secondary {
    @apply px-6 py-3 bg-white/5 backdrop-blur-xl border border-white/10;
    @apply text-white rounded-xl font-semibold;
    @apply hover:bg-white/10 transition-all duration-200;
    @apply active:scale-95 disabled:opacity-50;
  }
}
```

---

## ✅ Success Criteria

### Functional Requirements
- [ ] All SMB settings toggle and persist correctly
- [ ] Network adapter configuration works (DHCP/Static)
- [ ] Firewall profile management functions
- [ ] Admin elevation prompts when needed
- [ ] All Tauri commands execute successfully
- [ ] Registry operations work reliably

### Non-Functional Requirements
- [ ] Binary size: **8-12 MB** (.exe file)
- [ ] Startup time: < 2 seconds
- [ ] Memory usage: < 50 MB idle
- [ ] UI matches WinUI 3 mockup 95%+
- [ ] No crashes or exceptions in normal use
- [ ] Works on Windows 10 1809+ and Windows 11
- [ ] WebView2 runtime available (auto-download fallback)

---

## 📦 Build & Deployment

### Development
```bash
# Install dependencies
npm install

# Run dev mode (hot reload)
npm run tauri dev
```

### Production Build
```bash
# Build optimized executable
npm run tauri build

# Output locations:
# - src-tauri/target/release/anjaymabar-net-tools.exe (8-12 MB)
# - src-tauri/target/release/bundle/nsis/Anjaymabar Net Tools_2.0.0_x64-setup.exe (installer)
```

### Distribution
- **Standalone .exe:** Share `anjaymabar-net-tools.exe` directly
- **Installer:** Use NSIS installer for easier deployment
- **Requirements:** Windows 10 1809+, WebView2 runtime (usually pre-installed)

---

## 🚨 Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Rust learning curve | Medium | Medium | Follow Tauri docs, use examples, ask Claude |
| WebView2 not installed | Low | Medium | Tauri auto-downloads WebView2 if missing |
| Registry permission errors | Low | Medium | Proper UAC elevation, clear error messages |
| PowerShell execution blocked | Low | High | Request execution policy bypass in code |
| Timeline overrun | Medium | Medium | Focus core features first (SMB, Network) |
| UI not matching mockup | Low | Low | Iterative development, frequent comparisons |

---

## 📚 Resources & References

### Documentation
- [Tauri Documentation](https://tauri.app/)
- [Tauri 2.0 Guide](https://tauri.app/v2/)
- [React Documentation](https://react.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Framer Motion](https://www.framer.com/motion/)
- [windows-rs](https://github.com/microsoft/windows-rs)

### Tools
- VS Code + Extensions (rust-analyzer, Tauri, ES7+ React)
- Node.js 20+ LTS
- Rust 1.70+
- Tauri CLI

### Sample Code
- [Tauri Examples](https://github.com/tauri-apps/tauri/tree/dev/examples)
- [Tauri Plugin Registry](https://github.com/tauri-apps/plugins-workspace)

---

## 🎯 Next Steps

1. **Day 1:** Setup Rust + Node.js + VS Code
2. **Day 1:** Create Tauri project: `npm create tauri-app@latest`
3. **Day 1:** Install Tailwind + Framer Motion
4. **Day 2:** Configure project structure + theme colors
5. **Day 3:** Start building Layout components

**Ready to start? Let me know and I can help with:**
- ✅ Setting up the initial project (create-tauri-app)
- ✅ Generating boilerplate code (components, Rust modules)
- ✅ Troubleshooting during development
- ✅ Code review

---

*Planning document created: 2025-12-13*  
*Target: VS Code + Antigravity development only*  
*Estimated completion: 14 days from start*
