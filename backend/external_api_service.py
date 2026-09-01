"""
External API Service
Integrates with OpenCelliD and CellMapper for tower data
"""
import httpx
import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from models import CellTower
from config import settings

logger = logging.getLogger(__name__)

class ExternalAPIService:
    """Service for fetching tower data from external APIs"""
    
    def __init__(self):
        self.opencellid_base = "https://opencellid.org/ajax"
        self.timeout = 30.0
    
    async def fetch_opencellid_data(
        self,
        mcc: int,
        mnc: int,
        bbox: Dict[str, float]
    ) -> List[Dict]:
        """
        Fetch tower data from OpenCelliD API
        
        API Docs: https://wiki.opencellid.org/wiki/API
        """
        if not settings.OPENCELLID_API_KEY:
            logger.warning("OpenCelliD API key not configured")
            return []
        
        url = f"{self.opencellid_base}/searchCell.php"
        
        params = {
            "key": settings.OPENCELLID_API_KEY,
            "mcc": mcc,
            "mnc": mnc,
            "format": "json",
            "bbox": f"{bbox['min_lon']},{bbox['min_lat']},{bbox['max_lon']},{bbox['max_lat']}"
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if "cells" in data:
                    logger.info(f"Fetched {len(data['cells'])} cells from OpenCelliD")
                    return data["cells"]
                
                return []
        
        except httpx.HTTPError as e:
            logger.error(f"OpenCelliD API error: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching OpenCelliD data: {str(e)}")
            return []
    
    def import_to_database(self, db: Session, api_data: List[Dict], source: str) -> int:
        """
        Import tower data from external API into database
        """
        imported_count = 0
        
        for cell in api_data:
            try:
                # Check if tower already exists
                enodeb_id = cell.get("cell")  # or "cid" depending on API
                
                if not enodeb_id:
                    continue
                
                existing = db.query(CellTower).filter(CellTower.enodeb_id == enodeb_id).first()
                
                if existing:
                    # Update only if from external source (don't overwrite triangulated data)
                    if existing.source != 'triangulation':
                        existing.location = f"SRID=4326;POINT({cell['lon']} {cell['lat']})"
                        existing.last_updated = datetime.utcnow()
                else:
                    # Create new tower
                    tower = CellTower(
                        enodeb_id=enodeb_id,
                        mcc=cell.get("mcc", 515),
                        mnc=cell.get("mnc", 3),
                        network_type=self._map_network_type(cell.get("radio", "LTE")),
                        location=f"SRID=4326;POINT({cell['lon']} {cell['lat']})",
                        source=source,
                        external_id=str(cell.get("cellid", "")),
                        sample_count=cell.get("samples", 0),
                        confidence_score=50.0,  # Default for external data
                        first_seen=datetime.utcnow()
                    )
                    db.add(tower)
                
                imported_count += 1
            
            except Exception as e:
                logger.error(f"Error importing cell data: {str(e)}")
                continue
        
        db.commit()
        logger.info(f"Imported {imported_count} towers from {source}")
        
        return imported_count
    
    @staticmethod
    def _map_network_type(radio: str) -> str:
        """Map external API radio type to our network type enum"""
        mapping = {
            "GSM": "2G",
            "UMTS": "3G",
            "LTE": "4G",
            "NR": "5G"
        }
        return mapping.get(radio.upper(), "4G")
