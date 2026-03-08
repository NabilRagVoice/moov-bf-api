from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError
import os
from datetime import datetime
import uuid

class CosmosService:
    def __init__(self):
        connection_string = os.getenv('COSMOS_CONNECTION_STRING')
        self.client = CosmosClient.from_connection_string(connection_string)
        self.database = self.client.get_database_client(os.getenv('COSMOS_DATABASE', 'moov-db'))
        
        # Containers
        self.accords_hd = self.database.get_container_client('accords-internet')
        self.accords_mobile = self.database.get_container_client('accords-mobile')
        self.accords_mm = self.database.get_container_client('accords-moovmoney')
        self.offres = self.database.get_container_client('offres')
        self.activites = self.database.get_container_client('activites')
    
    def generate_id(self, prefix):
        year = datetime.utcnow().strftime('%Y')
        unique = str(uuid.uuid4())[:8].upper()
        return f"{prefix}-{year}-{unique}"
    
    # Generic CRUD operations
    def create_item(self, container, item):
        item['date_creation'] = datetime.utcnow().isoformat()
        item['date_modification'] = datetime.utcnow().isoformat()
        return container.create_item(body=item)
    
    def get_item(self, container, item_id, partition_key):
        try:
            return container.read_item(item=item_id, partition_key=partition_key)
        except CosmosResourceNotFoundError:
            return None
    
    def update_item(self, container, item_id, partition_key, updates):
        item = self.get_item(container, item_id, partition_key)
        if not item:
            return None
        item.update(updates)
        item['date_modification'] = datetime.utcnow().isoformat()
        return container.replace_item(item=item_id, body=item)
    
    def delete_item(self, container, item_id, partition_key):
        try:
            container.delete_item(item=item_id, partition_key=partition_key)
            return True
        except CosmosResourceNotFoundError:
            return False
    
    def query_items(self, container, query, parameters=None):
        return list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
    
    def list_items(self, container, filters=None, page=1, page_size=20):
        query = "SELECT * FROM c WHERE 1=1"
        parameters = []
        
        if filters:
            if filters.get('statut'):
                query += " AND c.statut = @statut"
                parameters.append({'name': '@statut', 'value': filters['statut']})
            if filters.get('agent_id'):
                query += " AND c.agent.id = @agent_id"
                parameters.append({'name': '@agent_id', 'value': filters['agent_id']})
        
        query += " ORDER BY c.date_creation DESC"
        query += f" OFFSET {(page-1)*page_size} LIMIT {page_size}"
        
        return self.query_items(container, query, parameters)
    
    # Log activity
    def log_activity(self, action, entite_type, entite_id, agent_id, agent_nom, details=None):
        activity = {
            'id': str(uuid.uuid4()),
            'type': action,
            'action': action,
            'entite_type': entite_type,
            'entite_id': entite_id,
            'agent_id': agent_id,
            'agent_nom': agent_nom,
            'details': details or {},
            'date': datetime.utcnow().isoformat()
        }
        self.activites.create_item(body=activity)

cosmos_service = CosmosService()
