# -*- coding: utf-8 -*-
"""Regression tests for ETF capability semantics and Agent settings limits."""

from types import SimpleNamespace

from data_provider.base import DataFetcherManager
from data_provider.realtime_types import get_chip_circuit_breaker
from src.core.config_registry import get_field_definition

from tests.test_chip_distribution_manager import _ChipFetcher


def test_manager_marks_etf_chip_distribution_unsupported_without_provider_calls():
    get_chip_circuit_breaker().reset()
    fetcher = _ChipFetcher("ShouldNotRun", 0, None)
    manager = DataFetcherManager(fetchers=[fetcher])

    with __import__("unittest").mock.patch(
        "src.config.get_config",
        return_value=SimpleNamespace(enable_chip_distribution=True),
    ):
        result = manager.get_chip_distribution("588000")

    assert result is None
    assert fetcher.calls == 0


def test_deep_research_timeout_schema_allows_longer_requests():
    field = get_field_definition("AGENT_DEEP_RESEARCH_TIMEOUT")

    assert field["validation"]["max"] >= 1800
