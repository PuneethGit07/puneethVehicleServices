import re
import json
from decimal import Decimal
from datetime import date, datetime
from functools import wraps
from flask import session, redirect, url_for, flash, jsonify, request

class CustomJSONEncoder(json.JSONEncoder):
    """
    JSON encoder for Decimal, date, datetime objects.
    """
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)

def json_response(data, status_code=200):
    """
    Return JSON response serialized with CustomJSONEncoder.
    """
    json_str = json.dumps(data, cls=CustomJSONEncoder)
    return json_str, status_code, {'Content-Type': 'application/json; charset=utf-8'}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'message': 'Authentication required. Please log in.'}), 401
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'message': 'Authentication required. Please log in.'}), 401
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login', next=request.path))
            
            user_role = session.get('role')
            if user_role not in allowed_roles:
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'message': 'Access forbidden: Insufficient permissions.'}), 403
                flash('You do not have permission to access that page.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))

def validate_phone(phone):
    pattern = r'^\+?[0-9]{10,15}$'
    clean = re.sub(r'[\s\-()]', '', phone)
    return bool(re.match(pattern, clean))

VALID_SERVICE_STATUSES = ['Pending', 'Approved', 'In Progress', 'Completed', 'Cancelled']
VALID_PAYMENT_STATUSES = ['Pending', 'Paid', 'Failed']
VALID_PAYMENT_METHODS = ['Cash', 'Credit/Debit Card', 'UPI / QR', 'Net Banking']
VALID_VEHICLE_TYPES = ['Sedan', 'SUV', 'Hatchback', 'Electric SUV', 'Motorcycle', 'Truck', 'Van', 'Luxury']

