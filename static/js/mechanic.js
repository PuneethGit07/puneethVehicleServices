// Puneeth Vehicle Services - Mechanic Dashboard Logic

document.addEventListener('DOMContentLoaded', function () {
    document.addEventListener('click', function (e) {
        const updateBayBtn = e.target.closest('.btn-update-bay');
        if (updateBayBtn) {
            try {
                const srv = JSON.parse(updateBayBtn.getAttribute('data-service'));
                openUpdateProgressModal(srv);
            } catch (err) {
                console.error('Failed to parse service data:', err);
            }
        }
    });
});

function openUpdateProgressModal(service) {
    document.getElementById('prog_service_id').value = service.service_id;
    document.getElementById('prog_id_badge').innerText = '#' + service.service_id;
    document.getElementById('prog_vehicle_number').innerText = `${service.vehicle_number} (${service.vehicle_model})`;
    document.getElementById('prog_service_type').innerText = service.service_type;
    document.getElementById('prog_status').value = service.status;
    document.getElementById('prog_notes').value = service.mechanic_notes || '';

    const modal = new bootstrap.Modal(document.getElementById('updateProgressModal'));
    modal.show();
}

function quickMarkCompleted() {
    document.getElementById('prog_status').value = 'Completed';
    const currentNotes = document.getElementById('prog_notes').value;
    if (!currentNotes.includes('Completed')) {
        document.getElementById('prog_notes').value = (currentNotes ? currentNotes + '\n' : '') + 'Service completed and tested. Ready for customer delivery.';
    }
}

async function submitProgressUpdate(event) {
    event.preventDefault();
    const service_id = document.getElementById('prog_service_id').value;
    const status = document.getElementById('prog_status').value;
    const mechanic_notes = document.getElementById('prog_notes').value.trim();

    try {
        const res = await fetch(`/api/services/${service_id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status, mechanic_notes })
        });
        const data = await res.json();
        if (data.success) {
            alert('Service bay updates saved successfully to MySQL!');
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (err) {
        alert('Network error saving updates.');
    }
}

function filterMechanicTable() {
    const input = document.getElementById('mechanicSearch').value.toLowerCase();
    const table = document.getElementById('mechanicTable');
    if (!table) return;
    const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');

    for (let i = 0; i < rows.length; i++) {
        const text = rows[i].textContent.toLowerCase();
        rows[i].style.display = text.includes(input) ? '' : 'none';
    }
}

