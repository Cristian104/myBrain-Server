/* app/static/dashboard/js/dashboard.js */

// --- GLOBAL VARIABLES ---
let editingTaskId = null;
let deletingTaskId = null;
let statsInterval = null;
let currentDataVersion = null;
let lastActionTime = 0;

// Track Category Order for Slide Direction
const categoryOrder = ['all', 'work', 'personal', 'dev', 'health'];
let currentCategoryIndex = 0;

// --- 1. SMART STATS POLLING ---
function updateStats() {
    fetch('/api/stats')
        .then(res => res.json())
        .then(data => {
            if (document.getElementById('cpu-text')) {
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
                    currentDataVersion = data.data_version; // Silent sync if active
                } else {
                    location.reload(); // Refresh if idle
                }
            }
        }).catch(console.error);
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

// --- 2. SMOOTH ANIMATIONS & FILTERING (THE FIX) ---

function filterTasks(category, btnElement) {
    const listContainer = document.getElementById('task-list');
    
    // 0. Ensure Animation Wrapper Exists
    let wrapper = listContainer.parentElement;
    if (!wrapper.classList.contains('smooth-height-wrapper')) {
        wrapper = document.createElement('div');
        wrapper.className = 'smooth-height-wrapper';
        listContainer.parentNode.insertBefore(wrapper, listContainer);
        wrapper.appendChild(listContainer);
    }

    // 1. CAPTURE START HEIGHT (The "Jump" Fix)
    // We lock the height to pixels BEFORE we change anything
    const startHeight = wrapper.offsetHeight;
    wrapper.style.height = startHeight + 'px';

    // 2. Determine Slide Direction
    const newIndex = categoryOrder.indexOf(category);
    const direction = newIndex > currentCategoryIndex ? 'right' : 'left';
    currentCategoryIndex = newIndex;

    // 3. Update Pills UI
    document.querySelectorAll('.cat-pill').forEach(b => b.classList.remove('active'));
    btnElement.classList.add('active');

    const outClass = direction === 'right' ? 'anim-out-left' : 'anim-out-right';
    const inClass = direction === 'right' ? 'anim-in-right' : 'anim-in-left';

    // 4. ANIMATE OUT (Slide Away)
    listContainer.classList.remove('anim-in-left', 'anim-in-right'); 
    listContainer.classList.add(outClass);

    setTimeout(() => {
        // 5. CHANGE THE DOM (Hide/Show Rows)
        document.querySelectorAll('.task-row').forEach(row => {
            const rowCat = row.getAttribute('data-category');
            const isCompleted = row.classList.contains('completed');
            let shouldShow = (category === 'all') 
                ? (!isCompleted || rowCat === 'general' || !rowCat) 
                : (rowCat === category);
            row.style.display = shouldShow ? 'flex' : 'none';
        });

        // 6. ANIMATE HEIGHT (Smooth Resize)
        // A. Release height constraint to measure the NEW size
        wrapper.style.height = 'auto';
        const targetHeight = wrapper.offsetHeight;
        
        // B. Snap back to OLD size instantly
        wrapper.style.height = startHeight + 'px';
        
        // C. Force Browser to Process (Reflow)
        void wrapper.offsetHeight; 

        // D. Animate to NEW size
        wrapper.style.height = targetHeight + 'px';

        // 7. ANIMATE IN (Slide Back)
        listContainer.classList.remove(outClass);
        listContainer.classList.add(inClass);

        // 8. Cleanup (Unlock height after animation ends)
        setTimeout(() => {
            wrapper.style.height = 'auto';
        }, 400); // 400ms matches CSS transition time

    }, 200); // Wait for Slide Out to finish
}

// Helper to animate height for other actions (like Quick Add)
function updateWrapperHeight(elementInside) {
    const wrapper = elementInside.closest('.smooth-height-wrapper');
    if(!wrapper) return;
    
    const startHeight = wrapper.offsetHeight;
    wrapper.style.height = startHeight + 'px';
    
    // Allow DOM to update (e.g. Quick Add row appears)
    requestAnimationFrame(() => {
        wrapper.style.height = 'auto';
        const targetHeight = wrapper.offsetHeight;
        wrapper.style.height = startHeight + 'px';
        void wrapper.offsetHeight;
        wrapper.style.height = targetHeight + 'px';
        setTimeout(() => wrapper.style.height = 'auto', 400);
    });
}

// --- 3. MODALS ---
function toggleQuickAdd() {
    const row = document.getElementById('quick-add-row');
    row.classList.toggle('active');
    
    if(row.classList.contains('active')) {
        document.getElementById('quick-task-input').focus();
    }
    // Animate the opening
    updateWrapperHeight(row);
}

function handleQuickEnter(e) {
    if (e.key === 'Enter') {
        const content = e.target.value;
        const category = document.getElementById('quick-category')?.value || 'general';
        if (content) {
            createTaskAPI(content, 'normal', null, '#3b5bdb', category);
            e.target.value = '';
        }
    }
}

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

// --- FIXED DELETE LOGIC ---
function openDeleteModal(id, content) {
    deletingTaskId = id;
    const nameEl = document.getElementById('del-task-name');
    if (nameEl) nameEl.innerText = content;

    const modal = document.getElementById('delete-modal');
    if (modal) {
        modal.classList.add('active');
        const oldBtn = document.getElementById('btn-confirm-delete');
        const newBtn = oldBtn.cloneNode(true);
        oldBtn.parentNode.replaceChild(newBtn, oldBtn);
        newBtn.onclick = function () { performDelete(deletingTaskId); };
    } else {
        if (confirm("Delete this habit? History will be lost.")) performDelete(id);
    }
}

function closeDeleteModal() {
    const modal = document.getElementById('delete-modal');
    if (modal) modal.classList.remove('active');
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
    if (row) {
        row.classList.add('deleting');
        // Animate height adjustment on delete
        setTimeout(() => updateWrapperHeight(row), 50);
    }
    fetch(`/api/tasks/${id}/delete`, { method: 'DELETE' })
        .then(res => res.json())
        .then(data => { if (data.success) { if (row) row.remove(); syncDataVersion(); loadCharts(); } });
}

// --- 4. TASK ACTIONS ---
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
    const content = document.getElementById('m-content').value.trim();
    const priority = document.getElementById('m-priority').value;
    const date = document.getElementById('m-date').value;  // YYYY-MM-DD
    const time = document.getElementById('m-time')?.value || '08:00';  // Default 8 AM if no input
    const color = document.getElementById('m-color').value;
    const recurrence = document.getElementById('m-recurrence').value;
    const category = document.getElementById('m-category').value;
    const is_habit = document.getElementById('m-is-habit').checked;

    if (!content) {
        alert("Task description is required!");
        return;
    }

    lastActionTime = Date.now();

    // Combine date + time into ISO-like string (or null if no date)
    const datetime = date ? `${date}T${time}:00` : null;

    // Single payload with 'datetime' key (backend will parse it)
    const payload = {
        content,
        priority,
        datetime,       // ← New key (replaces 'date')
        color,
        recurrence,
        category,
        is_habit
    };

    const url = editingTaskId ? `/api/tasks/${editingTaskId}/edit` : '/api/tasks/add';

    fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success || data.id) {
            location.reload();  // Refresh to see changes
        } else {
            alert("Error saving task");
        }
    })
    .catch(err => {
        console.error("Save error:", err);
        alert("Network error – check console");
    });
}

function createTaskAPI(content, priority = 'normal', datetime = null, color = '#3b5bdb', category = 'general') {
    // If datetime not passed, default to today at 08:00
    if (!datetime) {
        const today = new Date().toISOString().split('T')[0];
        datetime = `${today}T08:00:00`;
    }

    lastActionTime = Date.now();

    const payload = { content, priority, datetime, color, category };

    fetch('/api/tasks/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success || data.id) {
            location.reload();
        }
    });
}

function toggleTask(id) {
    if (event) event.stopPropagation();
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

                if (data.new_state) {  // Now completed
                    row.classList.add('completed');
                    btn.innerHTML = '<i class="fas fa-check"></i>';
                    // FIX: Re-append to trigger filter refresh (visibility)
                    taskList.appendChild(row);
                } else {  // Now incomplete
                    row.classList.remove('completed');
                    btn.innerHTML = '';
                    taskList.prepend(row);
                }

                // FORCE FILTER RE-APPLY (ensures visibility after complete/incomplete)
                const activePill = document.querySelector('.cat-pill.active');
                if (activePill) {
                    const cat = activePill.querySelector('span').innerText.toLowerCase() === 'all' ? 'all' : 
                                 activePill.onclick.toString().match(/'([^']+)'/)[1];
                    filterTasks(cat, activePill);
                }

                syncDataVersion();
                loadCharts(true);

            }, 300);
        }).catch(err => {
            console.error("Toggle failed:", err);
            row.classList.remove('animating-out');
        });
}

// --- 5. CHART ENGINE ---
function loadCharts(softUpdate = false) {
    if (!softUpdate) console.log("📊 Loading Charts...");

    fetch('/api/tasks/charts').then(res => res.json()).then(data => {        // --- A. RADIAL CHARTS (Mobile Optimized) ---
        const radialContainer = document.getElementById('radial-chart'); 
        if (radialContainer) {
            // 1. Calculate Average
            let total = 0, count = 0;
            data.radial.forEach(p => { if(p !== null) { total += p; count++; } });
            const average = count > 0 ? Math.round(total / count) : 0;
            
            radialContainer.innerHTML = ''; 
            
            // 2. Create Desktop Rings (With class 'desktop-ring')
            data.radial.forEach((percent, index) => {
                const label = data.radial_labels[index];
                const strokeColor = getColor(index);
                const circumference = 220; 
                let offset = percent !== null ? circumference - (percent / 100) * circumference : circumference;
                let textValue = percent !== null ? percent + '%' : '-';
                
                // Note the class 'desktop-ring' added here
                const html = `
                    <div class="radial-item desktop-ring" style="position: relative; width: 80px; display: flex; flex-direction: column; align-items: center; margin-bottom: 10px;">
                        <div style="position: relative; width: 80px; height: 80px;">
                            <svg class="progress-ring" width="80" height="80">
                                <circle stroke="#333" stroke-width="8" fill="transparent" r="35" cx="40" cy="40"/>
                                <circle class="progress-ring__circle" stroke="${strokeColor}" stroke-width="8" fill="transparent" r="35" cx="40" cy="40"
                                    style="stroke-dasharray: ${circumference}; stroke-dashoffset: ${circumference}; transform: rotate(-90deg); transform-origin: 50% 50%; transition: stroke-dashoffset 1s ease-out;"/>
                            </svg>
                            <div class="radial-text" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-weight: bold; color: white;">${textValue}</div>
                        </div>
                        <div class="radial-label" style="font-size: 12px; color: #888; margin-top: 5px; text-align: center;">${label}</div>
                    </div>`;
                radialContainer.innerHTML += html;
                setTimeout(() => { 
                    if(radialContainer.children[index])
                        radialContainer.children[index].querySelector('.progress-ring__circle').style.strokeDashoffset = offset; 
                }, 50);
            });

            // 3. Create SINGLE Mobile Ring (With class 'mobile-ring')
            const mobileCirc = 440; // Bigger circumference
            const mobileOffset = mobileCirc - (average / 100) * mobileCirc;
            
            const mobileHtml = `
                <div class="radial-item mobile-ring" style="display: none; position: relative; width: 150px; flex-direction: column; align-items: center; margin: 0 auto;">
                    <div style="position: relative; width: 150px; height: 150px;">
                        <svg class="progress-ring" width="150" height="150">
                            <circle stroke="#222" stroke-width="12" fill="transparent" r="70" cx="75" cy="75"/>
                            <circle class="progress-ring__circle" stroke="#3b5bdb" stroke-width="12" fill="transparent" r="70" cx="75" cy="75"
                                style="stroke-dasharray: ${mobileCirc}; stroke-dashoffset: ${mobileCirc}; transform: rotate(-90deg); transform-origin: 50% 50%; transition: stroke-dashoffset 1s ease-out;"/>
                        </svg>
                        <div class="radial-text" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 2rem; font-weight: bold; color: white;">
                            ${average}%
                        </div>
                    </div>
                    <div class="radial-label" style="font-size: 1rem; color: #aaa; margin-top: 10px; text-align: center;">Overall Focus</div>
                </div>`;
                
            radialContainer.innerHTML += mobileHtml;
            setTimeout(() => { 
                const mobRing = radialContainer.querySelector('.mobile-ring .progress-ring__circle');
                if(mobRing) mobRing.style.strokeDashoffset = mobileOffset; 
            }, 50);
        }

        // --- B. HEATMAP (Fixed "Egg" Shape & Day Letters) ---
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
                            dot.className = 'habit-dot animate-pop';
                            dot.style.animationDelay = `${i * 0.03}s`;

                            // Date + Day Letter Calculation (e.g. "28 T")
                            const dayNum = day.real_date.split('-')[2];
                            const dateObj = new Date(day.real_date + 'T00:00:00');
                            const dayLetter = dateObj.toLocaleDateString('en-US', { weekday: 'narrow' });
                            dot.setAttribute('data-date', `${dayNum} ${dayLetter}`);

                            dot.style.cssText = `
                                width:16px; height:16px; min-width:16px; min-height:16px; flex-shrink:0; 
                                border-radius:50%; 
                                transition:all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                            `;

                            if (day.is_future) {
                                dot.style.border = '2px dashed rgba(255,255,255,0.05)';
                                dot.style.backgroundColor = 'transparent';
                                dot.style.cursor = 'default';
                                dot.title = "Future date";
                            } else {
                                dot.style.backgroundColor = day.y > 0 ? day.fillColor : 'rgba(255,255,255,0.1)';
                                dot.style.cursor = 'pointer';
                                dot.onclick = function () { handleDotClick(this, habit.id, day.real_date, habit.color); };
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
                data.heatmap.forEach((habit) => {
                    const row = document.getElementById(`habit-row-${habit.id}`);
                    if (row) {
                        const dots = row.querySelectorAll('.habit-dot');
                        habit.data.forEach((day, dIndex) => {
                            const dot = dots[dIndex];
                            if (dot && !dot.classList.contains('confirming') && !dot.classList.contains('processing') && !day.is_future) {
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

// --- 6. HABIT ANIMATION (Double-Tap) ---
function handleDotClick(dotElement, taskId, dateStr, taskColor) {
    if (dotElement.classList.contains('processing')) return;

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

    clearTimeout(dotElement.dataset.timer);
    dotElement.classList.remove('confirming');
    dotElement.classList.add('processing');
    lastActionTime = Date.now();

    dotElement.style.transition = 'all 0.4s ease';
    dotElement.style.transform = 'scale(1.4)';
    dotElement.style.backgroundColor = taskColor;
    dotElement.style.opacity = '1';
    dotElement.style.border = 'none';
    dotElement.style.boxShadow = `0 0 15px ${taskColor}`;

    fetch(`/api/tasks/${taskId}/history/add`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ date: dateStr })
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