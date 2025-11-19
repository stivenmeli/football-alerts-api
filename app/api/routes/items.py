"""Items routes - Example CRUD endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.schemas.item import Item, ItemCreate, ItemUpdate

router = APIRouter()

# Simulación de base de datos en memoria
fake_items_db: dict[int, Item] = {}
next_id = 1


@router.get("/", response_model=list[Item])
async def get_items() -> list[Item]:
    """Get all items."""
    return list(fake_items_db.values())


@router.get("/{item_id}", response_model=Item)
async def get_item(item_id: int) -> Item:
    """Get a specific item by ID."""
    if item_id not in fake_items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found",
        )
    return fake_items_db[item_id]


@router.post("/", response_model=Item, status_code=status.HTTP_201_CREATED)
async def create_item(item_data: ItemCreate) -> Item:
    """Create a new item."""
    global next_id
    new_item = Item(id=next_id, **item_data.model_dump())
    fake_items_db[next_id] = new_item
    next_id += 1
    return new_item


@router.put("/{item_id}", response_model=Item)
async def update_item(item_id: int, item_data: ItemUpdate) -> Item:
    """Update an existing item."""
    if item_id not in fake_items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found",
        )
    
    stored_item = fake_items_db[item_id]
    update_data = item_data.model_dump(exclude_unset=True)
    updated_item = stored_item.model_copy(update=update_data)
    fake_items_db[item_id] = updated_item
    return updated_item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int) -> None:
    """Delete an item."""
    if item_id not in fake_items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found",
        )
    del fake_items_db[item_id]

