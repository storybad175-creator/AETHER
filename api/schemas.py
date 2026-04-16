from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Union, Annotated
from datetime import datetime
from config.regions import REGION_MAP

# ── Input Schemas ──────────────────────────────────────────────────

class PlayerRequest(BaseModel):
    uid: str = Field(..., description="The player's numeric UID (5-13 digits)")
    region: str = Field(..., description="The region code (e.g., IND, BR, SG)")

    @field_validator("uid")
    @classmethod
    def validate_uid(cls, v: str) -> str:
        if not v.isdigit() or not (5 <= len(v) <= 13):
            raise ValueError("UID must be numeric and between 5–13 digits.")
        return v

    @field_validator("region")
    @classmethod
    def validate_region(cls, v: str) -> str:
        v = v.upper()
        if v not in REGION_MAP:
            raise ValueError(f"Invalid region. Supported: {', '.join(REGION_MAP.keys())}")
        return v

# ── Output Metadata & Error ────────────────────────────────────────

class ResponseMetadata(BaseModel):
    request_uid: str
    request_region: str
    fetched_at: str
    response_time_ms: int
    api_version: str
    cache_hit: bool

class ErrorDetail(BaseModel):
    code: str
    message: str
    retryable: bool
    extra: Optional[dict] = None

# ── Player Data Components ────────────────────────────────────────

class AccountInfo(BaseModel):
    uid: str
    nickname: str
    level: int
    exp: int
    region: str
    season_id: int
    preferred_mode: str
    language: str
    signature: str
    honor_score: int
    total_likes: int
    ob_version: str
    created_at_epoch: Optional[int]
    created_at: Optional[str]
    last_login_epoch: Optional[int]
    last_login: Optional[str]
    account_type: str

class RankInfo(BaseModel):
    rank_name: str
    rank_code: int
    points: int
    visible: bool

class BRRankInfo(RankInfo):
    max_rank_name: str
    max_rank_code: int

class ModeRankInfo(BaseModel):
    battle_royale: BRRankInfo
    clash_squad: RankInfo

class StatLine(BaseModel):
    matches: int
    wins: int
    win_rate: str
    kills: int
    deaths: int
    kd_ratio: float
    headshots: int
    headshot_rate: str
    avg_damage_per_match: float
    booyahs: int

class BRStats(BaseModel):
    solo: StatLine
    duo: StatLine
    squad: StatLine

class CSRankedStats(BaseModel):
    matches: int
    wins: int
    win_rate: str
    kills: int
    kd_ratio: float

class StatsInfo(BaseModel):
    battle_royale: BRStats
    clash_squad: CSRankedStats

class GuildLeader(BaseModel):
    uid: str
    nickname: str
    level: int
    rank_name: str

class GuildInfo(BaseModel):
    id: str
    name: str
    level: int
    member_count: int
    capacity: int
    leader: GuildLeader

class SocialInfo(BaseModel):
    guild: Optional[GuildInfo]

class PetInfo(BaseModel):
    name: str
    level: int
    exp: int
    active_skill: str
    skin_id: int
    is_selected: bool

class CosmeticsInfo(BaseModel):
    avatar_id: int
    banner_id: int
    pin_id: int
    character_id: int
    equipped_outfit_ids: List[int]
    equipped_weapon_skin_ids: List[int]

class PassInfo(BaseModel):
    booyah_pass_level: int
    fire_pass_status: str
    fire_pass_badge_count: int

class CreditInfo(BaseModel):
    score: int
    reward_claimed: bool
    summary_period: str

class BanInfo(BaseModel):
    is_banned: bool
    ban_period: Optional[str]
    ban_type: Optional[str]

class PlayerData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    account: AccountInfo
    rank: ModeRankInfo
    stats: StatsInfo
    social: SocialInfo
    pet: Optional[PetInfo] = None
    cosmetics: CosmeticsInfo
    pass_info: PassInfo = Field(..., alias="pass")
    credit: CreditInfo
    ban: BanInfo

class PlayerResponse(BaseModel):
    metadata: ResponseMetadata
    data: Optional[PlayerData] = None
    error: Optional[ErrorDetail] = None
