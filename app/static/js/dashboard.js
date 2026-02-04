/* app/static/js/dashboard.js */

// --- GLOBAL VARIABLES ---
let editingTaskId = null; 
let deletingTaskId = null; 
let statsInterval = null; 
let currentDataVersion = null; 
let lastActionTime = 0; 

// --- 1. SMART STATS POLLING ---
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

            if (currentDataVersion === null) {
                currentDataVersion = data.data_version;
            } else if (data.data_version > currentDataVersion) {
                if (Date.now() - lastActionTime < 5000) {
                    console.log("♻️ Local update detected. Silently syncing version.");
                    currentDataVersion = data.data_version;
                } else {
                    console.log("♻️ Remote change detected. Refreshing...");
                    location.reload();
                }
            }
        })
        .catch(console.error);
}

function syncDataVersion() {
    return fetch('/api/stats').then(res => res.json()).then(data => { currentDataVersion = data.data_version; });
}

function startPolling() {
    if (!statsInterval) { updateStats(); statsInterval = setInterval(updateStats, 5000); }
}
function stopPolling() { if (statsInterval) { clearInterval(statsInterval); statsInterval = null; } }

document.addEventListener("visibilitychange", () => { document.hidden ? stopPolling() : startPolling(); });
startPolling();

// --- 2. MODALS ---
function toggleQuickAdd() {
    document.getElementById('quick-add-row').classList.toggle('active');
    document.getElementById('quick-task-input').focus();
}

function handleQuickEnter(e) {
    if(e.key === 'Enter') {
        const content = e.target.value;
        const category = document.getElementById('quick-category')?.value || 'general';
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

// --- FIXED DELETE LOGIC ---
function openDeleteModal(id, content) {
    deletingTaskId = id;
    const nameEl = document.getElementById('del-task-name');
    if(nameEl) nameEl.innerText = content;
    
    const modal = document.getElementById('delete-modal');
    if(modal) {
        modal.classList.add('active');
        const oldBtn = document.getElementById('btn-confirm-delete');
        const newBtn = oldBtn.cloneNode(true);
        oldBtn.parentNode.replaceChild(newBtn, oldBtn);
        newBtn.onclick = function() { performDelete(deletingTaskId); };
    } else {
        if(confirm("Delete this habit? History will be lost.")) performDelete(id);
    }
}

function closeDeleteModal() {
    const modal = document.getElementById('delete-modal');
    if(modal) modal.classList.remove('active');
    deletingTaskId = null;
}

function handleDeleteClick(event, id) {
    event.stopPropagation();
    event.preventDefault(); 
    const row = document.getElementById(`task-${id}`);
    let content = "Task";
    if (row.querySelector('.task-content')) content = row.querySelector('.task-content').innerText;
    else if (row.querySelector('.task-title')) content = row.querySelector('.task-title').innerText;

    const isHabit = row.querySelector('.task-info')?.getAttribute('data-ishabit') === 'true';

    if (isHabit) openDeleteModal(id, content);
    else performDelete(id);
}

function performDelete(id) {
    closeDeleteModal(); 
    const row = document.getElementById(`task-${id}`);
    lastActionTime = Date.now();
    if(row) row.classList.add('deleting');
    fetch(`/api/tasks/${id}/delete`, { method: 'DELETE' })
        .then(res => res.json())
        .then(data => { if(data.success) { if(row) row.remove(); syncDataVersion(); loadCharts(); } });
}

// --- 3. TASK ACTIONS ---
function editTask(element) {
    editingTaskId = element.getAttribute('data-id');
    document.getElementById('m-content').value = element.getAttribute('data-content');
    document.getElementById('m-priority').value = element.getAttribute('data-priority');
    document.getElementById('m-color').value = element.getAttribute('data-color');
    document.getElementById('m-recurrence').value = element.getAttribute('data-recurrence');
    document.getElementById('m-category').value = element.getAttribute('data-category');
    document.getElementById('m-is-habit').checked = element.getAttribute('data-ishabit') === 'true';
    const dateVal = element.getAttribute('data-date');
    document.getElementById('m-date').value = (dateVal && dateVal !== 'None') ? dateVal.split(' ')[0] : '';
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
    lastActionTime = Date.now();

    const payload = { content, priority, date, color, recurrence, category, is_habit };
    const url = editingTaskId ? `/api/tasks/${editingTaskId}/edit` : '/api/tasks/add';
    
    fetch(url, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) })
    .then(res => res.json()).then(data => { if(data.success) location.reload(); });
}

function createTaskAPI(content, priority, date, color, category = 'general') {
    lastActionTime = Date.now();
    fetch('/api/tasks/add', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ content, priority, date, color, category })
    }).then(res => res.json()).then(data => { if(data.success) location.reload(); });
}

function toggleTask(id) {
    if(event) event.stopPropagation(); 
    const row = document.getElementById(`task-${id}`);
    lastActionTime = Date.now();
    row.classList.add('animating-out');

    fetch(`/api/tasks/${id}/toggle`, { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            setTimeout(() => {
                const btn = document.getElementById(`btn-check-${id}`);
                const taskList = document.getElementById('task-list');
                row.classList.remove('animating-out');

                if (data.new_state) {
                    row.classList.add('completed');
                    btn.innerHTML = '<i class="fas fa-check"></i>';
                    taskList.appendChild(row); 
                } else {
                    row.classList.remove('completed');
                    btn.innerHTML = '';
                    taskList.prepend(row); 
                    row.style.display = 'flex'; 
                }
                
                syncDataVersion(); 
                loadCharts(true); 

            }, 300);
    });
}

function filterTasks(category, btnElement) {
    document.querySelectorAll('.cat-pill').forEach(b => b.classList.remove('active'));
    btnElement.classList.add('active');
    document.querySelectorAll('.task-row').forEach(row => {
        const rowCat = row.getAttribute('data-category');
        const isCompleted = row.classList.contains('completed');
        let shouldShow = (category === 'all') ? (!isCompleted || rowCat === 'general' || !rowCat) : (rowCat === category);
        row.style.display = shouldShow ? 'flex' : 'none';
    });
}

// --- 4. CHART ENGINE ---
function loadCharts(softUpdate = false) {
    if (!softUpdate) console.log("📊 Loading Charts...");
    
    fetch('/api/stats/charts').then(res => res.json()).then(data => {
        // --- A. RADIAL CHARTS ---
        const radialContainer = document.getElementById('radial-chart'); 
        if (radialContainer) {
            const existingItems = radialContainer.querySelectorAll('.radial-item');
            if (!softUpdate || existingItems.length !== data.radial.length) {
                radialContainer.innerHTML = ''; 
                radialContainer.style.cssText = "display: flex; flex-direction: row; flex-wrap: wrap; justify-content: center; gap: 20px; width: 100%;";
                
                data.radial.forEach((percent, index) => {
                    const label = data.radial_labels[index];
                    const strokeColor = getColor(index);
                    const circumference = 220; 
                    let offset = percent !== null ? circumference - (percent / 100) * circumference : circumference;
                    let textValue = percent !== null ? percent + '%' : '-';
                    let textColor = percent !== null ? 'white' : '#555';

                    const html = `
                        <div class="radial-item" style="position: relative; width: 80px; display: flex; flex-direction: column; align-items: center; margin-bottom: 10px;">
                            <div style="position: relative; width: 80px; height: 80px;">
                                <svg class="progress-ring" width="80" height="80">
                                    <circle stroke="#333" stroke-width="8" fill="transparent" r="35" cx="40" cy="40"/>
                                    <circle class="progress-ring__circle" stroke="${strokeColor}" stroke-width="8" fill="transparent" r="35" cx="40" cy="40"
                                        style="stroke-dasharray: ${circumference}; stroke-dashoffset: ${circumference}; transform: rotate(-90deg); transform-origin: 50% 50%; transition: stroke-dashoffset 1s ease-out;"/>
                                </svg>
                                <div class="radial-text" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-weight: bold; color: ${textColor};">${textValue}</div>
                            </div>
                            <div class="radial-label" style="font-size: 12px; color: #888; margin-top: 5px; text-align: center;">${label}</div>
                        </div>`;
                    radialContainer.innerHTML += html;
                    setTimeout(() => { 
                        if(radialContainer.children[index])
                            radialContainer.children[index].querySelector('.progress-ring__circle').style.strokeDashoffset = offset; 
                    }, 50);
                });
            } else {
                data.radial.forEach((percent, index) => {
                    const item = existingItems[index];
                    const circle = item.querySelector('.progress-ring__circle');
                    const text = item.querySelector('.radial-text');
                    const circumference = 220;
                    if (percent === null) {
                        circle.style.strokeDashoffset = circumference;
                        text.innerText = '-'; text.style.color = '#555';
                    } else {
                        circle.style.strokeDashoffset = circumference - (percent / 100) * circumference;
                        text.innerText = percent + '%'; text.style.color = 'white';
                    }
                });
            }
        }

        // --- B. HEATMAP (Fixed "Egg" Shape) ---
        const heatmapContainer = document.getElementById('habit-heatmap');
        if (heatmapContainer) {
            const currentRows = heatmapContainer.querySelectorAll('.habit-row');
            if (!softUpdate || currentRows.length !== data.heatmap.length) {
                heatmapContainer.innerHTML = ''; 
                
                if (data.heatmap && data.heatmap.length > 0) {
                    data.heatmap.forEach(habit => {
                        const habitWrapper = document.createElement('div');
                        habitWrapper.className = 'habit-row';
                        habitWrapper.setAttribute('id', `habit-row-${habit.id}`);
                        habitWrapper.style.marginBottom = '20px';
                        
                        const titleDiv = document.createElement('div');
                        titleDiv.style.cssText = `color:${habit.color}; font-weight:bold; font-size:0.9rem; margin-bottom:8px;`;
                        titleDiv.innerText = habit.name;
                        habitWrapper.appendChild(titleDiv);

                        const rowDiv = document.createElement('div');
                        rowDiv.style.cssText = 'display:flex; gap:5px; flex-wrap:wrap;';

                        habit.data.forEach((day, i) => {
                            const dot = document.createElement('div');
                            dot.className = 'habit-dot animate-in'; 
                            
                            dot.style.animationDelay = `${i * 0.03}s`;

                            const dayNum = day.real_date.split('-')[2];
                            dot.setAttribute('data-date', dayNum); 

                            // FIX: Added flex-shrink:0 and min-width/height to prevent squishing
                            dot.style.cssText = `
                                width:16px; 
                                height:16px; 
                                min-width:16px; 
                                min-height:16px; 
                                flex-shrink:0; 
                                border-radius:50%; 
                                transition:all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                            `;
                            
                            // Check if Future
                            if (day.is_future) {
                                dot.style.border = '2px dashed rgba(255,255,255,0.05)';
                                dot.style.backgroundColor = 'transparent';
                                dot.style.cursor = 'default';
                                dot.title = "Future date";
                            } else {
                                dot.style.backgroundColor = day.y > 0 ? day.fillColor : 'rgba(255,255,255,0.1)';
                                dot.style.cursor = 'pointer';
                                dot.onclick = function() { handleDotClick(this, habit.id, day.real_date, habit.color); };
                            }
                            rowDiv.appendChild(dot);
                        });
                        habitWrapper.appendChild(rowDiv);
                        heatmapContainer.appendChild(habitWrapper);
                    });
                } else {
                    heatmapContainer.innerHTML = '<div style="color:#555; font-style:italic;">No habits tracked yet.</div>';
                }
            } else {
                // SOFT UPDATE (Singular Animation)
                data.heatmap.forEach((habit) => {
                    const row = document.getElementById(`habit-row-${habit.id}`);
                    if(row) {
                        const dots = row.querySelectorAll('.habit-dot');
                        habit.data.forEach((day, dIndex) => {
                            const dot = dots[dIndex];
                            if(dot && !dot.classList.contains('confirming') && !dot.classList.contains('processing') && !day.is_future) {
                                const newColor = day.y > 0 ? day.fillColor : 'rgba(255,255,255,0.1)';
                                dot.style.backgroundColor = newColor;
                            }
                        });
                    }
                });
            }
        }
    }).catch(err => console.error("🔥 Chart Error:", err));
}

function getColor(index) { return ['#3b5bdb', '#2ecc71', '#f1c40f', '#e74c3c', '#9b59b6'][index % 5]; }

// --- 5. HABIT ANIMATION (Double-Tap) ---
function handleDotClick(dotElement, taskId, dateStr, taskColor) {
    if (dotElement.classList.contains('processing')) return;

    // STEP 1: DIM (Confirmation)
    if (!dotElement.classList.contains('confirming')) {
        dotElement.classList.add('confirming');
        dotElement.style.transform = 'scale(0.8)';
        dotElement.style.opacity = '0.5';
        dotElement.style.border = `2px solid ${taskColor}`;
        dotElement.style.backgroundColor = 'transparent';

        dotElement.dataset.timer = setTimeout(() => {
            dotElement.classList.remove('confirming');
            dotElement.style.transform = 'scale(1)';
            dotElement.style.opacity = '1';
            dotElement.style.border = 'none';
            if (dotElement.style.backgroundColor === 'transparent') {
                dotElement.style.backgroundColor = 'rgba(255,255,255,0.1)';
            }
        }, 3000); 
        return; 
    }

    // STEP 2: CONFIRMED
    clearTimeout(dotElement.dataset.timer);
    dotElement.classList.remove('confirming');
    dotElement.classList.add('processing');
    lastActionTime = Date.now();

    // Expansion Animation
    dotElement.style.transition = 'all 0.4s ease';
    dotElement.style.transform = 'scale(1.4)';
    dotElement.style.backgroundColor = taskColor;
    dotElement.style.opacity = '1';
    dotElement.style.border = 'none';
    dotElement.style.boxShadow = `0 0 15px ${taskColor}`;

    fetch(`/api/tasks/${taskId}/history/add`, {
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ date: dateStr })
    }).then(res => res.json()).then(data => {
        setTimeout(() => { 
            dotElement.style.transform = 'scale(1)'; 
            dotElement.style.boxShadow = 'none';
            dotElement.classList.remove('processing');
            syncDataVersion(); 
            loadCharts(true); 
        }, 400); 
    });
}

// --- INIT ---
document.addEventListener('DOMContentLoaded', () => {
    loadCharts(); 
    const modal = document.getElementById('task-modal');
    if (modal) modal.addEventListener('click', (e) => { if (e.target === modal) closeModal(); });
    const delModal = document.getElementById('delete-modal');
    if (delModal) delModal.addEventListener('click', (e) => { if (e.target === delModal) closeDeleteModal(); });
});