"""Pydantic schemas for request/response validation"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class NetworkTypeEnum(str, Enum):
    G2 = "2G"
    G3 = "3G"
    G4 = "4G"
    G5 = "5G"

class BandEnum(str, Enum):
    B1 = "B1"
    B3 = "B3"
    B5 = "B5"
    B7 = "B7"
    B8 = "B8"
    B28 = "B28"
    B41 = "B41"
    N78 = "N78"
    UNKNOWN = "UNKNOWN"

# =============================================================================
# FIELD LOG SCHEMAS
# =============================================================================

class FieldLogCreate(BaseModel):
    """Schema for creating a field log entry"""
    device_id: str
    session_id: str
    
    mcc: int = 515
    mnc: int = Field(..., ge=3, le=5)
    network_type: str
    
    enodeb_id: Optional[int] = None
    cell_id: int
    physical_cell_id: Optional[int] = None
    tracking_area_code: Optional[int] = None
    
    frequency_band: Optional[str] = "UNKNOWN"
    arfcn: Optional[int] = None
    bandwidth_mhz: Optional[int] = None
    
    rsrp: Optional[int] = Field(None, ge=-140, le=-40)
    rsrq: Optional[int] = Field(None, ge=-20, le=-3)
    rssi: Optional[int] = Field(None, ge=-120, le=-20)
    rssnr: Optional[int] = None
    cqi: Optional[int] = Field(None, ge=0, le=15)
    
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    gps_accuracy_meters: Optional[float] = None
    altitude_meters: Optional[float] = None
    
    device_timestamp: datetime
    
    carrier_name: Optional[str] = None
    connection_status: Optional[str] = None
    notes: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "android_abc123",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "mcc": 515,
                "mnc": 3,
                "network_type": "4G",
                "enodeb_id": 123456,
                "cell_id": 12345678,
                "physical_cell_id": 250,
                "tracking_area_code": 1234,
                "frequency_band": "B3",
                "rsrp": -95,
                "rsrq": -12,
                "rssi": -65,
                "latitude": 14.5995,
                "longitude": 121.0244,
                "gps_accuracy_meters": 15.5,
                "device_timestamp": "2024-01-15T10:30:00Z"
            }
        }

class FieldLogResponse(BaseModel):
    """Response schema for field log"""
    id: int
    device_id: str
    enodeb_id: Optional[int]
    cell_id: int
    network_type: str
    frequency_band: Optional[str]
    rsrp: Optional[int]
    rssi: Optional[int]
    timestamp_utc: datetime
    
    class Config:
        from_attributes = True

class FieldLogBatch(BaseModel):
    """Schema for batch field log upload"""
    logs: List[FieldLogCreate]

# =============================================================================
# CELL TOWER SCHEMAS
# =============================================================================

class CellTowerResponse(BaseModel):
    """Response schema for cell tower"""
    id: int
    enodeb_id: int
    site_name: Optional[str]
    network_type: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    confidence_score: Optional[float]
    sample_count: int
    source: str
    city: Optional[str]
    is_active: bool
    last_updated: datetime
    
    class Config:
        from_attributes = True

class TowerSectorResponse(BaseModel):
    """Response schema for tower sector"""
    id: int
    tower_id: int
    cell_id: int
    sector_number: Optional[int]
    frequency_band: str
    azimuth_degrees: Optional[int]
    beamwidth_degrees: int
    estimated_range_meters: int
    avg_rsrp: Optional[float]
    avg_rssi: Optional[float]
    is_active: bool
    
    class Config:
        from_attributes = True

# =============================================================================
# TRIANGULATION SCHEMAS
# =============================================================================

class TriangulationRequest(BaseModel):
    """Request schema for tower triangulation"""
    enodeb_id: int
    min_samples: Optional[int] = 5
    max_distance_meters: Optional[int] = 5000

class TriangulationResponse(BaseModel):
    """Response schema for triangulation result"""
    enodeb_id: int
    latitude: float
    longitude: float
    confidence_score: float
    sample_count: int
    avg_distance_error_meters: float
    calculation_method: str = "weighted_centroid"
    
# =============================================================================
# HEATMAP SCHEMAS
# =============================================================================

class SignalHeatmapResponse(BaseModel):
    """Response schema for signal heatmap data"""
    geojson: Dict[str, Any]
    point_count: int
    time_range_hours: int
