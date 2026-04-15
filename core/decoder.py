from typing import Any, Dict
from datetime import datetime
from config.settings import settings
from config.ranks import RANK_MAP
from core.crypto import cipher
from core.proto import decode_response
from api.errors import FFError, ErrorCode

def decode_payload(encrypted_data: bytes) -> Dict[str, Any]:
    try:
        # Step 1: AES Decrypt
        decrypted_data = cipher.decrypt(encrypted_data)
    except Exception:
        raise FFError(ErrorCode.DECODE_ERROR, "Failed to decrypt response. AES key/IV might be invalid.")

    try:
        # Step 2: Protobuf Decode
        raw_data = decode_response(decrypted_data)
    except Exception:
        raise FFError(ErrorCode.DECODE_ERROR, "Failed to parse protobuf response.")

    return raw_data

def format_timestamp(epoch: int) -> str:
    if not epoch:
        return "N/A"
    return datetime.fromtimestamp(epoch).isoformat() + "Z"

def map_to_player_data(raw: Dict[str, Any]) -> Dict[str, Any]:
    # This function maps flat raw dict from protobuf to the nested Pydantic structure
    # Stats calculation logic
    def calc_stats(m, w, k, d=0, h=0):
        m = max(m, 1)
        k = max(k, 0)
        return {
            "matches": m, "wins": w, "kills": k, "deaths": d, "headshots": h,
            "win_rate": f"{(w/m)*100:.2f}%",
            "kd_ratio": round(k / max(d, 1), 2),
            "headshot_rate": f"{(h/max(k, 1))*100:.2f}%" if k > 0 else "0.00%",
            "booyahs": w
        }

    return {
        "account": {
            "uid": str(raw.get("uid", "")),
            "nickname": raw.get("nickname", "Unknown"),
            "level": raw.get("level", 0),
            "exp": raw.get("exp", 0),
            "region": raw.get("region_code", "UNK"),
            "season_id": raw.get("season_id", 0),
            "preferred_mode": raw.get("preferred_mode", "Unknown"),
            "language": raw.get("language", "English"),
            "signature": raw.get("signature", ""),
            "honor_score": raw.get("honor_score", 0),
            "total_likes": raw.get("total_likes", 0),
            "ob_version": raw.get("ob_version", settings.OB_VERSION),
            "created_at_epoch": raw.get("created_at", 0),
            "created_at": format_timestamp(raw.get("created_at", 0)),
            "last_login_epoch": raw.get("last_login", 0),
            "last_login": format_timestamp(raw.get("last_login", 0)),
            "account_type": raw.get("account_type", "Normal")
        },
        "rank": {
            "battle_royale": {
                "rank_name": RANK_MAP.get(raw.get("br_rank_code", 0), "Unknown"),
                "rank_code": raw.get("br_rank_code", 0),
                "points": raw.get("br_points", 0),
                "max_rank_name": RANK_MAP.get(raw.get("br_max_rank_code", 0), "Unknown"),
                "max_rank_code": raw.get("br_max_rank_code", 0),
                "visible": bool(raw.get("br_rank_visible", True))
            },
            "clash_squad": {
                "rank_name": RANK_MAP.get(raw.get("cs_rank_code", 0), "Unknown"),
                "rank_code": raw.get("cs_rank_code", 0),
                "points": raw.get("cs_points", 0),
                "visible": bool(raw.get("cs_rank_visible", True))
            }
        },
        "stats": {
            "battle_royale": {
                "solo": calc_stats(raw.get("br_solo_matches", 0), raw.get("br_solo_wins", 0), raw.get("br_solo_kills", 0), raw.get("br_solo_deaths", 0), raw.get("br_solo_headshots", 0)),
                "duo": calc_stats(raw.get("br_duo_matches", 0), raw.get("br_duo_wins", 0), raw.get("br_duo_kills", 0), raw.get("br_duo_deaths", 0), raw.get("br_duo_headshots", 0)),
                "squad": calc_stats(raw.get("br_squad_matches", 0), raw.get("br_squad_wins", 0), raw.get("br_squad_kills", 0), raw.get("br_squad_deaths", 0), raw.get("br_squad_headshots", 0))
            },
            "clash_squad": {
                "ranked": calc_stats(raw.get("cs_matches", 0), raw.get("cs_wins", 0), raw.get("cs_kills", 0))
            }
        },
        "social": {
            "guild": {
                "id": str(raw.get("guild_id", "")) if raw.get("guild_id") else None,
                "name": raw.get("guild_name"),
                "level": raw.get("guild_level"),
                "member_count": raw.get("guild_member_count"),
                "capacity": raw.get("guild_capacity"),
                "leader": {
                    "uid": str(raw.get("guild_leader_uid", "")),
                    "nickname": raw.get("guild_leader_nickname", ""),
                    "level": raw.get("guild_leader_level", 0),
                    "rank_name": raw.get("guild_leader_rank", "")
                }
            } if raw.get("guild_id") else None
        },
        "pet": {
            "name": raw.get("pet_name"),
            "level": raw.get("pet_level"),
            "exp": raw.get("pet_exp"),
            "active_skill": raw.get("pet_active_skill"),
            "skin_id": raw.get("pet_skin_id"),
            "is_selected": bool(raw.get("pet_is_selected"))
        } if raw.get("pet_name") else None,
        "cosmetics": {
            "avatar_id": raw.get("avatar_id"),
            "banner_id": raw.get("banner_id"),
            "pin_id": raw.get("pin_id"),
            "character_id": raw.get("character_id"),
            "equipped_outfit_ids": raw.get("equipped_outfits", []),
            "equipped_weapon_skin_ids": raw.get("equipped_weapons", [])
        },
        "pass": {
            "booyah_pass_level": raw.get("bp_level", 0),
            "fire_pass_status": raw.get("fp_status", "Basic"),
            "fire_pass_badge_count": raw.get("fp_badges", 0)
        },
        "credit": {
            "score": raw.get("credit_score", 100),
            "reward_claimed": bool(raw.get("credit_reward_claimed")),
            "summary_period": raw.get("credit_summary_period", "")
        },
        "ban": {
            "is_banned": bool(raw.get("is_banned")),
            "ban_period": raw.get("ban_period"),
            "ban_type": raw.get("ban_type")
        }
    }
