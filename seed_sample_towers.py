"""
Seed sample Smart Communications towers for Manila
Based on publicly known tower locations
"""
import psycopg2
from datetime import datetime

# Sample Smart Communications tower locations in Manila
# These are approximate locations based on public information
SAMPLE_TOWERS = [
    # Manila City
    {"enodeb_id": 101, "lat": 14.5995, "lon": 121.0244, "area": "Manila City Center", "network": "4G"},
    {"enodeb_id": 102, "lat": 14.5885, "lon": 121.0285, "area": "Ermita", "network": "4G"},
    {"enodeb_id": 103, "lat": 14.6042, "lon": 121.0225, "area": "Quiapo", "network": "4G"},
    
    # Makati
    {"enodeb_id": 201, "lat": 14.5547, "lon": 121.0244, "area": "Makati CBD", "network": "5G"},
    {"enodeb_id": 202, "lat": 14.5636, "lon": 121.0371, "area": "Rockwell", "network": "5G"},
    {"enodeb_id": 203, "lat": 14.5472, "lon": 121.0163, "area": "Ayala Avenue", "network": "4G"},
    
    # Quezon City
    {"enodeb_id": 301, "lat": 14.6760, "lon": 121.0437, "area": "Quezon City Hall", "network": "4G"},
    {"enodeb_id": 302, "lat": 14.6504, "lon": 121.0494, "area": "Cubao", "network": "4G"},
    {"enodeb_id": 303, "lat": 14.6407, "lon": 121.0696, "area": "Eastwood", "network": "5G"},
    
    # Pasig
    {"enodeb_id": 401, "lat": 14.5764, "lon": 121.0851, "area": "Ortigas Center", "network": "5G"},
    {"enodeb_id": 402, "lat": 14.5873, "lon": 121.0645, "area": "Kapitolyo", "network": "4G"},
    
    # Mandaluyong
    {"enodeb_id": 501, "lat": 14.5794, "lon": 121.0359, "area": "EDSA Crossing", "network": "4G"},
    {"enodeb_id": 502, "lat": 14.5833, "lon": 121.0496, "area": "Shaw Boulevard", "network": "4G"},
    
    # BGC (Taguig)
    {"enodeb_id": 601, "lat": 14.5504, "lon": 121.0471, "area": "BGC Central", "network": "5G"},
    {"enodeb_id": 602, "lat": 14.5553, "lon": 121.0515, "area": "Market Market", "network": "5G"},
    {"enodeb_id": 603, "lat": 14.5446, "lon": 121.0543, "area": "Serendra", "network": "4G"},
]

def seed_towers():
    """Seed sample towers into the database"""
    try:
        # Connect to database
        conn = psycopg2.connect(
            host="localhost",
            port=5433,
            database="cellsite_db",
            user="postgres",
            password="cellsite123"
        )
        cur = conn.cursor()
        
        inserted = 0
        
        for tower in SAMPLE_TOWERS:
            # Map network type
            network_map = {"2G": "2G", "3G": "3G", "4G": "4G", "5G": "5G"}
            network_type = network_map.get(tower["network"], "4G")
            
            # Insert tower
            cur.execute("""
                INSERT INTO cell_towers (
                    enodeb_id, mcc, mnc, network_type, location,
                    site_name, source, sample_count, confidence_score,
                    is_active, first_seen, last_updated
                )
                VALUES (%s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (enodeb_id) DO NOTHING
            """, (
                tower["enodeb_id"],
                515,  # MCC for Philippines
                3,    # MNC for Smart LTE/5G
                network_type,
                tower["lon"],
                tower["lat"],
                tower["area"],
                "seeded_sample",
                10,  # sample_count
                75.0,  # confidence_score
                True,  # is_active
                datetime.utcnow(),
                datetime.utcnow()
            ))
            
            if cur.rowcount > 0:
                inserted += 1
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Successfully seeded {inserted} Smart Communications towers!")
        print(f"📍 Locations: Manila, Makati, Quezon City, Pasig, Mandaluyong, BGC")
        print(f"🗺️  Refresh your browser at https://cell-sites.vercel.app to see the towers!")
        
    except Exception as e:
        print(f"❌ Error seeding towers: {str(e)}")

if __name__ == "__main__":
    seed_towers()
