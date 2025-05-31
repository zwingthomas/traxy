document.addEventListener('DOMContentLoaded', () => {
    // 1) INTERCEPT “submit” on #new-tracker-form when action is /update-tracker/…
    const form = document.getElementById('new-tracker-form');
    form.addEventListener('submit', async function(event) {
      // If form.action matches /update-tracker/<id>, we want to send JSON
      if (form.action.includes('/update-tracker/')) {
        event.preventDefault();
  
        // Gather the tracker_id from the URL segment:
        // form.action might be "https://.../update-tracker/7"
        const urlParts = form.action.split('/');
        const tid      = urlParts[urlParts.length - 1];
  
        // Read form inputs:
        const nameVal   = document.getElementById('title').value.trim();
        const colorVal  = document.getElementById('color').value;
        const countVal  = parseInt(document.getElementById('rule_count').value, 10);
        const periodVal = document.getElementById('rule_period').value;
        const visVal    = document.getElementById('visibility').value;
  
        if (!nameVal) {
          alert('Title is required.');
          return;
        }
        if (isNaN(countVal) || countVal < 1) {
          alert('Goal count must be a positive integer.');
          return;
        }
  
        // Build JSON payload exactly as FastAPI expects:
        const payload = {
          name:       nameVal,
          color:      colorVal,
          rule:       { [periodVal]: countVal },
          visibility: visVal
        };
  
        try {
          // Send JSON via fetch to Flask → FastAPI
          const res = await fetch(form.action, {
            method:      'POST',
            credentials: 'include',
            headers:     { 'Content-Type': 'application/json' },
            body:        JSON.stringify(payload)
          });
  
          if (!res.ok) {
            const txt = await res.text();
            alert('Update failed: ' + res.status + '\n' + txt);
            return;
          }
        } catch (err) {
          alert('Network error: ' + err);
          return;
        }
  
        // 2) Close the modal
        document.getElementById('new-tracker-modal').classList.add('hidden');
  
        // 3) Re-render trackers by refreshing the page
        window.location.reload();
        
        return;
      }
  
      // Otherwise (action is "/new-tracker"), let the browser do a normal POST.
    });
  
    // 4) “Click on a tracker title” → fill the same modal, but switch into EDIT mode
    document.querySelectorAll('.edit-tracker-btn').forEach(btn => {
      btn.addEventListener('click', e => {
        // Find the parent .tracker-card:
        const card = e.currentTarget.closest('.tracker-card');
        if (!card) return;
  
        const tid           = card.dataset.trackerId;
        const existingColor = card.dataset.color;
        const existingVis   = card.dataset.visibility;
        let existingRule    = {};
        try {
          existingRule = JSON.parse(card.dataset.rule);
        } catch {
          existingRule = {};
        }
  
        // Decompose rule (e.g. { daily: 3 } → oldPeriod="daily", oldCount=3)
        let oldPeriod = 'daily', oldCount = 1;
        const entries = Object.entries(existingRule);
        if (entries.length === 1) {
          oldPeriod = entries[0][0];
          oldCount  = entries[0][1];
        }
  
        // Fill in the modal’s inputs:
        document.getElementById('title').value      = e.currentTarget.textContent.trim();
        document.getElementById('color').value      = existingColor;
        document.getElementById('rule_count').value = String(oldCount);
        document.getElementById('rule_period').value= oldPeriod;
        document.getElementById('visibility').value = existingVis;
  
        // Switch form → UPDATE mode:
        form.action = `/update-tracker/${tid}`;
        form.method = 'POST';  // still POST, but JS intercepts and sends JSON
        form.querySelector('button[type="submit"]').textContent = 'Save';
  
        // Show the modal:
        document.getElementById('new-tracker-modal').classList.remove('hidden');
      });
    });
  });