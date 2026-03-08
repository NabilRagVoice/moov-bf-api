"""
Configuration de l'application Moov BF API
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration principale"""
    
    # CosmosDB
    COSMOS_ENDPOINT = os.getenv('COSMOS_ENDPOINT', 'https://moov-burkina-cosmos.documents.azure.com:443/')
    COSMOS_KEY = os.getenv('COSMOS_KEY')
    COSMOS_DATABASE = os.getenv('COSMOS_DATABASE', 'moov-db')
    
    # Collections CosmosDB
    COLLECTION_ACCORDS_HD = 'accords-internet'
    COLLECTION_ACCORDS_MOBILE = 'accords-mobile'
    COLLECTION_ACCORDS_MM = 'accords-moovmoney'
    COLLECTION_OFFRES = 'offres'
    COLLECTION_ACTIVITES = 'activites'
    
    # Azure Blob Storage
    STORAGE_CONNECTION_STRING = os.getenv('STORAGE_CONNECTION_STRING')
    STORAGE_CONTAINER = 'documents'
    
    # API Security
    API_KEY = os.getenv('API_KEY', 'moovbf-dev-key-2024')
    
    # App Settings
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    PORT = int(os.getenv('PORT', 5000))
