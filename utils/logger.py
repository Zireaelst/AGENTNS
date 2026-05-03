"""utils/logger.py — Colored terminal output for demo clarity."""
import time

R = "\033[0m"
B = "\033[1m"

# ── V2 agent-label color map (used by V2 agents) ──────────────────
_AGENT_COLORS = {
    "scout":    ("\033[96m",  "SCOUT   "),   # cyan
    "strategy": ("\033[95m",  "STRATEGY"),   # magenta
    "executor": ("\033[92m",  "EXECUTOR"),   # green
    "ens":      ("\033[93m",  "ENS     "),   # yellow
    "axl":      ("\033[94m",  "AXL     "),   # blue
    "keeper":   ("\033[91m",  "KEEPER  "),   # red→green after success
    "sys":      ("\033[97m",  "SYS     "),   # white
}

# ── V1 compat: named color dict (used by demo_runner.py, agentns_cli.py) ──
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


def log(agent: str, msg: str, ok=True, color=None, **kwargs):
    """
    Log with agent label. Accepts either:
      - ok: bool (V2 style)
      - color: str (V1 compat, ignored in output)
    """
    ts = time.strftime("%H:%M:%S")
    col, label = _AGENT_COLORS.get(agent, ("\033[97m", agent.upper()[:8].ljust(8)))
    print(f"\033[90m[{ts}]\033[0m {col}{B}[{label}]{R} {col}{msg}{R}", flush=True)


def phase(title_or_num, total=None, icon=None, title=None):
    """
    V2: phase("Scout Cycle #1")
    V1 compat: phase(1, 5, "📛", "ENS Discovery")
    """
    if total is not None and title is not None:
        # V1 style
        actual_title = f"[Phase {title_or_num}/{total}] {icon} {title.upper()}"
    else:
        actual_title = title_or_num
    print(f"\n{B}\033[97m{'═'*55}{R}")
    print(f"{B}\033[93m  {actual_title}{R}")
    print(f"{B}\033[97m{'═'*55}{R}\n", flush=True)


def banner(title: str, subtitle: str = ""):
    print(f"\n{B}\033[96m╔{'═'*53}╗")
    print(f"║  {title:<51}║")
    if subtitle:
        print(f"║  {subtitle:<51}║")
    print(f"╚{'═'*53}╝{R}\n", flush=True)


# Alias for V1 compat
box = banner


def table(rows: list[tuple[str, str]]):
    w = max(len(k) for k, _ in rows) + 2
    print(f"  {B}┌{'─'*w}┬{'─'*35}┐{R}")
    for k, v in rows:
        print(f"  {B}│{R} {k:<{w-2}} {B}│{R} {v:<33} {B}│{R}")
    print(f"  {B}└{'─'*w}┴{'─'*35}┘{R}\n", flush=True)


# ── V1 compat functions (used by demo_runner.py, agentns_cli.py) ──

def separator(title: str = ""):
    print(f"\n{B}\033[97m{'─'*60}{R}")
    if title:
        print(f"{B}\033[93m  {title}{R}")
        print(f"{B}\033[97m{'─'*60}{R}\n")


def detail(agent: str, message: str, color: str = "white"):
    c = COLORS.get(color, COLORS["white"])
    print(f"          {c}   {message}{R}")


def success(message: str):
    print(f"   \033[92m✓ {message}{R}")


def warn(message: str):
    print(f"   \033[93m⚠ {message}{R}")


def error(message: str):
    print(f"   \033[91m✗ {message}{R}")


def info(message: str):
    print(f"   \033[96m→ {message}{R}")


def result_block(lines: list[str]):
    for line in lines:
        print(f"     \033[97m{line}{R}")
