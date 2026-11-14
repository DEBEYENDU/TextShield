from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
TESTS = Path(__file__).resolve().parent
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))


@pytest.fixture
def api_factory():
    from fake_api import FakeApi

    servers: list[FakeApi] = []

    def make(routes):
        server = FakeApi(routes)
        servers.append(server)
        return server

    yield make
    for server in servers:
        server.close()
