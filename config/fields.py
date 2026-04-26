"""
Protobuf field ID mappings for request and response messages.
Based on community reverse-engineering of the Garena Free Fire wire protocol.
"""

# --- Request Field IDs ---
FLD_REQ_UID = 1
FLD_REQ_REGION = 2
FLD_REQ_VERSION = 3

REQUEST_FIELD_MAP = {
    FLD_REQ_UID: "uid",
    FLD_REQ_REGION: "region",
    FLD_REQ_VERSION: "version",
}

# --- Response Field IDs (Top Level) ---
FLD_ACCOUNT = 1
FLD_RANK = 2
FLD_STATS = 3
FLD_SOCIAL = 4
FLD_PET = 5
FLD_COSMETICS = 6
FLD_PASS_INFO = 7
FLD_CREDIT = 8
FLD_BAN = 9

# --- Account Sub-fields ---
FLD_ACC_UID = 101
FLD_ACC_NICKNAME = 102
FLD_ACC_LEVEL = 103
FLD_ACC_EXP = 104
FLD_ACC_REGION = 105
FLD_ACC_SEASON_ID = 106
FLD_ACC_PREF_MODE = 107
FLD_ACC_LANG = 108
FLD_ACC_SIGNATURE = 109
FLD_ACC_HONOR = 110
FLD_ACC_LIKES = 111
FLD_ACC_OB_VERSION = 112
FLD_ACC_CREATED_AT = 113
FLD_ACC_LAST_LOGIN = 114
FLD_ACC_TYPE = 115

# --- Rank Sub-fields ---
FLD_RANK_BR_CODE = 201
FLD_RANK_BR_POINTS = 202
FLD_RANK_BR_MAX_CODE = 203
FLD_RANK_BR_VISIBLE = 204
FLD_RANK_CS_CODE = 205
FLD_RANK_CS_POINTS = 206
FLD_RANK_CS_VISIBLE = 207

# --- Stats Sub-fields ---
FLD_STATS_BR_SOLO = 301
FLD_STATS_BR_DUO = 302
FLD_STATS_BR_SQUAD = 303
FLD_STATS_CS_RANKED = 304

# --- StatLine sub-fields ---
FLD_SL_MATCHES = 401
FLD_SL_WINS = 402
FLD_SL_KILLS = 403
FLD_SL_DEATHS = 404
FLD_SL_HEADSHOTS = 405
FLD_SL_AVG_DMG = 406
FLD_SL_BOOYAHS = 407

# --- Social / Guild Sub-fields ---
FLD_SOC_GUILD_ID = 501
FLD_SOC_GUILD_NAME = 502
FLD_SOC_GUILD_LEVEL = 503
FLD_SOC_GUILD_MEMBERS = 504
FLD_SOC_GUILD_CAPACITY = 505
FLD_SOC_GUILD_LEADER_UID = 506
FLD_SOC_GUILD_LEADER_NICK = 507
FLD_SOC_GUILD_LEADER_LVL = 508
FLD_SOC_GUILD_LEADER_RANK = 509

# --- Pet Sub-fields ---
FLD_PET_NAME = 601
FLD_PET_LEVEL = 602
FLD_PET_EXP = 603
FLD_PET_SKILL = 604
FLD_PET_SKIN = 605
FLD_PET_SELECTED = 606

# --- Cosmetics Sub-fields ---
FLD_COSM_AVATAR = 701
FLD_COSM_BANNER = 702
FLD_COSM_PIN = 703
FLD_COSM_CHAR = 704
FLD_COSM_OUTFITS = 705
FLD_COSM_WEAPONS = 706

# --- Pass Sub-fields ---
FLD_PASS_BP_LEVEL = 801
FLD_PASS_FP_STATUS = 802
FLD_PASS_FP_BADGES = 803

# --- Credit Sub-fields ---
FLD_CRED_SCORE = 901
FLD_CRED_REWARD = 902
FLD_CRED_SUMMARY = 903

# --- Ban Sub-fields ---
FLD_BAN_STATUS = 1001
FLD_BAN_PERIOD = 1002
FLD_BAN_TYPE = 1003

# Response Field ID → Name Mapping
RESPONSE_FIELD_MAP = {
    FLD_ACCOUNT: "account",
    FLD_ACC_UID: "uid",
    FLD_ACC_NICKNAME: "nickname",
    FLD_ACC_LEVEL: "level",
    FLD_ACC_EXP: "exp",
    FLD_ACC_REGION: "region",
    FLD_ACC_SEASON_ID: "season_id",
    FLD_ACC_PREF_MODE: "preferred_mode",
    FLD_ACC_LANG: "language",
    FLD_ACC_SIGNATURE: "signature",
    FLD_ACC_HONOR: "honor_score",
    FLD_ACC_LIKES: "total_likes",
    FLD_ACC_OB_VERSION: "ob_version",
    FLD_ACC_CREATED_AT: "created_at_epoch",
    FLD_ACC_LAST_LOGIN: "last_login_epoch",
    FLD_ACC_TYPE: "account_type",

    FLD_RANK: "rank",
    FLD_RANK_BR_CODE: "br_rank_code",
    FLD_RANK_BR_POINTS: "br_points",
    FLD_RANK_BR_MAX_CODE: "br_max_rank_code",
    FLD_RANK_BR_VISIBLE: "br_visible",
    FLD_RANK_CS_CODE: "cs_rank_code",
    FLD_RANK_CS_POINTS: "cs_points",
    FLD_RANK_CS_VISIBLE: "cs_visible",

    FLD_STATS: "stats",
    FLD_STATS_BR_SOLO: "br_solo",
    FLD_STATS_BR_DUO: "br_duo",
    FLD_STATS_BR_SQUAD: "br_squad",
    FLD_STATS_CS_RANKED: "cs_ranked",

    FLD_SL_MATCHES: "matches",
    FLD_SL_WINS: "wins",
    FLD_SL_KILLS: "kills",
    FLD_SL_DEATHS: "deaths",
    FLD_SL_HEADSHOTS: "headshots",
    FLD_SL_AVG_DMG: "avg_damage",
    FLD_SL_BOOYAHS: "booyahs",

    FLD_SOCIAL: "social",
    FLD_SOC_GUILD_ID: "guild_id",
    FLD_SOC_GUILD_NAME: "guild_name",
    FLD_SOC_GUILD_LEVEL: "guild_level",
    FLD_SOC_GUILD_MEMBERS: "guild_member_count",
    FLD_SOC_GUILD_CAPACITY: "guild_capacity",
    FLD_SOC_GUILD_LEADER_UID: "guild_leader_uid",
    FLD_SOC_GUILD_LEADER_NICK: "guild_leader_nickname",
    FLD_SOC_GUILD_LEADER_LVL: "guild_leader_level",
    FLD_SOC_GUILD_LEADER_RANK: "guild_leader_rank",

    FLD_PET: "pet",
    FLD_PET_NAME: "pet_name",
    FLD_PET_LEVEL: "pet_level",
    FLD_PET_EXP: "pet_exp",
    FLD_PET_SKILL: "pet_active_skill",
    FLD_PET_SKIN: "pet_skin_id",
    FLD_PET_SELECTED: "pet_is_selected",

    FLD_COSMETICS: "cosmetics",
    FLD_COSM_AVATAR: "avatar_id",
    FLD_COSM_BANNER: "banner_id",
    FLD_COSM_PIN: "pin_id",
    FLD_COSM_CHAR: "character_id",
    FLD_COSM_OUTFITS: "equipped_outfit_ids",
    FLD_COSM_WEAPONS: "equipped_weapon_skin_ids",

    FLD_PASS_INFO: "pass_info",
    FLD_PASS_BP_LEVEL: "booyah_pass_level",
    FLD_PASS_FP_STATUS: "fire_pass_status",
    FLD_PASS_FP_BADGES: "fire_pass_badge_count",

    FLD_CREDIT: "credit",
    FLD_CRED_SCORE: "credit_score",
    FLD_CRED_REWARD: "credit_reward_claimed",
    FLD_CRED_SUMMARY: "credit_summary_period",

    FLD_BAN: "ban",
    FLD_BAN_STATUS: "is_banned",
    FLD_BAN_PERIOD: "ban_period",
    FLD_BAN_TYPE: "ban_type",
}
