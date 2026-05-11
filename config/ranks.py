"""
Mapping for rank integer codes to human-readable rank names.
Supports both Battle Royale (BR) and Clash Squad (CS) modes.
"""

# Comprehensive Rank Mapping (OB53 Standard)
RANK_MAP: dict[int, str] = {
    0: "Unranked",

    # Bronze (101-103)
    101: "Bronze I", 102: "Bronze II", 103: "Bronze III",

    # Silver (201-203)
    201: "Silver I", 202: "Silver II", 203: "Silver III",

    # Gold (301-304)
    301: "Gold I", 302: "Gold II", 303: "Gold III", 304: "Gold IV",

    # Platinum (401-404)
    401: "Platinum I", 402: "Platinum II", 403: "Platinum III", 404: "Platinum IV",

    # Diamond (501-504)
    501: "Diamond I", 502: "Diamond II", 503: "Diamond III", 504: "Diamond IV",

    # Heroic (601)
    601: "Heroic",

    # Master (602) - Sometimes used in specific seasons
    602: "Master",

    # Grandmaster (701)
    701: "Grandmaster",

    # CS Specific (Often uses different prefix)
    801: "CS-Bronze", 802: "CS-Silver", 803: "CS-Gold",
    804: "CS-Platinum", 805: "CS-Diamond", 806: "CS-Heroic",
    807: "CS-Grandmaster"
}

def get_rank_name(rank_code: int | None) -> str:
    """Translates integer rank code to string name with intelligent fallbacks."""
    if rank_code is None or rank_code == 0:
        return "Unranked"

    if rank_code in RANK_MAP:
        return RANK_MAP[rank_code]

    # Fallback/Default naming for unknown but structured codes
    if 1 <= rank_code <= 3: return f"Bronze {rank_code}"
    if 4 <= rank_code <= 6: return f"Silver {rank_code-3}"
    if 7 <= rank_code <= 10: return f"Gold {rank_code-6}"
    if 11 <= rank_code <= 14: return f"Platinum {rank_code-10}"
    if 15 <= rank_code <= 18: return f"Diamond {rank_code-14}"
    if rank_code == 19: return "Heroic"
    if rank_code >= 20 and rank_code < 100: return "Grandmaster"

    return f"Rank {rank_code}"
