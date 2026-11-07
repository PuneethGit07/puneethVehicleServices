// Puneeth Vehicle Services - Admin Dashboard Logic

let revenueChartInstance = null;
let statusChartInstance = null;

function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

document.addEventListener('DOMContentLoaded', function () {
    loadAdminStatsAndCharts();
    initAdminActionListeners();
});

// Delegated event listeners for action buttons to avoid unsafe inline Jinja interpolation
function initAdminActionListeners() {
    document.addEventListener('click', function (e) {
        // 1. Edit Service
        const editServiceBtn = e.target.closest('.btn-edit-service');
        if (editServiceBtn) {
            try {
                const srv = JSON.parse(editServiceBtn.getAttribute('data-service'));
                openEditServiceModal(srv);
            } catch (err) {
                console.error('Failed to parse service data:', err);
            }
            return;
        }

        // 2. Delete Service
        const deleteServiceBtn = e.target.closest('.btn-delete-service');
        if (deleteServiceBtn) {
            const id = deleteServiceBtn.getAttribute('data-service-id');
            if (id) {
                adminDeleteService(id);
            }
            return;
        }

        // 3. Edit Customer
        const editCustomerBtn = e.target.closest('.btn-edit-customer');
        if (editCustomerBtn) {
            try {
                const cust = JSON.parse(editCustomerBtn.getAttribute('data-customer'));
                openEditCustomerModal(cust);
            } catch (err) {
                console.error('Failed to parse customer data:', err);
            }
            return;
        }

        // 4. Delete Customer
        const deleteCustomerBtn = e.target.closest('.btn-delete-customer');
        if (deleteCustomerBtn) {
            const id = deleteCustomerBtn.getAttribute('data-customer-id');
            const name = deleteCustomerBtn.getAttribute('data-customer-name') || ('Customer #' + id);
            if (id) {
                adminDeleteCustomer(id, name);
            }
            return;
        }

        // 5. Edit Vehicle
        const editVehicleBtn = e.target.closest('.btn-edit-vehicle');
        if (editVehicleBtn) {
            try {
                const veh = JSON.parse(editVehicleBtn.getAttribute('data-vehicle'));
                openEditVehicleModal(veh);
            } catch (err) {
                console.error('Failed to parse vehicle data:', err);
            }
            return;
        }

        // 6. Delete Vehicle
        const deleteVehicleBtn = e.target.closest('.btn-delete-vehicle');
        if (deleteVehicleBtn) {
            const id = deleteVehicleBtn.getAttribute('data-vehicle-id');
            const regNumber = deleteVehicleBtn.getAttribute('data-vehicle-number') || ('Vehicle #' + id);
            if (id) {
                adminDeleteVehicle(id, regNumber);
            }
            return;
        }

        // 7. Edit Payment
        const editPaymentBtn = e.target.closest('.btn-edit-payment');
        if (editPaymentBtn) {
            try {
                const pay = JSON.parse(editPaymentBtn.getAttribute('data-payment'));
                openEditPaymentModal(pay);
            } catch (err) {
                console.error('Failed to parse payment data:', err);
            }
            return;
        }

        // 8. Delete Payment
        const deletePaymentBtn = e.target.closest('.btn-delete-payment');
        if (deletePaymentBtn) {
            const id = deletePaymentBtn.getAttribute('data-payment-id');
            if (id) {
                adminDeletePayment(id);
            }
            return;
        }
    });
}

// Load stats and render Chart.js
async function loadAdminStatsAndCharts() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        if (!data.success) return;

        // Update KPI Counters
        document.getElementById('kpi_customers').innerText = data.stats.total_customers;
        document.getElementById('kpi_vehicles').innerText = data.stats.total_vehicles;
        document.getElementById('kpi_services').innerText = data.stats.total_services;
        document.getElementById('kpi_pending').innerText = data.stats.pending_services;
        document.getElementById('kpi_completed').innerText = data.stats.completed_services;
        document.getElementById('kpi_revenue').innerText = '₹' + parseFloat(data.stats.total_revenue).toFixed(2);

        // Render Monthly Revenue Chart
        renderRevenueChart(data.charts.monthly_revenue);

        // Render Status Doughnut Chart
        renderStatusDoughnut(data.charts.status_distribution);
    } catch (err) {
        console.error('Error loading dashboard stats:', err);
    }
}

function refreshAdminStats() {
    loadAdminStatsAndCharts();
    alert('Dashboard stats refreshed from MySQL!');
}

function renderRevenueChart(monthlyData) {
    const ctx = document.getElementById('revenueChart');
    if (!ctx) return;

    const labels = (monthlyData && monthlyData.length > 0) ? monthlyData.map(d => d.month_label) : ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const values = (monthlyData && monthlyData.length > 0) ? monthlyData.map(d => parseFloat(d.total)) : [12000, 18500, 24000, 31000, 28500, 35000];

    if (revenueChartInstance) {
        revenueChartInstance.destroy();
    }

    revenueChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Revenue (₹)',
                data: values,
                backgroundColor: 'rgba(255, 107, 0, 0.85)',
                borderColor: '#FF6B00',
                borderWidth: 1.5,
                borderRadius: 6,
                maxBarThickness: 45
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: val => '₹' + val.toLocaleString()
                    },
                    grid: { color: 'rgba(0,0,0,0.05)' }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
}

function renderStatusDoughnut(statusData) {
    const ctx = document.getElementById('statusDoughnutChart');
    if (!ctx) return;

    const labels = (statusData && statusData.length > 0) ? statusData.map(d => d.status) : ['Completed', 'In Progress', 'Pending', 'Approved'];
    const values = (statusData && statusData.length > 0) ? statusData.map(d => d.count) : [5, 2, 2, 1];

    const colorMap = {
        'Completed': '#10B981',
        'In Progress': '#F59E0B',
        'Approved': '#3B82F6',
        'Pending': '#EF4444',
        'Cancelled': '#6B7280'
    };

    const bgColors = labels.map(l => colorMap[l] || '#FF6B00');

    if (statusChartInstance) {
        statusChartInstance.destroy();
    }

    statusChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: bgColors,
                borderWidth: 2,
                borderColor: '#FFFFFF'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } }
            },
            cutout: '68%'
        }
    });
}

// ==============================================================================
// CUSTOMER MANAGEMENT
// ==============================================================================
function resetCustomerForm() {
    document.getElementById('cust_edit_id').value = '';
    document.getElementById('adminCustomerModalTitle').innerHTML = '<i class="fa-solid fa-user-plus text-orange"></i> Add New Customer';
    document.getElementById('cust_name').value = '';
    document.getElementById('cust_phone').value = '';
    document.getElementById('cust_email').value = '';
    document.getElementById('cust_address').value = '';
}

function openEditCustomerModal(cust) {
    document.getElementById('cust_edit_id').value = cust.customer_id;
    document.getElementById('adminCustomerModalTitle').innerHTML = '<i class="fa-solid fa-user-pen text-orange"></i> Edit Customer #' + cust.customer_id;
    document.getElementById('cust_name').value = cust.name;
    document.getElementById('cust_phone').value = cust.phone;
    document.getElementById('cust_email').value = cust.email;
    document.getElementById('cust_address').value = cust.address || '';

    const modal = new bootstrap.Modal(document.getElementById('adminCustomerModal'));
    modal.show();
}

async function submitAdminCustomer(event) {
    event.preventDefault();
    const id = document.getElementById('cust_edit_id').value;
    const name = document.getElementById('cust_name').value.trim();
    const phone = document.getElementById('cust_phone').value.trim();
    const email = document.getElementById('cust_email').value.trim();
    const address = document.getElementById('cust_address').value.trim();

    const isEdit = Boolean(id);
    const url = isEdit ? `/api/customers/${id}` : '/api/customers';
    const method = isEdit ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, phone, email, address })
        });
        const data = await res.json();
        if (data.success) {
            alert(data.message);
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (err) {
        alert('Network error saving customer.');
    }
}

async function adminDeleteCustomer(id, name) {
    if (!confirm(`Delete customer "${name}"? This cascades to all vehicles, services, and payments associated with this customer in MySQL.`)) {
        return;
    }
    try {
        const res = await fetch(`/api/customers/${id}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
            alert(data.message);
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (err) {
        alert('Network error deleting customer.');
    }
}

function filterAdminCustomers() {
    const input = document.getElementById('customerSearch').value.toLowerCase();
    const table = document.getElementById('adminCustomersTable');
    if (!table) return;
    const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');

    for (let row of rows) {
        row.style.display = row.textContent.toLowerCase().includes(input) ? '' : 'none';
    }
}

// ==============================================================================
// VEHICLE MANAGEMENT
// ==============================================================================
function resetVehicleForm() {
    document.getElementById('veh_edit_id').value = '';
    document.getElementById('adminVehicleModalTitle').innerHTML = '<i class="fa-solid fa-car text-orange"></i> Add New Vehicle';
    document.getElementById('veh_owner_id').value = '';
    document.getElementById('veh_reg_number').value = '';
    document.getElementById('veh_reg_model').value = '';
    document.getElementById('veh_reg_type').value = 'SUV';
}

function openEditVehicleModal(veh) {
    document.getElementById('veh_edit_id').value = veh.vehicle_id;
    document.getElementById('adminVehicleModalTitle').innerHTML = '<i class="fa-solid fa-car text-orange"></i> Edit Vehicle #' + veh.vehicle_id;
    document.getElementById('veh_owner_id').value = veh.customer_id;
    document.getElementById('veh_reg_number').value = veh.vehicle_number;
    document.getElementById('veh_reg_model').value = veh.vehicle_model;
    document.getElementById('veh_reg_type').value = veh.vehicle_type;

    const modal = new bootstrap.Modal(document.getElementById('adminVehicleModal'));
    modal.show();
}

async function submitAdminVehicle(event) {
    event.preventDefault();
    const id = document.getElementById('veh_edit_id').value;
    const customer_id = document.getElementById('veh_owner_id').value;
    const vehicle_number = document.getElementById('veh_reg_number').value.trim().toUpperCase();
    const vehicle_model = document.getElementById('veh_reg_model').value.trim();
    const vehicle_type = document.getElementById('veh_reg_type').value;

    const isEdit = Boolean(id);
    const url = isEdit ? `/api/vehicles/${id}` : '/api/vehicles';
    const method = isEdit ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ customer_id, vehicle_number, vehicle_model, vehicle_type })
        });
        const data = await res.json();
        if (data.success) {
            alert(data.message);
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (err) {
        alert('Network error saving vehicle.');
    }
}

async function adminDeleteVehicle(id, vehicleNumber) {
    if (!confirm(`Delete vehicle "${vehicleNumber}"? All services and payments for this vehicle will also be removed in MySQL.`)) {
        return;
    }
    try {
        const res = await fetch(`/api/vehicles/${id}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
            alert(data.message);
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (err) {
        alert('Network error deleting vehicle.');
    }
}

function filterAdminVehicles() {
    const input = document.getElementById('vehicleSearch').value.toLowerCase();
    const table = document.getElementById('adminVehiclesTable');
    if (!table) return;
    const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');

    for (let row of rows) {
        row.style.display = row.textContent.toLowerCase().includes(input) ? '' : 'none';
    }
}

// ==============================================================================
// SERVICE MANAGEMENT
// ==============================================================================
function resetServiceForm() {
    document.getElementById('srv_edit_id').value = '';
    document.getElementById('adminServiceModalTitle').innerHTML = '<i class="fa-solid fa-wrench text-orange"></i> Add New Service Record';
    document.getElementById('srv_vehicle_select_group').style.display = 'block';
    document.getElementById('adm_srv_vehicle_id').required = true;
    document.getElementById('adm_srv_vehicle_id').value = '';
    document.getElementById('adm_srv_type').value = 'Periodic Maintenance & Oil Change';
    document.getElementById('adm_srv_date').value = new Date().toISOString().split('T')[0];
    document.getElementById('adm_srv_charge').value = '0.00';
    document.getElementById('adm_srv_status').value = 'Pending';
    document.getElementById('adm_srv_mechanic').value = '';
    document.getElementById('adm_srv_desc').value = '';
    document.getElementById('adm_srv_notes').value = '';
}

function openEditServiceModal(srv) {
    document.getElementById('srv_edit_id').value = srv.service_id;
    document.getElementById('adminServiceModalTitle').innerHTML = `<i class="fa-solid fa-wrench text-orange"></i> Edit Service #${srv.service_id} (${escapeHtml(srv.vehicle_number)})`;
    document.getElementById('srv_vehicle_select_group').style.display = 'block';
    document.getElementById('adm_srv_vehicle_id').value = srv.vehicle_id;
    document.getElementById('adm_srv_type').value = srv.service_type;
    document.getElementById('adm_srv_date').value = srv.service_date;
    document.getElementById('adm_srv_charge').value = srv.service_charge;
    document.getElementById('adm_srv_status').value = srv.status;
    document.getElementById('adm_srv_mechanic').value = srv.assigned_mechanic_id || '';
    document.getElementById('adm_srv_desc').value = srv.description || '';
    document.getElementById('adm_srv_notes').value = srv.mechanic_notes || '';

    const modal = new bootstrap.Modal(document.getElementById('adminServiceModal'));
    modal.show();
}

async function submitAdminService(event) {
    event.preventDefault();
    const id = document.getElementById('srv_edit_id').value;
    const vehicle_id = document.getElementById('adm_srv_vehicle_id').value;
    const service_type = document.getElementById('adm_srv_type').value;
    const service_date = document.getElementById('adm_srv_date').value;
    const service_charge = document.getElementById('adm_srv_charge').value;
    const status = document.getElementById('adm_srv_status').value;
    const assigned_mechanic_id = document.getElementById('adm_srv_mechanic').value || null;
    const description = document.getElementById('adm_srv_desc').value.trim();
    const mechanic_notes = document.getElementById('adm_srv_notes').value.trim();

    const isEdit = Boolean(id);
    const url = isEdit ? `/api/services/${id}` : '/api/services';
    const method = isEdit ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                vehicle_id, service_type, service_date, service_charge,
                status, assigned_mechanic_id, description, mechanic_notes
            })
        });
        const data = await res.json();
        if (data.success) {
            alert(data.message);
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (err) {
        alert('Network error saving service record.');
    }
}

async function adminDeleteService(id) {
    if (!confirm(`Permanently delete Service #${id}? Associated payments will also be deleted from MySQL.`)) {
        return;
    }
    try {
        const res = await fetch(`/api/services/${id}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
            alert(data.message);
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (err) {
        alert('Network error deleting service.');
    }
}

function filterAdminServices() {
    const input = document.getElementById('serviceSearch').value.toLowerCase();
    const statusFilter = document.getElementById('filterServiceStatus').value;
    const table = document.getElementById('adminServicesTable');
    if (!table) return;
    const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');

    for (let row of rows) {
        const text = row.textContent.toLowerCase();
        const rowStatus = row.getAttribute('data-status');
        const matchesSearch = text.includes(input);
        const matchesStatus = !statusFilter || rowStatus === statusFilter;

        row.style.display = (matchesSearch && matchesStatus) ? '' : 'none';
    }
}

// ==============================================================================
// PAYMENT MANAGEMENT
// ==============================================================================
function resetPaymentForm() {
    document.getElementById('pay_edit_id').value = '';
    document.getElementById('adminPaymentModalTitle').innerHTML = '<i class="fa-solid fa-receipt text-orange"></i> Record New Payment';
    document.getElementById('pay_service_select_group').style.display = 'block';
    document.getElementById('adm_pay_service_id').required = true;
    document.getElementById('adm_pay_service_id').value = '';
    document.getElementById('adm_pay_amount').value = '';
    document.getElementById('adm_pay_date').value = new Date().toISOString().split('T')[0];
    document.getElementById('adm_pay_method').value = 'UPI / QR';
    document.getElementById('adm_pay_status').value = 'Paid';
    document.getElementById('adm_pay_txid').value = '';
}

function openEditPaymentModal(pay) {
    document.getElementById('pay_edit_id').value = pay.payment_id;
    document.getElementById('adminPaymentModalTitle').innerHTML = `<i class="fa-solid fa-receipt text-orange"></i> Edit Payment #${pay.payment_id}`;
    document.getElementById('pay_service_select_group').style.display = 'block';
    document.getElementById('adm_pay_service_id').value = pay.service_id;
    document.getElementById('adm_pay_amount').value = pay.amount;
    document.getElementById('adm_pay_date').value = pay.payment_date;
    document.getElementById('adm_pay_method').value = pay.payment_method;
    document.getElementById('adm_pay_status').value = pay.status;
    document.getElementById('adm_pay_txid').value = pay.transaction_id || '';

    const modal = new bootstrap.Modal(document.getElementById('adminPaymentModal'));
    modal.show();
}

async function submitAdminPayment(event) {
    event.preventDefault();
    const id = document.getElementById('pay_edit_id').value;
    const service_id = document.getElementById('adm_pay_service_id').value;
    const amount = document.getElementById('adm_pay_amount').value;
    const payment_date = document.getElementById('adm_pay_date').value;
    const payment_method = document.getElementById('adm_pay_method').value;
    const status = document.getElementById('adm_pay_status').value;
    const transaction_id = document.getElementById('adm_pay_txid').value.trim();

    const isEdit = Boolean(id);
    const url = isEdit ? `/api/payments/${id}` : '/api/payments';
    const method = isEdit ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ service_id, amount, payment_date, payment_method, status, transaction_id })
        });
        const data = await res.json();
        if (data.success) {
            alert(data.message);
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (err) {
        alert('Network error saving payment.');
    }
}

async function adminDeletePayment(id) {
    if (!confirm(`Permanently delete Payment record #${id}?`)) {
        return;
    }
    try {
        const res = await fetch(`/api/payments/${id}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
            alert(data.message);
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (err) {
        alert('Network error deleting payment.');
    }
}

function filterAdminPayments() {
    const input = document.getElementById('paymentSearch').value.toLowerCase();
    const statusFilter = document.getElementById('filterPaymentStatus').value;
    const table = document.getElementById('adminPaymentsTable');
    if (!table) return;
    const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');

    for (let row of rows) {
        const text = row.textContent.toLowerCase();
        const rowStatus = row.getAttribute('data-status');
        const matchesSearch = text.includes(input);
        const matchesStatus = !statusFilter || rowStatus === statusFilter;

        row.style.display = (matchesSearch && matchesStatus) ? '' : 'none';
    }
}

// ==============================================================================
// HERO PHOTOGRAPH UPLOAD
// ==============================================================================
async function submitHeroUpload(event) {
    event.preventDefault();
    const fileInput = document.getElementById('hero_image_file');
    if (!fileInput.files || fileInput.files.length === 0) {
        alert('Please choose an image file first.');
        return;
    }

    const formData = new FormData();
    formData.append('hero_image', fileInput.files[0]);

    try {
        const res = await fetch('/api/upload-hero', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (data.success) {
            alert(data.message);
            document.getElementById('heroPreviewImg').src = data.url + '?t=' + new Date().getTime();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (err) {
        alert('Network error uploading banner photograph.');
    }
}

