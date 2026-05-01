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
    Handles nested protobuf messages via Strategy B.
    """
    try:
        # Step 1: AES Decrypt
        try:
            decrypted_bytes = aes_decrypt(raw_encrypted)
        except Exception as e:
            # Possible key rotation if decryption fails or padding is wrong
            logger.error(f"AES Decryption failed: {e}")
            raise FFError(
                ErrorCode.DECODE_ERROR,
                "Failed to decrypt player data. AES Key/IV may have rotated.",
                extra={"possible_key_rotation": True, "action": "Update AES_KEY and AES_IV in .env"}
            )

        # Step 2: Protobuf Decode (Top level)
        raw_msg = decode_response(decrypted_bytes)
        if not raw_msg:
             raise ValueError("Decoded protobuf message is empty")

        def safe_get(data: Dict[int, Any], field_id: int, default: Any = None) -> Any:
            return data.get(field_id, default)

        def decode_nested(data: Any) -> Dict[int, Any]:
            if isinstance(data, dict):
                return data
            if isinstance(data, bytes):
                return decode_response(data)
            return {}

        def to_str(data: Any) -> Optional[str]:
            if isinstance(data, bytes):
                try:
                    return data.decode('utf-8')
                except:
                    return None
            return str(data) if data is not None else None

        def format_iso8601(epoch: Optional[int]) -> Optional[str]:
            if not epoch:
                return None
            return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(epoch))

        # --- Sub-message Decoders ---

        # 1: Account
        acc_raw = decode_nested(safe_get(raw_msg, FLD_ACCOUNT))
        created_epoch = safe_get(acc_raw, FLD_ACC_CREATED)
        login_epoch = safe_get(acc_raw, FLD_ACC_LOGIN)
        account = {
            "uid": to_str(safe_get(acc_raw, FLD_ACC_UID)),
            "nickname": to_str(safe_get(acc_raw, FLD_ACC_NICKNAME)),
            "level": safe_get(acc_raw, FLD_ACC_LEVEL),
            "exp": safe_get(acc_raw, FLD_ACC_EXP),
            "region": to_str(safe_get(acc_raw, FLD_ACC_REGION)),
            "season_id": safe_get(acc_raw, FLD_ACC_SEASON),
            "preferred_mode": to_str(safe_get(acc_raw, FLD_ACC_MODE)) or "Battle Royale",
            "language": to_str(safe_get(acc_raw, FLD_ACC_LANG)) or "English",
            "signature": to_str(safe_get(acc_raw, FLD_ACC_SIGNATURE)),
            "honor_score": safe_get(acc_raw, FLD_ACC_HONOR),
            "total_likes": safe_get(acc_raw, FLD_ACC_LIKES),
            "ob_version": to_str(safe_get(acc_raw, FLD_ACC_OB_VER)),
            "created_at_epoch": created_epoch,
            "created_at": format_iso8601(created_epoch),
            "last_login_epoch": login_epoch,
            "last_login": format_iso8601(login_epoch),
            "account_type": "Normal" if safe_get(acc_raw, FLD_ACC_TYPE) == 0 else "Special"
        }

        # 2: Rank
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

        # 3: Stats
        stats_raw = decode_nested(safe_get(raw_msg, FLD_STATS))

        def parse_stat_line(data: Any) -> Dict[str, Any]:
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
                "avg_damage_per_match": round(safe_get(d, FLD_SL_AVG_DMG, 0.0), 2),
                "booyahs": w
            }

        cs_raw = decode_nested(safe_get(stats_raw, FLD_STATS_CS_RANKED))
        cs_m = safe_get(cs_raw, FLD_SL_MATCHES, 0)
        cs_w = safe_get(cs_raw, FLD_SL_WINS, 0)
        cs_k = safe_get(cs_raw, FLD_SL_KILLS, 0)

        stats = {
            "battle_royale": {
                "solo": parse_stat_line(safe_get(stats_raw, FLD_STATS_BR_SOLO)),
                "duo": parse_stat_line(safe_get(stats_raw, FLD_STATS_BR_DUO)),
                "squad": parse_stat_line(safe_get(stats_raw, FLD_STATS_BR_SQUAD))
            },
            "clash_squad": {
                "ranked": {
                    "matches": cs_m,
                    "wins": cs_w,
                    "win_rate": f"{(cs_w / max(cs_m, 1) * 100):.2f}%",
                    "kills": cs_k,
                    "kd_ratio": round(cs_k / max(cs_m - cs_w, 1), 2)
                }
            }
        }

        # 4: Social
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
                    "uid": to_str(safe_get(social_raw, FLD_SOC_LEADER_UID)),
                    "nickname": to_str(safe_get(social_raw, FLD_SOC_LEADER_NAME)),
                    "level": safe_get(social_raw, FLD_SOC_LEADER_LEVEL),
                    "rank_name": get_rank_name(safe_get(social_raw, FLD_SOC_LEADER_RANK))
                }
            } if guild_id else None
        }

        # 5: Pet
        pet_raw = decode_nested(safe_get(raw_msg, FLD_PET))
        pet_name = to_str(safe_get(pet_raw, FLD_PET_NAME))
        pet = {
            "name": pet_name,
            "level": safe_get(pet_raw, FLD_PET_LEVEL),
            "exp": safe_get(pet_raw, FLD_PET_EXP),
            "active_skill": to_str(safe_get(pet_raw, FLD_PET_SKILL)),
            "skin_id": safe_get(pet_raw, FLD_PET_SKIN),
            "is_selected": bool(safe_get(pet_raw, FLD_PET_SELECTED))
        } if pet_name else None

        # 6: Cosmetics
        cosm_raw = decode_nested(safe_get(raw_msg, FLD_COSMETICS))

        def to_int_list(data: Any) -> list[int]:
            if isinstance(data, list):
                return [int.from_bytes(x, 'little') if isinstance(x, bytes) else int(x) for x in data]
            if isinstance(data, bytes):
                return [int.from_bytes(data, 'little')]
            if data is not None:
                return [int(data)]
            return []

        cosmetics = {
            "avatar_id": safe_get(cosm_raw, FLD_COS_AVATAR),
            "banner_id": safe_get(cosm_raw, FLD_COS_BANNER),
            "pin_id": safe_get(cosm_raw, FLD_COS_PIN),
            "character_id": safe_get(cosm_raw, FLD_COS_CHAR),
            "equipped_outfit_ids": to_int_list(safe_get(cosm_raw, FLD_COS_OUTFITS, [])),
            "equipped_weapon_skin_ids": to_int_list(safe_get(cosm_raw, FLD_COS_WEAPONS, []))
        }

        # 7: Pass
        pass_raw = decode_nested(safe_get(raw_msg, FLD_PASS))
        pass_info = {
            "booyah_pass_level": safe_get(pass_raw, FLD_PASS_LEVEL),
            "fire_pass_status": to_str(safe_get(pass_raw, FLD_PASS_STATUS)) or "Basic",
            "fire_pass_badge_count": safe_get(pass_raw, FLD_PASS_BADGES)
        }

        # 8: Credit
        cred_raw = decode_nested(safe_get(raw_msg, FLD_CREDIT))
        credit = {
            "score": safe_get(cred_raw, FLD_CRED_SCORE),
            "reward_claimed": bool(safe_get(cred_raw, FLD_CRED_REWARD)),
            "summary_period": to_str(safe_get(cred_raw, FLD_CRED_SUMMARY))
        }

        # 9: Ban
        ban_raw = decode_nested(safe_get(raw_msg, FLD_BAN))
        ban = {
            "is_banned": bool(safe_get(ban_raw, FLD_BAN_STATUS)),
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
        # If decryption succeeded but proto parsing failed, it might be key rotation
        raise FFError(
            ErrorCode.DECODE_ERROR,
            f"Failed to decode player data: {str(e)}",
            extra={"possible_key_rotation": True, "action": "Update AES_KEY and AES_IV in .env"}
        )
