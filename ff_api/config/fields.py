# PROTO_FIELD_MAP maps integer protobuf field IDs to semantic names
# (community-documented field mappings)

PROTO_FIELD_MAP: dict[int, str] = {
    1: "uid",
    2: "nickname",
    3: "level",
    4: "exp",
    5: "region",
    6: "season_id",
    7: "preferred_mode",
    8: "language",
    9: "signature",
    10: "honor_score",
    11: "total_likes",
    12: "ob_version",
    13: "created_at_epoch",
    14: "last_login_epoch",
    15: "account_type",

    # Rank Info
    20: "br_rank_code",
    21: "br_points",
    22: "br_max_rank_code",
    23: "br_visible",
    24: "cs_rank_code",
    25: "cs_points",
    26: "cs_visible",

    # Stats - Battle Royale Solo
    30: "br_solo_matches",
    31: "br_solo_wins",
    32: "br_solo_kills",
    33: "br_solo_deaths",
    34: "br_solo_headshots",
    35: "br_solo_damage",

    # Stats - Battle Royale Duo
    40: "br_duo_matches",
    41: "br_duo_wins",
    42: "br_duo_kills",
    43: "br_duo_deaths",
    44: "br_duo_headshots",
    45: "br_duo_damage",

    # Stats - Battle Royale Squad
    50: "br_squad_matches",
    51: "br_squad_wins",
    52: "br_squad_kills",
    53: "br_squad_deaths",
    54: "br_squad_headshots",
    55: "br_squad_damage",

    # Stats - Clash Squad Ranked
    60: "cs_matches",
    61: "cs_wins",
    62: "cs_kills",

    # Social - Guild
    70: "guild_id",
    71: "guild_name",
    72: "guild_level",
    73: "guild_member_count",
    74: "guild_capacity",
    75: "guild_leader_uid",
    76: "guild_leader_nickname",
    77: "guild_leader_level",
    78: "guild_leader_rank_name",

    # Pet
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
    94: "equipped_outfit_ids",
    95: "equipped_weapon_skin_ids",

    # Pass
    100: "booyah_pass_level",
    101: "fire_pass_status",
    102: "fire_pass_badge_count",

    # Credit
    110: "credit_score",
    111: "credit_reward_claimed",
    112: "credit_summary_period",

    # Ban
    120: "is_banned",
    121: "ban_period",
    122: "ban_type",
}
