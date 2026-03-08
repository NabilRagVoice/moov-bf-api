"""
Connexion à CosmosDB et Azure Blob Storage
"""
from azure.cosmos import CosmosClient, PartitionKey
from azure.storage.blob import BlobServiceClient, ContentSettings
from config import Config
import uuid
from datetime import datetime

# Initialisation CosmosDB
cosmos_client = None
database = None
containers = {}

def init_cosmos():
    """Initialise la connexion CosmosDB"""
    global cosmos_client, database, containers
    
    cosmos_client = CosmosClient(Config.COSMOS_ENDPOINT, Config.COSMOS_KEY)
    database = cosmos_client.get_database_client(Config.COSMOS_DATABASE)
    
    containers['accords_hd'] = database.get_container_client(Config.COLLECTION_ACCORDS_HD)
    containers['accords_mobile'] = database.get_container_client(Config.COLLECTION_ACCORDS_MOBILE)
    containers['accords_mm'] = database.get_container_client(Config.COLLECTION_ACCORDS_MM)
    containers['offres'] = database.get_container_client(Config.COLLECTION_OFFRES)
    containers['activites'] = database.get_container_client(Config.COLLECTION_ACTIVITES)
    
    return containers

def get_container(name):
    """Récupère un container par son nom"""
    if not containers:
        init_cosmos()
    return containers.get(name)

# Initialisation Blob Storage
blob_service_client = None
blob_container_client = None

def init_blob_storage():
    """Initialise la connexion Blob Storage"""
    global blob_service_client, blob_container_client
    
    blob_service_client = BlobServiceClient.from_connection_string(Config.STORAGE_CONNECTION_STRING)
    blob_container_client = blob_service_client.get_container_client(Config.STORAGE_CONTAINER)
    
    return blob_container_client

def get_blob_container():
    """Récupère le container blob"""
    if not blob_container_client:
        init_blob_storage()
    return blob_container_client

def upload_document(accord_id, file_type, file_data, content_type='image/jpeg'):
    """
    Upload un document dans le dossier de l'accord
    
    Args:
        accord_id: ID de l'accord (ex: HD-2024-00001)
        file_type: Type de fichier (cni_recto, cni_verso, photo)
        file_data: Données binaires du fichier
        content_type: Type MIME du fichier
    
    Returns:
        URL du fichier uploadé
    """
    container = get_blob_container()
    
    # Déterminer l'extension
    ext = 'jpg' if 'jpeg' in content_type or 'jpg' in content_type else 'png'
    blob_name = f"{accord_id}/{file_type}.{ext}"
    
    # Upload
    blob_client = container.get_blob_client(blob_name)
    blob_client.upload_blob(
        file_data,
        overwrite=True,
        content_settings=ContentSettings(content_type=content_type)
    )
    
    return blob_client.url

def delete_document(accord_id, file_type):
    """Supprime un document"""
    container = get_blob_container()
    
    # Essayer les deux extensions
    for ext in ['jpg', 'png']:
        blob_name = f"{accord_id}/{file_type}.{ext}"
        blob_client = container.get_blob_client(blob_name)
        try:
            blob_client.delete_blob()
            return True
        except:
            continue
    return False

def list_documents(accord_id):
    """Liste les documents d'un accord"""
    container = get_blob_container()
    blobs = container.list_blobs(name_starts_with=f"{accord_id}/")
    
    documents = []
    for blob in blobs:
        documents.append({
            'name': blob.name.split('/')[-1],
            'url': f"{container.url}/{blob.name}",
            'size': blob.size,
            'last_modified': blob.last_modified.isoformat() if blob.last_modified else None
        })
    
    return documents

def generate_id(prefix):
    """Génère un ID unique avec préfixe"""
    now = datetime.utcnow()
    year = now.strftime('%Y')
    unique = str(uuid.uuid4())[:8].upper()
    return f"{prefix}-{year}-{unique}"

def log_activity(action, entity_type, entity_id, agent_id, agent_nom, details=None):
    """Enregistre une activité dans le journal d'audit"""
    container = get_container('activites')
    
    activity = {
        'id': generate_id('ACT'),
        'type': action,
        'action': action,
        'entite_type': entity_type,
        'entite_id': entity_id,
        'agent_id': agent_id,
        'agent_nom': agent_nom,
        'details': details or {},
        'date': datetime.utcnow().isoformat() + 'Z'
    }
    
    container.create_item(activity)
    return activity
