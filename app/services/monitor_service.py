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
        Fetch fixtures WITH ODDS from The Odds API in the next 20 hours.
        Only stores matches starting in next 20 hours (no pre-match alerts, only for live monitoring).
        
        Args:
            db: Database session
            
        Returns:
            Number of fixtures processed
        """
        count = 0

        try:
            # Limpiar partidos antiguos
            await self._cleanup_old_matches(db)
            
            # Obtener partidos CON cuotas desde The Odds API
            print(f"🔄 Fetching matches with odds from The Odds API...")
            all_odds = await self.odds_api.get_odds_for_soccer()
            
            print(f"✅ Found {len(all_odds)} matches with odds")
            
            # Filter only matches starting in the next 20 hours
            from datetime import timedelta, timezone
            
            # Get current time in UTC
            now_utc = datetime.now(timezone.utc)
            # Define window: next 20 hours
            window_end = now_utc + timedelta(hours=20)
            
            today_matches = []
            
            for odds_match in all_odds:
                try:
                    commence_time_str = odds_match.get("commence_time")
                    if commence_time_str:
                        # Parse UTC time
                        match_datetime_utc = datetime.fromisoformat(commence_time_str.replace('Z', '+00:00'))
                        
                        # Check if match starts within next 20 hours
                        if now_utc <= match_datetime_utc <= window_end:
                            today_matches.append(odds_match)
                            hours_until = (match_datetime_utc - now_utc).total_seconds() / 3600
                            print(f"  ✅ Match in next 20h: {odds_match.get('home_team')} vs {odds_match.get('away_team')} (in {hours_until:.1f}h)")
                        else:
                            hours_until = (match_datetime_utc - now_utc).total_seconds() / 3600
                            print(f"  ⏭️  Match outside window: {odds_match.get('home_team')} (in {hours_until:.1f}h)")
                except Exception as e:
                    print(f"  ⚠️  Error parsing date: {e}")
                    continue
            
            print(f"✅ Found {len(today_matches)} matches in next 20 hours")
            
            # Pre-fetch all API-Football fixtures for today and tomorrow to get real IDs
            # If API-Football is out of quota, we'll still store matches and try to get IDs during monitoring
            api_football_fixtures = {}
            try:
                # Fetch today's and tomorrow's fixtures to cover the 20-hour window
                today_str = now_utc.strftime("%Y-%m-%d")
                tomorrow_str = (now_utc + timedelta(days=1)).strftime("%Y-%m-%d")
                
                print(f"🔄 Fetching API-Football fixtures for {today_str} and {tomorrow_str} to get real IDs...")
                
                # Fetch both days
                for date_str in [today_str, tomorrow_str]:
                    try:
                        api_fixtures_list = await self.api_football.get_fixtures_by_date(date_str, league_id=None)
                        
                        # Index by team names for quick lookup
                        for fixture in api_fixtures_list:
                            try:
                                parsed = self.api_football.parse_fixture(fixture)
                                key = f"{parsed['home_team']['name'].lower()}_{parsed['away_team']['name'].lower()}"
                                api_football_fixtures[key] = parsed["api_id"]
                            except:
                                continue
                    except Exception as e:
                        print(f"⚠️  Error fetching {date_str}: {e}")
                        
                print(f"✅ Indexed {len(api_football_fixtures)} API-Football fixtures")
            except Exception as e:
                print(f"⚠️  Could not fetch API-Football fixtures (may be out of quota): {e}")
                print(f"⚠️  Will store matches anyway and try to get IDs during monitoring")
            
            for odds_match in today_matches:
                try:
                    # Store fixture from The Odds API data (NO pre-match alerts)
                    success = await self._store_fixture_from_odds(db, odds_match, api_football_fixtures, send_alert=False)
                    if success:
                        count += 1
                            
                except Exception as e:
                    print(f"⚠️  Error processing odds match: {e}")
                    continue
            
            print(f"✅ Stored {count} fixtures with odds (next 20 hours)")
            
        except Exception as e:
            print(f"❌ Error fetching fixtures: {e}")

        db.commit()
        return count

    async def _store_fixture_from_odds(self, db: Session, odds_match: dict[str, Any], api_football_fixtures: dict[str, int], send_alert: bool = False) -> bool:
        """
        Store fixture from The Odds API data.
        
        Args:
            db: Database session
            odds_match: Match data from The Odds API with odds
            api_football_fixtures: Dict mapping team names to API-Football IDs
            send_alert: Whether to send pre-match alert (default: False)
            
        Returns:
            True if stored successfully
        """
        try:
            home_team_name = odds_match.get("home_team", "").strip()
            away_team_name = odds_match.get("away_team", "").strip()
            league_key = odds_match.get("league_key", "unknown")
            commence_time = odds_match.get("commence_time")
            
            # Parse odds
            parsed_odds = self.odds_api.parse_odds(odds_match)
            if not parsed_odds:
                return False
            
            # Get or create league (using league_key as identifier)
            league = db.query(League).filter(League.name == league_key).first()
            if not league:
                league = League(
                    api_id=hash(league_key) % 1000000,  # Generate pseudo ID
                    name=league_key,
                    country="Unknown",
                    season=datetime.now().year,
                )
                db.add(league)
                db.flush()
            
            # Get or create home team
            home_team = db.query(Team).filter(Team.name == home_team_name).first()
            if not home_team:
                home_team = Team(
                    api_id=hash(home_team_name) % 1000000,
                    name=home_team_name,
                )
                db.add(home_team)
                db.flush()
            
            # Get or create away team
            away_team = db.query(Team).filter(Team.name == away_team_name).first()
            if not away_team:
                away_team = Team(
                    api_id=hash(away_team_name) % 1000000,
                    name=away_team_name,
                )
                db.add(away_team)
                db.flush()
            
            # Parse match date
            match_date_obj = datetime.fromisoformat(commence_time.replace('Z', '+00:00')).replace(tzinfo=None)
            
            # Try to find real API-Football ID from pre-loaded fixtures
            real_api_id = None
            lookup_key = f"{home_team_name.lower()}_{away_team_name.lower()}"
            
            # Try exact match first
            if lookup_key in api_football_fixtures:
                real_api_id = api_football_fixtures[lookup_key]
                print(f"  ✅ Found API-Football ID: {real_api_id}")
            else:
                # Try fuzzy match
                for key, api_id in api_football_fixtures.items():
                    if home_team_name.lower() in key and away_team_name.lower() in key:
                        real_api_id = api_id
                        print(f"  ✅ Found API-Football ID (fuzzy): {real_api_id}")
                        break
                        
            if not real_api_id:
                print(f"  ⚠️  No API-Football ID found for {home_team_name} vs {away_team_name}")
            
            # Check if match already exists
            match = db.query(Match).filter(
                Match.home_team_id == home_team.id,
                Match.away_team_id == away_team.id,
                Match.match_date >= match_date_obj.replace(hour=0, minute=0),
                Match.match_date < match_date_obj.replace(hour=23, minute=59),
            ).first()
            
            if not match:
                # Determine favorite
                favorite_team_id = home_team.id if parsed_odds["favorite_team"] == "home" else away_team.id
                should_monitor = parsed_odds["favorite_odds"] < settings.FAVORITE_ODDS_THRESHOLD
                
                # Use real API-Football ID if found, otherwise use hash
                api_id = real_api_id if real_api_id else hash(f"{home_team_name}{away_team_name}{commence_time}") % 1000000
                
                match = Match(
                    api_id=api_id,
                    league_id=league.id,
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    match_date=match_date_obj,
                    status="NS",  # Not Started
                    home_odds=parsed_odds.get("home_odds"),
                    draw_odds=parsed_odds.get("draw_odds"),
                    away_odds=parsed_odds.get("away_odds"),
                    favorite_team_id=favorite_team_id,
                    favorite_odds=parsed_odds.get("favorite_odds"),
                    should_monitor=should_monitor,
                )
                db.add(match)
                db.flush()
                
                # Send alert if odds < threshold (only if send_alert=True)
                if send_alert and should_monitor and not match.notification_sent:
                    await self._send_low_odds_alert(db, match, home_team, away_team)
                
                print(f"✅ Stored: {home_team_name} vs {away_team_name} (odds: {parsed_odds['favorite_odds']:.2f})")
                return True
            else:
                # Update existing match odds
                match.home_odds = parsed_odds.get("home_odds")
                match.draw_odds = parsed_odds.get("draw_odds")
                match.away_odds = parsed_odds.get("away_odds")
                match.favorite_odds = parsed_odds.get("favorite_odds")
                return True
                
        except Exception as e:
            print(f"⚠️  Error storing fixture from odds: {e}")
            return False

    async def _store_fixture(self, db: Session, parsed_data: dict[str, Any]) -> None:
        """Store or update fixture in database (from API-Football)."""
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
                # Mark all matches for monitoring (free version: monitor local team)
                should_monitor=True,
                favorite_team_id=home_team.id,  # Home team is considered "favorite"
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
                    home_team_name = odds_match.get("home_team", "").strip()
                    away_team_name = odds_match.get("away_team", "").strip()
                    
                    # Normalize team names for better matching
                    # Remove common suffixes like "FC", "F.C.", "United", etc.
                    home_norm = home_team_name.replace(" FC", "").replace(" F.C.", "").strip()
                    away_norm = away_team_name.replace(" FC", "").replace(" F.C.", "").strip()
                    
                    # Try exact match first, then partial match
                    home_team = (
                        db.query(Team).filter(Team.name == home_team_name).first() or
                        db.query(Team).filter(Team.name == home_norm).first() or
                        db.query(Team).filter(Team.name.ilike(f"%{home_norm}%")).first()
                    )
                    away_team = (
                        db.query(Team).filter(Team.name == away_team_name).first() or
                        db.query(Team).filter(Team.name == away_norm).first() or
                        db.query(Team).filter(Team.name.ilike(f"%{away_norm}%")).first()
                    )
                    
                    if not home_team or not away_team:
                        print(f"⚠️  Could not match teams: {home_team_name} vs {away_team_name}")
                        continue
                    
                    print(f"✅ Matched: {home_team.name} vs {away_team.name}")
                    
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
        Updates status of all matches marked for monitoring, then checks conditions.
        
        Args:
            db: Session
            
        Returns:
            Number of alerts sent
        """
        # Get ALL matches that should be monitored and haven't been notified yet
        # Include NS (not started) to update their status
        matches = db.query(Match).filter(
            Match.should_monitor == True,  # noqa: E712
            Match.notification_sent == False,  # noqa: E712
        ).all()

        alerts_sent = 0

        for match in matches:
            try:
                # Try to update match status from API-Football
                # First, try by searching with team names since we may not have correct api_id
                home_team = db.query(Team).filter(Team.id == match.home_team_id).first()
                away_team = db.query(Team).filter(Team.id == match.away_team_id).first()
                
                if not home_team or not away_team:
                    continue
                
                # Skip if we don't have a valid api_id from API-Football
                # Hash-generated IDs are typically > 500000
                if match.api_id > 500000:  # Likely hash-generated ID, not real API-Football ID
                    print(f"⚠️  Skipping {home_team.name} vs {away_team.name} - no API-Football ID (ID: {match.api_id})")
                    continue
                
                # Fetch live data from API-Football
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
                
                print(f"📊 Updated: {home_team.name} vs {away_team.name} | Status: {match.status} | Min: {match.current_minute} | Score: {match.home_score}-{match.away_score}")

                # Check if match is live (1H or 2H) and conditions are met
                if match.status in ["1H", "2H"] and match.is_in_monitoring_window and match.is_favorite_losing:
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
        """Send Telegram alert for a match (favorite losing in critical minutes 52-65)."""
        try:
            # Get team names
            home_team = db.query(Team).filter(Team.id == match.home_team_id).first()
            away_team = db.query(Team).filter(Team.id == match.away_team_id).first()
            league = db.query(League).filter(League.id == match.league_id).first()
            favorite_team = db.query(Team).filter(Team.id == match.favorite_team_id).first()

            if not all([home_team, away_team, league, favorite_team]):
                return False

            # Send Telegram message for favorite losing
            message = (
                f"🚨 ALERTA: Favorito Perdiendo (minutos 52-65)\n\n"
                f"⚽ {home_team.name} vs {away_team.name}\n"
                f"🏆 {league.name}\n\n"
                f"🎯 Favorito: {favorite_team.name}\n"
                f"💰 Cuota pre-partido: {match.favorite_odds:.2f}\n"
                f"⏱️ Minuto: {match.current_minute or 0}'\n"
                f"⚽ Resultado: {match.home_score or 0} - {match.away_score or 0}\n\n"
                f"📊 El favorito está perdiendo en momento crítico!"
            )
            
            success = await self.telegram.send_message(message)

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
        Delete matches from previous days (keeps today + next 3 days).
        
        Args:
            db: Database session
            
        Returns:
            Number of matches deleted
        """
        try:
            # Obtener el inicio del día de hoy
            today_start = datetime.combine(date.today(), datetime.min.time())
            
            # Borrar partidos de días anteriores a hoy
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

