"""WebSocket fan-out: every connected client gets the reading; dead clients are dropped."""

import asyncio
from datetime import datetime
from types import SimpleNamespace

import main


class FakeSocket:
    def __init__(self, fail=False):
        self.fail, self.sent = fail, []

    async def send_json(self, message):
        if self.fail:
            raise RuntimeError("client gone")
        self.sent.append(message)


def test_broadcast_reaches_clients_and_drops_dead_ones(monkeypatch):
    alive_a, alive_b, dead = FakeSocket(), FakeSocket(), FakeSocket(fail=True)
    monkeypatch.setattr(main, "active_connections", [alive_a, dead, alive_b])

    reading = SimpleNamespace(data={"temperature": 23.4}, timestamp=datetime(2026, 10, 7, 12, 0, 0))
    sensor = SimpleNamespace(sensor_id="dht22_01", type="temperature_humidity", location="living_room")
    asyncio.run(main.broadcast_reading(reading, sensor))

    expected = {
        "type": "reading_update", "sensor_id": "dht22_01", "sensor_type": "temperature_humidity",
        "location": "living_room", "data": {"temperature": 23.4}, "timestamp": "2026-10-07T12:00:00Z",
    }
    assert alive_a.sent == [expected] and alive_b.sent == [expected]
    assert main.active_connections == [alive_a, alive_b]
