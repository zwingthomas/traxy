document.addEventListener('DOMContentLoaded', () => {
    // Grab references to all the relevant DOM elements once:
    const newModal         = document.getElementById('new-tracker-modal');
    const deleteConfirmMod = document.getElementById('delete-confirm-modal');
    const confirmNameSpan  = document.getElementById('confirm-tracker-name');
    const confirmInput     = document.getElementById('confirm-name-input');
    const cancelDeleteBtn  = document.getElementById('cancel-delete-btn');
    const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
  
    const form          = document.getElementById('new-tracker-form');
    const modalTitle    = document.getElementById('modal-title');
    const titleInput    = document.getElementById('title');
    const colorInput    = document.getElementById('color');
    const countInput    = document.getElementById('rule_count');
    const periodSelect  = document.getElementById('rule_period');
    const visSelect     = document.getElementById('visibility');
    const saveBtn       = document.getElementById('save-btn');
    const deleteBtn     = document.getElementById('delete-tracker-btn');
  
    // Helper: hide both modals
    function hideAllModals() {
      newModal.classList.add('hidden');
      deleteConfirmMod.classList.add('hidden');
    }
  
    //-----------------------------------------------------------------------
    // 1) “Edit” button click → populate + show the “Create/Edit” modal:
    //-----------------------------------------------------------------------
    document.querySelectorAll('.edit-tracker-btn').forEach(btn => {
      btn.addEventListener('click', e => {
        const card = e.currentTarget.closest('.tracker-card');
        if (!card) return;
  
        const tid           = card.dataset.trackerId;
        const currentName   = card.querySelector('h3').textContent.trim();
        const existingColor = card.dataset.color;
        const existingVis   = card.dataset.visibility;
        let existingRule    = {};
        try {
          existingRule = JSON.parse(card.dataset.rule || '{}');
        } catch {
          existingRule = {};
        }
  
        // Extract “period” + “count” from existingRule (e.g. { daily: 3 })
        let oldPeriod = 'daily', oldCount = 1;
        const entries = Object.entries(existingRule);
        if (entries.length === 1) {
          oldPeriod = entries[0][0];
          oldCount  = entries[0][1];
        }
  
        //  2a) Pre-fill every field in the same modal form:
        modalTitle.textContent = "Edit Tracker";
        titleInput.value       = currentName;
        colorInput.value       = existingColor;
        countInput.value       = String(oldCount);
        periodSelect.value     = oldPeriod;
        visSelect.value        = existingVis;
        saveBtn.textContent    = "Save";
  
        //  2b) Change the <form action> to the update‐URL:
        form.action = `/update-tracker/${tid}`;
  
        //  3) Un-hide the red “Delete Tracker” button:
        deleteBtn.classList.remove('hidden');
  
        //  4) Show the “Create/Edit” modal on top:
        newModal.classList.remove('hidden');
      });
    });
  
    //-----------------------------------------------------------------------
    // 5) “Delete Tracker” button (in the edit modal) → open the Confirm popup
    //-----------------------------------------------------------------------
    deleteBtn.addEventListener('click', () => {
      // Extract the tid + name that are currently in the form action
      const actionUrl = form.action;              // e.g. "/update-tracker/7"
      const parts     = actionUrl.split('/');
      const tid       = parts[parts.length - 1];  // "7"
      const theName   = titleInput.value.trim();  // the current name in the form
  
      // Fill in the name into the confirmation popup
      confirmNameSpan.textContent = theName;
      confirmInput.value = '';
      confirmInput.focus();
  
      // Show the confirmation modal on top:
      deleteConfirmMod.classList.remove('hidden');
    });
  
    //-----------------------------------------------------------------------
    // 6) “Cancel” on the delete-confirm popup → just hide that confirm box
    //-----------------------------------------------------------------------
    cancelDeleteBtn.addEventListener('click', () => {
      deleteConfirmMod.classList.add('hidden');
    });
  
    //-----------------------------------------------------------------------
    // 7) “DELETE” on the delete-confirm popup → actually call DELETE, then reload
    //-----------------------------------------------------------------------
    confirmDeleteBtn.addEventListener('click', async () => {
      const typed = confirmInput.value.trim();
      const trackerName = confirmNameSpan.textContent.trim();
  
      if (typed !== trackerName) {
        alert('The name does not match exactly. No delete.');
        return;
      }
  
      // If they typed exactly the right name, extract tid from form.action:
      const actionUrl = form.action;               // "/update-tracker/7"
      const parts     = actionUrl.split('/');
      const tid       = parts[parts.length - 1];   // "7"
  
      try {
        const res = await fetch(`/delete-tracker/${tid}`, {
          method: 'DELETE',
          credentials: 'include'
        });
        if (!res.ok) {
          const txt = await res.text();
          alert('Delete failed: ' + res.status + '\n' + txt);
          return;
        }
      } catch (err) {
        alert('Network error while deleting: ' + err);
        return;
      }
  
      // On success → hide both modals and reload page:
      hideAllModals();
      window.location.reload();
    });
  });