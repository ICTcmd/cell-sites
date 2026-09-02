"""
Cell Site Mapping & Analytics System - FastAPI Backend
Main application entry point
"""
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Optional
import logging
from datetime import datetime, timedelta

from database import engine, Base, get_db
from models import FieldLog, CellTower, TowerSector
from schemas import (
    FieldLogCreate, FieldLogResponse, FieldLogBatch,
    CellTowerResponse, TowerSectorResponse,
    TriangulationRequest, TriangulationResponse,
    SignalHeatmapResponse
)
from triangulation_service import TriangulationService
from external_api_service import ExternalAPIService
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("Starting Cell Site Mapping System...")
    # Create tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
    yield
    logger.info("Shutting down...")

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Cell Site Mapping & Analytics API for Smart Communications Network",
    version=settings.API_VERSION,
    lifespan=lifespan
)

# CORS middleware - Allow all origins for ngrok compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (required for ngrok)
    allow_credentials=False,  # Must be False when using allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
triangulation_service = TriangulationService()
external_api_service = ExternalAPIService()

# =============================================================================
# HEALTH CHECK
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint - API status"""
    return {
        "service": settings.APP_NAME,
        "version": settings.API_VERSION,
        "status": "operational",
        "city": settings.CITY_NAME,
        "country": settings.COUNTRY
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# =============================================================================
# FIELD LOG ENDPOINTS (Data Collection)
# =============================================================================

@app.post("/api/v1/field-logs", response_model=FieldLogResponse, status_code=201)
async def create_field_log(
    log: FieldLogCreate,
    db = Depends(get_db)
):
    """
    Create a single field log entry from Android device
    """
    try:
        db_log = FieldLog(**log.dict())
        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        
        logger.info(f"Field log created: Cell ID {log.cell_id}, RSRP {log.rsrp}")
        return db_log
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating field log: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create field log: {str(e)}")

@app.post("/api/v1/field-logs/batch", status_code=201)
async def create_field_logs_batch(
    batch: FieldLogBatch,
    db = Depends(get_db)
):
    """
    Create multiple field log entries in a single request (batch upload)
    Optimized for mobile devices with queued data
    """
    try:
        created_count = 0
        failed_count = 0
        
        for log_data in batch.logs:
            try:
                db_log = FieldLog(**log_data.dict())
                db.add(db_log)
                created_count += 1
            except Exception as e:
                logger.warning(f"Failed to add log: {str(e)}")
                failed_count += 1
                continue
        
        db.commit()
        
        logger.info(f"Batch upload: {created_count} created, {failed_count} failed")
        
        return {
            "status": "success",
            "created": created_count,
            "failed": failed_count,
            "total": len(batch.logs)
        }
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error in batch upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch upload failed: {str(e)}")

@app.get("/api/v1/field-logs", response_model=List[FieldLogResponse])
async def get_field_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    enodeb_id: Optional[int] = None,
    network_type: Optional[str] = None,
    min_rsrp: Optional[int] = None,
    hours: int = Query(24, description="Get logs from last N hours"),
    db = Depends(get_db)
):
    """
    Retrieve field logs with optional filtering
    """
    query = db.query(FieldLog)
    
    # Time filter
    since = datetime.utcnow() - timedelta(hours=hours)
    query = query.filter(FieldLog.timestamp_utc >= since)
    
    # Optional filters
    if enodeb_id:
        query = query.filter(FieldLog.enodeb_id == enodeb_id)
    if network_type:
        query = query.filter(FieldLog.network_type == network_type)
    if min_rsrp:
        query = query.filter(FieldLog.rsrp >= min_rsrp)
    
    logs = query.order_by(FieldLog.timestamp_utc.desc()).offset(skip).limit(limit).all()
    return logs

# =============================================================================
# CELL TOWER ENDPOINTS (Triangulation Results)
# =============================================================================

@app.get("/api/v1/towers", response_model=List[CellTowerResponse])
async def get_cell_towers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    network_type: Optional[str] = None,
    min_confidence: Optional[float] = Query(None, ge=0, le=100),
    active_only: bool = True,
    db = Depends(get_db)
):
    """
    Retrieve cell towers with optional filtering
    """
    query = db.query(CellTower)
    
    if active_only:
        query = query.filter(CellTower.is_active == True)
    if network_type:
        query = query.filter(CellTower.network_type == network_type)
    if min_confidence:
        query = query.filter(CellTower.confidence_score >= min_confidence)
    
    towers = query.order_by(CellTower.last_updated.desc()).offset(skip).limit(limit).all()
    return towers

@app.get("/api/v1/towers/{enodeb_id}", response_model=CellTowerResponse)
async def get_tower_by_id(
    enodeb_id: int,
    db = Depends(get_db)
):
    """
    Get specific tower by eNodeB ID
    """
    tower = db.query(CellTower).filter(CellTower.enodeb_id == enodeb_id).first()
    if not tower:
        raise HTTPException(status_code=404, detail="Tower not found")
    return tower

@app.get("/api/v1/towers/{tower_id}/sectors", response_model=List[TowerSectorResponse])
async def get_tower_sectors(
    tower_id: int,
    db = Depends(get_db)
):
    """
    Get all sectors for a specific tower
    """
    sectors = db.query(TowerSector).filter(TowerSector.tower_id == tower_id).all()
    return sectors

# =============================================================================
# TRIANGULATION ENDPOINTS
# =============================================================================

@app.post("/api/v1/triangulation/calculate", response_model=TriangulationResponse)
async def calculate_tower_location(
    request: TriangulationRequest,
    db = Depends(get_db)
):
    """
    Calculate tower location using weighted centroid triangulation
    from field log data for a specific eNodeB
    """
    try:
        result = triangulation_service.triangulate_tower(db, request.enodeb_id)
        
        if not result:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data for triangulation. Need at least {settings.MIN_SAMPLES_FOR_TRIANGULATION} samples."
            )
        
        return result
    
    except Exception as e:
        logger.error(f"Triangulation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Triangulation failed: {str(e)}")

@app.post("/api/v1/triangulation/batch")
async def triangulate_all_towers(
    min_samples: int = Query(5, ge=3),
    db = Depends(get_db)
):
    """
    Run triangulation for all eNodeBs with sufficient field data
    """
    try:
        results = triangulation_service.batch_triangulate(db, min_samples)
        
        return {
            "status": "success",
            "towers_processed": len(results),
            "results": results
        }
    
    except Exception as e:
        logger.error(f"Batch triangulation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch triangulation failed: {str(e)}")

# =============================================================================
# HEATMAP / GEOSPATIAL ENDPOINTS
# =============================================================================

@app.get("/api/v1/heatmap/signal", response_model=SignalHeatmapResponse)
async def get_signal_heatmap(
    network_type: Optional[str] = None,
    hours: int = Query(24, ge=1, le=168),
    db = Depends(get_db)
):
    """
    Generate signal strength heatmap data (GeoJSON)
    """
    try:
        since = datetime.utcnow() - timedelta(hours=hours)
        
        query = db.query(
            FieldLog.location,
            FieldLog.rsrp,
            FieldLog.rssi,
            FieldLog.network_type,
            FieldLog.frequency_band
        ).filter(FieldLog.timestamp_utc >= since)
        
        if network_type:
            query = query.filter(FieldLog.network_type == network_type)
        
        logs = query.all()
        
        # Convert to GeoJSON format
        features = []
        for log in logs:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [log.location.x, log.location.y]
                },
                "properties": {
                    "rsrp": log.rsrp,
                    "rssi": log.rssi,
                    "network_type": log.network_type,
                    "band": log.frequency_band
                }
            })
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        return {
            "geojson": geojson,
            "point_count": len(features),
            "time_range_hours": hours
        }
    
    except Exception as e:
        logger.error(f"Heatmap generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Heatmap generation failed: {str(e)}")

# =============================================================================
# EXTERNAL API INTEGRATION
# =============================================================================

@app.post("/api/v1/external/seed-opencellid")
async def seed_from_opencellid(
    db = Depends(get_db)
):
    """
    Seed tower database from OpenCelliD API within city bounding box
    """
    try:
        result = await external_api_service.fetch_opencellid_data(
            mcc=515,
            mnc=3,
            bbox={
                "min_lat": settings.BBOX_MIN_LAT,
                "max_lat": settings.BBOX_MAX_LAT,
                "min_lon": settings.BBOX_MIN_LON,
                "max_lon": settings.BBOX_MAX_LON
            }
        )
        
        # Save to database
        imported_count = external_api_service.import_to_database(db, result, source="opencellid")
        
        return {
            "status": "success",
            "towers_imported": imported_count,
            "source": "OpenCelliD"
        }
    
    except Exception as e:
        logger.error(f"OpenCelliD import error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
