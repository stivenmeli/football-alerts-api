"""Tests for items endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint() -> None:
    """Test root endpoint returns correct response."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "version" in data


def test_health_check() -> None:
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_get_items_empty() -> None:
    """Test getting items when database is empty."""
    response = client.get("/api/v1/items/")
    assert response.status_code == 200
    assert response.json() == []


def test_create_item() -> None:
    """Test creating a new item."""
    item_data = {
        "name": "Test Item",
        "description": "A test item",
        "price": 99.99,
        "is_active": True,
    }
    response = client.post("/api/v1/items/", json=item_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == item_data["name"]
    assert data["price"] == item_data["price"]
    assert "id" in data


def test_create_item_invalid_price() -> None:
    """Test creating item with invalid price fails."""
    item_data = {
        "name": "Test Item",
        "description": "A test item",
        "price": -10.0,  # Precio negativo no válido
        "is_active": True,
    }
    response = client.post("/api/v1/items/", json=item_data)
    assert response.status_code == 422  # Validation error


def test_get_item_not_found() -> None:
    """Test getting non-existent item returns 404."""
    response = client.get("/api/v1/items/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_full_item_lifecycle() -> None:
    """Test complete CRUD operations on an item."""
    # Create
    item_data = {
        "name": "Lifecycle Item",
        "description": "Testing full lifecycle",
        "price": 49.99,
        "is_active": True,
    }
    create_response = client.post("/api/v1/items/", json=item_data)
    assert create_response.status_code == 201
    created_item = create_response.json()
    item_id = created_item["id"]

    # Read
    get_response = client.get(f"/api/v1/items/{item_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == item_data["name"]

    # Update
    update_data = {"name": "Updated Item", "price": 59.99}
    update_response = client.put(f"/api/v1/items/{item_id}", json=update_data)
    assert update_response.status_code == 200
    updated_item = update_response.json()
    assert updated_item["name"] == "Updated Item"
    assert updated_item["price"] == 59.99
    assert updated_item["description"] == item_data["description"]  # Sin cambios

    # Delete
    delete_response = client.delete(f"/api/v1/items/{item_id}")
    assert delete_response.status_code == 204

    # Verify deletion
    get_deleted_response = client.get(f"/api/v1/items/{item_id}")
    assert get_deleted_response.status_code == 404


def test_update_nonexistent_item() -> None:
    """Test updating non-existent item returns 404."""
    update_data = {"name": "Updated"}
    response = client.put("/api/v1/items/999", json=update_data)
    assert response.status_code == 404


def test_delete_nonexistent_item() -> None:
    """Test deleting non-existent item returns 404."""
    response = client.delete("/api/v1/items/999")
    assert response.status_code == 404

