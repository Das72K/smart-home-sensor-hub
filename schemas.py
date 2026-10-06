"""
Pydantic schemas for API request/response validation.

These define the contract between client and server.
Pydantic automatically validates incoming JSON and serializes outgoing responses.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime


class SensorCreate(BaseModel):
    """Schema for creating a new sensor."""
    sensor_id: str = Field(..., min_length=1, max_length=50)
    type: str = Field(..., min_length=1, max_length=50)
    location: Optional[str] = Field(None, max_length=100)


class SensorResponse(BaseModel):
    """Schema for sensor response."""
    id: int
    sensor_id: str
    type: str
    location: Optional[str]
    active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # SQLAlchemy compatibility


class ReadingCreate(BaseModel):
    """Schema for creating a sensor reading (from hub endpoint)."""
    sensor_id: str = Field(..., description="Sensor identifier, e.g., 'dht22_01'")
    data: Dict[str, Any] = Field(..., description="Sensor data as JSON object")
    timestamp: Optional[datetime] = Field(None, description="Reading timestamp (auto-set if None)")


class ReadingResponse(BaseModel):
    """Schema for reading response."""
    id: int
    sensor_id: int
    data: Dict[str, Any]
    timestamp: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class HubDataPayload(BaseModel):
    """Schema for data posted by sensor simulator to hub endpoint."""
    sensor_id: str = Field(..., description="Sensor identifier")
    type: Optional[str] = Field(None, description="Sensor type (informational)")
    data: Dict[str, Any] = Field(..., description="Sensor readings")
    timestamp: Optional[datetime] = Field(None, description="When measurement was taken")


class SensorWithLatest(BaseModel):
    """Sensor + its latest reading."""
    sensor: SensorResponse
    latest_reading: Optional[ReadingResponse]
