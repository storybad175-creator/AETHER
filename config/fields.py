"""
Protobuf field ID mappings for request and response messages.
Based on community reverse-engineering of the Garena Free Fire wire protocol (OB53).
"""

# Request Field IDs (Strategy B)
REQUEST_FIELD_MAP = {
    1: "uid",
    2: "region",
    3: "version",
}

# Response Field IDs (Strategy B) - Grouped by Category
# The top-level fields (1-9) represent logical data blocks.
RESPONSE_FIELD_MAP = {
    # --- Top-Level Message Blocks ---
    1: "account",
    2: "rank",
    3: "stats",
    4: "social",
    5: "pet",
    6: "cosmetics",
    7: "pass_info",
    8: "credit",
    9: "ban",

    # --- 1: Account Info Sub-fields ---
    101: "uid",
    102: "nickname",
    103: "level",
    104: "exp",
    105: "region",
    106: "season_id",
    107: "preferred_mode",
    108: "language",
    109: "signature",
    110: "honor_score",
    111: "total_likes",
    112: "ob_version",
    113: "created_at_epoch",
    114: "last_login_epoch",
    115: "account_type",

    # --- 2: Rank Info Sub-fields ---
    201: "br_rank_code",
    202: "br_points",
    203: "br_max_rank_code",
    204: "br_visible",
    205: "cs_rank_code",
    206: "cs_points",
    207: "cs_visible",

    # --- 3: Stats Info Sub-fields ---
    301: "br_solo",
    302: "br_duo",
    303: "br_squad",
    304: "cs_ranked",

    # --- StatLine common sub-fields (used within 301-304) ---
    401: "matches",
    402: "wins",
    403: "kills",
    404: "deaths",
    405: "headshots",
    406: "avg_damage",
    407: "booyahs",

    # --- 4: Social / Guild Sub-fields ---
    501: "guild_id",
    502: "guild_name",
    503: "guild_level",
    504: "guild_member_count",
    505: "guild_capacity",
    506: "guild_leader_uid",
    507: "guild_leader_nickname",
    508: "guild_leader_level",
    509: "guild_leader_rank",

    # --- 5: Pet Info Sub-fields ---
    601: "pet_name",
    602: "pet_level",
    603: "pet_exp",
    604: "pet_active_skill",
    605: "pet_skin_id",
    606: "pet_is_selected",

    # --- 6: Cosmetics Sub-fields ---
    701: "avatar_id",
    702: "banner_id",
    703: "pin_id",
    704: "character_id",
    705: "equipped_outfit_ids",
    706: "equipped_weapon_skin_ids",

    # --- 7: Pass Info Sub-fields ---
    801: "booyah_pass_level",
    802: "fire_pass_status",
    803: "fire_pass_badge_count",

    # --- 8: Credit Info Sub-fields ---
    901: "credit_score",
    902: "credit_reward_claimed",
    903: "credit_summary_period",

    # --- 9: Ban Info Sub-fields ---
    1001: "is_banned",
    1002: "ban_period",
    1003: "ban_type",
}
