from functools import wraps
from flask import request, jsonify, current_app

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'error': 'API key required', 'code': 'MISSING_API_KEY'}), 401
        
        if api_key != current_app.config['API_KEY']:
            return jsonify({'error': 'Invalid API key', 'code': 'INVALID_API_KEY'}), 403
        
        return f(*args, **kwargs)
    return decorated

def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        role = request.headers.get('X-Role', 'agent')
        
        if not api_key or api_key != current_app.config['API_KEY']:
            return jsonify({'error': 'Invalid API key', 'code': 'INVALID_API_KEY'}), 403
        
        if role != 'admin':
            return jsonify({'error': 'Admin access required', 'code': 'ADMIN_REQUIRED'}), 403
        
        return f(*args, **kwargs)
    return decorated
