"""Match monitoring service."""

from datetime import datetime, date
from sqlalchemy.orm import Session
from typing import Any

from app.core.config import settings
from app.database import SessionLocal
from app.models import Match, League, Team, Notification
from app.services.api_football import APIFootballService
from app.services.the_odds_api_service import TheOddsAPIService
from app.services.telegram_service import TelegramService


class MonitorService:
    """Service to monitor matches and send alerts."""

    def __init__(self) -> None:
        """Initialize monitoring service."""
        self.api_football = APIFootballService()
        self.odds_api = TheOddsAPIService()
        self.telegram = TelegramService()

    async def fetch_and_store_fixtures(self, db: Session) -> int:
        """
        Fetch fixtures for today and store them in database.
        
        Args:
            db: Database session
            
        Returns:
            Number of fixtures processed
        """
        today = date.today().strftime("%Y-%m-%d")
        count = 0

        try:
            # Limpiar partidos antiguos (más de 1 día finalizados)
            await self._cleanup_old_matches(db)
            
            # Obtener TODOS los fixtures disponibles del día (sin filtrar por liga)
            print(f"🔄 Fetching all fixtures for {today}...")
            all_fixtures = await self.api_football.get_fixtures_by_date(today, league_id=None)
            
            print(f"✅ Found {len(all_fixtures)} fixtures available")
            
            for fixture_data in all_fixtures:
                try:
                    parsed = self.api_football.parse_fixture(fixture_data)
                    
                    # Opcional: Filtrar solo las ligas que nos interesan
                    # league_id = parsed["league"]["api_id"]
                    # if league_id not in settings.leagues_to_monitor_list:
                    #     continue
                    
                    await self._store_fixture(db, parsed)
                    count += 1
                except Exception as e:
                    print(f"⚠️  Error processing fixture: {e}")
                    continue
            
            print(f"✅ Stored {count} fixtures in database")
            
        except Exception as e:
            print(f"❌ Error fetching fixtures: {e}")

        db.commit()
        return count

    async def _store_fixture(self, db: Session, parsed_data: dict[str, Any]) -> None:
        """Store or update fixture in database."""
        # Get or create league
        league_data = parsed_data["league"]
        league = db.query(League).filter(League.api_id == league_data["api_id"]).first()
        if not league:
            league = League(
                api_id=league_data["api_id"],
                name=league_data["name"],
                country=league_data["country"],
                logo=league_data.get("logo"),
                season=datetime.now().year,
            )
            db.add(league)
            db.flush()

        # Get or create home team
        home_team_data = parsed_data["home_team"]
        home_team = db.query(Team).filter(Team.api_id == home_team_data["api_id"]).first()
        if not home_team:
            home_team = Team(
                api_id=home_team_data["api_id"],
                name=home_team_data["name"],
                logo=home_team_data.get("logo"),
            )
            db.add(home_team)
            db.flush()

        # Get or create away team
        away_team_data = parsed_data["away_team"]
        away_team = db.query(Team).filter(Team.api_id == away_team_data["api_id"]).first()
        if not away_team:
            away_team = Team(
                api_id=away_team_data["api_id"],
                name=away_team_data["name"],
                logo=away_team_data.get("logo"),
            )
            db.add(away_team)
            db.flush()

        # Get or create match
        match = db.query(Match).filter(Match.api_id == parsed_data["api_id"]).first()
        
        # Convert match_date string to datetime object
        match_date_str = parsed_data["match_date"]
        if isinstance(match_date_str, str):
            # Remove timezone info if present for SQLite compatibility
            match_date_obj = datetime.fromisoformat(match_date_str.replace('+00:00', ''))
        else:
            match_date_obj = match_date_str
        
        if not match:
            match = Match(
                api_id=parsed_data["api_id"],
                league_id=league.id,
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                match_date=match_date_obj,
                status=parsed_data["status"],
            )
            db.add(match)
        else:
            # Update existing match
            match.status = parsed_data["status"]
            match.current_minute = parsed_data.get("current_minute")
            match.home_score = parsed_data.get("home_score")
            match.away_score = parsed_data.get("away_score")
            match.updated_at = datetime.utcnow()

    async def fetch_and_store_odds(self, db: Session) -> int:
        """
        Fetch odds from The Odds API for today's matches and determine favorites.
        
        Args:
            db: Database session
            
        Returns:
            Number of matches processed
        """
        try:
            # Fetch odds from The Odds API for all configured leagues
            print("🔍 Fetching odds from The Odds API...")
            all_odds = await self.odds_api.get_odds_for_soccer()
            
            if not all_odds:
                print("⚠️  No odds found from The Odds API")
                return 0
            
            count = 0
            alerts_sent = 0
            
            # Process each match with odds
            for odds_match in all_odds:
                try:
                    home_team_name = odds_match.get("home_team", "")
                    away_team_name = odds_match.get("away_team", "")
                    
                    # Find matching fixture in our database by team names
                    # Note: This is a fuzzy match - might need adjustment
                    home_team = db.query(Team).filter(Team.name.ilike(f"%{home_team_name}%")).first()
                    away_team = db.query(Team).filter(Team.name.ilike(f"%{away_team_name}%")).first()
                    
                    if not home_team or not away_team:
                        continue
                    
                    # Find the match
                    match = db.query(Match).filter(
                        Match.home_team_id == home_team.id,
                        Match.away_team_id == away_team.id,
                        Match.status == "NS"
                    ).first()
                    
                    if not match:
                        continue
                    
                    # Parse odds
                    parsed_odds = self.odds_api.parse_odds(odds_match)
                    if not parsed_odds:
                        continue
                    
                    # Store odds
                    match.home_odds = parsed_odds.get("home_odds")
                    match.draw_odds = parsed_odds.get("draw_odds")
                    match.away_odds = parsed_odds.get("away_odds")
                    match.favorite_odds = parsed_odds.get("favorite_odds")
                    
                    # Determine favorite team ID
                    if parsed_odds["favorite_team"] == "home":
                        match.favorite_team_id = home_team.id
                    else:
                        match.favorite_team_id = away_team.id
                    
                    # Check if favorite odds < threshold and send alert
                    if match.favorite_odds and match.favorite_odds < settings.FAVORITE_ODDS_THRESHOLD:
                        match.should_monitor = True
                        print(f"🎯 Match marked for monitoring: {home_team.name} vs {away_team.name} (odds: {match.favorite_odds})")
                        
                        # Send Telegram alert for low odds
                        if not match.notification_sent:
                            success = await self._send_low_odds_alert(db, match, home_team, away_team)
                            if success:
                                alerts_sent += 1
                    
                    count += 1
                    
                except Exception as e:
                    print(f"⚠️  Error processing odds for {odds_match.get('home_team')} vs {odds_match.get('away_team')}: {e}")
                    continue
            
            db.commit()
            print(f"✅ Processed {count} matches with odds, sent {alerts_sent} alerts")
            return count
            
        except Exception as e:
            print(f"❌ Error fetching odds: {e}")
            db.rollback()
            return 0

    async def monitor_live_matches(self, db: Session) -> int:
        """
        Monitor live matches and send alerts when conditions are met.
        
        Args:
            db: Database session
            
        Returns:
            Number of alerts sent
        """
        # Get matches that should be monitored and haven't been notified yet
        matches = db.query(Match).filter(
            Match.should_monitor == True,  # noqa: E712
            Match.notification_sent == False,  # noqa: E712
            Match.status.in_(["1H", "2H"]),
        ).all()

        alerts_sent = 0

        for match in matches:
            try:
                # Fetch live data
                live_data = await self.api_football.get_fixture_by_id(match.api_id)
                if not live_data:
                    continue

                parsed = self.api_football.parse_fixture(live_data)
                
                # Update match data
                match.status = parsed["status"]
                match.current_minute = parsed.get("current_minute")
                match.home_score = parsed.get("home_score") or 0
                match.away_score = parsed.get("away_score") or 0
                match.updated_at = datetime.utcnow()

                # Check if conditions are met
                if match.is_in_monitoring_window and match.is_favorite_losing:
                    # Send alert
                    success = await self._send_alert(db, match)
                    if success:
                        match.notification_sent = True
                        match.notified_at = datetime.utcnow()
                        alerts_sent += 1
                        print(f"🚨 Alert sent for match {match.api_id}")

            except Exception as e:
                print(f"❌ Error monitoring match {match.api_id}: {e}")

        db.commit()
        return alerts_sent

    async def _send_alert(self, db: Session, match: Match) -> bool:
        """Send Telegram alert for a match."""
        try:
            # Get team names
            home_team = db.query(Team).filter(Team.id == match.home_team_id).first()
            away_team = db.query(Team).filter(Team.id == match.away_team_id).first()
            league = db.query(League).filter(League.id == match.league_id).first()
            favorite_team = db.query(Team).filter(Team.id == match.favorite_team_id).first()

            if not all([home_team, away_team, league, favorite_team]):
                return False

            # Send Telegram message
            success = await self.telegram.send_match_alert(
                home_team=home_team.name,
                away_team=away_team.name,
                league=league.name,
                current_minute=match.current_minute or 0,
                home_score=match.home_score or 0,
                away_score=match.away_score or 0,
                favorite_team=favorite_team.name,
                favorite_odds=match.favorite_odds or 0,
            )

            # Store notification record
            notification = Notification(
                match_id=match.id,
                message=f"Alert sent for {home_team.name} vs {away_team.name}",
                status="sent" if success else "failed",
            )
            db.add(notification)

            return success

        except Exception as e:
            print(f"❌ Error sending alert: {e}")
            return False

    async def _send_low_odds_alert(self, db: Session, match: Match, home_team: Team, away_team: Team) -> bool:
        """Send Telegram alert for low pre-match odds."""
        try:
            league = db.query(League).filter(League.id == match.league_id).first()
            favorite_team = db.query(Team).filter(Team.id == match.favorite_team_id).first()

            if not all([league, favorite_team]):
                return False

            # Format match date/time
            match_time = match.match_date.strftime("%H:%M") if match.match_date else "TBD"

            # Send Telegram message for low odds
            message = (
                f"🚨 ALERTA: Cuota Pre-Partido Baja\n\n"
                f"⚽ {home_team.name} vs {away_team.name}\n"
                f"🏆 {league.name}\n\n"
                f"🎯 Favorito: {favorite_team.name}\n"
                f"💰 Cuota: {match.favorite_odds:.2f}\n"
                f"⏰ Inicio: {match_time}\n"
            )
            
            success = await self.telegram.send_message(message)

            # Store notification record
            if success:
                match.notification_sent = True
                notification = Notification(
                    match_id=match.id,
                    message=f"Low odds alert: {home_team.name} vs {away_team.name} ({match.favorite_odds})",
                    status="sent",
                )
                db.add(notification)

            return success

        except Exception as e:
            print(f"❌ Error sending low odds alert: {e}")
            return False

    async def _cleanup_old_matches(self, db: Session) -> int:
        """
        Delete ALL matches from previous days (regardless of status).
        
        Args:
            db: Database session
            
        Returns:
            Number of matches deleted
        """
        try:
            # Obtener el inicio del día de hoy
            today_start = datetime.combine(date.today(), datetime.min.time())
            
            # Borrar TODOS los partidos de días anteriores
            # (incluye NS, FT, etc. - cualquier partido que no sea de hoy)
            deleted = db.query(Match).filter(
                Match.match_date < today_start
            ).delete(synchronize_session=False)
            
            if deleted > 0:
                print(f"🗑️  Deleted {deleted} old matches from previous days")
                db.commit()
            
            return deleted
        except Exception as e:
            print(f"⚠️  Error cleaning old matches: {e}")
            db.rollback()
            return 0

    def get_db(self) -> Session:
        """Get database session."""
        return SessionLocal()

