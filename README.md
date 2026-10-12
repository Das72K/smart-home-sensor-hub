# Smart Home Sensor Hub

An end-to-end IoT pipeline: simulated sensors post readings to a **FastAPI** hub, which validates
them, stores them in **PostgreSQL**, and pushes each new reading to a **React** dashboard over
**WebSocket**, with REST endpoints for current values and history.

<!-- Screenshot: save one as docs/dashboard.png, then delete this comment line and the one below it.
![Dashboard](docs/dashboard.png) -->

**Stack:** Python · FastAPI · SQLAlchemy 2 · Pydantic 2 · PostgreSQL 16 · WebSocket · React 19 · Recharts · Docker Compose · pytest

---

## Architecture

```
sensor_simulator.py               FastAPI hub (main.py)                      React dashboard
───────────────────               ─────────────────────                      ───────────────
DHT22: temp + humidity  ─┐        POST /api/hub/data                         gauges + 24 h charts
PIR:   motion           ─┴─HTTP─▶   1. validate (Pydantic)                          ▲
every 5 s                           2. sensor registered & active?                  │
                                    3. store reading ─────▶ PostgreSQL               │
                                    4. broadcast ─────────────── WebSocket /ws/live ┘
                                  GET /api/sensors/...  ◀──── REST (initial load, history)
```

**Design choices**

- **Push, not poll.** The dashboard loads once over REST, then receives each reading over WebSocket
  the moment it is stored. No refresh loop, no polling load on the database.
- **One readings table for every sensor type.** The payload is a JSON column
  (`{"temperature": 24.5, "humidity": 52.1}` or `{"motion": true}`), so a new sensor type needs no
  schema migration.
- **Sensor registry.** Readings are only accepted from registered, active sensors (`404` unknown,
  `400` inactive), so a misconfigured device can't pollute the data.
- **Indexed for the main query.** A composite index on `(sensor_id, timestamp)` serves "last N hours
  of sensor X" directly.
- **Simulator behaves like real hardware.** DHT22 temperature follows a slow random walk and ~5% of
  reads fail (as real DHT22s do); the PIR has a 30-second re-trigger cooldown.

---

## Quick start

Requires **Docker**, **Python 3.11–3.12** and **Node.js 18+**.

```bash
# 1. Database + API (PostgreSQL 16 and FastAPI with hot reload)
docker compose up -d

# 2. Register the two simulated sensors (once)
curl -X POST http://localhost:8000/api/sensors -H "Content-Type: application/json" \
     -d '{"sensor_id": "dht22_01", "type": "temperature_humidity", "location": "living_room"}'
curl -X POST http://localhost:8000/api/sensors -H "Content-Type: application/json" \
     -d '{"sensor_id": "pir_01", "type": "motion", "location": "bedroom"}'

# 3. Simulator (new terminal)
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python sensor_simulator.py

# 4. Dashboard (new terminal)
cd smart-home-dashboard && npm install && npm start  # http://localhost:3000
```

API docs (Swagger UI): <http://localhost:8000/docs>

<details>
<summary>Without Docker (local PostgreSQL)</summary>

```bash
cp .env.example .env            # adjust DATABASE_URL if needed
pip install -r requirements.txt
uvicorn main:app --reload       # tables are created on startup
```

The database `smart_home_hub` and user `hub_user` must exist. The credentials in `.env.example`
and `docker-compose.yml` are local-development defaults only.
</details>

---

## API

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/hub/data` | Ingest a reading from a device (201, 404 unknown sensor, 400 inactive) |
| `POST` | `/api/sensors` | Register a sensor (400 if it already exists) |
| `GET` | `/api/sensors` | List active sensors |
| `GET` | `/api/sensors/{id}` | Sensor details |
| `GET` | `/api/sensors/latest` | Latest reading of every sensor |
| `GET` | `/api/sensors/{id}/latest` | Latest reading of one sensor |
| `GET` | `/api/sensors/{id}/history?hours=24` | Readings from the last N hours (1–720), oldest first |
| `GET` | `/api/health` | Health check |
| `WS` | `/ws/live` | Live stream of new readings |

**Ingest payload** (`POST /api/hub/data`):

```json
{"sensor_id": "dht22_01", "type": "temperature_humidity",
 "data": {"temperature": 24.5, "humidity": 52.1}, "timestamp": "2026-10-07T14:32:10Z"}
```

**WebSocket message** (one per stored reading):

```json
{"type": "reading_update", "sensor_id": "dht22_01", "sensor_type": "temperature_humidity",
 "location": "living_room", "data": {"temperature": 24.5, "humidity": 52.1},
 "timestamp": "2026-10-07T14:32:10Z"}
```

---

## Data model

```
sensors                                   sensor_readings
──────────────────────────────            ─────────────────────────────────────────
id           integer  PK                  id          integer  PK
sensor_id    varchar(50) unique  ◀──┐     sensor_id   integer  FK → sensors.id (cascade)
type         varchar(50)            └──── data        json     sensor-specific payload
location     varchar(100)                 timestamp   timestamp  (indexed)
active       boolean                      created_at  timestamp
created_at / updated_at                   INDEX (sensor_id, timestamp)
```

---

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

The API tests run against an in-memory SQLite database (no PostgreSQL needed): sensor registration
and validation, ingestion rules (unknown / inactive sensor, malformed payload), latest-reading
selection, the history time window and ordering, and query-parameter bounds. Further tests cover
WebSocket fan-out (including dropping disconnected clients) and the simulator (value ranges, DHT22
failure rate, PIR cooldown, HTTP error handling).

---

## Project layout

```
main.py               FastAPI app: routes, WebSocket endpoint, broadcast
crud.py               database queries (sensors, readings)
models.py             SQLAlchemy models
schemas.py            Pydantic request/response schemas
database.py           engine, session, FastAPI dependency
config.py             settings from environment / .env
sensor_simulator.py   DHT22 + PIR simulators posting to the hub
tests/                pytest suite
smart-home-dashboard/ React front-end (see its README)
docker-compose.yml    PostgreSQL 16 + API
```

## Limitations and next steps

Built as a local, single-user system. Before exposing it to a network it would need authentication
on the API and WebSocket, restricted CORS (currently `*` for development), proper secrets
management, and database migrations (Alembic) instead of `create_all`. Natural extensions:
alerting (thresholds, sensor silent for N minutes), downsampled history for long time ranges
(e.g. TimescaleDB), and real hardware (an ESP32 with DHT22 + PIR posting to the same endpoint).

## License

MIT © 2026 Dorin Dascălu
