from typing import Optional, List, Annotated, Union, Dict
from pydantic import BaseModel, Field, field_validator, ConfigDict
from config.regions import REGION_MAP

# --- Input Models ---

class PlayerRequest(BaseModel):
    uid: str = Field(..., description="Player Unique ID")
    region: str = Field(..., description="Region code (e.g., IND, SG, BR)")

    @field_validator("uid")
    @classmethod
    def validate_uid(cls, v: str) -> str:
        if not v.isdigit() or not (5 <= len(v) <= 13):
            raise ValueError("UID must be numeric and between 5–13 digits.")
        return v

    @field_validator("region")
    @classmethod
    def validate_region(cls, v: str) -> str:
        region = v.upper()
        if region not in REGION_MAP:
            raise ValueError(f"Invalid region. Supported: {', '.join(REGION_MAP.keys())}")
        return region

    model_config = ConfigDict(populate_by_name=True)

# --- Metadata & Error Models ---

class ResponseMetadata(BaseModel):
    request_uid: str
    request_region: str
    fetched_at: str
    response_time_ms: int
    api_version: str
    cache_hit: bool

    model_config = ConfigDict(populate_by_name=True)

class ErrorDetail(BaseModel):
    code: str
    message: str
    retryable: bool
    extra: dict | None = None

    model_config = ConfigDict(populate_by_name=True)

# --- Player Data Sub-Models ---

class AccountInfo(BaseModel):
    uid: str
    nickname: str | None = None
    level: int | None = None
    exp: int | None = None
    region: str | None = None
    season_id: int | None = None
    preferred_mode: str | None = None
    language: str | None = None
    signature: str | None = None
    honor_score: int | None = None
    total_likes: int | None = None
    ob_version: str | None = None
    created_at_epoch: int | None = None
    created_at: str | None = None
    last_login_epoch: int | None = None
    last_login: str | None = None
    account_type: str = "Normal"

    model_config = ConfigDict(populate_by_name=True)

class RankInfo(BaseModel):
    rank_name: str
    rank_code: int | None = None
    points: int | None = None
    visible: bool = True

    model_config = ConfigDict(populate_by_name=True)

class BRRankInfo(RankInfo):
    max_rank_name: str | None = None
    max_rank_code: int | None = None

    model_config = ConfigDict(populate_by_name=True)

class ModeRankInfo(BaseModel):
    battle_royale: BRRankInfo
    clash_squad: RankInfo

    model_config = ConfigDict(populate_by_name=True)

class StatLine(BaseModel):
    matches: int = 0
    wins: int = 0
    win_rate: str = "0.00%"
    kills: int = 0
    deaths: int = 0
    kd_ratio: Annotated[float, Field(ge=0.0)] = 0.0
    headshots: int = 0
    headshot_rate: str = "0.00%"
    avg_damage_per_match: Annotated[float, Field(ge=0.0)] = 0.0
    booyahs: int = 0

    model_config = ConfigDict(populate_by_name=True)

class BRStats(BaseModel):
    solo: StatLine
    duo: StatLine
    squad: StatLine

    model_config = ConfigDict(populate_by_name=True)

class CSRankedStats(BaseModel):
    matches: int = 0
    wins: int = 0
    win_rate: str = "0.00%"
    kills: int = 0
    kd_ratio: Annotated[float, Field(ge=0.0)] = 0.0

    model_config = ConfigDict(populate_by_name=True)

class StatsInfo(BaseModel):
    battle_royale: BRStats
    clash_squad: Dict[str, CSRankedStats]

    model_config = ConfigDict(populate_by_name=True)

class GuildLeader(BaseModel):
    uid: str
    nickname: str | None = None
    level: int | None = None
    rank_name: str | None = None

    model_config = ConfigDict(populate_by_name=True)

class GuildInfo(BaseModel):
    id: str
    name: str | None = None
    level: int | None = None
    member_count: int | None = None
    capacity: int | None = None
    leader: GuildLeader | None = None

    model_config = ConfigDict(populate_by_name=True)

class SocialInfo(BaseModel):
    guild: GuildInfo | None = None

    model_config = ConfigDict(populate_by_name=True)

class PetInfo(BaseModel):
    name: str | None = None
    level: int | None = None
    exp: int | None = None
    active_skill: str | None = None
    skin_id: int | None = None
    is_selected: bool = False

    model_config = ConfigDict(populate_by_name=True)

class CosmeticsInfo(BaseModel):
    avatar_id: int | None = None
    banner_id: int | None = None
    pin_id: int | None = None
    character_id: int | None = None
    equipped_outfit_ids: List[int] = []
    equipped_weapon_skin_ids: List[int] = []

    model_config = ConfigDict(populate_by_name=True)

class PassInfo(BaseModel):
    booyah_pass_level: int | None = None
    fire_pass_status: str = "Basic"
    fire_pass_badge_count: int | None = None

    model_config = ConfigDict(populate_by_name=True)

class CreditInfo(BaseModel):
    score: int | None = None
    reward_claimed: bool = False
    summary_period: str | None = None

    model_config = ConfigDict(populate_by_name=True)

class BanInfo(BaseModel):
    is_banned: bool = False
    ban_period: str | None = None
    ban_type: str | None = None

    model_config = ConfigDict(populate_by_name=True)

# --- Main Output Models ---

class PlayerData(BaseModel):
    account: AccountInfo
    rank: ModeRankInfo
    stats: StatsInfo
    social: SocialInfo
    pet: PetInfo | None = None
    cosmetics: CosmeticsInfo
    pass_info: PassInfo = Field(..., alias="pass")
    credit: CreditInfo
    ban: BanInfo

    model_config = ConfigDict(populate_by_name=True)

class PlayerResponse(BaseModel):
    metadata: ResponseMetadata
    data: PlayerData | None = None
    error: ErrorDetail | None = None

    model_config = ConfigDict(populate_by_name=True)
