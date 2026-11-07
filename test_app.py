"""
Automated Integration and Multi-Page Test Suite for Puneeth Vehicle Services
Tests live MySQL connectivity, all 9 dedicated multi-page routes,
Authentication, Role-based Access, Customer Registration,
Vehicle Management, Service Workflow, and Revenue Statistics.
"""

import unittest
from datetime import date
from app import app
from db import query_db, execute_db

class TestPuneethVehicleServices(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        self.client.testing = True

    def test_01_database_connectivity(self):
        """Test MySQL connection and initial seed data."""
        tables = query_db("SHOW TABLES;")
        table_names = [list(t.values())[0] for t in tables]
        for expected in ['customers', 'vehicles', 'services', 'payments', 'users']:
            self.assertIn(expected, table_names, f"Table {expected} missing in MySQL")

        users_count = query_db("SELECT COUNT(*) AS c FROM users", one=True)['c']
        self.assertGreaterEqual(users_count, 3, "Seed users missing")
        print(f"[TEST 1 PASS] MySQL tables verified: {table_names}. Seed users: {users_count}")

    def test_02_all_public_multipage_routes(self):
        """Test all dedicated multi-page routes render with 200 OK and distinct content."""
        # 1. Home Page ('/')
        res_home = self.client.get('/')
        self.assertEqual(res_home.status_code, 200)
        self.assertIn(b'Welcome to', res_home.data)
        self.assertIn(b'Puneeth Vehicle Services', res_home.data)
        self.assertIn(b'Trusted Vehicle Care, Driven by Excellence', res_home.data)
        self.assertIn(b'puneeth-owner.jpg', res_home.data)
        print("[TEST 2.1 PASS] 1. Home Page ('/') loaded successfully with Owner Photograph & Heading.")

        # 2. Our Services Page ('/services')
        res_services = self.client.get('/services')
        self.assertEqual(res_services.status_code, 200)
        self.assertIn(b'Comprehensive', res_services.data)
        self.assertIn(b'Periodic Maintenance Service', res_services.data)
        self.assertIn(b'Brake System Overhaul', res_services.data)
        print("[TEST 2.2 PASS] 2. Our Services Page ('/services') loaded successfully.")

        # 3. Why Choose Us Page ('/about')
        res_about = self.client.get('/about')
        self.assertEqual(res_about.status_code, 200)
        self.assertIn(b'The Six Pillars of Puneeth Vehicle Services', res_about.data)
        self.assertIn(b'Certified Master Technicians', res_about.data)
        print("[TEST 2.3 PASS] 3. Why Choose Us Page ('/about') loaded successfully.")

        # 4. Service Process Page ('/process')
        res_process = self.client.get('/process')
        self.assertEqual(res_process.status_code, 200)
        self.assertIn(b'Step-by-Step Vehicle Service Journey', res_process.data)
        self.assertIn(b'Digital Service Request', res_process.data)
        self.assertIn(b'Computerized Diagnostic & Quote', res_process.data)
        print("[TEST 2.4 PASS] 4. Service Process Page ('/process') loaded successfully.")

        # 5. Contact Us Page ('/contact')
        res_contact = self.client.get('/contact')
        self.assertEqual(res_contact.status_code, 200)
        self.assertIn(b'Visit Our Modern Service Centre', res_contact.data)
        self.assertIn(b'Send Us a Direct Message', res_contact.data)

        # Test Contact form submission
        res_post_contact = self.client.post('/contact', data={
            'name': 'Ramesh Verma',
            'phone': '9876541230',
            'email': 'ramesh@example.com',
            'service_type': 'Periodic Maintenance Service',
            'message': 'Need weekend slot for Honda City.'
        }, follow_redirects=True)
        self.assertEqual(res_post_contact.status_code, 200)
        self.assertIn(b'Thank you, Ramesh Verma', res_post_contact.data)
        print("[TEST 2.5 PASS] 5. Contact Us Page ('/contact') GET & POST inquiry verified.")

        # 6. Login Page ('/login')
        res_login = self.client.get('/login')
        self.assertEqual(res_login.status_code, 200)
        self.assertIn(b'Sign In to Account', res_login.data)
        print("[TEST 2.6 PASS] 6. Login Page ('/login') loaded successfully.")

    def test_03_customer_registration(self):
        """Test new customer self-registration in MySQL."""
        test_email = f"test_reg_{date.today().strftime('%Y%m%d')}_{int(date.today().day)}@example.com"
        test_user = f"testuser_{date.today().day}"
        test_phone = "9876599999"

        execute_db("DELETE FROM users WHERE username = %s OR email = %s", (test_user, test_email))
        execute_db("DELETE FROM customers WHERE email = %s OR phone = %s", (test_email, test_phone))

        res = self.client.post('/register', data={
            'full_name': 'Test Registration User',
            'username': test_user,
            'email': test_email,
            'phone': test_phone,
            'address': 'Test Lane, Bengaluru',
            'password': 'testpassword123',
            'confirm_password': 'testpassword123'
        }, follow_redirects=True)

        self.assertEqual(res.status_code, 200)
        user = query_db("SELECT * FROM users WHERE username = %s", (test_user,), one=True)
        self.assertIsNotNone(user)
        self.assertEqual(user['role'], 'customer')

        cust = query_db("SELECT * FROM customers WHERE email = %s", (test_email,), one=True)
        self.assertIsNotNone(cust)
        self.assertEqual(cust['user_id'], user['user_id'])
        print(f"[TEST 3 PASS] Customer registered successfully. User ID: {user['user_id']}, Cust ID: {cust['customer_id']}")

    def test_04_dashboards_access_and_full_workflow(self):
        """Test Customer, Mechanic, and Admin dashboards and full repair lifecycle."""
        # 1. Customer Login and Customer Dashboard ('/customer/dashboard')
        self.client.post('/login', data={'login_id': 'customer_arun', 'password': 'customer123'}, follow_redirects=True)
        cust_dash = self.client.get('/customer/dashboard')
        self.assertEqual(cust_dash.status_code, 200)
        self.assertIn(b'Customer Portal', cust_dash.data)
        self.assertIn(b'My Vehicles', cust_dash.data)
        print("[TEST 4.1 PASS] 7. Customer Dashboard ('/customer/dashboard') verified.")

        # Add vehicle
        veh_num = "KA-04-TEST-99"
        execute_db("DELETE FROM vehicles WHERE vehicle_number = %s", (veh_num,))
        post_res = self.client.post('/api/vehicles', json={
            'vehicle_number': veh_num,
            'vehicle_model': 'Mahindra XUV700 AX7',
            'vehicle_type': 'SUV'
        })
        self.assertEqual(post_res.status_code, 201)
        veh_id = post_res.get_json()['vehicle']['vehicle_id']

        # Book service
        srv_res = self.client.post('/api/services', json={
            'vehicle_id': veh_id,
            'service_type': 'Periodic Maintenance & Oil Change',
            'service_date': str(date.today()),
            'description': '30,000 km general service and oil replacement'
        })
        srv_id = srv_res.get_json()['service']['service_id']
        self.client.get('/logout')

        # 2. Admin Login and Admin Dashboard ('/admin/dashboard')
        self.client.post('/login', data={'login_id': 'admin', 'password': 'admin123'}, follow_redirects=True)
        admin_dash = self.client.get('/admin/dashboard')
        self.assertEqual(admin_dash.status_code, 200)
        self.assertIn(b'Control Hub', admin_dash.data)
        self.assertIn(b'Service Management', admin_dash.data)
        print("[TEST 4.2 PASS] 8. Admin Dashboard ('/admin/dashboard') verified.")

        # Admin approves service, assigns mechanic Rajesh, sets charge
        self.client.put(f'/api/services/{srv_id}', json={
            'service_type': 'Periodic Maintenance & Oil Change',
            'service_date': str(date.today()),
            'service_charge': 4200.00,
            'status': 'Approved',
            'assigned_mechanic_id': 2,
            'description': '30,000 km general service and oil replacement'
        })
        payment = query_db("SELECT * FROM payments WHERE service_id = %s", (srv_id,), one=True)
        self.assertEqual(float(payment['amount']), 4200.00)
        self.client.get('/logout')

        # 3. Mechanic Login and Mechanic Dashboard ('/mechanic/dashboard')
        self.client.post('/login', data={'login_id': 'mechanic_rajesh', 'password': 'mechanic123'}, follow_redirects=True)
        mech_dash = self.client.get('/mechanic/dashboard')
        self.assertEqual(mech_dash.status_code, 200)
        self.assertIn(b'Technician Bay', mech_dash.data)
        print("[TEST 4.3 PASS] 9. Mechanic Dashboard ('/mechanic/dashboard') verified.")

        # Mechanic updates progress and marks completed
        self.client.put(f'/api/services/{srv_id}', json={
            'status': 'Completed',
            'mechanic_notes': 'Synthetic 5W-30 engine oil filled, new Bosch filter fitted. Road test approved.'
        })
        self.client.get('/logout')

        # Customer logs in and pays bill online
        self.client.post('/login', data={'login_id': 'customer_arun', 'password': 'customer123'}, follow_redirects=True)
        pay_res = self.client.put(f"/api/payments/{payment['payment_id']}", json={'payment_method': 'UPI / QR'})
        self.assertEqual(pay_res.status_code, 200)

        pay_row = query_db("SELECT * FROM payments WHERE payment_id = %s", (payment['payment_id'],), one=True)
        self.assertEqual(pay_row['status'], 'Paid')
        print(f"[TEST 4.4 PASS] Full service lifecycle from booking to mechanic update and payment completion passed!")

        # Cleanup test vehicle & user
        execute_db("DELETE FROM vehicles WHERE vehicle_number = %s", (veh_num,))

    def test_05_admin_dashboard_stats_api(self):
        """Test /api/stats endpoint returns dynamic live statistics."""
        self.client.post('/login', data={'login_id': 'admin', 'password': 'admin123'}, follow_redirects=True)
        res = self.client.get('/api/stats')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertGreater(data['stats']['total_customers'], 0)
        self.assertGreater(data['stats']['total_vehicles'], 0)
        self.assertGreater(data['stats']['total_services'], 0)
        self.assertGreater(data['stats']['total_revenue'], 0)
        print(f"[TEST 5 PASS] Admin Stats API returned live metrics: Revenue: ₹{data['stats']['total_revenue']}, Customers: {data['stats']['total_customers']}, Services: {data['stats']['total_services']}")

if __name__ == '__main__':
    unittest.main()
