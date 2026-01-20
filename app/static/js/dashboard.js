/* app/static/js/dashboard.js */

// 1. Stats Logic
function updateStats() {
    fetch('/api/stats')
        .then(res => res.json())
        .then(data => {
            if(document.getElementById('cpu-text')) {
                document.getElementById('cpu-text').innerText = data.cpu + '%';
                document.getElementById('cpu-bar').style.width = data.cpu + '%';
                document.getElementById('ram-text').innerText = data.ram + '%';
                document.getElementById('ram-bar').style.width = data.ram + '%';
                document.getElementById('disk-text').innerText = data.disk + '%';
                document.getElementById('disk-bar').style.width = data.disk + '%';
            }
        })
        .catch(console.error);
}

// Start stats loop
updateStats();
setInterval(updateStats, 5000);

// 2. Task Modal Logic
function openModal() { 
    document.getElementById('task-modal').classList.add('active'); 
}

function closeModal() { 
    document.getElementById('task-modal').classList.remove('active'); 
}

function selectColor(hex) { 
    document.getElementById('m-color').value = hex; 
    // Optional: Add visual feedback for selected color here
}

// 3. Save Task Logic
function saveTask() {
    const content = document.getElementById('m-content').value;
    const priority = document.getElementById('m-priority').value;
    const date = document.getElementById('m-date').value;
    const color = document.getElementById('m-color').value;

    if(!content) return;

    fetch('/api/tasks/add', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ content, priority, date, color })
    })
    .then(res => res.json())
    .then(data => {
        if(data.success) {
            const list = document.getElementById('task-list');
            
            // HTML for the new task row
            const html = `
                <div class="task-row" id="task-${data.id}">
                    <div class="priority-dot" style="background-color: ${color}; box-shadow: 0 0 8px ${color};"></div>
                    <div class="task-info">
                        <span class="task-title">${content}</span>
                        <span class="task-meta">${priority} ${date ? '• '+date : ''}</span>
                    </div>
                    <div class="task-actions">
                        <button class="btn-check-circle" id="btn-check-${data.id}" onclick="toggleTask(${data.id})"></button>
                        <button class="btn-delete" onclick="deleteTask(${data.id})"><i class="fas fa-trash"></i></button>
                    </div>
                </div>`;
            
            list.insertAdjacentHTML('afterbegin', html);
            closeModal();
            document.getElementById('m-content').value = ''; // Reset input
        }
    });
}

// 4. Toggle Task Logic
function toggleTask(id) {
    fetch(`/api/tasks/${id}/toggle`, { method: 'POST' })
    .then(res => res.json())
    .then(data => {
        const row = document.getElementById(`task-${id}`);
        const btn = document.getElementById(`btn-check-${id}`);
        
        row.classList.toggle('completed');
        
        if(data.new_state) {
            btn.innerHTML = '<i class="fas fa-check"></i>';
        } else {
            btn.innerHTML = '';
        }
    });
}

// 5. Delete Task Logic
function deleteTask(id) {
    if(!confirm('Delete this task?')) return;
    
    fetch(`/api/tasks/${id}/delete`, { method: 'DELETE' })
    .then(res => res.json())
    .then(data => {
        if(data.success) {
            document.getElementById(`task-${id}`).remove();
        }
    });
}