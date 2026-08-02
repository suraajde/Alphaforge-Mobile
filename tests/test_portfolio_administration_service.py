import json
from pathlib import Path
import tempfile
import pytest

from services.portfolio_administration_service import PortfolioAdministrationService
from services.portfolio_state_service import PortfolioStateService


@pytest.fixture
def temp_dir():
    """Fixture providing a clean temporary directory."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture
def temp_state_file(temp_dir):
    """Fixture providing a temporary portfolio state JSON file."""
    data_dir = temp_dir / "data" / "portfolio"
    data_dir.mkdir(parents=True, exist_ok=True)
    state_file = data_dir / "portfolio_state.json"

    dummy_state = {
        "state_version": "1.0",
        "created_at": "2026-08-01T00:00:00Z",
        "updated_at": "2026-08-02T12:00:00Z",
        "cash_balance": 50000.0,
        "invested_market_value": 150000.0,
        "total_portfolio_value": 200000.0,
        "transaction_count": 5,
        "positions": {
            "RELIANCE": {"symbol": "RELIANCE", "quantity": 10},
            "TCS": {"symbol": "TCS", "quantity": 5},
        },
        "position_order": ["RELIANCE", "TCS"],
        "transactions": [{"symbol": "RELIANCE", "type": "BUY"}],
        "snapshots": [{"snapshot_id": "snap-1"}],
    }
    state_file.write_text(json.dumps(dummy_state), encoding="utf-8")
    return state_file


def test_administration_summary_returns_data(temp_state_file):
    service = PortfolioAdministrationService()
    result = service.get_administration_summary(path=temp_state_file)

    assert result["status"] == "OK"
    assert "holdings_count" in result
    assert result["holdings_count"] == 2
    assert "cash_balance" in result
    assert result["cash_balance"] == 50000.0
    assert result["transaction_count"] == 5
    assert result["snapshot_count"] == 1
    assert result["invested_market_value"] == 150000.0
    assert result["total_portfolio_value"] == 200000.0
    assert result["last_updated"] == "2026-08-02T12:00:00Z"


def test_administration_summary_not_found(temp_dir):
    service = PortfolioAdministrationService()
    non_existent = temp_dir / "non_existent.json"
    result = service.get_administration_summary(path=non_existent)
    assert result["status"] == "NOT_FOUND"


def test_create_backup(temp_state_file, temp_dir):
    service = PortfolioAdministrationService()
    backup_dir = temp_dir / "data" / "backups"
    result = service.create_backup(path=temp_state_file, backup_dir=backup_dir)

    assert result["status"] == "OK"
    assert "backup_path" in result
    backup_path = Path(result["backup_path"])
    assert backup_path.exists()
    assert backup_path.is_file()
    assert "portfolio_backup_" in backup_path.name


def test_restore_backup_success(temp_state_file, temp_dir):
    service = PortfolioAdministrationService()
    backup_dir = temp_dir / "data" / "backups"

    # Step 1: Create initial backup (A)
    backup_res = service.create_backup(path=temp_state_file, backup_dir=backup_dir)
    assert backup_res["status"] == "OK"
    backup_path = backup_res["backup_path"]

    # Step 2: Mutate current state file (B)
    mutated_state = {
        "state_version": "1.0",
        "created_at": "2026-08-01T00:00:00Z",
        "updated_at": "2026-08-02T15:00:00Z",
        "cash_balance": 99999.0,
        "positions": {"INFY": {"symbol": "INFY", "quantity": 100}},
        "position_order": ["INFY"],
        "transaction_count": 1,
        "transactions": [],
        "snapshots": [],
    }
    temp_state_file.write_text(json.dumps(mutated_state), encoding="utf-8")

    # Step 3: Restore state from initial backup (A)
    restore_res = service.restore_backup(
        backup_path=backup_path, path=temp_state_file, backup_dir=backup_dir
    )

    assert restore_res["status"] == "OK"
    assert restore_res["restored_from"] == str(backup_path)
    assert restore_res["safety_backup"] is not None
    assert Path(restore_res["safety_backup"]).exists()

    # Step 4: Verify restored file contents match initial state A
    state_service = PortfolioStateService()
    restored_state = state_service.load_state(path=temp_state_file)["state"]
    assert restored_state["cash_balance"] == 50000.0
    assert len(restored_state["positions"]) == 2
    assert "RELIANCE" in restored_state["positions"]


def test_restore_backup_missing_file(temp_state_file, temp_dir):
    service = PortfolioAdministrationService()
    missing_backup = temp_dir / "missing_backup.json"
    result = service.restore_backup(backup_path=missing_backup, path=temp_state_file)

    assert result["status"] == "NOT_FOUND"


def test_reset_portfolio_holdings(temp_state_file):
    service = PortfolioAdministrationService()
    result = service.reset_portfolio_holdings(path=temp_state_file)

    assert result["status"] == "OK"

    # Verify state reset correctness
    state_service = PortfolioStateService()
    load_res = state_service.load_state(path=temp_state_file)
    assert load_res["status"] == "OK"

    reset_state = load_res["state"]
    assert reset_state["state_version"] == "1.0"
    assert reset_state["created_at"] == "2026-08-01T00:00:00Z"
    assert reset_state["cash_balance"] == 0.0
    assert reset_state["positions"] == {}
    assert reset_state["position_order"] == []
    assert reset_state["transaction_count"] == 0
    assert reset_state["transactions"] == []
    assert reset_state["snapshots"] == []
    assert reset_state["invested_market_value"] == 0.0
    assert reset_state["total_portfolio_value"] == 0.0


def test_reset_creates_backup(temp_state_file, temp_dir):
    service = PortfolioAdministrationService()
    backup_dir = temp_dir / "data" / "backups"
    result = service.reset_portfolio_holdings(
        path=temp_state_file, backup_dir=backup_dir
    )

    assert result["status"] == "OK"
    assert result["backup_path"] is not None

    backup_file = Path(result["backup_path"])
    assert backup_file.exists()
    assert backup_file.is_file()

    # Verify backup contains original state prior to reset
    backup_state = json.loads(backup_file.read_text(encoding="utf-8"))
    assert backup_state["cash_balance"] == 50000.0
    assert len(backup_state["positions"]) == 2
