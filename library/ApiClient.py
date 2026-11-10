"""
API client — uses headers from builder.build_headers and settings from config.
"""

from __future__ import annotations

import random
import time
from typing import Any, Dict, Mapping, Optional, Union

import requests
import urllib3

from .builder import build_headers   # ← headers come from builder.py
from .config import Config


class ApiClient:
    """
    HTTP client bound to a Config instance.

    Every request builds headers via builder.build_headers(config, ...).
    Timeout, SSL, delays, and endpoints come from config.
    """

    def __init__(
        self,
        config: Config,
        *,
        session: Optional[requests.Session] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        auto_delay: bool = True,
    ) -> None:
        self.config = config
        self.session = session or requests.Session()
        self.extra_headers = dict(extra_headers) if extra_headers else {}
        self.auto_delay = auto_delay

        if not config.VERIFY_SSL:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _make_headers(
        self, extra_headers: Optional[Mapping[str, str]] = None
    ) -> Dict[str, str]:
        """Build headers using builder.py (config values + optional extras)."""
        merged: Dict[str, str] = dict(self.extra_headers)
        if extra_headers:
            merged.update(extra_headers)
        # All base header values come from config via builder.build_headers
        return build_headers(self.config, extra_headers=merged or None)

    def _maybe_delay(self) -> None:
        if self.auto_delay and self.config.MAX_DELAY > 0:
            time.sleep(random.uniform(self.config.MIN_DELAY, self.config.MAX_DELAY))

    def request(
        self,
        method: str,
        url: str,
        *,
        data: Any = None,
        json: Any = None,
        params: Optional[Mapping[str, Any]] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[Union[int, float]] = None,
        **kwargs: Any,
    ) -> requests.Response:
        self._maybe_delay()

        headers = self._make_headers(extra_headers)
        effective_timeout = timeout if timeout is not None else self.config.REQUEST_TIMEOUT

        def _do_request() -> requests.Response:
            return self.session.request(
                method=method.upper(),
                url=url,
                headers=headers,
                data=data,
                json=json,
                params=params,
                timeout=effective_timeout,
                verify=self.config.VERIFY_SSL,
                **kwargs,
            )

    # ── Attempt 1 ──────────────────────────────────────────────
        try:
            return _do_request()
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            print(f"Request timed out / connection error ({type(e).__name__}), retrying once...")
            time.sleep(1)

        # ── Attempt 2 ──────────────────────────────────────────────
        try:
            return _do_request()
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            print(
                f"Request timed out again ({type(e).__name__}). "
                "Waiting 5 minutes before final retry..."
            )
            time.sleep(5 * 60)  # 5 minutes

        # ── Attempt 3 (final) ──────────────────────────────────────
        return _do_request()

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> requests.Response:
        return self.request("POST", url, **kwargs)

    def login(
        self,
        country_code: str,
        username: str,
        password: str,
    ) -> requests.Response:
        payload: Dict[str, Any] = {
            "username": username,
            "password": password,
        }

        cfg = self.config
        payload.update(
            {
                "areaCode": f"+{country_code}",
                "deviceId": cfg.DEVICE_ID,
                "cId": cfg.DEVICE_ID,
            }
        )

        # First attempt
        resp = self.post(
            cfg.LOGIN_URL,
            data=payload,
        )

        # Retry once on any server error (5xx)
        if 500 <= resp.status_code < 600:
            print(f"Server error {resp.status_code} for {username}, retrying once...")
            resp = self.post(
                cfg.LOGIN_URL,
                data=payload,
            )

            # Still a server error after retry → give up and continue
            if 500 <= resp.status_code < 600:
                print(f"Server error {resp.status_code} again for {username}, skipping.")
                return None

        # Normal business-logic check (only reached on non-5xx responses)
        try:
            data = resp.json()
        except ValueError:
            print(f"Invalid JSON response for {username} (status {resp.status_code}), skipping.")
            return None

        if data.get("info") != "成功":
            print(data.get("info"))
            raise AssertionError(f"{username}: {data.get('info')}")
        return data.get("row")

    def get_single_json_debug(
        self,
        URL: str,
        token: str,
        data: Any = None,
    ) -> requests.Response:
        method = "POST" if data is not None else "GET"
        return self.post(
            URL,
            data=data,
            # params=params,
            extra_headers={"authorization": f"Bearer {token}"},
        )

    def get_json(
        self,
        URL: str,
        token: str,
        data: Any = None,
    ) -> requests.Response:
        method = "POST" if data is not None else "GET"
        return self.post(
            URL,
            data=data,
            # params=params,
            extra_headers={"authorization": f"Bearer {token}"},
        ).json()

    def get_multiple_json(
        self,
        URL: str,
        token: str,
        data: Any = None,
    ) -> requests.Response:
        extra = {
            "authorization": f"Bearer {token}",
            "content-type": "application/json",
        }
        if data is not None:
            # JSON body + JSON content-type
            return self.post(URL, json=data, extra_headers=extra)
        # no body
        return self.get(URL, extra_headers=extra)

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> "ApiClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()