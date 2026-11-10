"""
HTTP Header builder module.

All base header values come from a Config instance (config.py).
The only optional argument is a dictionary of extra / override headers.
"""

from __future__ import annotations

from typing import Dict, Mapping, Optional

from .config import Config


def build_headers(
    config: Config,
    extra_headers: Optional[Mapping[str, str]] = None,
) -> Dict[str, str]:
    """
    Build a dictionary of HTTP headers from *config*.

    Args:
        config: Config instance from ``get_config(area_code)``.
            All base header values are read from this object.
        extra_headers: Optional dict of additional headers to merge in.
            Keys already present in the base headers will be overwritten
            by values from ``extra_headers``.

    Returns:
        A dict of header name → value ready for requests / httpx / etc.
    """
    headers: Dict[str, str] = {
        "accept": "*/*",
        "accept-language": config.ACCEPT_LANGUAGE,
        "accept-encoding": config.ACCEPT_ENCODING,
        "businesslang": config.BUSINESSLANG,
        "connection": config.CONNECTION,
        "content-type": config.CONTENT_TYPE,
        "Host": config.HOST,
        "user-agent": config.USER_AGENT,
        "cookie": config.COOKIE,
        "check-ip-realip": config.CHECK_IP_REALIP,
        "accept": config.ACCEPT,
    }

    if extra_headers:
        headers.update(extra_headers)

    return headers
