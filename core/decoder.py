from typing import Any, Dict, Optional
from api.schemas import PlayerData, AccountInfo, ModeRankInfo, BRRankInfo, RankInfo, StatsInfo, BRStats, CSRankedStats, StatLine, SocialInfo, GuildInfo, GuildLeader, PetInfo, CosmeticsInfo, PassInfo, CreditInfo, BanInfo
from config.settings import settings
from config.ranks import get_rank_name
import time

class ResponseDecoder:
    def decode(self, raw_dict: Dict[str, Any], region: str) -> PlayerData:
        """
        Maps the raw dictionary from protobuf to the structured PlayerData model.
        """
        # Account Info
        acc_raw = raw_dict.get("account", {})
        created_at_epoch = acc_raw.get("created_at_epoch", 0)
        last_login_epoch = acc_raw.get("last_login_epoch", 0)

        account = AccountInfo(
            uid=str(acc_raw.get("uid", "")),
            nickname=acc_raw.get("nickname", "Unknown"),
            level=acc_raw.get("level", 0),
            exp=acc_raw.get("exp", 0),
            region=region,
            season_id=acc_raw.get("season_id", 0),
            preferred_mode=acc_raw.get("preferred_mode", "Unknown"),
            language=acc_raw.get("language", "English"),
            signature=acc_raw.get("signature", ""),
            honor_score=acc_raw.get("honor_score", 0),
            total_likes=acc_raw.get("total_likes", 0),
            ob_version=acc_raw.get("ob_version", settings.ob_version),
            created_at_epoch=created_at_epoch,
            created_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(created_at_epoch)) if created_at_epoch else None,
            last_login_epoch=last_login_epoch,
            last_login=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(last_login_epoch)) if last_login_epoch else None,
            account_type=acc_raw.get("account_type", "Normal")
        )

        # Rank Info
        rank_raw = raw_dict.get("rank", {})
        br_raw = rank_raw.get("battle_royale", {})
        cs_raw = rank_raw.get("clash_squad", {})

        rank = ModeRankInfo(
            battle_royale=BRRankInfo(
                rank_code=br_raw.get("rank_code", 0),
                rank_name=get_rank_name(br_raw.get("rank_code", 0)),
                points=br_raw.get("points", 0),
                max_rank_code=br_raw.get("max_rank_code", 0),
                max_rank_name=get_rank_name(br_raw.get("max_rank_code", 0)),
                visible=br_raw.get("visible", True)
            ),
            clash_squad=RankInfo(
                rank_code=cs_raw.get("rank_code", 0),
                rank_name=get_rank_name(cs_raw.get("rank_code", 0)),
                points=cs_raw.get("points", 0),
                visible=cs_raw.get("visible", True)
            )
        )

        # Stats Info
        stats_raw = raw_dict.get("stats", {})
        br_stats_raw = stats_raw.get("battle_royale", {})
        cs_stats_raw = stats_raw.get("clash_squad", {})

        def map_stat(s_raw):
            matches = s_raw.get("matches", 0)
            wins = s_raw.get("wins", 0)
            kills = s_raw.get("kills", 0)
            deaths = s_raw.get("deaths", 0)
            headshots = s_raw.get("headshots", 0)

            win_rate = f"{(wins / max(matches, 1) * 100):.2f}%" if matches > 0 else "0.00%"
            kd_ratio = round(kills / max(deaths, 1), 2)
            hs_rate = f"{(headshots / max(kills, 1) * 100):.2f}%" if kills > 0 else "0.00%"

            return StatLine(
                matches=matches,
                wins=wins,
                win_rate=win_rate,
                kills=kills,
                deaths=deaths,
                kd_ratio=kd_ratio,
                headshots=headshots,
                headshot_rate=hs_rate,
                avg_damage_per_match=round(s_raw.get("avg_damage_per_match", 0.0), 2),
                booyahs=wins
            )

        cs_ranked_raw = cs_stats_raw.get("ranked", {})
        cs_matches = cs_ranked_raw.get("matches", 0)
        cs_wins = cs_ranked_raw.get("wins", 0)
        cs_kills = cs_ranked_raw.get("kills", 0)

        stats = StatsInfo(
            battle_royale=BRStats(
                solo=map_stat(br_stats_raw.get("solo", {})),
                duo=map_stat(br_stats_raw.get("duo", {})),
                squad=map_stat(br_stats_raw.get("squad", {}))
            ),
            clash_squad=CSRankedStats(
                matches=cs_matches,
                wins=cs_wins,
                win_rate=f"{(cs_wins / max(cs_matches, 1) * 100):.2f}%" if cs_matches > 0 else "0.00%",
                kills=cs_kills,
                kd_ratio=round(cs_kills / max(cs_matches, 1), 2) # CS usually uses K/D per match or total
            )
        )

        # Social Info
        social_raw = raw_dict.get("social", {})
        guild_raw = social_raw.get("guild")
        social = SocialInfo(guild=None)
        if guild_raw:
            leader_raw = guild_raw.get("leader", {})
            social.guild = GuildInfo(
                id=str(guild_raw.get("id", "")),
                name=guild_raw.get("name", ""),
                level=guild_raw.get("level", 1),
                member_count=guild_raw.get("member_count", 0),
                capacity=guild_raw.get("capacity", 0),
                leader=GuildLeader(
                    uid=str(leader_raw.get("uid", "")),
                    nickname=leader_raw.get("nickname", ""),
                    level=leader_raw.get("level", 0),
                    rank_name=get_rank_name(leader_raw.get("rank_code", 0))
                )
            )

        # Pet Info
        pet_raw = raw_dict.get("pet", {})
        pet = None
        if pet_raw:
            pet = PetInfo(
                name=pet_raw.get("name", ""),
                level=pet_raw.get("level", 0),
                exp=pet_raw.get("exp", 0),
                active_skill=pet_raw.get("active_skill", ""),
                skin_id=pet_raw.get("skin_id", 0),
                is_selected=pet_raw.get("is_selected", True)
            )

        # Cosmetics & Pass
        cos_raw = raw_dict.get("cosmetics", {})
        cosmetics = CosmeticsInfo(
            avatar_id=cos_raw.get("avatar_id", 0),
            banner_id=cos_raw.get("banner_id", 0),
            pin_id=cos_raw.get("pin_id", 0),
            character_id=cos_raw.get("character_id", 0),
            equipped_outfit_ids=cos_raw.get("equipped_outfit_ids", []),
            equipped_weapon_skin_ids=cos_raw.get("equipped_weapon_skin_ids", [])
        )

        pass_raw = raw_dict.get("pass_info", {})
        pass_info = PassInfo(
            booyah_pass_level=pass_raw.get("booyah_pass_level", 0),
            fire_pass_status=pass_raw.get("fire_pass_status", "Basic"),
            fire_pass_badge_count=pass_raw.get("fire_pass_badge_count", 0)
        )

        # Credit & Ban
        credit_raw = raw_dict.get("credit", {})
        credit = CreditInfo(
            score=credit_raw.get("score", 100),
            reward_claimed=credit_raw.get("reward_claimed", False),
            summary_period=credit_raw.get("summary_period", "")
        )

        ban_raw = raw_dict.get("ban", {})
        ban = BanInfo(
            is_banned=ban_raw.get("is_banned", False),
            ban_period=ban_raw.get("ban_period"),
            ban_type=ban_raw.get("ban_type")
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

decoder = ResponseDecoder()
