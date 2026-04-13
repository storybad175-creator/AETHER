import pytest
from fastapi.testclient import TestClient
from ff_api.main import app
from unittest.mock import AsyncMock, patch

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_regions_endpoint():
    response = client.get("/regions")
    assert response.status_code == 200
    assert "IND" in response.json()

from ff_api.api.schemas import PlayerResponse, ResponseMetadata, PlayerData, AccountInfo, ModeRankInfo, BRRankInfo, RankInfo, StatsInfo, BRStats, StatLine, CSRankedStats, SocialInfo, CosmeticsInfo, PassInfo, CreditInfo, BanInfo

@patch("ff_api.api.routes.fetch_player", new_callable=AsyncMock)
def test_player_endpoint_valid(mock_fetch):
    metadata = ResponseMetadata(
        request_uid="1234567",
        request_region="IND",
        fetched_at="2026-04-11T14:32:07Z",
        response_time_ms=100,
        api_version="OB53",
        cache_hit=False
    )
    account = AccountInfo(
        uid="1234567", nickname="Test", level=1, exp=0, region="IND",
        season_id=1, preferred_mode="BR", language="EN", signature="",
        honor_score=100, total_likes=0, ob_version="OB53",
        created_at_epoch=0, created_at=None, last_login_epoch=0,
        last_login=None, account_type="Normal"
    )
    rank = ModeRankInfo(
        battle_royale=BRRankInfo(rank_name="Bronze I", rank_code=101, points=0, max_rank_name=None, max_rank_code=None, visible=True),
        clash_squad=RankInfo(rank_name="Bronze I", rank_code=201, points=0, visible=True)
    )
    stat_line = StatLine(matches=0, wins=0, win_rate="0%", kills=0, deaths=0, kd_ratio=0, headshots=0, headshot_rate="0%", avg_damage_per_match=0, booyahs=0)
    stats = StatsInfo(
        battle_royale=BRStats(solo=stat_line, duo=stat_line, squad=stat_line),
        clash_squad=CSRankedStats(matches=0, wins=0, win_rate="0%", kills=0, kd_ratio=0)
    )
    data = PlayerData(
        account=account, rank=rank, stats=stats, social=SocialInfo(guild=None),
        pet=None, cosmetics=CosmeticsInfo(equipped_outfit_ids=[], equipped_weapon_skin_ids=[]),
        pass_info=PassInfo(booyah_pass_level=0, fire_pass_status="Basic", fire_pass_badge_count=0),
        credit=CreditInfo(score=100, reward_claimed=False, summary_period=""),
        ban=BanInfo(is_banned=False, ban_period=None, ban_type=None)
    )
    mock_fetch.return_value = PlayerResponse(metadata=metadata, data=data)
    response = client.get("/player?uid=1234567&region=IND")
    assert response.status_code == 200
