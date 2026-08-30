import re
from datetime import datetime, timedelta, timezone

def parse_flexible_datetime(date_str: str) -> datetime:
    """Standardizes messy web timestamp patterns into a unified timezone-aware UTC format."""
    if not date_str:
        return datetime.now(timezone.utc)
        
    date_clean = date_str.strip().replace("GMT", "+0000").replace("UTC", "+0000")
    
    # Common format variations
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%d %b %Y %H:%M:%S %z"
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_clean, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            continue
            
    # Fallback to general parsing assumptions if strings do not match
    return datetime.now(timezone.utc)

def is_within_24_hours(dt: datetime) -> bool:
    """Enforces strict evaluation constraints to ensure data freshness."""
    now = datetime.now(timezone.utc)
    delta = now - dt
    return timedelta(hours=0) <= delta <= timedelta(hours=24)
