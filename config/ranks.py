from __future__ import annotations
"""
Mapping for rank integer codes to human-readable rank names.
Supports both Battle Royale (BR) and Clash Squad (CS) modes.
"""

# Common Rank Mapping
RANK_MAP: dict[int, str] = {
    0: "Unranked",
    # Bronze
    101: "Bronze I", 102: "Bronze II", 103: "Bronze III",
    # Silver
    201: "Silver I", 202: "Silver II", 203: "Silver III",
    # Gold
    301: "Gold I", 302: "Gold II", 303: "Gold III", 304: "Gold IV",
    # Platinum
    401: "Platinum I", 402: "Platinum II", 403: "Platinum III", 404: "Platinum IV",
    # Diamond
    501: "Diamond I", 502: "Diamond II", 503: "Diamond III", 504: "Diamond IV",
    # Heroic
    601: "Heroic",
    # Grandmaster
    701: "Grandmaster",
}

def get_rank_name(rank_code: int | None) -> str:
    """Translates integer rank code to string name."""
    if rank_code is None:
        return "Unknown"

    if rank_code in RANK_MAP:
        return RANK_MAP[rank_code]

    # Fallback/Default naming for unexpected codes
    if 1 <= rank_code <= 3: return f"Bronze {rank_code}"
    if 4 <= rank_code <= 6: return f"Silver {rank_code-3}"
    if 7 <= rank_code <= 10: return f"Gold {rank_code-6}"
    if 11 <= rank_code <= 14: return f"Platinum {rank_code-10}"
    if 15 <= rank_code <= 18: return f"Diamond {rank_code-14}"
    if rank_code == 19: return "Heroic"
    if rank_code >= 20: return "Grandmaster"

    return "Unknown"
