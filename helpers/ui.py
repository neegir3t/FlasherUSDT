# -*- coding: utf-8 -*-
"""Crypto-Sender — Rich terminal UI with tables, banners, and status displays."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.rule import Rule
from rich import box

console = Console(force_terminal=True, color_system="auto")

# ASCII Art Logo — Crypto-Sender

def print_banner():
    """Print main banner with logo and tagline."""
    panel = Panel(
        Text.from_markup(
            f"[bold magenta]{LOGO}[/]\n\n"
            "[bold white]U N I V E R S A L   T R A N S A C T I O N   D I S P A T C H E R[/]\n"
            "[dim]Native & Browser Wallets  |  30+ Networks  |  Batch Sends  |  Windows[/]"
        ),
        box=box.ROUNDED,
        border_style="magenta",
        padding=(0, 2),
        title="[bold white on magenta] CRYPTO‑SENDER [/]",
        title_align="center",
    )
    console.print(panel)


def show_menu_table(menu_items: list) -> str:
    """Display interactive menu table and return user choice."""
    console.print()
    console.print(Rule("[bold magenta]MENU[/]", style="magenta"))
    table = Table(
        show_header=True,
        header_style="bold magenta",
        border_style="dim",
        box=box.SIMPLE,
        expand=True,
    )
    table.add_column("[#]", style="bold", justify="center", width=4)
    table.add_column("Action", style="green")
    table.add_column("Description", style="dim")

    for key, action, desc in menu_items:
        table.add_row(key, action, desc)

    console.print(table)
    return console.input("\n[bold magenta]Select action [#]: [/]").strip()


def show_load_status_table(config: dict):
    """Display load status with key config parameters."""
    console.print()
    console.print(Rule("[bold magenta]STATUS[/]", style="magenta"))
    table = Table(
        show_header=True,
        header_style="bold magenta",
        border_style="dim",
        box=box.SIMPLE,
    )
    table.add_column("Parameter", style="green")
    table.add_column("Value", justify="center")
    table.add_column("Status", justify="center", style="bold")

    wallet_mode = config.get("wallet_mode", "auto")
    txs = config.get("transactions", [])
    table.add_row("Wallet Mode", str(wallet_mode), "[green]AUTO[/]" if wallet_mode == "auto" else "[cyan]CUSTOM[/]")
    table.add_row("Transactions", str(len(txs)), "[green]OK[/]" if txs else "[red]NONE[/]")
    table.add_row("Injection Mode", config.get("injection_mode", "ipc"), "[green]READY[/]")
    table.add_row("Persistence", "ON" if config.get("persist_session") else "OFF",
                  "[green]✓[/]" if config.get("persist_session") else "[dim]—[/]")

    console.print(table)
    console.print()


def show_transaction_table(rows: list):
    """Display a table of configured transactions."""
    console.print()
    console.print(Rule("[bold magenta]TRANSACTIONS[/]", style="magenta"))
    table = Table(
        show_header=True,
        header_style="bold magenta",
        border_style="dim",
        box=box.SIMPLE,
    )
    table.add_column("#", style="dim", justify="right", width=3)
    table.add_column("Asset", style="cyan")
    table.add_column("Recipient", style="yellow")
    table.add_column("Amount", style="green", justify="right")

    for row in rows:
        table.add_row(*row)

    console.print(table)
    console.print()


def show_status_table(rows: list):
    """Display a status table (for hook/connection status)."""
    console.print()
    console.print(Rule("[bold magenta]STATUS CHECK[/]", style="magenta"))
    table = Table(
        show_header=True,
        header_style="bold magenta",
        border_style="dim",
        box=box.SIMPLE,
    )
    table.add_column("Component", style="green")
    table.add_column("Value", justify="center", style="cyan")
    table.add_column("State", justify="center")

    for row in rows:
        table.add_row(*row)

    console.print(table)
    console.print()


def print_success(msg: str):
    console.print(f"[green]✓[/] {msg}")


def print_error(msg: str):
    console.print(f"[red]✗[/] {msg}")


def print_info(msg: str):
    console.print(f"[cyan]i[/] {msg}")


def print_warning(msg: str):
    console.print(f"[yellow]![/] {msg}")


def separator(char: str = "─", length: int = 58):
    """Print a Rich Rule separator."""
    console.print(Rule(style="dim"))


def progress_bar(current: int, total: int, width: int = 30, prefix: str = ""):
    """
    Display a progress bar.

    Args:
        current: Current step (0-based)
        total: Total steps
        width: Bar width in characters
        prefix: Text to display before the bar
    """
    filled = int(width * current / total) if total > 0 else 0
    pct = (current / total * 100) if total > 0 else 0
    bar = "█" * filled + "░" * (width - filled)
    console.print(f"\r{prefix}[magenta]{bar}[/] [dim]{pct:.0f}%[/]", end="")