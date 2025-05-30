document.addEventListener('DOMContentLoaded', ()=>{
    document.querySelectorAll('.edit-tracker-btn').forEach(btn=>{
      btn.addEventListener('click', async e=>{
        const card = e.currentTarget.closest('[data-tracker-id]');
        const tid  = card.dataset.trackerId;
        const name = card.querySelector('h3').textContent.trim();
        const rule = JSON.parse(card.dataset.rule);
        const color= card.dataset.color;
        const vis  = card.dataset.visibility;
  
        // show a prompt (quick & dirty)
        const newName = prompt('Name?', name);
        const newColor= prompt('Hex color?', color);
        // assume daily rule for simplicity
        const newRule = { daily: rule.daily || 1 };
        const newVis  = prompt('Visibility: private|friends|public', vis);
  
        const payload={name:newName,color:newColor,rule:newRule,visibility:newVis};
        const res = await fetch(`/update-tracker/${tid}`, {
          method:'POST',
          credentials:'include',
          headers:{'Content-Type':'application/json'},
          body: JSON.stringify(payload)
        });
        if(res.ok){
          // reload aggregates & name/color
          card.querySelector('h3').textContent = newName;
          card.querySelector('h3').style.color = newColor;
          card.dataset.rule   = JSON.stringify(newRule);
          card.dataset.color  = newColor;
          card.dataset.visibility = newVis;
          renderAllTrackers();
        } else {
          alert('Edit failed: '+res.status);
        }
      });
    });
  });