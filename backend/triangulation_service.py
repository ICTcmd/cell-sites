"""
Triangulation Service
Implements weighted centroid algorithm for tower location estimation
"""
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from geoalchemy2.functions import ST_X, ST_Y, ST_Distance, ST_Transform, ST_SetSRID, ST_MakePoint
import logging

from models import FieldLog, CellTower, TowerSector
from config import settings

logger = logging.getLogger(__name__)

class TriangulationService:
    """Service for calculating tower locations from field measurements"""
    
    def __init__(self):
        self.min_samples = settings.MIN_SAMPLES_FOR_TRIANGULATION
        self.max_distance = settings.MAX_DISTANCE_FROM_TOWER_METERS
        self.rsrp_weight_exp = settings.RSRP_WEIGHT_EXPONENT
    
    def triangulate_tower(self, db: Session, enodeb_id: int) -> Optional[Dict]:
        """
        Calculate tower location using weighted centroid triangulation
        
        Algorithm:
        1. Fetch all field logs for this eNodeB
        2. Filter outliers and low-quality measurements
        3. Calculate weights based on signal strength (RSRP)
        4. Compute weighted centroid
        5. Calculate confidence score
        
        Weight formula: w = (RSRP / RSRP_min) ^ exponent
        Higher RSRP = closer to tower = higher weight
        """
        
        # Fetch field logs for this tower
        logs = db.query(
            ST_X(FieldLog.location).label('lon'),
            ST_Y(FieldLog.location).label('lat'),
            FieldLog.rsrp,
            FieldLog.gps_accuracy_meters,
            FieldLog.network_type,
            FieldLog.frequency_band
        ).filter(
            and_(
                FieldLog.enodeb_id == enodeb_id,
                FieldLog.rsrp.isnot(None),
                FieldLog.rsrp >= -130,  # Filter very weak signals
                FieldLog.gps_accuracy_meters <= 50  # Good GPS accuracy only
            )
        ).all()
        
        if len(logs) < self.min_samples:
            logger.warning(f"Insufficient samples for eNodeB {enodeb_id}: {len(logs)} < {self.min_samples}")
            return None
        
        # Convert to numpy arrays
        lons = np.array([log.lon for log in logs])
        lats = np.array([log.lat for log in logs])
        rsrps = np.array([log.rsrp for log in logs])
        
        # Remove outliers using IQR method on RSRP
        q1, q3 = np.percentile(rsrps, [25, 75])
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        mask = (rsrps >= lower_bound) & (rsrps <= upper_bound)
        lons = lons[mask]
        lats = lats[mask]
        rsrps = rsrps[mask]
        
        if len(lons) < self.min_samples:
            logger.warning(f"Insufficient samples after outlier removal for eNodeB {enodeb_id}")
            return None
        
        # Calculate weights based on RSRP
        # Normalize RSRP to positive values (shift by min)
        rsrp_normalized = rsrps - rsrps.min()
        
        # Avoid division by zero
        if rsrp_normalized.max() == 0:
            weights = np.ones_like(rsrp_normalized)
        else:
            # Higher RSRP = closer to tower = higher weight
            weights = np.power(rsrp_normalized / rsrp_normalized.max(), self.rsrp_weight_exp)
        
        # Calculate weighted centroid
        tower_lon = np.average(lons, weights=weights)
        tower_lat = np.average(lats, weights=weights)
        
        # Calculate confidence metrics
        confidence_score = self._calculate_confidence(lons, lats, rsrps, weights)
        
        # Calculate average distance error
        distances = self._haversine_distance(
            np.full_like(lons, tower_lat),
            np.full_like(lons, tower_lon),
            lats,
            lons
        )
        avg_error = np.mean(distances)
        
        # Update or create tower in database
        tower = db.query(CellTower).filter(CellTower.enodeb_id == enodeb_id).first()
        
        network_type = logs[0].network_type if logs else "4G"
        
        if tower:
            # Update existing
            tower.location = f'SRID=4326;POINT({tower_lon} {tower_lat})'
            tower.confidence_score = confidence_score
            tower.sample_count = len(lons)
            tower.avg_distance_error_meters = float(avg_error)
            tower.last_updated = datetime.utcnow()
            tower.source = 'triangulation'
        else:
            # Create new
            tower = CellTower(
                enodeb_id=enodeb_id,
                network_type=network_type,
                location=f'SRID=4326;POINT({tower_lon} {tower_lat})',
                confidence_score=confidence_score,
                sample_count=len(lons),
                avg_distance_error_meters=float(avg_error),
                source='triangulation',
                first_seen=datetime.utcnow()
            )
            db.add(tower)
        
        db.commit()
        db.refresh(tower)
        
        logger.info(f"Triangulated eNodeB {enodeb_id}: ({tower_lat:.6f}, {tower_lon:.6f}), "
                   f"confidence={confidence_score:.2f}%, samples={len(lons)}")
        
        return {
            "enodeb_id": enodeb_id,
            "latitude": tower_lat,
            "longitude": tower_lon,
            "confidence_score": confidence_score,
            "sample_count": len(lons),
            "avg_distance_error_meters": float(avg_error),
            "calculation_method": "weighted_centroid"
        }
    
    def batch_triangulate(self, db: Session, min_samples: int = 5) -> List[Dict]:
        """
        Run triangulation for all eNodeBs with sufficient data
        """
        # Get all eNodeBs with enough samples
        enodeb_ids = db.query(
            FieldLog.enodeb_id,
            func.count(FieldLog.id).label('count')
        ).filter(
            FieldLog.enodeb_id.isnot(None)
        ).group_by(
            FieldLog.enodeb_id
        ).having(
            func.count(FieldLog.id) >= min_samples
        ).all()
        
        results = []
        for row in enodeb_ids:
            try:
                result = self.triangulate_tower(db, row.enodeb_id)
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"Error triangulating eNodeB {row.enodeb_id}: {str(e)}")
                continue
        
        return results
    
    def _calculate_confidence(self, lons, lats, rsrps, weights) -> float:
        """
        Calculate confidence score (0-100) based on:
        - Sample count (more is better)
        - Spatial clustering (tighter is better)
        - RSRP variation (lower is better)
        """
        sample_count = len(lons)
        
        # Sample count factor (0-40 points)
        count_score = min(40, sample_count * 2)
        
        # Spatial clustering factor (0-40 points)
        # Lower standard deviation = tighter cluster = higher confidence
        lon_std = np.std(lons)
        lat_std = np.std(lats)
        spatial_spread = np.sqrt(lon_std**2 + lat_std**2)
        
        # Convert to meters approximately (1 degree ≈ 111km)
        spatial_spread_meters = spatial_spread * 111000
        
        # Normalize: 0m = 40 points, 500m+ = 0 points
        clustering_score = max(0, 40 * (1 - spatial_spread_meters / 500))
        
        # RSRP consistency factor (0-20 points)
        rsrp_std = np.std(rsrps)
        # Lower std = more consistent = higher confidence
        consistency_score = max(0, 20 * (1 - rsrp_std / 20))
        
        total_score = count_score + clustering_score + consistency_score
        
        return min(100, total_score)
    
    @staticmethod
    def _haversine_distance(lat1, lon1, lat2, lon2):
        """
        Calculate distance between coordinates using Haversine formula
        Returns distance in meters
        """
        R = 6371000  # Earth radius in meters
        
        phi1 = np.radians(lat1)
        phi2 = np.radians(lat2)
        delta_phi = np.radians(lat2 - lat1)
        delta_lambda = np.radians(lon2 - lon1)
        
        a = np.sin(delta_phi/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return R * c
