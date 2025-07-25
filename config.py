# Define .env values
import os
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'vucity'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'password')
}

# City of London bounding box
LONDON_BBOX = (
    float(os.getenv('BBOX_SOUTH', 51.51)),
    float(os.getenv('BBOX_WEST', -0.11)),
    float(os.getenv('BBOX_NORTH', 51.53)),
    float(os.getenv('BBOX_EAST', -0.07))
)

# Urban planning building height categories
HEIGHT_THRESHOLDS = {
    'low_rise': 9,    # Under 9m
    'mid_rise': 30,    # 9-30m  
    'high_rise': None  # Over 30m
}