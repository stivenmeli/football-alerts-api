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


@router.post("/update-monitoring-threshold")
async def update_monitoring_threshold(threshold: float, db: Session = Depends(get_db)) -> dict[str, Any]:
    """
    Actualizar manualmente qué partidos monitorear basado en un threshold temporal.
    Útil para testing sin cambiar la configuración de Railway.
    """
    from app.models import Match
    
    # Obtener todos los partidos con cuotas
    matches = db.query(Match).filter(Match.favorite_odds != None).all()
    
    updated_count = 0
    newly_monitored = []
    
    for match in matches:
        old_should_monitor = match.should_monitor
        new_should_monitor = match.favorite_odds <= threshold
        
        if old_should_monitor != new_should_monitor:
            match.should_monitor = new_should_monitor
            updated_count += 1
            
            if new_should_monitor:
                # Get team names for display
                from app.models import Team
                home_team = db.query(Team).filter(Team.id == match.home_team_id).first()
                away_team = db.query(Team).filter(Team.id == match.away_team_id).first()
                
                newly_monitored.append({
                    "home": home_team.name if home_team else "Unknown",
                    "away": away_team.name if away_team else "Unknown",
                    "odds": match.favorite_odds
                })
    
    db.commit()
    
    return {
        "status": "success",
        "threshold_used": threshold,
        "matches_updated": updated_count,
        "newly_monitored": newly_monitored,
        "message": f"Updated {updated_count} matches with threshold {threshold}"
    }


@router.post("/test-alert-simulation")
async def test_alert_simulation(
    match_id: int,
    home_score: int,
    away_score: int,
    current_minute: int,
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """
    Simula un escenario de partido en vivo para probar el sistema de alertas.
    
    Args:
        match_id: ID del partido a simular
        home_score: Goles del equipo local
        away_score: Goles del equipo visitante
        current_minute: Minuto actual del partido
    """
    from app.services.monitor_service import MonitorService
    from app.models import Team, League
    
    # Obtener el partido
    match = db.query(Match).filter(Match.id == match_id).first()
    
    if not match:
        return {"error": f"Match with ID {match_id} not found"}
    
    # Obtener información de equipos
    home_team = db.query(Team).filter(Team.id == match.home_team_id).first()
    away_team = db.query(Team).filter(Team.id == match.away_team_id).first()
    favorite_team = db.query(Team).filter(Team.id == match.favorite_team_id).first()
    
    if not all([home_team, away_team, favorite_team]):
        return {"error": "Could not load team information"}
    
    # Guardar estado original
    original_status = match.status
    original_minute = match.current_minute
    original_home_score = match.home_score
    original_away_score = match.away_score
    original_notification_sent = match.notification_sent
    
    # Simular estado en vivo
    match.status = "LIVE"
    match.current_minute = current_minute
    match.home_score = home_score
    match.away_score = away_score
    
    # Verificar condiciones
    in_window = match.is_in_monitoring_window
    is_losing = match.is_favorite_losing
    
    result = {
        "simulation": {
            "match": f"{home_team.name} vs {away_team.name}",
            "favorite": favorite_team.name,
            "favorite_odds": match.favorite_odds,
            "score": f"{home_score} - {away_score}",
            "minute": current_minute,
            "status": "LIVE (simulado)"
        },
        "conditions": {
            "monitoring_window": f"{settings.MONITOR_MINUTE_START}-{settings.MONITOR_MINUTE_END}",
            "current_minute": current_minute,
            "in_window": in_window,
            "favorite_is_losing": is_losing,
            "should_alert": in_window and is_losing
        },
        "alert_sent": False,
        "message": ""
    }
    
    # Si se cumplen las condiciones, enviar alerta REAL
    if in_window and is_losing and not original_notification_sent:
        monitor = MonitorService()
        success = await monitor._send_alert(db, match)
        
        if success:
            result["alert_sent"] = True
            result["message"] = "✅ ¡ALERTA ENVIADA CON ÉXITO! Revisa tu Telegram."
            # NO marcar como notificado para poder probar de nuevo
            match.notification_sent = False
        else:
            result["message"] = "❌ Error al enviar alerta"
    elif not in_window:
        result["message"] = f"⏱️ Minuto {current_minute} fuera de ventana ({settings.MONITOR_MINUTE_START}-{settings.MONITOR_MINUTE_END})"
    elif not is_losing:
        result["message"] = f"✅ {favorite_team.name} (favorito) NO está perdiendo"
    else:
        result["message"] = "ℹ️ Condiciones no cumplidas"
    
    # Restaurar estado original
    match.status = original_status
    match.current_minute = original_minute
    match.home_score = original_home_score
    match.away_score = original_away_score
    match.notification_sent = original_notification_sent
    
    db.commit()
    
    return result


@router.post("/test-alert")
async def test_alert_simulation(
    home_team: str = "Test Home Team",
    away_team: str = "Test Away Team", 
    home_score: int = 0,
    away_score: int = 2,
    current_minute: int = 60,
    favorite_is_home: bool = True,
    favorite_odds: float = 1.30,
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """
    Simular un partido en vivo para probar el sistema de alertas.
    
    Parámetros:
    - home_team: Nombre del equipo local
    - away_team: Nombre del equipo visitante
    - home_score: Goles del local
    - away_score: Goles del visitante
    - current_minute: Minuto actual del partido
    - favorite_is_home: True si el favorito es el local
    - favorite_odds: Cuota del favorito
    """
    from app.models import League, Team
    
    try:
        # 0. Limpiar datos de prueba anteriores
        db.query(Match).filter(Match.api_id >= 999990).delete()
        db.query(Team).filter(Team.api_id >= 999990).delete()
        db.query(League).filter(League.api_id >= 999990).delete()
        db.commit()
        
        # 1. Crear liga de prueba
        test_league = League(
            api_id=999999,
            name="TEST_LEAGUE",
            country="Test",
            season=2025
        )
        db.add(test_league)
        db.flush()
        
        # 2. Crear equipos de prueba
        home = Team(api_id=999998, name=home_team)
        db.add(home)
        db.flush()
        
        away = Team(api_id=999997, name=away_team)
        db.add(away)
        db.flush()
        
        # 3. Crear partido de prueba
        from datetime import datetime, timezone
        
        test_match = Match(
            api_id=999996,
            league_id=test_league.id,
            home_team_id=home.id,
            away_team_id=away.id,
            match_date=datetime.now(timezone.utc),
            status="LIVE",
            home_score=home_score,
            away_score=away_score,
            current_minute=current_minute,
            home_odds=2.0 if not favorite_is_home else favorite_odds,
            away_odds=2.0 if favorite_is_home else favorite_odds,
            draw_odds=3.0,
            favorite_team_id=home.id if favorite_is_home else away.id,
            favorite_odds=favorite_odds,
            should_monitor=True,
            notification_sent=False
        )
        db.add(test_match)
        db.commit()
        
        # 4. Verificar condiciones
        is_in_window = test_match.is_in_monitoring_window
        is_losing = test_match.is_favorite_losing
        
        result = {
            "test_match_created": True,
            "match_id": test_match.id,
            "scenario": {
                "home_team": home_team,
                "away_team": away_team,
                "score": f"{home_score} - {away_score}",
                "minute": current_minute,
                "favorite": home_team if favorite_is_home else away_team,
                "favorite_odds": favorite_odds
            },
            "conditions": {
                "in_monitoring_window": is_in_window,
                "window_range": f"{settings.MONITOR_MINUTE_START}-{settings.MONITOR_MINUTE_END}",
                "favorite_is_losing": is_losing,
                "both_conditions_met": is_in_window and is_losing
            },
            "alert_sent": False,
            "message": ""
        }
        
        # 5. Ejecutar monitoreo
        if is_in_window and is_losing:
            monitor = MonitorService()
            alerts = await monitor.monitor_live_matches(db)
            
            # Refrescar para ver si se marcó como notificado
            db.refresh(test_match)
            
            result["alert_sent"] = test_match.notification_sent
            result["message"] = f"✅ Se enviaron {alerts} alerta(s)" if alerts > 0 else "❌ No se envió alerta"
        else:
            reasons = []
            if not is_in_window:
                reasons.append(f"Minuto {current_minute} está FUERA de ventana {settings.MONITOR_MINUTE_START}-{settings.MONITOR_MINUTE_END}")
            if not is_losing:
                reasons.append("El favorito NO está perdiendo")
            
            result["message"] = f"⚠️ Condiciones no cumplidas: {', '.join(reasons)}"
        
        return result
        
    except Exception as e:
        db.rollback()
        return {
            "error": str(e),
            "message": "❌ Error al crear partido de prueba"
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


@router.get("/match-details/{match_id}")
async def get_match_details(match_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get detailed information about a specific match for debugging."""
    match = db.query(Match).filter(Match.id == match_id).first()
    
    if not match:
        return {"error": "Match not found"}
    
    home_team = db.query(Team).filter(Team.id == match.home_team_id).first()
    away_team = db.query(Team).filter(Team.id == match.away_team_id).first()
    favorite_team = db.query(Team).filter(Team.id == match.favorite_team_id).first() if match.favorite_team_id else None
    league = db.query(League).filter(League.id == match.league_id).first()
    
    return {
        "id": match.id,
        "api_id": match.api_id,
        "is_real_api_football_id": match.api_id < 1000000,
        "home_team": {
            "id": home_team.id if home_team else None,
            "name": home_team.name if home_team else None,
            "api_id": home_team.api_id if home_team else None
        },
        "away_team": {
            "id": away_team.id if away_team else None,
            "name": away_team.name if away_team else None,
            "api_id": away_team.api_id if away_team else None
        },
        "favorite_team": {
            "name": favorite_team.name if favorite_team else None,
            "id": match.favorite_team_id
        },
        "league": {
            "name": league.name if league else None,
            "api_id": league.api_id if league else None
        },
        "match_date": match.match_date.isoformat() if match.match_date else None,
        "status": match.status,
        "scores": {
            "home": match.home_score,
            "away": match.away_score
        },
        "current_minute": match.current_minute,
        "odds": {
            "home": match.home_odds,
            "draw": match.draw_odds,
            "away": match.away_odds,
            "favorite": match.favorite_odds
        },
        "monitoring": {
            "should_monitor": match.should_monitor,
            "notification_sent": match.notification_sent,
            "notified_at": match.notified_at.isoformat() if match.notified_at else None,
            "monitoring_window": f"{settings.MONITOR_MINUTE_START}-{settings.MONITOR_MINUTE_END}"
        },
        "timestamps": {
            "created_at": match.created_at.isoformat() if match.created_at else None,
            "updated_at": match.updated_at.isoformat() if match.updated_at else None
        }
    }


@router.get("/api-quotas")
async def check_api_quotas() -> dict[str, Any]:
    """Check current API quotas for API-Football and The Odds API."""
    import httpx
    
    quotas = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "api_football": {},
        "the_odds_api": {}
    }
    
    # 1. Check API-Football quota
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                "https://v3.football.api-sports.io/status",
                headers={"x-apisports-key": settings.API_FOOTBALL_KEY}
            )
            data = response.json()
            
            if data.get("response"):
                account = data["response"]["account"]
                requests_data = data["response"]["requests"]
                
                used = requests_data.get("current", 0)
                limit = requests_data.get("limit_day", 100)
                available = limit - used
                
                quotas["api_football"] = {
                    "status": "✅ Conectado",
                    "plan": account.get("plan", "Free"),
                    "email": account.get("email", "N/A"),
                    "requests_used": used,
                    "requests_limit": limit,
                    "requests_available": available,
                    "percentage_used": round((used / limit * 100), 1) if limit > 0 else 0,
                    "quota_status": "❌ AGOTADA" if used >= limit else f"✅ Disponible ({available} restantes)",
                    "resets_at": "00:00 UTC (7 PM Colombia)"
                }
            else:
                quotas["api_football"] = {
                    "status": "❌ Error",
                    "error": data.get("errors", "Unknown error")
                }
    except Exception as e:
        quotas["api_football"] = {
            "status": "❌ Error de conexión",
            "error": str(e)
        }
    
    # 2. Check The Odds API (intentar una consulta para ver si responde)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Intentar obtener deportes disponibles (endpoint ligero)
            response = await client.get(
                "https://api.the-odds-api.com/v4/sports",
                params={"apiKey": settings.THE_ODDS_API_KEY}
            )
            
            # The Odds API devuelve las requests restantes en los headers
            remaining = response.headers.get("x-requests-remaining", "Unknown")
            used = response.headers.get("x-requests-used", "Unknown")
            
            if response.status_code == 200:
                quotas["the_odds_api"] = {
                    "status": "✅ Conectado",
                    "plan": "Free (500 requests/mes)",
                    "requests_used": used,
                    "requests_remaining": remaining,
                    "quota_status": "❌ AGOTADA" if remaining == "0" else f"✅ Disponible ({remaining} restantes)",
                    "resets_at": "1 de cada mes"
                }
            elif response.status_code == 401:
                quotas["the_odds_api"] = {
                    "status": "❌ API Key inválida",
                    "error": "La API Key no es válida o ha expirado"
                }
            elif response.status_code == 429:
                quotas["the_odds_api"] = {
                    "status": "❌ CUOTA AGOTADA",
                    "error": "Has alcanzado el límite mensual de 500 requests",
                    "resets_at": "1 de cada mes"
                }
            else:
                quotas["the_odds_api"] = {
                    "status": f"❌ Error HTTP {response.status_code}",
                    "error": response.text[:200]
                }
    except Exception as e:
        quotas["the_odds_api"] = {
            "status": "❌ Error de conexión",
            "error": str(e)
        }
    
    # 3. Calcular tiempo hasta próximo reset
    now_utc = datetime.now(timezone.utc)
    
    # API-Football se resetea a las 00:00 UTC
    next_reset_api_football = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    if now_utc.hour >= 0:
        next_reset_api_football += timedelta(days=1)
    hours_until_api_football = (next_reset_api_football - now_utc).total_seconds() / 3600
    
    # The Odds API se resetea el día 1 de cada mes
    if now_utc.day == 1:
        next_reset_the_odds = now_utc.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now_utc.month == 12:
            next_reset_the_odds = next_reset_the_odds.replace(year=now_utc.year + 1, month=1)
        else:
            next_reset_the_odds = next_reset_the_odds.replace(month=now_utc.month + 1)
    else:
        next_reset_the_odds = now_utc.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now_utc.month == 12:
            next_reset_the_odds = next_reset_the_odds.replace(year=now_utc.year + 1, month=1)
        else:
            next_reset_the_odds = next_reset_the_odds.replace(month=now_utc.month + 1)
    
    days_until_the_odds = (next_reset_the_odds - now_utc).days
    
    quotas["next_resets"] = {
        "api_football": {
            "time": next_reset_api_football.isoformat(),
            "hours_until": round(hours_until_api_football, 1),
            "local_time": f"{int(hours_until_api_football) // 1} horas"
        },
        "the_odds_api": {
            "date": next_reset_the_odds.date().isoformat(),
            "days_until": days_until_the_odds
        }
    }
    
    return quotas


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


@router.get("/debug-fetch-detailed")
async def debug_fetch_detailed() -> dict[str, Any]:
    """Simulate fetch_and_store_fixtures with detailed logging."""
    from app.services.the_odds_api_service import TheOddsAPIService
    from datetime import datetime, timezone, timedelta
    
    odds_service = TheOddsAPIService()
    now_utc = datetime.now(timezone.utc)
    window_end = now_utc + timedelta(hours=20)
    
    result = {
        "current_time_utc": now_utc.isoformat(),
        "window_end_utc": window_end.isoformat(),
        "steps": []
    }
    
    # Step 1: Fetch from The Odds API
    result["steps"].append({"step": 1, "action": "Fetching from The Odds API..."})
    all_odds = await odds_service.get_odds_for_soccer()
    result["total_fetched"] = len(all_odds)
    
    # Step 2: Filter by window
    today_matches = []
    for odds_match in all_odds:
        commence_time_str = odds_match.get("commence_time")
        if commence_time_str:
            match_datetime_utc = datetime.fromisoformat(commence_time_str.replace('Z', '+00:00'))
            if now_utc <= match_datetime_utc <= window_end:
                today_matches.append(odds_match)
    
    result["in_window"] = len(today_matches)
    result["steps"].append({"step": 2, "action": f"Filtered to {len(today_matches)} matches in window"})
    
    # Step 3: Parse odds for each
    parsed_results = []
    for match in today_matches[:5]:  # Only first 5 for brevity
        parsed_odds = odds_service.parse_odds(match)
        parsed_results.append({
            "home": match.get("home_team"),
            "away": match.get("away_team"),
            "league": match.get("league_key"),
            "parsed_odds": parsed_odds,
            "should_monitor": parsed_odds and parsed_odds.get("favorite_odds", 999) < float(settings.FAVORITE_ODDS_THRESHOLD) if parsed_odds else False
        })
    
    result["sample_parsed"] = parsed_results
    result["steps"].append({"step": 3, "action": f"Parsed {len(parsed_results)} sample matches"})
    
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
            matches = await odds_service.get_odds_for_soccer(leagues=[league_key.strip()], regions="eu", markets="h2h")
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

