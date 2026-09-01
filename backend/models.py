"""SQLAlchemy ORM models"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, BigInteger, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from database import Base
import enum

class NetworkType(str, enum.Enum):
    LTE_2G = "2G"
    LTE_3G = "3G"
    LTE_4G = "4G"
    LTE_5G = "5G"

class BandType(str, enum.Enum):
    B1 = "B1"
    B3 = "B3"
    B5 = "B5"
    B7 = "B7"
    B8 = "B8"
    B28 = "B28"
    B41 = "B41"
    N78 = "N78"
    UNKNOWN = "UNKNOWN"

class FieldLog(Base):
    """Raw telemetry data from field collection"""
    __tablename__ = "field_logs"
    
    id = Column(BigInteger, primary_key=True, index=True)
    
    # Device info
    device_id = Column(String(100), nullable=False, index=True)
    session_id = Column(String(36), nullable=False)
    
    # Network parameters
    mcc = Column(Integer, nullable=False)  # 515
    mnc = Column(Integer, nullable=False)  # 03 or 05
    network_type = Column(String(10), nullable=False)
    
    # Cell identifiers
    enodeb_id = Column(Integer, index=True)
    cell_id = Column(BigInteger, nullable=False, index=True)
    physical_cell_id = Column(Integer)
    tracking_area_code = Column(Integer)
    
    # Frequency
    frequency_band = Column(String(10))
    arfcn = Column(Integer)
    bandwidth_mhz = Column(Integer)
    
    # Signal metrics
    rsrp = Column(Integer)  # dBm
    rsrq = Column(Integer)
    rssi = Column(Integer)
    rssnr = Column(Integer)
    cqi = Column(Integer)
    
    # Location
    location = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    gps_accuracy_meters = Column(Float)
    altitude_meters = Column(Float)
    
    # Timing
    timestamp_utc = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    device_timestamp = Column(DateTime(timezone=True), nullable=False)
    
    # Optional
    carrier_name = Column(String(100))
    connection_status = Column(String(50))
    notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CellTower(Base):
    """Calculated tower locations"""
    __tablename__ = "cell_towers"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Identifiers
    enodeb_id = Column(Integer, unique=True, nullable=False, index=True)
    site_name = Column(String(200))
    
    # Network
    mcc = Column(Integer, nullable=False, default=515)
    mnc = Column(Integer, nullable=False)
    network_type = Column(String(10), nullable=False)
    
    # Location
    location = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    
    # Quality metrics
    confidence_score = Column(Float)
    sample_count = Column(Integer, default=0)
    avg_distance_error_meters = Column(Float)
    
    # Source
    source = Column(String(50), default='triangulation')
    external_id = Column(String(100))
    
    # Address
    address = Column(Text)
    barangay = Column(String(200))
    city = Column(String(200))
    province = Column(String(200))
    
    # Timing
    first_seen = Column(DateTime(timezone=True))
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)
    notes = Column(Text)
    
    # Relationships
    sectors = relationship("TowerSector", back_populates="tower", cascade="all, delete-orphan")

class TowerSector(Base):
    """Individual cell sectors for towers"""
    __tablename__ = "tower_sectors"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key
    tower_id = Column(Integer, ForeignKey('cell_towers.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Identifiers
    cell_id = Column(BigInteger, unique=True, nullable=False, index=True)
    physical_cell_id = Column(Integer)
    sector_number = Column(Integer)
    
    # Frequency
    frequency_band = Column(String(10), nullable=False)
    arfcn = Column(Integer)
    bandwidth_mhz = Column(Integer)
    
    # Orientation
    azimuth_degrees = Column(Integer)
    beamwidth_degrees = Column(Integer, default=120)
    
    # Coverage
    coverage_area = Column(Geometry(geometry_type='POLYGON', srid=4326))
    estimated_range_meters = Column(Integer, default=1000)
    
    # Statistics
    avg_rsrp = Column(Float)
    avg_rssi = Column(Float)
    max_observed_distance_meters = Column(Float)
    
    # Metadata
    sample_count = Column(Integer, default=0)
    last_observed = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Relationship
    tower = relationship("CellTower", back_populates="sectors")
