"""API-Football service for fetching match data."""

import httpx
from typing import Any
from datetime import datetime

from app.core.config import settings


class APIFootballService:
    """Service to interact with API-Football."""

    def __init__(self) -> None:
        """Initialize API-Football service."""
        self.base_url = settings.API_FOOTBALL_BASE_URL
        self.headers = {
            "x-apisports-key": settings.API_FOOTBALL_KEY,
        }

    async def get_fixtures_by_date(self, date: str, league_id: int | None = None) -> list[dict[str, Any]]:
        """
        Get fixtures for a specific date and optionally league.
        
        Args:
            date: Date in format YYYY-MM-DD
            league_id: League ID from API-Football (optional, gets all if None)
            
        Returns:
            List of fixtures
        """
        url = f"{self.base_url}/fixtures"
        params: dict[str, Any] = {"date": date}
        
        # Solo agregar league y season si se especifica
        if league_id:
            params["league"] = league_id
            params["season"] = datetime.now().year

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("response", [])

    async def get_live_fixtures(self) -> list[dict[str, Any]]:
        """
        Get all live fixtures.
        
        Returns:
            List of live fixtures
        """
        url = f"{self.base_url}/fixtures"
        params = {"live": "all"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("response", [])

    async def get_fixture_by_id(self, fixture_id: int) -> dict[str, Any] | None:
        """
        Get specific fixture by ID.
        
        Args:
            fixture_id: Fixture ID from API-Football
            
        Returns:
            Fixture data or None
        """
        url = f"{self.base_url}/fixtures"
        params = {"id": fixture_id}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            fixtures = data.get("response", [])
            return fixtures[0] if fixtures else None

    async def get_odds(self, fixture_id: int, bookmaker: int = 8) -> dict[str, Any] | None:
        """
        Get odds for a specific fixture.
        
        Args:
            fixture_id: Fixture ID from API-Football
            bookmaker: Bookmaker ID (default: 8 = Bet365)
            
        Returns:
            Odds data or None
        """
        url = f"{self.base_url}/odds"
        params = {
            "fixture": fixture_id,
            "bookmaker": bookmaker,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            odds_data = data.get("response", [])
            return odds_data[0] if odds_data else None

    def parse_fixture(self, fixture_data: dict[str, Any]) -> dict[str, Any]:
        """
        Parse fixture data from API response.
        
        Args:
            fixture_data: Raw fixture data from API
            
        Returns:
            Parsed fixture data
        """
        fixture = fixture_data.get("fixture", {})
        teams = fixture_data.get("teams", {})
        goals = fixture_data.get("goals", {})
        league = fixture_data.get("league", {})

        return {
            "api_id": fixture.get("id"),
            "match_date": fixture.get("date"),
            "status": fixture.get("status", {}).get("short", "NS"),
            "current_minute": fixture.get("status", {}).get("elapsed"),
            "home_team": {
                "api_id": teams.get("home", {}).get("id"),
                "name": teams.get("home", {}).get("name"),
                "logo": teams.get("home", {}).get("logo"),
            },
            "away_team": {
                "api_id": teams.get("away", {}).get("id"),
                "name": teams.get("away", {}).get("name"),
                "logo": teams.get("away", {}).get("logo"),
            },
            "home_score": goals.get("home"),
            "away_score": goals.get("away"),
            "league": {
                "api_id": league.get("id"),
                "name": league.get("name"),
                "country": league.get("country"),
                "logo": league.get("logo"),
            },
        }

    def parse_odds(self, odds_data: dict[str, Any]) -> dict[str, float] | None:
        """
        Parse odds data from API response.
        
        Args:
            odds_data: Raw odds data from API
            
        Returns:
            Dict with home, draw, away odds or None
        """
        bookmakers = odds_data.get("bookmakers", [])
        if not bookmakers:
            return None

        bets = bookmakers[0].get("bets", [])
        for bet in bets:
            if bet.get("name") == "Match Winner":
                values = bet.get("values", [])
                odds_dict = {}
                for value in values:
                    if value.get("value") == "Home":
                        odds_dict["home"] = float(value.get("odd", 0))
                    elif value.get("value") == "Draw":
                        odds_dict["draw"] = float(value.get("odd", 0))
                    elif value.get("value") == "Away":
                        odds_dict["away"] = float(value.get("odd", 0))
                return odds_dict

        return None

