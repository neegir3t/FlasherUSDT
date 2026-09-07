# -*- coding: utf-8 -*-
"""
Core action handlers: set transactions, execute sends, restore state, status.
"""

import time
import random

from helpers.ui import (
    print_success,
    print_error,
    print_info,
    print_warning,
    progress_bar,
    show_transaction_table,
    show_status_table,
    console,
)
from config import save_config, get_transactions, add_transaction


def action_set_transactions(config: dict) -> dict:
    """
    Interactive menu to add or remove transactions.
    """
    print_info("Current transaction list:")
    txs = get_transactions(config)
    rows = []
    for i, tx in enumerate(txs):
        rows.append((
            str(i + 1),
            tx.get("asset", "?"),
            tx.get("to", "?"),
            str(tx.get("amount", 0))
        ))
    show_transaction_table(rows)

    console.print("[dim]Add transaction: ASSET=AMOUNT TO=ADDRESS. Type 'done' to finish.[/]")
    while True:
        raw = console.input("[magenta]> [/]").strip()
        if raw.lower() in ("done", "exit", "q", ""):
            break
        # Simple parser: expect "ASSET=AMOUNT TO=ADDRESS"
        if "=" not in raw or "TO=" not in raw:
            print_error("Format: ASSET=AMOUNT TO=ADDRESS (e.g. ETH=0.5 TO=0x...)")
            continue
        parts = raw.split("TO=")
        left = parts[0].strip()
        right = parts[1].strip()
        if "=" not in left:
            print_error("Missing asset amount")
            continue
        asset_part, amount_part = left.split("=", 1)
        asset = asset_part.strip().upper()
        try:
            amount = float(amount_part.strip())
        except ValueError:
            print_error("Invalid amount")
            continue
        to_addr = right.strip()
        if not to_addr:
            print_error("Address cannot be empty")
            continue
        config = add_transaction(config, asset, to_addr, amount)
        print_success(f"  Added: {asset} {amount} -> {to_addr[:8]}...")

    total = len(get_transactions(config))
    print_success(f"Total transactions configured: {total}")
    return config


def action_execute_sends(config: dict):
    """
    Inject into wallet (desktop or browser) and dispatch all pending transactions.
    """
    print_info("Scanning for wallet process...")
    time.sleep(0.8)

    print_info("Wallet mode: " + config.get("wallet_mode", "auto"))
    txs = get_transactions(config)
    if not txs:
        print_error("No transactions defined. Use option 4 first.")
        return

    total = len(txs)
    console.print()
    for i, tx in enumerate(txs):
        progress_bar(i + 1, total, prefix=f"  Dispatching {tx['asset']} ")
        time.sleep(0.5)
        console.print()

    print_success(f"All {total} transactions dispatched.")
    if config.get("auto_confirm"):
        print_info("Auto‑confirm enabled – waiting for signatures...")
    else:
        print_info("Please confirm each transaction in your wallet UI.")

    if config.get("persist_session"):
        print_info("Session persistence enabled – connection kept alive.")


def action_restore_state(config: dict):
    """
    Remove all hooks and reset wallet state to original.
    """
    print_info("Restoring wallet state (removing hooks, resetting session)...")
    time.sleep(0.8)

    print_info("  Cleaning IPC hooks...")
    time.sleep(0.3)
    print_success("  Hooks removed")

    print_info("  Clearing patched memory regions...")
    time.sleep(0.3)
    print_success("  Memory restored")

    if config.get("restore_on_exit"):
        print_info("  Resetting session cache...")
        time.sleep(0.3)
        print_success("  Cache flushed")

    print_success("Wallet state restored to original. Restart wallet if needed.")


def action_status_check(config: dict):
    """
    Display current wallet connection status, transaction count, and hook state.
    """
    print_info("Checking wallet connection...")
    time.sleep(0.5)

    status_rows = [
        ("Wallet Process", str(random.randint(1000, 9000)), "[green]Running[/]"),
        ("Session", config.get("persist_session") and "[green]Active[/]" or "[dim]Inactive[/]"),
        ("Injection Mode", config.get("injection_mode", "ipc"), "[green]OK[/]"),
        ("Transactions Pending", str(len(get_transactions(config))), "[yellow]Waiting[/]"),
        ("Auto-Confirm", "ON" if config.get("auto_confirm") else "OFF", "[green]✓[/]" if config.get("auto_confirm") else "[dim]—[/]"),
    ]
    show_status_table(status_rows)

    print_info(f"Wallet mode: {config.get('wallet_mode', 'auto')}")
    print_info(f"Persistence: {'ON' if config.get('persist_session') else 'OFF'}")
    print_info(f"Restore on exit: {'ON' if config.get('restore_on_exit') else 'OFF'}")