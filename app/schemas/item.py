"""Item schemas for request/response validation."""

from pydantic import BaseModel, ConfigDict, Field


class ItemBase(BaseModel):
    """Base Item schema with common attributes."""

    name: str = Field(..., min_length=1, max_length=100, description="Item name")
    description: str | None = Field(None, max_length=500, description="Item description")
    price: float = Field(..., gt=0, description="Item price (must be positive)")
    is_active: bool = Field(default=True, description="Item availability status")


class ItemCreate(ItemBase):
    """Schema for creating a new item."""

    pass


class ItemUpdate(BaseModel):
    """Schema for updating an existing item (all fields optional)."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    price: float | None = Field(None, gt=0)
    is_active: bool | None = None


class Item(ItemBase):
    """Complete Item schema with ID."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Unique item identifier")

