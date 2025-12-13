# Analisis Codebase SMB Network Manager

## Struktur Proyek
```
smb_network_manager/
├── main.py                    # Entry point aplikasi
├── requirements.txt           # Dependency: PyQt5>=5.15.0
├── SMB_Network_Manager.spec   # PyInstaller spec file
├── version_info.txt           # Version metadata
├── config/
│   └── smb_settings.json      # Konfigurasi SMB tersimpan
├── res/                       # Resources (icons, dll)
├── ui/
│   ├── __init__.py
│   ├── main_window.py         # Main window dengan tab interface
│   ├── smb_tab.py             # Tab konfigurasi SMB (978 baris)
│   ├── network_tab.py         # Tab pengaturan jaringan (803 baris)
│   ├── firewall_tab.py        # Tab pengaturan firewall (251 baris)
│   ├── toggle_switch.py       # Custom toggle switch widget
│   └── loading_overlay.py     # Loading overlay widget
├── utils/
│   ├── __init__.py
│   ├── admin_check.py         # Cek hak administrator
│   └── powershell.py          # Utility eksekusi PowerShell/CMD (318 baris)
├── build/                     # Build output
└── dist/                      # Distribution output
```

## Teknologi
- **Framework GUI**: PyQt5 >= 5.15.0
- **Bahasa**: Python 3 (Windows)
- **Packaging**: PyInstaller

## Fitur Utama (Tab)
### SMB Settings (`smb_tab.py`)
- Toggle *Insecure Guest Logons*, *Client Security Signature*, *Server Security Signature*
- Reset ke default, restart service, test koneksi, buka explorer

### Network Settings (`network_tab.py`)
- Pilih adapter, konfigurasi DHCP/Static IP, apply, tools ipconfig, release/renew, flush DNS
- Tombol cepat ke Control Panel (Network Connections, Settings, Sharing)

### Firewall Settings (`firewall_tab.py`)
- Enable/disable semua profil, toggle per profil, buka Firewall Settings & Advanced, tampilkan status

## Utility (`utils/powershell.py`)
- `run_powershell_command`, `run_cmd_command`
- Registry helper (`set_registry_value`, `get_registry_value`, `delete_registry_value`)
- SMB registry helpers (`set_smb_insecure_guest_auth`, `get_smb_insecure_guest_auth`, dll.)
- `get_firewall_status`

## Keamanan
- Cek hak admin pada startup, prompt UAC, peringatan bila tidak admin, banner status admin di UI.

## Konfigurasi Tersimpan (`config/smb_settings.json`)
```json
{
  "insecure_guest_logons": false,
  "client_require_security_signature": true,
  "server_require_security_signature": true,
  "last_updated": null
}
```

*Dokumen ini disimpan di folder `docs` untuk referensi pengembang.*
