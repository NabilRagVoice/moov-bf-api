from flask import Blueprint, jsonify
from datetime import datetime

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'moov-bf-api',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }), 200
