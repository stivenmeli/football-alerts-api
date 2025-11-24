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
        self.the_odds_leagues_list = settings.the_odds_leagues_list

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

    async def get_live_scores(self, sport_key: str = "soccer_spain_la_liga") -> list[dict[str, Any]]:
        """
        Get live scores for a specific sport/league.
        
        Args:
            sport_key: League key (e.g., "soccer_spain_la_liga")
            
        Returns:
            List of live matches with scores
        """
        try:
            # The Odds API provides scores in the same endpoint as odds
            params = {
                "regions": "eu",
                "markets": "h2h",
                "oddsFormat": "decimal",
            }
            
            matches = await self._make_request(f"sports/{sport_key}/scores", params)
            return matches if isinstance(matches, list) else []
            
        except Exception as e:
            print(f"⚠️  Error fetching live scores for {sport_key}: {e}")
            return []
    
    async def get_all_live_scores(self) -> list[dict[str, Any]]:
        """
        Get live scores from all configured leagues.
        
        Returns:
            List of all live matches with scores
        """
        all_scores = []
        leagues = self.the_odds_leagues_list
        
        for league_key in leagues:
            try:
                scores = await self.get_live_scores(league_key)
                if scores:
                    for score in scores:
                        score["league_key"] = league_key
                    all_scores.extend(scores)
            except Exception as e:
                print(f"⚠️  Error fetching scores from {league_key}: {e}")
                continue
        
        return all_scores
    
    def parse_live_score(self, score_data: dict[str, Any]) -> dict[str, Any] | None:
        """
        Parse live score data from The Odds API.
        
        Args:
            score_data: Raw score data
            
        Returns:
            Parsed match data with scores and status
        """
        try:
            # Check if match has started
            if not score_data.get("completed") and score_data.get("scores"):
                scores = score_data.get("scores", [])
                
                # Extract home and away scores
                home_score = None
                away_score = None
                
                for score in scores:
                    if score.get("name") == score_data.get("home_team"):
                        home_score = score.get("score")
                    elif score.get("name") == score_data.get("away_team"):
                        away_score = score.get("score")
                
                return {
                    "home_team": score_data.get("home_team"),
                    "away_team": score_data.get("away_team"),
                    "home_score": int(home_score) if home_score else 0,
                    "away_score": int(away_score) if away_score else 0,
                    "completed": score_data.get("completed", False),
                    "commence_time": score_data.get("commence_time"),
                    "league_key": score_data.get("league_key"),
                }
            
            return None
            
        except Exception as e:
            print(f"⚠️  Error parsing live score: {e}")
            return None
    
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
        Find the BEST (lowest) odds across all bookmakers.
        
        Args:
            odds_data: Raw odds data
            
        Returns:
            Parsed odds with home, away, draw (using best odds available)
        """
        try:
            if not odds_data.get("bookmakers"):
                return None
            
            # Initialize with high values
            home_odds = float('inf')
            away_odds = float('inf')
            draw_odds = float('inf')
            best_bookmaker = None
            
            # Iterate through ALL bookmakers to find the best (lowest) odds
            for bookmaker in odds_data["bookmakers"]:
                markets = bookmaker.get("markets", [])
                
                # Find h2h market
                h2h_market = next((m for m in markets if m["key"] == "h2h"), None)
                if not h2h_market:
                    continue
                
                outcomes = h2h_market.get("outcomes", [])
                
                # Extract odds from this bookmaker
                curr_home = next((o["price"] for o in outcomes if o["name"] == odds_data["home_team"]), None)
                curr_away = next((o["price"] for o in outcomes if o["name"] == odds_data["away_team"]), None)
                curr_draw = next((o["price"] for o in outcomes if o["name"] == "Draw"), None)
                
                # Update if this bookmaker has better (lower) odds
                if curr_home and curr_home < home_odds:
                    home_odds = curr_home
                    best_bookmaker = bookmaker.get("title", "Unknown")
                if curr_away and curr_away < away_odds:
                    away_odds = curr_away
                if curr_draw and curr_draw < draw_odds:
                    draw_odds = curr_draw
            
            # Check if we found valid odds
            if home_odds == float('inf') or away_odds == float('inf'):
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
                "draw_odds": draw_odds if draw_odds != float('inf') else None,
                "favorite_team": favorite_team,
                "favorite_odds": favorite_odds,
                "bookmaker": best_bookmaker,
            }
            
        except Exception as e:
            print(f"⚠️  Error parsing odds: {e}")
            return None

