"""
Pytest configuration and session fixtures for PRAMAAN-X test suite:
Ensures all tests run in an isolated temporary database in tempfile directory,
preventing any test residue (such as APP-TEST-* rows) from touching dev/demo pramaan_x.db.
"""
import os
import tempfile
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configure isolated test database in OS temp directory
TEST_DB_PATH = Path(tempfile.gettempdir()) / "pramaan_x_test.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

# Reconfigure backend settings and engine
from backend.app.core.config import settings
settings.DATABASE_URL = TEST_DATABASE_URL

import backend.app.core.database as core_db
core_db.engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True
)
core_db.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=core_db.engine)
from backend.app.data.seed_data import seed_database


@pytest.fixture(scope="session", autouse=True)
def setup_isolated_test_database():
    """Initializes schema and seed data in the temporary test database."""
    # Ensure fresh baseline in test DB
    seed_database(reset=True)
    yield
    # Teardown: close engine and cleanup temp database
    core_db.engine.dispose()
    try:
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink(missing_ok=True)
    except Exception:
        pass
