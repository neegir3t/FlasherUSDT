# -*- coding: utf-8 -*-
"""
Configuration loader for Crypto-Sender.
Manages wallet mode, RPC endpoints, transaction list, and runtime flags.
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).parent

_DEFAULTS = {
    "wallet_mode": "auto",                 # "auto", "native", "browser"
    "target_networks": {
        "ETH": {
            "rpc": "https://mainnet.infura.io/v3/demo",
            "chain_id": 1
        },
        "SOL": {
            "rpc": "https://api.mainnet-beta.solana.com"
        },
        "BTC": {
            "rpc": "https://blockstream.info/api"
        },
        "BNB": {
            "rpc": "https://bsc-dataseed.binance.org",
            "chain_id": 56
        },
        "MATIC": {
            "rpc": "https://polygon-rpc.com",
            "chain_id": 137
        }
    },
    "transactions": [
        {
            "asset": "ETH",
            "to": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            "amount": 0.01,
            "gas_price": "auto"
        },
        {
            "asset": "SOL",
            "to": "8xY7KZ...",
            "amount": 1.5
        }
    ],
    "persist_session": True,
    "auto_confirm": False,
    "injection_mode": "ipc",               # "ipc" (desktop) or "content" (browser)
    "restore_on_exit": True,
    "verbose_logging": False
}


def load_config() -> dict:
    """
    Load configuration from config.json with fallback to defaults.
    Creates config.json if missing.
    """
    config_path = BASE_DIR / "config.json"
    if not config_path.exists():
        save_config(_DEFAULTS)
        return dict(_DEFAULTS)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        merged = dict(_DEFAULTS)
        merged.update(data)
        return merged
    except (json.JSONDecodeError, IOError) as e:
        # If corrupt, return defaults and warn (handled by caller)
        return dict(_DEFAULTS)


def save_config(config: dict) -> None:
    """Save configuration to config.json with pretty formatting."""
    config_path = BASE_DIR / "config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


def get_transactions(config: dict) -> list:
    """Return the list of configured transactions."""
    return config.get("transactions", [])


def add_transaction(config: dict, asset: str, to: str, amount: float,
                    gas_price: str = "auto") -> dict:
    """
    Add a new transaction to the configuration and save.
    Returns updated config dict.
    """
    if "transactions" not in config:
        config["transactions"] = []
    config["transactions"].append({
        "asset": asset.upper(),
        "to": to.strip(),
        "amount": amount,
        "gas_price": gas_price
    })
    save_config(config)
    return config


def remove_transaction(config: dict, index: int) -> dict:
    """Remove a transaction by index (0-based) and save."""
    if "transactions" in config and 0 <= index < len(config["transactions"]):
        del config["transactions"][index]
        save_config(config)
    return config


def get_network_rpc(config: dict, asset: str) -> str:
    """Get RPC URL for a given asset from target_networks."""
    networks = config.get("target_networks", {})
    asset_upper = asset.upper()
    if asset_upper in networks:
        return networks[asset_upper].get("rpc", "")
    return ""


def get_chain_id(config: dict, asset: str) -> int:
    """Get chain ID for EVM-compatible asset (if defined)."""
    networks = config.get("target_networks", {})
    asset_upper = asset.upper()
    if asset_upper in networks:
        return networks[asset_upper].get("chain_id", 1)
    return 1