from datetime import datetime
import uuid

def generate_id(prefix):
    """Generate unique ID with prefix"""
    year = datetime.utcnow().strftime('%Y')
    unique = str(uuid.uuid4())[:8].upper()
    return f"{prefix}-{year}-{unique}"

def get_timestamp():
    """Get current UTC timestamp"""
    return datetime.utcnow().isoformat() + 'Z'

def parse_pagination(request):
    """Parse pagination parameters"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)  # Max 100 per page
    offset = (page - 1) * per_page
    return page, per_page, offset

def build_response(data, page=1, per_page=20, total=None):
    """Build paginated response"""
    response = {
        'data': data,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'count': len(data)
        }
    }
    if total is not None:
        response['pagination']['total'] = total
        response['pagination']['pages'] = (total + per_page - 1) // per_page
    return response

def log_activity(container, action, entity_type, entity_id, agent_id, agent_nom, details=None):
    """Log an activity"""
    activity = {
        'id': generate_id('ACT'),
        'type': action,
        'action': action,
        'entity_type': entity_type,
        'entity_id': entity_id,
        'agent_id': agent_id,
        'agent_nom': agent_nom,
        'details': details or {},
        'date': get_timestamp()
    }
    container.create_item(activity)
    return activity
