"""Match monitoring service."""

from datetime import datetime, date
from sqlalchemy.orm import Session
from typing import Any

from app.core.config import settings
from app.database import SessionLocal
from app.models import Match, League, Team, Notification
from app.services.api_football import APIFootballService
from app.services.telegram_service import TelegramService


class MonitorService:
    """Service to monitor matches and send alerts."""

    def __init__(self) -> None:
        """Initialize monitoring service."""
        self.api_football = APIFootballService()
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
        Fetch odds for matches without odds and determine favorites.
        
        Args:
            db: Database session
            
        Returns:
            Number of matches processed
        """
        # Get matches without odds that haven't started yet
        matches = db.query(Match).filter(
            Match.home_odds.is_(None),
            Match.status == "NS",
        ).all()

        count = 0
        for match in matches:
            try:
                odds_data = await self.api_football.get_odds(match.api_id)
                if odds_data:
                    odds = self.api_football.parse_odds(odds_data)
                    if odds:
                        match.home_odds = odds.get("home")
                        match.draw_odds = odds.get("draw")
                        match.away_odds = odds.get("away")

                        # Determine favorite
                        if match.home_odds and match.away_odds:
                            if match.home_odds < match.away_odds:
                                match.favorite_team_id = match.home_team_id
                                match.favorite_odds = match.home_odds
                            else:
                                match.favorite_team_id = match.away_team_id
                                match.favorite_odds = match.away_odds

                            # Mark for monitoring if favorite odds < threshold
                            if match.favorite_odds < settings.FAVORITE_ODDS_THRESHOLD:
                                match.should_monitor = True
                                print(f"🎯 Match {match.api_id} marked for monitoring (odds: {match.favorite_odds})")

                        count += 1
            except Exception as e:
                print(f"❌ Error fetching odds for match {match.api_id}: {e}")

        db.commit()
        return count

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

    def get_db(self) -> Session:
        """Get database session."""
        return SessionLocal()

