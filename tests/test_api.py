from datetime import datetime, timedelta

from crud import ReadingCRUD, SensorCRUD


def post_reading(client, data, sensor_id="dht22_01", timestamp=None):
    payload = {"sensor_id": sensor_id, "type": "temperature_humidity", "data": data}
    if timestamp is not None:
        payload["timestamp"] = timestamp.isoformat()
    return client.post("/api/hub/data", json=payload)


# --------------------------------------------------------------- basics
def test_health(client):
    assert client.get("/api/health").json()["status"] == "healthy"


def test_root_points_to_docs(client):
    assert client.get("/").json()["docs"] == "/docs"


# --------------------------------------------------------------- sensors
def test_register_sensor(client, dht):
    assert dht["sensor_id"] == "dht22_01" and dht["active"] is True and dht["id"] >= 1


def test_duplicate_sensor_rejected(client, dht):
    r = client.post("/api/sensors", json={"sensor_id": "dht22_01", "type": "temperature_humidity"})
    assert r.status_code == 400


def test_invalid_sensor_payload_rejected(client):
    assert client.post("/api/sensors", json={"sensor_id": "", "type": "motion"}).status_code == 422
    assert client.post("/api/sensors", json={"type": "motion"}).status_code == 422


def test_list_sensors(client, dht):
    client.post("/api/sensors", json={"sensor_id": "pir_01", "type": "motion"})
    ids = {s["sensor_id"] for s in client.get("/api/sensors").json()}
    assert ids == {"dht22_01", "pir_01"}


def test_unknown_sensor_id_404(client):
    assert client.get("/api/sensors/999").status_code == 404


# --------------------------------------------------------------- hub ingestion
def test_hub_stores_reading(client, dht):
    r = post_reading(client, {"temperature": 22.5, "humidity": 48.0})
    assert r.status_code == 201 and r.json()["reading_id"] >= 1
    latest = client.get(f"/api/sensors/{dht['id']}/latest").json()
    assert latest["data"] == {"temperature": 22.5, "humidity": 48.0}


def test_hub_rejects_unregistered_sensor(client):
    assert post_reading(client, {"temperature": 20}, sensor_id="ghost_01").status_code == 404


def test_hub_rejects_inactive_sensor(client, db, dht):
    SensorCRUD.update_sensor_active(db, dht["id"], False)
    assert post_reading(client, {"temperature": 20}).status_code == 400


def test_hub_rejects_malformed_payload(client, dht):
    r = client.post("/api/hub/data", json={"sensor_id": "dht22_01", "data": "not-an-object"})
    assert r.status_code == 422


# --------------------------------------------------------------- queries
def test_latest_picks_newest_timestamp(client, dht):
    now = datetime.utcnow()
    post_reading(client, {"temperature": 30.0}, timestamp=now - timedelta(minutes=1))
    post_reading(client, {"temperature": 10.0}, timestamp=now - timedelta(minutes=5))  # older, sent later
    assert client.get(f"/api/sensors/{dht['id']}/latest").json()["data"]["temperature"] == 30.0


def test_latest_404_when_no_readings(client, dht):
    assert client.get(f"/api/sensors/{dht['id']}/latest").status_code == 404


def test_latest_across_sensors_one_per_sensor(client, dht):
    client.post("/api/sensors", json={"sensor_id": "pir_01", "type": "motion"})
    post_reading(client, {"temperature": 21.0})
    post_reading(client, {"temperature": 22.0})
    post_reading(client, {"motion": True}, sensor_id="pir_01")
    latest = client.get("/api/sensors/latest").json()
    assert len(latest) == 2


def test_history_window_and_order(client, db, dht):
    now = datetime.utcnow()
    ReadingCRUD.create_reading(db, dht["id"], {"temperature": 1.0}, now - timedelta(hours=30))  # outside 24 h
    ReadingCRUD.create_reading(db, dht["id"], {"temperature": 2.0}, now - timedelta(hours=2))
    ReadingCRUD.create_reading(db, dht["id"], {"temperature": 3.0}, now - timedelta(hours=1))
    hist = client.get(f"/api/sensors/{dht['id']}/history?hours=24").json()
    assert [h["data"]["temperature"] for h in hist] == [2.0, 3.0]  # oldest first, 30 h one excluded
    wide = client.get(f"/api/sensors/{dht['id']}/history?hours=48").json()
    assert len(wide) == 3


def test_history_validates_hours(client, dht):
    assert client.get(f"/api/sensors/{dht['id']}/history?hours=0").status_code == 422
    assert client.get(f"/api/sensors/{dht['id']}/history?hours=721").status_code == 422


def test_history_unknown_sensor_404(client):
    assert client.get("/api/sensors/999/history").status_code == 404
