# Puneeth Vehicle Services - Full-Stack Vehicle Service Centre Management System

A complete, professional, responsive, and secure Full-Stack Web Application for **Puneeth Vehicle Services**, designed to streamline customer vehicle management, service appointments, repair workflow tracking, technician dispatch, service billing, and revenue analytics.

Built strictly using **Python Flask**, **MySQL**, **Bootstrap 5**, **Chart.js**, and **Font Awesome**.

---

## 🚀 Key Features

### 1. Modern Automotive Homepage
- **Hero Section**: Displays vehicle/service centre photography with crisp cover styling and dark overlay.
- **Dynamic Counters**: Live metrics fetched dynamically from MySQL (Happy Clients, Jobs Done, Rating).
- **Our Services**: Interactive cards for Periodic Maintenance, Brake Overhauls, Computer Diagnostics, AC Servicing, Battery Diagnostics, and Wheel Alignment.
- **The Puneeth Advantage**: Highlights ASE Certified Technicians, OEM Spares, Live Tracking, and 6-Month Warranty.
- **Four-Step Service Process**: Visual flow from Online Booking to Delivery.
- **Contact & Inquiry**: Workshop address, WhatsApp, phone, email, and interactive inquiry form.

### 2. Role-Based Access Control (RBAC) & Security
- **Unified Portal Access**: Dedicated dashboards for **Admin**, **Mechanic**, and **Customer**.
- **Secure Password Hashing**: Hashed using `werkzeug.security` (scrypt).
- **SQL Injection Prevention**: 100% parameterized SQL queries via `PyMySQL`.
- **Session Management**: Role-protected routes and API endpoints.

### 3. Customer Portal
- Self-registration and login.
- Register and view vehicles (SUV, Sedan, Hatchback, EV, Motorcycle).
- Book service appointments (choose vehicle, service type, preferred date, complaint).
- **Live Status Tracker**: Visual step progress: `Requested` ➔ `Approved` ➔ `In Progress` ➔ `Completed`.
- Inspect technician notes and service charges.
- Digital payment settlement (UPI / QR, Card, Net Banking, Cash).
- Profile update (name, phone, email, address).

### 4. Mechanic Bay
- View assigned service requests with customer details and vehicle models.
- Read customer complaints and vehicle symptoms.
- Update live repair notes and technician diagnosis.
- Transition job statuses (`Approved` ➔ `In Progress` ➔ `Completed`).
- One-click "Quick Mark Completed" with timestamp.

### 5. Admin Control Panel
- **Real-Time KPIs**: Total Customers, Total Vehicles, Total Services, Pending Services, Completed Services, Total Revenue.
- **Chart.js Visualizations**:
  - Monthly Revenue bar chart (paid invoices).
  - Service Status ratio doughnut chart.
- **Customer Management (Full CRUD)**: Add, View, Edit, Delete, and instant search.
- **Vehicle Management (Full CRUD)**: Add, View, Edit, Delete, and instant search.
- **Service Management**: Approve/Reject, Assign Mechanics, Update Service Charges, Change Status, Search & Filter.
- **Payment & Invoicing**: Record payments, update status (`Paid`, `Pending`, `Failed`), track transaction IDs.
- **Hero Photograph Management**: Upload and replace homepage hero banner photograph dynamically.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3.3 |
| **Icons** | Font Awesome 6.5.2 |
| **Charts** | Chart.js 4.4.2 |
| **Backend** | Python 3 (Flask 3.1) |
| **Database** | MySQL Server 8.0 |
| **DB Connector** | PyMySQL / mysql-connector-python |
| **Security** | Werkzeug Security, Parameterized SQL, Environment Configuration |

---

## 📁 Project Structure

```text
vehicle/
├── .env                          # Local MySQL credentials & secret key (created)
├── .env.example                  # Environment template
├── requirements.txt              # Python dependencies
├── database.sql                  # MySQL database schema & seed data
├── app.py                        # Flask entry point & global error handlers
├── config.py                     # Configuration settings
├── db.py                         # MySQL connection helpers & query executors
├── utils.py                      # Auth decorators, JSON encoder, validators
├── README.md                     # Documentation
├── routes/
│   ├── __init__.py
│   ├── auth_routes.py            # Login, Customer Registration, Logout
│   ├── customer_routes.py        # Customer dashboard views
│   ├── mechanic_routes.py        # Mechanic dashboard views
│   ├── admin_routes.py           # Admin control panel views
│   └── api_routes.py             # Full REST API for CRUD, stats & file upload
├── static/
│   ├── css/
│   │   ├── style.css             # Main automotive theme (Navy, White, Orange)
│   │   └── dashboard.css         # Modern KPI cards, tables, steppers
│   ├── js/
│   │   ├── main.js               # Global scrolling & toast auto-dismiss
│   │   ├── customer.js           # Customer AJAX operations
│   │   ├── mechanic.js           # Mechanic AJAX progress updates
│   │   └── admin.js              # Admin CRUD, filters, and Chart.js charts
│   └── images/
│       └── hero-banner.jpg       # Homepage hero background image
└── templates/
    ├── base.html                 # Master template with navigation and footer
    ├── index.html                # Modern Homepage
    ├── login.html                # Unified login portal with demo presets
    ├── register.html             # Customer self-registration form
    ├── customer/
    │   └── dashboard.html        # Customer Portal
    ├── mechanic/
    │   └── dashboard.html        # Mechanic Bay
    └── admin/
        └── dashboard.html        # Admin Dashboard
```

---

## 🗄️ Database Design (MySQL)

Database Name: `puneeth_vehicle_services`

### Table 1: `customers`
- `customer_id` (INT, PRIMARY KEY, AUTO_INCREMENT)
- `user_id` (INT, FOREIGN KEY REFERENCES users(user_id) ON DELETE SET NULL)
- `name` (VARCHAR 100)
- `phone` (VARCHAR 15)
- `email` (VARCHAR 100)
- `address` (TEXT)

### Table 2: `vehicles`
- `vehicle_id` (INT, PRIMARY KEY, AUTO_INCREMENT)
- `customer_id` (INT, FOREIGN KEY REFERENCES customers(customer_id) ON DELETE CASCADE)
- `vehicle_number` (VARCHAR 20, UNIQUE)
- `vehicle_model` (VARCHAR 100)
- `vehicle_type` (VARCHAR 50)

### Table 3: `services`
- `service_id` (INT, PRIMARY KEY, AUTO_INCREMENT)
- `vehicle_id` (INT, FOREIGN KEY REFERENCES vehicles(vehicle_id) ON DELETE CASCADE)
- `service_type` (VARCHAR 100)
- `service_date` (DATE)
- `description` (TEXT)
- `service_charge` (DECIMAL 10,2)
- `status` (VARCHAR 30: `Pending`, `Approved`, `In Progress`, `Completed`, `Cancelled`)
- `assigned_mechanic_id` (INT, FOREIGN KEY REFERENCES users(user_id) ON DELETE SET NULL)
- `mechanic_notes` (TEXT)

### Table 4: `payments`
- `payment_id` (INT, PRIMARY KEY, AUTO_INCREMENT)
- `service_id` (INT, FOREIGN KEY REFERENCES services(service_id) ON DELETE CASCADE)
- `amount` (DECIMAL 10,2)
- `payment_date` (DATE)
- `payment_method` (VARCHAR 50)
- `status` (VARCHAR 30: `Pending`, `Paid`, `Failed`)
- `transaction_id` (VARCHAR 100)

### Table 5: `users`
- `user_id` (INT, PRIMARY KEY, AUTO_INCREMENT)
- `username` (VARCHAR 50, UNIQUE)
- `email` (VARCHAR 100, UNIQUE)
- `password_hash` (VARCHAR 255)
- `role` (`admin`, `mechanic`, `customer`)
- `full_name` (VARCHAR 100)
- `phone` (VARCHAR 20)

---

## ⚙️ Setup & Installation Instructions

### Prerequisites
- Python 3.10+
- MySQL Server 8.0+ running on port 3306

### Step 1: Clone or Navigate to Directory
```bash
cd "c:\Users\GT-BOOK\Desktop\vehicle"
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: MySQL Database Setup
Open MySQL command prompt or run `database.sql` directly:
```bash
mysql -u root -p < database.sql
```
*(Enter your MySQL root password when prompted)*

### Step 4: Configure Environment Variables
Verify `.env` contains your MySQL credentials:
```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=puneeth@mysql
DB_NAME=puneeth_vehicle_services
SECRET_KEY=puneeth_vehicle_services_super_secret_key_2026_xyz
FLASK_ENV=development
PORT=5000
```

### Step 5: Start the Flask Application
```bash
python app.py
```

### Step 6: Access the Application
Open your browser and navigate to:
**http://127.0.0.1:5000**

---

## 🔑 Initial Demo Login Accounts

All demo accounts can be logged in via **http://127.0.0.1:5000/login** (with convenient one-click presets provided on the login page):

| Role | Username | Password | Email | Description |
|---|---|---|---|---|
| **Administrator** | `admin` | `admin123` | `admin@puneethservices.com` | Complete access to customers, vehicles, mechanics, services, and revenue |
| **Lead Mechanic** | `mechanic_rajesh` | `mechanic123` | `rajesh@puneethservices.com` | Technician bay to manage assigned services and live notes |
| **Senior Technician** | `mechanic_suresh` | `mechanic123` | `suresh@puneethservices.com` | Technician bay to manage assigned services and live notes |
| **Customer** | `customer_arun` | `customer123` | `arun.patel@gmail.com` | Customer portal (owns Hyundai Creta & Honda City) |
| **Customer** | `customer_priya` | `customer123` | `priya.nair@gmail.com` | Customer portal (owns Maruti Baleno) |

*(Note: You can also register a brand new customer account at **http://127.0.0.1:5000/register**)*

---

## 🌐 REST API Endpoints

### Customers
- `GET /api/customers` — List all customers (searchable)
- `GET /api/customers/<id>` — Get single customer with vehicles
- `POST /api/customers` — Create customer (Admin)
- `PUT /api/customers/<id>` — Update customer info
- `DELETE /api/customers/<id>` — Delete customer (Admin, cascaded)

### Vehicles
- `GET /api/vehicles` — List vehicles (filtered by customer)
- `GET /api/vehicles/<id>` — Single vehicle with service logs
- `POST /api/vehicles` — Register new vehicle
- `PUT /api/vehicles/<id>` — Edit vehicle details
- `DELETE /api/vehicles/<id>` — Delete vehicle

### Services
- `GET /api/services` — List service requests (filtered by status/role)
- `GET /api/services/<id>` — Single service details
- `POST /api/services` — Create / Book service appointment
- `PUT /api/services/<id>` — Update service / progress / charges / assign mechanic
- `DELETE /api/services/<id>` — Delete service (Admin)

### Payments
- `GET /api/payments` — List payments (filtered by status/service)
- `GET /api/payments/<id>` — Single payment record with invoice
- `POST /api/payments` — Record payment
- `PUT /api/payments/<id>` — Update payment status / Customer pay invoice
- `DELETE /api/payments/<id>` — Delete payment record

### Analytics & Upload
- `GET /api/stats` — Dashboard KPI numbers & Chart.js data series
- `GET /api/mechanics` — List of available mechanics for assignment
- `POST /api/upload-hero` — Upload / replace homepage hero photograph

