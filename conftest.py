"""
conftest.py — Phase 2 project root
Playwright pytest plugin automatically injects `page`, `browser`,
`browser_context`, and `playwright` fixtures when pytest-playwright is installed.
"""

import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow-running")
