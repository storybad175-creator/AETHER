# Maps protobuf field IDs to semantic names (community-documented)
PROTO_FIELD_MAP = {
    # Request fields
    1: "uid",
    2: "region",

    # Response fields (Account Info)
    10: "nickname",
    11: "level",
    12: "exp",
    13: "region_code",
    14: "season_id",
    15: "preferred_mode",
    16: "language",
    17: "signature",
    18: "honor_score",
    19: "total_likes",
    20: "ob_version",
    21: "created_at",
    22: "last_login",
    23: "account_type",

    # Rank Info
    30: "br_rank_code",
    31: "br_points",
    32: "br_max_rank_code",
    33: "br_rank_visible",
    34: "cs_rank_code",
    35: "cs_points",
    36: "cs_rank_visible",

    # Stats (BR)
    40: "br_solo_matches",
    41: "br_solo_wins",
    42: "br_solo_kills",
    43: "br_solo_deaths",
    44: "br_solo_headshots",
    45: "br_solo_damage",
    46: "br_duo_matches",
    47: "br_duo_wins",
    48: "br_duo_kills",
    49: "br_duo_deaths",
    50: "br_duo_headshots",
    51: "br_duo_damage",
    52: "br_squad_matches",
    53: "br_squad_wins",
    54: "br_squad_kills",
    55: "br_squad_deaths",
    56: "br_squad_headshots",
    57: "br_squad_damage",

    # Stats (CS)
    60: "cs_matches",
    61: "cs_wins",
    62: "cs_kills",

    # Guild Info
    70: "guild_id",
    71: "guild_name",
    72: "guild_level",
    73: "guild_member_count",
    74: "guild_capacity",
    75: "guild_leader_uid",
    76: "guild_leader_nickname",
    77: "guild_leader_level",
    78: "guild_leader_rank",

    # Pet Info
    80: "pet_name",
    81: "pet_level",
    82: "pet_exp",
    83: "pet_active_skill",
    84: "pet_skin_id",
    85: "pet_is_selected",

    # Cosmetics
    90: "avatar_id",
    91: "banner_id",
    92: "pin_id",
    93: "character_id",
    94: "equipped_outfits",
    95: "equipped_weapons",

    # Pass Info
    100: "bp_level",
    101: "fp_status",
    102: "fp_badges",

    # Credit Info
    110: "credit_score",
    111: "credit_reward_claimed",
    112: "credit_summary_period",

    # Ban Info
    120: "is_banned",
    121: "ban_period",
    122: "ban_type"
}
