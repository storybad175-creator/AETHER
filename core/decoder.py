import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from config.fields import PROTO_FIELD_MAP
from config.ranks import RANK_MAP
from api.schemas import (
    PlayerData, AccountInfo, ModeRankInfo, BRRankInfo, RankInfo,
    StatsInfo, BRStats, StatLine, CSRankedStats, SocialInfo,
    GuildInfo, GuildLeader, PetInfo, CosmeticsInfo, PassInfo,
    CreditInfo, BanInfo
)

logger = logging.getLogger(__name__)

class ResponseDecoder:
    """Decodes raw protobuf dict into typed Pydantic models."""

    def decode(self, raw_proto: Dict[int, Any]) -> PlayerData:
        """Maps raw field IDs to Pydantic models."""

        # 1. Account Info (Field 1 in response)
        acc_data = self._map_fields(raw_proto.get(1, {}), PROTO_FIELD_MAP["account"])
        account = self._build_account_info(acc_data)

        # 2. Rank Info (Field 2)
        rank_data = self._map_fields(raw_proto.get(2, {}), PROTO_FIELD_MAP["rank"])
        rank = self._build_rank_info(rank_data)

        # 3. Stats (Field 3)
        stats_data = self._map_fields(raw_proto.get(3, {}), PROTO_FIELD_MAP["br_stats"])
        cs_data = self._map_fields(raw_proto.get(4, {}), PROTO_FIELD_MAP["cs_stats"])
        stats = self._build_stats_info(stats_data, cs_data)

        # 4. Social/Guild (Field 5)
        guild_data = self._map_fields(raw_proto.get(5, {}), PROTO_FIELD_MAP["guild"])
        social = self._build_social_info(guild_data)

        # 5. Pet (Field 6)
        pet_data = self._map_fields(raw_proto.get(6, {}), PROTO_FIELD_MAP["pet"])
        pet = self._build_pet_info(pet_data)

        # 6. Cosmetics (Field 7)
        cos_data = self._map_fields(raw_proto.get(7, {}), PROTO_FIELD_MAP["cosmetics"])
        cosmetics = self._build_cosmetics_info(cos_data)

        # 7. Pass (Field 8)
        pass_data = self._map_fields(raw_proto.get(8, {}), PROTO_FIELD_MAP["pass"])
        pass_info = self._build_pass_info(pass_data)

        # 8. Credit (Field 9)
        credit_data = self._map_fields(raw_proto.get(9, {}), PROTO_FIELD_MAP["credit"])
        credit = self._build_credit_info(credit_data)

        # 9. Ban (Field 10)
        ban_data = self._map_fields(raw_proto.get(10, {}), PROTO_FIELD_MAP["ban"])
        ban = self._build_ban_info(ban_data)

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

    def _map_fields(self, data: Any, field_map: Dict[int, str]) -> Dict[str, Any]:
        """Converts integer field IDs to named keys."""
        if not isinstance(data, dict):
            return {}
        return {field_map[k]: v for k, v in data.items() if k in field_map}

    def _epoch_to_iso(self, epoch: Optional[int]) -> Optional[str]:
        if not epoch:
            return None
        return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat().replace("+00:00", "Z")

    def _get_rank_name(self, code: Optional[int]) -> str:
        if not code:
            return "Unranked"
        return RANK_MAP.get(code, f"Unknown ({code})")

    def _build_account_info(self, data: Dict[str, Any]) -> AccountInfo:
        epoch_created = data.get("created_at_epoch")
        epoch_last = data.get("last_login_epoch")

        # Handle nickname which might be bytes from protobuf
        nick = data.get("nickname", "Unknown")
        if isinstance(nick, bytes):
            nick = nick.decode('utf-8', errors='replace')

        return AccountInfo(
            uid=str(data.get("uid", "")),
            nickname=nick,
            level=data.get("level", 0),
            exp=data.get("exp", 0),
            region=data.get("region", ""),
            season_id=data.get("season_id", 0),
            preferred_mode=data.get("preferred_mode", "Unknown"),
            language=data.get("language", "English"),
            signature=data.get("signature", ""),
            honor_score=data.get("honor_score", 0),
            total_likes=data.get("total_likes", 0),
            ob_version=data.get("ob_version", "Unknown"),
            created_at_epoch=epoch_created,
            created_at=self._epoch_to_iso(epoch_created),
            last_login_epoch=epoch_last,
            last_login=self._epoch_to_iso(epoch_last),
            account_type=data.get("account_type", "Normal")
        )

    def _build_rank_info(self, data: Dict[str, Any]) -> ModeRankInfo:
        br_code = data.get("br_rank_code")
        br_max_code = data.get("br_max_rank_code")
        cs_code = data.get("cs_rank_code")

        return ModeRankInfo(
            battle_royale=BRRankInfo(
                rank_name=self._get_rank_name(br_code),
                rank_code=br_code or 0,
                points=data.get("br_points", 0),
                visible=data.get("rank_visible", True),
                max_rank_name=self._get_rank_name(br_max_code),
                max_rank_code=br_max_code or 0
            ),
            clash_squad=RankInfo(
                rank_name=self._get_rank_name(cs_code),
                rank_code=cs_code or 0,
                points=data.get("cs_points", 0),
                visible=data.get("rank_visible", True)
            )
        )

    def _calc_rate(self, numerator: int, denominator: int) -> str:
        if denominator <= 0:
            return "0.00%"
        return f"{(numerator / denominator) * 100:.2f}%"

    def _build_stat_line(self, matches, wins, kills, deaths, headshots, damage) -> StatLine:
        matches = matches or 0
        kills = kills or 0
        deaths = deaths or 0

        return StatLine(
            matches=matches,
            wins=wins or 0,
            win_rate=self._calc_rate(wins or 0, matches),
            kills=kills,
            deaths=deaths,
            kd_ratio=round(kills / max(deaths, 1), 2),
            headshots=headshots or 0,
            headshot_rate=self._calc_rate(headshots or 0, kills),
            avg_damage_per_match=round((damage or 0) / max(matches, 1), 2),
            booyahs=wins or 0
        )

    def _build_stats_info(self, br: Dict[str, Any], cs: Dict[str, Any]) -> StatsInfo:
        return StatsInfo(
            battle_royale=BRStats(
                solo=self._build_stat_line(
                    br.get("solo_matches"), br.get("solo_wins"), br.get("solo_kills"),
                    br.get("solo_deaths"), br.get("solo_headshots"), br.get("solo_damage")
                ),
                duo=self._build_stat_line(
                    br.get("duo_matches"), br.get("duo_wins"), br.get("duo_kills"),
                    br.get("duo_deaths"), br.get("duo_headshots"), br.get("duo_damage")
                ),
                squad=self._build_stat_line(
                    br.get("squad_matches"), br.get("squad_wins"), br.get("squad_kills"),
                    br.get("squad_deaths"), br.get("squad_headshots"), br.get("squad_damage")
                )
            ),
            clash_squad=CSRankedStats(
                matches=cs.get("matches", 0),
                wins=cs.get("wins", 0),
                win_rate=self._calc_rate(cs.get("wins", 0), cs.get("matches", 0)),
                kills=cs.get("kills", 0),
                kd_ratio=round(cs.get("kd_ratio_raw", 0) / 100, 2) if cs.get("kd_ratio_raw") else 0.0
            )
        )

    def _build_social_info(self, data: Dict[str, Any]) -> SocialInfo:
        if not data or not data.get("id"):
            return SocialInfo(guild=None)

        leader_nick = data.get("leader_nickname", "Unknown")
        if isinstance(leader_nick, bytes):
            leader_nick = leader_nick.decode('utf-8', errors='replace')

        return SocialInfo(
            guild=GuildInfo(
                id=str(data.get("id", "")),
                name=data.get("name", "Unknown"),
                level=data.get("level", 1),
                member_count=data.get("member_count", 0),
                capacity=data.get("capacity", 0),
                leader=GuildLeader(
                    uid=str(data.get("leader_uid", "")),
                    nickname=leader_nick,
                    level=data.get("leader_level", 0),
                    rank_name=self._get_rank_name(data.get("leader_rank_code"))
                )
            )
        )

    def _build_pet_info(self, data: Dict[str, Any]) -> Optional[PetInfo]:
        if not data or not data.get("name"):
            return None
        return PetInfo(
            name=data.get("name", ""),
            level=data.get("level", 1),
            exp=data.get("exp", 0),
            active_skill=data.get("active_skill", ""),
            skin_id=data.get("skin_id", 0),
            is_selected=data.get("is_selected", True)
        )

    def _build_cosmetics_info(self, data: Dict[str, Any]) -> CosmeticsInfo:
        return CosmeticsInfo(
            avatar_id=data.get("avatar_id", 0),
            banner_id=data.get("banner_id", 0),
            pin_id=data.get("pin_id", 0),
            character_id=data.get("character_id", 0),
            equipped_outfit_ids=data.get("equipped_outfit_ids", []) if isinstance(data.get("equipped_outfit_ids"), list) else ([data.get("equipped_outfit_ids")] if data.get("equipped_outfit_ids") else []),
            equipped_weapon_skin_ids=data.get("equipped_weapon_skin_ids", []) if isinstance(data.get("equipped_weapon_skin_ids"), list) else ([data.get("equipped_weapon_skin_ids")] if data.get("equipped_weapon_skin_ids") else [])
        )

    def _build_pass_info(self, data: Dict[str, Any]) -> PassInfo:
        status_code = data.get("fire_pass_status_code", 0)
        status_map = {0: "Basic", 1: "Premium", 2: "Elite"}
        return PassInfo(
            booyah_pass_level=data.get("booyah_pass_level", 0),
            fire_pass_status=status_map.get(status_code, "Basic"),
            fire_pass_badge_count=data.get("fire_pass_badge_count", 0)
        )

    def _build_credit_info(self, data: Dict[str, Any]) -> CreditInfo:
        return CreditInfo(
            score=data.get("score", 100),
            reward_claimed=data.get("reward_claimed", False),
            summary_period=data.get("summary_period", "")
        )

    def _build_ban_info(self, data: Dict[str, Any]) -> BanInfo:
        epoch = data.get("ban_period_epoch")
        return BanInfo(
            is_banned=data.get("is_banned", False),
            ban_period=self._epoch_to_iso(epoch),
            ban_type=data.get("ban_type")
        )

response_decoder = ResponseDecoder()
