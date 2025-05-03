function updateApplicationStatus(appId, field, value) {
    fetch(`/api/applications/${appId}/status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            field: field,
            value: value
        })
    })
    .then(response => {
        if (!response.ok) throw new Error('Failed to update status');
        return response.json();
    })
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert(data.message || 'Failed to update application status');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to update application status');
    });
}

function toggleEdit() {
    const editableFields = document.querySelectorAll('.editable-field');
    const saveButton = document.getElementById('saveProfileBtn');
    
    editableFields.forEach(field => {
        field.disabled = !field.disabled;
    });
    
    saveButton.classList.toggle('d-none');
}taskkill /f /im python.exe
python app.py