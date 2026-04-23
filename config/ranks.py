from typing import Optional

"""
Mapping for rank integer codes to human-readable rank names.
Supports both Battle Royale (BR) and Clash Squad (CS) modes.
"""

# Mapping for common Garena rank codes (OB53)
RANK_MAP: dict[int, str] = {
    0: "Unranked",
    # Bronze (1-3)
    101: "Bronze I", 102: "Bronze II", 103: "Bronze III",
    # Silver (1-3)
    201: "Silver I", 202: "Silver II", 203: "Silver III",
    # Gold (1-4)
    301: "Gold I", 302: "Gold II", 303: "Gold III", 304: "Gold IV",
    # Platinum (1-4)
    401: "Platinum I", 402: "Platinum II", 403: "Platinum III", 404: "Platinum IV",
    # Diamond (1-4)
    501: "Diamond I", 502: "Diamond II", 503: "Diamond III", 504: "Diamond IV",
    # Heroic
    601: "Heroic",
    # Grandmaster
    701: "Grandmaster",
}

def get_rank_name(rank_code: Optional[int]) -> str:
    """
    Translates an integer rank code into its human-readable equivalent.
    Includes fallbacks for unknown codes based on typical range patterns.
    """
    if rank_code is None:
        return "Unknown"

    if rank_code in RANK_MAP:
        return RANK_MAP[rank_code]

    # Fallback heuristic logic if exact code isn't in map
    if 101 <= rank_code <= 103: return f"Bronze {rank_code - 100}"
    if 201 <= rank_code <= 203: return f"Silver {rank_code - 200}"
    if 301 <= rank_code <= 304: return f"Gold {rank_code - 300}"
    if 401 <= rank_code <= 404: return f"Platinum {rank_code - 400}"
    if 501 <= rank_code <= 504: return f"Diamond {rank_code - 500}"
    if 600 <= rank_code <= 699: return "Heroic"
    if 700 <= rank_code: return "Grandmaster"

    return "Unknown"
