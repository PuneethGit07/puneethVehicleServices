// Puneeth Vehicle Services - Customer Dashboard Logic

document.addEventListener('DOMContentLoaded', function () {
    document.addEventListener('click', function (e) {
        // 1. Pay Bill
        const payBtn = e.target.closest('.btn-pay-bill');
        if (payBtn) {
            const paymentId = payBtn.getAttribute('data-payment-id');
            const amount = payBtn.getAttribute('data-amount');
            const srvType = payBtn.getAttribute('data-service-type');
            const vehNum = payBtn.getAttribute('data-vehicle-number');
            if (paymentId) {
                payBillModal(paymentId, amount, srvType, vehNum);
            }
            return;
        }

        // 2. Track Service
        const trackBtn = e.target.closest('.btn-track-service');
        if (trackBtn) {
            try {
                const srv = JSON.parse(trackBtn.getAttribute('data-service'));
                showTrackingModal(srv);
            } catch (err) {
                console.error('Failed to parse tracking data:', err);
            }
            return;
        }

        // 3. Book For Vehicle
        const bookBtn = e.target.closest('.btn-book-vehicle');
        if (bookBtn) {
            const vehId = bookBtn.getAttribute('data-vehicle-id');
            const vehNum = bookBtn.getAttribute('data-vehicle-number');
            if (vehId) {
                openBookForVehicle(vehId, vehNum);
            }
            return;
        }

        // 4. Delete Vehicle
        const deleteVehBtn = e.target.closest('.btn-delete-vehicle');
        if (deleteVehBtn) {
            const vehId = deleteVehBtn.getAttribute('data-vehicle-id');
            const vehNum = deleteVehBtn.getAttribute('data-vehicle-number');
            if (vehId) {
                deleteVehicle(vehId, vehNum);
            }
            return;
        }
    });
});

// Add Vehicle
async function submitAddVehicle(event) {
    event.preventDefault();
    const vehicle_number = document.getElementById('veh_number').value.trim().toUpperCase();
    const vehicle_model = document.getElementById('veh_model').value.trim();
    const vehicle_type = document.getElementById('veh_type').value;

    try {
        const res = await fetch('/api/vehicles', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ vehicle_number, vehicle_model, vehicle_type })
        });
        const data = await res.json();
        if (data.success) {
            alert('Vehicle registered successfully!');
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (err) {
        alert('Network error registering vehicle.');
    }
}

// Delete Vehicle
async function deleteVehicle(vehicleId, vehicleNumber) {
    if (!confirm(`Are you sure you want to delete vehicle ${vehicleNumber}? This will also delete any service records associated with it.`)) {
        return;
    }
    try {
        const res = await fetch(`/api/vehicles/${vehicleId}`, { method: 'DELETE' });
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

// Open booking modal pre-selected for a vehicle
function openBookForVehicle(vehicleId, vehicleNumber) {
    const sel = document.getElementById('srv_vehicle_id');
    if (sel) {
        sel.value = vehicleId;
    }
    const modal = new bootstrap.Modal(document.getElementById('bookServiceModal'));
    modal.show();
}

// Book Service
async function submitBookService(event) {
    event.preventDefault();
    const vehicle_id = document.getElementById('srv_vehicle_id').value;
    const service_type = document.getElementById('srv_type').value;
    const service_date = document.getElementById('srv_date').value;
    const description = document.getElementById('srv_desc').value.trim();

    try {
        const res = await fetch('/api/services', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ vehicle_id, service_type, service_date, description })
        });
        const data = await res.json();
        if (data.success) {
            alert('Service appointment requested successfully! Our team will approve it shortly.');
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (err) {
        alert('Network error submitting service request.');
    }
}

// Live Status Tracking Modal
function showTrackingModal(service) {
    document.getElementById('trackSrvId').innerText = '#' + service.service_id;
    document.getElementById('trackSrvType').innerText = service.service_type;
    document.getElementById('trackSrvVeh').innerText = `${service.vehicle_number} (${service.vehicle_model})`;
    document.getElementById('trackTechnician').innerText = service.mechanic_name || 'Technician to be assigned';
    document.getElementById('trackCharge').innerText = service.service_charge > 0 ? `₹${parseFloat(service.service_charge).toFixed(2)}` : 'Quote Pending';
    document.getElementById('trackNotes').innerText = service.mechanic_notes || 'Vehicle awaiting inspection.';

    const steps = ['Pending', 'Approved', 'In Progress', 'Completed'];
    const currentStatus = service.status;

    // Reset steps
    ['stepPending', 'stepApproved', 'stepInProgress', 'stepCompleted'].forEach(id => {
        const el = document.getElementById(id);
        el.classList.remove('active', 'completed');
    });

    const currIdx = steps.indexOf(currentStatus);
    if (currIdx >= 0) {
        if (currIdx >= 0) document.getElementById('stepPending').classList.add(currIdx === 0 ? 'active' : 'completed');
        if (currIdx >= 1) document.getElementById('stepApproved').classList.add(currIdx === 1 ? 'active' : 'completed');
        if (currIdx >= 2) document.getElementById('stepInProgress').classList.add(currIdx === 2 ? 'active' : 'completed');
        if (currIdx >= 3) document.getElementById('stepCompleted').classList.add('completed');
    }

    const modal = new bootstrap.Modal(document.getElementById('trackServiceModal'));
    modal.show();
}

// Pay Bill Modal
function payBillModal(paymentId, amount, srvType, vehNum) {
    document.getElementById('pay_payment_id').value = paymentId;
    document.getElementById('pay_amount_display').innerText = `₹${parseFloat(amount).toFixed(2)}`;
    document.getElementById('pay_service_display').innerText = `${srvType} for ${vehNum}`;

    const modal = new bootstrap.Modal(document.getElementById('payBillModal'));
    modal.show();
}

// Submit Payment
async function submitPayment(event) {
    event.preventDefault();
    const paymentId = document.getElementById('pay_payment_id').value;
    const method = document.getElementById('pay_method').value;

    try {
        const res = await fetch(`/api/payments/${paymentId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ payment_method: method })
        });
        const data = await res.json();
        if (data.success) {
            alert(`Payment of successfully recorded! Ref: ${data.transaction_id}`);
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (err) {
        alert('Network error processing payment.');
    }
}

// Update Profile
async function updateCustomerProfile(event) {
    event.preventDefault();
    const name = document.getElementById('prof_name').value.trim();
    const phone = document.getElementById('prof_phone').value.trim();
    const email = document.getElementById('prof_email').value.trim();
    const address = document.getElementById('prof_address').value.trim();

    // Get current customer ID from profile
    try {
        const getRes = await fetch('/api/customers');
        const getData = await getRes.json();
        if (getData.success && getData.customers.length > 0) {
            const custId = getData.customers[0].customer_id;
            const res = await fetch(`/api/customers/${custId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, phone, email, address })
            });
            const data = await res.json();
            if (data.success) {
                alert('Profile updated successfully in MySQL!');
                location.reload();
            } else {
                alert('Error: ' + data.message);
            }
        }
    } catch (err) {
        alert('Network error updating profile.');
    }
}

