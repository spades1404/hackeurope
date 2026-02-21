# Pytest configuration and shared fixtures
import os
import pytest
import aiosqlite
import asyncio
from backend.database import DB_PATH, setup_database

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
async def setup_test_db():
    """Ensure the test database is clean before each test run."""
    # We will use the standard DB_PATH for simplicity in these tests, but if isolation is 
    # fully required we could patch DB_PATH to point to a test.db.
    # We assume the database has been fully set up.
    await setup_database()
