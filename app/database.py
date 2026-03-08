from azure.cosmos import CosmosClient, PartitionKey
from flask import g, current_app

cosmos_client = None
database = None
containers = {}

def init_cosmos_db(app):
    global cosmos_client, database, containers
    
    cosmos_client = CosmosClient(
        app.config['COSMOS_ENDPOINT'],
        credential=app.config['COSMOS_KEY']
    )
    database = cosmos_client.get_database_client(app.config['COSMOS_DATABASE'])
    
    containers['accords_hd'] = database.get_container_client(app.config['CONTAINER_ACCORDS_HD'])
    containers['accords_mobile'] = database.get_container_client(app.config['CONTAINER_ACCORDS_MOBILE'])
    containers['accords_mm'] = database.get_container_client(app.config['CONTAINER_ACCORDS_MM'])
    containers['offres'] = database.get_container_client(app.config['CONTAINER_OFFRES'])
    containers['activites'] = database.get_container_client(app.config['CONTAINER_ACTIVITES'])

def get_container(name):
    return containers.get(name)
