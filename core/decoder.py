from datetime import datetime
from typing import Any, Dict, Optional
from core.crypto import aes_decrypt
from core.proto import decode_response
from config.fields import PROTO_FIELD_MAP
from config.ranks import get_rank_name
from api.schemas import (
    PlayerData, AccountInfo, ModeRankInfo, BRRankInfo, RankInfo,
    StatsInfo, BRStats, CSRankedStats, StatLine, SocialInfo, GuildInfo,
    GuildLeader, PetInfo, CosmeticsInfo, PassInfo, CreditInfo, BanInfo
)
from api.errors import FFError, ErrorCode

def decode_player_data(raw_encrypted_bytes: bytes) -> PlayerData:
    try:
        decrypted_bytes = aes_decrypt(raw_encrypted_bytes)
    except ValueError as e:
        raise FFError(ErrorCode.DECODE_ERROR, str(e), extra={"possible_key_rotation": True})

    raw_data = decode_response(decrypted_bytes)

    # Map raw field IDs to names
    mapped = {PROTO_FIELD_MAP.get(k, f"field_{k}"): v for k, v in raw_data.items()}

    def to_iso(epoch: Optional[int]) -> Optional[str]:
        if not epoch: return None
        return datetime.fromtimestamp(epoch).isoformat() + "Z"

    def calc_rate(a: float, b: float) -> str:
        if not b: return "0.00%"
        return f"{(a / b) * 100:.2f}%"

    def get_stat_line(matches, wins, kills, deaths, headshots, damage) -> StatLine:
        m = int(matches or 0)
        w = int(wins or 0)
        k = int(kills or 0)
        d = int(deaths or 0)
        h = int(headshots or 0)
        dmg = float(damage or 0)

        return StatLine(
            matches=m,
            wins=w,
            win_rate=calc_rate(w, m),
            kills=k,
            deaths=d,
            kd_ratio=round(k / max(d, 1), 2),
            headshots=h,
            headshot_rate=calc_rate(h, max(k, 1)),
            avg_damage_per_match=round(dmg / max(m, 1), 2),
            booyahs=w
        )

    # Building the nested Pydantic models
    account = AccountInfo(
        uid=str(mapped.get("uid", "")),
        nickname=mapped.get("nickname", "Unknown"),
        level=mapped.get("level", 0),
        exp=mapped.get("exp", 0),
        region=mapped.get("region", ""),
        season_id=mapped.get("season_id", 0),
        preferred_mode=mapped.get("preferred_mode", "Battle Royale"),
        language=mapped.get("language", "English"),
        signature=mapped.get("signature", ""),
        honor_score=mapped.get("honor_score", 0),
        total_likes=mapped.get("total_likes", 0),
        ob_version=mapped.get("ob_version", "OB53"),
        created_at_epoch=mapped.get("created_at", 0),
        created_at=to_iso(mapped.get("created_at")),
        last_login_epoch=mapped.get("last_login", 0),
        last_login=to_iso(mapped.get("last_login")),
        account_type=mapped.get("account_type", "Normal")
    )

    rank = ModeRankInfo(
        battle_royale=BRRankInfo(
            rank_name=get_rank_name(mapped.get("br_rank_code", 0)),
            rank_code=mapped.get("br_rank_code", 0),
            points=mapped.get("br_points", 0),
            max_rank_name=get_rank_name(mapped.get("br_max_rank_code", 0)),
            max_rank_code=mapped.get("br_max_rank_code", 0),
            visible=bool(mapped.get("br_rank_visible", True))
        ),
        clash_squad=RankInfo(
            rank_name=get_rank_name(mapped.get("cs_rank_code", 0)),
            rank_code=mapped.get("cs_rank_code", 0),
            points=mapped.get("cs_points", 0),
            visible=bool(mapped.get("cs_rank_visible", True))
        )
    )

    stats = StatsInfo(
        battle_royale=BRStats(
            solo=get_stat_line(
                mapped.get("br_solo_matches"), mapped.get("br_solo_wins"),
                mapped.get("br_solo_kills"), mapped.get("br_solo_deaths"),
                mapped.get("br_solo_headshots"), mapped.get("br_solo_damage")
            ),
            duo=get_stat_line(
                mapped.get("br_duo_matches"), mapped.get("br_duo_wins"),
                mapped.get("br_duo_kills"), mapped.get("br_duo_deaths"),
                mapped.get("br_duo_headshots"), mapped.get("br_duo_damage")
            ),
            squad=get_stat_line(
                mapped.get("br_squad_matches"), mapped.get("br_squad_wins"),
                mapped.get("br_squad_kills"), mapped.get("br_squad_deaths"),
                mapped.get("br_squad_headshots"), mapped.get("br_squad_damage")
            )
        ),
        clash_squad=CSRankedStats(
            matches=mapped.get("cs_ranked_matches", 0),
            wins=mapped.get("cs_ranked_wins", 0),
            win_rate=calc_rate(mapped.get("cs_ranked_wins", 0), mapped.get("cs_ranked_matches", 0)),
            kills=mapped.get("cs_ranked_kills", 0),
            kd_ratio=round(mapped.get("cs_ranked_kills", 0) / max(mapped.get("cs_ranked_matches", 0), 1), 2)
        )
    )

    social = SocialInfo(
        guild=GuildInfo(
            id=str(mapped.get("guild_id", "")),
            name=mapped.get("guild_name", ""),
            level=mapped.get("guild_level", 0),
            member_count=mapped.get("guild_member_count", 0),
            capacity=mapped.get("guild_capacity", 0),
            leader=GuildLeader(
                uid=str(mapped.get("guild_leader_uid", "")),
                nickname=mapped.get("guild_leader_nickname", ""),
                level=mapped.get("guild_leader_level", 0),
                rank_name=get_rank_name(mapped.get("guild_leader_rank_code", 0))
            )
        ) if mapped.get("guild_id") else None
    )

    pet = PetInfo(
        name=mapped.get("pet_name", ""),
        level=mapped.get("pet_level", 0),
        exp=mapped.get("pet_exp", 0),
        active_skill=mapped.get("pet_active_skill", ""),
        skin_id=mapped.get("pet_skin_id", 0),
        is_selected=bool(mapped.get("pet_is_selected", False))
    ) if mapped.get("pet_name") else None

    cosmetics = CosmeticsInfo(
        avatar_id=mapped.get("avatar_id", 0),
        banner_id=mapped.get("banner_id", 0),
        pin_id=mapped.get("pin_id", 0),
        character_id=mapped.get("character_id", 0),
        equipped_outfit_ids=mapped.get("equipped_outfit_ids", []),
        equipped_weapon_skin_ids=mapped.get("equipped_weapon_skin_ids", [])
    )

    pass_info = PassInfo(
        booyah_pass_level=mapped.get("booyah_pass_level", 0),
        fire_pass_status=mapped.get("fire_pass_status", "Basic"),
        fire_pass_badge_count=mapped.get("fire_pass_badge_count", 0)
    )

    credit = CreditInfo(
        score=mapped.get("credit_score", 100),
        reward_claimed=bool(mapped.get("credit_reward_claimed", False)),
        summary_period=mapped.get("credit_summary_period", "")
    )

    ban = BanInfo(
        is_banned=bool(mapped.get("is_banned", False)),
        ban_period=mapped.get("ban_period"),
        ban_type=mapped.get("ban_type")
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
