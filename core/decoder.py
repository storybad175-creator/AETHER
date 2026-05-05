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
        decrypted_bytes = aes_decrypt(raw_encrypted)

        # Step 2: Protobuf Decode (Top level)
        # 1: account, 2: rank, 3: stats, 4: social, 5: pet, 6: cosmetics, 7: pass, 8: credit, 9: ban
        raw_msg = decode_response(decrypted_bytes)

        def safe_get(data: Dict[int, Any], field_id: int, default: Any = None) -> Any:
            return data.get(field_id, default)

        def decode_nested(data: Any) -> Dict[int, Any]:
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

        def format_iso(epoch: Optional[int]) -> Optional[str]:
            if epoch is None or epoch <= 0:
                return None
            return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(epoch))

        # --- Sub-message Decoders ---

        # 1: Account
        acc_raw = decode_nested(safe_get(raw_msg, 1))
        account = {
            "uid": to_str(safe_get(acc_raw, 101)),
            "nickname": to_str(safe_get(acc_raw, 102)),
            "level": safe_get(acc_raw, 103),
            "exp": safe_get(acc_raw, 104),
            "region": to_str(safe_get(acc_raw, 105)),
            "season_id": safe_get(acc_raw, 106),
            "preferred_mode": to_str(safe_get(acc_raw, 107)) or "Battle Royale",
            "language": to_str(safe_get(acc_raw, 108)) or "English",
            "signature": to_str(safe_get(acc_raw, 109)),
            "honor_score": safe_get(acc_raw, 110),
            "total_likes": safe_get(acc_raw, 111),
            "ob_version": to_str(safe_get(acc_raw, 112)),
            "created_at_epoch": safe_get(acc_raw, 113),
            "created_at": format_iso(safe_get(acc_raw, 113)),
            "last_login_epoch": safe_get(acc_raw, 114),
            "last_login": format_iso(safe_get(acc_raw, 114)),
            "account_type": "Normal" if safe_get(acc_raw, 115) == 0 else "Special"
        }

        # 2: Rank
        rank_raw = decode_nested(safe_get(raw_msg, 2))
        rank = {
            "battle_royale": {
                "rank_name": get_rank_name(safe_get(rank_raw, 201)),
                "rank_code": safe_get(rank_raw, 201),
                "points": safe_get(rank_raw, 202),
                "max_rank_name": get_rank_name(safe_get(rank_raw, 203)),
                "max_rank_code": safe_get(rank_raw, 203),
                "visible": bool(safe_get(rank_raw, 204, True))
            },
            "clash_squad": {
                "rank_name": get_rank_name(safe_get(rank_raw, 205)),
                "rank_code": safe_get(rank_raw, 205),
                "points": safe_get(rank_raw, 206),
                "visible": bool(safe_get(rank_raw, 207, True))
            }
        }

        # 3: Stats
        stats_raw = decode_nested(safe_get(raw_msg, 3))

        def parse_stat_line(data_bytes_or_dict: Union[bytes, Dict[int, Any]]) -> Dict[str, Any]:
            d = decode_nested(data_bytes_or_dict)
            m = safe_get(d, 401, 0)
            w = safe_get(d, 402, 0)
            k = safe_get(d, 403, 0)
            de = safe_get(d, 404, 0)
            hs = safe_get(d, 405, 0)

            return {
                "matches": m,
                "wins": w,
                "win_rate": f"{(w / max(m, 1) * 100):.2f}%",
                "kills": k,
                "deaths": de,
                "kd_ratio": round(k / max(de, 1), 2),
                "headshots": hs,
                "headshot_rate": f"{(hs / max(k, 1) * 100):.2f}%",
                "avg_damage_per_match": round(float(safe_get(d, 406, 0.0)), 2),
                "booyahs": w
            }

        cs_ranked_raw = decode_nested(safe_get(stats_raw, 304))
        cs_m = safe_get(cs_ranked_raw, 401, 0)
        cs_w = safe_get(cs_ranked_raw, 402, 0)
        cs_k = safe_get(cs_ranked_raw, 403, 0)

        stats = {
            "battle_royale": {
                "solo": parse_stat_line(safe_get(stats_raw, 301, b"")),
                "duo": parse_stat_line(safe_get(stats_raw, 302, b"")),
                "squad": parse_stat_line(safe_get(stats_raw, 303, b""))
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
        social_raw = decode_nested(safe_get(raw_msg, 4))
        guild_id = to_str(safe_get(social_raw, 501))
        social = {
            "guild": {
                "id": guild_id,
                "name": to_str(safe_get(social_raw, 502)),
                "level": safe_get(social_raw, 503),
                "member_count": safe_get(social_raw, 504),
                "capacity": safe_get(social_raw, 505),
                "leader": {
                    "uid": to_str(safe_get(social_raw, 506)),
                    "nickname": to_str(safe_get(social_raw, 507)),
                    "level": safe_get(social_raw, 508),
                    "rank_name": get_rank_name(safe_get(social_raw, 509))
                }
            } if guild_id else None
        }

        # 5: Pet
        pet_raw = decode_nested(safe_get(raw_msg, 5))
        pet_name = to_str(safe_get(pet_raw, 601))
        pet = {
            "name": pet_name,
            "level": safe_get(pet_raw, 602),
            "exp": safe_get(pet_raw, 603),
            "active_skill": to_str(safe_get(pet_raw, 604)),
            "skin_id": safe_get(pet_raw, 605),
            "is_selected": bool(safe_get(pet_raw, 606))
        } if pet_name else None

        # 6: Cosmetics
        cosm_raw = decode_nested(safe_get(raw_msg, 6))

        def to_int_list(data: Any) -> list[int]:
            if isinstance(data, list):
                # Ensure each element is int
                result = []
                for x in data:
                    if isinstance(x, bytes):
                        # Handle potential binary encoded ints
                        try:
                            result.append(int.from_bytes(x, 'little'))
                        except: pass
                    else:
                        try:
                            result.append(int(x))
                        except: pass
                return result
            if data is not None:
                if isinstance(data, bytes):
                     try:
                        return [int.from_bytes(data, 'little')]
                     except: return []
                try:
                    return [int(data)]
                except: return []
            return []

        cosmetics = {
            "avatar_id": safe_get(cosm_raw, 701),
            "banner_id": safe_get(cosm_raw, 702),
            "pin_id": safe_get(cosm_raw, 703),
            "character_id": safe_get(cosm_raw, 704),
            "equipped_outfit_ids": to_int_list(safe_get(cosm_raw, 705, [])),
            "equipped_weapon_skin_ids": to_int_list(safe_get(cosm_raw, 706, []))
        }

        # 7: Pass
        pass_raw = decode_nested(safe_get(raw_msg, 7))
        pass_info = {
            "booyah_pass_level": safe_get(pass_raw, 801),
            "fire_pass_status": to_str(safe_get(pass_raw, 802)) or "Basic",
            "fire_pass_badge_count": safe_get(pass_raw, 803)
        }

        # 8: Credit
        cred_raw = decode_nested(safe_get(raw_msg, 8))
        credit = {
            "score": safe_get(cred_raw, 901),
            "reward_claimed": bool(safe_get(cred_raw, 902)),
            "summary_period": to_str(safe_get(cred_raw, 903))
        }

        # 9: Ban
        ban_raw = decode_nested(safe_get(raw_msg, 9))
        ban = {
            "is_banned": bool(safe_get(ban_raw, 1001)),
            "ban_period": to_str(safe_get(ban_raw, 1002)),
            "ban_type": to_str(safe_get(ban_raw, 1003))
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

    except Exception as e:
        if "PKCS7" in str(e) or "padding" in str(e).lower():
            logger.error("AES Decryption failed - possible key rotation")
            raise FFError(
                ErrorCode.DECODE_ERROR,
                "Failed to decrypt payload. The AES keys might have rotated.",
                extra={"possible_key_rotation": True, "action": "Update AES_KEY and AES_IV in .env"}
            )
        logger.exception("Decoding error")
        raise FFError(
            ErrorCode.DECODE_ERROR,
            f"Failed to decode player data: {str(e)}"
        )
