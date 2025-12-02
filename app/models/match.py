"""Match model."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Match(Base):
    """Match database model."""

    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    api_id = Column(Integer, unique=True, index=True, nullable=False)
    
    # Relaciones
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    home_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    
    # Información del partido
    match_date = Column(DateTime, nullable=False)
    status = Column(String(50), nullable=False, default="NS")  # NS, 1H, HT, 2H, FT, etc
    current_minute = Column(Integer, nullable=True)
    
    # Scores
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    
    # Cuotas y favorito
    home_odds = Column(Float, nullable=True)
    draw_odds = Column(Float, nullable=True)
    away_odds = Column(Float, nullable=True)
    favorite_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    favorite_odds = Column(Float, nullable=True)
    
    # Control de monitoreo
    should_monitor = Column(Boolean, default=False, index=True)
    is_monitored = Column(Boolean, default=False)
    notification_sent = Column(Boolean, default=False)
    notified_at = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<Match {self.id}: {self.home_team_id} vs {self.away_team_id}>"
    
    @property
    def is_favorite_losing(self) -> bool:
        """Check if favorite team is losing."""
        if not self.favorite_team_id or self.home_score is None or self.away_score is None:
            return False
        
        if self.favorite_team_id == self.home_team_id:
            return self.home_score < self.away_score
        else:
            return self.away_score < self.home_score
    
    @property
    def is_in_monitoring_window(self) -> bool:
        """Check if match is in the monitoring window (configurable via settings)."""
        from app.core.config import settings
        
        if not self.current_minute:
            return False
        return settings.MONITOR_MINUTE_START <= self.current_minute <= settings.MONITOR_MINUTE_END

