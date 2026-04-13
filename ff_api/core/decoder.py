from typing import Any, Dict
from datetime import datetime, timezone
from ff_api.core.crypto import aes_decrypt
from ff_api.core.proto import decode_response
from ff_api.config.ranks import RANK_MAP
from ff_api.api.schemas import PlayerData, AccountInfo, BRRankInfo, RankInfo, ModeRankInfo, StatLine, BRStats, CSRankedStats, StatsInfo, SocialInfo, GuildInfo, GuildLeader, PetInfo, CosmeticsInfo, PassInfo, CreditInfo, BanInfo
from ff_api.api.errors import FFError, ErrorCode

def decode_player_data(raw_bytes: bytes) -> PlayerData:
    try:
        decrypted = aes_decrypt(raw_bytes)
    except Exception:
        raise FFError(ErrorCode.DECODE_ERROR, "Failed to decrypt response.", extra={"possible_key_rotation": True})

    try:
        raw_dict = decode_response(decrypted)
    except Exception:
        raise FFError(ErrorCode.DECODE_ERROR, "Failed to decode protobuf response.")

    if not raw_dict or "uid" not in raw_dict:
        raise FFError(ErrorCode.PLAYER_NOT_FOUND, "Decoded response contains no player data.")

    # Helper for timestamp conversion
    def format_ts(ts: int | None) -> str | None:
        if not ts: return None
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace("+00:00", "Z")

    # Helper for rank translation
    def get_rank_name(code: int | None) -> str | None:
        if code is None: return None
        return RANK_MAP.get(code, "Unknown")

    # Mapping to Pydantic Model
    account = AccountInfo(
        uid=str(raw_dict.get("uid")),
        nickname=raw_dict.get("nickname", "Unknown"),
        level=raw_dict.get("level", 0),
        exp=raw_dict.get("exp", 0),
        region=raw_dict.get("region", "Unknown"),
        season_id=raw_dict.get("season_id", 0),
        preferred_mode=raw_dict.get("preferred_mode", "Unknown"),
        language=raw_dict.get("language", "Unknown"),
        signature=raw_dict.get("signature", ""),
        honor_score=raw_dict.get("honor_score", 0),
        total_likes=raw_dict.get("total_likes", 0),
        ob_version=raw_dict.get("ob_version", "Unknown"),
        created_at_epoch=raw_dict.get("created_at_epoch", 0),
        created_at=format_ts(raw_dict.get("created_at_epoch")),
        last_login_epoch=raw_dict.get("last_login_epoch", 0),
        last_login=format_ts(raw_dict.get("last_login_epoch")),
        account_type=raw_dict.get("account_type", "Normal")
    )

    rank = ModeRankInfo(
        battle_royale=BRRankInfo(
            rank_name=get_rank_name(raw_dict.get("br_rank_code")),
            rank_code=raw_dict.get("br_rank_code"),
            points=raw_dict.get("br_points", 0),
            max_rank_name=get_rank_name(raw_dict.get("br_max_rank_code")),
            max_rank_code=raw_dict.get("br_max_rank_code"),
            visible=bool(raw_dict.get("br_visible", True))
        ),
        clash_squad=RankInfo(
            rank_name=get_rank_name(raw_dict.get("cs_rank_code")),
            rank_code=raw_dict.get("cs_rank_code"),
            points=raw_dict.get("cs_points", 0),
            visible=bool(raw_dict.get("cs_visible", True))
        )
    )

    def make_stat_line(matches, wins, kills, deaths, headshots, damage) -> StatLine:
        matches = matches or 0
        wins = wins or 0
        kills = kills or 0
        deaths = deaths or 0
        headshots = headshots or 0
        damage = damage or 0.0

        win_rate = f"{(wins / max(matches, 1)) * 100:.2f}%"
        kd_ratio = round(kills / max(deaths, 1), 2)
        hs_rate = f"{(headshots / max(kills, 1)) * 100:.2f}%"
        avg_damage = round(damage / max(matches, 1), 2)

        return StatLine(
            matches=matches, wins=wins, win_rate=win_rate,
            kills=kills, deaths=deaths, kd_ratio=kd_ratio,
            headshots=headshots, headshot_rate=hs_rate,
            avg_damage_per_match=avg_damage, booyahs=wins
        )

    stats = StatsInfo(
        battle_royale=BRStats(
            solo=make_stat_line(raw_dict.get("br_solo_matches"), raw_dict.get("br_solo_wins"), raw_dict.get("br_solo_kills"), raw_dict.get("br_solo_deaths"), raw_dict.get("br_solo_headshots"), raw_dict.get("br_solo_damage")),
            duo=make_stat_line(raw_dict.get("br_duo_matches"), raw_dict.get("br_duo_wins"), raw_dict.get("br_duo_kills"), raw_dict.get("br_duo_deaths"), raw_dict.get("br_duo_headshots"), raw_dict.get("br_duo_damage")),
            squad=make_stat_line(raw_dict.get("br_squad_matches"), raw_dict.get("br_squad_wins"), raw_dict.get("br_squad_kills"), raw_dict.get("br_squad_deaths"), raw_dict.get("br_squad_headshots"), raw_dict.get("br_squad_damage")),
        ),
        clash_squad=CSRankedStats(
            matches=raw_dict.get("cs_matches", 0),
            wins=raw_dict.get("cs_wins", 0),
            win_rate=f"{(raw_dict.get('cs_wins', 0) / max(raw_dict.get('cs_matches', 1), 1)) * 100:.2f}%",
            kills=raw_dict.get("cs_kills", 0),
            kd_ratio=round(raw_dict.get("cs_kills", 0) / max(raw_dict.get("cs_matches", 1), 1), 2) # simplified CS KD
        )
    )

    social = SocialInfo(
        guild=GuildInfo(
            id=str(raw_dict.get("guild_id")) if raw_dict.get("guild_id") else None,
            name=raw_dict.get("guild_name"),
            level=raw_dict.get("guild_level"),
            member_count=raw_dict.get("guild_member_count"),
            capacity=raw_dict.get("guild_capacity"),
            leader=GuildLeader(
                uid=str(raw_dict.get("guild_leader_uid")),
                nickname=raw_dict.get("guild_leader_nickname"),
                level=raw_dict.get("guild_leader_level"),
                rank_name=raw_dict.get("guild_leader_rank_name")
            ) if raw_dict.get("guild_leader_uid") else None
        ) if raw_dict.get("guild_id") else None
    )

    pet = PetInfo(
        name=raw_dict.get("pet_name"),
        level=raw_dict.get("pet_level", 0),
        exp=raw_dict.get("pet_exp", 0),
        active_skill=raw_dict.get("pet_active_skill", "Unknown"),
        skin_id=raw_dict.get("pet_skin_id", 0),
        is_selected=bool(raw_dict.get("pet_is_selected", False))
    ) if raw_dict.get("pet_name") else None

    cosmetics = CosmeticsInfo(
        avatar_id=raw_dict.get("avatar_id"),
        banner_id=raw_dict.get("banner_id"),
        pin_id=raw_dict.get("pin_id"),
        character_id=raw_dict.get("character_id"),
        equipped_outfit_ids=raw_dict.get("equipped_outfit_ids") if isinstance(raw_dict.get("equipped_outfit_ids"), list) else [],
        equipped_weapon_skin_ids=raw_dict.get("equipped_weapon_skin_ids") if isinstance(raw_dict.get("equipped_weapon_skin_ids"), list) else []
    )

    pass_info = PassInfo(
        booyah_pass_level=raw_dict.get("booyah_pass_level", 0),
        fire_pass_status=raw_dict.get("fire_pass_status", "Basic"),
        fire_pass_badge_count=raw_dict.get("fire_pass_badge_count", 0)
    )

    credit = CreditInfo(
        score=raw_dict.get("credit_score", 100),
        reward_claimed=bool(raw_dict.get("credit_reward_claimed", False)),
        summary_period=raw_dict.get("credit_summary_period", "")
    )

    ban = BanInfo(
        is_banned=bool(raw_dict.get("is_banned", False)),
        ban_period=raw_dict.get("ban_period"),
        ban_type=raw_dict.get("ban_type")
    )

    return PlayerData(
        account=account,
        rank=rank,
        stats=stats,
        social=social,
        pet=pet,
        cosmetics=cosmetics,
        pass_info=pass_info,
        credit=credit,
        ban=ban
    )
