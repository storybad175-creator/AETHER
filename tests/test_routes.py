import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, AsyncMock
from api.schemas import PlayerResponse, ResponseMetadata, PlayerData, AccountInfo, ModeRankInfo, BRRankInfo, RankInfo, StatsInfo, BRStats, CSRankedStats, StatLine, SocialInfo, CosmeticsInfo, PassInfo, CreditInfo, BanInfo

client = TestClient(app)

@pytest.fixture
def mock_player_response():
    return PlayerResponse(
        metadata=ResponseMetadata(
            request_uid="4899748638",
            request_region="IND",
            fetched_at="2026-04-11T14:32:07Z",
            response_time_ms=100,
            api_version="OB53",
            cache_hit=False
        ),
        data=PlayerData(
            account=AccountInfo(
                uid="4899748638", nickname="TestPlayer", level=60, exp=1000,
                region="IND", season_id=38, preferred_mode="BR", language="EN",
                signature="Hi", honor_score=100, total_likes=500, ob_version="OB53",
                created_at_epoch=0, created_at=None, last_login_epoch=0, last_login=None,
                account_type="Normal"
            ),
            rank=ModeRankInfo(
                battle_royale=BRRankInfo(rank_name="Heroic", rank_code=601, points=3200, max_rank_name="Heroic", max_rank_code=601, visible=True),
                clash_squad=RankInfo(rank_name="Gold", rank_code=301, points=100, visible=True)
            ),
            stats=StatsInfo(
                battle_royale=BRStats(
                    solo=StatLine(matches=0, wins=0, win_rate="0%", kills=0, deaths=0, kd_ratio=0, headshots=0, headshot_rate="0%", avg_damage_per_match=0, booyahs=0),
                    duo=StatLine(matches=0, wins=0, win_rate="0%", kills=0, deaths=0, kd_ratio=0, headshots=0, headshot_rate="0%", avg_damage_per_match=0, booyahs=0),
                    squad=StatLine(matches=0, wins=0, win_rate="0%", kills=0, deaths=0, kd_ratio=0, headshots=0, headshot_rate="0%", avg_damage_per_match=0, booyahs=0)
                ),
                clash_squad=CSRankedStats(matches=0, wins=0, win_rate="0%", kills=0, kd_ratio=0)
            ),
            social=SocialInfo(guild=None),
            cosmetics=CosmeticsInfo(avatar_id=0, banner_id=0, pin_id=0, character_id=0, equipped_outfit_ids=[], equipped_weapon_skin_ids=[]),
            pass_info=PassInfo(booyah_pass_level=0, fire_pass_status="Basic", fire_pass_badge_count=0),
            credit=CreditInfo(score=100, reward_claimed=False, summary_period=""),
            ban=BanInfo(is_banned=False)
        ),
        error=None
    )

@patch("api.routes.fetch_player")
def test_get_player_valid(mock_fetch, mock_player_response):
    mock_fetch.return_value = mock_player_response
    response = client.get("/player?uid=4899748638&region=IND")
    assert response.status_code == 200
    assert response.json()["data"]["account"]["nickname"] == "TestPlayer"

@patch("api.routes.fetch_player")
def test_get_player_cache_hit(mock_fetch, mock_player_response):
    # Simulate a cache hit by setting cache_hit=True in metadata
    mock_player_response.metadata.cache_hit = True
    mock_fetch.return_value = mock_player_response
    response = client.get("/player?uid=4899748638&region=IND")
    assert response.status_code == 200
    assert response.json()["metadata"]["cache_hit"] is True

def test_get_player_invalid_uid():
    response = client.get("/player?uid=abc&region=IND")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_UID"

def test_get_player_invalid_region():
    response = client.get("/player?uid=4899748638&region=XYZ")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REGION"

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
