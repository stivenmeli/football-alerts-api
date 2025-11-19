"""Team model."""

from sqlalchemy import Column, Integer, String

from app.database import Base


class Team(Base):
    """Team database model."""

    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    api_id = Column(Integer, unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    code = Column(String(10), nullable=True)
    logo = Column(String(500), nullable=True)
    country = Column(String(100), nullable=True)

    def __repr__(self) -> str:
        return f"<Team {self.name}>"

