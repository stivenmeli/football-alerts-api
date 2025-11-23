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
    import os
    
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    
    # Ocultar parcialmente valores sensibles
    token_preview = f"{token[:10]}...{token[-10:]}" if token and len(token) > 20 else "EMPTY OR TOO SHORT"
    
    # Verificar variables del sistema directamente
    telegram_token_env = os.getenv("TELEGRAM_BOT_TOKEN", "NOT_FOUND")
    telegram_chat_env = os.getenv("TELEGRAM_CHAT_ID", "NOT_FOUND")
    api_key_env = os.getenv("API_FOOTBALL_KEY", "NOT_FOUND")
    
    return {
        "from_settings": {
            "telegram_bot_token_length": len(token) if token else 0,
            "telegram_bot_token_preview": token_preview,
            "telegram_chat_id": chat_id,
            "api_football_key_length": len(settings.API_FOOTBALL_KEY) if settings.API_FOOTBALL_KEY else 0,
            "project_name": settings.PROJECT_NAME,
            "leagues_to_monitor": settings.LEAGUES_TO_MONITOR,
        },
        "from_os_environ": {
            "telegram_bot_token": "FOUND" if telegram_token_env != "NOT_FOUND" else "NOT_FOUND",
            "telegram_chat_id": "FOUND" if telegram_chat_env != "NOT_FOUND" else "NOT_FOUND",
            "api_football_key": "FOUND" if api_key_env != "NOT_FOUND" else "NOT_FOUND",
            "port": os.getenv("PORT", "NOT_FOUND"),
        }
    }


@router.get("/test-odds-api")
async def test_odds_api() -> dict[str, Any]:
    """Test connection to The Odds API."""
    from app.services.the_odds_api_service import TheOddsAPIService
    from datetime import datetime, timezone, timedelta
    
    odds_service = TheOddsAPIService()
    result = await odds_service.test_connection()
    
    # Try to get some sample odds
    try:
        sample_odds = await odds_service.get_odds_for_soccer(leagues=["soccer_epl"], regions="eu", markets="h2h")
        result["sample_matches_count"] = len(sample_odds)
        
        # Check 20 hour window
        now_utc = datetime.now(timezone.utc)
        window_end = now_utc + timedelta(hours=20)
        
        in_window = []
        for match in sample_odds:
            commence_time_str = match.get("commence_time")
            if commence_time_str:
                match_dt = datetime.fromisoformat(commence_time_str.replace('Z', '+00:00'))
                if now_utc <= match_dt <= window_end:
                    hours_until = (match_dt - now_utc).total_seconds() / 3600
                    in_window.append({
                        "home": match.get("home_team"),
                        "away": match.get("away_team"),
                        "hours_until": round(hours_until, 1)
                    })
        
        result["in_20h_window"] = len(in_window)
        result["sample_in_window"] = in_window[:3] if in_window else []
        result["current_time_utc"] = now_utc.isoformat()
        result["window_end_utc"] = window_end.isoformat()
        
    except Exception as e:
        result["sample_error"] = str(e)
    
    return result


@router.get("/debug-fixtures")
async def debug_fixtures() -> dict[str, Any]:
    """Detailed debug of fixture fetching process."""
    from app.services.the_odds_api_service import TheOddsAPIService
    from datetime import datetime, timezone, timedelta
    
    odds_service = TheOddsAPIService()
    now_utc = datetime.now(timezone.utc)
    window_end = now_utc + timedelta(hours=20)
    
    debug_info = {
        "current_time_utc": now_utc.isoformat(),
        "window_end_utc": window_end.isoformat(),
        "leagues_configured": settings.THE_ODDS_LEAGUES,
        "leagues_by_key": {}
    }
    
    # Check each league
    leagues = settings.THE_ODDS_LEAGUES.split(",")
    total_in_window = 0
    total_with_low_odds = 0
    
    for league_key in leagues:
        try:
            matches = await odds_service.get_odds(league_key.strip(), regions="eu", markets="h2h")
            if not matches:
                debug_info["leagues_by_key"][league_key] = {"error": "No matches returned"}
                continue
                
            in_window = 0
            low_odds = 0
            sample_matches = []
            
            for match in matches:
                commence_time_str = match.get("commence_time")
                if not commence_time_str:
                    continue
                    
                match_dt = datetime.fromisoformat(commence_time_str.replace('Z', '+00:00'))
                
                # Check if in window
                if now_utc <= match_dt <= window_end:
                    in_window += 1
                    
                    # Get minimum odd
                    min_odd = 999
                    if match.get("bookmakers"):
                        for bookmaker in match["bookmakers"]:
                            for market in bookmaker.get("markets", []):
                                if market["key"] == "h2h":
                                    for outcome in market.get("outcomes", []):
                                        min_odd = min(min_odd, outcome.get("price", 999))
                    
                    if min_odd < 1.35:
                        low_odds += 1
                        
                    if len(sample_matches) < 2:
                        hours_until = (match_dt - now_utc).total_seconds() / 3600
                        sample_matches.append({
                            "home": match.get("home_team"),
                            "away": match.get("away_team"),
                            "hours_until": round(hours_until, 1),
                            "min_odd": round(min_odd, 2) if min_odd < 999 else None
                        })
            
            total_in_window += in_window
            total_with_low_odds += low_odds
            
            debug_info["leagues_by_key"][league_key] = {
                "total_matches": len(matches),
                "in_20h_window": in_window,
                "with_low_odds": low_odds,
                "sample_matches": sample_matches
            }
            
        except Exception as e:
            debug_info["leagues_by_key"][league_key] = {"error": str(e)}
    
    debug_info["summary"] = {
        "total_in_window": total_in_window,
        "total_with_low_odds": total_with_low_odds
    }
    
    return debug_info

