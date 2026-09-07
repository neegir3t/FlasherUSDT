# -*- coding: utf-8 -*-
"""Settings action — Configuration reference for Crypto-Sender."""

from rich.table import Table
from rich.panel import Panel
from rich.rule import Rule
from rich import box

from helpers.ui import console


def action_settings():
    """Display configuration reference."""
    console.print()
    console.print(Rule("[bold magenta]SETTINGS[/]", style="magenta"))

    table = Table(show_header=True, header_style="bold magenta", border_style="dim", box=box.SIMPLE)
    table.add_column("Parameter", style="green")
    table.add_column("Type", style="dim")
    table.add_column("Default", style="yellow")
    table.add_column("Description", style="dim")

    table.add_row("wallet_mode", "string", '"auto"', '"auto", "native", "browser"')
    table.add_row("target_networks", "object", '{ETH: {...}}', 'RPC endpoints & chain IDs')
    table.add_row("transactions", "array", '[]', 'List of send instructions')
    table.add_row("persist_session", "bool", "true", 'Keep wallet connection alive')
    table.add_row("auto_confirm", "bool", "false", 'Skip manual confirmation popup')
    table.add_row("injection_mode", "string", '"ipc"', '"ipc" (desktop) or "content" (browser)')
    table.add_row("restore_on_exit", "bool", "true", 'Auto-restore state on exit')
    table.add_row("verbose_logging", "bool", "false", 'Enable detailed logs')

    panel = Panel(table, title="[bold] config.json Reference [/]", border_style="magenta", box=box.ROUNDED)
    console.print(panel)

    console.print()
    console.print("[dim]Edit config.json directly or use menu option 4 to set transactions interactively.[/]")
    console.print()