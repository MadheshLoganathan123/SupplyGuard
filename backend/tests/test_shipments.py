"""
Basic shipment endpoint tests.
"""

import pytest


@pytest.mark.asyncio
async def test_list_shipments_empty(client):
    response = await client.get("/api/v1/shipments/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_and_get_shipment(client):
    payload = {
        "shipment_code": "#SS-TEST1",
        "origin": "Valley Farms Hub",
        "destination": "Midtown Pantry",
        "status": "IN-TRANSIT",
    }
    create_resp = await client.post("/api/v1/shipments/", json=payload)
    assert create_resp.status_code == 201

    data = create_resp.json()
    assert data["shipment_code"] == "#SS-TEST1"
    assert data["status"] == "IN-TRANSIT"

    get_resp = await client.get(f"/api/v1/shipments/{data['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == data["id"]


@pytest.mark.asyncio
async def test_duplicate_shipment_code(client):
    payload = {
        "shipment_code": "#SS-DUPE",
        "origin": "Farm A",
        "destination": "Hub B",
    }
    await client.post("/api/v1/shipments/", json=payload)
    resp = await client.post("/api/v1/shipments/", json=payload)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_update_shipment_status(client):
    create = await client.post(
        "/api/v1/shipments/",
        json={"shipment_code": "#SS-UPD1", "origin": "A", "destination": "B"},
    )
    sid = create.json()["id"]
    update = await client.patch(f"/api/v1/shipments/{sid}", json={"status": "REROUTED"})
    assert update.status_code == 200
    assert update.json()["status"] == "REROUTED"
