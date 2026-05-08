"""
Rank ID mappings for Battle Royale and Clash Squad modes.
Used to translate integer rank codes from Garena into human-readable strings.
"""

RANK_MAP = {
    # --- Battle Royale (1xx) ---
    0: "Unranked",
    101: "Bronze I",
    102: "Bronze II",
    103: "Bronze III",
    104: "Silver I",
    105: "Silver II",
    106: "Silver III",
    107: "Gold I",
    108: "Gold II",
    109: "Gold III",
    110: "Gold IV",
    111: "Platinum I",
    112: "Platinum II",
    113: "Platinum III",
    114: "Platinum IV",
    115: "Diamond I",
    116: "Diamond II",
    117: "Diamond III",
    118: "Diamond IV",
    119: "Heroic",
    120: "Elite Heroic",
    121: "Master",
    122: "Elite Master",
    123: "Grandmaster",

    # --- Clash Squad (2xx) ---
    201: "Bronze I",
    202: "Bronze II",
    203: "Bronze III",
    204: "Silver I",
    205: "Silver II",
    206: "Silver III",
    207: "Gold I",
    208: "Gold II",
    209: "Gold III",
    210: "Gold IV",
    211: "Platinum I",
    212: "Platinum II",
    213: "Platinum III",
    214: "Platinum IV",
    215: "Diamond I",
    216: "Diamond II",
    217: "Diamond III",
    218: "Diamond IV",
    219: "Heroic",
    220: "Elite Heroic",
    221: "Master",
    222: "Elite Master",
    223: "Grandmaster",

    # --- Other Ranks / Legacy ---
    601: "Heroic",
    602: "Grandmaster",
}

def get_rank_name(rank_code: int | None) -> str:
    """Returns the human-readable rank name for a given code."""
    if rank_code is None:
        return "Unranked"
    return RANK_MAP.get(rank_code, f"Rank {rank_code}")
