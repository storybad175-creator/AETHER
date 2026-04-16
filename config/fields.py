# Protobuf field ID mappings (community-extracted)
# Maps integer field IDs in the wire protocol to semantic names

PROTO_FIELD_MAP = {
    # Request fields
    "request": {
        1: "uid",
        2: "region",
    },

    # Response fields (Account Info)
    "account": {
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
    },

    # Rank Info
    "rank": {
        1: "br_rank_code",
        2: "br_points",
        3: "br_max_rank_code",
        4: "cs_rank_code",
        5: "cs_points",
        6: "rank_visible",
    },

    # Stats (BR)
    "br_stats": {
        1: "solo_matches",
        2: "solo_wins",
        3: "solo_kills",
        4: "solo_deaths",
        5: "solo_headshots",
        6: "solo_damage",
        7: "duo_matches",
        8: "duo_wins",
        9: "duo_kills",
        10: "duo_deaths",
        11: "duo_headshots",
        12: "duo_damage",
        13: "squad_matches",
        14: "squad_wins",
        15: "squad_kills",
        16: "squad_deaths",
        17: "squad_headshots",
        18: "squad_damage",
    },

    # Stats (CS)
    "cs_stats": {
        1: "matches",
        2: "wins",
        3: "kills",
        4: "kd_ratio_raw",
    },

    # Guild Info
    "guild": {
        1: "id",
        2: "name",
        3: "level",
        4: "member_count",
        5: "capacity",
        6: "leader_uid",
        7: "leader_nickname",
        8: "leader_level",
        9: "leader_rank_code",
    },

    # Pet Info
    "pet": {
        1: "name",
        2: "level",
        3: "exp",
        4: "active_skill",
        5: "skin_id",
        6: "is_selected",
    },

    # Cosmetics
    "cosmetics": {
        1: "avatar_id",
        2: "banner_id",
        3: "pin_id",
        4: "character_id",
        5: "equipped_outfit_ids",
        6: "equipped_weapon_skin_ids",
    },

    # Booyah/Fire Pass
    "pass": {
        1: "booyah_pass_level",
        2: "fire_pass_status_code",
        3: "fire_pass_badge_count",
    },

    # Credit Score
    "credit": {
        1: "score",
        2: "reward_claimed",
        3: "summary_period",
    },

    # Ban Info
    "ban": {
        1: "is_banned",
        2: "ban_period_epoch",
        3: "ban_type",
    }
}
