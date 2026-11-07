from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from db import query_db, execute_db
from utils import login_required, role_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@role_required(['admin'])
def dashboard():
    # 1. Summary Statistics
    total_customers = query_db("SELECT COUNT(*) AS count FROM customers", one=True)['count']
    total_vehicles = query_db("SELECT COUNT(*) AS count FROM vehicles", one=True)['count']
    total_services = query_db("SELECT COUNT(*) AS count FROM services", one=True)['count']
    pending_services = query_db("SELECT COUNT(*) AS count FROM services WHERE status = 'Pending'", one=True)['count']
    in_progress_services = query_db("SELECT COUNT(*) AS count FROM services WHERE status = 'In Progress'", one=True)['count']
    completed_services = query_db("SELECT COUNT(*) AS count FROM services WHERE status = 'Completed'", one=True)['count']
    
    rev_row = query_db("SELECT COALESCE(SUM(amount), 0) AS total FROM payments WHERE status = 'Paid'", one=True)
    total_revenue = float(rev_row['total']) if rev_row else 0.0

    # 2. Customers List
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

    # 3. Vehicles List
    vehicles = query_db("""
        SELECT v.*, c.name AS customer_name, c.phone AS customer_phone,
               COUNT(s.service_id) AS total_services
        FROM vehicles v
        JOIN customers c ON v.customer_id = c.customer_id
        LEFT JOIN services s ON v.vehicle_id = s.vehicle_id
        GROUP BY v.vehicle_id
        ORDER BY v.created_at DESC
    """)

    # 4. Services List with related details
    services = query_db("""
        SELECT s.*, 
               v.vehicle_number, v.vehicle_model, v.vehicle_type,
               c.name AS customer_name, c.phone AS customer_phone,
               m.full_name AS mechanic_name,
               p.payment_id, p.amount AS payment_amount, p.status AS payment_status, p.payment_method
        FROM services s
        JOIN vehicles v ON s.vehicle_id = v.vehicle_id
        JOIN customers c ON v.customer_id = c.customer_id
        LEFT JOIN users m ON s.assigned_mechanic_id = m.user_id
        LEFT JOIN payments p ON s.service_id = p.service_id
        ORDER BY s.created_at DESC
    """)

    # 5. Payments List
    payments = query_db("""
        SELECT p.*,
               s.service_type, s.service_date, s.status AS service_status,
               v.vehicle_number, v.vehicle_model,
               c.name AS customer_name, c.phone AS customer_phone
        FROM payments p
        JOIN services s ON p.service_id = s.service_id
        JOIN vehicles v ON s.vehicle_id = v.vehicle_id
        JOIN customers c ON v.customer_id = c.customer_id
        ORDER BY p.payment_date DESC, p.created_at DESC
    """)

    # 6. Mechanics list for assignment dropdown
    mechanics = query_db("""
        SELECT user_id, full_name, username, phone 
        FROM users 
        WHERE role = 'mechanic' 
        ORDER BY full_name ASC
    """)

    return render_template(
        'admin/dashboard.html',
        stats={
            'total_customers': total_customers,
            'total_vehicles': total_vehicles,
            'total_services': total_services,
            'pending_services': pending_services,
            'in_progress_services': in_progress_services,
            'completed_services': completed_services,
            'total_revenue': total_revenue
        },
        customers=customers,
        vehicles=vehicles,
        services=services,
        payments=payments,
        mechanics=mechanics
    )

