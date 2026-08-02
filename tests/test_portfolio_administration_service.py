import json
from pathlib import Path
import tempfile
import pytest

from services.portfolio_administration_service import PortfolioAdministrationService


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


def test_restore_not_implemented():
    service = PortfolioAdministrationService()
    with pytest.raises(NotImplementedError, match="Backup restore will be implemented in Sprint 13.2.1C"):
        service.restore_backup()


def test_reset_not_implemented():
    service = PortfolioAdministrationService()
    with pytest.raises(NotImplementedError, match="Portfolio reset will be implemented in Sprint 13.2.1C"):
        service.reset_portfolio_holdings()
