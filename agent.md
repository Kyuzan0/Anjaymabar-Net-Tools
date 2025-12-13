# Agent Instructions
- Gunakan Bahasa Indonesia dan Inggris
- Jawaban singkat dan teknis

# Project Overview
**Anjaymabar Net Tools** - SMB & Network Manager untuk Windows
- **Status:** In Development - Refactor ke Rust + Tauri
- **Current:** Python 3 + PyQt5 (~35 MB)
- **Target:** Rust + Tauri + React (~8-12 MB)
- **Tools:** VS Code + Antigravity (NO Visual Studio needed!)

---

# 🎯 Refactor Plan Summary (Python → Rust + Tauri)

## Timeline: 14 Hari (2 Minggu)

### Week 1: Foundation
- **Day 1-2:** Rust + Tauri setup, VS Code extensions, project init
- **Day 3:** React app setup + Tailwind CSS, basic layout
- **Day 4-5:** Rust backend (Windows Registry, PowerShell execution)

### Week 2: UI & Polish
- **Day 6-7:** SMB page (3 toggle switches, buttons) - React components
- **Day 8-9:** Network page (adapter selector, IP config) - Forms
- **Day 10:** Firewall page (profile toggles)
- **Day 11:** Styling & animations (Framer Motion, glassmorphism)
- **Day 12:** Testing & bug fixes
- **Day 13:** Build optimization (size reduction)
- **Day 14:** Documentation & release

## 🏗️ Architecture

### Project Structure
```
am_net_tools/
├── src-tauri/              # Rust backend
│   ├── src/
│   │   ├── main.rs         # Entry point
│   │   ├── smb.rs          # SMB operations (Registry)
│   │   ├── network.rs      # Network config
│   │   └── firewall.rs     # Firewall operations
│   ├── Cargo.toml          # Rust dependencies
│   └── tauri.conf.json     # Tauri config
├── src/                     # React frontend
│   ├── App.tsx             # Main app component
│   ├── components/
│   │   ├── SMBTab.tsx      # SMB page
│   │   ├── NetworkTab.tsx  # Network page
│   │   └── FirewallTab.tsx # Firewall page
│   ├── styles/
│   │   └── globals.css     # Tailwind + custom styles
│   └── main.tsx
├── package.json
└── vite.config.ts
```

### Design Specs (WinUI 3 style replicated dengan Web tech)
- **Theme:** Dark mode with gradient background (mimic Mica)
- **Accent Color:** #2196F3 (Blue) - same as WinUI 3
- **Layout:** Sidebar navigation (replicate NavigationView)
- **Font:** Segoe UI Variable Display / Inter
- **Cards:** Glassmorphism (backdrop-filter: blur) - replicate Acrylic
- **Animations:** Framer Motion - smooth like Fluent Design

### Key Components (Same as WinUI 3 mockup!)
1. **SMB Settings:** 3 custom toggle switches (Guest Auth, Client Sig, Server Sig)
2. **Network Settings:** Dropdown, radio buttons, text inputs
3. **Firewall Settings:** Profile toggles (Domain, Private, Public)

## 📝 Tech Stack

### Frontend (UI Layer)
- **React 18** + **TypeScript** - Component framework
- **Tailwind CSS v4** - Utility-first styling
- **Framer Motion** - Smooth animations
- **Vite** - Fast bundler & dev server
- **Lucide React** - Icon library

### Backend (Native Layer)
- **Rust** - Systems programming language
- **Tauri 2.0** - Desktop app framework
- **winreg** - Windows Registry access
- **serde** - JSON serialization

### Integration
- **Tauri Commands** - Rust ↔ JavaScript bridge
- **WebView2** - Edge engine (built-in Windows)
- **Native .exe** - Single executable output (~8-12 MB)

## ✅ Success Criteria
- Binary size: **8-12 MB** (vs 35 MB current) - **65-75% reduction!**
- Startup: < 2 seconds
- Memory: < 50 MB idle
- UI matches WinUI 3 mockup 95%+ (replicated dengan web tech)
- All features working (SMB toggle, network config, firewall)

## 🚨 Development Rules

### DO:
- ✅ Use TypeScript untuk type safety
- ✅ Implement async Tauri commands (@tauri-apps/api)
- ✅ Use React hooks (useState, useEffect, custom hooks)
- ✅ Apply Tailwind CSS utility classes (avoid inline styles)
- ✅ Add Framer Motion animations untuk smooth transitions
- ✅ Test admin vs non-admin scenarios (UAC elevation)
- ✅ Use Rust Result<T, E> untuk error handling
- ✅ Leverage WebView2 DevTools untuk debugging

### DON'T:
- ❌ Hardcode colors (use Tailwind theme config)
- ❌ Block UI with synchronous operations (use async/await)
- ❌ Ignore UAC/admin requirements untuk registry access
- ❌ Skip error notifications to users (use toast/modal)
- ❌ Use deprecated Tauri APIs (check Tauri 2.0 docs)
- ❌ Bundle unnecessary dependencies (check bundle size)

## 📚 Reference Documents
- Full plan: `docs/refactor_tauri_plan.md`
- Design mockup: `docs/design_mockup_comparison.md`
- Tauri analysis: `docs/best_pick_modern_ui.md`
- Alternative analysis: `docs/alternative_languages_analysis.md`
- Current codebase: `docs/analysis.md`

---

# Build Instructions

## Current (Python)
```bash
python -m PyInstaller --onefile --noconsole main.py
# Output: ~35 MB
```

## Target (Rust + Tauri)
```bash
# Development (hot reload)
npm run tauri dev

# Production build (optimized .exe)
npm run tauri build
# Output: ./src-tauri/target/release/am_net_tools.exe (~8-12 MB)
```

## VS Code Setup
```bash
# Install Rust
# https://rustup.rs

# Install Node.js
# https://nodejs.org

# VS Code Extensions (Recommended):
# - rust-analyzer
# - Tauri
# - ES7+ React/Redux/React-Native snippets
# - Tailwind CSS IntelliSense
```

---

# Important Notes
- **Fokus:** Ikuti plan 14 hari, prioritas core features dulu
- **Design:** Replicate WinUI 3 mockup dengan HTML/CSS/React + Tailwind
- **Size:** Target 8-12 MB dengan Tauri build optimization
- **Quality:** Production-ready .exe, no shortcuts
- **Tools:** VS Code + Antigravity ONLY (no Visual Studio needed!)
