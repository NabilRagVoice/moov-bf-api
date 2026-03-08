import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Security
    API_KEY = os.getenv('API_KEY', 'moovbf-dev-key-2024')
    
    # CosmosDB
    COSMOS_ENDPOINT = os.getenv('COSMOS_ENDPOINT', 'https://moov-burkina-cosmos.documents.azure.com:443/')
    COSMOS_KEY = os.getenv('COSMOS_KEY')
    COSMOS_DATABASE = os.getenv('COSMOS_DATABASE', 'moov-db')
    
    # Containers
    CONTAINER_ACCORDS_HD = 'accords-internet'
    CONTAINER_ACCORDS_MOBILE = 'accords-mobile'
    CONTAINER_ACCORDS_MM = 'accords-moovmoney'
    CONTAINER_OFFRES = 'offres'
    CONTAINER_ACTIVITES = 'activites'
    
    # Azure Blob Storage
    STORAGE_CONNECTION_STRING = os.getenv('STORAGE_CONNECTION_STRING')
    STORAGE_CONTAINER = 'documents'
    
    # App settings
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
