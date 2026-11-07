from flask import Blueprint, render_template, session, redirect, url_for, flash
from db import query_db
from utils import login_required, role_required

customer_bp = Blueprint('customer', __name__, url_prefix='/customer')

@customer_bp.route('/dashboard')
@login_required
@role_required(['customer'])
def dashboard():
    cust_id = session.get('customer_id')
    user_id = session.get('user_id')

    # Get customer info
    customer = query_db("SELECT * FROM customers WHERE customer_id = %s", (cust_id,), one=True)
    if not customer:
        customer = query_db("SELECT * FROM customers WHERE user_id = %s", (user_id,), one=True)

    # Get vehicles
    vehicles = query_db("""
        SELECT v.*, COUNT(s.service_id) AS service_count
        FROM vehicles v
        LEFT JOIN services s ON v.vehicle_id = s.vehicle_id
        WHERE v.customer_id = %s
        GROUP BY v.vehicle_id
        ORDER BY v.created_at DESC
    """, (cust_id,))

    # Get services with vehicle & payment details
    services = query_db("""
        SELECT s.*, v.vehicle_number, v.vehicle_model, v.vehicle_type,
               p.payment_id, p.amount AS payment_amount, p.status AS payment_status, p.payment_method,
               m.full_name AS mechanic_name
        FROM services s
        JOIN vehicles v ON s.vehicle_id = v.vehicle_id
        LEFT JOIN users m ON s.assigned_mechanic_id = m.user_id
        LEFT JOIN payments p ON s.service_id = p.service_id
        WHERE v.customer_id = %s
        ORDER BY s.service_date DESC, s.created_at DESC
    """, (cust_id,))

    # Quick metrics for customer
    pending_count = sum(1 for s in services if s['status'] == 'Pending')
    active_count = sum(1 for s in services if s['status'] in ['Approved', 'In Progress'])
    completed_count = sum(1 for s in services if s['status'] == 'Completed')
    unpaid_payments = [s for s in services if s.get('payment_amount') and s.get('payment_status') != 'Paid']

    return render_template(
        'customer/dashboard.html',
        customer=customer,
        vehicles=vehicles,
        services=services,
        pending_count=pending_count,
        active_count=active_count,
        completed_count=completed_count,
        unpaid_payments=unpaid_payments
    )

