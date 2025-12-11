"""Admin privilege checking and elevation utilities."""

import ctypes
import sys


def is_admin() -> bool:
    """
    Check if the current process has administrator privileges.
    
    Returns:
        bool: True if running as admin, False otherwise.
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except (AttributeError, OSError):
        return False


def run_as_admin() -> bool:
    """
    Request to run the current script with administrator privileges using UAC.
    
    Returns:
        bool: True if elevation was requested successfully, False otherwise.
    """
    if is_admin():
        return True
    
    try:
        # Get the current script path and arguments
        script = sys.executable
        params = ' '.join([f'"{arg}"' for arg in sys.argv])
        
        # Use ShellExecuteW to request elevation
        result = ctypes.windll.shell32.ShellExecuteW(
            None,           # hwnd
            "runas",        # lpOperation - request elevation
            script,         # lpFile - the executable
            params,         # lpParameters - script arguments
            None,           # lpDirectory
            1               # nShowCmd - SW_SHOWNORMAL
        )
        
        # ShellExecuteW returns > 32 on success
        return result > 32
    except (AttributeError, OSError) as e:
        print(f"Failed to request elevation: {e}")
        return False


def get_admin_status_message() -> str:
    """
    Get a human-readable message about the current admin status.
    
    Returns:
        str: Status message indicating admin privileges.
    """
    if is_admin():
        return "✓ Running with Administrator privileges"
    else:
        return "⚠ Not running as Administrator - Some features may not work"