from flask import Blueprint, render_template, session, redirect, url_for
from db import query_db
from utils import login_required, role_required

mechanic_bp = Blueprint('mechanic', __name__, url_prefix='/mechanic')

@mechanic_bp.route('/dashboard')
@login_required
@role_required(['mechanic'])
def dashboard():
    mechanic_id = session.get('user_id')

    # Get all services assigned to this mechanic
    assigned_services = query_db("""
        SELECT s.*, 
               v.vehicle_number, v.vehicle_model, v.vehicle_type,
               c.customer_id, c.name AS customer_name, c.phone AS customer_phone, c.email AS customer_email, c.address AS customer_address,
               p.payment_id, p.amount AS payment_amount, p.status AS payment_status
        FROM services s
        JOIN vehicles v ON s.vehicle_id = v.vehicle_id
        JOIN customers c ON v.customer_id = c.customer_id
        LEFT JOIN payments p ON s.service_id = p.service_id
        WHERE s.assigned_mechanic_id = %s
        ORDER BY 
            CASE 
                WHEN s.status = 'In Progress' THEN 1
                WHEN s.status = 'Approved' THEN 2
                WHEN s.status = 'Pending' THEN 3
                WHEN s.status = 'Completed' THEN 4
                ELSE 5
            END,
            s.service_date ASC
    """, (mechanic_id,))

    # Metrics for mechanic
    in_progress_count = sum(1 for s in assigned_services if s['status'] == 'In Progress')
    approved_count = sum(1 for s in assigned_services if s['status'] == 'Approved')
    completed_count = sum(1 for s in assigned_services if s['status'] == 'Completed')
    total_assigned = len(assigned_services)

    return render_template(
        'mechanic/dashboard.html',
        services=assigned_services,
        in_progress_count=in_progress_count,
        approved_count=approved_count,
        completed_count=completed_count,
        total_assigned=total_assigned
    )

