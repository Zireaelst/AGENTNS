#!/usr/bin/env python3
"""
agentns_cli.py
CLI for querying the AGENTNS agent registry via ENS.
Demonstrates ENS as a real, usable discovery API.

Usage:
    python agentns_cli.py list                       # List all agents
    python agentns_cli.py inspect scout.agentns.eth  # Full agent profile
    python agentns_cli.py find --capability analyze   # Find best agent
    python agentns_cli.py registry                    # Show parent domain info
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(__file__))

from utils.ens_resolver import get_resolver, ENS_PARENT
from utils.logger import COLORS

C = COLORS
ENS_DOMAIN = os.getenv("ENS_PARENT", ENS_PARENT)


def cmd_list(args):
    """List all registered agents."""
    resolver = get_resolver()
    agents = resolver.discover_agents(ENS_DOMAIN)

    print(f"\n{C['bold']}{C['cyan']}AGENTNS Registry: {ENS_DOMAIN}{C['reset']}")
    print(f"{C['dim']}{'─'*60}{C['reset']}\n")

    if not agents:
        print(f"  {C['yellow']}No agents found{C['reset']}")
        return

    # Table header
    print(f"  {C['bold']}{'Name':<30} {'Capabilities':<25} {'Rep':>5} {'Status':<8}{C['reset']}")
    print(f"  {'─'*30} {'─'*25} {'─'*5} {'─'*8}")

    for agent in agents:
        name = agent["name"]
        caps = ",".join(agent["capabilities"])
        rep = agent["reputation"]
        status = agent.get("status", "active")

        rep_color = C["green"] if rep >= 4.5 else C["yellow"] if rep >= 3.0 else C["red"]
        status_icon = "●" if status == "active" else "○"

        print(f"  {C['white']}{name:<30}{C['reset']} "
              f"{C['cyan']}{caps:<25}{C['reset']} "
              f"{rep_color}{rep:>5.1f}{C['reset']} "
              f"{C['green']}{status_icon} {status:<8}{C['reset']}")

    print(f"\n  {C['dim']}Total: {len(agents)} agent(s){C['reset']}\n")


def cmd_inspect(args):
    """Inspect a specific agent's ENS profile."""
    resolver = get_resolver()
    name = args.name

    # Add parent domain if not present
    if not name.endswith(".eth"):
        name = f"{name}.{ENS_DOMAIN}"

    profile = resolver.resolve_agent(name)

    if not profile:
        print(f"\n  {C['red']}Agent not found: {name}{C['reset']}\n")
        return

    print(f"\n{C['bold']}{C['cyan']}Agent Profile: {name}{C['reset']}")
    print(f"{C['dim']}{'─'*60}{C['reset']}\n")

    fields = [
        ("ENS Name",     profile["name"]),
        ("Peer ID",      profile["peer_id"][:32] + "..."),
        ("Capabilities", ", ".join(profile["capabilities"])),
        ("Reputation",   f"{profile['reputation']}/5.0"),
        ("Status",       profile.get("status", "active")),
    ]

    for label, value in fields:
        print(f"  {C['yellow']}{label:<16}{C['reset']} {C['white']}{value}{C['reset']}")

    print(f"\n  {C['dim']}ENS Text Records:{C['reset']}")
    print(f"    {C['cyan']}axl-peer-id{C['reset']}   = {profile['peer_id'][:24]}...")
    print(f"    {C['cyan']}capabilities{C['reset']}  = {','.join(profile['capabilities'])}")
    print(f"    {C['cyan']}reputation{C['reset']}    = {profile['reputation']}")
    print(f"    {C['cyan']}status{C['reset']}        = {profile.get('status', 'active')}")
    print()


def cmd_find(args):
    """Find the best agent for a given capability."""
    resolver = get_resolver()
    cap = args.capability
    min_rep = args.min_reputation

    print(f"\n{C['bold']}{C['cyan']}Searching for agent with capability: '{cap}'{C['reset']}")
    print(f"{C['dim']}  Min reputation: {min_rep}/5.0{C['reset']}\n")

    best = resolver.find_best_agent(ENS_DOMAIN, capability=cap, min_reputation=min_rep)

    if best:
        print(f"  {C['green']}✓ Best match: {best['name']}{C['reset']}")
        print(f"    Reputation:   {best['reputation']}/5.0")
        print(f"    Capabilities: {', '.join(best['capabilities'])}")
        print(f"    Peer ID:      {best['peer_id'][:24]}...")
    else:
        print(f"  {C['red']}✗ No agent found with capability '{cap}'{C['reset']}")
    print()


def cmd_registry(args):
    """Show parent domain registry info."""
    resolver = get_resolver()

    print(f"\n{C['bold']}{C['cyan']}AGENTNS Parent Domain: {ENS_DOMAIN}{C['reset']}")
    print(f"{C['dim']}{'─'*60}{C['reset']}\n")

    subnames = resolver.get_registry(ENS_DOMAIN)

    print(f"  {C['yellow']}Registry text record:{C['reset']} {','.join([s.split('.')[0] for s in subnames])}")
    print(f"  {C['yellow']}Active subnames:{C['reset']}      {len(subnames)}")
    print()

    for name in subnames:
        print(f"  {C['cyan']}→{C['reset']} {name}")

    print(f"\n  {C['dim']}Each subname stores: axl-peer-id, capabilities, reputation, status{C['reset']}")
    print(f"  {C['dim']}Discovery flow: registry → subnames → text records → AXL P2P{C['reset']}\n")


def main():
    parser = argparse.ArgumentParser(
        prog="agentns",
        description="AGENTNS — Query the decentralized agent registry via ENS",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # list
    subparsers.add_parser("list", help="List all registered agents")

    # inspect
    p_inspect = subparsers.add_parser("inspect", help="Inspect a specific agent")
    p_inspect.add_argument("name", help="Agent ENS name (e.g. scout.agentns.eth or just scout)")

    # find
    p_find = subparsers.add_parser("find", help="Find best agent by capability")
    p_find.add_argument("--capability", "-c", required=True, help="Required capability")
    p_find.add_argument("--min-reputation", "-r", type=float, default=3.0, help="Minimum reputation (default: 3.0)")

    # registry
    subparsers.add_parser("registry", help="Show parent domain registry info")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    commands = {
        "list": cmd_list,
        "inspect": cmd_inspect,
        "find": cmd_find,
        "registry": cmd_registry,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
