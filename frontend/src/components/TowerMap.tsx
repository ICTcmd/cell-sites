import React, { useEffect, useState } from 'react';
import Map, { Marker, Source, Layer, Popup } from 'react-map-gl';
import type { CircleLayer, HeatmapLayer } from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

// Replace with your Mapbox token
const MAPBOX_TOKEN = 'YOUR_MAPBOX_ACCESS_TOKEN';

// Band color mapping
const BAND_COLORS: Record<string, string> = {
  'B1': '#FF6B6B',    // Red
  'B3': '#4ECDC4',    // Teal
  'B5': '#45B7D1',    // Blue
  'B7': '#96CEB4',    // Green
  'B8': '#FFEAA7',    // Yellow
  'B28': '#DFE6E9',   // Gray
  'B41': '#A29BFE',   // Purple
  'N78': '#FD79A8',   // Pink (5G)
  'UNKNOWN': '#95A5A6' // Dark gray
};

interface Tower {
  id: number;
  enodeb_id: number;
  site_name?: string;
  network_type: string;
  latitude: number;
  longitude: number;
  confidence_score?: number;
  sample_count: number;
  is_active: boolean;
}

interface TowerMapProps {
  apiBaseUrl: string;
  initialCenter?: [number, number];
  initialZoom?: number;
}

const TowerMap: React.FC<TowerMapProps> = ({
  apiBaseUrl,
  initialCenter = [121.0244, 14.5995], // Manila default
  initialZoom = 12
}) => {
  const [towers, setTowers] = useState<Tower[]>([]);
  const [heatmapData, setHeatmapData] = useState<any>(null);
  const [selectedTower, setSelectedTower] = useState<Tower | null>(null);
  const [viewState, setViewState] = useState({
    longitude: initialCenter[0],
    latitude: initialCenter[1],
    zoom: initialZoom
  });
  const [showHeatmap, setShowHeatmap] = useState(true);
  const [selectedNetworkType, setSelectedNetworkType] = useState<string>('all');

  // Fetch towers
  useEffect(() => {
    fetchTowers();
  }, [selectedNetworkType]);

  // Fetch heatmap data
  useEffect(() => {
    if (showHeatmap) {
      fetchHeatmap();
    }
  }, [showHeatmap, selectedNetworkType]);

  const fetchTowers = async () => {
    try {
      let url = `${apiBaseUrl}/towers?limit=500`;
      if (selectedNetworkType !== 'all') {
        url += `&network_type=${selectedNetworkType}`;
      }
      
      const response = await fetch(url, {
        headers: {
          'ngrok-skip-browser-warning': 'true'
        }
      });
      const data = await response.json();
      setTowers(data);
    } catch (error) {
      console.error('Error fetching towers:', error);
    }
  };

  const fetchHeatmap = async () => {
    try {
      let url = `${apiBaseUrl}/heatmap/signal?hours=24`;
      if (selectedNetworkType !== 'all') {
        url += `&network_type=${selectedNetworkType}`;
      }
      
      const response = await fetch(url, {
        headers: {
          'ngrok-skip-browser-warning': 'true'
        }
      });
      const data = await response.json();
      setHeatmapData(data.geojson);
    } catch (error) {
      console.error('Error fetching heatmap:', error);
    }
  };

  // Heatmap layer style
  const heatmapLayer: HeatmapLayer = {
    id: 'signal-heatmap',
    type: 'heatmap',
    source: 'signal-heatmap',
    paint: {
      // Color gradient based on RSRP values
      'heatmap-weight': [
        'interpolate',
        ['linear'],
        ['get', 'rsrp'],
        -130, 0,
        -100, 0.5,
        -70, 1
      ],
      'heatmap-intensity': [
        'interpolate',
        ['linear'],
        ['zoom'],
        10, 0.5,
        15, 1
      ],
      'heatmap-color': [
        'interpolate',
        ['linear'],
        ['heatmap-density'],
        0, 'rgba(33,102,172,0)',
        0.2, 'rgb(103,169,207)',
        0.4, 'rgb(209,229,240)',
        0.6, 'rgb(253,219,199)',
        0.8, 'rgb(239,138,98)',
        1, 'rgb(178,24,43)'
      ],
      'heatmap-radius': [
        'interpolate',
        ['linear'],
        ['zoom'],
        10, 15,
        15, 30
      ],
      'heatmap-opacity': 0.7
    }
  };

  // Signal point layer (alternative to heatmap)
  const signalPointLayer: CircleLayer = {
    id: 'signal-points',
    type: 'circle',
    source: 'signal-points',
    paint: {
      'circle-radius': [
        'interpolate',
        ['linear'],
        ['zoom'],
        10, 3,
        15, 6
      ],
      'circle-color': [
        'interpolate',
        ['linear'],
        ['get', 'rsrp'],
        -130, '#d73027',
        -110, '#fc8d59',
        -90, '#fee090',
        -70, '#91cf60',
        -50, '#1a9850'
      ],
      'circle-opacity': 0.6
    }
  };

  const getTowerColor = (tower: Tower): string => {
    // Color by confidence score or use network type
    if (tower.confidence_score) {
      if (tower.confidence_score >= 80) return '#2ECC71'; // Green - high confidence
      if (tower.confidence_score >= 60) return '#F39C12'; // Orange - medium
      return '#E74C3C'; // Red - low confidence
    }
    return '#3498DB'; // Default blue
  };

  return (
    <div className="relative w-full h-full">
      {/* Map Controls */}
      <div className="absolute top-4 left-4 z-10 bg-white p-4 rounded-lg shadow-lg">
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Network Type
            </label>
            <select
              value={selectedNetworkType}
              onChange={(e) => setSelectedNetworkType(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="all">All Networks</option>
              <option value="2G">2G</option>
              <option value="3G">3G</option>
              <option value="4G">4G</option>
              <option value="5G">5G</option>
            </select>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="showHeatmap"
              checked={showHeatmap}
              onChange={(e) => setShowHeatmap(e.target.checked)}
              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <label htmlFor="showHeatmap" className="ml-2 block text-sm text-gray-700">
              Show Signal Heatmap
            </label>
          </div>

          <div>
            <p className="text-sm font-medium text-gray-700 mb-2">Frequency Bands</p>
            <div className="space-y-1">
              {Object.entries(BAND_COLORS).map(([band, color]) => (
                <div key={band} className="flex items-center text-xs">
                  <div
                    className="w-3 h-3 rounded-full mr-2"
                    style={{ backgroundColor: color }}
                  />
                  <span>{band}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Stats Panel */}
      <div className="absolute top-4 right-4 z-10 bg-white p-4 rounded-lg shadow-lg">
        <div className="text-sm space-y-2">
          <div>
            <span className="font-medium">Total Towers:</span> {towers.length}
          </div>
          <div>
            <span className="font-medium">Active:</span>{' '}
            {towers.filter(t => t.is_active).length}
          </div>
          <div>
            <span className="font-medium">Avg Confidence:</span>{' '}
            {towers.length > 0
              ? (towers.reduce((sum, t) => sum + (t.confidence_score || 0), 0) / towers.length).toFixed(1)
              : 'N/A'}%
          </div>
        </div>
      </div>

      {/* Mapbox Map */}
      <Map
        {...viewState}
        onMove={(evt) => setViewState(evt.viewState)}
        mapboxAccessToken={MAPBOX_TOKEN}
        style={{ width: '100%', height: '100%' }}
        mapStyle="mapbox://styles/mapbox/streets-v12"
      >
        {/* Signal Heatmap Layer */}
        {showHeatmap && heatmapData && (
          <Source id="signal-heatmap" type="geojson" data={heatmapData}>
            <Layer {...heatmapLayer} />
          </Source>
        )}

        {/* Tower Markers */}
        {towers.map((tower) => (
          <Marker
            key={tower.id}
            longitude={tower.longitude}
            latitude={tower.latitude}
            anchor="bottom"
            onClick={(e) => {
              e.originalEvent.stopPropagation();
              setSelectedTower(tower);
            }}
          >
            <div
              className="cursor-pointer transition-transform hover:scale-110"
              style={{
                width: '24px',
                height: '24px',
                borderRadius: '50%',
                backgroundColor: getTowerColor(tower),
                border: '3px solid white',
                boxShadow: '0 2px 4px rgba(0,0,0,0.3)'
              }}
            />
          </Marker>
        ))}

        {/* Tower Info Popup */}
        {selectedTower && (
          <Popup
            longitude={selectedTower.longitude}
            latitude={selectedTower.latitude}
            anchor="top"
            onClose={() => setSelectedTower(null)}
            closeButton={true}
            closeOnClick={false}
          >
            <div className="p-2">
              <h3 className="font-bold text-lg mb-2">
                {selectedTower.site_name || `Tower ${selectedTower.enodeb_id}`}
              </h3>
              <div className="space-y-1 text-sm">
                <div>
                  <span className="font-medium">eNodeB ID:</span> {selectedTower.enodeb_id}
                </div>
                <div>
                  <span className="font-medium">Network:</span> {selectedTower.network_type}
                </div>
                <div>
                  <span className="font-medium">Confidence:</span>{' '}
                  {selectedTower.confidence_score?.toFixed(1) || 'N/A'}%
                </div>
                <div>
                  <span className="font-medium">Samples:</span> {selectedTower.sample_count}
                </div>
                <div>
                  <span className="font-medium">Status:</span>{' '}
                  <span className={selectedTower.is_active ? 'text-green-600' : 'text-gray-500'}>
                    {selectedTower.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                <div className="text-xs text-gray-500 mt-2">
                  {selectedTower.latitude.toFixed(6)}, {selectedTower.longitude.toFixed(6)}
                </div>
              </div>
            </div>
          </Popup>
        )}
      </Map>
    </div>
  );
};

export default TowerMap;
