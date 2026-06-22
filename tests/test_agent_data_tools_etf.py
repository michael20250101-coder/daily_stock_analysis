# -*- coding: utf-8 -*-
"""Regression tests for agent data tool ETF chip-distribution handling."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from src.agent.tools import data_tools


def test_chip_distribution_tool_skips_etf_without_calling_manager():
    manager = MagicMock()

    with patch("src.agent.tools.data_tools._get_fetcher_manager", return_value=manager):
        result = data_tools._handle_get_chip_distribution("588000")

    assert result["unsupported"] is True
    assert result["reason"] == "etf_chip_distribution_not_supported"
    assert "ETF" in result["message"]
    manager.get_chip_distribution.assert_not_called()


def test_tushare_priority_log_message_is_console_encoding_safe():
    source = Path("data_provider/tushare_fetcher.py").read_text(encoding="utf-8")

    assert "✅ 检测到 TUSHARE_TOKEN" not in source
    assert "检测到 TUSHARE_TOKEN 且 API 初始化成功" in source
