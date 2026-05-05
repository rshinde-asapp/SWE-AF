from datetime import datetime, timedelta

from src.utils import get_date_range, format_credits, format_bytes_to_tb


def test_get_date_range_30d():
    start, end = get_date_range(30)
    expected_end = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    assert end == expected_end
    assert start == expected_end - timedelta(days=30)


def test_get_date_range_7d():
    start, end = get_date_range(7)
    expected_end = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    assert end == expected_end
    assert start == expected_end - timedelta(days=7)


def test_format_credits():
    assert format_credits(1234.56) == "1,234.56"


def test_format_bytes_to_tb():
    assert format_bytes_to_tb(1099511627776) == "1.00 TB"
