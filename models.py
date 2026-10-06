"""
SQLAlchemy ORM models.

Define database tables as Python classes.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Sensor(Base):
    """
    Sensor registry table.
    
    Stores metadata about each physical sensor in the system.
    Every reading references a sensor via foreign key.
    """
    __tablename__ = "sensors"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(50), unique=True, nullable=False, index=True)  # "dht22_01"
    type = Column(String(50), nullable=False)  # "temperature_humidity", "motion"
    location = Column(String(100))  # "living_room", "bedroom"
    active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self) -> str:
        return f"Sensor(id={self.id}, sensor_id={self.sensor_id}, type={self.type})"


class SensorReading(Base):
    """
    Sensor readings table.
    
    Stores every data point from every sensor.
    Uses JSONB for flexible data (different sensor types in same table).
    Indexed for fast historical queries.
    """
    __tablename__ = "sensor_readings"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id", ondelete="CASCADE"), nullable=False)
    
    # JSONB: flexible JSON payload
    # DHT22: {"temperature": 24.5, "humidity": 52.1}
    # PIR: {"motion": true}
    data = Column(JSON, nullable=False)
    
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Composite index for common query patterns
    __table_args__ = (
        Index('idx_sensor_timestamp', 'sensor_id', 'timestamp'),
    )
    
    def __repr__(self) -> str:
        return f"SensorReading(id={self.id}, sensor_id={self.sensor_id}, timestamp={self.timestamp})"
