/* app/static/js/dashboard.js */

// --- GLOBAL VARIABLES ---
let editingTaskId = null; 
let deletePendingId = null;
let radialChartInstance = null;

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

// --- 2. QUICK ADD & MODAL ---
function toggleQuickAdd() {
    document.getElementById('quick-add-row').classList.toggle('active');
    document.getElementById('quick-task-input').focus();
}

function handleQuickEnter(e) {
    if(e.key === 'Enter') {
        const content = e.target.value;
        const categorySelect = document.getElementById('quick-category');
        const category = categorySelect ? categorySelect.value : 'general';
        if(content) {
            createTaskAPI(content, 'normal', null, '#3b5bdb', category);
            e.target.value = '';
        }
    }
}

function openModal(isEdit=false) {
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
    document.getElementById('m-is-habit').checked = element.getAttribute('data-ishabit') === 'true';
    const dateVal = element.getAttribute('data-date');
    if(dateVal && dateVal !== 'None') { document.getElementById('m-date').value = dateVal.split(' ')[0]; } 
    else { document.getElementById('m-date').value = ''; }
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
    fetch(url, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) })
    .then(res => res.json()).then(data => { if(data.success) location.reload(); });
}

function createTaskAPI(content, priority, date, color, category = 'general') {
    fetch('/api/tasks/add', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ content, priority, date, color, category })
    }).then(res => res.json()).then(data => { if(data.success) location.reload(); });
}

// --- 3. FILTERING LOGIC ---
function filterTasks(category, btnElement) {
    document.querySelectorAll('.cat-pill').forEach(b => b.classList.remove('active'));
    btnElement.classList.add('active');
    const quickSelect = document.getElementById('quick-category');
    if (quickSelect) quickSelect.value = (category === 'all') ? 'general' : category;

    const rows = document.querySelectorAll('.task-row');
    rows.forEach(row => {
        const rowCat = row.getAttribute('data-category');
        const isCompleted = row.classList.contains('completed');
        let shouldShow = false;

        if (category === 'all') {
            if (!isCompleted) shouldShow = true;
            else if (rowCat === 'general' || rowCat === 'None' || !rowCat) shouldShow = true;
        } else {
            shouldShow = (rowCat === category);
        }
        row.style.display = shouldShow ? 'flex' : 'none';
    });
}

function handleDeleteClick(event, id) {
    event.stopPropagation();
    const row = document.getElementById(`task-${id}`);
    const isHabit = row.querySelector('.task-info').getAttribute('data-ishabit') === 'true';
    if (isHabit && !confirm("⚠️ Warning: Deleting a habit removes its history. Continue?")) return;
    
    row.classList.add('deleting');
    setTimeout(() => {
        fetch(`/api/tasks/${id}/delete`, { method: 'DELETE' }).then(res => res.json()).then(data => { if(data.success) { row.remove(); loadCharts(); } });
    }, 300);
}

function toggleTask(id) {
    if(event) event.stopPropagation(); 
    fetch(`/api/tasks/${id}/toggle`, { method: 'POST' }).then(res => res.json()).then(data => {
        const row = document.getElementById(`task-${id}`);
        const btn = document.getElementById(`btn-check-${id}`);
        const taskList = document.getElementById('task-list');
        
        if (data.new_state) {
            row.classList.add('completed');
            btn.innerHTML = '<i class="fas fa-check"></i>';
            taskList.appendChild(row); 
            
            const activeCat = document.querySelector('.cat-pill.active').innerText.trim().toLowerCase();
            const rowCat = row.getAttribute('data-category');
            if(activeCat === 'all' && rowCat !== 'general') row.style.display = 'none';
        } else {
            row.classList.remove('completed');
            btn.innerHTML = '';
            taskList.prepend(row);
            row.style.display = 'flex'; 
        }

        // ✅ UPDATE DATE LABEL INSTANTLY
        if (data.new_date_label) {
            const metaSpan = row.querySelector('.task-meta');
            if (metaSpan) {
                const prio = data.priority.charAt(0).toUpperCase() + data.priority.slice(1);
                let html = `${prio} • `;
                
                if (data.new_date_label.includes('overdue')) {
                    html += `<span style="color: var(--danger-red); font-weight: bold">${data.new_date_label}</span>`;
                } else if (data.new_date_label === 'Today') {
                    html += `<span style="color: var(--accent-blue); font-weight: bold">Today</span>`;
                } else {
                    html += data.new_date_label;
                }
                
                // Assuming it's recurring if we are updating the date
                html += ` • <i class="fas fa-sync-alt" title="Repeats"></i>`;
                metaSpan.innerHTML = html;
            }
        }

        loadCharts();
    });
}

// --- 4. GRAPH INTERACTION ---
function loadCharts() {
    fetch('/api/stats/charts')
    .then(res => res.json())
    .then(data => {
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
                
                const label = document.createElement('div');
                label.className = 'habit-label';
                label.innerText = habit.name;
                row.appendChild(label);

                const dots = document.createElement('div');
                dots.className = 'habit-grid';

                habit.data.forEach(point => {
                    const dot = document.createElement('div');
                    dot.className = 'habit-dot';
                    const isDone = (point.y === 100);

                    if (isDone) {
                        dot.style.backgroundColor = point.fillColor;
                        dot.style.boxShadow = `0 0 6px ${point.fillColor}`;
                        dot.setAttribute('data-date', `${point.x}: Completed`);
                    } else {
                        dot.style.backgroundColor = '#1A1A1A';
                        dot.setAttribute('data-date', `${point.x}: Missed`);
                        
                        // ✅ FIX: PASSING THE REAL COLOR (habit.color), NOT THE EMPTY COLOR (point.fillColor)
                        dot.onclick = function() {
                           handleDotClick(dot, habit.id, point.real_date, habit.color); 
                        };
                    }
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

// --- 5. DOT CLICK HANDLER ---
let clickTimers = {};

function handleDotClick(dotElement, taskId, dateStr, taskColor) {
    if (!dotElement.classList.contains('confirming')) {
        // CLICK 1: DIM COLOR
        dotElement.classList.add('confirming');
        dotElement.style.backgroundColor = taskColor; 
        dotElement.style.opacity = '0.4'; 
        
        dotElement.dataset.timer = setTimeout(() => {
            dotElement.classList.remove('confirming');
            dotElement.style.backgroundColor = '#1A1A1A';
            dotElement.style.opacity = '1';
        }, 3000);
        
    } else {
        // CLICK 2: CONFIRM
        clearTimeout(dotElement.dataset.timer);
        dotElement.classList.remove('confirming');
        
        // Paint it solid instantly
        dotElement.style.opacity = '1';
        dotElement.style.boxShadow = `0 0 8px ${taskColor}`;
        dotElement.style.backgroundColor = taskColor;
        
        // Update Text
        const currentLabel = dotElement.getAttribute('data-date').split(':')[0];
        dotElement.setAttribute('data-date', `${currentLabel}: Completed`);
        
        // Lock interaction
        dotElement.onclick = null;
        dotElement.style.cursor = 'default';
        
        fetch(`/api/tasks/${taskId}/history/add`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ date: dateStr })
        }).then(res => res.json()).then(data => {
            if(!data.success) {
                alert("Error saving habit");
                dotElement.style.backgroundColor = '#1A1A1A'; 
            }
        });
    }
}

// --- INIT ---
document.addEventListener('DOMContentLoaded', () => {
    loadCharts();
    const modal = document.getElementById('task-modal');
    if (modal) modal.addEventListener('click', (e) => { if (e.target === modal) closeModal(); });
});