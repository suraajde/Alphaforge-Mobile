from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
from typing import Optional

from services.portfolio_state_service import PortfolioStateService


class PortfolioAdministrationService:
    """Portfolio Administration Service providing summary metrics, backup, restore, and reset capabilities."""

    def __init__(self, state_service: Optional[PortfolioStateService] = None) -> None:
        self.state_service = state_service or PortfolioStateService()

    def get_administration_summary(self, path: Optional[str | Path] = None) -> dict:
        """Load portfolio state and return key administrative metrics."""
        load_res = self.state_service.load_state(path=path)
        if load_res.get("status") != "OK" or not load_res.get("state"):
            return {"status": "NOT_FOUND"}

        state = load_res["state"]
        positions = state.get("positions", {})
        holdings_count = len(positions) if isinstance(positions, dict) else 0
        transaction_count = state.get("transaction_count", 0)
        snapshots = state.get("snapshots", [])
        snapshot_count = len(snapshots) if isinstance(snapshots, list) else 0

        cash_balance = state.get("cash_balance", 0.0)
        invested_market_value = state.get("invested_market_value", 0.0)
        total_portfolio_value = state.get("total_portfolio_value", 0.0)
        last_updated = state.get("updated_at")

        return {
            "status": "OK",
            "holdings_count": holdings_count,
            "transaction_count": transaction_count,
            "snapshot_count": snapshot_count,
            "cash_balance": cash_balance,
            "invested_market_value": invested_market_value,
            "total_portfolio_value": total_portfolio_value,
            "last_updated": last_updated,
        }

    def create_backup(
        self,
        path: Optional[str | Path] = None,
        backup_dir: Optional[str | Path] = None,
    ) -> dict:
        """Create a timestamped backup copy of the portfolio state JSON file."""
        source_path = Path(path) if path is not None else self.state_service.DEFAULT_STATE_PATH
        if not source_path.exists():
            return {"status": "NOT_FOUND"}

        if backup_dir is not None:
            target_dir = Path(backup_dir)
        else:
            target_dir = source_path.parent.parent / "backups"

        target_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"portfolio_backup_{timestamp}"
        backup_file = target_dir / f"{base_name}.json"

        counter = 1
        while backup_file.exists():
            backup_file = target_dir / f"{base_name}_{counter}.json"
            counter += 1

        shutil.copy2(source_path, backup_file)

        return {
            "status": "OK",
            "backup_path": str(backup_file),
        }

    def restore_backup(
        self,
        backup_path: str | Path,
        path: Optional[str | Path] = None,
        backup_dir: Optional[str | Path] = None,
    ) -> dict:
        """Restore portfolio state from a backup JSON file, creating a safety backup first."""
        backup_file = Path(backup_path)
        if not backup_file.exists() or not backup_file.is_file():
            return {"status": "NOT_FOUND"}

        try:
            with open(backup_file, "r", encoding="utf-8") as f:
                payload = json.load(f)
            if not isinstance(payload, dict):
                return {"status": "ERROR", "error": "Invalid backup JSON payload"}
        except Exception as exc:
            return {"status": "ERROR", "error": f"Failed to parse backup JSON: {exc}"}

        target_file = Path(path) if path is not None else self.state_service.DEFAULT_STATE_PATH

        # Create automatic safety backup of current state before restore
        safety_res = self.create_backup(path=target_file, backup_dir=backup_dir)
        safety_backup = safety_res.get("backup_path") if safety_res.get("status") == "OK" else None

        # Replace target state file with selected backup
        target_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup_file, target_file)

        # Validate restored state through PortfolioStateService
        load_res = self.state_service.load_state(path=target_file)
        if load_res.get("status") != "OK":
            return {"status": "ERROR", "error": "Restored portfolio state validation failed"}

        return {
            "status": "OK",
            "restored_from": str(backup_file),
            "safety_backup": safety_backup,
        }

    def reset_portfolio_holdings(
        self,
        path: Optional[str | Path] = None,
        backup_dir: Optional[str | Path] = None,
    ) -> dict:
        """Reset portfolio holdings while preserving state version and creation date, creating an automatic backup first."""
        target_file = Path(path) if path is not None else self.state_service.DEFAULT_STATE_PATH

        # Automatic backup before reset
        backup_res = self.create_backup(path=target_file, backup_dir=backup_dir)
        backup_path = backup_res.get("backup_path") if backup_res.get("status") == "OK" else None

        # Load existing state to preserve state_version and created_at if available
        load_res = self.state_service.load_state(path=target_file)
        current_state = load_res.get("state") if load_res.get("status") == "OK" else {}

        now_iso = datetime.now(timezone.utc).isoformat()
        state_version = (
            current_state.get("state_version", self.state_service.STATE_VERSION)
            if current_state
            else self.state_service.STATE_VERSION
        )
        created_at = (
            current_state.get("created_at", now_iso)
            if current_state
            else now_iso
        )

        reset_state = {
            "state_version": state_version,
            "created_at": created_at,
            "updated_at": now_iso,
            "cash_balance": 0.0,
            "positions": {},
            "position_order": [],
            "transaction_count": 0,
            "transactions": [],
            "snapshots": [],
            "invested_market_value": 0.0,
            "total_portfolio_value": 0.0,
        }

        self.state_service.save_state(reset_state, path=target_file)

        return {
            "status": "OK",
            "backup_path": backup_path,
        }
