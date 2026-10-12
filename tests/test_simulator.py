import random

import requests

import sensor_simulator as sim


def test_dht22_values_stay_physical():
    random.seed(0)
    dht = sim.DHT22Simulator()
    readings = [r for r in (dht.read() for _ in range(2000)) if r]
    assert all(-40 <= r["temperature"] <= 80 for r in readings)
    assert all(0 <= r["humidity"] <= 100 for r in readings)


def test_dht22_fails_about_5_percent():
    random.seed(1)
    dht = sim.DHT22Simulator()
    failures = sum(dht.read() is None for _ in range(4000))
    assert 0.03 < failures / 4000 < 0.07


def test_dht22_drifts_slowly():
    random.seed(2)
    dht = sim.DHT22Simulator(base_temp=22.0)
    temps = [r["temperature"] for r in (dht.read() for _ in range(200)) if r]
    steps = [abs(b - a) for a, b in zip(temps, temps[1:])]
    assert max(steps) < 0.5  # random walk, not jumps


def test_pir_cooldown(monkeypatch):
    clock = {"t": 1000.0}
    monkeypatch.setattr(sim.time, "time", lambda: clock["t"])
    monkeypatch.setattr(sim.random, "random", lambda: 0.0)  # would detect motion every time

    pir = sim.PIRSimulator(cooldown_seconds=30)
    assert pir.read() == {"motion": True}
    clock["t"] += 10
    assert pir.read() == {"motion": False}  # still cooling down
    clock["t"] += 25
    assert pir.read() == {"motion": True}   # 35 s later: armed again
    assert pir.motion_count == 2


def test_pir_no_motion_when_random_high(monkeypatch):
    monkeypatch.setattr(sim.random, "random", lambda: 0.99)
    assert sim.PIRSimulator().read() == {"motion": False}


class FakeResponse:
    def __init__(self, status, text=""):
        self.status_code, self.text = status, text


def test_send_reading_payload_and_success(monkeypatch):
    calls = {}

    def fake_post(url, json, timeout):
        calls.update(url=url, json=json, timeout=timeout)
        return FakeResponse(201)

    monkeypatch.setattr(sim.requests, "post", fake_post)
    assert sim.send_reading("dht22_01", "temperature_humidity", {"temperature": 21.0}) is True
    assert calls["url"] == sim.HUB_URL and calls["timeout"] == sim.REQUEST_TIMEOUT
    assert calls["json"]["sensor_id"] == "dht22_01" and calls["json"]["timestamp"].endswith("Z")


def test_send_reading_http_error(monkeypatch):
    monkeypatch.setattr(sim.requests, "post", lambda *a, **k: FakeResponse(404, "not found"))
    assert sim.send_reading("ghost", "motion", {"motion": False}) is False


def test_send_reading_hub_down(monkeypatch):
    def boom(*a, **k):
        raise requests.exceptions.ConnectionError()

    monkeypatch.setattr(sim.requests, "post", boom)
    assert sim.send_reading("pir_01", "motion", {"motion": False}) is False
