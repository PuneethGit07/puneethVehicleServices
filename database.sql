-- Puneeth Vehicle Services Database Schema
-- Database Name: puneeth_vehicle_services

CREATE DATABASE IF NOT EXISTS puneeth_vehicle_services
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE puneeth_vehicle_services;

-- --------------------------------------------------------
-- Users Table (for Authentication & Role-Based Access)
-- Roles: admin, mechanic, customer
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'mechanic', 'customer') NOT NULL DEFAULT 'customer',
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_role (role),
    INDEX idx_user_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------
-- TABLE 1: customers
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(15) NOT NULL,
    email VARCHAR(100) NOT NULL,
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_customer_phone (phone),
    INDEX idx_customer_email (email),
    CONSTRAINT fk_customer_user FOREIGN KEY (user_id) 
        REFERENCES users(user_id) 
        ON DELETE SET NULL 
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------
-- TABLE 2: vehicles
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    vehicle_number VARCHAR(20) NOT NULL UNIQUE,
    vehicle_model VARCHAR(100) NOT NULL,
    vehicle_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_vehicle_customer (customer_id),
    INDEX idx_vehicle_number (vehicle_number),
    CONSTRAINT fk_vehicle_customer FOREIGN KEY (customer_id) 
        REFERENCES customers(customer_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------
-- TABLE 3: services
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS services (
    service_id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_id INT NOT NULL,
    service_type VARCHAR(100) NOT NULL,
    service_date DATE NOT NULL,
    description TEXT,
    service_charge DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    status VARCHAR(30) NOT NULL DEFAULT 'Pending',
    assigned_mechanic_id INT NULL,
    mechanic_notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_service_vehicle (vehicle_id),
    INDEX idx_service_status (status),
    INDEX idx_service_date (service_date),
    INDEX idx_service_mechanic (assigned_mechanic_id),
    CONSTRAINT fk_service_vehicle FOREIGN KEY (vehicle_id) 
        REFERENCES vehicles(vehicle_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    CONSTRAINT fk_service_mechanic FOREIGN KEY (assigned_mechanic_id) 
        REFERENCES users(user_id) 
        ON DELETE SET NULL 
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------
-- TABLE 4: payments
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    service_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_date DATE NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'Pending',
    transaction_id VARCHAR(100) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_payment_service (service_id),
    INDEX idx_payment_status (status),
    INDEX idx_payment_date (payment_date),
    CONSTRAINT fk_payment_service FOREIGN KEY (service_id) 
        REFERENCES services(service_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------
-- INITIAL SEED DATA (Password for all demo accounts: admin123 / mechanic123 / customer123)
-- werkzeug scrypt hashes generated for standard security
-- --------------------------------------------------------

-- Demo Users
-- admin / admin123
-- mechanic_rajesh / mechanic123
-- mechanic_suresh / mechanic123
-- customer_arun / customer123
-- customer_priya / customer123
INSERT INTO users (user_id, username, email, password_hash, role, full_name, phone) VALUES
(1, 'admin', 'admin@puneethservices.com', 'scrypt:32768:8:1$peKO5LfVPLa4amps$2fa9349c5d78d427ccdc91cd99e6c574293fa10df552035c7a512dbd63f6edc4619418ba9203126e43461f0575885b57ec6024272c4e62644537d3a63fab7fe4', 'admin', 'Admin Puneeth', '9876543210'),
(2, 'mechanic_rajesh', 'rajesh@puneethservices.com', 'scrypt:32768:8:1$lE06k6CaNHbKXTnT$c4dc0685bd641405734c37dd76ec6a0f8f2e7390656c4b6a3f4820a205519c36059717606a95ac222eb65ba76c53af90fd586b0f7763464051ee97c3494e79fa', 'mechanic', 'Rajesh Sharma (Lead Mechanic)', '9876501234'),
(3, 'mechanic_suresh', 'suresh@puneethservices.com', 'scrypt:32768:8:1$lE06k6CaNHbKXTnT$c4dc0685bd641405734c37dd76ec6a0f8f2e7390656c4b6a3f4820a205519c36059717606a95ac222eb65ba76c53af90fd586b0f7763464051ee97c3494e79fa', 'mechanic', 'Suresh Kumar (Senior Technician)', '9876505678'),
(4, 'customer_arun', 'arun.patel@gmail.com', 'scrypt:32768:8:1$MFMh6asvvbDzUO65$d86ae7ddbf278c645a99cab3790c002727a0741efdbd055ad012c5553f78cd1b02c9d4e64ae4625f00703bd464b9c6107b07390fa09f90a5fb5ea97c48c3902c', 'customer', 'Arun Patel', '9812345678'),
(5, 'customer_priya', 'priya.nair@gmail.com', 'scrypt:32768:8:1$MFMh6asvvbDzUO65$d86ae7ddbf278c645a99cab3790c002727a0741efdbd055ad012c5553f78cd1b02c9d4e64ae4625f00703bd464b9c6107b07390fa09f90a5fb5ea97c48c3902c', 'customer', 'Priya Nair', '9898765432')
ON DUPLICATE KEY UPDATE password_hash = VALUES(password_hash);

-- Demo Customers
INSERT INTO customers (customer_id, user_id, name, phone, email, address) VALUES
(1, 4, 'Arun Patel', '9812345678', 'arun.patel@gmail.com', 'Flat 402, Green Glen Layout, Bellandur, Bengaluru'),
(2, 5, 'Priya Nair', '9898765432', 'priya.nair@gmail.com', '12/A, 4th Main, Indiranagar, Bengaluru'),
(3, NULL, 'Karthik Rao', '9741238901', 'karthik.rao@outlook.com', '78, 5th Cross, Koramangala 6th Block, Bengaluru'),
(4, NULL, 'Deepa Sundaram', '9632587410', 'deepa.sundaram@gmail.com', '204, Palm Springs, HSR Layout Sector 2, Bengaluru')
ON DUPLICATE KEY UPDATE name = VALUES(name);

-- Demo Vehicles
INSERT INTO vehicles (vehicle_id, customer_id, vehicle_number, vehicle_model, vehicle_type) VALUES
(1, 1, 'KA-01-MJ-2024', 'Hyundai Creta SX (O)', 'SUV'),
(2, 1, 'KA-03-AB-9876', 'Honda City V MT', 'Sedan'),
(3, 2, 'KA-05-EP-4321', 'Maruti Suzuki Baleno Alpha', 'Hatchback'),
(4, 3, 'KA-51-ND-5544', 'Tata Nexon EV Max', 'Electric SUV'),
(5, 4, 'KA-04-XY-1122', 'Royal Enfield Classic 350', 'Motorcycle')
ON DUPLICATE KEY UPDATE vehicle_model = VALUES(vehicle_model);

-- Demo Services
INSERT INTO services (service_id, vehicle_id, service_type, service_date, description, service_charge, status, assigned_mechanic_id, mechanic_notes) VALUES
(1, 1, 'Periodic Maintenance & Oil Change', '2026-11-01', 'Full 30,000km periodic service, synthetic oil change, oil filter, air filter, wheel rotation.', 4500.00, 'Completed', 2, 'Servicing completed smoothly. Brake pads in good shape. Test drive approved.'),
(2, 2, 'Brake System Overhaul', '2026-11-03', 'Front brake pad replacement, rotor skim and brake fluid flush.', 3200.00, 'In Progress', 2, 'Rotors resurfaced, installing Bosch brake pads.'),
(3, 3, 'AC Cooling & Filter Service', '2026-11-05', 'AC blowing warm air, cabin filter replacement and refrigerant gas recharge.', 2800.00, 'Approved', 3, 'Scheduled for technician inspection on vehicle bay 3.'),
(4, 4, 'Suspension & Steering Checkup', '2026-11-06', 'Creaking sound coming from front left suspension over road bumps.', 1800.00, 'Pending', NULL, 'Pending initial diagnosis and bay assignment.'),
(5, 5, 'Complete Chain Sprocket & Full Service', '2026-11-02', 'Engine tuning, valve clearance, chain cleaning, sprocket kit change.', 3500.00, 'Completed', 3, 'Chain sprocket set replaced with OEM parts. Clean wash completed.')
ON DUPLICATE KEY UPDATE service_type = VALUES(service_type);

-- Demo Payments
INSERT INTO payments (payment_id, service_id, amount, payment_date, payment_method, status, transaction_id) VALUES
(1, 1, 4500.00, '2026-11-01', 'UPI / QR', 'Paid', 'UPI-9847291048'),
(2, 2, 3200.00, '2026-11-03', 'Credit/Debit Card', 'Pending', NULL),
(3, 3, 2800.00, '2026-11-05', 'Cash', 'Pending', NULL),
(4, 4, 1800.00, '2026-11-06', 'Net Banking', 'Pending', NULL),
(5, 5, 3500.00, '2026-11-02', 'UPI / QR', 'Paid', 'UPI-7762518392')
ON DUPLICATE KEY UPDATE amount = VALUES(amount);
