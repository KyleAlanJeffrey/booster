#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os
import re
from pathlib import Path

# Defaults
DEFAULT_TARGET = "booster@192.168.10.102"
DEFAULT_PUBKEY = "~/.ssh/id_rsa.pub"
DEFAULT_HOST_ALIAS = "booster-wifi"


def run_interactive_nmtui(target: str) -> int:
    return subprocess.call(["ssh", "-tt", target, "sudo", "nmtui"])


def copy_ssh_key(target: str, pubkey_path: str):
    pubkey_path = os.path.expanduser(pubkey_path)

    if not os.path.exists(pubkey_path):
        raise FileNotFoundError(f"Public key not found: {pubkey_path}")

    print(f"\nCopying SSH public key ({pubkey_path}) to {target}...\n")
    subprocess.check_call([
        "ssh-copy-id",
        "-i", pubkey_path,
        target
    ])


def get_remote_ip(target: str) -> tuple[str, str]:
    """
    Returns (ip, interface) from the remote host.
    Robust against extra SSH banner/MOTD output by parsing the last non-empty line.
    """
    remote_cmd = r"""
set -e
IFACE="$(ip route show default 0.0.0.0/0 | awk '{print $5}' | head -n1)"
IP="$(ip -4 addr show dev "$IFACE" | awk '/inet /{print $2}' | cut -d/ -f1 | head -n1)"
echo "$IP $IFACE"
"""
    out = subprocess.check_output(
        ["ssh", "-t", target, "bash", "-lc", remote_cmd],
        text=True
    )

    # Take the last non-empty line (avoids MOTD/banner/extra ssh noise)
    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    if not lines:
        raise RuntimeError("No output received while determining remote IP")

    last = lines[-1]
    parts = last.split(maxsplit=1)
    if len(parts) != 2:
        raise RuntimeError(f"Unexpected IP output line: {last!r}")

    ip, iface = parts[0], parts[1]
    return ip, iface

def update_ssh_config(
    host_alias: str,
    hostname: str,
    user: str,
    identity_file: str | None,
):
    ssh_dir = Path.home() / ".ssh"
    ssh_dir.mkdir(mode=0o700, exist_ok=True)

    config_path = ssh_dir / "config"
    existing = config_path.read_text() if config_path.exists() else ""

    identity_file = os.path.expanduser(identity_file) if identity_file else None

    new_block = [
        f"Host {host_alias}",
        f"    HostName {hostname}",
        f"    User {user}",
    ]
    if identity_file:
        new_block.append(f"    IdentityFile {identity_file}")
    new_block.append("")  # trailing newline

    new_block_text = "\n".join(new_block)

    # Regex to replace existing Host block
    pattern = re.compile(
        rf"^Host\s+{re.escape(host_alias)}\b.*?(?=^Host\s+|\Z)",
        re.MULTILINE | re.DOTALL
    )

    if pattern.search(existing):
        updated = pattern.sub(new_block_text, existing)
        print(f"Updated existing SSH config entry: Host {host_alias}")
    else:
        updated = existing.rstrip() + "\n\n" + new_block_text
        print(f"Added new SSH config entry: Host {host_alias}")

    config_path.write_text(updated)
    os.chmod(config_path, 0o600)


def main():
    parser = argparse.ArgumentParser(
        description="SSH into booster, run nmtui, copy SSH key, print IP, update SSH config"
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=DEFAULT_TARGET,
        help=f"SSH target (default: {DEFAULT_TARGET})"
    )
    parser.add_argument(
        "--pubkey",
        default=DEFAULT_PUBKEY,
        help=f"Path to SSH public key (default: {DEFAULT_PUBKEY})"
    )
    parser.add_argument(
        "--ssh-host-alias",
        default=DEFAULT_HOST_ALIAS,
        help=f"SSH config Host alias (default: {DEFAULT_HOST_ALIAS})"
    )
    parser.add_argument(
        "--add-ssh-config",
        action="store_true",
        help="Add/update ~/.ssh/config entry after Wi-Fi setup"
    )
    parser.add_argument(
        "--identity-file",
        default=None,
        help="IdentityFile to set in ~/.ssh/config (optional)"
    )

    args = parser.parse_args()

    # Parse user from target (user@host)
    if "@" not in args.target:
        print("ERROR: target must be in the form user@host", file=sys.stderr)
        sys.exit(1)
    user, _ = args.target.split("@", 1)

    # 1) Run nmtui
    rc = run_interactive_nmtui(args.target)

    # 2) Copy SSH key
    try:
        copy_ssh_key(args.target, args.pubkey)
    except Exception as e:
        print(f"WARNING: Failed to copy SSH key: {e}")

    # 3) Get new IP
    try:
        ip, iface = get_remote_ip(args.target)
        print(f"\nBooster IP after nmtui: {ip} ({iface})\n")
    except Exception as e:
        print("Failed to get remote IP:", e)
        sys.exit(rc)

    # 4) Update local SSH config
    if args.add_ssh_config:
        update_ssh_config(
            host_alias=args.ssh_host_alias,
            hostname=ip,
            user=user,
            identity_file=args.identity_file,
        )

        print(f"\nYou can now SSH with:\n  ssh {args.ssh_host_alias}\n")

    sys.exit(rc)


if __name__ == "__main__":
    main()