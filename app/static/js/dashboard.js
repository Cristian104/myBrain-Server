/* app/static/js/dashboard.js */

// --- GLOBAL VARIABLES ---
let editingTaskId = null; 
let deletePendingId = null;

// Store chart instances globally so we can destroy them later
let radialChartInstance = null;
let habitChartInstance = null;


// --- 1. STATS ---
function updateStats() {
    fetch('/api/stats').then(res=>res.json()).then(data => {
        if(document.getElementById('cpu-text')) {
            document.getElementById('cpu-text').innerText = data.cpu + '%';
            document.getElementById('cpu-bar').style.width = data.cpu + '%';
            document.getElementById('ram-text').innerText = data.ram + '%';
            document.getElementById('ram-bar').style.width = data.ram + '%';
            document.getElementById('disk-text').innerText = data.disk + '%';
            document.getElementById('disk-bar').style.width = data.disk + '%';
        }
    }).catch(console.error);
}
updateStats();
setInterval(updateStats, 5000);

// --- 2. QUICK ADD LOGIC ---
function toggleQuickAdd() {
    const row = document.getElementById('quick-add-row');
    row.classList.toggle('active');
    if(row.classList.contains('active')) {
        document.getElementById('quick-task-input').focus();
    }
}

function handleQuickEnter(e) {
    if(e.key === 'Enter') {
        const content = e.target.value;
        const categorySelect = document.getElementById('quick-category');
        const category = categorySelect ? categorySelect.value : 'general';

        if(content) {
            createTaskAPI(content, 'normal', null, '#3b5bdb', category);
            e.target.value = '';
            toggleQuickAdd();
        }
    }
}

// --- 3. MODAL LOGIC ---
function openModal(isEdit = false) {
    const modal = document.getElementById('task-modal');
    const title = modal.querySelector('h3');
    const btn = modal.querySelector('.btn-save');

    if (isEdit) {
        title.innerText = "Edit Task";
        btn.innerText = "Save Changes";
    } else {
        title.innerText = "Create New Task";
        btn.innerText = "Create Task";
        document.getElementById('m-content').value = '';
        document.getElementById('m-date').value = '';
        document.getElementById('m-category').value = 'general';
        document.getElementById('m-is-habit').checked = false; 
        editingTaskId = null;
    }
    modal.classList.add('active');
}

function closeModal() { document.getElementById('task-modal').classList.remove('active'); }
function selectColor(hex) { document.getElementById('m-color').value = hex; }

function editTask(element) {
    editingTaskId = element.getAttribute('data-id');
    
    document.getElementById('m-content').value = element.getAttribute('data-content');
    document.getElementById('m-priority').value = element.getAttribute('data-priority');
    document.getElementById('m-color').value = element.getAttribute('data-color');
    document.getElementById('m-recurrence').value = element.getAttribute('data-recurrence');
    document.getElementById('m-category').value = element.getAttribute('data-category');

    const isHabit = element.getAttribute('data-ishabit') === 'true';
    document.getElementById('m-is-habit').checked = isHabit;

    const dateVal = element.getAttribute('data-date');
    if(dateVal && dateVal !== 'None') {
        const cleanDate = dateVal.split(' ')[0]; 
        document.getElementById('m-date').value = cleanDate;
    } else {
        document.getElementById('m-date').value = '';
    }
    
    openModal(true);
}

function submitTaskForm() {
    const content = document.getElementById('m-content').value;
    const priority = document.getElementById('m-priority').value;
    const date = document.getElementById('m-date').value;
    const color = document.getElementById('m-color').value;
    const recurrence = document.getElementById('m-recurrence').value;
    const category = document.getElementById('m-category').value;
    const is_habit = document.getElementById('m-is-habit').checked;

    if(!content) return;

    const payload = { content, priority, date, color, recurrence, category, is_habit };
    const url = editingTaskId ? `/api/tasks/${editingTaskId}/edit` : '/api/tasks/add';
    
    fetch(url, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    }).then(res => res.json()).then(data => {
        if(data.success) location.reload();
    });
}

function createTaskAPI(content, priority, date, color, category = 'general') {
    fetch('/api/tasks/add', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ content, priority, date, color, category })
    })
    .then(res => res.json())
    .then(data => {
        if(data.success) location.reload(); 
    });
}

// --- 4. CATEGORY FILTERING ---
function filterTasks(category, btnElement) {
    document.querySelectorAll('.cat-pill').forEach(b => b.classList.remove('active'));
    btnElement.classList.add('active');

    const rows = document.querySelectorAll('.task-row');
    rows.forEach(row => {
        const rowCat = row.getAttribute('data-category');
        if (category === 'all' || rowCat === category) {
            row.style.display = 'flex';
        } else {
            row.style.display = 'none';
        }
    });
}

// --- 5. SMART DELETE LOGIC ---
function handleDeleteClick(event, id) {
    event.stopPropagation();
    
    const row = document.getElementById(`task-${id}`);
    const isHabit = row.querySelector('.task-info').getAttribute('data-ishabit') === 'true';
    
    if (isHabit) {
        const confirmed = confirm("⚠️ Warning: This task is part of your Habit Tracker.\nDeleting it will remove all history from the charts.\n\nAre you sure?");
        if (!confirmed) return;
    }

    const isCompleted = row.classList.contains('completed');
    const isArmed = (deletePendingId === id);

    if (isCompleted || isArmed || isHabit) {
        row.classList.add('deleting');
        setTimeout(() => {
            fetch(`/api/tasks/${id}/delete`, { method: 'DELETE' })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    row.remove();
                    loadCharts(); // Refresh charts
                }
            });
        }, 300);
        deletePendingId = null;
    } else {
        if (deletePendingId) resetPendingDelete();
        deletePendingId = id;
        row.classList.add('delete-pending');
        document.addEventListener('click', handleOutsideClick);
    }
}

function resetPendingDelete() {
    if(!deletePendingId) return;
    const row = document.getElementById(`task-${deletePendingId}`);
    if(row) row.classList.remove('delete-pending');
    deletePendingId = null;
    document.removeEventListener('click', handleOutsideClick);
}

function handleOutsideClick(event) {
    if (!event.target.closest('.btn-delete')) {
        resetPendingDelete();
    }
}

// --- 6. TOGGLE LOGIC ---
function toggleTask(id) {
    if(event) event.stopPropagation(); 
    
    fetch(`/api/tasks/${id}/toggle`, { method: 'POST' })
    .then(res => res.json())
    .then(data => {
        const row = document.getElementById(`task-${id}`);
        const btn = document.getElementById(`btn-check-${id}`);
        const taskList = document.getElementById('task-list');

        if (data.new_state) {
            row.classList.add('completed');
            btn.innerHTML = '<i class="fas fa-check"></i>';
            taskList.appendChild(row); 
        } else {
            row.classList.remove('completed');
            btn.innerHTML = '';
            taskList.prepend(row); 
        }
        
        loadCharts(); // Refresh charts
    });
}

// --- 7. CHARTS LOGIC (Responsive Grid Fix) ---
function loadCharts() {
    fetch('/api/stats/charts')
    .then(res => res.json())
    .then(data => {
        
        // --- A. RADIAL CHART (ApexCharts) ---
        const radialContainer = document.querySelector("#radial-chart");
        if(radialContainer) {
            if(radialChartInstance) radialChartInstance.destroy();
            var radialOptions = {
                series: data.radial,
                chart: { height: 280, type: 'radialBar', fontFamily: 'Inter', background: 'transparent' },
                plotOptions: {
                    radialBar: {
                        dataLabels: {
                            total: { show: true, label: 'Focus', color: '#fff', formatter: (w) => Math.round(w.globals.seriesTotals.reduce((a, b) => a + b, 0) / 5) + "%" }
                        },
                        track: { background: '#222' }
                    }
                },
                labels: data.radial_labels,
                colors: ['#9b59b6', '#f1c40f', '#e74c3c', '#3b5bdb', '#2ecc71'], 
                theme: { mode: 'dark' }
            };
            radialChartInstance = new ApexCharts(radialContainer, radialOptions);
            radialChartInstance.render();
        }

        // --- B. HABIT GRID (Responsive HTML Builder) ---
        const gridContainer = document.getElementById('habit-heatmap');
        if (gridContainer) {
            gridContainer.innerHTML = ''; 

            if (!data.heatmap || data.heatmap.length === 0) {
                gridContainer.innerHTML = '<p style="color:#555; text-align:center; padding-top:40px;">No habits tracked yet.</p>';
                return;
            }

            const wrapper = document.createElement('div');
            wrapper.className = 'habit-container';

            data.heatmap.forEach(habit => {
                const row = document.createElement('div');
                row.className = 'habit-row';

                // Label
                const label = document.createElement('div');
                label.className = 'habit-label';
                label.innerText = habit.name;
                row.appendChild(label);

                // Dots Container
                const dots = document.createElement('div');
                dots.className = 'habit-grid';

                habit.data.forEach(point => {
                    const dot = document.createElement('div');
                    dot.className = 'habit-dot';
                    
                    // ✅ SAFETY CHECK: Only apply color if explicitly DONE (100)
                    // This fixes the "Active by default" bug if the backend sends loose data
                    const isDone = (point.y === 100);

                    if (isDone && point.fillColor && point.fillColor !== '#1A1A1A') {
                        dot.style.backgroundColor = point.fillColor;
                        dot.style.boxShadow = `0 0 6px ${point.fillColor}`; 
                    } else {
                        // Force empty state
                        dot.style.backgroundColor = '#1A1A1A';
                        dot.style.boxShadow = 'none';
                    }
                    
                    // Tooltip
                    const status = isDone ? "Completed" : "Missed";
                    dot.setAttribute('data-date', `${point.x}: ${status}`);
                    
                    dots.appendChild(dot);
                });

                row.appendChild(dots);
                wrapper.appendChild(row);
            });

            gridContainer.appendChild(wrapper);
        }
    })
    .catch(console.error);
}

// --- INIT LISTENERS ---
document.addEventListener('DOMContentLoaded', () => {
    loadCharts();
    
    const modal = document.getElementById('task-modal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeModal();
        });
    }
});