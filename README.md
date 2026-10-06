# Smart Home Sensor Hub

A **production-grade IoT system** that collects environmental data from distributed sensors in real-time and streams it to a live dashboard via WebSocket.

**Tech Stack:** FastAPI, PostgreSQL, React 18, Docker

---

## Overview

This project demonstrates a **complete full-stack architecture** for IoT/sensor systems:

```
Sensor Simulator          Hub (FastAPI)         Dashboard (React)
──────────────           ─────────────         ────────────────
DHT22 (temp/humidity)    REST API              Live gauges
PIR (motion)     ──→ POST /api/hub/data  ──→  Charts
                         |                     WebSocket updates
                         ↓
                    PostgreSQL DB
                    (persistent storage)
```

**Key Features:**
- ✅ Real-time sensor data streaming (WebSocket)
- ✅ RESTful API for historical queries
- ✅ Distributed sensor network (simulator = N devices)
- ✅ Reliable data persistence (PostgreSQL)
- ✅ Production-grade error handling & logging
- ✅ Docker deployment ready

---

## Project Structure

```
smart-home-sensor-hub/
├── Backend (FastAPI)
│   ├── main.py                 # FastAPI app (routes, WebSocket)
│   ├── config.py               # Configuration from environment
│   ├── database.py             # SQLAlchemy setup & session mgmt
│   ├── models.py               # ORM models (Sensor, SensorReading)
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── crud.py                 # Database operations
│   ├── sensor_simulator.py     # Generates fake sensor data
│   ├── requirements.txt        # Python dependencies
│   ├── .env.example            # Template for environment config
│   ├── Dockerfile              # Container image spec
│   ├── docker-compose.yml      # Orchestration (PostgreSQL + FastAPI)
│   └── .gitignore              # Git exclude rules
│
├── Frontend (React 18)
│   └── smart-home-dashboard/
│       ├── src/
│       │   ├── components/
│       │   │   ├── SensorGauge.jsx    # Current reading displays
│       │   │   └── HistoryChart.jsx   # 24-hour trend charts
│       │   ├── hooks/
│       │   │   └── useSensorData.js   # WebSocket + API integration
│       │   ├── App.js                 # Main application
│       │   ├── index.js               # React entry point
│       │   └── index.css              # Global styles
│       ├── public/
│       │   └── index.html
│       ├── package.json
│       └── README.md
│
└── Documentation
    └── README.md               # This file
```

---

## Quick Start (Local Development)

### Prerequisites
- PostgreSQL 15+ (running, credentials: `hub_user` / `hub_secure_pass_123`)
- Python 3.11+
- pip

### 1. Clone & Setup

```bash
cd smart-home-sensor-hub

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

### 2. Database

Ensure PostgreSQL is running with database `smart_home_hub` created:

```bash
psql -h localhost -U hub_user -d smart_home_hub -c "\dt"
```

Should show `sensors` and `sensor_readings` tables.

### 3. Start Backend

```bash
python main.py
# or with uvicorn directly:
uvicorn main:app --reload
```

Backend runs on `http://localhost:8000`

### 4. Register Sensors

In another terminal, register the test sensors:

```bash
# Register DHT22
curl -X POST http://localhost:8000/api/sensors \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "dht22_01",
    "type": "temperature_humidity",
    "location": "living_room"
  }'

# Register PIR
curl -X POST http://localhost:8000/api/sensors \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "pir_01",
    "type": "motion",
    "location": "bedroom"
  }'
```

### 5. Start Simulator

In another terminal:

```bash
python sensor_simulator.py
```

Simulator generates fake DHT22 + PIR data and POSTs to the hub every 5 seconds.

### 6. Start Dashboard (Terminal 4)

In another terminal:

```bash
cd smart-home-dashboard
npm install
npm start
```

Dashboard opens at `http://localhost:3000` with real-time updates.

### 7. Verify

Check the API and dashboard:

```bash
# Latest readings from all sensors
curl http://localhost:8000/api/sensors/latest

# Interactive API docs
http://localhost:8000/docs

# Live dashboard
http://localhost:3000
```

You should see:
- 🟢 WebSocket connected ("Live" indicator)
- Current sensor readings in gauges
- 24-hour historical charts updating in real-time

---

## API Documentation

Auto-generated interactive docs available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key Endpoints

**Hub (receive data)**
- `POST /api/hub/data` — Sensor posts reading here

**Sensors (manage)**
- `POST /api/sensors` — Register new sensor
- `GET /api/sensors` — List all sensors
- `GET /api/sensors/{id}` — Get sensor details

**Readings (query data)**
- `GET /api/sensors/latest` — Latest from all sensors
- `GET /api/sensors/{id}/latest` — Latest for one sensor
- `GET /api/sensors/{id}/history?hours=24` — Historical data

**WebSocket (real-time)**
- `WS /ws/live` — Subscribe to live updates

---

## Docker Deployment

### Using Docker Compose

Orchestrates PostgreSQL + FastAPI in one command:

```bash
docker-compose up
```

This:
1. Starts PostgreSQL on `localhost:5432`
2. Builds FastAPI image
3. Starts FastAPI on `localhost:8000`
4. Mounts local code (hot reload)

Then register sensors and run simulator (same as above).

To stop:
```bash
docker-compose down
```

---

## Data Schema

### `sensors` Table (Registry)
```
id          INTEGER PRIMARY KEY
sensor_id   VARCHAR(50) UNIQUE  -- "dht22_01", "pir_01"
type        VARCHAR(50)         -- "temperature_humidity", "motion"
location    VARCHAR(100)        -- "living_room", "bedroom"
active      BOOLEAN DEFAULT TRUE
created_at  TIMESTAMP
updated_at  TIMESTAMP
```

### `sensor_readings` Table (Time-Series)
```
id          BIGSERIAL PRIMARY KEY
sensor_id   INT FOREIGN KEY     -- References sensors.id
data        JSONB               -- {"temperature": 24.5, "humidity": 52.1}
timestamp   TIMESTAMP           -- When reading was taken
created_at  TIMESTAMP
```

**Why JSONB?** Allows flexible data formats — DHT22 stores temp+humidity, PIR stores motion boolean. Same table, no schema migrations needed for new sensor types.

---

## Simulator Behavior

**DHT22** (Temperature/Humidity)
- Reads every 5 seconds
- Temperature drifts gradually (-40 to +80°C range)
- Humidity correlates with temperature
- ~5% chance of read failure (simulates flaky sensors)

**PIR** (Motion)
- 10% chance of motion detection (baseline)
- 30-second cooldown after detection (realistic hardware)
- Always returns a reading (true/false)

To customize simulator behavior, edit `sensor_simulator.py`:
```python
dht22 = DHT22Simulator(base_temp=22.0, base_humidity=50.0)
pir = PIRSimulator(cooldown_seconds=30)
```

---

## Development

### Add a New Sensor Type

1. **Simulator:** Add a new class in `sensor_simulator.py` (e.g., `LightSensorSimulator`)
2. **Hub:** Send data to `POST /api/hub/data`
3. **Database:** JSONB automatically accepts any JSON structure
4. **Dashboard:** Query it via REST/WebSocket

### Testing

```bash
# Run unit tests (Phase 3)
pytest tests/

# Test a single endpoint
curl -X GET http://localhost:8000/api/sensors
```

### Logging

Logs go to console. Configure level in `.env`:
```
LOG_LEVEL=INFO
```

Adjust to `DEBUG` for verbose output.

---

## Performance Notes

**Current setup handles:**
- 100 sensors @ 1 reading/5s = ~20 reads/sec (trivial)
- 1M+ historical readings (fast indexed queries)

**For scaling to 10,000+ sensors:**
- Add read replicas (PostgreSQL streaming replication)
- Implement sensor data aggregation (hourly/daily)
- Use time-series database (ClickHouse, TimescaleDB) for compression

---

## Project Phases (Completed)

✅ **Phase 1:** Architecture & API design  
✅ **Phase 2:** Backend implementation (FastAPI, PostgreSQL, WebSocket)  
✅ **Phase 3:** Sensor simulator with realistic behavior  
✅ **Phase 4:** React dashboard with live gauges & 24-hour charts  
✅ **Phase 5:** Documentation & GitHub publication

## Future Enhancements

- [ ] Alerting (temperature out of range, no reading in 30min)
- [ ] Machine learning (anomaly detection, forecasting)
- [ ] Authentication & authorization
- [ ] Mobile app (React Native)
- [ ] Metrics dashboard (Prometheus/Grafana)

---

## Troubleshooting

### "Connection refused" on `POST /api/hub/data`
→ FastAPI not running. Start it: `python main.py`

### "Sensor not found" error
→ Register sensors first (curl commands above) or via `POST /api/sensors`

### PostgreSQL connection errors
→ Check `DATABASE_URL` in `.env` matches your setup

### WebSocket not updating
→ Ensure clients are connected to `ws://localhost:8000/ws/live` before sensors post data

---

## Portfolio Impact

This project demonstrates:
- ✅ **Full-stack architecture** (hardware → API → database)
- ✅ **Real-time systems** (WebSocket, event streaming)
- ✅ **Database design** (normalization, indexing, JSONB flexibility)
- ✅ **Production code** (error handling, logging, validation)
- ✅ **DevOps** (Docker, environment config, deployment)
- ✅ **Scalability mindset** (connection pooling, query optimization)

**Signals to employers:** 
"I can design and build systems that handle real-time sensor data at scale."

Direct relevance to:
- Autonomous systems (sensor fusion, real-time processing)
- Embedded systems (distributed networks, reliability)
- Robotics (data acquisition, edge computing)
- Aerospace/Military (Măgurele institute work)

---

## Author

Built for portfolio: Road to DeepTech 🚀

---

## License

MIT
