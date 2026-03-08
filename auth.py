"""
Authentification par API Key
"""
from functools import wraps
from flask import request, jsonify
from config import Config

def require_api_key(f):
    """Décorateur pour protéger les endpoints avec API Key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({
                'error': 'API Key manquante',
                'message': "Header 'X-API-Key' requis"
            }), 401
        
        if api_key != Config.API_KEY:
            return jsonify({
                'error': 'API Key invalide',
                'message': 'Clé API non reconnue'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def get_agent_from_request():
    """Récupère les infos de l'agent depuis les headers"""
    return {
        'id': request.headers.get('X-Agent-Id', 'UNKNOWN'),
        'nom': request.headers.get('X-Agent-Nom', 'Agent Inconnu')
    }
