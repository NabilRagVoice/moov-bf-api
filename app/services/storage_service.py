from azure.storage.blob import BlobServiceClient, ContentSettings
import os
from datetime import datetime
import uuid

class StorageService:
    def __init__(self):
        connection_string = os.getenv('STORAGE_CONNECTION_STRING')
        self.blob_service = BlobServiceClient.from_connection_string(connection_string)
        self.container_name = 'documents'
        self.container_client = self.blob_service.get_container_client(self.container_name)
    
    def upload_document(self, accord_id, doc_type, file_data, content_type='image/jpeg'):
        """Upload a document to blob storage
        
        Args:
            accord_id: ID of the accord (used as folder name)
            doc_type: Type of document (cni_recto, cni_verso, photo)
            file_data: Binary file data
            content_type: MIME type of the file
        
        Returns:
            URL of the uploaded blob
        """
        # Determine file extension
        ext_map = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'application/pdf': '.pdf'
        }
        ext = ext_map.get(content_type, '.jpg')
        
        # Create blob path: {accord_id}/{doc_type}{ext}
        blob_name = f"{accord_id}/{doc_type}{ext}"
        
        blob_client = self.container_client.get_blob_client(blob_name)
        
        content_settings = ContentSettings(content_type=content_type)
        blob_client.upload_blob(
            file_data,
            overwrite=True,
            content_settings=content_settings
        )
        
        return blob_client.url
    
    def get_document_url(self, accord_id, doc_type):
        """Get the URL of a document"""
        # Try common extensions
        for ext in ['.jpg', '.png', '.pdf']:
            blob_name = f"{accord_id}/{doc_type}{ext}"
            blob_client = self.container_client.get_blob_client(blob_name)
            if blob_client.exists():
                return blob_client.url
        return None
    
    def list_documents(self, accord_id):
        """List all documents for an accord"""
        documents = []
        prefix = f"{accord_id}/"
        
        blobs = self.container_client.list_blobs(name_starts_with=prefix)
        for blob in blobs:
            doc_type = blob.name.replace(prefix, '').rsplit('.', 1)[0]
            documents.append({
                'type': doc_type,
                'name': blob.name,
                'url': f"{self.container_client.url}/{blob.name}",
                'size': blob.size,
                'last_modified': blob.last_modified.isoformat() if blob.last_modified else None
            })
        
        return documents
    
    def delete_document(self, accord_id, doc_type):
        """Delete a specific document"""
        for ext in ['.jpg', '.png', '.pdf']:
            blob_name = f"{accord_id}/{doc_type}{ext}"
            blob_client = self.container_client.get_blob_client(blob_name)
            if blob_client.exists():
                blob_client.delete_blob()
                return True
        return False
    
    def delete_accord_folder(self, accord_id):
        """Delete all documents for an accord"""
        prefix = f"{accord_id}/"
        blobs = self.container_client.list_blobs(name_starts_with=prefix)
        for blob in blobs:
            self.container_client.delete_blob(blob.name)

storage_service = StorageService()
