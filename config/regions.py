from __future__ import annotations
"""
Supported regions and their corresponding Garena base URLs.
All 14 regions as of OB53 (April 2026).
"""

REGION_MAP: dict[str, str] = {
    "IND": "https://client.ind.freefiremobile.com",
    "BR": "https://client.br.freefiremobile.com",
    "SG": "https://client.sg.freefiremobile.com",
    "RU": "https://client.ru.freefiremobile.com",
    "ID": "https://client.id.freefiremobile.com",
    "TW": "https://client.tw.freefiremobile.com",
    "US": "https://client.us.freefiremobile.com",
    "VN": "https://client.vn.freefiremobile.com",
    "TH": "https://client.th.freefiremobile.com",
    "ME": "https://client.me.freefiremobile.com",
    "PK": "https://client.pk.freefiremobile.com",
    "CIS": "https://client.cis.freefiremobile.com",
    "BD": "https://client.bd.freefiremobile.com",
    "NA": "https://client.us.freefiremobile.com",
}

def get_region_url(region: str) -> str:
    """Returns the base URL for a given region code."""
    return REGION_MAP.get(region.upper())
