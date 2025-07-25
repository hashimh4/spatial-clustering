# PostgreSQL and PostGIS
import pandas as pd
from sqlalchemy import create_engine, text
from config import DB_CONFIG

class DatabaseManager:    
    def __init__(self):
        self.engine = None

    # Connect to the database    
    def connect(self):        
        try:
            # Connection string using .env
            conn_str = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
            self.engine = create_engine(conn_str)
            
            # Enable PostGIS extension
            with self.engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
                # conn.commit()
                
            print("Database connected")
            return True
            
        except Exception as e:
            print(f"Database connection failed. {e}")
            return False
    
    # Load GeoFrame to PostGIS
    def load_buildings(self, gdf):
        try:
            # Clean the dataset        
            gdf = gdf.copy()    
            gdf['building_type'] = gdf['building_type'].astype(str).str.strip().str.lower()
            gdf = gdf[~gdf['building_type'].isin(['no', 'nan', 'none', ''])]
            gdf['building_type'] = gdf['building_type'].replace('yes', 'unspecified')

            # Remake the database
            with self.engine.connect() as conn:
                conn.execute(text("DROP TABLE IF EXISTS london_buildings;"))
                # conn.commit()
            
            # Load API data
            gdf.to_postgis('london_buildings', self.engine, if_exists='replace', index=False)

            # Create spatial indexes
            with self.engine.begin() as conn:
                conn.execute(text("""
                    CREATE INDEX idx_buildings_geom ON london_buildings USING GIST (geometry);
                    CREATE INDEX idx_buildings_height ON london_buildings (height_m);
                    CREATE INDEX idx_buildings_type ON london_buildings (building_type);
                """))
                # conn.commit()
            
            return True
            
        except Exception as e:
            print(f"GeoFrame to PostGIS failed. {e}")
            return False
        
    def run_analysis(self):        
        queries = {
            'basic_stats': """
                SELECT 
                    COUNT(*) as total_buildings,
                    ROUND(AVG(height_m::numeric), 1) as avg_height_m,
                    ROUND(MAX(height_m::numeric), 1) as max_height_m,
                    ROUND(AVG(volume_m3::numeric), 0) as avg_volume_m3,
                    COUNT(DISTINCT building_type) as building_types
                FROM london_buildings;
            """,
            
            'height_distribution': """
                SELECT 
                    height_category,
                    COUNT(*) as building_count,
                    ROUND(AVG(height_m::numeric), 1) as avg_height,
                    ROUND(AVG(volume_m3::numeric), 1) as avg_volume,
                    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER()), 1) as percentage
                FROM london_buildings
                GROUP BY height_category
                ORDER BY avg_height;
            """,
            
            'building_types': """
                SELECT 
                    building_type,
                    COUNT(*) as count,
                    ROUND(AVG(height_m::numeric), 1) as avg_height,
                    ROUND(AVG(footprint_area_m2::numeric), 0) as avg_footprint_m2
                FROM london_buildings
                GROUP BY building_type
                ORDER BY count DESC;
            """,
            
            # Spatial clustering with DBSCAN
            'spatial_clusters': """
                WITH high_rise_clusters AS (
                    SELECT 
                        building_id,
                        height_m::numeric AS height_m,
                        building_type,
                        ST_ClusterDBSCAN(geometry, 0.002, 2) OVER() as cluster_id
                    FROM london_buildings
                    WHERE height_m::numeric > 40
                )
                SELECT 
                    cluster_id,
                    COUNT(*) as buildings_in_cluster,
                    ROUND(AVG(height_m), 1) as avg_cluster_height,
                    ROUND(MAX(height_m), 1) as tallest_in_cluster,
                    string_agg(DISTINCT building_type, ', ') as building_types
                FROM high_rise_clusters
                WHERE cluster_id IS NOT NULL
                GROUP BY cluster_id
                HAVING COUNT(*) >= 2
                ORDER BY buildings_in_cluster DESC;
            """
        }
        
        results = {}
        try:
            for name, query in queries.items():
                results[name] = pd.read_sql(query, self.engine)
            return results
            
        except Exception as e:
            print(f"SQL queries failed. {e}")
            return {}
    
    # Close database connection
    def close(self):
        if self.engine:
            self.engine.dispose()