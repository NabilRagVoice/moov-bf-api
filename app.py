"""
Moov Burkina Faso API
API de gestion des accords Haut Débit, Mobile et Moov Money
"""

import os
import uuid
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from azure.storage.blob import BlobServiceClient, ContentSettings

# ============================================
# CONFIGURATION
# ============================================

app = Flask(__name__)
CORS(app)

# Variables d'environnement
COSMOS_ENDPOINT = os.environ.get("COSMOS_ENDPOINT")
COSMOS_KEY = os.environ.get("COSMOS_KEY")
COSMOS_DATABASE = os.environ.get("COSMOS_DATABASE", "moovbf-db")
STORAGE_CONNECTION_STRING = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
STORAGE_CONTAINER = os.environ.get("STORAGE_CONTAINER", "documents")
API_KEY = os.environ.get("API_KEY", "dev-key-change-me")

# Clients Azure
cosmos_client = None
database = None
blob_service_client = None
container_client = None

# Collections CosmosDB
collections = {
    "accords_haut_debit": None,
    "accords_mobile": None,
    "accords_moov_money": None,
    "offres": None
}

# ============================================
# INITIALISATION
# ============================================

def init_cosmos():
    """Initialise la connexion CosmosDB"""
    global cosmos_client, database, collections
    
    if not COSMOS_ENDPOINT or not COSMOS_KEY:
        print("⚠️ CosmosDB non configuré - Mode demo")
        return False
    
    try:
        cosmos_client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        database = cosmos_client.get_database_client(COSMOS_DATABASE)
        
        for collection_name in collections.keys():
            collections[collection_name] = database.get_container_client(collection_name)
        
        print("✅ CosmosDB connecté")
        return True
    except Exception as e:
        print(f"❌ Erreur CosmosDB: {e}")
        return False

def init_storage():
    """Initialise la connexion Azure Blob Storage"""
    global blob_service_client, container_client
    
    if not STORAGE_CONNECTION_STRING:
        print("⚠️ Blob Storage non configuré - Mode demo")
        return False
    
    try:
        blob_service_client = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(STORAGE_CONTAINER)
        
        # Créer le container s'il n'existe pas
        try:
            container_client.create_container()
        except Exception:
            pass  # Container existe déjà
        
        print("✅ Blob Storage connecté")
        return True
    except Exception as e:
        print(f"❌ Erreur Blob Storage: {e}")
        return False

# ============================================
# MIDDLEWARE - AUTHENTIFICATION
# ============================================

def require_api_key(f):
    """Décorateur pour vérifier l'API Key"""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get("X-API-Key")
        if api_key != API_KEY:
            return jsonify({"error": "API Key invalide ou manquante"}), 401
        return f(*args, **kwargs)
    return decorated

# ============================================
# HELPERS
# ============================================

def generate_id():
    """Génère un ID unique"""
    return str(uuid.uuid4())

def get_timestamp():
    """Retourne le timestamp actuel"""
    return datetime.utcnow().isoformat()

def create_document_folder(accord_type, accord_id):
    """Crée un dossier pour les documents d'un accord dans Blob Storage"""
    if not container_client:
        return False
    
    try:
        # Créer un blob vide pour initialiser le "dossier"
        folder_path = f"{accord_type}/{accord_id}/.folder"
        blob_client = container_client.get_blob_client(folder_path)
        blob_client.upload_blob(b"", overwrite=True)
        return True
    except Exception as e:
        print(f"Erreur création dossier: {e}")
        return False

def get_required_documents(type_piece):
    """Retourne la liste des documents requis selon le type de pièce"""
    if type_piece == "CNI":
        return ["cni_recto", "cni_verso", "photo_profil"]
    elif type_piece == "PASSEPORT":
        return ["passeport", "photo_profil"]
    else:
        return ["photo_profil"]

def check_documents_complete(accord_type, accord_id, type_piece):
    """Vérifie si tous les documents requis sont présents"""
    if not container_client:
        return False, []
    
    required = get_required_documents(type_piece)
    uploaded = []
    
    try:
        prefix = f"{accord_type}/{accord_id}/"
        blobs = container_client.list_blobs(name_starts_with=prefix)
        
        for blob in blobs:
            filename = blob.name.replace(prefix, "").split(".")[0]
            if filename in required:
                uploaded.append(filename)
        
        missing = [doc for doc in required if doc not in uploaded]
        return len(missing) == 0, missing
    except Exception as e:
        print(f"Erreur vérification documents: {e}")
        return False, required

# ============================================
# CRUD GÉNÉRIQUE
# ============================================

def crud_list(collection_name):
    """Liste tous les documents d'une collection"""
    if not collections[collection_name]:
        return jsonify({"error": "Base de données non disponible"}), 503
    
    try:
        query = "SELECT * FROM c ORDER BY c.created_at DESC"
        items = list(collections[collection_name].query_items(query, enable_cross_partition_query=True))
        return jsonify({"data": items, "count": len(items)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def crud_get(collection_name, item_id):
    """Récupère un document par ID"""
    if not collections[collection_name]:
        return jsonify({"error": "Base de données non disponible"}), 503
    
    try:
        item = collections[collection_name].read_item(item_id, partition_key=item_id)
        return jsonify({"data": item}), 200
    except exceptions.CosmosResourceNotFoundError:
        return jsonify({"error": "Document non trouvé"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def crud_create(collection_name, data, accord_type=None):
    """Crée un nouveau document"""
    if not collections[collection_name]:
        return jsonify({"error": "Base de données non disponible"}), 503
    
    try:
        item_id = generate_id()
        data["id"] = item_id
        data["created_at"] = get_timestamp()
        data["updated_at"] = get_timestamp()
        data["statut"] = data.get("statut", "en_attente")
        data["documents_complets"] = False
        
        # Créer le dossier documents si c'est un accord
        if accord_type:
            folder_created = create_document_folder(accord_type, item_id)
            data["dossier_documents"] = f"{accord_type}/{item_id}"
            data["folder_created"] = folder_created
        
        collections[collection_name].create_item(data)
        return jsonify({"data": data, "message": "Créé avec succès"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def crud_update(collection_name, item_id, data):
    """Met à jour un document"""
    if not collections[collection_name]:
        return jsonify({"error": "Base de données non disponible"}), 503
    
    try:
        existing = collections[collection_name].read_item(item_id, partition_key=item_id)
        
        # Mettre à jour les champs
        for key, value in data.items():
            if key not in ["id", "created_at"]:
                existing[key] = value
        
        existing["updated_at"] = get_timestamp()
        
        collections[collection_name].replace_item(item_id, existing)
        return jsonify({"data": existing, "message": "Mis à jour avec succès"}), 200
    except exceptions.CosmosResourceNotFoundError:
        return jsonify({"error": "Document non trouvé"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def crud_delete(collection_name, item_id):
    """Supprime un document"""
    if not collections[collection_name]:
        return jsonify({"error": "Base de données non disponible"}), 503
    
    try:
        collections[collection_name].delete_item(item_id, partition_key=item_id)
        return jsonify({"message": "Supprimé avec succès"}), 200
    except exceptions.CosmosResourceNotFoundError:
        return jsonify({"error": "Document non trouvé"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# ENDPOINTS SYSTÈME
# ============================================

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    cosmos_status = "connected" if cosmos_client else "disconnected"
    storage_status = "connected" if blob_service_client else "disconnected"
    
    return jsonify({
        "status": "healthy",
        "timestamp": get_timestamp(),
        "services": {
            "cosmosdb": cosmos_status,
            "blob_storage": storage_status
        }
    }), 200

@app.route("/api/docs", methods=["GET"])
def api_docs():
    """Documentation de l'API"""
    return jsonify({
        "name": "Moov Burkina Faso API",
        "version": "1.0.0",
        "description": "API de gestion des accords Haut Débit, Mobile et Moov Money",
        "endpoints": {
            "système": [
                {"method": "GET", "path": "/api/health", "description": "Health check"},
                {"method": "GET", "path": "/api/docs", "description": "Documentation API"}
            ],
            "accords_haut_debit": [
                {"method": "GET", "path": "/api/accords-haut-debit", "description": "Liste les accords"},
                {"method": "GET", "path": "/api/accords-haut-debit/<id>", "description": "Détail d'un accord"},
                {"method": "POST", "path": "/api/accords-haut-debit", "description": "Créer un accord"},
                {"method": "PUT", "path": "/api/accords-haut-debit/<id>", "description": "Modifier un accord"},
                {"method": "DELETE", "path": "/api/accords-haut-debit/<id>", "description": "Supprimer un accord"}
            ],
            "accords_mobile": [
                {"method": "GET", "path": "/api/accords-mobile", "description": "Liste les accords"},
                {"method": "GET", "path": "/api/accords-mobile/<id>", "description": "Détail d'un accord"},
                {"method": "POST", "path": "/api/accords-mobile", "description": "Créer un accord"},
                {"method": "PUT", "path": "/api/accords-mobile/<id>", "description": "Modifier un accord"},
                {"method": "DELETE", "path": "/api/accords-mobile/<id>", "description": "Supprimer un accord"}
            ],
            "accords_moov_money": [
                {"method": "GET", "path": "/api/accords-moov-money", "description": "Liste les accords"},
                {"method": "GET", "path": "/api/accords-moov-money/<id>", "description": "Détail d'un accord"},
                {"method": "POST", "path": "/api/accords-moov-money", "description": "Créer un accord"},
                {"method": "PUT", "path": "/api/accords-moov-money/<id>", "description": "Modifier un accord"},
                {"method": "DELETE", "path": "/api/accords-moov-money/<id>", "description": "Supprimer un accord"}
            ],
            "offres": [
                {"method": "GET", "path": "/api/offres", "description": "Liste les offres"},
                {"method": "GET", "path": "/api/offres/<id>", "description": "Détail d'une offre"},
                {"method": "POST", "path": "/api/offres", "description": "Créer une offre"},
                {"method": "PUT", "path": "/api/offres/<id>", "description": "Modifier une offre"},
                {"method": "DELETE", "path": "/api/offres/<id>", "description": "Supprimer une offre"}
            ],
            "documents": [
                {"method": "GET", "path": "/api/documents/<accord_type>/<accord_id>", "description": "Liste les documents d'un accord"},
                {"method": "POST", "path": "/api/documents/<accord_type>/<accord_id>", "description": "Upload un document"},
                {"method": "GET", "path": "/api/documents/<accord_type>/<accord_id>/<filename>", "description": "Télécharger un document"},
                {"method": "DELETE", "path": "/api/documents/<accord_type>/<accord_id>/<filename>", "description": "Supprimer un document"}
            ]
        },
        "authentication": {
            "type": "API Key",
            "header": "X-API-Key"
        },
        "types_piece": {
            "CNI": "Carte Nationale d'Identité - Requiert: cni_recto, cni_verso, photo_profil",
            "PASSEPORT": "Passeport - Requiert: passeport, photo_profil"
        }
    }), 200

# ============================================
# ENDPOINTS ACCORDS HAUT DÉBIT
# ============================================

@app.route("/api/accords-haut-debit", methods=["GET"])
@require_api_key
def list_accords_haut_debit():
    """Liste tous les accords Haut Débit"""
    return crud_list("accords_haut_debit")

@app.route("/api/accords-haut-debit/<item_id>", methods=["GET"])
@require_api_key
def get_accord_haut_debit(item_id):
    """Récupère un accord Haut Débit par ID"""
    return crud_get("accords_haut_debit", item_id)

@app.route("/api/accords-haut-debit", methods=["POST"])
@require_api_key
def create_accord_haut_debit():
    """Crée un nouvel accord Haut Débit"""
    data = request.get_json()
    
    # Validation des champs requis
    required_fields = ["nom_client", "prenom_client", "telephone", "type_piece", "numero_piece", "adresse", "gps_latitude", "gps_longitude", "offre_id"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        return jsonify({"error": f"Champs requis manquants: {', '.join(missing)}"}), 400
    
    # Validation type_piece
    if data["type_piece"] not in ["CNI", "PASSEPORT"]:
        return jsonify({"error": "type_piece doit être 'CNI' ou 'PASSEPORT'"}), 400
    
    return crud_create("accords_haut_debit", data, accord_type="accords-haut-debit")

@app.route("/api/accords-haut-debit/<item_id>", methods=["PUT"])
@require_api_key
def update_accord_haut_debit(item_id):
    """Met à jour un accord Haut Débit"""
    data = request.get_json()
    return crud_update("accords_haut_debit", item_id, data)

@app.route("/api/accords-haut-debit/<item_id>", methods=["DELETE"])
@require_api_key
def delete_accord_haut_debit(item_id):
    """Supprime un accord Haut Débit"""
    return crud_delete("accords_haut_debit", item_id)

# ============================================
# ENDPOINTS ACCORDS MOBILE
# ============================================

@app.route("/api/accords-mobile", methods=["GET"])
@require_api_key
def list_accords_mobile():
    """Liste tous les accords Mobile"""
    return crud_list("accords_mobile")

@app.route("/api/accords-mobile/<item_id>", methods=["GET"])
@require_api_key
def get_accord_mobile(item_id):
    """Récupère un accord Mobile par ID"""
    return crud_get("accords_mobile", item_id)

@app.route("/api/accords-mobile", methods=["POST"])
@require_api_key
def create_accord_mobile():
    """Crée un nouvel accord Mobile"""
    data = request.get_json()
    
    # Validation des champs requis
    required_fields = ["nom_client", "prenom_client", "telephone", "type_piece", "numero_piece", "offre_id"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        return jsonify({"error": f"Champs requis manquants: {', '.join(missing)}"}), 400
    
    # Validation type_piece
    if data["type_piece"] not in ["CNI", "PASSEPORT"]:
        return jsonify({"error": "type_piece doit être 'CNI' ou 'PASSEPORT'"}), 400
    
    return crud_create("accords_mobile", data, accord_type="accords-mobile")

@app.route("/api/accords-mobile/<item_id>", methods=["PUT"])
@require_api_key
def update_accord_mobile(item_id):
    """Met à jour un accord Mobile"""
    data = request.get_json()
    return crud_update("accords_mobile", item_id, data)

@app.route("/api/accords-mobile/<item_id>", methods=["DELETE"])
@require_api_key
def delete_accord_mobile(item_id):
    """Supprime un accord Mobile"""
    return crud_delete("accords_mobile", item_id)

# ============================================
# ENDPOINTS ACCORDS MOOV MONEY
# ============================================

@app.route("/api/accords-moov-money", methods=["GET"])
@require_api_key
def list_accords_moov_money():
    """Liste tous les accords Moov Money"""
    return crud_list("accords_moov_money")

@app.route("/api/accords-moov-money/<item_id>", methods=["GET"])
@require_api_key
def get_accord_moov_money(item_id):
    """Récupère un accord Moov Money par ID"""
    return crud_get("accords_moov_money", item_id)

@app.route("/api/accords-moov-money", methods=["POST"])
@require_api_key
def create_accord_moov_money():
    """Crée un nouvel accord Moov Money"""
    data = request.get_json()
    
    # Validation des champs requis
    required_fields = ["nom_client", "prenom_client", "telephone", "type_piece", "numero_piece", "type_compte"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        return jsonify({"error": f"Champs requis manquants: {', '.join(missing)}"}), 400
    
    # Validation type_piece
    if data["type_piece"] not in ["CNI", "PASSEPORT"]:
        return jsonify({"error": "type_piece doit être 'CNI' ou 'PASSEPORT'"}), 400
    
    return crud_create("accords_moov_money", data, accord_type="accords-moov-money")

@app.route("/api/accords-moov-money/<item_id>", methods=["PUT"])
@require_api_key
def update_accord_moov_money(item_id):
    """Met à jour un accord Moov Money"""
    data = request.get_json()
    return crud_update("accords_moov_money", item_id, data)

@app.route("/api/accords-moov-money/<item_id>", methods=["DELETE"])
@require_api_key
def delete_accord_moov_money(item_id):
    """Supprime un accord Moov Money"""
    return crud_delete("accords_moov_money", item_id)

# ============================================
# ENDPOINTS OFFRES
# ============================================

@app.route("/api/offres", methods=["GET"])
@require_api_key
def list_offres():
    """Liste toutes les offres"""
    return crud_list("offres")

@app.route("/api/offres/<item_id>", methods=["GET"])
@require_api_key
def get_offre(item_id):
    """Récupère une offre par ID"""
    return crud_get("offres", item_id)

@app.route("/api/offres", methods=["POST"])
@require_api_key
def create_offre():
    """Crée une nouvelle offre"""
    data = request.get_json()
    
    # Validation des champs requis
    required_fields = ["nom", "type_offre", "prix", "description"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        return jsonify({"error": f"Champs requis manquants: {', '.join(missing)}"}), 400
    
    # Validation type_offre
    if data["type_offre"] not in ["haut_debit", "mobile", "moov_money"]:
        return jsonify({"error": "type_offre doit être 'haut_debit', 'mobile' ou 'moov_money'"}), 400
    
    return crud_create("offres", data)

@app.route("/api/offres/<item_id>", methods=["PUT"])
@require_api_key
def update_offre(item_id):
    """Met à jour une offre"""
    data = request.get_json()
    return crud_update("offres", item_id, data)

@app.route("/api/offres/<item_id>", methods=["DELETE"])
@require_api_key
def delete_offre(item_id):
    """Supprime une offre"""
    return crud_delete("offres", item_id)

# ============================================
# ENDPOINTS DOCUMENTS
# ============================================

@app.route("/api/documents/<accord_type>/<accord_id>", methods=["GET"])
@require_api_key
def list_documents(accord_type, accord_id):
    """Liste les documents d'un accord"""
    if not container_client:
        return jsonify({"error": "Blob Storage non disponible"}), 503
    
    try:
        prefix = f"{accord_type}/{accord_id}/"
        blobs = container_client.list_blobs(name_starts_with=prefix)
        
        documents = []
        for blob in blobs:
            if not blob.name.endswith(".folder"):
                documents.append({
                    "name": blob.name.replace(prefix, ""),
                    "size": blob.size,
                    "created": blob.creation_time.isoformat() if blob.creation_time else None,
                    "url": f"/api/documents/{accord_type}/{accord_id}/{blob.name.replace(prefix, '')}"
                })
        
        return jsonify({
            "accord_id": accord_id,
            "accord_type": accord_type,
            "documents": documents,
            "count": len(documents)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/documents/<accord_type>/<accord_id>", methods=["POST"])
@require_api_key
def upload_document(accord_type, accord_id):
    """Upload un document pour un accord"""
    if not container_client:
        return jsonify({"error": "Blob Storage non disponible"}), 503
    
    # Vérifier le type de document
    doc_type = request.form.get("type")
    valid_types = ["cni_recto", "cni_verso", "passeport", "photo_profil"]
    
    if not doc_type or doc_type not in valid_types:
        return jsonify({"error": f"Type de document invalide. Valeurs acceptées: {', '.join(valid_types)}"}), 400
    
    # Vérifier le fichier
    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier fourni"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Nom de fichier vide"}), 400
    
    # Déterminer l'extension
    extension = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "jpg"
    allowed_extensions = ["jpg", "jpeg", "png", "pdf"]
    
    if extension not in allowed_extensions:
        return jsonify({"error": f"Extension non autorisée. Valeurs acceptées: {', '.join(allowed_extensions)}"}), 400
    
    try:
        # Upload vers Blob Storage
        blob_name = f"{accord_type}/{accord_id}/{doc_type}.{extension}"
        blob_client = container_client.get_blob_client(blob_name)
        
        content_type = f"image/{extension}" if extension in ["jpg", "jpeg", "png"] else "application/pdf"
        
        blob_client.upload_blob(
            file.read(),
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type)
        )
        
        # Vérifier si tous les documents sont complets
        # Récupérer le type_piece depuis l'accord (simplifié ici)
        
        return jsonify({
            "message": "Document uploadé avec succès",
            "document": {
                "type": doc_type,
                "path": blob_name,
                "url": f"/api/documents/{accord_type}/{accord_id}/{doc_type}.{extension}"
            }
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/documents/<accord_type>/<accord_id>/<filename>", methods=["GET"])
@require_api_key
def download_document(accord_type, accord_id, filename):
    """Télécharge un document"""
    if not container_client:
        return jsonify({"error": "Blob Storage non disponible"}), 503
    
    try:
        blob_name = f"{accord_type}/{accord_id}/{filename}"
        blob_client = container_client.get_blob_client(blob_name)
        
        # Vérifier si le blob existe
        if not blob_client.exists():
            return jsonify({"error": "Document non trouvé"}), 404
        
        # Télécharger le contenu
        download_stream = blob_client.download_blob()
        content = download_stream.readall()
        
        # Déterminer le content-type
        extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        content_type = "application/pdf" if extension == "pdf" else f"image/{extension}"
        
        from flask import Response
        return Response(
            content,
            mimetype=content_type,
            headers={"Content-Disposition": f"inline; filename={filename}"}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/documents/<accord_type>/<accord_id>/<filename>", methods=["DELETE"])
@require_api_key
def delete_document(accord_type, accord_id, filename):
    """Supprime un document"""
    if not container_client:
        return jsonify({"error": "Blob Storage non disponible"}), 503
    
    try:
        blob_name = f"{accord_type}/{accord_id}/{filename}"
        blob_client = container_client.get_blob_client(blob_name)
        
        # Vérifier si le blob existe
        if not blob_client.exists():
            return jsonify({"error": "Document non trouvé"}), 404
        
        blob_client.delete_blob()
        
        return jsonify({"message": "Document supprimé avec succès"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# DÉMARRAGE
# ============================================

# Initialiser les connexions au démarrage
init_cosmos()
init_storage()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
