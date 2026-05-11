from __future__ import annotations

import pytest
import pytest_asyncio


@pytest.fixture(scope="session", autouse=True)
def apply_migrations() -> None:
    return None


@pytest_asyncio.fixture(autouse=True)
async def clean_state() -> None:
    yield
