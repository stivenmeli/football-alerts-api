"""Telegram notification service."""

import httpx
from typing import Any

from app.core.config import settings


class TelegramService:
    """Service to send Telegram notifications."""

    def __init__(self) -> None:
        """Initialize Telegram service."""
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    async def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        Send a message via Telegram.
        
        Args:
            message: Message text to send
            parse_mode: Parse mode (HTML or Markdown)
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.bot_token or not self.chat_id:
            print("⚠️  Telegram not configured. Skipping notification.")
            return False

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": parse_mode,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"❌ Error sending Telegram message: {e}")
            return False

    async def send_match_alert(
        self,
        home_team: str,
        away_team: str,
        league: str,
        current_minute: int,
        home_score: int,
        away_score: int,
        favorite_team: str,
        favorite_odds: float,
    ) -> bool:
        """
        Send a formatted match alert.
        
        Args:
            home_team: Home team name
            away_team: Away team name
            league: League name
            current_minute: Current match minute
            home_score: Home team score
            away_score: Away team score
            favorite_team: Favorite team name
            favorite_odds: Pre-match odds of favorite
            
        Returns:
            True if sent successfully
        """
        message = f"""
🚨 <b>ALERTA DE VALOR</b> 🚨

⚽ <b>{home_team}</b> vs <b>{away_team}</b>
🕐 Minuto: <b>{current_minute}'</b>
📊 Score: <b>{home_score} - {away_score}</b>
😱 <b>{favorite_team}</b> está perdiendo!
📉 Cuota pre-partido: <b>{favorite_odds}</b>
🏆 Liga: {league}

#AlertaDeValor #{league.replace(' ', '')}
"""
        return await self.send_message(message.strip())

    async def test_connection(self) -> dict[str, Any]:
        """
        Test Telegram bot connection.
        
        Returns:
            Bot information or error
        """
        url = f"{self.base_url}/getMe"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"error": str(e)}

