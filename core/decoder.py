import time
import logging
from typing import Any, Dict, Optional, Union
from core.crypto import aes_decrypt
from core.proto import decode_response
from api.schemas import PlayerData
from config.ranks import get_rank_name
from api.errors import FFError, ErrorCode
from config.fields import *

logger = logging.getLogger(__name__)

def decode_player_data(raw_encrypted: bytes) -> PlayerData:
    """
    Decrypts, decodes, and maps raw Garena response bytes to a PlayerData model.
    Handles nested protobuf messages via recursive Strategy B.
    """
    try:
        # Step 1: AES Decrypt
        try:
            decrypted_bytes = aes_decrypt(raw_encrypted)
        except Exception as e:
            logger.error(f"AES decryption failed: {e}")
            raise FFError(
                ErrorCode.DECODE_ERROR,
                "Failed to decrypt player data. Possible AES key rotation.",
                extra={"possible_key_rotation": True, "action": "Update AES_KEY and AES_IV in .env"}
            )

        # Step 2: Protobuf Decode
        # The recursive decoder already handles nesting
        raw_msg = decode_response(decrypted_bytes)
        if not isinstance(raw_msg, dict) or not raw_msg:
             raise ValueError("Protobuf decoding returned empty or invalid data.")

        def safe_get(data: Dict[int, Any], field_id: int, default: Any = None) -> Any:
            if not isinstance(data, dict):
                return default
            return data.get(field_id, default)

        def decode_nested(data: Any) -> Dict[int, Any]:
            # With recursive decoder, nested fields might already be dicts
            if isinstance(data, dict):
                return data
            if isinstance(data, bytes) and data:
                return decode_response(data)
            return {}

        def to_str(data: Any) -> Optional[str]:
            if isinstance(data, bytes):
                try:
                    return data.decode('utf-8')
                except:
                    return None
            return str(data) if data is not None else None

        # --- Sub-message Mapping using Symbolic Constants ---

        # Account
        acc_raw = decode_nested(safe_get(raw_msg, FLD_ACCOUNT))
        account = {
            "uid": to_str(safe_get(acc_raw, FLD_ACC_UID)),
            "nickname": to_str(safe_get(acc_raw, FLD_ACC_NICKNAME)),
            "level": safe_get(acc_raw, FLD_ACC_LEVEL),
            "exp": safe_get(acc_raw, FLD_ACC_EXP),
            "region": to_str(safe_get(acc_raw, FLD_ACC_REGION)),
            "season_id": safe_get(acc_raw, FLD_ACC_SEASON_ID),
            "preferred_mode": to_str(safe_get(acc_raw, FLD_ACC_PREF_MODE)) or "Battle Royale",
            "language": to_str(safe_get(acc_raw, FLD_ACC_LANG)) or "English",
            "signature": to_str(safe_get(acc_raw, FLD_ACC_SIGNATURE)),
            "honor_score": safe_get(acc_raw, FLD_ACC_HONOR),
            "total_likes": safe_get(acc_raw, FLD_ACC_LIKES),
            "ob_version": to_str(safe_get(acc_raw, FLD_ACC_OB_VERSION)),
            "created_at_epoch": safe_get(acc_raw, FLD_ACC_CREATED_AT),
            "created_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(safe_get(acc_raw, FLD_ACC_CREATED_AT, 0))),
            "last_login_epoch": safe_get(acc_raw, FLD_ACC_LAST_LOGIN),
            "last_login": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(safe_get(acc_raw, FLD_ACC_LAST_LOGIN, 0))),
            "account_type": "Normal" if safe_get(acc_raw, FLD_ACC_TYPE) == 0 else "Special"
        }

        # Rank
        rank_raw = decode_nested(safe_get(raw_msg, FLD_RANK))
        rank = {
            "battle_royale": {
                "rank_name": get_rank_name(safe_get(rank_raw, FLD_RANK_BR_CODE)),
                "rank_code": safe_get(rank_raw, FLD_RANK_BR_CODE),
                "points": safe_get(rank_raw, FLD_RANK_BR_POINTS),
                "max_rank_name": get_rank_name(safe_get(rank_raw, FLD_RANK_BR_MAX_CODE)),
                "max_rank_code": safe_get(rank_raw, FLD_RANK_BR_MAX_CODE),
                "visible": bool(safe_get(rank_raw, FLD_RANK_BR_VISIBLE, True))
            },
            "clash_squad": {
                "rank_name": get_rank_name(safe_get(rank_raw, FLD_RANK_CS_CODE)),
                "rank_code": safe_get(rank_raw, FLD_RANK_CS_CODE),
                "points": safe_get(rank_raw, FLD_RANK_CS_POINTS),
                "visible": bool(safe_get(rank_raw, FLD_RANK_CS_VISIBLE, True))
            }
        }

        # Stats
        stats_raw = decode_nested(safe_get(raw_msg, FLD_STATS))

        def parse_stat_line(data: Union[Dict, bytes]) -> Dict[str, Any]:
            d = decode_nested(data)
            m = safe_get(d, FLD_SL_MATCHES, 0)
            w = safe_get(d, FLD_SL_WINS, 0)
            k = safe_get(d, FLD_SL_KILLS, 0)
            de = safe_get(d, FLD_SL_DEATHS, 0)
            hs = safe_get(d, FLD_SL_HEADSHOTS, 0)

            return {
                "matches": m,
                "wins": w,
                "win_rate": f"{(w / max(m, 1) * 100):.2f}%",
                "kills": k,
                "deaths": de,
                "kd_ratio": round(k / max(de, 1), 2),
                "headshots": hs,
                "headshot_rate": f"{(hs / max(k, 1) * 100):.2f}%",
                "avg_damage_per_match": round(safe_get(d, FLD_SL_AVG_DAMAGE, 0.0), 2),
                "booyahs": safe_get(d, FLD_SL_BOOYAHS, w)
            }

        stats = {
            "battle_royale": {
                "solo": parse_stat_line(safe_get(stats_raw, FLD_STATS_BR_SOLO, {})),
                "duo": parse_stat_line(safe_get(stats_raw, FLD_STATS_BR_DUO, {})),
                "squad": parse_stat_line(safe_get(stats_raw, FLD_STATS_BR_SQUAD, {}))
            },
            "clash_squad": {
                "ranked": {
                    "matches": safe_get(decode_nested(safe_get(stats_raw, FLD_STATS_CS_RANKED, {})), FLD_SL_MATCHES, 0),
                    "wins": safe_get(decode_nested(safe_get(stats_raw, FLD_STATS_CS_RANKED, {})), FLD_SL_WINS, 0),
                    "win_rate": "0.00%",
                    "kills": safe_get(decode_nested(safe_get(stats_raw, FLD_STATS_CS_RANKED, {})), FLD_SL_KILLS, 0),
                    "kd_ratio": 0.0
                }
            }
        }
        cs_r = stats["clash_squad"]["ranked"]
        cs_r["win_rate"] = f"{(cs_r['wins'] / max(cs_r['matches'], 1) * 100):.2f}%"
        cs_r["kd_ratio"] = round(cs_r["kills"] / max(cs_r["matches"] - cs_r["wins"], 1), 2)

        # Social
        social_raw = decode_nested(safe_get(raw_msg, FLD_SOCIAL))
        guild_id = to_str(safe_get(social_raw, FLD_SOC_GUILD_ID))
        social = {
            "guild": {
                "id": guild_id,
                "name": to_str(safe_get(social_raw, FLD_SOC_GUILD_NAME)),
                "level": safe_get(social_raw, FLD_SOC_GUILD_LEVEL),
                "member_count": safe_get(social_raw, FLD_SOC_GUILD_MEMBERS),
                "capacity": safe_get(social_raw, FLD_SOC_GUILD_CAPACITY),
                "leader": {
                    "uid": to_str(safe_get(social_raw, FLD_SOC_GUILD_LEADER_UID)),
                    "nickname": to_str(safe_get(social_raw, FLD_SOC_GUILD_LEADER_NICK)),
                    "level": safe_get(social_raw, FLD_SOC_GUILD_LEADER_LEVEL),
                    "rank_name": get_rank_name(safe_get(social_raw, FLD_SOC_GUILD_LEADER_RANK))
                }
            } if guild_id else None
        }

        # Pet
        pet_raw = decode_nested(safe_get(raw_msg, FLD_PET))
        pet_name = to_str(safe_get(pet_raw, FLD_PET_NAME))
        pet = {
            "name": pet_name,
            "level": safe_get(pet_raw, FLD_PET_LEVEL),
            "exp": safe_get(pet_raw, FLD_PET_EXP),
            "active_skill": to_str(safe_get(pet_raw, FLD_PET_SKILL)),
            "skin_id": safe_get(pet_raw, FLD_PET_SKIN_ID),
            "is_selected": bool(safe_get(pet_raw, FLD_PET_SELECTED))
        } if pet_name else None

        # Cosmetics
        cosm_raw = decode_nested(safe_get(raw_msg, FLD_COSMETICS))

        def to_int_list(data: Any) -> list[int]:
            if isinstance(data, list):
                return [int.from_bytes(x, 'little') if isinstance(x, bytes) else int(x) for x in data]
            if isinstance(data, (bytes, int)):
                return [int.from_bytes(data, 'little') if isinstance(data, bytes) else int(data)]
            return []

        cosmetics = {
            "avatar_id": safe_get(cosm_raw, FLD_COS_AVATAR),
            "banner_id": safe_get(cosm_raw, FLD_COS_BANNER),
            "pin_id": safe_get(cosm_raw, FLD_COS_PIN),
            "character_id": safe_get(cosm_raw, FLD_COS_CHARACTER),
            "equipped_outfit_ids": to_int_list(safe_get(cosm_raw, FLD_COS_OUTFITS, [])),
            "equipped_weapon_skin_ids": to_int_list(safe_get(cosm_raw, FLD_COS_WEAPONS, []))
        }

        # Pass
        pass_raw = decode_nested(safe_get(raw_msg, FLD_PASS_INFO))
        pass_info = {
            "booyah_pass_level": safe_get(pass_raw, FLD_PASS_BP_LEVEL),
            "fire_pass_status": to_str(safe_get(pass_raw, FLD_PASS_STATUS)) or "Basic",
            "fire_pass_badge_count": safe_get(pass_raw, FLD_PASS_BADGES)
        }

        # Credit
        cred_raw = decode_nested(safe_get(raw_msg, FLD_CREDIT))
        credit = {
            "score": safe_get(cred_raw, FLD_CRED_SCORE),
            "reward_claimed": bool(safe_get(cred_raw, FLD_CRED_REWARD)),
            "summary_period": to_str(safe_get(cred_raw, FLD_CRED_PERIOD))
        }

        # Ban
        ban_raw = decode_nested(safe_get(raw_msg, FLD_BAN))
        ban = {
            "is_banned": bool(safe_get(ban_raw, FLD_BAN_IS_BANNED)),
            "ban_period": to_str(safe_get(ban_raw, FLD_BAN_PERIOD)),
            "ban_type": to_str(safe_get(ban_raw, FLD_BAN_TYPE))
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
            f"Failed to decode player data: {str(e)}",
            extra={"possible_key_rotation": True}
        )
