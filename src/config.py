import os 

# base directories
DATA_PATH = os.get('DATA_PATH', './data')
MODEL_PATH = os.get('MODEL_PATH', './models')
OUTPUT_PATH = os.get('OUTPUT_PATH', './OUTPUT_PATH')
API_DATA_PATH = os.getenv('API_DATA_PATH', './api/data')

# subdirectories
STAGING_PATH = os.path.join(DATA_PATH, 'staging')
PROCESSED_PATH = os.path.join(DATA_PATH, 'processed')
MODELS_DIR = MODEL_PATH
OUTPUT_DIR = OUTPUT_PATH
API_DATA_DIR = API_DATA_PATH