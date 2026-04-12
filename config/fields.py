# Community-documented Protobuf field ID mappings for request and response messages

# Field IDs for the request message
REQUEST_FIELD_MAP = {
    1: "uid",
    2: "region",
    3: "version",
}

# Field IDs for the player response message
PROTO_FIELD_MAP = {
    # Account Info
    1: "account_info",
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
    20: "rank_info",
    21: "br_rank_code",
    22: "br_points",
    23: "br_max_rank_code",
    24: "br_visible",
    25: "cs_rank_code",
    26: "cs_points",
    27: "cs_visible",

    # Stats Info
    30: "stats_info",
    31: "br_solo_stats",
    32: "br_duo_stats",
    33: "br_squad_stats",
    34: "cs_ranked_stats",

    # Social Info
    40: "social_info",
    41: "guild_info",
    42: "guild_id",
    43: "guild_name",
    44: "guild_level",
    45: "guild_member_count",
    46: "guild_capacity",
    47: "guild_leader_info",

    # Pet Info
    50: "pet_info",
    51: "pet_name",
    52: "pet_level",
    53: "pet_exp",
    54: "pet_active_skill",
    55: "pet_skin_id",
    56: "pet_is_selected",

    # Cosmetics Info
    60: "cosmetics_info",
    61: "avatar_id",
    62: "banner_id",
    63: "pin_id",
    64: "character_id",
    65: "equipped_outfit_ids",
    66: "equipped_weapon_skin_ids",

    # Pass Info
    70: "pass_info",
    71: "booyah_pass_level",
    72: "fire_pass_status",
    73: "fire_pass_badge_count",

    # Credit Info
    80: "credit_info",
    81: "credit_score",
    82: "credit_reward_claimed",
    83: "credit_summary_period",

    # Ban Info
    90: "ban_info",
    91: "is_banned",
    92: "ban_period",
    93: "ban_type",
}
