from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from db import query_db, execute_db, get_db_connection
from utils import validate_email, validate_phone, login_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif role == 'mechanic':
            return redirect(url_for('mechanic.dashboard'))
        else:
            return redirect(url_for('customer.dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Server-side validation
        if not full_name or not username or not email or not phone or not password:
            flash('Please fill in all required fields.', 'danger')
            return render_template('register.html')

        if len(username) < 3:
            flash('Username must be at least 3 characters long.', 'danger')
            return render_template('register.html')

        if not validate_email(email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('register.html')

        if not validate_phone(phone):
            flash('Please enter a valid 10-15 digit phone number.', 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        # Check existing username or email
        existing_user = query_db(
            "SELECT user_id FROM users WHERE username = %s OR email = %s LIMIT 1",
            (username, email),
            one=True
        )
        if existing_user:
            flash('Username or email already exists. Please choose another or log in.', 'danger')
            return render_template('register.html')

        # Transaction to create user and customer profile
        password_hash = generate_password_hash(password)
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # 1. Insert user
                cursor.execute(
                    """INSERT INTO users (username, email, password_hash, role, full_name, phone)
                       VALUES (%s, %s, %s, 'customer', %s, %s)""",
                    (username, email, password_hash, full_name, phone)
                )
                user_id = cursor.lastrowid

                # 2. Check if customer record exists with same email/phone
                cursor.execute(
                    "SELECT customer_id FROM customers WHERE email = %s OR phone = %s LIMIT 1",
                    (email, phone)
                )
                existing_cust = cursor.fetchone()

                if existing_cust:
                    cursor.execute(
                        "UPDATE customers SET user_id = %s, name = %s, address = %s WHERE customer_id = %s",
                        (user_id, full_name, address, existing_cust['customer_id'])
                    )
                    cust_id = existing_cust['customer_id']
                else:
                    cursor.execute(
                        """INSERT INTO customers (user_id, name, phone, email, address)
                           VALUES (%s, %s, %s, %s, %s)""",
                        (user_id, full_name, phone, email, address)
                    )
                    cust_id = cursor.lastrowid

            conn.commit()
            flash('Registration successful! Please sign in with your credentials.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            conn.rollback()
            flash(f'Registration error: {str(e)}', 'danger')
            return render_template('register.html')
        finally:
            conn.close()

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif role == 'mechanic':
            return redirect(url_for('mechanic.dashboard'))
        else:
            return redirect(url_for('customer.dashboard'))

    if request.method == 'POST':
        login_id = request.form.get('login_id', '').strip()
        password = request.form.get('password', '')
        selected_role = request.form.get('role', '').strip()  # optional role filter

        if not login_id or not password:
            flash('Please enter your username/email and password.', 'danger')
            return render_template('login.html', login_id=login_id)

        user = query_db(
            """SELECT * FROM users 
               WHERE (username = %s OR email = %s) LIMIT 1""",
            (login_id, login_id.lower()),
            one=True
        )

        if not user or not check_password_hash(user['password_hash'], password):
            flash('Invalid username/email or password.', 'danger')
            return render_template('login.html', login_id=login_id)

        if selected_role and user['role'] != selected_role:
            flash(f'Account role is {user["role"].title()}, not {selected_role.title()}.', 'warning')

        # Retrieve associated customer_id if customer
        customer_id = None
        if user['role'] == 'customer':
            cust = query_db(
                "SELECT customer_id FROM customers WHERE user_id = %s OR email = %s LIMIT 1",
                (user['user_id'], user['email']),
                one=True
            )
            if cust:
                customer_id = cust['customer_id']
                if not cust.get('user_id'):
                    execute_db("UPDATE customers SET user_id = %s WHERE customer_id = %s", (user['user_id'], customer_id))
            else:
                # Auto create customer record if missing
                customer_id = execute_db(
                    "INSERT INTO customers (user_id, name, phone, email, address) VALUES (%s, %s, %s, %s, '')",
                    (user['user_id'], user['full_name'], user['phone'] or '0000000000', user['email']),
                    return_id=True
                )

        # Set session
        session.clear()
        session['user_id'] = user['user_id']
        session['username'] = user['username']
        session['full_name'] = user['full_name']
        session['email'] = user['email']
        session['role'] = user['role']
        session['customer_id'] = customer_id

        flash(f'Welcome back, {user["full_name"]}!', 'success')

        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)

        if user['role'] == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif user['role'] == 'mechanic':
            return redirect(url_for('mechanic.dashboard'))
        else:
            return redirect(url_for('customer.dashboard'))

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

