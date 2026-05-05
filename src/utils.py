from datetime import datetime, timedelta


def get_date_range(days: int) -> tuple[datetime, datetime]:
    """Return (start_date, end_date) for the last N days.

    end_date is today at 00:00:00. start_date is N days before end_date.
    """
    end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(days=days)
    return start_date, end_date


def format_credits(value: float) -> str:
    """Format credit value for display: '1,234.56'."""
    return f"{value:,.2f}"


def format_bytes_to_tb(bytes_val: float) -> str:
    """Convert bytes to TB string: '1.23 TB'."""
    return f"{bytes_val / (1024**4):.2f} TB"
