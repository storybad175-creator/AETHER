from typing import Optional, List, Annotated, Union
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
    extra: Optional[dict] = None

    model_config = ConfigDict(populate_by_name=True)

# --- Player Data Sub-Models ---

class AccountInfo(BaseModel):
    uid: str
    nickname: Optional[str] = None
    level: Optional[int] = None
    exp: Optional[int] = None
    region: Optional[str] = None
    season_id: Optional[int] = None
    preferred_mode: Optional[str] = None
    language: Optional[str] = None
    signature: Optional[str] = None
    honor_score: Optional[int] = None
    total_likes: Optional[int] = None
    ob_version: Optional[str] = None
    created_at_epoch: Optional[int] = None
    created_at: Optional[str] = None
    last_login_epoch: Optional[int] = None
    last_login: Optional[str] = None
    account_type: str = "Normal"

    model_config = ConfigDict(populate_by_name=True)

class RankInfo(BaseModel):
    rank_name: str
    rank_code: Optional[int] = None
    points: Optional[int] = None
    visible: bool = True

    model_config = ConfigDict(populate_by_name=True)

class BRRankInfo(RankInfo):
    max_rank_name: Optional[str] = None
    max_rank_code: Optional[int] = None

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
    clash_squad: dict[str, CSRankedStats]

    model_config = ConfigDict(populate_by_name=True)

class GuildLeader(BaseModel):
    uid: str
    nickname: Optional[str] = None
    level: Optional[int] = None
    rank_name: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)

class GuildInfo(BaseModel):
    id: str
    name: Optional[str] = None
    level: Optional[int] = None
    member_count: Optional[int] = None
    capacity: Optional[int] = None
    leader: Optional[GuildLeader] = None

    model_config = ConfigDict(populate_by_name=True)

class SocialInfo(BaseModel):
    guild: Optional[GuildInfo] = None

    model_config = ConfigDict(populate_by_name=True)

class PetInfo(BaseModel):
    name: Optional[str] = None
    level: Optional[int] = None
    exp: Optional[int] = None
    active_skill: Optional[str] = None
    skin_id: Optional[int] = None
    is_selected: bool = False

    model_config = ConfigDict(populate_by_name=True)

class CosmeticsInfo(BaseModel):
    avatar_id: Optional[int] = None
    banner_id: Optional[int] = None
    pin_id: Optional[int] = None
    character_id: Optional[int] = None
    equipped_outfit_ids: List[int] = []
    equipped_weapon_skin_ids: List[int] = []

    model_config = ConfigDict(populate_by_name=True)

class PassInfo(BaseModel):
    booyah_pass_level: Optional[int] = None
    fire_pass_status: str = "Basic"
    fire_pass_badge_count: Optional[int] = None

    model_config = ConfigDict(populate_by_name=True)

class CreditInfo(BaseModel):
    score: Optional[int] = None
    reward_claimed: bool = False
    summary_period: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)

class BanInfo(BaseModel):
    is_banned: bool = False
    ban_period: Optional[str] = None
    ban_type: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)

# --- Main Output Models ---

class PlayerData(BaseModel):
    account: AccountInfo
    rank: ModeRankInfo
    stats: StatsInfo
    social: SocialInfo
    pet: Optional[PetInfo] = None
    cosmetics: CosmeticsInfo
    pass_info: PassInfo = Field(..., alias="pass")
    credit: CreditInfo
    ban: BanInfo

    model_config = ConfigDict(populate_by_name=True)

class PlayerResponse(BaseModel):
    metadata: ResponseMetadata
    data: Optional[PlayerData] = None
    error: Optional[ErrorDetail] = None

    model_config = ConfigDict(populate_by_name=True)
