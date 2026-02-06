/* app/static/gym/js/routine_detail.js */

document.addEventListener("DOMContentLoaded", function () {
    const inputField = document.getElementById('ex-name');
    const hiddenIdField = document.getElementById('ex-lib-id'); // <--- NEW
    
    const suggestionsBox = document.getElementById('suggestions-box');
    const addCard = document.getElementById('add-card');
    
    // UI Elements for Toggle
    const badge = document.getElementById('template-badge');
    const saveOption = document.getElementById('save-option');
    const saveCheck = document.getElementById('save-check');

    let timeout = null;

    window.searchExercises = function() {
        const query = inputField.value;
        
        // If user is typing, they are potentially creating a NEW thing.
        // So we clear the hidden ID and reset UI to "Manual Mode"
        if (hiddenIdField.value) {
            resetToManualMode(); 
        }

        if (query.length < 2) { 
            suggestionsBox.style.display = 'none'; 
            return; 
        }
        
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            fetch(`/gym/api/search_exercises?q=${query}`)
                .then(response => response.json())
                .then(data => {
                    suggestionsBox.innerHTML = '';
                    if (data.length > 0) {
                        suggestionsBox.style.display = 'block';
                        data.forEach(item => {
                            const div = document.createElement('div');
                            div.style.padding = '12px 15px'; 
                            div.style.cursor = 'pointer'; 
                            div.style.borderBottom = '1px solid #333'; 
                            div.style.color = '#eee';
                            div.style.display = 'flex';
                            div.style.justifyContent = 'space-between';
                            div.style.alignItems = 'center';

                            div.innerHTML = `
                                <div>
                                    <div style="font-weight:600;">${item.name_en}</div>
                                    <div style="font-size:0.75rem; color:#888;">${item.name_es || ''}</div>
                                </div>
                                <span style="background: rgba(59, 91, 219, 0.2); color: #7b96ff; font-size: 0.65rem; padding: 2px 6px; border-radius: 4px;">TEMPLATE</span>
                            `;
                            
                            div.onclick = () => {
                                selectTemplate(item, item.id); // Passing ID (assuming API sends it, we might need to add it to routes.py api)
                            };
                            
                            div.onmouseover = () => { div.style.background = '#252525'; };
                            div.onmouseout = () => { div.style.background = 'transparent'; };
                            
                            suggestionsBox.appendChild(div);
                        });
                    } else { 
                        suggestionsBox.style.display = 'none'; 
                    }
                });
        }, 300);
    }

    // We need to fetch the ID in the API. If API doesn't return ID, we rely on name matching in backend.
    // For now, let's update the API call in routes.py to include 'id'.
    // Assuming you updated routes.py as well. If not, backend will handle name match.
    // But hidden ID is safer.
    
    function selectTemplate(item) {
        // 1. Fill Data
        inputField.value = item.name_en;
        hiddenIdField.value = item.name_en; // Use name as ID for backend lookup if ID missing
        document.getElementById('ex-es').value = item.name_es;
        document.getElementById('ex-sets').value = item.default_sets;
        document.getElementById('ex-reps').value = item.default_reps;
        
        // 2. Visual Feedback
        suggestionsBox.style.display = 'none';
        
        // Show Badge, Hide Checkbox
        addCard.style.border = '1px solid #4cd137'; 
        addCard.style.background = 'rgba(76, 209, 55, 0.05)';
        
        badge.style.display = 'flex';
        saveOption.style.display = 'none';
        saveCheck.checked = false; // Uncheck safe option
    }

    function resetToManualMode() {
        // Clear hidden ID
        hiddenIdField.value = '';
        
        // Reset UI
        addCard.style.border = '1px dashed rgba(255, 255, 255, 0.1)';
        addCard.style.background = 'rgba(0, 0, 0, 0.3)';
        
        badge.style.display = 'none';
        saveOption.style.display = 'flex';
    }

    document.addEventListener('click', function(e) { 
        if (e.target.id !== 'ex-name') suggestionsBox.style.display = 'none'; 
    });
});