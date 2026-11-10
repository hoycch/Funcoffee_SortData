from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Union
from urllib.parse import urlparse


# Mapping of area_code → CloudFront base URL
_Server_URLS = {
    "HK": "https://dhzx6onj3zqr3.cloudfront.net",
    "SG": "https://d1vqujo8itcqpm.cloudfront.net",
    "KR": "https://d29m8ihcfwtow5.cloudfront.net",
}


@dataclass(frozen=True)
class Config:
    """Immutable configuration for a given area_code."""

    BASE_URL: str
    LOGIN_URL: str
    AUTH_CHECK_URL: str
    USER_INFO_URL: str
    TEAM_INFO_URL: str
    TEAM_MEMBERS_URL: str
    CAPITAL_FLOW_URL: str
    INVEST_RECORD_URL: str
    INPUT_FILE: str
    OUTPUT_DIR: Path
    DEVICE_ID: str
    REQUEST_TIMEOUT: int
    MIN_DELAY: float
    MAX_DELAY: float
    VERIFY_SSL: bool

    # ── Base HTTP header values (all header data lives here) ──
    HOST: str
    CONTENT_TYPE: str
    COOKIE: str
    CHECK_IP_REALIP: str
    CONNECTION: str
    ACCEPT: str
    USER_AGENT: str
    ACCEPT_LANGUAGE: str
    ACCEPT_ENCODING: str
    BUSINESSLANG: str

    @property
    def host(self) -> str:
        """Alias for HOST (hostname for the Host header)."""
        return self.HOST


def get_config(server_code: Union[int, str]) -> Config:
    code = str(server_code).strip()
    base_url = _Server_URLS.get(code)
    if base_url is None:
        supported = ", ".join(sorted(_Server_URLS.keys()))
        raise ValueError(
            f"Unsupported area_code '{server_code}'. "
            f"Supported values: {supported}"
        )

    host = urlparse(base_url).netloc

    return Config(
        BASE_URL=base_url,
        LOGIN_URL=f"{base_url}/api/user/login",
        AUTH_CHECK_URL=f"{base_url}/api/invest/auth/check",
        USER_INFO_URL=f"{base_url}/api/user/getUserInfo",
        TEAM_INFO_URL=f"{base_url}/api/user/team/getTeamInfo",
        TEAM_MEMBERS_URL=f"{base_url}/api/user/team/getTeamMemberList",
        CAPITAL_FLOW_URL = F"{base_url}/api/user/capital/flow/page",
        INVEST_RECORD_URL = F"{base_url}/api/invest/record/page",
        INPUT_FILE="successful.csv",
        OUTPUT_DIR=Path("results"),
        DEVICE_ID="5f3fbd80c94874e6789e781ad0dd9efe",
        REQUEST_TIMEOUT=30,
        MIN_DELAY=0.5,
        MAX_DELAY=2.0,
        VERIFY_SSL=False,
        # Header values
        HOST=host,
        CONTENT_TYPE="application/x-www-form-urlencoded",
        COOKIE="SITE_TOTAL_ID=4d913556bb7defb4af2006d9732e48e6",
        CHECK_IP_REALIP="221.127.137.240",
        CONNECTION="keep-alive",
        ACCEPT="*/*",
        USER_AGENT=(
            "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
            "Html5Plus/1.0 (Immersed/20) uni-app"
        ),
        ACCEPT_LANGUAGE="zh_HANT",
        ACCEPT_ENCODING="gzip, deflate, br",
        BUSINESSLANG="zh_HANT",
    )


