"""Service for The Odds API integration."""

import httpx
from typing import Any
from datetime import datetime

from app.core.config import settings


class TheOddsAPIService:
    """Client for The Odds API to fetch betting odds."""

    def __init__(self) -> None:
        """Initialize The Odds API service."""
        self.base_url = "https://api.the-odds-api.com/v4"
        self.api_key = settings.THE_ODDS_API_KEY
        self.timeout = 30.0

    async def _make_request(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Make HTTP request to The Odds API.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            API response as dict
        """
        url = f"{self.base_url}/{endpoint}"
        
        # Add API key to params
        if params is None:
            params = {}
        params["apiKey"] = self.api_key
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                print(f"❌ HTTP Error {e.response.status_code}: {e.response.text}")
                raise
            except Exception as e:
                print(f"❌ Error making request to The Odds API: {e}")
                raise

    async def get_available_sports(self) -> list[dict[str, Any]]:
        """
        Get list of available sports.
        
        Returns:
            List of sports with their keys
        """
        try:
            return await self._make_request("sports")
        except Exception as e:
            print(f"❌ Error fetching sports: {e}")
            return []

    async def get_odds_for_soccer(
        self, 
        leagues: list[str] | None = None,
        regions: str = "eu,uk",
        markets: str = "h2h",
        odds_format: str = "decimal"
    ) -> list[dict[str, Any]]:
        """
        Get odds for soccer matches across multiple leagues.
        
        Args:
            leagues: List of league keys (e.g., ["soccer_epl", "soccer_spain_la_liga"])
            regions: Regions to get odds from (eu, uk, us, au)
            markets: Markets to get (h2h = head to head, spreads, totals)
            odds_format: Format for odds (decimal, american)
            
        Returns:
            List of matches with odds
        """
        if leagues is None:
            leagues = settings.the_odds_leagues_list
        
        params = {
            "regions": regions,
            "markets": markets,
            "oddsFormat": odds_format,
        }
        
        all_odds = []
        
        try:
            # Fetch odds from each league
            for league_key in leagues:
                try:
                    print(f"🔍 Fetching odds for {league_key}...")
                    league_odds = await self._make_request(f"sports/{league_key}/odds", params)
                    
                    if isinstance(league_odds, list):
                        # Add league info to each match
                        for match in league_odds:
                            match["league_key"] = league_key
                        all_odds.extend(league_odds)
                        print(f"✅ Found {len(league_odds)} matches with odds in {league_key}")
                    
                except Exception as e:
                    print(f"⚠️  Error fetching odds for {league_key}: {e}")
                    continue
            
            print(f"✅ Total matches with odds: {len(all_odds)}")
            return all_odds
            
        except Exception as e:
            print(f"❌ Error fetching odds: {e}")
            return []

    async def test_connection(self) -> dict[str, Any]:
        """
        Test connection to The Odds API.
        
        Returns:
            Status of connection
        """
        try:
            sports = await self.get_available_sports()
            return {
                "status": "success" if sports else "no_data",
                "sports_count": len(sports),
                "message": f"Connected successfully. Found {len(sports)} sports available."
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def parse_odds(self, odds_data: dict[str, Any]) -> dict[str, Any] | None:
        """
        Parse odds data from The Odds API.
        
        Args:
            odds_data: Raw odds data
            
        Returns:
            Parsed odds with home, away, draw
        """
        try:
            if not odds_data.get("bookmakers"):
                return None
            
            # Get the first bookmaker's odds
            bookmaker = odds_data["bookmakers"][0]
            markets = bookmaker.get("markets", [])
            
            # Find h2h market
            h2h_market = next((m for m in markets if m["key"] == "h2h"), None)
            if not h2h_market:
                return None
            
            outcomes = h2h_market.get("outcomes", [])
            
            # Extract odds
            home_odds = next((o["price"] for o in outcomes if o["name"] == odds_data["home_team"]), None)
            away_odds = next((o["price"] for o in outcomes if o["name"] == odds_data["away_team"]), None)
            draw_odds = next((o["price"] for o in outcomes if o["name"] == "Draw"), None)
            
            if not home_odds or not away_odds:
                return None
            
            # Determine favorite (lowest odds)
            if home_odds < away_odds:
                favorite_team = "home"
                favorite_odds = home_odds
            else:
                favorite_team = "away"
                favorite_odds = away_odds
            
            return {
                "home_odds": home_odds,
                "away_odds": away_odds,
                "draw_odds": draw_odds,
                "favorite_team": favorite_team,
                "favorite_odds": favorite_odds,
                "bookmaker": bookmaker.get("title", "Unknown"),
            }
            
        except Exception as e:
            print(f"⚠️  Error parsing odds: {e}")
            return None

