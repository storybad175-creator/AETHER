# Maps integer Protobuf field IDs to semantic names
# Derived from community reverse-engineering of the OB53 wire protocol

PROTO_FIELD_MAP = {
    # Account Info
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
    12: "created_at",
    13: "last_login",
    14: "account_type",

    # Ranks
    20: "br_rank_code",
    21: "br_points",
    22: "br_max_rank_code",
    23: "cs_rank_code",
    24: "cs_points",

    # Stats - BR
    30: "br_solo_matches",
    31: "br_solo_wins",
    32: "br_solo_kills",
    33: "br_solo_deaths",
    34: "br_solo_headshots",
    35: "br_solo_damage",

    40: "br_duo_matches",
    41: "br_duo_wins",
    42: "br_duo_kills",
    43: "br_duo_deaths",
    44: "br_duo_headshots",
    45: "br_duo_damage",

    50: "br_squad_matches",
    51: "br_squad_wins",
    52: "br_squad_kills",
    53: "br_squad_deaths",
    54: "br_squad_headshots",
    55: "br_squad_damage",

    # Stats - CS
    60: "cs_matches",
    61: "cs_wins",
    62: "cs_kills",

    # Guild
    70: "guild_id",
    71: "guild_name",
    72: "guild_level",
    73: "guild_member_count",
    74: "guild_capacity",
    75: "guild_leader_uid",
    76: "guild_leader_name",
    77: "guild_leader_level",

    # Pet
    80: "pet_name",
    81: "pet_level",
    82: "pet_exp",
    83: "pet_skill",
    84: "pet_skin_id",
    85: "pet_selected",

    # Cosmetics
    90: "avatar_id",
    91: "banner_id",
    92: "pin_id",
    93: "character_id",
    94: "equipped_outfit_ids",
    95: "equipped_weapon_skin_ids",

    # Pass & Credit
    100: "booyah_pass_level",
    101: "fire_pass_status",
    102: "fire_pass_badge_count",
    103: "credit_score",
    104: "credit_reward_claimed",
    105: "credit_summary_period",

    # Ban
    110: "is_banned",
    111: "ban_period",
    112: "ban_type"
}
