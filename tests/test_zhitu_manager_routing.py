# -*- coding: utf-8 -*-
"""Tests for Zhitu realtime routing in DataFetcherManager."""

from types import SimpleNamespace
from unittest.mock import patch

from data_provider.base import DataFetcherManager
from data_provider.realtime_types import RealtimeSource, UnifiedRealtimeQuote


class _StubFetcher:
    def __init__(self, name: str, priority: int):
        self.name = name
        self.priority = priority


class _StubZhituFetcher(_StubFetcher):
    def __init__(self):
        super().__init__("ZhituFetcher", 0)
        self.calls = []

    def get_realtime_quote(self, stock_code: str):
        self.calls.append(stock_code)
        return UnifiedRealtimeQuote(
            code=stock_code,
            source=RealtimeSource.ZHITU,
            price=2.017,
            change_pct=4.02,
            amount=8160146200,
            provider_timestamp="2026-06-18 15:00:18",
        )


def _base_config(**overrides):
    values = dict(
        tushare_token="",
        zhitu_api_token="",
        longbridge_app_key="",
        longbridge_app_secret="",
        longbridge_access_token="",
        longbridge_oauth_client_id="",
        finnhub_api_key="",
        alphavantage_api_key="",
        enable_realtime_quote=True,
        realtime_source_priority="zhitu,akshare_sina",
        realtime_cache_ttl=600,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


@patch("src.config.get_config")
def test_manager_skips_zhitu_without_token(mock_get_config):
    mock_get_config.return_value = _base_config(zhitu_api_token="")

    with patch("data_provider.efinance_fetcher.EfinanceFetcher", return_value=_StubFetcher("EfinanceFetcher", 0)), patch(
        "data_provider.tencent_fetcher.TencentFetcher", return_value=_StubFetcher("TencentFetcher", 0)
    ), patch("data_provider.akshare_fetcher.AkshareFetcher", return_value=_StubFetcher("AkshareFetcher", 1)), patch(
        "data_provider.pytdx_fetcher.PytdxFetcher", return_value=_StubFetcher("PytdxFetcher", 2)
    ), patch("data_provider.baostock_fetcher.BaostockFetcher", return_value=_StubFetcher("BaostockFetcher", 3)), patch(
        "data_provider.yfinance_fetcher.YfinanceFetcher", return_value=_StubFetcher("YfinanceFetcher", 4)
    ), patch("data_provider.longbridge_fetcher.LongbridgeFetcher") as mock_longbridge, patch(
        "data_provider.zhitu_fetcher.ZhituFetcher", return_value=_StubZhituFetcher()
    ) as mock_zhitu:
        mock_longbridge.has_configured_credentials.return_value = False
        manager = DataFetcherManager()

    assert "ZhituFetcher" not in manager.available_fetchers
    mock_zhitu.assert_not_called()


@patch("src.config.get_config")
def test_manager_routes_realtime_quote_to_zhitu_when_configured(mock_get_config):
    mock_get_config.return_value = _base_config(zhitu_api_token="demo-token")
    zhitu = _StubZhituFetcher()

    with patch("data_provider.efinance_fetcher.EfinanceFetcher", return_value=_StubFetcher("EfinanceFetcher", 0)), patch(
        "data_provider.tencent_fetcher.TencentFetcher", return_value=_StubFetcher("TencentFetcher", 0)
    ), patch("data_provider.akshare_fetcher.AkshareFetcher", return_value=_StubFetcher("AkshareFetcher", 1)), patch(
        "data_provider.pytdx_fetcher.PytdxFetcher", return_value=_StubFetcher("PytdxFetcher", 2)
    ), patch("data_provider.baostock_fetcher.BaostockFetcher", return_value=_StubFetcher("BaostockFetcher", 3)), patch(
        "data_provider.yfinance_fetcher.YfinanceFetcher", return_value=_StubFetcher("YfinanceFetcher", 4)
    ), patch("data_provider.longbridge_fetcher.LongbridgeFetcher") as mock_longbridge, patch(
        "data_provider.zhitu_fetcher.ZhituFetcher", return_value=zhitu
    ):
        mock_longbridge.has_configured_credentials.return_value = False
        manager = DataFetcherManager()
        quote = manager.get_realtime_quote("588000")

    assert "ZhituFetcher" in manager.available_fetchers
    assert quote.source == RealtimeSource.ZHITU
    assert quote.price == 2.017
    assert quote.provider_timestamp.endswith("+00:00") or quote.provider_timestamp == "2026-06-18T15:00:18+00:00"
    assert zhitu.calls == ["588000"]
