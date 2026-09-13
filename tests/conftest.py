"""
MarketLens - Phase 17: Automated Testing
tests/conftest.py
==============================================================================
Shared setup for the whole test suite.

Every phase's run_*.py script does two things before importing its own
modules: (1) assumes the process's CWD is the project root (several modules,
e.g. churn_features.py, read paths like "data/processed/orders_enriched.csv"
relative to CWD rather than via __file__), and (2) inserts its own
`python/<subpackage>/` directory onto sys.path so sibling modules in that
folder (not a real Python package - no __init__.py) can import each other by
bare name (e.g. `import revenue as rev`).

This conftest reproduces both, once, for every test in the suite - so tests
can `import revenue`, `import churn_features`, etc. directly, exactly the
way the orchestrators do, and so relative-path reads resolve correctly
regardless of what directory `pytest` was invoked from.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]

# Make every phase's module directory importable by bare name, same as each
# run_*.py already does for itself.
for sub in [
    "python/analytics",
    "python/modeling",
    "python/scenarios",
    "python/validation",
    "python/ingestion",
]:
    p = str(ROOT / sub)
    if p not in sys.path:
        sys.path.insert(0, p)


@pytest.fixture(scope="session", autouse=True)
def _chdir_to_project_root():
    """Some modules (churn_features.py) read data with bare relative paths.
    Every run_*.py is documented to be invoked from the project root, so
    tests reproduce that assumption instead of patching the modules."""
    prev = os.getcwd()
    os.chdir(ROOT)
    yield
    os.chdir(prev)


# ---------------------------------------------------------------------------
# Cached data fixtures - session-scoped so the ~83k-order / 206k-item CSVs
# are read once for the whole suite, not once per test.
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def orders_raw() -> pd.DataFrame:
    return pd.read_csv(ROOT / "data" / "raw" / "orders.csv", parse_dates=["order_date"])


@pytest.fixture(scope="session")
def order_items_raw() -> pd.DataFrame:
    return pd.read_csv(ROOT / "data" / "raw" / "order_items.csv")


@pytest.fixture(scope="session")
def customers_raw() -> pd.DataFrame:
    return pd.read_csv(ROOT / "data" / "raw" / "customers.csv", parse_dates=["signup_date"])


@pytest.fixture(scope="session")
def products_raw() -> pd.DataFrame:
    return pd.read_csv(ROOT / "data" / "raw" / "products.csv")


@pytest.fixture(scope="session")
def returns_raw() -> pd.DataFrame:
    return pd.read_csv(ROOT / "data" / "raw" / "returns.csv")


@pytest.fixture(scope="session")
def campaigns_raw() -> pd.DataFrame:
    return pd.read_csv(ROOT / "data" / "raw" / "marketing_campaigns.csv", parse_dates=["campaign_date"])


@pytest.fixture(scope="session")
def stores_raw() -> pd.DataFrame:
    return pd.read_csv(ROOT / "data" / "raw" / "stores.csv")


@pytest.fixture(scope="session")
def regions_raw() -> pd.DataFrame:
    return pd.read_csv(ROOT / "data" / "raw" / "regions.csv")


@pytest.fixture(scope="session")
def orders_enriched() -> pd.DataFrame:
    return pd.read_csv(
        ROOT / "data" / "processed" / "orders_enriched.csv",
        parse_dates=["order_date", "signup_date"],
    )


@pytest.fixture(scope="session")
def order_items_enriched() -> pd.DataFrame:
    return pd.read_csv(
        ROOT / "data" / "processed" / "order_items_enriched.csv",
        parse_dates=["order_date", "signup_date"],
    )
