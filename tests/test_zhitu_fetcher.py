# -*- coding: utf-8 -*-
"""Tests for Zhitu realtime ETF quote fetcher."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from data_provider.realtime_types import RealtimeSource


class _FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.text = "{}"

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def _cfg(token="demo-token", timeout=8.0):
    return SimpleNamespace(
        zhitu_api_token=token,
        zhitu_request_timeout=timeout,
    )


@patch("data_provider.zhitu_fetcher.get_config")
@patch("data_provider.zhitu_fetcher.requests.get")
def test_zhitu_fetcher_maps_fund_realtime_quote(mock_get, mock_get_config):
    from data_provider.zhitu_fetcher import ZhituFetcher

    mock_get_config.return_value = _cfg()
    mock_get.return_value = _FakeResponse(
        {
            "pe": 2.0143,
            "ud": 0.078,
            "pc": 4.0227,
            "zf": 5.673,
            "p": 2.017,
            "o": 1.935,
            "h": 2.042,
            "l": 1.932,
            "yc": 1.939,
            "cje": 8160146200,
            "v": 40816717,
            "pv": 4081671719,
            "tv": 2465,
            "tr": 2.45,
            "t": "2026-06-18 15:00:18",
        }
    )

    quote = ZhituFetcher().get_realtime_quote("588000")

    assert quote.code == "588000"
    assert quote.source == RealtimeSource.ZHITU
    assert quote.price == 2.017
    assert quote.open_price == 1.935
    assert quote.high == 2.042
    assert quote.low == 1.932
    assert quote.pre_close == 1.939
    assert quote.change_amount == 0.078
    assert quote.change_pct == 4.0227
    assert quote.amplitude == 5.673
    assert quote.amount == 8160146200
    assert quote.volume == 4081671719
    assert quote.turnover_rate == 2.45
    assert quote.pe_ratio == 2.0143
    assert quote.provider_timestamp == "2026-06-18T15:00:18+08:00"
    assert "demo-token" not in mock_get.call_args.args[0]
    assert mock_get.call_args.kwargs["params"] == {"token": "demo-token"}
    assert mock_get.call_args.kwargs["timeout"] == 8.0


@patch("data_provider.zhitu_fetcher.get_config")
def test_zhitu_fetcher_unavailable_without_token(mock_get_config):
    from data_provider.zhitu_fetcher import ZhituFetcher

    mock_get_config.return_value = _cfg(token="")

    fetcher = ZhituFetcher()

    assert fetcher.is_available() is False
    assert fetcher.get_realtime_quote("588000") is None


@patch("data_provider.zhitu_fetcher.get_config")
@patch("data_provider.zhitu_fetcher.requests.get")
def test_zhitu_fetcher_returns_none_for_incomplete_quote(mock_get, mock_get_config):
    from data_provider.zhitu_fetcher import ZhituFetcher

    mock_get_config.return_value = _cfg()
    mock_get.return_value = _FakeResponse({"p": 0, "t": "2026-06-18 15:00:18"})

    assert ZhituFetcher().get_realtime_quote("588000") is None


@patch("data_provider.zhitu_fetcher.get_config")
@patch("data_provider.zhitu_fetcher.requests.get")
def test_zhitu_fetcher_ignores_zero_optional_fields(mock_get, mock_get_config):
    from data_provider.zhitu_fetcher import ZhituFetcher

    mock_get_config.return_value = _cfg()
    mock_get.return_value = _FakeResponse(
        {
            "p": 2.017,
            "o": 0,
            "h": 0,
            "l": 0,
            "yc": 2.017,
            "cje": 0,
            "pv": 0,
            "tr": 0,
            "t": "2026-06-22 09:20:26",
        }
    )

    quote = ZhituFetcher().get_realtime_quote("588000")

    assert quote.price == 2.017
    assert quote.open_price is None
    assert quote.high is None
    assert quote.low is None
    assert quote.amount is None
    assert quote.volume is None
    assert quote.turnover_rate is None
    assert quote.pre_close == 2.017
