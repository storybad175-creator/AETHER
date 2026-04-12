from typing import Any, Dict
from datetime import datetime, timezone
from config.ranks import RANK_MAP

class ResponseDecoder:
    """Decodes the raw dictionary from Protobuf into a structured format for Pydantic."""

    def decode(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Maps raw fields to the structure expected by api/schemas.py."""

        acc = raw_data.get("account_info", {})
        rank = raw_data.get("rank_info", {})
        stats = raw_data.get("stats_info", {})
        social = raw_data.get("social_info", {})
        pet = raw_data.get("pet_info", {})
        cos = raw_data.get("cosmetics_info", {})
        pas = raw_data.get("pass_info", {})
        cre = raw_data.get("credit_info", {})
        ban = raw_data.get("ban_info", {})

        # Helper for timestamps
        def format_ts(ts: Any) -> str | None:
            if not ts or not isinstance(ts, int): return None
            return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace("+00:00", "Z")

        # Helper for win rates and K/D
        def calc_win_rate(wins: int, matches: int) -> str:
            if matches == 0: return "0.00%"
            return f"{(wins / matches) * 100:.2f}%"

        def calc_kd(kills: int, deaths: int) -> float:
            return round(kills / max(deaths, 1), 2)

        def process_stat_line(line: Dict[str, Any]) -> Dict[str, Any]:
            matches = line.get("matches", 0)
            wins = line.get("wins", 0)
            kills = line.get("kills", 0)
            deaths = line.get("deaths", 0)
            headshots = line.get("headshots", 0)

            return {
                "matches": matches,
                "wins": wins,
                "win_rate": calc_win_rate(wins, matches),
                "kills": kills,
                "deaths": deaths,
                "kd_ratio": calc_kd(kills, deaths),
                "headshots": headshots,
                "headshot_rate": calc_win_rate(headshots, kills),
                "avg_damage_per_match": round(line.get("avg_damage", 0), 2),
                "booyahs": wins
            }

        return {
            "account": {
                "uid": str(acc.get("uid", "")),
                "nickname": acc.get("nickname"),
                "level": acc.get("level"),
                "exp": acc.get("exp"),
                "region": acc.get("region"),
                "season_id": acc.get("season_id"),
                "preferred_mode": acc.get("preferred_mode"),
                "language": acc.get("language"),
                "signature": acc.get("signature"),
                "honor_score": acc.get("honor_score"),
                "total_likes": acc.get("total_likes"),
                "ob_version": acc.get("ob_version"),
                "created_at_epoch": acc.get("created_at_epoch"),
                "created_at": format_ts(acc.get("created_at_epoch")),
                "last_login_epoch": acc.get("last_login_epoch"),
                "last_login": format_ts(acc.get("last_login_epoch")),
                "account_type": acc.get("account_type", "Normal")
            },
            "rank": {
                "battle_royale": {
                    "rank_name": RANK_MAP.get(rank.get("br_rank_code", 0), "Unknown"),
                    "rank_code": rank.get("br_rank_code"),
                    "points": rank.get("br_points"),
                    "max_rank_name": RANK_MAP.get(rank.get("br_max_rank_code", 0), "Unknown"),
                    "max_rank_code": rank.get("br_max_rank_code"),
                    "visible": rank.get("br_visible", True)
                },
                "clash_squad": {
                    "rank_name": RANK_MAP.get(rank.get("cs_rank_code", 0), "Unknown"),
                    "rank_code": rank.get("cs_rank_code"),
                    "points": rank.get("cs_points"),
                    "visible": rank.get("cs_visible", True)
                }
            },
            "stats": {
                "battle_royale": {
                    "solo": process_stat_line(stats.get("br_solo_stats", {})),
                    "duo": process_stat_line(stats.get("br_duo_stats", {})),
                    "squad": process_stat_line(stats.get("br_squad_stats", {}))
                },
                "clash_squad": {
                    "ranked": {
                        "matches": stats.get("cs_ranked_stats", {}).get("matches", 0),
                        "wins": stats.get("cs_ranked_stats", {}).get("wins", 0),
                        "win_rate": calc_win_rate(stats.get("cs_ranked_stats", {}).get("wins", 0), stats.get("cs_ranked_stats", {}).get("matches", 0)),
                        "kills": stats.get("cs_ranked_stats", {}).get("kills", 0),
                        "kd_ratio": calc_kd(stats.get("cs_ranked_stats", {}).get("kills", 0), stats.get("cs_ranked_stats", {}).get("deaths", 0))
                    }
                }
            },
            "social": {
                "guild": {
                    "id": str(social.get("guild_id", "")) if social.get("guild_id") else None,
                    "name": social.get("guild_name"),
                    "level": social.get("guild_level"),
                    "member_count": social.get("guild_member_count"),
                    "capacity": social.get("guild_capacity"),
                    "leader": {
                        "uid": str(social.get("guild_leader_info", {}).get("uid", "")),
                        "nickname": social.get("guild_leader_info", {}).get("nickname"),
                        "level": social.get("guild_leader_info", {}).get("level"),
                        "rank_name": RANK_MAP.get(social.get("guild_leader_info", {}).get("br_rank_code", 0), "Unknown")
                    }
                } if social.get("guild_id") else None
            },
            "pet": {
                "name": pet.get("pet_name"),
                "level": pet.get("pet_level"),
                "exp": pet.get("pet_exp"),
                "active_skill": pet.get("pet_active_skill"),
                "skin_id": pet.get("pet_skin_id"),
                "is_selected": pet.get("pet_is_selected", False)
            } if pet.get("pet_name") else None,
            "cosmetics": {
                "avatar_id": cos.get("avatar_id"),
                "banner_id": cos.get("banner_id"),
                "pin_id": cos.get("pin_id"),
                "character_id": cos.get("character_id"),
                "equipped_outfit_ids": cos.get("equipped_outfit_ids", []),
                "equipped_weapon_skin_ids": cos.get("equipped_weapon_skin_ids", [])
            },
            "pass": {
                "booyah_pass_level": pas.get("booyah_pass_level"),
                "fire_pass_status": pas.get("fire_pass_status", "Basic"),
                "fire_pass_badge_count": pas.get("fire_pass_badge_count")
            },
            "credit": {
                "score": cre.get("credit_score"),
                "reward_claimed": cre.get("credit_reward_claimed", False),
                "summary_period": cre.get("credit_summary_period")
            },
            "ban": {
                "is_banned": ban.get("is_banned", False),
                "ban_period": ban.get("ban_period"),
                "ban_type": ban.get("ban_type")
            }
        }

decoder = ResponseDecoder()
