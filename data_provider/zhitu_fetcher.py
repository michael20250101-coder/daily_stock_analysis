# -*- coding: utf-8 -*-
"""
ZhituFetcher - 智兔 ETF 实时行情数据源

定位：作为 A 股 ETF 实时行情增强/校验源，重点提供 provider_timestamp
用于判断行情新鲜度。默认仅在配置 ZHITU_API_TOKEN 后启用。
"""

from __future__ import annotations

import logging
from typing import Any, Optional
from zoneinfo import ZoneInfo

import pandas as pd
import requests

from src.config import get_config
from .base import BaseFetcher, DataFetchError, normalize_stock_code
from .realtime_types import RealtimeSource, UnifiedRealtimeQuote, safe_float, safe_int

logger = logging.getLogger(__name__)


def _positive_float(value: Any) -> Optional[float]:
    """Return positive float values only; Zhitu may return 0 for pre-open placeholders."""
    parsed = safe_float(value)
    return parsed if parsed is not None and parsed > 0 else None


def _positive_int(value: Any) -> Optional[int]:
    """Return positive int values only; zero volume/amount placeholders should not block supplements."""
    parsed = safe_int(value)
    return parsed if parsed is not None and parsed > 0 else None


class ZhituFetcher(BaseFetcher):
    """Zhitu API realtime ETF quote fetcher."""

    name = "ZhituFetcher"
    priority = 0
    _BASE_URL = "https://api.zhituapi.com/fund/real/ssjy/{code}"

    def __init__(self) -> None:
        config = get_config()
        self.token = (getattr(config, "zhitu_api_token", None) or "").strip()
        self.timeout = float(getattr(config, "zhitu_request_timeout", 8.0) or 8.0)
        self.priority = int(getattr(config, "zhitu_priority", 0) or 0)

    def is_available(self) -> bool:
        """Return whether the fetcher has a configured token."""
        return bool(self.token)

    def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Zhitu realtime source does not implement daily history."""
        raise DataFetchError("ZhituFetcher only supports realtime ETF quotes")

    def _normalize_data(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        """Zhitu realtime source does not implement daily history."""
        raise DataFetchError("ZhituFetcher only supports realtime ETF quotes")

    def get_realtime_quote(self, stock_code: str) -> Optional[UnifiedRealtimeQuote]:
        """Fetch realtime ETF quote from Zhitu fund realtime endpoint."""
        if not self.is_available():
            logger.debug("[Zhitu] ZHITU_API_TOKEN 未配置，跳过实时行情")
            return None

        code = normalize_stock_code(stock_code)
        url = self._BASE_URL.format(code=code)
        try:
            response = requests.get(
                url,
                params={"token": self.token},
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            logger.warning("[Zhitu] 获取 %s 实时行情失败: %s", code, exc)
            return None

        quote = self._quote_from_payload(code, payload)
        if quote is None or not quote.has_basic_data():
            logger.debug("[Zhitu] %s 返回空或无效实时行情", code)
            return None
        return quote

    @staticmethod
    def _quote_from_payload(code: str, payload: dict[str, Any]) -> Optional[UnifiedRealtimeQuote]:
        price = safe_float(payload.get("p"))
        if price is None or price <= 0:
            return None

        volume = _positive_int(payload.get("pv"))
        if volume is None:
            volume = _positive_int(payload.get("v"))

        return UnifiedRealtimeQuote(
            code=code,
            source=RealtimeSource.ZHITU,
            price=price,
            open_price=_positive_float(payload.get("o")),
            high=_positive_float(payload.get("h")),
            low=_positive_float(payload.get("l")),
            pre_close=_positive_float(payload.get("yc")),
            change_amount=safe_float(payload.get("ud")),
            change_pct=safe_float(payload.get("pc")),
            amplitude=safe_float(payload.get("zf")),
            amount=_positive_float(payload.get("cje")),
            volume=volume,
            turnover_rate=_positive_float(payload.get("tr")),
            pe_ratio=_positive_float(payload.get("pe")),
            provider_timestamp=ZhituFetcher._normalize_provider_time(payload.get("t")),
        )

    @staticmethod
    def _normalize_provider_time(value: Any) -> Optional[str]:
        """Normalize Zhitu's Beijing-time timestamp to an ISO string with timezone."""
        if value in (None, ""):
            return None
        text = str(value).strip()
        if not text:
            return None
        # Zhitu returns local China market time like "2026-06-18 15:00:18".
        # Attach Asia/Shanghai so DataFetcherManager does not treat it as UTC.
        if "+" not in text and not text.endswith("Z"):
            try:
                from datetime import datetime

                parsed = datetime.fromisoformat(text).replace(tzinfo=ZoneInfo("Asia/Shanghai"))
                return parsed.isoformat()
            except ValueError:
                return text
        return text
