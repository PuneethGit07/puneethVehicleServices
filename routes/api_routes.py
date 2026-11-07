import os
from decimal import Decimal
from datetime import datetime, date
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.utils import secure_filename
from db import query_db, execute_db, get_db_connection
from utils import (
    json_response, login_required, role_required,
    validate_email, validate_phone,
    VALID_SERVICE_STATUSES, VALID_PAYMENT_STATUSES,
    VALID_PAYMENT_METHODS, VALID_VEHICLE_TYPES
)

api_bp = Blueprint('api', __name__, url_prefix='/api')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==============================================================================
# DASHBOARD STATS API
# ==============================================================================
@api_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    """
    Returns dashboard statistics:
    Total Customers, Total Vehicles, Total Services,
    Pending Services, Completed Services, Total Revenue.
    Plus status breakdown and monthly trends for Chart.js.
    """
    try:
        # Metrics
        total_customers = query_db("SELECT COUNT(*) AS count FROM customers", one=True)['count']
        total_vehicles = query_db("SELECT COUNT(*) AS count FROM vehicles", one=True)['count']
        total_services = query_db("SELECT COUNT(*) AS count FROM services", one=True)['count']
        pending_services = query_db("SELECT COUNT(*) AS count FROM services WHERE status = 'Pending'", one=True)['count']
        in_progress_services = query_db("SELECT COUNT(*) AS count FROM services WHERE status = 'In Progress'", one=True)['count']
        completed_services = query_db("SELECT COUNT(*) AS count FROM services WHERE status = 'Completed'", one=True)['count']
        
        rev_row = query_db("SELECT COALESCE(SUM(amount), 0) AS total FROM payments WHERE status = 'Paid'", one=True)
        total_revenue = float(rev_row['total']) if rev_row else 0.0

        # Status breakdown for doughnut chart
        status_dist = query_db("""
            SELECT status, COUNT(*) AS count 
            FROM services 
            GROUP BY status
        """)

        # Service types breakdown
        service_types_dist = query_db("""
            SELECT service_type, COUNT(*) AS count 
            FROM services 
            GROUP BY service_type 
            ORDER BY count DESC 
            LIMIT 6
        """)

        # Recent 6 months revenue for bar/line chart
        monthly_revenue = query_db("""
            SELECT 
                DATE_FORMAT(payment_date, '%%b %%Y') AS month_label,
                DATE_FORMAT(payment_date, '%%Y-%%m') AS month_sort,
                SUM(amount) AS total
            FROM payments
            WHERE status = 'Paid'
            GROUP BY month_sort, month_label
            ORDER BY month_sort DESC
            LIMIT 6
        """)
        monthly_revenue = list(reversed(monthly_revenue))

        # Recent activities
        recent_services = query_db("""
            SELECT s.service_id, s.service_type, s.service_date, s.status, s.service_charge,
                   v.vehicle_number, v.vehicle_model, c.name AS customer_name
            FROM services s
            JOIN vehicles v ON s.vehicle_id = v.vehicle_id
            JOIN customers c ON v.customer_id = c.customer_id
            ORDER BY s.created_at DESC
            LIMIT 5
        """)

        return json_response({
            'success': True,
            'stats': {
                'total_customers': total_customers,
                'total_vehicles': total_vehicles,
                'total_services': total_services,
                'pending_services': pending_services,
                'in_progress_services': in_progress_services,
                'completed_services': completed_services,
                'total_revenue': total_revenue
            },
            'charts': {
                'status_distribution': status_dist,
                'service_types': service_types_dist,
                'monthly_revenue': monthly_revenue
            },
            'recent_services': recent_services
        })
    except Exception as e:
        return json_response({'success': False, 'message': str(e)}, 500)

# ==============================================================================
# MECHANICS LIST API
# ==============================================================================
@api_bp.route('/mechanics', methods=['GET'])
@login_required
def get_mechanics():
    mechanics = query_db("""
        SELECT user_id, full_name, username, phone, email 
        FROM users 
        WHERE role = 'mechanic' 
        ORDER BY full_name ASC
    """)
    return json_response({'success': True, 'mechanics': mechanics})

# ==============================================================================
# CUSTOMERS API
# ==============================================================================
@api_bp.route('/customers', methods=['GET'])
@login_required
def get_customers():
    # If customer role, only return their own profile
    if session.get('role') == 'customer':
        cust_id = session.get('customer_id')
        customer = query_db("SELECT * FROM customers WHERE customer_id = %s", (cust_id,), one=True)
        return json_response({'success': True, 'customers': [customer] if customer else []})

    search = request.args.get('search', '').strip()
    if search:
        search_pattern = f"%{search}%"
        customers = query_db("""
            SELECT c.*, 
                   COUNT(DISTINCT v.vehicle_id) AS total_vehicles,
                   COUNT(DISTINCT s.service_id) AS total_services
            FROM customers c
            LEFT JOIN vehicles v ON c.customer_id = v.customer_id
            LEFT JOIN services s ON v.vehicle_id = s.vehicle_id
            WHERE c.name LIKE %s OR c.phone LIKE %s OR c.email LIKE %s
            GROUP BY c.customer_id
            ORDER BY c.created_at DESC
        """, (search_pattern, search_pattern, search_pattern))
    else:
        customers = query_db("""
            SELECT c.*, 
                   COUNT(DISTINCT v.vehicle_id) AS total_vehicles,
                   COUNT(DISTINCT s.service_id) AS total_services
            FROM customers c
            LEFT JOIN vehicles v ON c.customer_id = v.customer_id
            LEFT JOIN services s ON v.vehicle_id = s.vehicle_id
            GROUP BY c.customer_id
            ORDER BY c.created_at DESC
        """)
    return json_response({'success': True, 'customers': customers})

@api_bp.route('/customers/<int:customer_id>', methods=['GET'])
@login_required
def get_customer(customer_id):
    if session.get('role') == 'customer' and session.get('customer_id') != customer_id:
        return json_response({'success': False, 'message': 'Access denied.'}, 403)

    customer = query_db("SELECT * FROM customers WHERE customer_id = %s", (customer_id,), one=True)
    if not customer:
        return json_response({'success': False, 'message': 'Customer not found.'}, 404)

    vehicles = query_db("SELECT * FROM vehicles WHERE customer_id = %s ORDER BY created_at DESC", (customer_id,))
    return json_response({'success': True, 'customer': customer, 'vehicles': vehicles})

@api_bp.route('/customers', methods=['POST'])
@login_required
def create_customer():
    # Only Admin or Staff can create customer records directly via this endpoint
    if session.get('role') not in ['admin']:
        return json_response({'success': False, 'message': 'Unauthorized action.'}, 403)

    data = request.get_json() or request.form
    name = (data.get('name') or '').strip()
    phone = (data.get('phone') or '').strip()
    email = (data.get('email') or '').strip().lower()
    address = (data.get('address') or '').strip()

    if not name or not phone or not email:
        return json_response({'success': False, 'message': 'Name, phone, and email are required.'}, 400)

    if not validate_email(email):
        return json_response({'success': False, 'message': 'Invalid email format.'}, 400)

    if not validate_phone(phone):
        return json_response({'success': False, 'message': 'Invalid phone number format.'}, 400)

    existing = query_db("SELECT customer_id FROM customers WHERE email = %s OR phone = %s", (email, phone), one=True)
    if existing:
        return json_response({'success': False, 'message': 'A customer with this email or phone already exists.'}, 400)

    try:
        new_id = execute_db(
            "INSERT INTO customers (name, phone, email, address) VALUES (%s, %s, %s, %s)",
            (name, phone, email, address),
            return_id=True
        )
        created = query_db("SELECT * FROM customers WHERE customer_id = %s", (new_id,), one=True)
        return json_response({'success': True, 'message': 'Customer created successfully.', 'customer': created}, 201)
    except Exception as e:
        return json_response({'success': False, 'message': str(e)}, 500)

@api_bp.route('/customers/<int:customer_id>', methods=['PUT'])
@login_required
def update_customer(customer_id):
    if session.get('role') == 'customer' and session.get('customer_id') != customer_id:
        return json_response({'success': False, 'message': 'Access denied.'}, 403)

    data = request.get_json() or request.form
    name = (data.get('name') or '').strip()
    phone = (data.get('phone') or '').strip()
    email = (data.get('email') or '').strip().lower()
    address = (data.get('address') or '').strip()

    if not name or not phone or not email:
        return json_response({'success': False, 'message': 'Name, phone, and email are required.'}, 400)

    if not validate_email(email):
        return json_response({'success': False, 'message': 'Invalid email format.'}, 400)

    if not validate_phone(phone):
        return json_response({'success': False, 'message': 'Invalid phone number format.'}, 400)

    # Check for duplicate email/phone on other customers
    existing = query_db(
        "SELECT customer_id FROM customers WHERE (email = %s OR phone = %s) AND customer_id != %s",
        (email, phone, customer_id),
        one=True
    )
    if existing:
        return json_response({'success': False, 'message': 'Another customer is already using this email or phone.'}, 400)

    try:
        execute_db(
            "UPDATE customers SET name = %s, phone = %s, email = %s, address = %s WHERE customer_id = %s",
            (name, phone, email, address, customer_id)
        )
        updated = query_db("SELECT * FROM customers WHERE customer_id = %s", (customer_id,), one=True)
        return json_response({'success': True, 'message': 'Customer updated successfully.', 'customer': updated})
    except Exception as e:
        return json_response({'success': False, 'message': str(e)}, 500)

@api_bp.route('/customers/<int:customer_id>', methods=['DELETE'])
@login_required
@role_required(['admin'])
def delete_customer(customer_id):
    customer = query_db("SELECT * FROM customers WHERE customer_id = %s", (customer_id,), one=True)
    if not customer:
        return json_response({'success': False, 'message': 'Customer not found.'}, 404)

    try:
        execute_db("DELETE FROM customers WHERE customer_id = %s", (customer_id,))
        return json_response({'success': True, 'message': f"Customer '{customer['name']}' and associated records deleted."})
    except Exception as e:
        return json_response({'success': False, 'message': str(e)}, 500)

# ==============================================================================
# VEHICLES API
# ==============================================================================
@api_bp.route('/vehicles', methods=['GET'])
@login_required
def get_vehicles():
    role = session.get('role')
    customer_id_param = request.args.get('customer_id')

    if role == 'customer':
        cust_id = session.get('customer_id')
        vehicles = query_db("""
            SELECT v.*, c.name AS customer_name, c.phone AS customer_phone
            FROM vehicles v
            JOIN customers c ON v.customer_id = c.customer_id
            WHERE v.customer_id = %s
            ORDER BY v.created_at DESC
        """, (cust_id,))
        return json_response({'success': True, 'vehicles': vehicles})

    query = """
        SELECT v.*, c.name AS customer_name, c.phone AS customer_phone, c.email AS customer_email,
               COUNT(s.service_id) AS total_services
        FROM vehicles v
        JOIN customers c ON v.customer_id = c.customer_id
        LEFT JOIN services s ON v.vehicle_id = s.vehicle_id
    """
    args = []

    if customer_id_param:
        query += " WHERE v.customer_id = %s"
        args.append(customer_id_param)

    query += " GROUP BY v.vehicle_id ORDER BY v.created_at DESC"
    vehicles = query_db(query, tuple(args))
    return json_response({'success': True, 'vehicles': vehicles})

@api_bp.route('/vehicles/<int:vehicle_id>', methods=['GET'])
@login_required
def get_vehicle(vehicle_id):
    vehicle = query_db("""
        SELECT v.*, c.name AS customer_name, c.phone AS customer_phone, c.email AS customer_email
        FROM vehicles v
        JOIN customers c ON v.customer_id = c.customer_id
        WHERE v.vehicle_id = %s
    """, (vehicle_id,), one=True)

    if not vehicle:
        return json_response({'success': False, 'message': 'Vehicle not found.'}, 404)

    if session.get('role') == 'customer' and vehicle['customer_id'] != session.get('customer_id'):
        return json_response({'success': False, 'message': 'Access denied.'}, 403)

    services = query_db("""
        SELECT * FROM services WHERE vehicle_id = %s ORDER BY service_date DESC
    """, (vehicle_id,))

    return json_response({'success': True, 'vehicle': vehicle, 'services': services})

@api_bp.route('/vehicles', methods=['POST'])
@login_required
def create_vehicle():
    data = request.get_json() or request.form
    role = session.get('role')

    if role == 'customer':
        customer_id = session.get('customer_id')
    else:
        customer_id = data.get('customer_id')

    vehicle_number = (data.get('vehicle_number') or '').strip().upper()
    vehicle_model = (data.get('vehicle_model') or '').strip()
    vehicle_type = (data.get('vehicle_type') or '').strip()

    if not customer_id or not vehicle_number or not vehicle_model or not vehicle_type:
        return json_response({'success': False, 'message': 'All vehicle fields are required.'}, 400)

    # Verify customer exists
    cust = query_db("SELECT customer_id FROM customers WHERE customer_id = %s", (customer_id,), one=True)
    if not cust:
        return json_response({'success': False, 'message': 'Selected customer does not exist.'}, 404)

    # Check vehicle number uniqueness
    existing = query_db("SELECT vehicle_id FROM vehicles WHERE vehicle_number = %s", (vehicle_number,), one=True)
    if existing:
        return json_response({'success': False, 'message': f"Vehicle number '{vehicle_number}' is already registered."}, 400)

    try:
        new_id = execute_db(
            "INSERT INTO vehicles (customer_id, vehicle_number, vehicle_model, vehicle_type) VALUES (%s, %s, %s, %s)",
            (customer_id, vehicle_number, vehicle_model, vehicle_type),
            return_id=True
        )
        created = query_db("SELECT * FROM vehicles WHERE vehicle_id = %s", (new_id,), one=True)
        return json_response({'success': True, 'message': 'Vehicle added successfully.', 'vehicle': created}, 201)
    except Exception as e:
        return json_response({'success': False, 'message': str(e)}, 500)

@api_bp.route('/vehicles/<int:vehicle_id>', methods=['PUT'])
@login_required
def update_vehicle(vehicle_id):
    current = query_db("SELECT * FROM vehicles WHERE vehicle_id = %s", (vehicle_id,), one=True)
    if not current:
        return json_response({'success': False, 'message': 'Vehicle not found.'}, 404)

    role = session.get('role')
    if role == 'customer' and current['customer_id'] != session.get('customer_id'):
        return json_response({'success': False, 'message': 'Access denied.'}, 403)

    data = request.get_json() or request.form
    vehicle_number = (data.get('vehicle_number') or current['vehicle_number']).strip().upper()
    vehicle_model = (data.get('vehicle_model') or current['vehicle_model']).strip()
    vehicle_type = (data.get('vehicle_type') or current['vehicle_type']).strip()

    # Admin may also change owner
    if role == 'admin' and data.get('customer_id'):
        customer_id = data.get('customer_id')
    else:
        customer_id = current['customer_id']

    # Uniqueness check
    existing = query_db(
        "SELECT vehicle_id FROM vehicles WHERE vehicle_number = %s AND vehicle_id != %s",
        (vehicle_number, vehicle_id),
        one=True
    )
    if existing:
        return json_response({'success': False, 'message': f"Vehicle number '{vehicle_number}' is used by another vehicle."}, 400)

    try:
        execute_db(
            "UPDATE vehicles SET customer_id = %s, vehicle_number = %s, vehicle_model = %s, vehicle_type = %s WHERE vehicle_id = %s",
            (customer_id, vehicle_number, vehicle_model, vehicle_type, vehicle_id)
        )
        updated = query_db("SELECT * FROM vehicles WHERE vehicle_id = %s", (vehicle_id,), one=True)
        return json_response({'success': True, 'message': 'Vehicle updated successfully.', 'vehicle': updated})
    except Exception as e:
        return json_response({'success': False, 'message': str(e)}, 500)

@api_bp.route('/vehicles/<int:vehicle_id>', methods=['DELETE'])
@login_required
def delete_vehicle(vehicle_id):
    vehicle = query_db("SELECT * FROM vehicles WHERE vehicle_id = %s", (vehicle_id,), one=True)
    if not vehicle:
        return json_response({'success': False, 'message': 'Vehicle not found.'}, 404)

    role = session.get('role')
    if role == 'customer' and vehicle['customer_id'] != session.get('customer_id'):
        return json_response({'success': False, 'message': 'Access denied.'}, 403)

    try:
        execute_db("DELETE FROM vehicles WHERE vehicle_id = %s", (vehicle_id,))
        return json_response({'success': True, 'message': f"Vehicle '{vehicle['vehicle_number']}' deleted successfully."})
    except Exception as e:
        return json_response({'success': False, 'message': str(e)}, 500)

# ==============================================================================
# SERVICES API
# ==============================================================================
@api_bp.route('/services', methods=['GET'])
@login_required
def get_services():
    role = session.get('role')
    status_filter = request.args.get('status')
    vehicle_filter = request.args.get('vehicle_id')

    base_query = """
        SELECT s.*, 
               v.vehicle_number, v.vehicle_model, v.vehicle_type,
               c.customer_id, c.name AS customer_name, c.phone AS customer_phone, c.email AS customer_email,
               m.full_name AS mechanic_name,
               p.payment_id, p.amount AS payment_amount, p.status AS payment_status, p.payment_method
        FROM services s
        JOIN vehicles v ON s.vehicle_id = v.vehicle_id
        JOIN customers c ON v.customer_id = c.customer_id
        LEFT JOIN users m ON s.assigned_mechanic_id = m.user_id
        LEFT JOIN payments p ON s.service_id = p.service_id
    """
    where_clauses = []
    args = []

    if role == 'customer':
        where_clauses.append("c.customer_id = %s")
        args.append(session.get('customer_id'))
    elif role == 'mechanic':
        where_clauses.append("s.assigned_mechanic_id = %s")
        args.append(session.get('user_id'))

    if status_filter:
        where_clauses.append("s.status = %s")
        args.append(status_filter)

    if vehicle_filter:
        where_clauses.append("s.vehicle_id = %s")
        args.append(vehicle_filter)

    if where_clauses:
        base_query += " WHERE " + " AND ".join(where_clauses)

    base_query += " ORDER BY s.service_date DESC, s.created_at DESC"
    services = query_db(base_query, tuple(args))
    return json_response({'success': True, 'services': services})

@api_bp.route('/services/<int:service_id>', methods=['GET'])
@login_required
def get_service(service_id):
    service = query_db("""
        SELECT s.*, 
               v.vehicle_number, v.vehicle_model, v.vehicle_type,
               c.customer_id, c.name AS customer_name, c.phone AS customer_phone, c.email AS customer_email,
               m.full_name AS mechanic_name,
               p.payment_id, p.amount AS payment_amount, p.status AS payment_status, p.payment_method, p.payment_date
        FROM services s
        JOIN vehicles v ON s.vehicle_id = v.vehicle_id
        JOIN customers c ON v.customer_id = c.customer_id
        LEFT JOIN users m ON s.assigned_mechanic_id = m.user_id
        LEFT JOIN payments p ON s.service_id = p.service_id
        WHERE s.service_id = %s
    """, (service_id,), one=True)

    if not service:
        return json_response({'success': False, 'message': 'Service not found.'}, 404)

    role = session.get('role')
    if role == 'customer' and service['customer_id'] != session.get('customer_id'):
        return json_response({'success': False, 'message': 'Access denied.'}, 403)
    if role == 'mechanic' and service['assigned_mechanic_id'] != session.get('user_id'):
        return json_response({'success': False, 'message': 'Access denied: service not assigned to you.'}, 403)

    return json_response({'success': True, 'service': service})

@api_bp.route('/services', methods=['POST'])
@login_required
def create_service():
    data = request.get_json() or request.form
    vehicle_id = data.get('vehicle_id')
    service_type = (data.get('service_type') or '').strip()
    service_date = (data.get('service_date') or '').strip()
    description = (data.get('description') or '').strip()
    service_charge = data.get('service_charge', 0.00)
    status = data.get('status', 'Pending').strip()
    assigned_mechanic_id = data.get('assigned_mechanic_id')

    if not vehicle_id or not service_type or not service_date:
        return json_response({'success': False, 'message': 'Vehicle, service type, and date are required.'}, 400)

    # Check vehicle ownership
    vehicle = query_db("SELECT * FROM vehicles WHERE vehicle_id = %s", (vehicle_id,), one=True)
    if not vehicle:
        return json_response({'success': False, 'message': 'Invalid vehicle.'}, 404)

    if session.get('role') == 'customer':
        if vehicle['customer_id'] != session.get('customer_id'):
            return json_response({'success': False, 'message': 'You can only book services for your own vehicles.'}, 403)
        # Customers always start at Pending
        status = 'Pending'
        service_charge = 0.00
        assigned_mechanic_id = None

    if status not in VALID_SERVICE_STATUSES:
        status = 'Pending'

    try:
        service_charge_val = float(service_charge)
    except (ValueError, TypeError):
        service_charge_val = 0.00

    try:
        new_id = execute_db(
            """INSERT INTO services (vehicle_id, service_type, service_date, description, service_charge, status, assigned_mechanic_id)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (vehicle_id, service_type, service_date, description, service_charge_val, status, assigned_mechanic_id if assigned_mechanic_id else None),
            return_id=True
        )

        # Also create initial pending payment record for this service if charge > 0
        if service_charge_val > 0:
            execute_db(
                """INSERT INTO payments (service_id, amount, payment_date, payment_method, status)
                   VALUES (%s, %s, %s, 'Cash', 'Pending')""",
                (new_id, service_charge_val, service_date)
            )

        created = query_db("SELECT * FROM services WHERE service_id = %s", (new_id,), one=True)
        return json_response({'success': True, 'message': 'Service appointment created successfully.', 'service': created}, 201)
    except Exception as e:
        return json_response({'success': False, 'message': str(e)}, 500)

@api_bp.route('/services/<int:service_id>', methods=['PUT'])
@login_required
def update_service(service_id):
    current = query_db("SELECT * FROM services WHERE service_id = %s", (service_id,), one=True)
    if not current:
        return json_response({'success': False, 'message': 'Service not found.'}, 404)

    role = session.get('role')
    data = request.get_json() or request.form

    if role == 'customer':
        # Customer can only update their service if it's still Pending
        cust_id = session.get('customer_id')
        veh = query_db("SELECT customer_id FROM vehicles WHERE vehicle_id = %s", (current['vehicle_id'],), one=True)
        if not veh or veh['customer_id'] != cust_id:
            return json_response({'success': False, 'message': 'Access denied.'}, 403)
        if current['status'] not in ['Pending']:
            return json_response({'success': False, 'message': 'Cannot modify service after it has been approved/processed.'}, 400)

        service_type = (data.get('service_type') or current['service_type']).strip()
        service_date = (data.get('service_date') or str(current['service_date'])).strip()
        description = (data.get('description') or current['description']).strip()

        execute_db(
            "UPDATE services SET service_type = %s, service_date = %s, description = %s WHERE service_id = %s",
            (service_type, service_date, description, service_id)
        )
        return json_response({'success': True, 'message': 'Appointment updated successfully.'})

    elif role == 'mechanic':
        # Mechanic can update status and technician notes
        if current['assigned_mechanic_id'] != session.get('user_id'):
            return json_response({'success': False, 'message': 'Service is not assigned to you.'}, 403)

        status = data.get('status', current['status'])
        mechanic_notes = data.get('mechanic_notes', current['mechanic_notes'])

        if status not in VALID_SERVICE_STATUSES:
            return json_response({'success': False, 'message': 'Invalid status.'}, 400)

        execute_db(
            "UPDATE services SET status = %s, mechanic_notes = %s WHERE service_id = %s",
            (status, mechanic_notes, service_id)
        )
        return json_response({'success': True, 'message': 'Service progress updated.'})

    else:
        # Admin has complete control over services, charges, status, mechanic assignment
        service_type = (data.get('service_type') or current['service_type']).strip()
        service_date = (data.get('service_date') or str(current['service_date'])).strip()
        description = data.get('description', current['description'])
        status = data.get('status', current['status'])
        mechanic_notes = data.get('mechanic_notes', current['mechanic_notes'])
        assigned_mechanic = data.get('assigned_mechanic_id')
        
        try:
            charge = float(data.get('service_charge', current['service_charge']))
        except (ValueError, TypeError):
            charge = float(current['service_charge'])

        if status not in VALID_SERVICE_STATUSES:
            return json_response({'success': False, 'message': 'Invalid status value.'}, 400)

        # Parse mechanic id
        mechanic_id = int(assigned_mechanic) if (assigned_mechanic and str(assigned_mechanic).isdigit()) else None

        execute_db("""
            UPDATE services 
            SET service_type = %s, service_date = %s, description = %s, 
                service_charge = %s, status = %s, assigned_mechanic_id = %s,
                mechanic_notes = %s
            WHERE service_id = %s
        """, (service_type, service_date, description, charge, status, mechanic_id, mechanic_notes, service_id))

        # Synchronize payment record if exists, or create one if charge > 0
        payment = query_db("SELECT payment_id FROM payments WHERE service_id = %s", (service_id,), one=True)
        if payment:
            execute_db("UPDATE payments SET amount = %s WHERE payment_id = %s", (charge, payment['payment_id']))
        elif charge > 0:
            execute_db(
                "INSERT INTO payments (service_id, amount, payment_date, payment_method, status) VALUES (%s, %s, %s, 'Cash', 'Pending')",
                (service_id, charge, service_date)
            )

        updated = query_db("SELECT * FROM services WHERE service_id = %s", (service_id,), one=True)
        return json_response({'success': True, 'message': 'Service record updated successfully.', 'service': updated})

@api_bp.route('/services/<int:service_id>', methods=['DELETE'])
@login_required
@role_required(['admin'])
def delete_service(service_id):
    service = query_db("SELECT * FROM services WHERE service_id = %s", (service_id,), one=True)
    if not service:
        return json_response({'success': False, 'message': 'Service not found.'}, 404)

    try:
        execute_db("DELETE FROM services WHERE service_id = %s", (service_id,))
        return json_response({'success': True, 'message': f"Service #{service_id} deleted successfully."})
    except Exception as e:
        return json_response({'success': False, 'message': str(e)}, 500)

# ==============================================================================
# PAYMENTS API
# ==============================================================================
@api_bp.route('/payments', methods=['GET'])
@login_required
def get_payments():
    role = session.get('role')
    status_filter = request.args.get('status')
    service_id_filter = request.args.get('service_id')

    base_query = """
        SELECT p.*,
               s.service_type, s.service_date, s.status AS service_status,
               v.vehicle_number, v.vehicle_model,
               c.customer_id, c.name AS customer_name, c.phone AS customer_phone, c.email AS customer_email
        FROM payments p
        JOIN services s ON p.service_id = s.service_id
        JOIN vehicles v ON s.vehicle_id = v.vehicle_id
        JOIN customers c ON v.customer_id = c.customer_id
    """
    where_clauses = []
    args = []

    if role == 'customer':
        where_clauses.append("c.customer_id = %s")
        args.append(session.get('customer_id'))

    if status_filter:
        where_clauses.append("p.status = %s")
        args.append(status_filter)

    if service_id_filter:
        where_clauses.append("p.service_id = %s")
        args.append(service_id_filter)

    if where_clauses:
        base_query += " WHERE " + " AND ".join(where_clauses)

    base_query += " ORDER BY p.payment_date DESC, p.created_at DESC"
    payments = query_db(base_query, tuple(args))
    return json_response({'success': True, 'payments': payments})

@api_bp.route('/payments/<int:payment_id>', methods=['GET'])
@login_required
def get_payment(payment_id):
    payment = query_db("""
        SELECT p.*,
               s.service_type, s.service_date, s.status AS service_status, s.description AS service_description,
               v.vehicle_number, v.vehicle_model, v.vehicle_type,
               c.customer_id, c.name AS customer_name, c.phone AS customer_phone, c.email AS customer_email, c.address AS customer_address
        FROM payments p
        JOIN services s ON p.service_id = s.service_id
        JOIN vehicles v ON s.vehicle_id = v.vehicle_id
        JOIN customers c ON v.customer_id = c.customer_id
        WHERE p.payment_id = %s
    """, (payment_id,), one=True)

    if not payment:
        return json_response({'success': False, 'message': 'Payment record not found.'}, 404)

    if session.get('role') == 'customer' and payment['customer_id'] != session.get('customer_id'):
        return json_response({'success': False, 'message': 'Access denied.'}, 403)

    return json_response({'success': True, 'payment': payment})

@api_bp.route('/payments', methods=['POST'])
@login_required
def create_payment():
    data = request.get_json() or request.form
    service_id = data.get('service_id')
    amount = data.get('amount')
    payment_date = data.get('payment_date') or date.today().isoformat()
    payment_method = data.get('payment_method') or 'Cash'
    status = data.get('status') or 'Pending'
    transaction_id = data.get('transaction_id')

    if not service_id or amount is None:
        return json_response({'success': False, 'message': 'Service ID and amount are required.'}, 400)

    try:
        amount_val = float(amount)
        if amount_val <= 0:
            return json_response({'success': False, 'message': 'Payment amount must be greater than 0.'}, 400)
    except (ValueError, TypeError):
        return json_response({'success': False, 'message': 'Invalid amount value.'}, 400)

    service = query_db("SELECT * FROM services WHERE service_id = %s", (service_id,), one=True)
    if not service:
        return json_response({'success': False, 'message': 'Associated service not found.'}, 404)

    if status not in VALID_PAYMENT_STATUSES:
        status = 'Pending'

    try:
        new_id = execute_db(
            """INSERT INTO payments (service_id, amount, payment_date, payment_method, status, transaction_id)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (service_id, amount_val, payment_date, payment_method, status, transaction_id),
            return_id=True
        )
        created = query_db("SELECT * FROM payments WHERE payment_id = %s", (new_id,), one=True)
        return json_response({'success': True, 'message': 'Payment recorded successfully.', 'payment': created}, 201)
    except Exception as e:
        return json_response({'success': False, 'message': str(e)}, 500)

@api_bp.route('/payments/<int:payment_id>', methods=['PUT'])
@login_required
def update_payment(payment_id):
    payment = query_db("SELECT * FROM payments WHERE payment_id = %s", (payment_id,), one=True)
    if not payment:
        return json_response({'success': False, 'message': 'Payment not found.'}, 404)

    role = session.get('role')
    data = request.get_json() or request.form

    # Customer paying their bill online
    if role == 'customer':
        service = query_db("""
            SELECT v.customer_id FROM services s 
            JOIN vehicles v ON s.vehicle_id = v.vehicle_id 
            WHERE s.service_id = %s
        """, (payment['service_id'],), one=True)

        if not service or service['customer_id'] != session.get('customer_id'):
            return json_response({'success': False, 'message': 'Access denied.'}, 403)

        method = data.get('payment_method') or 'UPI / QR'
        tx_id = f"PAY-CUST-{int(datetime.now().timestamp())}"
        execute_db("""
            UPDATE payments 
            SET status = 'Paid', payment_method = %s, transaction_id = %s, payment_date = %s
            WHERE payment_id = %s
        """, (method, tx_id, date.today().isoformat(), payment_id))
        return json_response({'success': True, 'message': 'Payment completed successfully!', 'transaction_id': tx_id})

    # Admin updates payment
    amount = data.get('amount', payment['amount'])
    payment_date = data.get('payment_date', payment['payment_date'])
    payment_method = data.get('payment_method', payment['payment_method'])
    status = data.get('status', payment['status'])
    transaction_id = data.get('transaction_id', payment['transaction_id'])

    if status not in VALID_PAYMENT_STATUSES:
        return json_response({'success': False, 'message': 'Invalid status.'}, 400)

    try:
        amount_val = float(amount)
    except (ValueError, TypeError):
        amount_val = float(payment['amount'])

    try:
        execute_db("""
            UPDATE payments 
            SET amount = %s, payment_date = %s, payment_method = %s, status = %s, transaction_id = %s
            WHERE payment_id = %s
        """, (amount_val, payment_date, payment_method, status, transaction_id, payment_id))
        updated = query_db("SELECT * FROM payments WHERE payment_id = %s", (payment_id,), one=True)
        return json_response({'success': True, 'message': 'Payment updated successfully.', 'payment': updated})
    except Exception as e:
        return json_response({'success': False, 'message': str(e)}, 500)

@api_bp.route('/payments/<int:payment_id>', methods=['DELETE'])
@login_required
@role_required(['admin'])
def delete_payment(payment_id):
    payment = query_db("SELECT * FROM payments WHERE payment_id = %s", (payment_id,), one=True)
    if not payment:
        return json_response({'success': False, 'message': 'Payment not found.'}, 404)

    try:
        execute_db("DELETE FROM payments WHERE payment_id = %s", (payment_id,))
        return json_response({'success': True, 'message': f"Payment #{payment_id} deleted successfully."})
    except Exception as e:
        return json_response({'success': False, 'message': str(e)}, 500)

# ==============================================================================
# HERO PHOTOGRAPH UPLOAD API
# ==============================================================================
@api_bp.route('/upload-hero', methods=['POST'])
@login_required
@role_required(['admin'])
def upload_hero():
    """
    Allows the admin to upload or replace the homepage hero/banner photograph.
    Saves to static/images/hero-banner.jpg with fallback preservation.
    """
    if 'hero_image' not in request.files:
        return json_response({'success': False, 'message': 'No file part in request.'}, 400)

    file = request.files['hero_image']
    if file.filename == '':
        return json_response({'success': False, 'message': 'No file selected.'}, 400)

    if file and allowed_file(file.filename):
        images_dir = os.path.join(current_app.root_path, 'static', 'images')
        os.makedirs(images_dir, exist_ok=True)
        dest_path = os.path.join(images_dir, 'hero-banner.jpg')
        file.save(dest_path)
        return json_response({
            'success': True, 
            'message': 'Hero banner photograph updated successfully!',
            'url': '/static/images/hero-banner.jpg'
        })
    else:
        return json_response({'success': False, 'message': 'Invalid file format. Allowed: PNG, JPG, JPEG, WEBP.'}, 400)
