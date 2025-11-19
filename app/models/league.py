"""League model."""

from sqlalchemy import Column, Integer, String

from app.database import Base


class League(Base):
    """League database model."""

    __tablename__ = "leagues"

    id = Column(Integer, primary_key=True, index=True)
    api_id = Column(Integer, unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    country = Column(String(100), nullable=False)
    logo = Column(String(500), nullable=True)
    season = Column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<League {self.name} ({self.country})>"

