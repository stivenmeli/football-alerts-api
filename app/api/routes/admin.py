"""Admin routes for manual operations."""

from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.monitor_service import MonitorService
from app.services.telegram_service import TelegramService
from app.models import Match, League, Team
from app.core.config import settings

router = APIRouter()


@router.post("/fetch-fixtures")
async def manual_fetch_fixtures(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Manually fetch fixtures for today."""
    monitor = MonitorService()
    count = await monitor.fetch_and_store_fixtures(db)
    return {
        "status": "success",
        "fixtures_fetched": count,
        "message": f"Fetched {count} fixtures"
    }


@router.post("/fetch-odds")
async def manual_fetch_odds(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Manually fetch odds for matches."""
    monitor = MonitorService()
    count = await monitor.fetch_and_store_odds(db)
    return {
        "status": "success",
        "odds_fetched": count,
        "message": f"Processed odds for {count} matches"
    }


@router.post("/monitor-matches")
async def manual_monitor(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Manually check live matches and send alerts."""
    monitor = MonitorService()
    alerts = await monitor.monitor_live_matches(db)
    return {
        "status": "success",
        "alerts_sent": alerts,
        "message": f"Sent {alerts} alerts"
    }


@router.get("/test-api-football")
async def test_api_football() -> dict[str, Any]:
    """Test API-Football connection."""
    from app.services.api_football import APIFootballService
    
    api = APIFootballService()
    
    try:
        # Test simple: obtener fixtures de mañana
        from datetime import date, timedelta
        tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        fixtures = await api.get_fixtures_by_date(tomorrow, 39)  # Premier League
        
        return {
            "status": "success",
            "message": "API-Football connected successfully",
            "date_tested": tomorrow,
            "fixtures_found": len(fixtures),
            "sample": fixtures[0] if fixtures else None
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to connect to API-Football"
        }


@router.post("/test-telegram")
async def test_telegram() -> dict[str, Any]:
    """Test Telegram bot connection."""
    telegram = TelegramService()
    result = await telegram.test_connection()
    
    if "error" in result:
        return {
            "status": "error",
            "error": result["error"],
            "message": "Failed to connect to Telegram bot"
        }
    
    # Send test message
    success = await telegram.send_message("🧪 Test message from Football Alerts API")
    
    return {
        "status": "success" if success else "error",
        "bot_info": result.get("result", {}),
        "test_message_sent": success
    }


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get system statistics."""
    total_matches = db.query(Match).count()
    monitored_matches = db.query(Match).filter(Match.should_monitor == True).count()  # noqa: E712
    notified_matches = db.query(Match).filter(Match.notification_sent == True).count()  # noqa: E712
    total_leagues = db.query(League).count()
    total_teams = db.query(Team).count()
    
    return {
        "total_matches": total_matches,
        "monitored_matches": monitored_matches,
        "notifications_sent": notified_matches,
        "total_leagues": total_leagues,
        "total_teams": total_teams,
    }


@router.get("/matches")
async def get_matches(
    monitored_only: bool = False,
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Get list of matches."""
    query = db.query(Match)
    
    if monitored_only:
        query = query.filter(Match.should_monitor == True)  # noqa: E712
    
    matches = query.limit(50).all()
    
    results = []
    for match in matches:
        home_team = db.query(Team).filter(Team.id == match.home_team_id).first()
        away_team = db.query(Team).filter(Team.id == match.away_team_id).first()
        league = db.query(League).filter(League.id == match.league_id).first()
        
        results.append({
            "id": match.id,
            "home_team": home_team.name if home_team else "Unknown",
            "away_team": away_team.name if away_team else "Unknown",
            "league": league.name if league else "Unknown",
            "status": match.status,
            "score": f"{match.home_score or 0} - {match.away_score or 0}",
            "minute": match.current_minute,
            "favorite_odds": match.favorite_odds,
            "should_monitor": match.should_monitor,
            "notification_sent": match.notification_sent,
        })
    
    return {
        "count": len(results),
        "matches": results
    }


@router.get("/env-check")
async def check_environment() -> dict[str, Any]:
    """Check environment variables configuration (for debugging)."""
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    
    # Ocultar parcialmente valores sensibles
    token_preview = f"{token[:10]}...{token[-10:]}" if token and len(token) > 20 else "EMPTY OR TOO SHORT"
    
    return {
        "telegram_bot_token_length": len(token) if token else 0,
        "telegram_bot_token_preview": token_preview,
        "telegram_chat_id": chat_id,
        "api_football_key_length": len(settings.API_FOOTBALL_KEY) if settings.API_FOOTBALL_KEY else 0,
        "project_name": settings.PROJECT_NAME,
        "leagues_to_monitor": settings.LEAGUES_TO_MONITOR,
    }

