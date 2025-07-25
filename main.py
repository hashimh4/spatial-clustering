import time
from database import DatabaseManager
from data_extractor import RealBuildingDataExtractor
from analyser import UrbanInsightsAnalyser
import sys
sys.stdout.reconfigure(encoding='utf-8')

class SmartCitiesPipeline:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.data_extractor = RealBuildingDataExtractor()
        self.analyser = UrbanInsightsAnalyser()
    
    # Full ETA and analysis
    def run_complete_pipeline(self):
        start_time = time.time()
        
        print("Analysis of Buildings in the City of London - Python and PostGIS with Real Data")
        print("=" * 60)

        try:
            # Connect the database
            if not self.db_manager.connect():
                return False
            
            # Extract data from Overpass API
            raw_buildings = self.data_extractor.extract_buildings()
            
            # Transform the data to measure heights
            transformed_buildings = self.data_extractor.transform_buildings(raw_buildings)
            
            # Load the data to the PostGIS database
            if not self.db_manager.load_buildings(transformed_buildings):
                return False
            
            # Perform spatial analysis
            analysis_results = self.db_manager.run_analysis()
            
            if not analysis_results:
                return False
            
            # Generate the urban planning insights
            insights_report = self.analyser.analysis(analysis_results)
            runtime = time.time() - start_time
            self.analyser.save_analysis_summary(analysis_results, runtime)
            
            # Results
            print(f"\nPipeline completed in {runtime:.1f} seconds")
            print(f"\n{insights_report}")
            return True
            
        except Exception as e:
            runtime = time.time() - start_time
            print(f"\n Pipeline failed after {runtime:.1f} seconds: {e}")
            return False
        
        finally:
            self.db_manager.close()

def main():    
    # Run the pipeline
    pipeline = SmartCitiesPipeline()
    success = pipeline.run_complete_pipeline()
    
    if not success:
        print(f"\nCheck the env file / ensure PostgreSQL is running.")

if __name__ == "__main__":
    main()