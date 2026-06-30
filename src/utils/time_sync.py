"""Time synchronization utilities for TOTP accuracy.

Checks system time against an NTP server to detect clock drift,
which could cause TOTP code mismatches.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class TimeSyncResult:
    """Result of a time synchronization check."""

    system_time: float       # Unix timestamp from system
    ntp_time: Optional[float]  # Unix timestamp from NTP server
    offset: Optional[float]  # Difference in seconds (positive = system ahead)
    is_synced: bool          # True if offset is within acceptable range
    acceptable_drift: int    # Max acceptable drift in seconds


def check_time_sync(acceptable_drift: int = 30) -> TimeSyncResult:
    """Check if system time is synchronized with NTP.

    Args:
        acceptable_drift: Maximum acceptable drift in seconds.

    Returns:
        TimeSyncResult with sync status and offset.
    """
    import time

    system_time = time.time()
    ntp_time = None
    offset = None

    try:
        import ntplib
        client = ntplib.NTPClient()
        response = client.request("pool.ntp.org", version=3, timeout=5)
        ntp_time = response.tx_time
        offset = system_time - ntp_time
    except Exception:
        # NTP check failed, can't determine offset
        pass

    is_synced = True
    if offset is not None:
        is_synced = abs(offset) <= acceptable_drift

    return TimeSyncResult(
        system_time=system_time,
        ntp_time=ntp_time,
        offset=offset,
        is_synced=is_synced,
        acceptable_drift=acceptable_drift,
    )
