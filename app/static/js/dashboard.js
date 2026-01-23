/* app/static/js/dashboard.js */

// --- GLOBAL VARIABLES ---
let editingTaskId = null; 
let statsInterval = null; 
let currentDataVersion = null; 
let lastActionTime = 0; // Timestamp of last user interaction to block auto-reloads

// --- 1. SMART STATS POLLING (With Grace Period) ---
function updateStats() {
    fetch('/api/stats')
        .then(res => res.json())
        .then(data => {
            // Update Text UI
            if(document.getElementById('cpu-text')) {
                document.getElementById('cpu-text').innerText = data.cpu + '%';
                document.getElementById('cpu-bar').style.width = data.cpu + '%';
                document.getElementById('ram-text').innerText = data.ram + '%';
                document.getElementById('ram-bar').style.width = data.ram + '%';
                document.getElementById('disk-text').innerText = data.disk + '%';
                document.getElementById('disk-bar').style.width = data.disk + '%';
            }

            // AUTO-SYNC LOGIC
            if (currentDataVersion === null) {
                currentDataVersion = data.data_version;
            } else if (data.data_version > currentDataVersion) {
                // CHECK: Did the user do something recently (last 5 seconds)?
                if (Date.now() - lastActionTime < 5000) {
                    // YES: User is active. Don't reload. Sync silently.
                    console.log("♻️ Local update detected. Silently syncing version.");
                    currentDataVersion = data.data_version;
                } else {
                    // NO: This is a remote change (or user is idle). Refresh.
                    console.log("♻️ Remote change detected. Refreshing...");
                    location.reload();
                }
            }
        })
        .catch(console.error);
}

// Helper to manually fetch the new version after we do something
function syncDataVersion() {
    return fetch('/api/stats')
        .then(res => res.json())
        .then(data => {
            currentDataVersion = data.data_version; 
        });
}

function startPolling() {
    if (!statsInterval) {
        updateStats(); 
        statsInterval = setInterval(updateStats, 5000);
    }
}

function stopPolling() {
    if (statsInterval) {
        clearInterval(statsInterval);
        statsInterval = null;
    }
}

document.addEventListener("visibilitychange", () => {
    if (document.hidden) stopPolling();
    else startPolling();
});

startPolling();

// --- 2. QUICK ADD & MODALS ---
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
    
    // Mark action to prevent auto-reload
    lastActionTime = Date.now();

    const payload = { content, priority, date, color, recurrence, category, is_habit };
    const url = editingTaskId ? `/api/tasks/${editingTaskId}/edit` : '/api/tasks/add';
    
    fetch(url, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) })
    .then(res => res.json()).then(data => { if(data.success) location.reload(); });
}

function createTaskAPI(content, priority, date, color, category = 'general') {
    // Mark action to prevent auto-reload
    lastActionTime = Date.now();
    
    fetch('/api/tasks/add', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ content, priority, date, color, category })
    }).then(res => res.json()).then(data => { 
        if(data.success) {
            location.reload();
        }
    });
}

// --- 3. FILTERING ---
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

// --- 4. ACTIONS (Delete & Toggle) ---
function handleDeleteClick(event, id) {
    event.stopPropagation();
    const row = document.getElementById(`task-${id}`);
    const btn = event.currentTarget;
    
    const isHabit = row.querySelector('.task-info')?.getAttribute('data-ishabit') === 'true';
    const isCompleted = row.classList.contains('completed');
    const requiresConfirmation = isHabit || !isCompleted;

    if (requiresConfirmation) {
        if (!row.classList.contains('confirm-delete-mode')) {
            row.classList.add('confirm-delete-mode'); 
            const icon = btn.querySelector('i');
            if(icon) icon.className = "fas fa-exclamation-triangle"; 
            setTimeout(() => {
                row.classList.remove('confirm-delete-mode');
                if(icon) icon.className = "fas fa-trash-alt";
            }, 2000);
            return; 
        }
    }

    // Set flag
    lastActionTime = Date.now();
    
    row.classList.add('deleting');
    setTimeout(() => {
        fetch(`/api/tasks/${id}/delete`, { method: 'DELETE' })
            .then(res => res.json())
            .then(data => { 
                if(data.success) { 
                    row.remove(); 
                    syncDataVersion(); 
                    loadCharts(); 
                } 
            });
    }, 500);
}

function toggleTask(id) {
    if(event) event.stopPropagation(); 
    const row = document.getElementById(`task-${id}`);
    
    // Set flag to block reload
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
                    
                    const activeCat = document.querySelector('.cat-pill.active').innerText.trim().toLowerCase();
                    const rowCat = row.getAttribute('data-category');
                    if(activeCat === 'all' && rowCat !== 'general') row.style.display = 'none';
                } else {
                    row.classList.remove('completed');
                    btn.innerHTML = '';
                    taskList.prepend(row); 
                    row.style.display = 'flex'; 
                }

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
                        html += ` • <i class="fas fa-sync-alt" title="Repeats"></i>`;
                        metaSpan.innerHTML = html;
                    }
                }

                // Smooth Re-entry
                requestAnimationFrame(() => {
                    row.classList.add('animating-in');
                    setTimeout(() => {
                        row.classList.remove('animating-in');
                    }, 400);
                });

                syncDataVersion(); 
                loadCharts(); 

            }, 300);
    });
}

// --- 5. CHART ENGINE (Smart Empty State + Stacked Heatmap) ---
function loadCharts() {
    console.log("📊 Loading Charts...");

    fetch('/api/stats/charts')
        .then(res => res.json())
        .then(data => {
            // --- A. RADIAL PROGRESS BARS ---
            const radialContainer = document.getElementById('radial-chart'); 
            if (radialContainer) {
                // Check if we can update instead of rebuild
                const existingItems = radialContainer.querySelectorAll('.radial-item');
                const shouldRebuild = existingItems.length === 0 || existingItems.length !== data.radial.length;

                if (!shouldRebuild) {
                    // SMOOTH UPDATE MODE
                    data.radial.forEach((percent, index) => {
                        const item = existingItems[index];
                        const circle = item.querySelector('.progress-ring__circle');
                        const text = item.querySelector('.radial-text');
                        
                        // EMPTY STATE LOGIC
                        if (percent === null) {
                            circle.style.strokeDashoffset = 220; // Full circumference (empty)
                            circle.style.stroke = '#333';        // Grey
                            text.innerText = '-';
                            text.style.color = '#555';
                        } else {
                            const circumference = 220;
                            const offset = circumference - (percent / 100) * circumference;
                            circle.style.strokeDashoffset = offset;
                            circle.style.stroke = getColor(index);
                            text.innerText = percent + '%';
                            text.style.color = 'white';
                        }
                    });
                } else {
                    // BUILD MODE
                    radialContainer.innerHTML = ''; 
                    radialContainer.style.display = 'flex';
                    radialContainer.style.gap = '20px';
                    radialContainer.style.flexWrap = 'wrap';
                    
                    data.radial.forEach((percent, index) => {
                        const label = data.radial_labels[index];
                        const circumference = 220; 
                        
                        // Default to Empty
                        let offset = circumference;
                        let strokeColor = '#333';
                        let textValue = '-';
                        let textColor = '#555';

                        if (percent !== null) {
                            offset = circumference - (percent / 100) * circumference;
                            strokeColor = getColor(index);
                            textValue = percent + '%';
                            textColor = 'white';
                        }
                        
                        const html = `
                            <div class="radial-item" style="position: relative; width: 80px; display: flex; flex-direction: column; align-items: center;">
                                <div style="position: relative; width: 80px; height: 80px;">
                                    <svg class="progress-ring" width="80" height="80">
                                        <circle class="progress-ring__circle-bg" stroke="#333" stroke-width="8" fill="transparent" r="35" cx="40" cy="40"/>
                                        <circle class="progress-ring__circle" stroke="${strokeColor}" stroke-width="8" fill="transparent" r="35" cx="40" cy="40"
                                            style="stroke-dasharray: ${circumference}; stroke-dashoffset: ${circumference}; transform: rotate(-90deg); transform-origin: 50% 50%; transition: stroke-dashoffset 1s ease-out, stroke 0.5s;"/>
                                    </svg>
                                    <div class="radial-text" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-weight: bold; color: ${textColor};">${textValue}</div>
                                </div>
                                <div class="radial-label" style="font-size: 12px; color: #888; margin-top: 5px; text-align: center;">${label}</div>
                            </div>`;
                        radialContainer.innerHTML += html;

                        // Trigger Animation
                        setTimeout(() => {
                            if (percent !== null) {
                                const newItem = radialContainer.children[index];
                                newItem.querySelector('.progress-ring__circle').style.strokeDashoffset = offset;
                            }
                        }, 100);
                    });
                }
            }

            // --- B. HEATMAP (Stacked & Time Travel Protected) ---
            const heatmapContainer = document.getElementById('habit-heatmap');
            if (heatmapContainer) {
                heatmapContainer.innerHTML = ''; 

                const today = new Date();
                const todayStr = today.getFullYear() + '-' + 
                                String(today.getMonth() + 1).padStart(2, '0') + '-' + 
                                String(today.getDate()).padStart(2, '0');

                if (data.heatmap && data.heatmap.length > 0) {
                    data.heatmap.forEach(habit => {
                        const habitWrapper = document.createElement('div');
                        habitWrapper.style.marginBottom = '20px';

                        const titleDiv = document.createElement('div');
                        titleDiv.style.color = habit.color;
                        titleDiv.style.fontWeight = 'bold';
                        titleDiv.style.fontSize = '0.9rem';
                        titleDiv.style.marginBottom = '8px';
                        titleDiv.innerText = habit.name; 
                        habitWrapper.appendChild(titleDiv);

                        const rowDiv = document.createElement('div');
                        rowDiv.style.display = 'flex';
                        rowDiv.style.gap = '5px';
                        rowDiv.style.flexWrap = 'wrap';

                        habit.data.forEach((day, i) => {
                            const dot = document.createElement('div');
                            dot.className = 'habit-dot'; 
                            // Use pure day number for tooltip (e.g. "16")
                            dot.setAttribute('data-date', day.real_date.split('-')[2]); 

                            dot.style.width = '16px'; 
                            dot.style.height = '16px';
                            dot.style.borderRadius = '50%'; 
                            dot.style.transition = 'all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)'; 
                            
                            dot.style.opacity = '0';
                            dot.style.animation = `fadeIn 0.5s ease forwards ${i * 0.03}s`;

                            if (day.real_date > todayStr) {
                                // FUTURE: Locked
                                dot.style.backgroundColor = 'transparent';
                                dot.style.border = '2px dashed rgba(255,255,255,0.1)';
                                dot.style.cursor = 'not-allowed';
                            } else {
                                // PAST/TODAY: Active
                                dot.style.backgroundColor = day.y > 0 ? day.fillColor : 'rgba(255,255,255,0.1)';
                                dot.style.cursor = 'pointer';
                                dot.onclick = function() {
                                    handleDotClick(this, habit.id, day.real_date, habit.color);
                                };
                            }
                            rowDiv.appendChild(dot);
                        });
                        
                        habitWrapper.appendChild(rowDiv);
                        heatmapContainer.appendChild(habitWrapper);
                    });
                } else {
                    heatmapContainer.innerHTML = '<div style="color:#555; font-style:italic;">No habits tracked yet.</div>';
                }
            }
        })
        .catch(err => console.error("🔥 Chart Error:", err));
}

function getColor(index) {
    const colors = ['#3b5bdb', '#2ecc71', '#f1c40f', '#e74c3c', '#9b59b6'];
    return colors[index % colors.length];
}

// --- 6. HABIT DOT CLICK ---
function handleDotClick(dotElement, taskId, dateStr, taskColor) {
    if (document.querySelector('.confirming') && !dotElement.classList.contains('confirming')) return;

    if (!dotElement.classList.contains('confirming')) {
        // CLICK 1: DIM COLOR
        dotElement.classList.add('confirming');
        dotElement.style.backgroundColor = taskColor; 
        dotElement.style.opacity = '0.5'; 
        dotElement.style.transform = 'scale(0.9)';
        
        dotElement.dataset.timer = setTimeout(() => {
            dotElement.classList.remove('confirming');
            dotElement.style.backgroundColor = 'rgba(255,255,255,0.1)'; 
            dotElement.style.opacity = '1';
            dotElement.style.transform = 'scale(1)';
        }, 3000);
        
    } else {
        // CLICK 2: CONFIRM
        clearTimeout(dotElement.dataset.timer);
        dotElement.classList.remove('confirming');
        
        lastActionTime = Date.now(); // Block reload

        dotElement.style.opacity = '1';
        dotElement.style.transform = 'scale(1.2)';
        dotElement.style.boxShadow = `0 0 10px ${taskColor}`;
        dotElement.style.backgroundColor = taskColor;
        
        dotElement.onclick = null;
        dotElement.style.cursor = 'default';
        
        fetch(`/api/tasks/${taskId}/history/add`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ date: dateStr })
        }).then(res => res.json()).then(data => {
            if(data.success) {
                setTimeout(() => { 
                    dotElement.style.transform = 'scale(1)'; 
                    syncDataVersion(); 
                    loadCharts(); 
                }, 300);
            } else {
                dotElement.style.backgroundColor = 'rgba(255,255,255,0.1)';
                dotElement.style.boxShadow = 'none';
                dotElement.style.transform = 'scale(1)';
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