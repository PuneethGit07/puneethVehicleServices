import os
from flask import Flask, render_template, session, redirect, url_for, request, flash
from config import Config
from db import query_db, check_db_connection
from routes.auth_routes import auth_bp
from routes.customer_routes import customer_bp
from routes.mechanic_routes import mechanic_bp
from routes.admin_routes import admin_bp
from routes.api_routes import api_bp

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload directory exists
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
images_dir = os.path.join(app.root_path, 'static', 'images')
os.makedirs(images_dir, exist_ok=True)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(customer_bp)
app.register_blueprint(mechanic_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(api_bp)

@app.context_processor
def inject_global_vars():
    """Inject variables into all Jinja templates."""
    return {
        'app_name': 'Puneeth Vehicle Services',
        'current_user': {
            'user_id': session.get('user_id'),
            'username': session.get('username'),
            'full_name': session.get('full_name'),
            'email': session.get('email'),
            'role': session.get('role'),
            'customer_id': session.get('customer_id')
        } if 'user_id' in session else None
    }

# ==============================================================================
# MULTI-PAGE PUBLIC ROUTES
# ==============================================================================

@app.route('/')
def index():
    """
    1. Home Page ('/')
    Large automotive hero section, overview of key services, introduction,
    live operational counters, and quick booking CTA.
    """
    total_services = 0
    total_customers = 0
    try:
        ts = query_db("SELECT COUNT(*) AS count FROM services", one=True)
        tc = query_db("SELECT COUNT(*) AS count FROM customers", one=True)
        total_services = ts['count'] if ts else 0
        total_customers = tc['count'] if tc else 0
    except Exception:
        pass

    hero_image_exists = os.path.exists(os.path.join(app.root_path, 'static', 'images', 'hero-banner.jpg'))

    return render_template(
        'index.html',
        total_services=total_services,
        total_customers=total_customers,
        hero_image_exists=hero_image_exists
    )

@app.route('/services')
def services():
    """
    2. Our Services Page ('/services')
    Comprehensive catalog of automotive repair & maintenance services,
    transparent pricing tiers, diagnostic descriptions, and booking links.
    """
    return render_template('services.html')

@app.route('/about')
def about():
    """
    3. Why Choose Us / About Us Page ('/about')
    Detailed presentation of Puneeth Vehicle Services, master mechanics,
    OEM certification, workshop facility, and quality guarantees.
    """
    total_customers = 0
    total_services = 0
    try:
        tc = query_db("SELECT COUNT(*) AS count FROM customers", one=True)
        ts = query_db("SELECT COUNT(*) AS count FROM services", one=True)
        total_customers = tc['count'] if tc else 0
        total_services = ts['count'] if ts else 0
    except Exception:
        pass

    return render_template('about.html', total_customers=total_customers, total_services=total_services)

@app.route('/process')
def process():
    """
    4. Service Process Page ('/process')
    Interactive 4-step workflow explaining booking, bay inspection,
    precision repair with live status tracking, and delivery.
    """
    return render_template('process.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """
    5. Contact Us Page ('/contact')
    Physical workshop location, interactive map card, operating hours,
    direct hotline, WhatsApp link, and functional inquiry submission form.
    """
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        service_type = request.form.get('service_type', 'General Inquiry').strip()
        message = request.form.get('message', '').strip()

        if not name or not phone:
            flash('Please provide your name and contact phone number.', 'danger')
            return render_template('contact.html')

        flash(f'Thank you, {name}! Your service inquiry for "{service_type}" has been received. Our service advisor will call you at {phone} within 15 minutes.', 'success')
        return redirect(url_for('contact'))

    return render_template('contact.html')

@app.errorhandler(404)
def not_found_error(error):
    if request.path.startswith('/api/'):
        return {'success': False, 'message': 'Resource not found'}, 404
    return render_template('base.html', not_found=True), 404

@app.errorhandler(500)
def internal_error(error):
    if request.path.startswith('/api/'):
        return {'success': False, 'message': 'Internal server error'}, 500
    return render_template('base.html', internal_error=True), 500

if __name__ == '__main__':
    db_ok, db_msg = check_db_connection()
    if db_ok:
        print("[DATABASE] Connected to MySQL successfully.")
    else:
        print(f"[DATABASE WARNING] Could not connect to MySQL: {db_msg}")

    print("==========================================================")
    print(" Puneeth Vehicle Services is running!")
    print(" Localhost URL: http://127.0.0.1:5000")
    print("==========================================================")
    app.run(host='0.0.0.0', port=5000, debug=True)
