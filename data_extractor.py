import requests
import geopandas as gpd
from shapely.geometry import Polygon
from config import LONDON_BBOX, HEIGHT_THRESHOLDS

class RealBuildingDataExtractor:
    # Exact real building data using Overpass API by OpenStreetMap
    def extract_buildings(self):
        print("Downloading OpenStreetMap data via Overpass API")
        overpass_url = "http://overpass-api.de/api/interpreter"
        query = f"""
        [out:json][timeout:60];
        way["building"]({LONDON_BBOX[0]},{LONDON_BBOX[1]},{LONDON_BBOX[2]},{LONDON_BBOX[3]});
        out geom;
        """

        try:
            response = requests.post(overpass_url, data=query, timeout=90)
            response.raise_for_status()
            data = response.json()
            
            buildings = []
            for element in data.get('elements', []):
                if element['type'] == 'way' and 'geometry' in element:
                    coords = [(node['lon'], node['lat']) for node in element['geometry']]
                    if len(coords) > 2:
                        # For unclosed polygons
                        if coords[0] != coords[-1]:
                            coords.append(coords[0])
                        
                        polygon = Polygon(coords)
                        if polygon.is_valid:
                            buildings.append({
                                'building_id': f"osm_{element['id']}",
                                'building_type': element.get('tags', {}).get('building', 'building'),
                                'height_m': self._parse_height(element.get('tags', {}).get('height')),
                                'floors': self._parse_floors(element.get('tags', {}).get('building:levels')),
                                'geometry': polygon
                            })
            
            gdf = gpd.GeoDataFrame(buildings, crs='EPSG:4326')
            print(f"Downloaded and processed {len(gdf)} buildings")
            return gdf
        
        except Exception as e:
            print(f"Overpass API query failed. {e}")
            raise

    # Process height from the dataset
    def _parse_height(self, height_str):
        if not height_str:
            return None
        try:
            clean_height = str(height_str).lower().replace('m', '').replace(' ', '').strip()
            return float(clean_height)
        except:
            return None

    # Process the number of floors from the dataset
    def _parse_floors(self, floors_str):
        if not floors_str:
            return None
        try:
            return int(float(floors_str))
        except:
            return None

    # Transform to EPSG:27700 (from EPSG:4326 for lat/lon) which is suitable to measure distances and heights
    def transform_buildings(self, gdf):
        gdf_projected = gdf.to_crs('EPSG:27700')
        
        gdf['footprint_area_m2'] = gdf_projected.geometry.area
        gdf['estimated_height_m'] = gdf.apply(self._estimate_height, axis=1)
        gdf['volume_m3'] = gdf['footprint_area_m2'] * gdf['estimated_height_m']
        gdf['height_category'] = gdf['estimated_height_m'].apply(self._categorise_height)
        
        # Filter incorrect values
        gdf = gdf[gdf['footprint_area_m2'] > 10]
        gdf = gdf[gdf['estimated_height_m'] > 2]
        return gdf

    def _estimate_height(self, row):
        if row['height_m'] and row['height_m'] > 0:
            return row['height_m']
        if row['floors'] and row['floors'] > 0:
            return row['floors'] * 3.5
        return 12.0

    def _categorise_height(self, height):
        if height < HEIGHT_THRESHOLDS['low_rise']:
            return 'low_rise'
        elif height < HEIGHT_THRESHOLDS['mid_rise']:
            return 'mid_rise'
        else:
            return 'high_rise'
