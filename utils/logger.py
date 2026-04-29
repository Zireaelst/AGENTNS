"""
utils/logger.py
Clean colored terminal output for demo visibility.
Upgraded with phase headers, detail logging, and box titles.
"""

import time

COLORS = {
    "cyan":    "\033[96m",
    "green":   "\033[92m",
    "yellow":  "\033[93m",
    "red":     "\033[91m",
    "magenta": "\033[95m",
    "white":   "\033[97m",
    "blue":    "\033[94m",
    "reset":   "\033[0m",
    "bold":    "\033[1m",
    "dim":     "\033[2m",
}

AGENT_COLORS = {
    "scout":    "cyan",
    "strategy": "magenta",
    "executor": "green",
    "ens":      "yellow",
    "system":   "blue",
    "keeperhub": "green",
}

AGENT_ICONS = {
    "scout":    "🔍",
    "strategy": "🧠",
    "executor": "⚡",
    "ens":      "📛",
    "system":   "🟣",
    "keeperhub": "🔗",
}


def log(agent: str, message: str, color: str = "white"):
    """Standard log line with timestamp and agent tag."""
    ts = time.strftime("%H:%M:%S")
    c = COLORS.get(color, COLORS["white"])
    agent_color = COLORS.get(AGENT_COLORS.get(agent, "white"), COLORS["white"])
    reset = COLORS["reset"]
    bold = COLORS["bold"]
    icon = AGENT_ICONS.get(agent, "●")
    print(f"{COLORS['dim']}[{ts}]{reset} {bold}{agent_color}{icon} [{agent.upper()}]{reset} {c}{message}{reset}")


def detail(agent: str, message: str, color: str = "white"):
    """Indented sub-step log for detail within a phase."""
    c = COLORS.get(color, COLORS["white"])
    reset = COLORS["reset"]
    print(f"          {c}   {message}{reset}")


def separator(title: str = ""):
    """Section divider with optional title."""
    print(f"\n{COLORS['bold']}{COLORS['white']}{'─'*60}{COLORS['reset']}")
    if title:
        print(f"{COLORS['bold']}{COLORS['yellow']}  {title}{COLORS['reset']}")
        print(f"{COLORS['bold']}{COLORS['white']}{'─'*60}{COLORS['reset']}\n")


def phase(number: int, total: int, icon: str, title: str):
    """Phase header for demo narrative."""
    reset = COLORS["reset"]
    bold = COLORS["bold"]
    cyan = COLORS["cyan"]
    dim = COLORS["dim"]
    print(f"\n{bold}{cyan}[Phase {number}/{total}] {icon} {title.upper()}{reset}")
    print(f"{dim}{'─'*60}{reset}")


def box(title: str, subtitle: str = ""):
    """Boxed title for major sections."""
    reset = COLORS["reset"]
    bold = COLORS["bold"]
    cyan = COLORS["cyan"]
    width = 60
    print(f"\n{bold}{cyan}╔{'═'*width}╗{reset}")
    print(f"{bold}{cyan}║  {title:<{width-2}}║{reset}")
    if subtitle:
        print(f"{bold}{cyan}║  {subtitle:<{width-2}}║{reset}")
    print(f"{bold}{cyan}╚{'═'*width}╝{reset}")


def success(message: str):
    """Green success message."""
    print(f"   {COLORS['green']}✓ {message}{COLORS['reset']}")


def warn(message: str):
    """Yellow warning message."""
    print(f"   {COLORS['yellow']}⚠ {message}{COLORS['reset']}")


def error(message: str):
    """Red error message."""
    print(f"   {COLORS['red']}✗ {message}{COLORS['reset']}")


def info(message: str):
    """Cyan info message."""
    print(f"   {COLORS['cyan']}→ {message}{COLORS['reset']}")


def result_block(lines: list[str]):
    """Print a block of result lines, indented."""
    for line in lines:
        print(f"     {COLORS['white']}{line}{COLORS['reset']}")
