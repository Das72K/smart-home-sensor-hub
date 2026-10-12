"""
FastAPI application entry point.

Define routes, WebSocket handlers, and FastAPI setup.
"""

import logging
from datetime import datetime
from typing import List

from fastapi import FastAPI, Depends, HTTPException, WebSocket, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from config import settings
from database import get_db, engine
from models import Base
from schemas import (
    SensorCreate, SensorResponse, ReadingResponse, 
    HubDataPayload, SensorWithLatest
)
from crud import SensorCRUD, ReadingCRUD

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# Configure logging
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Smart Home Sensor Hub",
    description="Real-time sensor data collection and streaming",
    version="1.0.0",
)

# Add CORS middleware (allow requests from any origin during development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active WebSocket connections
active_connections: List[WebSocket] = []


@app.on_event("startup")
async def startup_event():
    """Initialize on app startup."""
    logger.info("🚀 Smart Home Sensor Hub starting...")
    logger.info(f"📊 Database: {make_url(settings.database_url).render_as_string(hide_password=True)}")
    logger.info(f"🌐 Server: http://{settings.host}:{settings.port}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on app shutdown."""
    logger.info("💤 Smart Home Sensor Hub shutting down...")


# ============================================================================
# HUB ENDPOINTS (receive data from simulator)
# ============================================================================

@app.post("/api/hub/data", response_model=dict, status_code=201)
async def receive_sensor_data(
    payload: HubDataPayload,
    db: Session = Depends(get_db)
) -> dict:
    """
    Receive sensor data from simulator/device.
    
    The sensor simulator POSTs here every 5 seconds.
    This endpoint validates the sensor exists, stores the reading,
    and broadcasts to all WebSocket clients.
    
    Expected payload:
    {
        "sensor_id": "dht22_01",
        "type": "temperature_humidity",
        "data": {"temperature": 24.5, "humidity": 52.1},
        "timestamp": "2025-01-15T14:32:10Z"
    }
    """
    try:
        # Look up sensor
        sensor = SensorCRUD.get_sensor_by_sensor_id(db, payload.sensor_id)
        if not sensor:
            logger.warning(f"⚠️ Received data for unknown sensor: {payload.sensor_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Sensor '{payload.sensor_id}' not found. Register it first."
            )
        
        if not sensor.active:
            logger.warning(f"⚠️ Received data from inactive sensor: {payload.sensor_id}")
            raise HTTPException(
                status_code=400,
                detail=f"Sensor '{payload.sensor_id}' is inactive."
            )
        
        # Use provided timestamp or current time
        timestamp = payload.timestamp or datetime.utcnow()
        
        # Store reading
        reading = ReadingCRUD.create_reading(
            db,
            sensor_id=sensor.id,
            data=payload.data,
            timestamp=timestamp
        )
        
        logger.debug(f"✓ Stored reading from {payload.sensor_id}: {payload.data}")
        
        # Broadcast to WebSocket clients
        await broadcast_reading(reading, sensor)
        
        return {
            "status": "success",
            "message": f"Reading stored for sensor {payload.sensor_id}",
            "reading_id": reading.id,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error storing reading: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# SENSOR MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/api/sensors", response_model=SensorResponse, status_code=201)
async def create_sensor(
    sensor: SensorCreate,
    db: Session = Depends(get_db)
) -> SensorResponse:
    """Register a new sensor."""
    existing = SensorCRUD.get_sensor_by_sensor_id(db, sensor.sensor_id)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Sensor '{sensor.sensor_id}' already exists."
        )
    
    db_sensor = SensorCRUD.create_sensor(db, sensor)
    logger.info(f"✓ Created sensor: {db_sensor.sensor_id}")
    return db_sensor


@app.get("/api/sensors", response_model=List[SensorResponse])
async def list_sensors(db: Session = Depends(get_db)) -> List[SensorResponse]:
    """List all sensors."""
    sensors = SensorCRUD.list_sensors(db)
    return sensors

@app.get("/api/sensors/latest", response_model=List[ReadingResponse])
async def get_latest_readings(db: Session = Depends(get_db)) -> List[ReadingResponse]:
    """Get the latest reading from each sensor."""
    readings = ReadingCRUD.get_latest_readings(db)
    return readings

@app.get("/api/sensors/{sensor_id}", response_model=SensorResponse)
async def get_sensor(sensor_id: int, db: Session = Depends(get_db)) -> SensorResponse:
    """Get a specific sensor by ID."""
    sensor = SensorCRUD.get_sensor_by_id(db, sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return sensor


# ============================================================================
# DATA ENDPOINTS (query readings)
# ============================================================================



@app.get("/api/sensors/{sensor_id}/latest", response_model=ReadingResponse)
async def get_sensor_latest(sensor_id: int, db: Session = Depends(get_db)) -> ReadingResponse:
    """Get the latest reading for a specific sensor."""
    reading = ReadingCRUD.get_latest_reading_for_sensor(db, sensor_id)
    if not reading:
        raise HTTPException(status_code=404, detail="No readings for this sensor yet")
    return reading


@app.get("/api/sensors/{sensor_id}/history", response_model=List[ReadingResponse])
async def get_sensor_history(
    sensor_id: int,
    hours: int = Query(24, ge=1, le=720),
    db: Session = Depends(get_db)
) -> List[ReadingResponse]:
    """Get historical readings for a sensor (default last 24 hours)."""
    sensor = SensorCRUD.get_sensor_by_id(db, sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    readings = ReadingCRUD.get_readings_since(db, sensor_id, hours)
    return list(reversed(readings))  # Return in ascending order (oldest first)


@app.get("/api/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "service": "Smart Home Sensor Hub"}


# ============================================================================
# WEBSOCKET (real-time streaming)
# ============================================================================

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time sensor updates.
    
    Dashboard opens this connection and receives updates whenever
    a new reading arrives at the hub.
    
    Example client-side usage:
    ```javascript
    const ws = new WebSocket("ws://localhost:8000/ws/live");
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log("New reading:", data);
    };
    ```
    """
    await websocket.accept()
    active_connections.append(websocket)
    
    logger.info(f"🔗 WebSocket client connected. Total connections: {len(active_connections)}")
    
    try:
        while True:
            # Keep connection open, wait for messages from client
            # (we mainly push from server, but allow pings from client)
            data = await websocket.receive_text()
            logger.debug(f"Received from client: {data}")
    
    except Exception as e:
        logger.info(f"WebSocket disconnected: {str(e)}")
    
    finally:
        active_connections.remove(websocket)
        logger.info(f"🔌 WebSocket client disconnected. Total connections: {len(active_connections)}")


async def broadcast_reading(reading, sensor):
    """
    Broadcast a new reading to all connected WebSocket clients.
    """
    message = {
        "type": "reading_update",
        "sensor_id": sensor.sensor_id,
        "sensor_type": sensor.type,
        "location": sensor.location,
        "data": reading.data,
        "timestamp": reading.timestamp.isoformat() + "Z",
    }
    
    # Send to all connected clients
    disconnected = []
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except Exception as e:
            logger.warning(f"Failed to send to WebSocket: {str(e)}")
            disconnected.append(connection)
    
    # Remove disconnected clients
    for conn in disconnected:
        active_connections.remove(conn)


# ============================================================================
# ROOT
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint - provides API info."""
    return {
        "service": "Smart Home Sensor Hub",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }
