"""LAN address and Windows Firewall helpers for NexaFlow Remote Access."""

from __future__ import annotations

import ipaddress
import json
import os
import socket
import subprocess
from dataclasses import dataclass


_VIRTUAL_ADDRESS_PREFIXES = ("192.168.56.",)


def is_pairable_ipv4(address: str) -> bool:
    """Return whether an IPv4 address can reasonably be reached by a phone."""
    try:
        ip = ipaddress.ip_address(str(address).strip())
    except ValueError:
        return False
    if ip.version != 4 or not ip.is_private:
        return False
    if ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_unspecified:
        return False
    return not str(ip).startswith(_VIRTUAL_ADDRESS_PREFIXES)


def local_ipv4_candidates() -> list[str]:
    """Return phone-reachable IPv4 addresses with the active route first."""
    candidates: list[str] = []

    def add(address: str) -> None:
        address = str(address or "").strip()
        if is_pairable_ipv4(address) and address not in candidates:
            candidates.append(address)

    # UDP connect performs route selection without sending traffic.
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("192.0.2.1", 9))
            add(sock.getsockname()[0])
    except OSError:
        pass

    try:
        for item in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            add(item[4][0])
    except OSError:
        pass
    return candidates


def recommended_local_ipv4() -> str:
    candidates = local_ipv4_candidates()
    return candidates[0] if candidates else ""


@dataclass(frozen=True)
class FirewallRuleSpec:
    name: str
    port: int
    executable: str
    description: str


def firewall_rule_spec(port: int, executable: str, packaged: bool) -> FirewallRuleSpec:
    suffix = "" if packaged else " (Development)"
    return FirewallRuleSpec(
        name=f"NexaFlow Remote {int(port)}{suffix}",
        port=int(port),
        executable=os.path.normcase(os.path.abspath(executable)),
        description=(
            "NexaFlow local pairing only. Scoped to this app, the local subnet, "
            "and the Remote Access port."
        ),
    )


def _as_values(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def firewall_rule_matches(rule: dict, spec: FirewallRuleSpec) -> bool:
    """Validate normalized data returned by the PowerShell inspection script."""
    if not isinstance(rule, dict):
        return False
    enabled = str(rule.get("Enabled", "")).lower() in {"true", "1"}
    direction = str(rule.get("Direction", "")).lower()
    action = str(rule.get("Action", "")).lower()
    profile = str(rule.get("Profile", "")).lower().replace(" ", "")
    profile_ok = profile in {"any", "0", "domain,private,public", "private,public,domain"}
    protocols = {item.lower() for item in _as_values(rule.get("Protocol"))}
    ports = {item.lower() for item in _as_values(rule.get("LocalPort"))}
    remotes = {item.lower() for item in _as_values(rule.get("RemoteAddress"))}
    program = os.path.normcase(os.path.abspath(str(rule.get("Program", ""))))
    return (
        enabled
        and direction == "inbound"
        and action == "allow"
        and profile_ok
        and bool(protocols & {"tcp", "6"})
        and str(spec.port).lower() in ports
        and "localsubnet" in remotes
        and program == spec.executable
    )


def _ps_quote(value: str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def firewall_inspection_script(spec: FirewallRuleSpec) -> str:
    name = _ps_quote(spec.name)
    return (
        "$ErrorActionPreference='Stop';"
        f"$r=Get-NetFirewallRule -DisplayName {name} -ErrorAction SilentlyContinue | Select-Object -First 1;"
        "if($null -eq $r){'null';exit 0};"
        "$p=Get-NetFirewallPortFilter -AssociatedNetFirewallRule $r;"
        "$a=Get-NetFirewallAddressFilter -AssociatedNetFirewallRule $r;"
        "$x=Get-NetFirewallApplicationFilter -AssociatedNetFirewallRule $r;"
        "[pscustomobject]@{"
        "Enabled=[string]$r.Enabled;Direction=[string]$r.Direction;Action=[string]$r.Action;"
        "Profile=[string]$r.Profile;Protocol=@($p.Protocol);LocalPort=@($p.LocalPort);"
        "RemoteAddress=@($a.RemoteAddress);Program=[string]$x.Program"
        "}|ConvertTo-Json -Compress"
    )


def inspect_firewall_rule(spec: FirewallRuleSpec, timeout: int = 30) -> dict:
    if os.name != "nt":
        return {"status": "unsupported", "rule": None}
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", firewall_inspection_script(spec)],
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if result.returncode != 0:
            return {"status": "error", "error": (result.stderr or "Inspection failed").strip()}
        raw = (result.stdout or "").strip()
        rule = None if not raw or raw == "null" else json.loads(raw)
        if rule is None:
            return {"status": "missing", "rule": None}
        return {"status": "valid" if firewall_rule_matches(rule, spec) else "invalid", "rule": rule}
    except Exception as exc:
        return {"status": "error", "error": f"{type(exc).__name__}: {exc}"}


def firewall_repair_script(spec: FirewallRuleSpec) -> str:
    name = _ps_quote(spec.name)
    executable = _ps_quote(spec.executable)
    description = _ps_quote(spec.description)
    return (
        "$ErrorActionPreference='Stop';"
        f"$n={name};"
        "Get-NetFirewallRule -DisplayName $n -ErrorAction SilentlyContinue | Remove-NetFirewallRule;"
        "$p=@{DisplayName=$n;Direction='Inbound';Action='Allow';Enabled='True';"
        f"Profile='Any';Protocol='TCP';LocalPort={spec.port};RemoteAddress='LocalSubnet';"
        f"Program={executable};Description={description}}};"
        "New-NetFirewallRule @p | Out-Null"
    )
