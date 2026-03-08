from azure.storage.blob import BlobServiceClient, ContentSettings
from flask import current_app
import uuid

blob_service_client = None
container_client = None

def init_blob_storage(app):
    global blob_service_client, container_client
    
    connection_string = app.config['STORAGE_CONNECTION_STRING']
    if connection_string:
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(app.config['STORAGE_CONTAINER'])

def upload_document(accord_id, file, doc_type):
    """Upload un document dans le dossier de l'accord"""
    if not container_client:
        raise Exception('Storage not configured')
    
    # Determine extension
    filename = file.filename
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'jpg'
    
    # Create blob path: {accord_id}/{doc_type}.{ext}
    blob_name = f"{accord_id}/{doc_type}.{ext}"
    
    # Determine content type
    content_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'pdf': 'application/pdf'
    }
    content_type = content_types.get(ext, 'application/octet-stream')
    
    # Upload
    blob_client = container_client.get_blob_client(blob_name)
    blob_client.upload_blob(
        file.read(),
        overwrite=True,
        content_settings=ContentSettings(content_type=content_type)
    )
    
    return blob_client.url

def get_document_url(accord_id, doc_type):
    """Get URL of a document"""
    if not container_client:
        return None
    
    # List blobs in accord folder to find the document
    prefix = f"{accord_id}/{doc_type}"
    blobs = list(container_client.list_blobs(name_starts_with=prefix))
    
    if blobs:
        blob_client = container_client.get_blob_client(blobs[0].name)
        return blob_client.url
    return None

def list_documents(accord_id):
    """List all documents for an accord"""
    if not container_client:
        return []
    
    prefix = f"{accord_id}/"
    blobs = container_client.list_blobs(name_starts_with=prefix)
    
    documents = []
    for blob in blobs:
        doc_type = blob.name.replace(prefix, '').rsplit('.', 1)[0]
        blob_client = container_client.get_blob_client(blob.name)
        documents.append({
            'type': doc_type,
            'url': blob_client.url,
            'size': blob.size,
            'last_modified': blob.last_modified.isoformat() if blob.last_modified else None
        })
    
    return documents

def delete_document(accord_id, doc_type):
    """Delete a document"""
    if not container_client:
        return False
    
    prefix = f"{accord_id}/{doc_type}"
    blobs = list(container_client.list_blobs(name_starts_with=prefix))
    
    for blob in blobs:
        container_client.delete_blob(blob.name)
    
    return len(blobs) > 0
