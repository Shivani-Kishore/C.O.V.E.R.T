"""
C.O.V.E.R.T - Pytest Configuration for Backend Tests
"""

import pytest
import asyncio
from typing import Generator

# Configure pytest for async tests
@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
