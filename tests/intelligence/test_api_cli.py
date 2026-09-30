"""Tests for intelligence API and CLI stubs."""

from app.intelligence.api import router
from app.intelligence.cli import intelligence_cli


def test_api_router_exists():
    assert router is not None
    assert router.prefix == "/api/v1/intelligence"


def test_cli_group():
    assert intelligence_cli.name == "intelligence"
    commands = [cmd.name for cmd in intelligence_cli.commands.values()]
    assert "list" in commands
    assert "gaps" in commands
    assert "coverage" in commands
    assert "stale" in commands
