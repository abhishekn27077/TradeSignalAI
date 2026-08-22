import logging
import uuid
from typing import Any

logger = logging.getLogger(__name__)

class VirtualAccount:
    """Represents an in-memory paper trading account."""
    def __init__(self, account_id: str, initial_balance: float = 10000.0):
        self.account_id = account_id
        self.balance = initial_balance
        self.equity = initial_balance
        self.used_margin = 0.0
        self.free_margin = initial_balance
        self.realized_pnl = 0.0
        self.floating_pnl = 0.0
        
    def update_floating_pnl(self, new_floating_pnl: float):
        self.floating_pnl = new_floating_pnl
        self.equity = self.balance + self.floating_pnl
        self.free_margin = self.equity - self.used_margin

    def adjust_margin(self, margin_change: float):
        self.used_margin += margin_change
        self.free_margin = self.equity - self.used_margin
        
    def apply_realized_pnl(self, pnl: float):
        self.realized_pnl += pnl
        self.balance += pnl
        self.equity = self.balance + self.floating_pnl
        self.free_margin = self.equity - self.used_margin
        
    def dump_state(self) -> dict[str, Any]:
        return {
            "account_id": self.account_id,
            "balance": self.balance,
            "equity": self.equity,
            "used_margin": self.used_margin,
            "free_margin": self.free_margin,
            "realized_pnl": self.realized_pnl,
            "floating_pnl": self.floating_pnl
        }

class AccountManager:
    """Manages all active paper accounts."""
    def __init__(self):
        self.accounts: dict[str, VirtualAccount] = {}

    def create_account(self, initial_balance: float = 10000.0) -> VirtualAccount:
        acc_id = str(uuid.uuid4())
        acc = VirtualAccount(acc_id, initial_balance)
        self.accounts[acc_id] = acc
        return acc

    def get_account(self, account_id: str) -> VirtualAccount:
        return self.accounts.get(account_id)

    def get_summary(self) -> dict[str, Any]:
        if not self.accounts:
            # Create a default account if none exists
            self.create_account()
        
        acc = list(self.accounts.values())[0]
        return {
            "total_equity": acc.equity,
            "total_pnl": acc.realized_pnl + acc.floating_pnl,
            "daily_pnl": acc.realized_pnl + acc.floating_pnl, # Mocked as same for now
            "open_positions": 0, # Since we didn't mock positions inside account
            "margin_used": acc.used_margin,
            "free_margin": acc.free_margin
        }

account_manager = AccountManager()
