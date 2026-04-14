from datetime import datetime, timezone
from typing import Any, Dict
from core.crypto import cipher
from core.proto import proto_handler
from config.ranks import RANK_MAP
from api.schemas import (
    PlayerData, AccountInfo, ModeRankInfo, BRRankInfo, RankInfo,
    StatsInfo, BRStats, CSRankedStats, StatLine, SocialInfo,
    GuildInfo, GuildLeader, PetInfo, CosmeticsInfo, PassInfo,
    CreditInfo, BanInfo
)

class ResponseDecoder:
    @staticmethod
    def decode(raw_bytes: bytes) -> PlayerData:
        try:
            # Step 1: AES Decrypt
            decrypted_data = cipher.decrypt(raw_bytes)

            # Step 2: Protobuf Decode
            raw_dict = proto_handler.decode_response(decrypted_data)

            # Step 3: Map to Pydantic Model
            return ResponseDecoder._map_to_model(raw_dict)
        except Exception as e:
            from api.errors import FFError, ErrorCode
            raise FFError(
                ErrorCode.DECODE_ERROR,
                f"Failed to decode Garena response: {str(e)}",
                extra={"possible_key_rotation": True}
            )

    @staticmethod
    def _map_to_model(d: Dict[str, Any]) -> PlayerData:
        def get_iso(epoch: int | None) -> str | None:
            if not epoch: return None
            return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat().replace("+00:00", "Z")

        def calc_stat_line(matches, wins, kills, deaths, headshots, damage) -> StatLine:
            matches = matches or 0
            wins = wins or 0
            kills = kills or 0
            deaths = deaths or 0
            headshots = headshots or 0
            damage = damage or 0

            win_rate = f"{(wins / max(matches, 1) * 100):.2f}%"
            kd_ratio = round(kills / max(deaths, 1), 2)
            hs_rate = f"{(headshots / max(kills, 1) * 100):.2f}%"
            avg_dmg = round(damage / max(matches, 1), 2)

            return StatLine(
                matches=matches, wins=wins, win_rate=win_rate,
                kills=kills, deaths=deaths, kd_ratio=kd_ratio,
                headshots=headshots, headshot_rate=hs_rate,
                avg_damage_per_match=avg_dmg, booyahs=wins
            )

        # Account
        account = AccountInfo(
            uid=str(d.get("uid", "")),
            nickname=d.get("nickname", "Unknown"),
            level=d.get("level", 0),
            exp=d.get("exp", 0),
            region=d.get("region", "UNK"),
            season_id=d.get("season_id", 0),
            preferred_mode=d.get("preferred_mode", "Battle Royale"),
            language=d.get("language", "English"),
            signature=d.get("signature", ""),
            honor_score=d.get("honor_score", 100),
            total_likes=d.get("total_likes", 0),
            ob_version=d.get("ob_version", "OB53"),
            created_at_epoch=d.get("created_at"),
            created_at=get_iso(d.get("created_at")),
            last_login_epoch=d.get("last_login"),
            last_login=get_iso(d.get("last_login")),
            account_type=d.get("account_type", "Normal")
        )

        # Rank
        br_rank_code = d.get("br_rank_code", 101)
        br_max_code = d.get("br_max_rank_code", 101)
        cs_rank_code = d.get("cs_rank_code", 101)

        rank = ModeRankInfo(
            battle_royale=BRRankInfo(
                rank_name=RANK_MAP.get(br_rank_code, "Bronze I"),
                rank_code=br_rank_code,
                points=d.get("br_points", 0),
                max_rank_name=RANK_MAP.get(br_max_code, "Bronze I"),
                max_rank_code=br_max_code,
                visible=True
            ),
            clash_squad=RankInfo(
                rank_name=RANK_MAP.get(cs_rank_code, "Bronze I"),
                rank_code=cs_rank_code,
                points=d.get("cs_points", 0),
                visible=True
            )
        )

        # Stats
        stats = StatsInfo(
            battle_royale=BRStats(
                solo=calc_stat_line(d.get("br_solo_matches"), d.get("br_solo_wins"), d.get("br_solo_kills"), d.get("br_solo_deaths"), d.get("br_solo_headshots"), d.get("br_solo_damage")),
                duo=calc_stat_line(d.get("br_duo_matches"), d.get("br_duo_wins"), d.get("br_duo_kills"), d.get("br_duo_deaths"), d.get("br_duo_headshots"), d.get("br_duo_damage")),
                squad=calc_stat_line(d.get("br_squad_matches"), d.get("br_squad_wins"), d.get("br_squad_kills"), d.get("br_squad_deaths"), d.get("br_squad_headshots"), d.get("br_squad_damage"))
            ),
            clash_squad=CSRankedStats(
                matches=d.get("cs_matches", 0),
                wins=d.get("cs_wins", 0),
                win_rate=f"{(d.get('cs_wins',0) / max(d.get('cs_matches',1), 1) * 100):.2f}%",
                kills=d.get("cs_kills", 0),
                kd_ratio=round(d.get("cs_kills",0) / max(d.get("cs_matches",1) - d.get("cs_wins",0), 1), 2)
            )
        )

        # Social
        guild = None
        if d.get("guild_id"):
            guild = GuildInfo(
                id=str(d.get("guild_id")),
                name=d.get("guild_name", ""),
                level=d.get("guild_level", 1),
                member_count=d.get("guild_member_count", 1),
                capacity=d.get("guild_capacity", 30),
                leader=GuildLeader(
                    uid=str(d.get("guild_leader_uid", "")),
                    nickname=d.get("guild_leader_name", ""),
                    level=d.get("guild_leader_level", 1),
                    rank_name="Member" # Placeholder
                )
            )
        social = SocialInfo(guild=guild)

        # Pet
        pet = None
        if d.get("pet_name"):
            pet = PetInfo(
                name=d.get("pet_name"),
                level=d.get("pet_level", 1),
                exp=d.get("pet_exp", 0),
                active_skill=d.get("pet_skill", ""),
                skin_id=d.get("pet_skin_id", 0),
                is_selected=bool(d.get("pet_selected"))
            )

        # Cosmetics
        cosmetics = CosmeticsInfo(
            avatar_id=d.get("avatar_id", 0),
            banner_id=d.get("banner_id", 0),
            pin_id=d.get("pin_id", 0),
            character_id=d.get("character_id", 0),
            equipped_outfit_ids=d.get("equipped_outfit_ids", []),
            equipped_weapon_skin_ids=d.get("equipped_weapon_skin_ids", [])
        )

        # Pass
        pass_info = PassInfo(
            booyah_pass_level=d.get("booyah_pass_level", 0),
            fire_pass_status=d.get("fire_pass_status", "Basic"),
            fire_pass_badge_count=d.get("fire_pass_badge_count", 0)
        )

        # Credit
        credit = CreditInfo(
            score=d.get("credit_score", 100),
            reward_claimed=bool(d.get("credit_reward_claimed")),
            summary_period=d.get("credit_summary_period", "")
        )

        # Ban
        ban = BanInfo(
            is_banned=bool(d.get("is_banned")),
            ban_period=d.get("ban_period"),
            ban_type=d.get("ban_type")
        )

        return PlayerData(
            account=account, rank=rank, stats=stats, social=social,
            pet=pet, cosmetics=cosmetics, pass_info=pass_info,
            credit=credit, ban=ban
        )

decoder = ResponseDecoder()
