# Protobuf field ID mapping (Community Documented)

PROTO_FIELD_MAP = {
    # Request Fields
    "request": {
        1: "uid",
        2: "region",
    },
    # Response Fields (Top-level PlayerData)
    "response": {
        1: "account",
        2: "rank",
        3: "stats",
        4: "social",
        5: "pet",
        6: "cosmetics",
        7: "pass_info",
        8: "credit",
        9: "ban",
    },
    # Account Fields
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
    # Rank Fields
    "rank": {
        1: "battle_royale",
        2: "clash_squad",
    },
    "rank_detail": {
        1: "rank_code",
        2: "points",
        3: "max_rank_code",
        4: "visible",
    },
    # Stats Fields
    "stats": {
        1: "battle_royale",
        2: "clash_squad",
    },
    "br_stats": {
        1: "solo",
        2: "duo",
        3: "squad",
    },
    "stat_line": {
        1: "matches",
        2: "wins",
        3: "kills",
        4: "deaths",
        5: "headshots",
        6: "avg_damage_per_match",
    },
    "cs_stats": {
        1: "ranked",
    },
    "cs_stat_line": {
        1: "matches",
        2: "wins",
        3: "kills",
    },
    # Social Fields
    "social": {
        1: "guild",
    },
    "guild": {
        1: "id",
        2: "name",
        3: "level",
        4: "member_count",
        5: "capacity",
        6: "leader",
    },
    "guild_leader": {
        1: "uid",
        2: "nickname",
        3: "level",
        4: "rank_code",
    },
    # Pet Fields
    "pet": {
        1: "name",
        2: "level",
        3: "exp",
        4: "active_skill",
        5: "skin_id",
        6: "is_selected",
    },
    # Cosmetics Fields
    "cosmetics": {
        1: "avatar_id",
        2: "banner_id",
        3: "pin_id",
        4: "character_id",
        5: "equipped_outfit_ids",
        6: "equipped_weapon_skin_ids",
    },
    # Pass Info
    "pass_info": {
        1: "booyah_pass_level",
        2: "fire_pass_status",
        3: "fire_pass_badge_count",
    },
    # Credit Info
    "credit": {
        1: "score",
        2: "reward_claimed",
        3: "summary_period",
    },
    # Ban Info
    "ban": {
        1: "is_banned",
        2: "ban_period",
        3: "ban_type",
    }
}
