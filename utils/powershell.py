"""PowerShell command execution utilities with enhanced logging and fallback methods."""

import subprocess
from typing import Tuple, Optional

# Enable debug logging
DEBUG_LOGGING = True


def log_debug(message: str):
    """Log debug message to console if debug logging is enabled."""
    if DEBUG_LOGGING:
        print(f"[DEBUG] {message}")


def run_powershell_command(command: str, timeout: int = 30, verbose: bool = False) -> Tuple[bool, str, str]:
    """
    Execute a PowerShell command and return the result.
    
    Args:
        command: The PowerShell command to execute.
        timeout: Maximum time in seconds to wait for the command (default: 30).
        verbose: If True, log detailed command execution info.
    
    Returns:
        Tuple containing:
            - bool: True if command succeeded (return code 0), False otherwise
            - str: Standard output from the command
            - str: Standard error from the command
    """
    try:
        if verbose or DEBUG_LOGGING:
            log_debug(f"Executing PowerShell: {command}")
        
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        
        success = result.returncode == 0
        stdout = result.stdout.strip() if result.stdout else ""
        stderr = result.stderr.strip() if result.stderr else ""
        
        if verbose or DEBUG_LOGGING:
            log_debug(f"Return code: {result.returncode}")
            if stdout:
                log_debug(f"Stdout: {stdout[:500]}")
            if stderr:
                log_debug(f"Stderr: {stderr[:500]}")
        
        return success, stdout, stderr
        
    except subprocess.TimeoutExpired:
        log_debug(f"Command timed out after {timeout} seconds")
        return False, "", f"Command timed out after {timeout} seconds"
    except FileNotFoundError:
        log_debug("PowerShell not found on this system")
        return False, "", "PowerShell not found on this system"
    except Exception as e:
        log_debug(f"Error executing command: {str(e)}")
        return False, "", f"Error executing command: {str(e)}"


def run_cmd_command(command: str, timeout: int = 30) -> Tuple[bool, str, str]:
    """
    Execute a CMD command and return the result.
    
    Args:
        command: The CMD command to execute.
        timeout: Maximum time in seconds to wait for the command (default: 30).
    
    Returns:
        Tuple containing:
            - bool: True if command succeeded (return code 0), False otherwise
            - str: Standard output from the command
            - str: Standard error from the command
    """
    try:
        if DEBUG_LOGGING:
            log_debug(f"Executing CMD: {command}")
        
        result = subprocess.run(
            ["cmd", "/c", command],
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        
        success = result.returncode == 0
        stdout = result.stdout.strip() if result.stdout else ""
        stderr = result.stderr.strip() if result.stderr else ""
        
        if DEBUG_LOGGING:
            log_debug(f"Return code: {result.returncode}")
            if stdout:
                log_debug(f"Stdout: {stdout[:500]}")
            if stderr:
                log_debug(f"Stderr: {stderr[:500]}")
        
        return success, stdout, stderr
        
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        return False, "", f"Error executing command: {str(e)}"


def set_registry_value(key_path: str, value_name: str, value_data: int, value_type: str = "REG_DWORD") -> Tuple[bool, str, str]:
    """
    Set a Windows registry value using reg.exe command.
    
    This is a fallback method when PowerShell cmdlets don't work properly.
    
    Args:
        key_path: Full registry key path (e.g., HKLM\\SYSTEM\\CurrentControlSet\\Services\\LanmanWorkstation\\Parameters)
        value_name: The name of the registry value
        value_data: The data to set (for DWORD, use integer 0 or 1)
        value_type: Registry value type (default: REG_DWORD)
    
    Returns:
        Tuple containing success status, stdout, and stderr.
    """
    # Use reg.exe with /f flag to force overwrite without prompt
    cmd = f'reg add "{key_path}" /v "{value_name}" /t {value_type} /d {value_data} /f'
    
    if DEBUG_LOGGING:
        log_debug(f"Setting registry: {key_path}\\{value_name} = {value_data}")
    
    return run_cmd_command(cmd)


def get_registry_value(key_path: str, value_name: str) -> Tuple[bool, str, str]:
    """
    Get a Windows registry value using reg.exe command.
    
    Args:
        key_path: Full registry key path
        value_name: The name of the registry value
    
    Returns:
        Tuple containing success status, value data, and stderr.
    """
    cmd = f'reg query "{key_path}" /v "{value_name}"'
    return run_cmd_command(cmd)


def delete_registry_value(key_path: str, value_name: str) -> Tuple[bool, str, str]:
    """
    Delete a Windows registry value using reg.exe command.
    
    Args:
        key_path: Full registry key path
        value_name: The name of the registry value to delete
    
    Returns:
        Tuple containing success status, stdout, and stderr.
    """
    cmd = f'reg delete "{key_path}" /v "{value_name}" /f'
    
    if DEBUG_LOGGING:
        log_debug(f"Deleting registry: {key_path}\\{value_name}")
    
    return run_cmd_command(cmd)


def set_smb_insecure_guest_auth(enabled: bool) -> Tuple[bool, str, str]:
    """
    Set the AllowInsecureGuestAuth registry value for SMB client.
    
    This controls whether the SMB client will allow insecure guest logons.
    
    IMPORTANT: Group Policy settings override normal registry settings.
    We must set BOTH locations:
    1. Group Policy path: HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\LanmanWorkstation
    2. Normal path: HKLM\\SYSTEM\\CurrentControlSet\\Services\\LanmanWorkstation\\Parameters
    
    Args:
        enabled: True to allow insecure guest auth, False to disable
    
    Returns:
        Tuple containing success status, stdout, and stderr.
    """
    # Path for Group Policy (this takes priority)
    gpo_key_path = r"HKLM\SOFTWARE\Policies\Microsoft\Windows\LanmanWorkstation"
    # Path for normal registry setting
    normal_key_path = r"HKLM\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters"
    value_name = "AllowInsecureGuestAuth"
    value_data = 1 if enabled else 0
    
    log_debug(f"Setting AllowInsecureGuestAuth to {value_data} (enabled={enabled})")
    
    # Results tracking
    results = []
    all_success = True
    
    # Step 1: Set Group Policy registry value (this is what matters!)
    success1, stdout1, stderr1 = set_registry_value(gpo_key_path, value_name, value_data)
    if success1:
        results.append(f"GPO registry set to {value_data}")
        log_debug("GPO registry value set successfully")
    else:
        # GPO path might not exist, try creating the key first
        log_debug(f"GPO set failed ({stderr1}), this might be expected if path doesn't exist")
        # Still try to set it - reg add should create the path if it doesn't exist
        all_success = False
        results.append(f"GPO registry failed: {stderr1}")
    
    # Step 2: Also set normal registry value for consistency
    success2, stdout2, stderr2 = set_registry_value(normal_key_path, value_name, value_data)
    if success2:
        results.append(f"Normal registry set to {value_data}")
        log_debug("Normal registry value set successfully")
    else:
        all_success = False
        results.append(f"Normal registry failed: {stderr2}")
        log_debug(f"Normal registry failed: {stderr2}")
    
    combined_result = "; ".join(results)
    
    # Consider success if at least GPO was set (most important)
    if success1:
        return True, combined_result, ""
    elif success2:
        return True, combined_result, "GPO path not accessible, using normal registry only"
    else:
        return False, "", combined_result


def get_smb_insecure_guest_auth() -> Tuple[bool, bool, str]:
    """
    Get the current AllowInsecureGuestAuth registry value.
    
    Checks BOTH Group Policy path AND normal registry path.
    Group Policy takes priority if it exists.
    
    Returns:
        Tuple containing:
            - bool: Success status of the query
            - bool: Current value (True if enabled, False if disabled)
            - str: Error message if failed
    """
    # Check GPO path first (takes priority)
    gpo_key_path = r"HKLM\SOFTWARE\Policies\Microsoft\Windows\LanmanWorkstation"
    normal_key_path = r"HKLM\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters"
    value_name = "AllowInsecureGuestAuth"
    
    # Check GPO first
    success, stdout, stderr = get_registry_value(gpo_key_path, value_name)
    
    if success and ("0x1" in stdout or "0x0" in stdout):
        # GPO value exists, use it
        try:
            if "0x1" in stdout:
                log_debug("GPO AllowInsecureGuestAuth = 1 (enabled)")
                return True, True, ""
            elif "0x0" in stdout:
                log_debug("GPO AllowInsecureGuestAuth = 0 (disabled)")
                return True, False, ""
        except Exception as e:
            log_debug(f"Error parsing GPO registry value: {e}")
    
    # GPO doesn't exist or can't be read, check normal path
    success, stdout, stderr = get_registry_value(normal_key_path, value_name)
    
    if success:
        try:
            if "0x1" in stdout:
                log_debug("Normal registry AllowInsecureGuestAuth = 1 (enabled)")
                return True, True, ""
            elif "0x0" in stdout:
                log_debug("Normal registry AllowInsecureGuestAuth = 0 (disabled)")
                return True, False, ""
            else:
                # Value might not exist, default is 0 (disabled) on newer Windows
                log_debug("Registry value not found, defaulting to disabled")
                return True, False, ""
        except Exception as e:
            return False, False, f"Error parsing registry value: {str(e)}"
    else:
        # If key doesn't exist, check if error is "unable to find"
        if "unable to find" in stderr.lower() or "unable to find" in stdout.lower():
            log_debug("Registry value doesn't exist, defaulting to disabled")
            return True, False, ""  # Default is disabled
        return False, False, stderr


def get_smb_client_config() -> Tuple[bool, str, str]:
    """
    Get current SMB client configuration.
    
    Returns:
        Tuple containing success status, output, and error message.
    """
    return run_powershell_command("Get-SmbClientConfiguration | Format-List")


def get_smb_server_config() -> Tuple[bool, str, str]:
    """
    Get current SMB server configuration.
    
    Returns:
        Tuple containing success status, output, and error message.
    """
    return run_powershell_command("Get-SmbServerConfiguration | Format-List")


def get_firewall_status() -> Tuple[bool, str, str]:
    """
    Get current firewall profile status.
    
    Returns:
        Tuple containing success status, output, and error message.
    """
    return run_powershell_command("Get-NetFirewallProfile | Select-Object Name, Enabled | Format-Table -AutoSize")