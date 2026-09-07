# -*- coding: utf-8 -*-
"""About action — Features, supported assets, contact."""

from rich.table import Table
from rich.panel import Panel
from rich.rule import Rule
from rich import box

from helpers.ui import console


def action_about():
    """Display project info."""
    console.print()
    console.print(Rule("[bold magenta]ABOUT[/]", style="magenta"))

    # Features table
    features_table = Table(show_header=True, header_style="bold magenta", border_style="dim", box=box.SIMPLE)
    features_table.add_column("Feature", style="green")
    features_table.add_column("Status", justify="center")

    features = [
        "Send BTC, ETH, SOL, BNB, XRP, ADA, DOGE & 200+ tokens",
        "Native desktop wallet integration (Electron, Qt, C++)",
        "Browser extension injection (MetaMask, Phantom, Keplr)",
        "Custom RPC endpoints for any EVM or non‑EVM chain",
        "Batch transaction dispatching",
        "Persistent session handling",
        "Screenshot‑safe UI (no visible hooks)",
        "Multi‑signature & hardware wallet fallback",
        "Windows‑native process injection (IPC & memory hooks)",
        "Auto‑detect wallet installation and process",
        "One‑click apply / restore state",
        "No private key access – uses wallet signing only",
    ]
    for feat in features:
        features_table.add_row(feat, "[green]✓[/]")

    # Supported networks table
    networks_table = Table(show_header=True, header_style="bold magenta", border_style="dim", box=box.SIMPLE)
    networks_table.add_column("Network", style="green")
    networks_table.add_column("Assets", style="cyan")
    networks_table.add_row("EVM (Ethereum, BSC, Polygon, Avalanche, Arbitrum, Optimism)",
                           "ETH, USDT, USDC, DAI, UNI, AAVE, LINK, MATIC, AVAX, BNB, ARB, OP")
    networks_table.add_row("Solana", "SOL, USDC, BONK, RAY, ORCA")
    networks_table.add_row("Bitcoin", "BTC, LTC, DOGE, DASH")
    networks_table.add_row("XRP Ledger", "XRP")
    networks_table.add_row("Cosmos", "ATOM, OSMO, JUNO")
    networks_table.add_row("Polkadot", "DOT")
    networks_table.add_row("Cardano", "ADA")
    networks_table.add_row("Privacy", "XMR, ZEC, DASH (via native wallets)")

    # Contact table
    contact_table = Table(show_header=True, header_style="bold magenta", border_style="dim", box=box.SIMPLE)
    contact_table.add_column("Channel", style="green")
    contact_table.add_column("Value", style="cyan")
    contact_table.add_row("Telegram", "JOIN OUR TELEGRAM CHAT")
    contact_table.add_row("ETH Donation", "0x9E3d7A1c82B45f06Da4e28C1F53b90d2A17cE645")
    contact_table.add_row("Support", "GitHub Issues or Telegram")

    console.print(Panel(features_table, title="[bold] Features [/]", border_style="magenta", box=box.ROUNDED))
    console.print()
    console.print(Panel(networks_table, title="[bold] Supported Networks & Assets [/]", border_style="magenta", box=box.ROUNDED))
    console.print()
    console.print(Panel(contact_table, title="[bold] Contact [/]", border_style="magenta", box=box.ROUNDED))
    console.print()
    console.print("[bold magenta]Contribution:[/] Don't forget to put stars ⭐")
    console.print("[dim]Windows‑only (x64). Questions? Contact via Telegram or Issues.[/]")
    console.print()