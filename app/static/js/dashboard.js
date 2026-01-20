/* app/static/js/dashboard.js */

// --- GLOBAL VARIABLES ---
let editingTaskId = null; // Tracks if we are editing or creating
let deletePendingId = null; // Tracks which task is waiting for 2nd click

// --- 1. STATS (Keep as is) ---
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

// --- 2. QUICK ADD LOGIC ("New" Button) ---
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
        // NEW: Get the category from the dropdown next to the input
        const categorySelect = document.getElementById('quick-category');
        const category = categorySelect ? categorySelect.value : 'general';

        if(content) {
            // Send with defaults: normal, blue, no date + Selected Category
            createTaskAPI(content, 'normal', null, '#3b5bdb', category);
            
            e.target.value = ''; // Clear input
            toggleQuickAdd(); // Hide row
        }
    }
}

// --- 3. MODAL LOGIC ("New+" & Edit) ---
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
        // Clear form for new task
        document.getElementById('m-content').value = '';
        document.getElementById('m-date').value = '';
        document.getElementById('m-category').value = 'general'; // Default
        editingTaskId = null;
    }
    modal.classList.add('active');
}

function closeModal() { document.getElementById('task-modal').classList.remove('active'); }
function selectColor(hex) { document.getElementById('m-color').value = hex; }

// Triggered by clicking a task row (Updated to use Data Attributes)
function editTask(element) {
    // Read from the clicked element's data attributes
    editingTaskId = element.getAttribute('data-id');
    
    document.getElementById('m-content').value = element.getAttribute('data-content');
    document.getElementById('m-priority').value = element.getAttribute('data-priority');
    document.getElementById('m-color').value = element.getAttribute('data-color');
    document.getElementById('m-recurrence').value = element.getAttribute('data-recurrence');
    document.getElementById('m-category').value = element.getAttribute('data-category'); // NEW

    const dateVal = element.getAttribute('data-date');
    if(dateVal && dateVal !== 'None') {
        // Python format usually YYYY-MM-DD HH:MM:SS, we need YYYY-MM-DD
        const cleanDate = dateVal.split(' ')[0]; 
        document.getElementById('m-date').value = cleanDate;
    } else {
        document.getElementById('m-date').value = '';
    }
    
    openModal(true);
}

// Central Function for Modal Submit
function submitTaskForm() {
    const content = document.getElementById('m-content').value;
    const priority = document.getElementById('m-priority').value;
    const date = document.getElementById('m-date').value;
    const color = document.getElementById('m-color').value;
    const recurrence = document.getElementById('m-recurrence').value;
    const category = document.getElementById('m-category').value; // NEW

    if(!content) return;

    const payload = { content, priority, date, color, recurrence, category };

    if (editingTaskId) {
        fetch(`/api/tasks/${editingTaskId}/edit`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        }).then(res => res.json()).then(data => {
            if(data.success) location.reload();
        });
    } else {
        fetch('/api/tasks/add', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        }).then(res => res.json()).then(data => {
            if(data.success) location.reload();
        });
    }
}

// API Helper for Quick Add
function createTaskAPI(content, priority, date, color, category = 'general') {
    fetch('/api/tasks/add', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ content, priority, date, color, category })
    })
    .then(res => res.json())
    .then(data => {
        if(data.success) {
            location.reload(); 
        }
    });
}

// --- 4. CATEGORY FILTERING (NEW) ---
function filterTasks(category, btnElement) {
    // 1. Visual update for buttons
    document.querySelectorAll('.cat-pill').forEach(b => b.classList.remove('active'));
    btnElement.classList.add('active');

    // 2. Filter Rows
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
    event.stopPropagation(); // Stop click from triggering "Edit"
    
    const row = document.getElementById(`task-${id}`);
    
    // CHECK: Is the task already completed?
    // If YES, or if it's already "armed" (deletePendingId), we delete immediately.
    const isCompleted = row.classList.contains('completed');
    const isArmed = (deletePendingId === id);

    if (isCompleted || isArmed) {
        // EXECUTE DELETE (Animation + API)
        row.classList.add('deleting'); // Trigger CSS animation swipe
        
        setTimeout(() => {
            fetch(`/api/tasks/${id}/delete`, { method: 'DELETE' })
            .then(res => res.json())
            .then(data => {
                if(data.success) row.remove();
            });
        }, 300); // 300ms matches CSS
        
        deletePendingId = null; // Clear any pending state
    } else {
        // ARM DELETE (First Click for Active Tasks)
        if (deletePendingId) {
            resetPendingDelete();
        }
        
        deletePendingId = id;
        row.classList.add('delete-pending');
        
        // Add global listener to cancel if clicked elsewhere
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
    // If click is NOT on the delete button
    if (!event.target.closest('.btn-delete')) {
        resetPendingDelete();
    }
}

// --- 6. TOGGLE Logic ---
function toggleTask(id) {
    // Don't trigger edit
    if(event) event.stopPropagation(); 
    
    fetch(`/api/tasks/${id}/toggle`, { method: 'POST' })
    .then(res => res.json())
    .then(data => {
        const row = document.getElementById(`task-${id}`);
        const btn = document.getElementById(`btn-check-${id}`);
        row.classList.toggle('completed');
        btn.innerHTML = data.new_state ? '<i class="fas fa-check"></i>' : '';
    });
}

/* --- CLOSE MODAL ON OUTSIDE CLICK --- */
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('task-modal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            // If the click target is the overlay itself (not the box inside)
            if (e.target === modal) {
                closeModal();
            }
        });
    }
});