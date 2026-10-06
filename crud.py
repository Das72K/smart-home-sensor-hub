"""
CRUD (Create, Read, Update, Delete) operations.

Database abstraction layer - all queries go through here.
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime, timedelta
from typing import Optional, List

from models import Sensor, SensorReading
from schemas import SensorCreate, ReadingCreate


class SensorCRUD:
    """Operations on Sensor table."""
    
    @staticmethod
    def create_sensor(db: Session, sensor: SensorCreate) -> Sensor:
        """Create a new sensor in the database."""
        db_sensor = Sensor(
            sensor_id=sensor.sensor_id,
            type=sensor.type,
            location=sensor.location,
        )
        db.add(db_sensor)
        db.commit()
        db.refresh(db_sensor)
        return db_sensor
    
    @staticmethod
    def get_sensor_by_id(db: Session, sensor_id: int) -> Optional[Sensor]:
        """Get sensor by database ID."""
        return db.query(Sensor).filter(Sensor.id == sensor_id).first()
    
    @staticmethod
    def get_sensor_by_sensor_id(db: Session, sensor_id: str) -> Optional[Sensor]:
        """Get sensor by sensor_id (user-friendly identifier)."""
        return db.query(Sensor).filter(Sensor.sensor_id == sensor_id).first()
    
    @staticmethod
    def list_sensors(db: Session, active_only: bool = True) -> List[Sensor]:
        """List all sensors."""
        query = db.query(Sensor)
        if active_only:
            query = query.filter(Sensor.active == True)
        return query.order_by(Sensor.created_at).all()
    
    @staticmethod
    def update_sensor_active(db: Session, sensor_id: int, active: bool) -> Optional[Sensor]:
        """Enable/disable a sensor."""
        sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
        if sensor:
            sensor.active = active
            sensor.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(sensor)
        return sensor


class ReadingCRUD:
    """Operations on SensorReading table."""
    
    @staticmethod
    def create_reading(db: Session, sensor_id: int, data: dict, timestamp: Optional[datetime] = None) -> SensorReading:
        """Create a new sensor reading."""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        reading = SensorReading(
            sensor_id=sensor_id,
            data=data,
            timestamp=timestamp,
        )
        db.add(reading)
        db.commit()
        db.refresh(reading)
        return reading
    
    @staticmethod
    def get_latest_readings(db: Session, limit: int = 50) -> List[SensorReading]:
        """Get the latest reading from each sensor."""
        readings = []
        sensors = db.query(Sensor).all()
        for sensor in sensors:
            reading = db.query(SensorReading).filter(
                SensorReading.sensor_id == sensor.id
            ).order_by(desc(SensorReading.timestamp)).first()
            if reading:
                readings.append(reading)
        return readings[:limit]
    
    @staticmethod
    def get_latest_reading_for_sensor(db: Session, sensor_id: int) -> Optional[SensorReading]:
        """Get the most recent reading for a specific sensor."""
        return db.query(SensorReading).filter(
            SensorReading.sensor_id == sensor_id
        ).order_by(desc(SensorReading.timestamp)).first()
    
    @staticmethod
    def get_readings_since(
        db: Session,
        sensor_id: int,
        hours: int = 24,
        limit: int = 10000
    ) -> List[SensorReading]:
        """Get readings for a sensor from the last N hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return db.query(SensorReading).filter(
            and_(
                SensorReading.sensor_id == sensor_id,
                SensorReading.timestamp >= cutoff_time
            )
        ).order_by(desc(SensorReading.timestamp)).limit(limit).all()
    
    @staticmethod
    def get_readings_range(
        db: Session,
        sensor_id: int,
        start_time: datetime,
        end_time: datetime,
        limit: int = 10000
    ) -> List[SensorReading]:
        """Get readings within a time range."""
        return db.query(SensorReading).filter(
            and_(
                SensorReading.sensor_id == sensor_id,
                SensorReading.timestamp >= start_time,
                SensorReading.timestamp <= end_time
            )
        ).order_by(desc(SensorReading.timestamp)).limit(limit).all()
    
    @staticmethod
    def count_readings_for_sensor(db: Session, sensor_id: int) -> int:
        """Count total readings for a sensor."""
        return db.query(SensorReading).filter(
            SensorReading.sensor_id == sensor_id
        ).count()
