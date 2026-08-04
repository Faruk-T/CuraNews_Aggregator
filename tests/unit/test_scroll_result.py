"""Unit tests for scroll helpers (no browser required)."""

import pytest

from curanews.browser.scroll import ScrollResult


def test_scroll_result_fields():
    result = ScrollResult(rounds=3, final_count=6, initial_count=2)
    assert result.final_count - result.initial_count == 4
    assert result.rounds == 3
