import time
import logging
from typing import Any, Dict, Optional, Union
from core.crypto import aes_decrypt
from core.proto import decode_response
from api.schemas import PlayerData
from config.ranks import get_rank_name
from api.errors import FFError, ErrorCode

logger = logging.getLogger(__name__)

def decode_player_data(raw_encrypted: bytes) -> PlayerData:
    """
    Decrypts, decodes, and maps raw Garena response bytes to a PlayerData model.
    Handles nested protobuf messages via Strategy B.
    """
    try:
        # Step 1: AES Decrypt
        try:
            decrypted_bytes = aes_decrypt(raw_encrypted)
        except ValueError as e:
            # unpad error usually means wrong key/iv
            logger.error(f"AES Decryption failed (unpad error): {e}")
            raise FFError(
                ErrorCode.DECODE_ERROR,
                "Failed to decrypt response. This may indicate an AES key rotation.",
                extra={"possible_key_rotation": True, "action": "Update AES_KEY and AES_IV in .env"}
            )

        # Step 2: Protobuf Decode (Recursive via Strategy B)
        # 1: account, 2: rank, 3: stats, 4: social, 5: pet, 6: cosmetics, 7: pass, 8: credit, 9: ban
        try:
            raw_msg = decode_response(decrypted_bytes)
        except Exception as e:
            logger.error(f"Protobuf decoding failed: {e}")
            raise FFError(
                ErrorCode.DECODE_ERROR,
                "Failed to parse decrypted protobuf data.",
                extra={"possible_key_rotation": True}
            )

        # If we got an empty dict, it's likely wrong keys or invalid data
        if not raw_msg or "account" not in raw_msg:
             logger.warning("Decoded message is empty or missing mandatory 'account' field.")
             if not raw_msg:
                 raise FFError(
                    ErrorCode.DECODE_ERROR,
                    "Decoded response is empty. Possible AES key rotation.",
                    extra={"possible_key_rotation": True}
                )

        def safe_get(data: Any, key: Union[int, str], default: Any = None) -> Any:
            if not isinstance(data, dict):
                return default
            return data.get(key, default)

        def to_str(data: Any) -> Optional[str]:
            if isinstance(data, bytes):
                try:
                    return data.decode('utf-8')
                except:
                    return None
            return str(data) if data is not None else None

        def to_iso8601(epoch: Any) -> Optional[str]:
            if not epoch or not isinstance(epoch, (int, float)):
                return None
            try:
                return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(epoch))
            except:
                return None

        # --- Sub-message Decoders ---

        # 1: Account
        acc_raw = safe_get(raw_msg, "account", {})
        account = {
            "uid": to_str(safe_get(acc_raw, "uid")),
            "nickname": to_str(safe_get(acc_raw, "nickname")),
            "level": safe_get(acc_raw, "level"),
            "exp": safe_get(acc_raw, "exp"),
            "region": to_str(safe_get(acc_raw, "region")),
            "season_id": safe_get(acc_raw, "season_id"),
            "preferred_mode": to_str(safe_get(acc_raw, "preferred_mode")) or "Battle Royale",
            "language": to_str(safe_get(acc_raw, "language")) or "English",
            "signature": to_str(safe_get(acc_raw, "signature")),
            "honor_score": safe_get(acc_raw, "honor_score"),
            "total_likes": safe_get(acc_raw, "total_likes"),
            "ob_version": to_str(safe_get(acc_raw, "ob_version")),
            "created_at_epoch": safe_get(acc_raw, "created_at_epoch"),
            "created_at": to_iso8601(safe_get(acc_raw, "created_at_epoch")),
            "last_login_epoch": safe_get(acc_raw, "last_login_epoch"),
            "last_login": to_iso8601(safe_get(acc_raw, "last_login_epoch")),
            "account_type": "Normal" if safe_get(acc_raw, "account_type") == 0 else "Special"
        }

        # 2: Rank
        rank_raw = safe_get(raw_msg, "rank", {})
        rank = {
            "battle_royale": {
                "rank_name": get_rank_name(safe_get(rank_raw, "br_rank_code")),
                "rank_code": safe_get(rank_raw, "br_rank_code"),
                "points": safe_get(rank_raw, "br_points"),
                "max_rank_name": get_rank_name(safe_get(rank_raw, "br_max_rank_code")),
                "max_rank_code": safe_get(rank_raw, "br_max_rank_code"),
                "visible": bool(safe_get(rank_raw, "br_visible", True))
            },
            "clash_squad": {
                "rank_name": get_rank_name(safe_get(rank_raw, "cs_rank_code")),
                "rank_code": safe_get(rank_raw, "cs_rank_code"),
                "points": safe_get(rank_raw, "cs_points"),
                "visible": bool(safe_get(rank_raw, "cs_visible", True))
            }
        }

        # 3: Stats
        stats_raw = safe_get(raw_msg, "stats", {})

        def parse_stat_line(d: Any) -> Dict[str, Any]:
            if not isinstance(d, dict): d = {}
            m = safe_get(d, "matches", 0)
            w = safe_get(d, "wins", 0)
            k = safe_get(d, "kills", 0)
            de = safe_get(d, "deaths", 0)
            hs = safe_get(d, "headshots", 0)

            return {
                "matches": m,
                "wins": w,
                "win_rate": f"{(w / max(m, 1) * 100):.2f}%",
                "kills": k,
                "deaths": de,
                "kd_ratio": round(k / max(de, 1), 2),
                "headshots": hs,
                "headshot_rate": f"{(hs / max(k, 1) * 100):.2f}%",
                "avg_damage_per_match": round(safe_get(d, "avg_damage", 0.0), 2),
                "booyahs": safe_get(d, "booyahs", w)
            }

        stats = {
            "battle_royale": {
                "solo": parse_stat_line(safe_get(stats_raw, "br_solo")),
                "duo": parse_stat_line(safe_get(stats_raw, "br_duo")),
                "squad": parse_stat_line(safe_get(stats_raw, "br_squad"))
            },
            "clash_squad": {
                "ranked": {
                    "matches": safe_get(safe_get(stats_raw, "cs_ranked", {}), "matches", 0),
                    "wins": safe_get(safe_get(stats_raw, "cs_ranked", {}), "wins", 0),
                    "win_rate": "0.00%",
                    "kills": safe_get(safe_get(stats_raw, "cs_ranked", {}), "kills", 0),
                    "kd_ratio": 0.0
                }
            }
        }
        # Correct CS ranked win rate and KD
        cs_r = stats["clash_squad"]["ranked"]
        cs_r["win_rate"] = f"{(cs_r['wins'] / max(cs_r['matches'], 1) * 100):.2f}%"
        # KD for CS is often kills per match or kills/deaths. If deaths not available, kills/matches
        cs_r["kd_ratio"] = round(cs_r["kills"] / max(cs_r["matches"], 1), 2)

        # 4: Social
        social_raw = safe_get(raw_msg, "social", {})
        guild_id = to_str(safe_get(social_raw, "guild_id"))
        social = {
            "guild": {
                "id": guild_id,
                "name": to_str(safe_get(social_raw, "guild_name")),
                "level": safe_get(social_raw, "guild_level"),
                "member_count": safe_get(social_raw, "guild_member_count"),
                "capacity": safe_get(social_raw, "guild_capacity"),
                "leader": {
                    "uid": to_str(safe_get(social_raw, "guild_leader_uid")),
                    "nickname": to_str(safe_get(social_raw, "guild_leader_nickname")),
                    "level": safe_get(social_raw, "guild_leader_level"),
                    "rank_name": get_rank_name(safe_get(social_raw, "guild_leader_rank"))
                }
            } if guild_id else None
        }

        # 5: Pet
        pet_raw = safe_get(raw_msg, "pet", {})
        pet_name = to_str(safe_get(pet_raw, "pet_name"))
        pet = {
            "name": pet_name,
            "level": safe_get(pet_raw, "pet_level"),
            "exp": safe_get(pet_raw, "pet_exp"),
            "active_skill": to_str(safe_get(pet_raw, "pet_active_skill")),
            "skin_id": safe_get(pet_raw, "pet_skin_id"),
            "is_selected": bool(safe_get(pet_raw, "pet_is_selected"))
        } if pet_name else None

        # 6: Cosmetics
        cosm_raw = safe_get(raw_msg, "cosmetics", {})

        def to_int_list(data: Any) -> list[int]:
            if isinstance(data, list):
                return [int.from_bytes(x, 'little') if isinstance(x, bytes) else int(x) for x in data]
            if isinstance(data, (bytes, int)):
                return [int.from_bytes(data, 'little') if isinstance(data, bytes) else int(data)]
            return []

        cosmetics = {
            "avatar_id": safe_get(cosm_raw, "avatar_id"),
            "banner_id": safe_get(cosm_raw, "banner_id"),
            "pin_id": safe_get(cosm_raw, "pin_id"),
            "character_id": safe_get(cosm_raw, "character_id"),
            "equipped_outfit_ids": to_int_list(safe_get(cosm_raw, "equipped_outfit_ids", [])),
            "equipped_weapon_skin_ids": to_int_list(safe_get(cosm_raw, "equipped_weapon_skin_ids", []))
        }

        # 7: Pass
        pass_raw = safe_get(raw_msg, "pass_info", {})
        pass_info = {
            "booyah_pass_level": safe_get(pass_raw, "booyah_pass_level"),
            "fire_pass_status": to_str(safe_get(pass_raw, "fire_pass_status")) or "Basic",
            "fire_pass_badge_count": safe_get(pass_raw, "fire_pass_badge_count")
        }

        # 8: Credit
        cred_raw = safe_get(raw_msg, "credit", {})
        credit = {
            "score": safe_get(cred_raw, "credit_score"),
            "reward_claimed": bool(safe_get(cred_raw, "credit_reward_claimed")),
            "summary_period": to_str(safe_get(cred_raw, "credit_summary_period"))
        }

        # 9: Ban
        ban_raw = safe_get(raw_msg, "ban", {})
        ban = {
            "is_banned": bool(safe_get(ban_raw, "is_banned")),
            "ban_period": to_str(safe_get(ban_raw, "ban_period")),
            "ban_type": to_str(safe_get(ban_raw, "ban_type"))
        }

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

    except FFError:
        raise
    except Exception as e:
        logger.exception("Decoding error")
        raise FFError(
            ErrorCode.DECODE_ERROR,
            f"Failed to decode player data: {str(e)}"
        )
