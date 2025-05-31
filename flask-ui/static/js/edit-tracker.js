document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.edit-tracker-btn').forEach(btn => {
      btn.addEventListener('click', e => {
        // 1) Find the wrapping .tracker-card <div> (not the <h3> itself)
        const card = e.currentTarget.closest('.tracker-card');
        if (!card) return;
  
        // 2) Extract ID + existing values from data-attributes on that <div>
        const tid = card.dataset.trackerId;
        const currentName   = e.currentTarget.textContent.trim();
        const existingColor = card.dataset.color;
        const existingVis   = card.dataset.visibility;
        let existingRule = {};
        try {
          existingRule = JSON.parse(card.dataset.rule || '{}');
        } catch {
          existingRule = {};
        }
  
        // 3) Decompose existingRule (which might be e.g. { daily: 3 } or { monthly: 10 }, etc.)
        let oldPeriod = 'daily';
        let oldCount  = 1;
        {
          const entries = Object.entries(existingRule);
          if (entries.length === 1) {
            oldPeriod = entries[0][0];
            oldCount  = entries[0][1];
          }
        }
  
        // 4) Grab references to the modal, the form, and each input inside it:
        const modal       = document.getElementById('new-tracker-modal');
        const form        = document.getElementById('new-tracker-form');
        const titleInput  = document.getElementById('title');
        const colorInput  = document.getElementById('color');
        const countInput  = document.getElementById('rule_count');
        const periodSelect= document.getElementById('rule_period');
        const visSelect   = document.getElementById('visibility');
        const submitBtn   = form.querySelector('button[type="submit"]');
  
        // 5) Pre-fill every field with the existing tracker’s values:
        titleInput.value     = currentName;
        colorInput.value     = existingColor;
        countInput.value     = String(oldCount);
        periodSelect.value   = oldPeriod;
        visSelect.value      = existingVis;
  
        // 6) Change the form’s action URL to “update” instead of “create”:
        //     Example: /update-tracker/7
        form.action = `/update-tracker/${tid}`;
  
        // 7) Change the submit button’s text to “Save” (instead of “Create”):
        submitBtn.textContent = 'Save';
  
        // 8) Finally, show the modal:
        modal.classList.remove('hidden');
      });
    });
  });